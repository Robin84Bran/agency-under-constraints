"""D2 output exhaustion, immutable clearance and mixed-freeze provenance regressions."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from trl_core import ROOT, canonical, sha, strict_load, render
from trl_io import Stop, read, save, stop, timestamp
from trl_transport import Fake, request, raw_record
from trl_validation import validate, stdout
from trl_budget import Ledger, ActiveTime, maximum
from trl_collect import episode, push_gate, collect
from trl_analysis import replay
from trl_freeze import (D2_CHANGED, D2_ADDED, D1_FREEZE_SHA256, inputs, freeze_d2,
                        verify, attest)
from trl_d2 import EPISODE, record_clearance, clearance, stop_gate
from trl_test import tested_inputs


class LengthFake(Fake):
    def generate(self,actor,req,work):
        raw = super().generate(actor,req,work)
        if len(self.calls)==2:
            e = strict_load(stdout(raw));e.update(done_reason='length',eval_count=192,response='{"cells":[')
            return raw_record(canonical(e).encode(),running=raw['running'])
        return raw


class OutputTests(unittest.TestCase):
    def raw(self,**changes):
        req = request('llama8b',render('central',1,0,[]),3,10,maximum('central'))
        raw = Fake().generate('llama8b',req,Path('.'))
        env = strict_load(stdout(raw));env.update(changes)
        return raw_record(canonical(env).encode(),running=raw['running'])

    def test_length_or_exact_limit_invalid_even_with_valid_json(self):
        for change in ({'done_reason':'length'},{'eval_count':192},{'done_reason':'length','eval_count':192}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError,'output-length'):
                validate(self.raw(**change),'llama8b',3,maximum('central'))

    def test_identity_context_digest_and_unknown_stop_remain_fatal(self):
        for change in ({'model':'wrong'},{'done_reason':'unknown'},{'eval_count':193},{'prompt_eval_count':8000}):
            with self.subTest(change=change),self.assertRaises(Stop):
                validate(self.raw(**dict({'done_reason':'length'},**change)),'llama8b',3,maximum('central'))
        for key,value in (('digest','wrong'),('context_length',2048)):
            raw=self.raw(done_reason='length');raw['running']['models'][0][key]=value
            with self.assertRaises(Stop):validate(raw,'llama8b',3,maximum('central'))

    def test_input_shortfall_is_fatal_before_output_length(self):
        raw=self.raw(done_reason='length',prompt_eval_count=239)
        with self.assertRaisesRegex(Stop,'input truncation'):
            validate(raw,'llama8b',3,maximum('central'),expected_input_tokens=240)

    def test_envelope_and_usage_errors_not_downgraded(self):
        for raw in (raw_record(b'not json'),self.raw(done_reason='length',eval_count=None),
                    raw_record(b'{}',returncode=1)):
            with self.assertRaises((Stop,ValueError)):
                validate(raw,'llama8b',3,maximum('central'))
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);timer=ActiveTime(base/'time.jsonl',43200);timer.begin('fixture')
            class EnvelopeFake(Fake):
                def generate(self,*args):return raw_record(b'not json')
            ep={'actor':'llama8b','seed':0,'regime':'central','id':'llama8b-s000-central'}
            result=episode(ep,EnvelopeFake(),base,Ledger(base/'cost.jsonl'),timer,'FAKE')
            self.assertFalse(result['fatal'])
            self.assertFalse((base/'STOP.json').exists())

    def test_length_terminates_episode_no_retry_prior_round_kept_replays(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);timer=ActiveTime(base/'time.jsonl',43200);timer.begin('fixture')
            ep={'actor':'llama8b','seed':0,'regime':'central','id':'llama8b-s000-central'}
            fake=LengthFake();result=episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
            self.assertFalse(result['fatal']);self.assertFalse(result['complete'])
            self.assertEqual(len(fake.calls),2);self.assertEqual(len(result['receipts']),3)
            self.assertEqual([e['status'] for e in result['events']],['executed']*3+['technical']*3+['missing']*6)
            self.assertFalse((base/'STOP.json').exists())
            row=replay(ep,base/'episodes'/ep['id']);self.assertTrue(row['attempted']);self.assertEqual(row['calls'],2)
            with self.assertRaises(Stop):episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')


class D2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        for n in read(ROOT/'freeze-d2.json')['files']:
            p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True)
            baseline=ROOT/'deviations/d3/baseline'/n
            p.write_bytes((baseline if baseline.exists() else ROOT/n).read_bytes())
        for n in D2_ADDED:
            p=self.root/n
            if not p.exists() and n!='deviations/d2/clearance.json':
                p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{"fixture":true}\n')
        # One genuine stopped episode, never synthesize or overwrite its evidence.
        shutil.copytree(ROOT/'collection/episodes'/EPISODE,self.root/'collection/episodes'/EPISODE)
        for n in ('STOP.json','push.json','push-event.raw.json'):
            shutil.copyfile(ROOT/'collection'/n,self.root/'collection'/n)
        (self.root/'deviations/d2/clearance.json').unlink(missing_ok=True) # temp fixture only
        record_clearance(self.root)
        self.report()
        freeze_d2(self.root)
        self.commit='b'*40
        import datetime as dt
        self.when=(timestamp(read(self.root/'freeze-d2.json')['created_at'])+dt.timedelta(microseconds=1)).isoformat()
        self.event={'id':'synthetic-d2','activity_type':'push','after':self.commit,
                    'ref':'refs/heads/claude/d2','timestamp':self.when}
        self.eventpath=self.root/'build/activity.json';self.eventpath.parent.mkdir(exist_ok=True)
        self.eventpath.write_text(canonical(self.event))

    def report(self):
        p=self.root/'evidence/test-report-d2.json'
        p.write_text(canonical({'status':'PASS','failures':0,'errors':0,'tests':1,
                               'tested_files':tested_inputs(self.root),'fixture':True})+'\n')

    def git(self,args,**kw):
        self.assertEqual(kw['cwd'],self.clone)
        if args[1]=='rev-parse':return (self.commit+'\n').encode()
        if args[1]=='remote':return b'https://github.com/Robin84Bran/research.git\n'
        if args[1]=='ls-remote':return (self.commit+'\t'+self.event['ref']+'\n').encode()
        if args[1]=='show':return (self.root/args[2].split(':three-rules-one-lunch/')[1]).read_bytes()
        raise AssertionError(args)

    def attest(self):
        with patch('trl_freeze.subprocess.check_output',side_effect=self.git):
            return attest(self.root,self.eventpath,self.commit,'three-rules-one-lunch',self.clone)

    def test_freeze_binds_both_parents_and_clearance_create_once(self):
        f=read(self.root/'freeze-d2.json');self.assertEqual(f['parent_freeze_sha256'],D1_FREEZE_SHA256)
        self.assertEqual(f['files']['freeze-d1.json'],D1_FREEZE_SHA256)
        for n in D2_CHANGED:self.assertEqual(f['files']['deviations/d2/baseline/'+n],read(self.root/'freeze-d1.json')['files'][n])
        with self.assertRaises(FileExistsError):freeze_d2(self.root)
        with self.assertRaises(FileExistsError):record_clearance(self.root)

    def test_scored_disposition_old_bytes_preserved(self):
        c=clearance(self.root);self.assertEqual(c['disposition'],'SCORED_NO_RERUN')
        self.assertEqual((c['Y'],c['H'],c['technical_opportunities'],c['missing_opportunities']),(0,0,3,9))
        self.assertTrue(read(self.root/'collection/episodes'/EPISODE/'episode.json')['fatal'])
        for n,h in c['preserved_files'].items():self.assertEqual(sha((self.root/n).read_bytes()),h)

    def test_historical_and_new_start_pushes_separately_bound(self):
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        old=(self.root/'collection/push.json').read_bytes()
        digest=self.attest();self.assertEqual(push_gate(self.root),digest)
        self.assertEqual((self.root/'collection/push.json').read_bytes(),old)
        save(self.root/'collection/episodes/new/r1-j0.start.json',{'freeze_sha256':digest,'started_at':__import__('trl_io').now()})
        self.assertEqual(push_gate(self.root),digest)
        p=self.root/'collection/episodes/new/r1-j0.start.json';v=read(p);v['freeze_sha256']=D1_FREEZE_SHA256;p.write_text(canonical(v))
        with self.assertRaises(Stop):push_gate(self.root)

    def test_attestation_create_once_and_no_new_start_before_attestation(self):
        self.attest()
        with self.assertRaises(FileExistsError):self.attest()
        self.assertTrue((self.root/'collection/push-event-d2.raw.json').exists())

    def test_d2_start_before_attestation_is_rejected(self):
        save(self.root/'collection/episodes/new/r1-j0.start.json',
             {'freeze_sha256':verify(self.root),'started_at':__import__('trl_io').now()})
        with self.assertRaisesRegex(Stop,'precede all D2 starts'):self.attest()
        self.assertFalse((self.root/'collection/push-d2.json').exists())

    def test_d2_push_must_follow_d2_freeze(self):
        self.event['timestamp']=read(self.root/'freeze-d1.json')['created_at']
        self.eventpath.write_text(canonical(self.event))
        with self.assertRaisesRegex(Stop,'follow active freeze'):self.attest()

    def test_historical_start_tampering_and_stop_tampering_rejected(self):
        for rel in ('collection/STOP.json','collection/episodes/'+EPISODE+'/r1-j0.start.json'):
            p=self.root/rel;original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(rel=rel),self.assertRaisesRegex(Stop,'preserved evidence changed'):
                clearance(self.root)
            p.write_bytes(original)

    def test_any_other_fatal_or_partial_episode_blocks_resume(self):
        self.attest()
        ep=read(self.root/'collection/episodes'/EPISODE/'episode.json')['episode']
        original_read=__import__('trl_collect').read
        def selected(path):
            if Path(path)==self.root/'config/episodes.json':return [ep]
            return original_read(path)
        d=self.root/'collection/episodes/other';d.mkdir()
        with patch('trl_collect.read',side_effect=selected),patch('trl_collect.Local',side_effect=AssertionError('no dispatch')):
            with self.assertRaisesRegex(Stop,'nonterminal episode'):collect(self.root,'local')
            save(d/'episode.json',{'fatal':True})
            with self.assertRaisesRegex(Stop,'terminal integrity failure'):collect(self.root,'local')

    def test_freeze_parent_identity_and_missing_current_tests_rejected(self):
        p=self.root/'freeze-d1.json';original=p.read_bytes();p.write_bytes(original+b' ')
        with self.assertRaisesRegex(Stop,'D1 freeze identity'):verify(self.root)
        p.write_bytes(original)
        (self.root/'freeze-d2.json').unlink() # temp fixture only
        (self.root/'evidence/test-report-d2.json').write_text('{"status":"PASS"}')
        with self.assertRaisesRegex(Stop,'passing D2 tests'):freeze_d2(self.root)

    def test_clearance_does_not_clear_future_or_tampered_stops(self):
        original=(self.root/'collection/STOP.json').read_bytes()
        stop(self.root/'collection','new fatal identity error')
        self.assertEqual((self.root/'collection/STOP.json').read_bytes(),original)
        with self.assertRaisesRegex(Stop,'uncleared'):stop_gate(self.root)

    def test_changed_historical_evidence_and_extra_call_rejected(self):
        p=self.root/'collection/episodes'/EPISODE/'r2-j0.start.json';save(p,{'fixture':True})
        with self.assertRaisesRegex(Stop,'additional'):clearance(self.root)

    def test_parent_and_scientific_drift_rejected(self):
        p=self.root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
        f=read(self.root/'freeze-d2.json');f['files']['config/prompts.json']=sha(p.read_bytes());f['content_sha256']=sha(canonical(f['files']).encode())
        (self.root/'freeze-d2.json').write_text(canonical(f))
        with self.assertRaisesRegex(Stop,'scope'):verify(self.root)

    def test_resume_skips_cleared_episode_without_constructing_transport(self):
        digest=self.attest();ep=read(self.root/'collection/episodes'/EPISODE/'episode.json')['episode']
        original_read=__import__('trl_collect').read
        def selected(path):
            if Path(path)==self.root/'config/episodes.json':return [ep]
            return original_read(path)
        with patch('trl_collect.read',side_effect=selected),patch('trl_collect.Local',side_effect=AssertionError('no resend')):
            collect(self.root,'local')
        self.assertEqual(push_gate(self.root),digest)
