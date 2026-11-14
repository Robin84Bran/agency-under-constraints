import copy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from bob_core import *
from bob_collect import *
from bob_offline import FakeTransport,dry_run


def ep(model='qwen7b',world='stable',arm='registry',seed=0):
    return dict(id=f'{model}-{seed:02d}-{world}-{arm}',model=model,seed=seed,world=world,arm=arm)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-test-')
        self.root=Path(self.temp.name)
        self.ledger=Ledger(self.root/'collection/cost.jsonl')
        self.timer=ActiveTime(self.root/'collection/time.jsonl',43200)

    def tearDown(self):
        self.temp.cleanup()

    def episode(self,episode=None,mode=None):
        e=episode or ep()
        fake=FakeTransport(e,mode=mode)
        saved=run_episode(self.root,e,fake,self.ledger,self.timer,'FIXTURE')
        return saved,fake

    def test_reserve_all_seven_before_first_call(self):
        e=ep('claude')
        base=FakeTransport(e)
        class Observe:
            def generate(inner,request,phase,budget):
                ident=e['id']
                if base.calls==0:
                    self.assertEqual(len(self.ledger.holds[ident]),7)
                    self.assertTrue((self.root/'collection/episode-starts'/f'{ident}.json').exists())
                    self.assertEqual(len(list((self.root/'collection/starts').glob('*.json'))),1)
                    self.assertEqual(len(list((self.root/'collection/requests').glob('*.json'))),1)
                return base.generate(request,phase,budget)
        saved=run_episode(self.root,e,Observe(),self.ledger,self.timer,'FIXTURE')
        self.assertTrue(saved['committed'])
        self.assertEqual(self.ledger.exposure,0)

    def test_successful_report_separate(self):
        saved,fake=self.episode()
        self.assertEqual((saved['decisions'],fake.calls),(5,6))
        self.assertEqual(saved['report'],{'submitted':True})
        self.assertEqual(saved['terminal_reason'],'accepted_submit')

    def test_malformed_action_no_repair_or_report(self):
        saved,fake=self.episode(mode='malformed')
        self.assertEqual(fake.calls,1)
        self.assertFalse(saved['trajectory_valid'])
        self.assertIsNone(saved['report'])
        self.assertEqual(saved['events'],[])

    def test_missing_structured_payload_no_result_fallback(self):
        with self.assertRaisesRegex(Stop,'durable'):
            self.episode(ep('claude'),mode='missing_payload')
        saved=read(self.root/'collection/episodes'/f"{ep('claude')['id']}.json")
        self.assertEqual(len(saved['calls']),1)
        self.assertIn('missing object structured_output',saved['error'])
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_missing_usage_retains_entire_hold_and_stops(self):
        e=ep('claude')
        with self.assertRaises(Stop): self.episode(e,'missing_usage')
        ledger=Ledger(self.ledger.path)
        self.assertTrue(ledger.blocked)
        self.assertEqual(ledger.exposure,sum(x['micro_usd'] for x in subholds(e)))
        self.assertEqual(len(list((self.root/'collection/calls').glob('*.json'))),1)
        self.assertTrue((self.root/'collection/episodes'/f"{e['id']}.json").exists())

    def test_settlement_overrun_never_clipped(self):
        e=ep('claude')
        with self.assertRaises(Stop): self.episode(e,'overrun')
        ledger=Ledger(self.ledger.path)
        self.assertTrue(ledger.blocked)
        self.assertGreater(ledger.spent,subholds(e)[0]['micro_usd'])
        with self.assertRaises(Stop): ledger.reserve(ep('claude',seed=1))

    def test_wrong_identity_is_durable_stop(self):
        with self.assertRaises(Stop): self.episode(ep('claude'),'wrong_identity')
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_truncation_stops_and_saves_raw(self):
        with self.assertRaises(Stop): self.episode(mode='truncated')
        self.assertEqual(len(list((self.root/'collection/raw').glob('*.stdout'))),1)
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_abstention_no_acknowledgment(self):
        from bob_analysis import score
        saved,fake=self.episode(mode='all_null')
        scored=score(ep(),saved)
        self.assertEqual((scored['Sstar'],scored['Astar']),(1,0))
        self.assertTrue(scored['explicit_null'])

    def test_no_repeat_of_started_episode(self):
        self.episode()
        with self.assertRaises((Stop,FileExistsError)): self.episode()

    def test_request_raw_and_hash_preserved(self):
        saved,_=self.episode()
        for cid in saved['calls']:
            start=read(self.root/'collection/starts'/f'{cid}.json')
            req=(self.root/'collection/requests'/f'{cid}.json').read_bytes()
            stdout=(self.root/'collection/raw'/f'{cid}.stdout').read_bytes()
            receipt=read(self.root/'collection/calls'/f'{cid}.json')
            self.assertEqual(sha(req),start['request_sha256'])
            self.assertEqual(sha(stdout),receipt['response_sha256'])
            self.assertEqual(start['freeze_sha256'],'FIXTURE')
            self.assertEqual(strict_load(req)['options']['seed'],0)

    def test_timeout_partial_bytes_retained_no_resend(self):
        e=ep()
        class Timeout:
            def generate(inner,*args):
                raise subprocess.TimeoutExpired('FAKE',180,output=b'partial',stderr=b'fixture-timeout')
        saved=run_episode(self.root,e,Timeout(),self.ledger,self.timer,'FIXTURE')
        self.assertEqual(len(saved['calls']),1)
        cid=saved['calls'][0]
        self.assertEqual((self.root/'collection/raw'/f'{cid}.stdout').read_bytes(),b'partial')
        self.assertTrue(saved['transport_failure'])

    def test_seven_generation_max(self):
        e=ep()
        class FinishAfterSix:
            calls=0
            def generate(inner,req,phase,budget):
                inner.calls+=1
                a=act('describe',target='lookup') if phase=='action' else {'submitted':False}
                return dict(stdout=canonical(dict(model=req['model'],response=canonical(a),done=True,done_reason='stop',prompt_eval_count=1,eval_count=1)).encode(),stderr=b'',returncode=0)
        f=FinishAfterSix()
        saved=run_episode(self.root,e,f,self.ledger,self.timer,'FIXTURE')
        self.assertEqual((saved['decisions'],f.calls),(6,7))
        self.assertFalse(saved['committed'])

    def test_frontier_unknown_gate_before_process_creation(self):
        with patch('bob_collect.subprocess.run') as proc:
            with self.assertRaises(Stop): ClaudeAdapter(self.root,'/not/executed')
            proc.assert_not_called()

    def test_claude_flags_schema_json_and_disabled_tools(self):
        cmd=claude_command('/fixture/claude','action',30000)
        self.assertEqual(cmd[cmd.index('--json-schema')+1],canonical(SCHEMAS['action']))
        self.assertEqual(cmd[cmd.index('--output-format')+1],'json')
        self.assertEqual(cmd[cmd.index('--tools')+1],'')
        self.assertEqual(cmd[cmd.index('--max-turns')+1],'1')
        for flag in ('--safe-mode','--restricted','--strict-mcp-config','--disable-slash-commands','--no-session-persistence','--no-chrome'):
            self.assertIn(flag,cmd)

    def test_no_inherited_api_override(self):
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'FIXTURE_DO_NOT_USE','ANTHROPIC_BASE_URL':'https://invalid','CLAUDE_CODE_MAX_RETRIES':'9'}):
            env=clean_env()
            self.assertNotIn('ANTHROPIC_API_KEY',env)
            self.assertNotIn('ANTHROPIC_BASE_URL',env)
            self.assertEqual(env['CLAUDE_CODE_MAX_RETRIES'],'0')
            self.assertEqual(env['MAX_STRUCTURED_OUTPUT_RETRIES'],'0')

    def test_envelope_duplicate_payload_rejected(self):
        with self.assertRaises(ValueError): strict_load('{"structured_output":{"submitted":true,"submitted":false}}')
        with self.assertRaises(ValueError): strict_load('{"structured_output":{},"structured_output":{}}')

    def test_string_structured_output_rejected(self):
        e=ep('claude')
        f=FakeTransport(e)
        env=strict_load(f.generate({'prompt':'fake'},'action',30000)['stdout'])
        env['structured_output']=canonical(env['structured_output'])
        with self.assertRaises(ValueError): payload(env,e,'action')

    def test_internal_turn_effort_identity_checked(self):
        e=ep('claude'); f=FakeTransport(e)
        env=strict_load(f.generate({'prompt':'fake'},'action',30000)['stdout'])
        for key,value in [('num_turns',2),('num_turns',True),('effort','high'),('modelUsage',{})]:
            altered=dict(env); altered[key]=value
            with self.assertRaises(Stop): payload(altered,e,'action')
        self.assertEqual(payload(env,e,'action')['op'],'lookup')

    def test_missing_usage_never_zero(self):
        for env in [{},{'usage':{}},{'usage':{'input_tokens':False}}]:
            with self.assertRaises(Stop): usage(env,'claude')

    def test_dry_run_matches_frozen_fixture(self):
        result=dry_run()
        self.assertEqual(result,read(ROOT/'fixtures/dry-run-expected.json'))
        self.assertEqual(result['episodes'],32)
        self.assertEqual(result['real_model_calls'],0)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-ledger-')
        self.path=Path(self.temp.name)/'cost.jsonl'
        self.ledger=Ledger(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_atomic_full_episode_reservation(self):
        e=ep('claude')
        self.ledger.reserve(e)
        self.assertEqual(self.ledger.exposure,195072)
        self.assertEqual(len(self.ledger.holds[e['id']]),7)
        self.assertEqual(len(self.path.read_text().splitlines()),1)

    def test_locked_duplicate_admission(self):
        stale=Ledger(self.path)
        self.ledger.reserve(ep('claude'))
        with self.assertRaises(Stop): stale.reserve(ep('claude'))
        self.assertEqual(len(self.path.read_text().splitlines()),1)

    def test_concurrent_lock_refuses_admission(self):
        with lock(self.path.with_suffix('.lock')):
            with self.assertRaises(Stop): self.ledger.reserve(ep('claude'))
        self.assertFalse(self.path.exists())

    def test_full_frontier_plan_within_envelope(self):
        for e in schedule():
            if e['model']=='claude': self.ledger.reserve(e)
        self.assertEqual(self.ledger.exposure,15493120)
        self.assertLess(self.ledger.exposure+2000000,25000000)

    def test_budget_cap(self):
        self.ledger.event(event='reserve',id='fixture',subholds=[3000000]*7)
        with self.assertRaises(Stop): self.ledger.event(event='reserve',id='fixture2',subholds=[1000000]*7)
        self.assertEqual(Ledger(self.path).exposure,21000000)

    def test_overrun_persisted_and_reconstructed(self):
        self.ledger.reserve(ep('claude'))
        with self.assertRaises(Stop): self.ledger.event(event='settle',id='call',episode=ep('claude')['id'],slot=0,actual=100000)
        new=Ledger(self.path)
        self.assertTrue(new.blocked)
        self.assertEqual(new.spent,100000)
        self.assertGreater(new.exposure,195072)

    def test_duplicate_settlement_rejected(self):
        self.ledger.reserve(ep('claude'))
        kw=dict(event='settle',id='call',episode=ep('claude')['id'],slot=0,actual=0)
        self.ledger.event(**kw)
        with self.assertRaises(Stop): self.ledger.event(**kw)

    def test_torn_ledger_rejected(self):
        self.path.write_text('{"event":"reserve"}')
        with self.assertRaises(Stop): Ledger(self.path)

    def test_negative_boolean_noninteger_cost_rejected(self):
        for value in [-1,True,1.5]:
            with self.assertRaises(Stop): self.ledger.event(event='reserve',id='fixture',subholds=[value]*7)

    def test_crash_time_charged_full(self):
        path=self.path.with_name('time.jsonl')
        timer=ActiveTime(path,7200)
        timer.begin('fixture',420)
        self.assertEqual(ActiveTime(path,7200).charged,420)

    def test_time_cap_persistent_across_resumes(self):
        path=self.path.with_name('time.jsonl')
        timer=ActiveTime(path,500)
        timer.begin('fixture',420)
        resumed=ActiveTime(path,500)
        with self.assertRaises(Stop): resumed.begin('fixture2',100)

    def test_exclusive_evidence_creation(self):
        save(self.path,{'fixture':True})
        with self.assertRaises(FileExistsError): save(self.path,{'fixture':False})
        self.assertEqual(read(self.path),{'fixture':True})


class LocalTransportTests(unittest.TestCase):
    def metadata(self,path,body=None,timeout=10):
        if path=='/api/tags':
            return canonical({'models':[dict(name=PINS['qwen7b'][0],digest=PINS['qwen7b'][1])]}).encode()
        if path=='/api/show':
            expected=read(Path(__file__).resolve().parents[1]/'deviations/d2/evidence/local-identity.json')['models']['qwen7b']
            return canonical(dict(template=expected['template'],system=expected['system'],model_info={'qwen2.context_length':32768})).encode()
        if path=='/api/version':
            return b'{"version":"FIXTURE"}'
        raise AssertionError('unexpected endpoint: '+path)

    def test_metadata_only_readiness(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('bob_collect.http',side_effect=self.metadata) as network:
                import shutil
                source=Path(__file__).resolve().parents[1]/'deviations/d2/evidence'
                target=Path(temp)/'deviations/d2/evidence'
                shutil.copytree(source/'models',target/'models')
                shutil.copy2(source/'local-identity.json',target/'local-identity.json')
                adapter=LocalAdapter(temp,'qwen7b')
                adapter.check()
                self.assertTrue(adapter.ready)
                self.assertEqual(network.call_count,3)
                value=read(Path(temp)/'collection/runtime/qwen7b.json')
                self.assertLessEqual(value['context_byte_allowance'],8192)

    def test_wrong_pin_stops_before_generation(self):
        def fake(path,body=None,timeout=10):
            raw=self.metadata(path,body,timeout)
            if path=='/api/tags':
                value=strict_load(raw); value['models'][0]['digest']='wrong'; return canonical(value).encode()
            return raw
        with tempfile.TemporaryDirectory() as temp,patch('bob_collect.http',side_effect=fake):
            with self.assertRaises(Stop): LocalAdapter(temp,'qwen7b').check()

    def test_oversized_context_stops_before_generation(self):
        def fake(path,body=None,timeout=10):
            raw=self.metadata(path,body,timeout)
            if path=='/api/show':
                value=strict_load(raw); value['template']='X'*8192; return canonical(value).encode()
            return raw
        with tempfile.TemporaryDirectory() as temp,patch('bob_collect.http',side_effect=fake):
            with self.assertRaises(Stop): LocalAdapter(temp,'qwen7b').check()

    def test_actual_context_mismatch_preserves_generation(self):
        def fake(path,body=None,timeout=10):
            if path=='/api/generate': return b'{"fixture":"raw-generation"}'
            if path=='/api/ps': return canonical({'models':[dict(name=PINS['qwen7b'][0],context_length=4096)]}).encode()
            raise AssertionError('unexpected endpoint')
        with tempfile.TemporaryDirectory() as temp,patch('bob_collect.http',side_effect=fake):
            adapter=LocalAdapter(temp,'qwen7b'); adapter.ready=True
            result=adapter.generate({},'action',0)
            self.assertEqual(result['stdout'],b'{"fixture":"raw-generation"}')
            self.assertEqual(result['returncode'],1)

    def test_http_has_wall_timeout_before_network(self):
        import time
        def slow(*args,**kwargs):
            time.sleep(.2)
            raise AssertionError('wall timeout did not interrupt')
        with patch('bob_collect.urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=slow
            began=time.monotonic()
            with self.assertRaises(TimeoutError): http('/FIXTURE',timeout=.01)
            self.assertLess(time.monotonic()-began,.15)


class DispatchGuardTests(unittest.TestCase):
    def test_drift_guard_precedes_transport(self):
        e=ep()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ledger=Ledger(root/'collection/cost.jsonl')
            timer=ActiveTime(root/'collection/time.jsonl',43200)
            fake=FakeTransport(e)
            def changed():
                raise Stop('fixture source drift')
            with self.assertRaises(Stop):
                run_episode(root,e,fake,ledger,timer,'FIXTURE',guard=changed)
            self.assertEqual(fake.calls,0)
            self.assertEqual(list((root/'collection/starts').glob('*.json')),[])
