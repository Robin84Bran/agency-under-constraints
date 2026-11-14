"""Offline r1 regressions: no provider/process/Git calls."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,canonical,sha,strict_load,schedule
from bob_collect import Ledger,ActiveTime,run_episode,collect,Stop,read,save
from bob_usage_limit import definite_nonstart,reset_time,pending,records,verify_prefix
from bob_offline import FakeTransport,write
from bob_audit import audit_episode,reconcile_ledger
from bob_analysis import load_collection
from test_collect import ep
from bob_paths import collection_dir

BEFORE='2026-11-11T13:00:00+00:00'
AFTER='2026-11-11T13:31:00+00:00'


class UsageLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.e=ep('claude');self.fixture=(ROOT/'fixtures/claude-usage-limit.json').read_bytes()
        write(self.root/'freeze.json',{'test':'offline'})
        self.digest=sha((self.root/'freeze.json').read_bytes())
        write(self.root/'config/order.json',[self.e]);write(self.root/'config/runtime.json',{'claude_binary':'NOT_EXECUTED'})
        self.ledger=Ledger(collection_dir(self.root)/'cost.jsonl');self.timer=ActiveTime(collection_dir(self.root)/'frontier-time.jsonl',7200)
        self.fake=FakeTransport(self.e);self.requests=[];self.refuse_at={0};self.dispatches=0
        outer=self
        class Transport:
            def generate(self,req,phase,budget):
                i=outer.dispatches;outer.dispatches+=1;outer.requests.append(canonical(req).encode())
                if i in outer.refuse_at:return dict(stdout=outer.fixture,stderr=b'limit fixture',returncode=1)
                return outer.fake.generate(req,phase,budget)
        self.transport=Transport()
    def tearDown(self):self.tmp.cleanup()
    def run_episode(self,stamp=BEFORE,resumption=None):
        with patch('bob_usage_limit.now',return_value=stamp):
            return run_episode(self.root,self.e,self.transport,self.ledger,self.timer,self.digest,resumption=resumption)
    def run_collect(self,stamp=BEFORE):
        with patch('bob_usage_limit.now',return_value=stamp),patch('bob_freeze.verify',return_value={}),patch('bob_freeze.push_gate'),patch('bob_collect.frontier_gate'),patch('bob_collect.ClaudeAdapter',return_value=self.transport):
            return collect(self.root,['claude'])
    def test_exact_refusal_fixture_and_real_valid_envelope(self):
        self.assertTrue(definite_nonstart(strict_load(self.fixture)))
        real=(ROOT/'fixtures/real-claude-envelope.json').read_bytes()
        self.assertEqual(sha(real),'a4e9f03ce0cd4cbde843924c06880082baaee6e58597fcad0f970022a9c6eb2c')
        self.assertFalse(definite_nonstart(strict_load(real)))
    def test_all_near_misses_keep_frozen_handling(self):
        base=strict_load(self.fixture)
        variants=[]
        for key,value in [('api_error_status',500),('api_error_status',None),('is_error',False),('total_cost_usd',.01),('total_cost_usd',False),('result','other error'),('structured_output',{}),('queued_turn_count',1)]:
            e=copy.deepcopy(base);e[key]=value;variants.append(e)
        for key in base['usage']:
            for value in (1,True,None):
                e=copy.deepcopy(base);e['usage'][key]=value;variants.append(e)
            e=copy.deepcopy(base);del e['usage'][key];variants.append(e)
        for e in variants:self.assertFalse(definite_nonstart(e),e)
    def test_reset_in_local_zone_and_unknown_time(self):
        env=strict_load(self.fixture)
        self.assertEqual(reset_time(env,BEFORE),'2026-11-11T13:30:00+00:00')
        env['result']="You've hit your 5-hour limit · resets unknown"
        self.assertIsNone(reset_time(env,BEFORE))
    def test_pause_zero_settlement_no_terminal_or_stop(self):
        saved=self.run_collect()
        self.assertEqual(saved['status'],'PAUSED');self.assertEqual(self.dispatches,1)
        ledger=Ledger(self.ledger.path);self.assertFalse(ledger.blocked);self.assertEqual(ledger.spent,0)
        r=records(self.root)[0];self.assertEqual(ledger.calls[r['id']],0)
        self.assertNotIn('0',ledger.holds[self.e['id']])
        self.assertFalse((collection_dir(self.root)/'episodes').exists())
        self.assertEqual((collection_dir(self.root)/'usage-limits'/f"{r['id']}.stdout").read_bytes(),self.fixture)
        self.assertFalse((collection_dir(self.root)/'transport-pause.json').exists())
    def test_collect_before_reset_no_dispatch_or_mutation(self):
        self.run_collect();before={str(p):p.read_bytes() for p in (collection_dir(self.root)).rglob('*') if p.is_file()}
        self.assertEqual(self.run_collect()['status'],'PAUSED');self.assertEqual(self.dispatches,1)
        self.assertEqual(before,{str(p):p.read_bytes() for p in (collection_dir(self.root)).rglob('*') if p.is_file()})
    def test_collect_resume_identical_request_and_analysis(self):
        self.run_collect();self.run_collect(AFTER)
        self.assertEqual(self.requests[0],self.requests[1]);self.assertEqual(self.fake.calls,6)
        saved=read(collection_dir(self.root)/'episodes'/f"{self.e['id']}.json")
        audit_episode(self.root,self.e,saved,self.digest)
        self.assertEqual(reconcile_ledger(self.root,{self.e['id']:saved})['status'],'PASS')
        result=load_collection(self.root,[e for e in schedule() if e['model']=='claude'])
        self.assertEqual(result['operational_events']['usage_limit_refusals'],1)
        self.assertTrue(next(x for x in result['episodes'] if x['id']==self.e['id'])['trajectory_valid']);self.assertEqual(len(saved['calls']),6)
    def test_mid_episode_resume_never_resends_prior_history(self):
        self.refuse_at={2};self.run_collect()
        r=records(self.root)[0];self.assertEqual(len(r['snapshot']['events']),2)
        prior={p:p.read_bytes() for folder in ('calls','raw') for p in (collection_dir(self.root)/folder).glob('*')}
        self.run_collect(AFTER)
        self.assertEqual(self.fake.calls,6);self.assertEqual(self.requests[2],self.requests[3])
        for p,raw in prior.items():self.assertEqual(p.read_bytes(),raw)
        saved=read(collection_dir(self.root)/'episodes'/f"{self.e['id']}.json");audit_episode(self.root,self.e,saved,self.digest)
    def test_report_position_resume(self):
        self.refuse_at={5};self.run_collect()
        r=records(self.root)[0];self.assertEqual(r['slot'],6);self.assertEqual(len(r['prior_calls']),5)
        self.run_collect(AFTER);self.assertEqual(self.fake.calls,6);self.assertEqual(self.requests[5],self.requests[6])
        self.assertEqual(reconcile_ledger(self.root,{self.e['id']:read(collection_dir(self.root)/'episodes'/f"{self.e['id']}.json")})['status'],'PASS')
    def test_repeated_limit_pauses_and_zero_settlements(self):
        self.refuse_at={0,1};self.run_collect();self.run_collect(AFTER)
        self.assertEqual(len(records(self.root)),2);self.assertFalse(Ledger(self.ledger.path).blocked)
        self.assertEqual(self.run_collect(AFTER)['status'],'PAUSED');self.assertEqual(self.dispatches,2)
        self.run_collect('2026-11-12T13:31:00+00:00');self.assertEqual(self.fake.calls,6)
        self.assertTrue(all(x==self.requests[0] for x in self.requests[:3]))
    def test_pause_not_counted_as_model_or_technical_failure(self):
        self.refuse_at={2};self.run_collect();result=load_collection(self.root,[e for e in schedule() if e['model']=='claude'])
        row=next(x for x in result['episodes'] if x['id']==self.e['id']);self.assertFalse(row['known']);self.assertTrue(row['attempted']);self.assertEqual(row['behavior'],{})
        self.assertEqual(result['operational_events']['usage_limit_paused_episodes'],1)
    def test_tampered_cost_prefix_is_rejected(self):
        self.run_collect();path=self.ledger.path;raw=path.read_bytes();path.write_bytes(raw.replace(b'"actual":0',b'"actual":1'))
        with self.assertRaisesRegex(Stop,'prefix'):self.run_collect(AFTER)
    def test_tampered_request_is_rejected(self):
        self.run_collect();r=records(self.root)[0];(collection_dir(self.root)/'requests'/f"{r['call_id']}.json").write_text('{}')
        with self.assertRaisesRegex(Stop,'request/start'):self.run_collect(AFTER)
    def test_uncertain_crash_after_clearance_is_not_retried(self):
        self.run_collect();r=records(self.root)[0]
        write(collection_dir(self.root)/'usage-limit-resumes'/f"{r['id']}.json",{'fixture':'crash'})
        with self.assertRaisesRegex(Stop,'uncertain dispatch'):self.run_collect(AFTER)
        self.assertEqual(self.dispatches,1)
    def test_nonzero_usage_is_still_a_durable_stop(self):
        env=strict_load(self.fixture);env['usage']['input_tokens']=1;self.fixture=canonical(env).encode()
        with self.assertRaises(Stop):self.run_collect()
        self.assertTrue(Ledger(self.ledger.path).blocked);self.assertEqual(records(self.root),[])
    def test_unknown_reset_stays_paused_without_dispatch(self):
        env=strict_load(self.fixture);env['result']="You've hit your 5-hour limit · resets unknown"
        self.fixture=canonical(env).encode();self.run_collect()
        self.assertIsNone(records(self.root)[0]['resume_after_utc'])
        self.assertEqual(self.run_collect(AFTER)['status'],'PAUSED');self.assertEqual(self.dispatches,1)
    def test_other_zero_usage_error_is_not_a_nonstart(self):
        env=strict_load(self.fixture);env['result']='some other failure';self.fixture=canonical(env).encode()
        with self.assertRaises(Stop):self.run_collect()
        self.assertTrue(Ledger(self.ledger.path).blocked);self.assertEqual(records(self.root),[])
    def test_extra_nonzero_usage_or_tool_activity_is_not_a_nonstart(self):
        for changes in ({'reasoning_tokens':1},{'server_tool_use':{'web_fetch_requests':1}}):
            env=strict_load(self.fixture);env['usage'].update(changes)
            self.assertFalse(definite_nonstart(env))
        env=strict_load(self.fixture);env['modelUsage']={'claude-opus-5-5':{'inputTokens':1}}
        self.assertFalse(definite_nonstart(env))
    def test_tampered_prior_response_prevents_resume(self):
        self.refuse_at={2};self.run_collect();r=records(self.root)[0]
        path=collection_dir(self.root)/'raw'/f"{r['prior_calls'][0]}.stdout";path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'stdout hash'):self.run_collect(AFTER)
        self.assertEqual(self.dispatches,3)
    def test_orphan_after_pause_remains_uncertain(self):
        self.run_collect();write(collection_dir(self.root)/'starts/orphan.json',{'fixture':'uncertain'})
        with self.assertRaisesRegex(Stop,'orphan/uncertain'):self.run_collect(AFTER)
        self.assertEqual(self.dispatches,1)
    def test_rearm_requires_original_hold_and_is_single_use(self):
        self.run_collect();r=records(self.root)[0]
        with self.assertRaisesRegex(Stop,'original hold'):
            self.ledger.event(event='rearm',id=r['id'],episode=self.e['id'],slot=0,amount=0)
        self.run_collect(AFTER)
        with self.assertRaisesRegex(Stop,'invalid non-start rearm'):
            self.ledger.event(event='rearm',id=r['id'],episode=self.e['id'],slot=0,amount=0)
    def test_time_prefix_is_checked_but_append_is_valid(self):
        self.run_collect();r=records(self.root)[0];path=self.timer.path
        verify_prefix(path,r['ledger_prefixes'][path.name])
        raw=path.read_bytes();path.write_bytes(b' '+raw)
        with self.assertRaisesRegex(Stop,'prefix'):self.run_collect(AFTER)


class RevisionFreezeTests(unittest.TestCase):
    def test_revision_binds_parent_and_rejects_overwrite_drift_and_starts(self):
        from bob_freeze import inventory,create,create_revision,verify
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in inventory(ROOT):
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            write(root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256=sha(canonical(inventory(root)).encode())))
            create(root);parent=(root/'freeze.json').read_bytes()
            create_revision(root);self.assertEqual((root/'freeze.json').read_bytes(),parent)
            self.assertEqual(verify(root)['parent_freeze_sha256'],sha(parent))
            with self.assertRaises(Stop):create_revision(root)
            (root/'freeze.json').write_bytes(parent+b' ')
            with self.assertRaisesRegex(Stop,'parent'):verify(root)


class R2UsageLimitTests(UsageLimitTests):
    """Exercise the complete existing refusal/resume boundary in the r2 namespace."""
    def setUp(self):
        super().setUp()
        write(self.root/'freeze-r2.json',{'test':'offline-r2'})
        self.digest=sha((self.root/'freeze-r2.json').read_bytes())
        write(self.root/'collection/sentinel.json',{'disposition':'VOID-HARNESS'})
        self.ledger=Ledger(collection_dir(self.root)/'cost.jsonl')
        self.timer=ActiveTime(collection_dir(self.root)/'frontier-time.jsonl',7200)

    def tearDown(self):
        self.assertEqual(read(self.root/'collection/sentinel.json'),{'disposition':'VOID-HARNESS'})
        self.assertEqual(list((self.root/'collection').iterdir()),[self.root/'collection/sentinel.json'])
        super().tearDown()
