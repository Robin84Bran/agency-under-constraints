import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from od_core import *
from od_io import *
from od_collect import collect
from od_transport import Fake
from od_analysis import replay,analyze_rows
from od_provenance import push_record,receipt_gate
from od_freeze import attest
from od_stats import evaluate_sample,percentile

class Integrity(unittest.TestCase):
    def test_log_replay_prefix_truncate_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.jsonl';l=Ledger(p)
            l.event(event='reserve',id='a',amount=20000);l.event(event='settle',id='a',actual=1000)
            self.assertEqual(Ledger(p).spent,1000);data=p.read_bytes()
            p.write_bytes(data.splitlines(keepends=True)[0])
            with self.assertRaises(Stop):Ledger(p)
            p.write_bytes(data.replace(b'20000',b'20001'))
            with self.assertRaises(Stop):Ledger(p)
            p.write_bytes(data+b'{')
            with self.assertRaises(Stop):Ledger(p)
    def test_rolling_gate_and_overrun_unclipped(self):
        with tempfile.TemporaryDirectory() as d:
            l=Ledger(Path(d)/'ledger.jsonl');l.event(event='reserve',id='a',amount=24000000)
            with self.assertRaises(Stop):l.event(event='reserve',id='b',amount=1)
            l.event(event='settle',id='a',actual=1000);l.event(event='reserve',id='b',amount=20000)
            l.event(event='settle',id='b',actual=40000000)
            self.assertEqual(l.spent,40001000)
            with self.assertRaises(Stop):l.event(event='reserve',id='c',amount=1)
    def test_unknown_hold_and_duplicate_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.jsonl';l=Ledger(p);l.event(event='reserve',id='a',amount=22000)
            self.assertEqual(Ledger(p).exposure,22000)
            with self.assertRaises(Stop):l.event(event='reserve',id='a',amount=22000)
    def test_concurrency_lock(self):
        with tempfile.TemporaryDirectory() as d:
            with lock(d):
                with self.assertRaises(Stop):
                    with lock(d):pass
    def test_timer_crash_charge_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'time.jsonl';t=ActiveTime(p,200);t.begin('a',190)
            self.assertGreaterEqual(ActiveTime(p,200).charged,190)
            with self.assertRaises(Stop):ActiveTime(p,200).begin('b',20)
            p.write_bytes(b'')
            with self.assertRaises(Stop):ActiveTime(p,200)
    def jobs(self,actor='qwen7b'):return [e for e in schedule() if e['actor']==actor][:2]
    def test_local_failures_continue_no_resend(self):
        for fault in ('length','done','usage','timeout','invalid'):
            with tempfile.TemporaryDirectory() as d:
                fake=Fake(fault);base=Path(d)/'out';jobs=self.jobs()
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),2);self.assertFalse((base/'STOP.json').exists())
                rows,_=replay(ROOT,base,True,jobs);self.assertTrue(all(not r['schema_valid'] for r in rows))
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),2)
    def test_identity_stops(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';fake=Fake('identity')
            with self.assertRaises(Stop):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=self.jobs())
            self.assertEqual(len(fake.calls),1);self.assertTrue((base/'STOP.json').exists());replay(ROOT,base,True,self.jobs())
    def test_first_frontier_fails_closed(self):
        for fault in ('cost','overrun','timeout'):
            with tempfile.TemporaryDirectory() as d:
                fake=Fake(fault);base=Path(d)/'out';jobs=self.jobs('claude')
                with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),1);self.assertTrue((base/'STOP.json').exists());rows,ledger=replay(ROOT,base,True,jobs)
                if fault in ('cost','timeout'):self.assertGreater(ledger['open_holds_micro_usd'],0)
                if fault=='overrun':self.assertEqual(ledger['spent_micro_usd'],26000000)
                with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),1)
    def test_paid_success_then_bad_answer_episode(self):
        class Sequence(Fake):
            def generate(self,*args):
                self.fault='invalid' if self.calls else None
                return super().generate(*args)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';fake=Sequence();jobs=self.jobs('claude')
            collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            rows,l=replay(ROOT,base,True,jobs)
            self.assertEqual([r['schema_valid'] for r in rows],[True,False]);self.assertEqual(l['spent_micro_usd'],4000)
    def test_interrupted_reservation_no_resend(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';base.mkdir();ep=self.jobs('claude')[0]
            Ledger(base/'ledger.jsonl').event(event='reserve',id=ep['id'],amount=reserve(render(ep))['micro_usd'])
            fake=Fake()
            with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=[ep])
            self.assertEqual(fake.calls,[])
    def test_tampered_terminal_raw_and_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs('claude');collect(ROOT,'claude',fake_transport=Fake(),output=base,jobs_override=jobs)
            with self.assertRaises(Stop):replay(ROOT,base,False,jobs)
            p=base/'episodes'/jobs[0]['id']/'episode.json';e=read(p);e['fleet']=None;p.write_text(canonical(e))
            with self.assertRaises(Stop):replay(ROOT,base,True,jobs)
    def test_unstarted_and_null_fixed_denominators(self):
        jobs=schedule();null=[dict(e,fleet=None,choice_status='ABSTENTION',reason=None,attempted=True,schema_valid=True,usage=None,**score(e,None,True)) for e in jobs]
        result=analyze_rows(null)
        self.assertEqual(result['joint_primary'],'FAIL');self.assertEqual(result['contrasts']['qwen7b/independent']['rehearsal_optimal_rate'],0)
        self.assertTrue(all(r['operational_value']==0 and r['optimal']==0 for r in null))
        for row in null:row['attempted']=False;row['schema_valid']=False
        result=analyze_rows(null);self.assertEqual(result['joint_primary'],'UNKNOWN');self.assertEqual(result['contrasts']['qwen7b/independent']['pairs'],300)
    def test_bootstrap_multiplicity(self):
        f=read(ROOT/'fixtures/analysis.json')
        b=f['bootstrap_multiplicity'];self.assertEqual(evaluate_sample(b['terms'],b['units'],b['sampled']),b['expected'])
        p=f['percentile'];self.assertEqual(percentile(p['values'],p['q']),p['expected'])
    def test_server_activity_record(self):
        commit='a'*40;e={'activity_type':'push','after':commit,'ref':'refs/heads/main','id':123,'timestamp':'2026-01-01T00:00:00Z'}
        self.assertEqual(push_record(e,commit)[0],'refs/heads/main')
        for edit in [dict(e,after='b'*40),dict(e,timestamp='2026-01-01'),dict(e,ref='main'),dict(e,activity_type='force_push')]:
            with self.assertRaises(Stop):push_record(edit,commit)
    def test_attest_separate_roots_committed_sources(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'study';clone=Path(d)/'clone';root.mkdir();clone.mkdir();commit='a'*40
            save(root/'freeze.json',{'created_at':'2026-01-01T00:00:00Z','files':{'input.txt':sha(b'input')}});(root/'input.txt').write_bytes(b'input')
            event=Path(d)/'event.json';save(event,{'activity_type':'push','after':commit,'ref':'refs/heads/main','id':123,'timestamp':'2026-02-01T00:00:00Z'})
            h=sha((root/'freeze.json').read_bytes());seen=[]
            def git(args,cwd,timeout):
                self.assertEqual(cwd,clone);seen.append(args)
                if args[1:]==['rev-parse','HEAD']:return (commit+'\n').encode()
                if args[1:]==['remote','get-url','origin']:return b'git@github.com:Robin84Bran/research.git\n'
                if args[1]=='show':return (root/args[2].split('one-door-many-hands/')[1]).read_bytes()
                if args[1]=='ls-remote':return (commit+'\trefs/heads/main\n').encode()
                raise AssertionError(args)
            with patch('od_freeze.verify',return_value=h),patch('od_freeze.subprocess.check_output',side_effect=git):
                attest(root,event,commit,clone,'one-door-many-hands')
            self.assertTrue((root/'collection/push.json').exists());self.assertEqual(list(clone.iterdir()),[]);receipt_gate(root)
            self.assertIn(['git','show',commit+':one-door-many-hands/input.txt'],seen)
    def test_invalid_repo_path_no_git_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);save(root/'freeze.json',{'created_at':'2026-01-01T00:00:00Z'});e=root/'event.json'
            save(e,{'activity_type':'push','after':'a'*40,'ref':'refs/heads/main','id':1,'timestamp':'2026-02-01T00:00:00Z'})
            with patch('od_freeze.verify',return_value='x'):
                with self.assertRaises(Stop):attest(root,e,'a'*40,root,'../other')
    def test_partial_fixture_analysis_regression(self):
        jobs=self.jobs();rows=[dict(e,fleet=None,attempted=False,schema_valid=False,choice_status='UNKNOWN',reason='unstarted',usage=None,**score(e,None,False)) for e in jobs]
        self.assertEqual(analyze_rows(rows)['joint_primary'],'UNKNOWN')
    def test_positive_joint_fixture_and_ceiling(self):
        jobs=[e for e in schedule() if e['actor']=='qwen7b']
        rows=[]
        for e in jobs:
            p=payload(e);n=oracle(p['target'],p['failure_percent'],e['door'],e['mode'])[2][0] if e['evidence']=='rehearsal' else 24
            rows.append(dict(e,fleet=n,attempted=True,schema_valid=True,choice_status='CHOICE',reason=None,usage=None,**score(e,n,True)))
        self.assertEqual(analyze_rows(rows)['joint_primary'],'PASS')
        for r in rows:
            p=payload(r);n=oracle(p['target'],p['failure_percent'],r['door'],r['mode'])[2][0];r.update(fleet=n,**score(r,n,True))
        result=analyze_rows(rows);self.assertEqual(result['joint_primary'],'FAIL');self.assertEqual(result['contrasts']['qwen7b/independent']['D_R'],0)
    def test_real_freeze_manifest_drift(self):
        import shutil
        from od_freeze import freeze,verify
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('config','evidence'):shutil.copytree(ROOT/name,root/name)
            for name in ('tests','fixtures','offline'):(root/name).mkdir()
            h=freeze(root);self.assertEqual(verify(root),h)
            (root/'extra.py').write_text('x=1')
            with self.assertRaises(Stop):verify(root)
            (root/'extra.py').unlink();p=root/'config/episodes.json';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaises(Stop):verify(root)
    def test_analysis_does_not_import_providers(self):
        import subprocess,sys
        subprocess.check_call([sys.executable,'-B','-c',"import od_analysis,sys; assert 'od_transport' not in sys.modules and 'urllib.request' not in sys.modules"],cwd=ROOT)
    def test_retained_preflight_detects_wrong_system(self):
        from od_identity import verify_preflight,identity
        m=identity(ROOT)['qwen7b'];meta={'tags':{'models':[{'name':m['tag'],'digest':m['digest']}]},'show':{'template':m['template'],'system':''}}
        with self.assertRaises(Stop):verify_preflight(ROOT,'qwen7b',meta)
