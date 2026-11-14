"""D3b offline regressions: no model process, network, or Git mutation."""
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from trl_core import ROOT, canonical, render, roles, sha, strict_load
from trl_io import Stop, now, read, save, stop, timestamp
from trl_budget import ActiveTime, Ledger, maximum
from trl_collect import collect, episode, push_gate
from trl_transport import Fake, raw_record, request
from trl_validation import MODEL, cost, stdout, usage, validate
from trl_analysis import replay, score
from trl_freeze import (D3B_ADDED, D3B_CHANGED, D3_FREEZE_SHA256, attest, freeze_d3b,
                        inputs, verify)
from trl_d3b import PauseStop, pause_gate, pause_if_needed, record_clearance, stop_gate
from trl_test import tested_inputs
from historical import collection_snapshot, frozen_bytes


class ClaudeTests(unittest.TestCase):
    def raw(self,quota=1,**changes):
        req=request('claude',render('central' if quota==3 else 'shared',1,0 if quota==3 else 1,[]),quota,11,maximum('central'))
        env=strict_load(stdout(Fake().generate('claude',req,Path('.'))))
        env.update(changes)
        return raw_record(canonical(env).encode())

    def test_one_and_two_schema_turns_with_strict_payload_all_quotas(self):
        for quota in (1,3):
            for turns,reason in ((1,'end_turn'),(1,'tool_use'),(2,'tool_use')):
                raw=self.raw(quota,num_turns=turns,stop_reason=reason)
                value,env,u=validate(raw,'claude',quota,maximum('central'))
                self.assertEqual(len(value['cells']),quota)

    def test_only_allowed_counts_types_and_stops(self):
        for turns in (0,3,-1,True,False,1.0,'2',None):
            with self.subTest(turns=turns),self.assertRaises(Stop):
                validate(self.raw(num_turns=turns,stop_reason='tool_use'),'claude',1,maximum('shared'))
        for reason in ('end_turn','max_tokens',None,'unknown'):
            with self.subTest(reason=reason),self.assertRaises(Stop):
                validate(self.raw(num_turns=2,stop_reason=reason),'claude',1,maximum('shared'))

    def test_two_turns_never_bypass_payload_or_integrity_checks(self):
        changes=[{'structured_output':v} for v in (None,[], 'prose',{}, {'cells':[True]},
            {'cells':[48]}, {'cells':[1,2]}, {'cells':[1],'extra':0})]
        changes += [{'modelUsage':{}},{'effort':'high'},{'tool_calls':[{}]},
            {'permission_denials':[{}]},{'subtype':'error'},{'is_error':True}]
        for change in changes:
            with self.subTest(change=change),self.assertRaises((Stop,ValueError)):
                validate(self.raw(num_turns=2,stop_reason='tool_use',**change),'claude',1,maximum('shared'))
        env=strict_load(stdout(self.raw(num_turns=2,stop_reason='tool_use')))
        env.pop('structured_output');env['result']='{"cells":[1]}'
        with self.assertRaises(Stop):validate(raw_record(canonical(env).encode()),'claude',1,maximum('shared'))
        for text in (canonical(env)+'\n'+canonical(env),'['+canonical(env)+']',
                     canonical(env)[:-1]+',"num_turns":2}'):
            with self.assertRaises((Stop,ValueError)):validate(raw_record(text.encode()),'claude',1,maximum('shared'))

    def test_cache_tokens_are_input_once_and_overrun_guard_counts_them(self):
        env=strict_load(stdout(self.raw(num_turns=2,stop_reason='tool_use')))
        env['usage'].update(input_tokens=2,cache_creation_input_tokens=1600,cache_read_input_tokens=7,output_tokens=199)
        env['modelUsage'][MODEL].update(inputTokens=2,cacheCreationInputTokens=1600,cacheReadInputTokens=7,outputTokens=199)
        raw=raw_record(canonical(env).encode());_,_,u=validate(raw,'claude',1,maximum('shared'))
        self.assertEqual(sum(u[k] for k in ('input','cache_creation','cache_read')),1609)
        self.assertEqual(cost(u),4*1609+20*199)
        env['total_cost_usd']='0.016788'
        self.assertEqual(cost(usage(env,'claude')),16788)
        env.pop('total_cost_usd');env['usage']['cache_creation_input_tokens']=3000
        env['modelUsage'][MODEL]['cacheCreationInputTokens']=3000
        with self.assertRaisesRegex(Stop,'overrun'):
            validate(raw_record(canonical(env).encode()),'claude',1,maximum('shared'))
        env['usage'].pop('cache_read_input_tokens')
        self.assertIsNone(usage(env,'claude'))

    def test_first_scheduled_two_turn_envelope_passes_contract_and_replay(self):
        class SchemaFake(Fake):
            def generate(self,*args):
                env=strict_load(stdout(super().generate(*args)))
                env.update(num_turns=2,stop_reason='tool_use')
                return raw_record(canonical(env).encode())
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);timer=ActiveTime(base/'time.jsonl',10800);timer.begin('fixture')
            ep={'actor':'claude','seed':0,'regime':'shared','id':'claude-s000-shared'}
            fake=SchemaFake();ledger=Ledger(base/'cost.jsonl')
            result=episode(ep,fake,base,ledger,timer,'FAKE')
            self.assertTrue(result['complete']);self.assertEqual(len(fake.calls),12)
            self.assertEqual(read(base/'claude-contract.json')['status'],'PASS')
            self.assertTrue(replay(ep,base/'episodes'/ep['id'])['complete'])
            self.assertEqual(ledger.spent,19200)


class D3bTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.template=Path(cls.tmp.name)/'template'
        # Reconstruct the sealed D3b inputs without later builder edits.
        parent=read(ROOT/'freeze-d3b.json')
        for n,digest in parent['files'].items():
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(frozen_bytes(n,digest))
        shutil.copyfile(ROOT/'freeze-d3.json',cls.template/'freeze-d3.json')
        for n in D3B_ADDED:
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(frozen_bytes(n,parent['files'][n]))
        collection_snapshot(cls.template)
        cls.report(cls.template)
        freeze_d3b(cls.template)

    @staticmethod
    def report(root):
        (root/'evidence/test-report-d3b.json').write_text(canonical({'status':'PASS','failures':0,'errors':0,
            'tests':1,'fixture':True,'tested_files':tested_inputs(root)})+'\n')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';shutil.copytree(self.template,self.root)
        self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        self.commit='d'*40
        self.event={'id':'synthetic-d3b','activity_type':'push','after':self.commit,'ref':'refs/heads/claude/d3b',
            'timestamp':(timestamp(read(self.root/'freeze-d3b.json')['created_at'])+dt.timedelta(microseconds=1)).isoformat()}
        self.eventpath=self.root/'build/activity.json';self.eventpath.parent.mkdir(exist_ok=True)
        self.eventpath.write_text(canonical(self.event))

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

    def order(self,count=6):
        # These local episodes are definitely unstarted in saved evidence.
        existing={p.parent.name for p in (self.root/'collection/episodes').glob('*/episode.json')}
        return [e for e in read(self.root/'config/episodes.json') if e['actor']!='claude' and e['id'] not in existing][:count]

    def run_collect(self,order,faults):
        original=__import__('trl_collect').read
        def selected(path):
            return order if Path(path)==self.root/'config/episodes.json' else original(path)
        class Controlled(Fake):
            def preflight(self,actor):
                prior=sorted((self_root/'collection/runtime').glob(actor+'-*.json'))
                return read(prior[0]) if prior else {'fixture':True}
            def generate(self,actor,req,work):
                raw=super().generate(actor,req,work)
                fault=faults.get(Path(work).name)
                late_at=2 if Path(work).name.endswith('-central') else 4
                if fault=='transport' or (fault=='late_transport' and len(self.calls)==late_at):
                    env=strict_load(stdout(raw));env.update(done=False);env.pop('eval_count')
                    return raw_record(canonical(env).encode(),running=raw['running'])
                if faults.get(Path(work).name)=='schema':
                    env=strict_load(stdout(raw));env['response']='{"cells":[true]}'
                    return raw_record(canonical(env).encode(),running=raw['running'])
                return raw
        self_root=self.root
        with patch('trl_collect.read',side_effect=selected),patch('trl_collect.Local',side_effect=Controlled):
            return collect(self.root,'local')

    def clear(self,name='STOP-d3b.json'):
        return record_clearance(self.root,name,'Claude','Transport reviewed; resume only unattempted episodes.')

    def test_freeze_parent_chain_baselines_and_scientific_scope(self):
        f=read(self.root/'freeze-d3b.json');self.assertEqual(f['parent_freeze_sha256'],D3_FREEZE_SHA256)
        for n in D3B_CHANGED:self.assertEqual(f['files']['deviations/d3b/baseline/'+n],read(self.root/'freeze-d3.json')['files'][n])
        with self.assertRaises(FileExistsError):freeze_d3b(self.root)
        p=self.root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
        f['files']['config/prompts.json']=sha(p.read_bytes());f['content_sha256']=sha(canonical(f['files']).encode())
        (self.root/'freeze-d3b.json').write_text(canonical(f))
        with self.assertRaisesRegex(Stop,'scope'):verify(self.root)

    def test_fresh_d3b_push_directly_binds_preserved_d1_d2_starts(self):
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        digest=self.attest();self.assertEqual(push_gate(self.root),digest)
        self.assertTrue((self.root/'collection/push-d3b.json').exists())
        self.assertFalse((self.root/'collection/push-d3.json').exists())
        with self.assertRaises(FileExistsError):self.attest()
        save(self.root/'collection/episodes/new/r1-j0.start.json',{'freeze_sha256':D3_FREEZE_SHA256,'started_at':now()})
        with self.assertRaisesRegex(Stop,'push/start'):push_gate(self.root)

    def test_late_attestation_and_missing_tests_block(self):
        save(self.root/'collection/episodes/new/r1-j0.start.json',{'freeze_sha256':verify(self.root),'started_at':now()})
        with self.assertRaisesRegex(Stop,'precede all D3b starts'):self.attest()
        (self.root/'collection/episodes/new/r1-j0.start.json').unlink() # temporary fixture
        (self.root/'freeze-d3b.json').unlink()
        (self.root/'evidence/test-report-d3b.json').write_text('{"status":"PASS"}')
        with self.assertRaisesRegex(Stop,'passing D3b tests'):freeze_d3b(self.root)

    def test_three_episodes_pause_durably_clear_and_skip_without_resend(self):
        self.attest();order=self.order(4);self.assertEqual(len(order),4)
        with self.assertRaises(PauseStop):self.run_collect(order,{e['id']:'transport' for e in order})
        p=self.root/'collection/STOP-d3b.json';saved=p.read_bytes()
        self.assertEqual(read(p)['episode_ids'],[e['id'] for e in order[:3]])
        self.assertFalse((self.root/'collection/episodes'/order[3]['id']).exists())
        # A restart is blocked before constructing a provider.
        with patch('trl_collect.Local',side_effect=AssertionError('no dispatch')):
            with self.assertRaises(PauseStop):collect(self.root,'local')
        self.assertEqual(p.read_bytes(),saved)
        for ep in order[:3]:
            row=replay(ep,self.root/'collection/episodes'/ep['id'])
            self.assertFalse(row['complete']);self.assertEqual(row['calls'],1)
        # The unattempted episode remains a missing row with twelve opportunities.
        row=replay(order[3],self.root/'collection/episodes'/order[3]['id'])
        self.assertFalse(row['attempted']);self.assertEqual((row['Y'],row['H']),(0,0))
        self.clear()
        with self.assertRaises(FileExistsError):self.clear()
        self.run_collect(order,{})
        self.assertEqual(p.read_bytes(),saved)
        for ep in order[:3]:self.assertEqual(len(list((self.root/'collection/episodes'/ep['id']).glob('*.start.json'))),1)
        self.assertTrue(read(self.root/'collection/episodes'/order[3]['id']/'episode.json')['complete'])

    def test_success_and_schema_failure_reset_episode_streak(self):
        self.attest();order=self.order(6)
        faults={e['id']:'transport' for e in order}
        faults[order[2]['id']]='schema'
        self.run_collect(order[:5],faults)
        # A new invocation is a new run.
        self.run_collect(order[5:],{})
        self.assertFalse((self.root/'collection/STOP-d3b.json').exists())
        self.assertFalse(read(self.root/'collection/episodes'/order[2]['id']/'episode.json')['transport_failure'])

    def test_same_run_success_breaks_streak_and_multi_call_failure_counts_once(self):
        self.attest();order=self.order(5)
        faults={order[i]['id']:'late_transport' for i in (0,1,3,4)}
        self.run_collect(order,faults)
        self.assertFalse((self.root/'collection/STOP-d3b.json').exists())
        for ep in order:
            if ep['id'] in faults:
                terminal=read(self.root/'collection/episodes'/ep['id']/'episode.json')
                self.assertEqual(terminal['attempted_calls'],len(roles(ep['regime']))+1)
                self.assertTrue(terminal['transport_failure'])
                self.assertEqual(len(terminal['receipts']),3)
                self.assertFalse(replay(ep,self.root/'collection/episodes'/ep['id'])['complete'])

    def test_two_failures_in_each_separate_run_do_not_combine(self):
        self.attest();order=self.order(4);faults={e['id']:'transport' for e in order}
        self.run_collect(order[:2],faults)
        self.run_collect(order[2:],faults)
        self.assertFalse((self.root/'collection/STOP-d3b.json').exists())
        runs={read(self.root/'collection/episodes'/e['id']/'episode.json')['cohort_run_id'] for e in order}
        self.assertEqual(len(runs),2)

    def test_repeated_pause_after_clearance_gets_new_stop(self):
        self.attest();order=self.order(6);faults={e['id']:'transport' for e in order}
        with self.assertRaises(PauseStop):self.run_collect(order,faults)
        old=(self.root/'collection/STOP-d3b.json').read_bytes();self.clear()
        with self.assertRaises(PauseStop):self.run_collect(order,faults)
        self.assertEqual((self.root/'collection/STOP-d3b.json').read_bytes(),old)
        self.assertTrue((self.root/'collection/STOP-d3b-002.json').exists())
        self.clear('STOP-d3b-002.json');stop_gate(self.root)

    def test_crash_between_third_terminal_and_pause_recovers_before_next_dispatch(self):
        self.attest();order=self.order(4);faults={e['id']:'transport' for e in order}
        actual=pause_if_needed;count=0
        def crash(root):
            nonlocal count
            count+=1
            if count==4:raise KeyboardInterrupt('fixture crash after third terminal')
            actual(root)
        with patch('trl_d3b.pause_if_needed',side_effect=crash):
            # Includes one startup check; call 4 is after third terminal.
            with self.assertRaises(KeyboardInterrupt):self.run_collect(order,faults)
        self.assertFalse((self.root/'collection/STOP-d3b.json').exists())
        with patch('trl_collect.Local',side_effect=AssertionError('no dispatch after crash')):
            with self.assertRaises(PauseStop):collect(self.root,'local')
        self.assertTrue((self.root/'collection/STOP-d3b.json').exists())
        self.assertFalse((self.root/'collection/episodes'/order[3]['id']).exists())

    def test_integrity_stop_cannot_be_cleared_and_prior_evidence_cannot_change(self):
        self.attest();stop(self.root/'collection','wrong pinned model')
        original=(self.root/'collection/STOP-d3b.json').read_bytes()
        with self.assertRaisesRegex(Stop,'integrity STOP'):self.clear()
        with self.assertRaises(Stop):stop_gate(self.root)
        stop(self.root/'collection','second error')
        self.assertEqual((self.root/'collection/STOP-d3b.json').read_bytes(),original)
        self.assertFalse((self.root/'collection/STOP-d3b-002.json').exists())

    def test_pause_stop_and_bound_episode_tampering_blocks_clearance(self):
        self.attest();order=self.order(3)
        with self.assertRaises(PauseStop):self.run_collect(order,{e['id']:'transport' for e in order})
        terminal=self.root/'collection/episodes'/order[0]['id']/'episode.json'
        terminal.write_bytes(terminal.read_bytes()+b' ')
        with self.assertRaisesRegex(Stop,'changed D3b pause evidence'):self.clear()
