"""Offline D4 non-start, continuation, provenance, and evidence-preservation checks."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from trl_core import ROOT, canonical, sha, strict_load
from trl_io import Stop, read, save, timestamp, now
from trl_budget import ActiveTime, Ledger, maximum
from trl_transport import Fake, raw_record
from trl_validation import stdout, validate, usage
from trl_d4 import (CLEARANCE, UsageLimitPause, refusal, reset_at, clearance, record_clearance,
    episode, effective_calls, terminal_path, verify_pause, admission, provenance_layers, prepush_gate)
from trl_analysis import replay, analyze

REFUSAL = read(ROOT/'fixtures/d4/usage-limit.raw.json')
BEFORE = '2026-11-11T13:00:00+00:00'
AFTER = '2026-11-11T13:31:00+00:00'


class LimitFake(Fake):
    def __init__(self,at=0,raw=REFUSAL):
        super().__init__();self.at,self.raw=at,raw
    def generate(self,actor,req,work):
        raw=super().generate(actor,req,work)
        return deepcopy(self.raw) if len(self.calls)-1==self.at else raw


class RefusalTests(unittest.TestCase):
    def test_saved_exact_refusal_and_timezone_reset(self):
        self.assertIsNotNone(refusal(REFUSAL))
        self.assertEqual(reset_at(REFUSAL,BEFORE),'2026-11-11T13:30:00+00:00')
        self.assertEqual(reset_at(REFUSAL,AFTER),'2026-11-12T13:30:00+00:00')
        self.assertEqual(refusal(REFUSAL),strict_load(stdout(REFUSAL)))

    def test_nonzero_unknown_and_other_errors_are_not_nonstarts(self):
        original=strict_load(stdout(REFUSAL))
        for key,value in [('api_error_status',500),('api_error_status','429'),('is_error',False),
                          ('api_error','overloaded'),('total_cost_usd',0.000001),('total_cost_usd',None),
                          ('total_cost_usd',False),('structured_output',{'cells':[1]}),
                          ('result',original['result']+'\ngenerated answer'),('result','rate limited'),
                          ('modelUsage',{'x':{'outputTokens':1}}),('tool_calls',[{}])]:
            e=deepcopy(original);e[key]=value
            with self.subTest(key=key,value=value):
                self.assertIsNone(refusal(raw_record(canonical(e).encode(),returncode=1)))
        for key in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            for value in (1,None,False,-1):
                e=deepcopy(original);e['usage'][key]=value
                with self.subTest(key=key,value=value):
                    self.assertIsNone(refusal(raw_record(canonical(e).encode(),returncode=1)))
            e=deepcopy(original);del e['usage'][key]
            self.assertIsNone(refusal(raw_record(canonical(e).encode(),returncode=1)))
        self.assertIsNone(refusal(dict(REFUSAL,stdout_b64='!')))
        # An exact saved pre-generation refusal is decisive even if the wrapper
        # was interrupted after receiving it; no generation is made uncertain.
        for change in ({'returncode':None},{'returncode':0},{'transport_error':'timeout'}):
            self.assertIsNotNone(refusal(dict(REFUSAL,**change)))
        self.assertIsNone(refusal(raw_record((stdout(REFUSAL)+stdout(REFUSAL)).encode(),returncode=1)))

    def test_real_valid_envelope_keeps_validation_and_payload_rules(self):
        real=read(ROOT/'fixtures/d4/real-claude-envelope.json')
        raw=raw_record((ROOT/'fixtures/d4/real-claude-envelope.json').read_bytes())
        self.assertIsNone(refusal(raw))
        self.assertEqual(usage(real,'claude')['reported_cost_micro_usd'],16788)
        # Its real payload belongs to a sibling study; it must still fail this schema.
        with self.assertRaises(ValueError):validate(raw,'claude',1,maximum('private'))
        adapted=deepcopy(real);adapted['structured_output']={'cells':[9]}
        self.assertEqual(validate(raw_record(canonical(adapted).encode()),'claude',1,maximum('private'))[0],{'cells':[9]})
        # Raw valid envelope remains exactly the supplied file; adaptation is in memory.
        self.assertEqual(real,read(ROOT/'fixtures/d4/real-claude-envelope.json'))


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.base=self.root/'collection'
        self.ep={'id':'claude-s014-private','actor':'claude','regime':'private','seed':14}
        self.ledger=Ledger(self.base/'cost.jsonl')
        self.timer=ActiveTime(self.base/'time-claude.jsonl',10800);self.timer.begin('fixture')
        self.addCleanup(self.timer.end)

    def run_episode(self,transport,when=BEFORE):
        with patch('trl_d4.now',return_value=when):
            return episode(self.ep,transport,self.base,self.ledger,self.timer,'FAKE-D4',cohort_run_id='fixture')

    def test_first_refusal_not_contract_or_terminal_or_fatal_and_settles_zero(self):
        fake=LimitFake()
        with self.assertRaises(UsageLimitPause):self.run_episode(fake)
        self.assertEqual(len(fake.calls),1)
        self.assertEqual(self.ledger.spent,0);self.assertFalse(any(self.ledger.holds.values()))
        self.assertFalse(self.ledger.stopped)
        self.assertFalse((self.base/'STOP.json').exists())
        self.assertFalse((self.base/'claude-contract.json').exists())
        self.assertFalse((self.base/'episodes'/self.ep['id']/'episode.json').exists())
        p=self.base/'episodes'/self.ep['id']/'r1-j1'
        self.assertEqual(verify_pause(self.base,p)['settled_micro_usd'],0)
        with self.assertRaises(UsageLimitPause):self.run_episode(Fake(),BEFORE)
        result=self.run_episode(Fake(),AFTER)
        self.assertTrue(result['complete'])
        self.assertEqual(read(self.base/'claude-contract.json')['status'],'PASS')
        row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertEqual(row['operational_usage_limit_refusals'],1)
        self.assertEqual(row['technical_missing_rate'],0)
        self.assertEqual(row['calls'],12)

    def test_mid_episode_retains_history_resends_identical_bytes_only(self):
        fake=LimitFake(at=6)
        with self.assertRaises(UsageLimitPause):self.run_episode(fake)
        directory=self.base/'episodes'/self.ep['id']
        old={p:p.read_bytes() for p in directory.rglob('*') if p.is_file()}
        paused=replay(self.ep,directory)
        self.assertTrue(paused['paused']);self.assertEqual(paused['status'],'UNKNOWN')
        self.assertNotIn('technical_missing_rate',paused)
        resumed=Fake();result=self.run_episode(resumed,AFTER)
        self.assertEqual(len(resumed.calls),6);self.assertEqual(resumed.calls[0],fake.calls[-1])
        for p,data in old.items():self.assertEqual(p.read_bytes(),data)
        retry=self.base/'d4-episodes'/self.ep['id']/'attempts/r3-j1/0001/call.request.json'
        self.assertEqual(retry.read_bytes(),(directory/'r3-j1.request.json').read_bytes())
        expected_history = [[e['round'],e['slot'],e['cell'],e['reward']] for r in (1,2) for e in read(directory/f'round-{r}.json')]
        self.assertEqual(result['receipts'][:6],expected_history)
        row=replay(self.ep,directory)
        self.assertTrue(row['complete']);self.assertEqual(row['calls'],12)
        baseline=Fake()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);timer=ActiveTime(base/'time.jsonl',10800);timer.begin('baseline')
            expected=episode(self.ep,baseline,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
            timer.end()
        self.assertEqual(result['events'],expected['events']);self.assertEqual(result['receipts'],expected['receipts'])
        self.assertEqual(self.ledger.spent,12*1600)

    def test_repeated_refusals_at_same_position_are_separate_operational_events(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(at=7))
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(),AFTER)
        done=Fake();result=self.run_episode(done,'2026-11-12T13:31:00+00:00')
        self.assertTrue(result['complete']);self.assertEqual(len(done.calls),5)
        row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertEqual(row['operational_usage_limit_refusals'],2)
        self.assertEqual(row['technical_missing_rate'],0)
        self.assertEqual(len(list((self.base/'usage-limit-pauses').glob('*.json'))),2)
        self.assertFalse(any(self.ledger.holds.values()))

    def test_pause_on_later_round_after_resume_does_not_rewrite_rounds(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(at=6))
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(at=4),AFTER)
        # r3 is committed in the continuation; a further invocation replays it.
        result=self.run_episode(Fake(),'2026-11-12T13:31:00+00:00')
        self.assertTrue(result['complete']);self.assertTrue(replay(self.ep,self.base/'episodes'/self.ep['id'])['complete'])

    def test_changed_saved_request_or_pause_cannot_resume(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(at=6))
        p=self.base/'episodes'/self.ep['id']/'r3-j1.request.json'
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(Stop,'pause evidence changed'):self.run_episode(Fake(),AFTER)

    def test_nonzero_refusal_remains_terminal_no_resend(self):
        e=strict_load(stdout(REFUSAL));e['usage']['output_tokens']=1
        with self.assertRaises(Stop):self.run_episode(LimitFake(raw=raw_record(canonical(e).encode(),returncode=1)))
        terminal=read(self.base/'episodes'/self.ep['id']/'episode.json')
        self.assertTrue(terminal['fatal']);self.assertEqual(self.ledger.spent,20)
        self.assertTrue((self.base/'STOP.json').exists())
        with self.assertRaisesRegex(Stop,'terminal episode'):self.run_episode(Fake(),AFTER)

    def test_other_error_after_resume_stays_technical_and_replays(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake(at=6))
        result=self.run_episode(Fake('malformed'),AFTER)
        self.assertFalse(result['complete']);self.assertFalse(result['fatal'])
        row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertFalse(row['complete']);self.assertEqual(row['calls'],7)
        self.assertEqual(row['operational_usage_limit_refusals'],1)
        self.assertEqual([e['status'] for e in result['events']][6:],['technical']+['missing']*5)

    def test_timeout_retains_unknown_hold_and_never_resends(self):
        with self.assertRaises(Stop):self.run_episode(Fake('timeout'))
        self.assertTrue(self.ledger.stopped);self.assertTrue(any(self.ledger.holds.values()))
        with self.assertRaisesRegex(Stop,'terminal episode'):self.run_episode(Fake(),AFTER)

    def test_uncertain_retry_start_and_extra_attempt_block(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake())
        p=self.base/'d4-episodes'/self.ep['id']/'attempts/r1-j1/0001'
        p.mkdir(parents=True);save(p/'call.start.json',{'id':'uncertain'})
        with self.assertRaisesRegex(Stop,'uncertain D4 start'):self.run_episode(Fake(),AFTER)

    def test_analysis_pending_reports_operational_event_without_model_failure(self):
        with self.assertRaises(UsageLimitPause):self.run_episode(LimitFake())
        save(self.root/'config/episodes.json',[self.ep])
        result=analyze(self.root,self.base,self.root/'analysis')
        self.assertEqual(result['status'],'UNKNOWN');self.assertEqual(result['cohorts'],{})
        self.assertEqual(result['operational_events']['usage_limit_refusals'],1)
        self.assertIn('not model technical failures',(self.root/'analysis/RESULTS.md').read_text())


class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        c=clearance(ROOT)
        for name,digest in c['preserved_files'].items():
            data=(ROOT/name).read_bytes()
            if name in c['ledger_prefixes']:data=data[:c['ledger_prefixes'][name]['bytes']]
            self.assertEqual(sha(data),digest)
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        save(self.root/CLEARANCE,c)
        for name in ('deviations/d2/clearance.json','deviations/d3/clearance.json',
                     'deviations/d3c/clearance.json','deviations/d3c/disposition.json'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((ROOT/name).read_bytes())

    def test_clearance_preserves_saved_bytes_and_redispositions_failure(self):
        c=clearance(self.root)
        self.assertEqual(c['reviewer'],'Claude')
        self.assertEqual(c['paused_episodes'],['claude-s014-private'])
        self.assertEqual(c['cleared_stops'],['STOP-d3b-002.json'])
        self.assertEqual(c['events'][0]['settled_micro_usd'],0)
        self.assertEqual(c['events'][0]['previous_disposition'],'terminal technical/transport failure')
        p=self.root/'collection/episodes/claude-s014-private'
        self.assertTrue(read(p/'episode.json')['fatal'])
        row=replay(read(p/'episode.json')['episode'],p)
        self.assertTrue(row['paused']);self.assertNotIn('technical_missing_rate',row)
        with self.assertRaises(FileExistsError):record_clearance(self.root,'Claude','again')

    def test_ledger_prefix_append_allowed_rewrite_or_torn_tail_blocks(self):
        c=clearance(self.root)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            # Only exact preserved files, not unrelated project data.
            for name,digest in c['preserved_files'].items():
                source=self.root/name;data=source.read_bytes()
                if name in c['ledger_prefixes']:data=data[:c['ledger_prefixes'][name]['bytes']]
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            save(root/CLEARANCE,c)
            for name in c['ledger_prefixes']:
                p=root/name;original=p.read_bytes()
                p.write_bytes(original+b'{"fixture":"append"}\n');clearance(root)
                p.write_bytes(b'!'+original[1:])
                with self.assertRaisesRegex(Stop,'prefix'):clearance(root)
                p.write_bytes(original+b'{')
                with self.assertRaisesRegex(Stop,'prefix'):clearance(root)
                p.write_bytes(original)

    def test_new_d4_starts_cannot_claim_historical_provenance(self):
        c=clearance(self.root)
        layers=provenance_layers(self.root)
        self.assertEqual(layers[-1][0],'freeze-d4.json')
        self.assertFalse(layers[-1][2])
        self.assertEqual(set.union(*(v[2] for v in layers)),{n for n in c['preserved_files'] if n.endswith('.start.json')})
        prepush_gate(self.root)


class FreezeAndCollectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from historical import frozen_bytes
        from trl_freeze import D4_ADDED,D4_CHANGED,freeze_d4
        from trl_test import tested_inputs
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.template=Path(cls.tmp.name)/'template'
        parent=read(ROOT/'freeze-d3d.json')
        for name,digest in parent['files'].items():
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(frozen_bytes(name,digest))
        shutil.copyfile(ROOT/'freeze-d3d.json',cls.template/'freeze-d3d.json')
        c=clearance(ROOT)
        for name in c['preserved_files']:
            data=(ROOT/name).read_bytes()
            if name in c['ledger_prefixes']:data=data[:c['ledger_prefixes'][name]['bytes']]
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for name in D4_ADDED|D4_CHANGED:
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(frozen_bytes(name,read(ROOT/'freeze-d4.json')['files'][name]))
        (cls.template/'evidence/test-report-d4.json').write_text(canonical({
            'status':'PASS','tests':1,'failures':0,'errors':0,'fixture':True,
            'tested_files':tested_inputs(cls.template)})+'\n')
        freeze_d4(cls.template)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';shutil.copytree(self.template,self.root)
        self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        self.commit='d'*40

    def attest(self,bad=None):
        from trl_freeze import attest
        event={'id':'synthetic-d4','activity_type':'push','after':self.commit,
            'ref':'refs/heads/main','timestamp':(timestamp(read(self.root/'freeze-d4.json')['created_at'])+dt.timedelta(microseconds=1)).isoformat()}
        path=self.root/'build/event.json';path.parent.mkdir(exist_ok=True);path.write_text(canonical(event)+'\n')
        def git(args,**kwargs):
            if args[1]=='rev-parse':return (self.commit+'\n').encode()
            if args[1]=='remote':return b'https://github.com/Robin84Bran/research.git\n'
            if args[1]=='ls-remote':return (self.commit+'\trefs/heads/main\n').encode()
            if args[1]=='show':
                name=args[2].split(':three-rules-one-lunch/')[1]
                return b'wrong committed file' if name==bad else (self.root/name).read_bytes()
            raise AssertionError(args)
        with patch('trl_freeze.subprocess.check_output',side_effect=git):
            return attest(self.root,path,self.commit,'three-rules-one-lunch',self.clone,'freeze-d4.json')

    def test_seal_binds_parent_baselines_science_and_current_tests(self):
        from trl_freeze import verify,freeze_d4,d4_scope,D3D_FREEZE_SHA256
        f=read(self.root/'freeze-d4.json')
        self.assertEqual(f['parent_freeze_sha256'],D3D_FREEZE_SHA256)
        verify(self.root)
        with self.assertRaises(FileExistsError):freeze_d4(self.root)
        for name in ('config/prompts.json','trl_validation.py','deviations/d4/baseline/trl_collect.py'):
            bad=deepcopy(f);bad['files'][name]='0'*64
            with self.subTest(name=name),self.assertRaises(Stop):d4_scope(self.root,bad)
        (self.root/'freeze-d4.json').unlink()
        (self.root/'trl_d4.py').write_text('changed after tests')
        with self.assertRaisesRegex(Stop,'passing D4 tests'):freeze_d4(self.root)

    def test_attest_checks_committed_blobs_and_parent_receipts(self):
        from trl_collect import push_gate
        with self.assertRaisesRegex(Stop,'frozen file'):self.attest('trl_d4.py')
        self.attest();push_gate(self.root)
        (self.root/'collection/push-d3d.json').unlink()
        with self.assertRaises(FileNotFoundError):push_gate(self.root)

    def test_pre_reset_collect_is_clean_and_makes_no_service_access(self):
        from trl_collect import collect,main
        self.attest()
        with patch('trl_d4.now',return_value=BEFORE),patch('trl_collect.Claude',side_effect=AssertionError('no service access')):
            with self.assertRaises(UsageLimitPause):collect(self.root,'claude')
            with patch('sys.argv',['trl_collect.py','--root',str(self.root),'--cohort','claude']):
                main()  # CLI handles pause as a zero-status return.
        self.assertFalse(list((self.root/'collection').glob('STOP-d3b-003.json')))
        self.assertFalse((self.root/'collection/d4-episodes').exists())

    def test_real_mid_episode_collect_continues_only_refused_position(self):
        from trl_collect import collect,push_gate
        self.attest()
        ident='claude-s014-private';directory=self.root/'collection/episodes'/ident
        ep=read(directory/'episode.json')['episode']
        old={p:p.read_bytes() for p in directory.rglob('*') if p.is_file()}
        original=__import__('trl_collect').read
        def schedule(p):return [ep] if Path(p)==self.root/'config/episodes.json' else original(p)
        fake=Fake()
        fake.preflight=lambda actor:read(sorted((self.root/'collection/runtime').glob('claude-*.json'))[0])
        with patch('trl_d4.now',return_value='2099-01-01T00:00:00+00:00'),patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',return_value=fake):
            collect(self.root,'claude')
        self.assertEqual(len(fake.calls),6)
        self.assertEqual(fake.calls[0],read(directory/'r3-j1.request.json')['request'])
        for p,data in old.items():self.assertEqual(p.read_bytes(),data)
        row=replay(ep,directory);self.assertTrue(row['complete']);self.assertEqual(row['operational_usage_limit_refusals'],1)
        self.assertEqual(row['technical_missing_rate'],0)
        push_gate(self.root);clearance(self.root)
        # A second collect skips the now-complete continuation.
        with patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',side_effect=AssertionError('no resend')):
            collect(self.root,'claude')

    def test_new_start_cannot_be_laundered_into_parent_or_attested_late(self):
        save(self.root/'collection/d4-episodes/extra/attempts/r1-j1/0001/call.start.json',{
            'id':'foreign','freeze_sha256':sha((self.root/'freeze-d3d.json').read_bytes()),'started_at':now()})
        self.assertEqual(len(provenance_layers(self.root)[-1][2]),1)
        with self.assertRaisesRegex(Stop,'precede all D4 starts'):self.attest()

    def test_future_integrity_stop_is_not_cleared_by_usage_limit_record(self):
        from trl_io import stop
        from trl_d4 import stop_gate
        stop(self.root/'collection','wrong pinned model')
        self.assertEqual(read(self.root/'collection/STOP-d3b-003.json')['reason'],'wrong pinned model')
        with self.assertRaisesRegex(Stop,'integrity STOP'):stop_gate(self.root)
