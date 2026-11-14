"""D1 offline tests. All Git/server/process effects are mocked; no inference."""
import copy
import datetime as dt
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,canonical,sha,strict_load,subholds,sizing
from bob_collect import (Stop,read,save,Ledger,ActiveTime,run_episode,frontier_gate,
                         ClaudeAdapter,collect)
from bob_freeze import (inventory,verify,freeze_d1,active_freeze,attest,push_record,
                        push_gate,check_d1_push,ORIGINAL_FREEZE_SHA256,REPOSITORY)
from bob_offline import FakeTransport,write
from bob_audit import audit_episode,reconcile_ledger


COMMIT='a'*40


def activity():
    return dict(id=123,activity_type='push',ref='refs/heads/main',after=COMMIT,
                timestamp='2024-01-01T00:00:00Z')


class PushRecordTests(unittest.TestCase):
    def test_activity_and_pushevent(self):
        event=activity()
        result=push_record(event,COMMIT)
        self.assertEqual(result['github_time'],event['timestamp'])
        self.assertEqual(result['source_api'],'/repos/Robin84Bran/research/activity')
        other=dict(id='event',type='PushEvent',repo=dict(name=REPOSITORY),
                   payload=dict(head=COMMIT,ref=event['ref']),created_at=event['timestamp'])
        self.assertEqual(push_record(other,COMMIT)['source_api'],'/repos/Robin84Bran/research/events')
        other['repo']['name']='wrong/repository'
        with self.assertRaises(Stop): push_record(other,COMMIT)

    def test_missing_and_conflicting_fields(self):
        for key in activity():
            with self.subTest(missing=key):
                event=activity(); del event[key]
                with self.assertRaises(Stop): push_record(event,COMMIT)
        for key,value in [('activity_type','force_push'),('ref','refs/tags/v1'),
                          ('ref','refs/heads/'),('after','b'*40),('id',None),
                          ('timestamp','2024-01-01T00:00:00'),('timestamp','bad'),
                          ('timestamp',None),('timestamp','2999-01-01T00:00:00Z')]:
            with self.subTest(key=key,value=value):
                event=activity(); event[key]=value
                with self.assertRaises(Stop): push_record(event,COMMIT)
        for commit in ['short',None,'A'*40]:
            with self.assertRaises(Stop): push_record(activity(),commit)
        for event in [[],None,dict(sha=COMMIT),dict(activity_type='push')]:
            with self.assertRaises(Stop): push_record(event,COMMIT)


class D1Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-d1-')
        self.root=Path(self.temp.name).resolve()/'canonical'
        # Reconstruct the exact D1 source fixture from its immutable inventory.
        # Current D2 files are deliberately absent from this historical test.
        manifest=read(ROOT/'freeze-d1.json')
        for name in list(manifest['files'])+['freeze.json']:
            archived=ROOT/'deviations/d2/original'/name
            source=archived if archived.is_file() else ROOT/name
            target=self.root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes())
        self.bind_report()
        freeze_d1(self.root)
        # Only this synthetic test freeze uses a historical timestamp, allowing
        # deterministic saved server fixtures without a clock/network request.
        manifest=read(self.root/'freeze-d1.json')
        manifest['frozen_utc']='2000-01-01T00:00:00+00:00'
        write(self.root/'freeze-d1.json',manifest)
        self.clone=Path(self.temp.name).resolve()/'research-clone'
        self.clone.mkdir()
        self.event=Path(self.temp.name)/'raw-activity.json'
        self.raw=b'  '+canonical(activity()).encode()+b'\n\n'
        self.event.write_bytes(self.raw)
        self.overrides={}
        self.commands=[]

    def tearDown(self):
        self.temp.cleanup()

    def bind_report(self):
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,
              python_tests=1,toy_tests=0,source_sha256=sha(canonical(inventory(self.root)).encode())))

    def git(self,argv,**kwargs):
        self.commands.append(argv)
        self.assertEqual(argv[:3],['git','-C',str(self.clone)])
        args=tuple(argv[3:])
        if args in self.overrides:
            raw=self.overrides[args]
        elif args==('rev-parse','--show-toplevel'): raw=str(self.clone).encode()
        elif args==('rev-parse','HEAD'): raw=COMMIT.encode()
        elif args==('remote','get-url','origin'): raw=b'https://github.com/Robin84Bran/research.git'
        elif args==('ls-remote','origin','refs/heads/main'): raw=(COMMIT+'\trefs/heads/main\n').encode()
        elif args[0]=='show':
            prefix=COMMIT+':bridge-or-bus/'
            self.assertTrue(args[1].startswith(prefix))
            raw=(self.root/args[1][len(prefix):]).read_bytes()
        else: raise AssertionError('unexpected Git operation: '+str(args))
        return subprocess.CompletedProcess(argv,0,stdout=raw)

    def attest(self,repo_path='bridge-or-bus'):
        with patch('bob_freeze.subprocess.run',side_effect=self.git):
            return attest(self.root,self.event,COMMIT,self.clone,repo_path)


class AmendmentTests(D1Fixture):
    def test_parent_scientific_inputs_and_exact_inventory(self):
        f=verify(self.root)
        self.assertEqual(active_freeze(self.root),'freeze-d1.json')
        self.assertEqual(sha((self.root/'freeze.json').read_bytes()),ORIGINAL_FREEZE_SHA256)
        for name,expected in read(self.root/'freeze.json')['files'].items():
            if name not in {'bob.py','bob_collect.py','bob_freeze.py','tests/test_freeze.py','tests/test_collect.py'}:
                self.assertEqual(f['files'][name],expected,name)
        self.assertEqual(f['frontier_reservation_micro_usd'],15493120)

    def test_parent_replacement_rejected(self):
        p=self.root/'freeze.json'; p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(Stop): verify(self.root)

    def test_postfreeze_drift_and_undeclared_file_rejected(self):
        p=self.root/'bob_core.py'; original=p.read_bytes(); p.write_bytes(original+b'\n')
        with self.assertRaises(Stop): verify(self.root)
        p.write_bytes(original)
        (self.root/'unlisted.py').write_text('x=1\n')
        with self.assertRaises(Stop): verify(self.root)

    def test_scientific_drift_cannot_be_refrozen(self):
        (self.root/'freeze-d1.json').unlink()
        p=self.root/'config/prompts.json'; p.write_bytes(p.read_bytes()+b'\n')
        self.bind_report()
        with self.assertRaisesRegex(Stop,'scientific'): freeze_d1(self.root)

    def test_unrelated_collector_change_rejected(self):
        (self.root/'freeze-d1.json').unlink()
        p=self.root/'bob_collect.py'
        p.write_text(p.read_text().replace('cost<0:', 'cost<=0:'))
        self.bind_report()
        with self.assertRaisesRegex(Stop,'unrelated collector'): freeze_d1(self.root)

    def test_d1_exclusive_and_requires_tested_source(self):
        before=(self.root/'freeze-d1.json').read_bytes()
        with self.assertRaises(Stop): freeze_d1(self.root)
        self.assertEqual(before,(self.root/'freeze-d1.json').read_bytes())
        (self.root/'freeze-d1.json').unlink()
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256='wrong'))
        with self.assertRaisesRegex(Stop,'passing tests'): freeze_d1(self.root)

    def test_d1_preinference_only(self):
        (self.root/'freeze-d1.json').unlink()
        save(self.root/'collection/calls/attempt.json',dict(usage=None))
        with self.assertRaisesRegex(Stop,'pre-inference'): freeze_d1(self.root)

    def test_d1_metadata_cannot_change_budget_or_design(self):
        p=self.root/'freeze-d1.json'; f=read(p)
        for key in ['frontier_reservation_micro_usd','frontier_episodes','maximum_generations','new_model_calls']:
            altered=dict(f); altered[key]+=1; write(p,altered)
            with self.assertRaises(Stop): verify(self.root)
        write(p,f)
        self.assertEqual(verify(self.root)['deviation'],'D1')

    def test_empirical_gate_releases_without_claiming_verified_rates(self):
        with patch('bob_collect.subprocess.run') as process:
            frontier_gate(self.root)
            process.assert_not_called()
        historical=read(self.root/'evidence/claude-transport.json')
        self.assertEqual(historical['current_rates_status'],'UNKNOWN')
        self.assertEqual(historical['accounted_output_enforcement_status'],'UNKNOWN')

    def test_changed_source_stops_before_adapter_process(self):
        p=self.root/'bob.py'; p.write_bytes(p.read_bytes()+b'\n')
        with patch('bob_collect.subprocess.run') as process:
            with self.assertRaises(Stop): ClaudeAdapter(self.root,'/not/executed')
            process.assert_not_called()


class AttestationTests(D1Fixture):
    def test_activity_raw_preserved_only_in_canonical_root(self):
        push=self.attest()
        self.assertEqual((self.root/'collection/push-event.json').read_bytes(),self.raw)
        self.assertEqual(push['evidence_sha256'],sha(self.raw))
        self.assertEqual(push['freeze_sha256'],sha((self.root/'freeze-d1.json').read_bytes()))
        self.assertEqual(push['original_freeze_sha256'],ORIGINAL_FREEZE_SHA256)
        self.assertFalse((self.clone/'collection').exists())
        self.assertTrue(self.commands)
        with patch('bob_freeze.subprocess.run') as process:
            self.assertEqual(push_gate(self.root,verify(self.root)),push)
            process.assert_not_called()

    def test_pushevent_supported(self):
        a=activity()
        self.event.write_text(canonical(dict(type='PushEvent',id='event',repo=dict(name=REPOSITORY),
                  payload=dict(after=COMMIT,ref=a['ref']),created_at=a['timestamp'])))
        self.assertTrue(self.attest()['source_api'].endswith('/events'))

    def test_receipt_create_once(self):
        self.attest()
        before=(self.root/'collection/push.json').read_bytes()
        with self.assertRaises(Stop): self.attest()
        self.assertEqual(before,(self.root/'collection/push.json').read_bytes())
        self.assertEqual((self.root/'collection/push-event.json').read_bytes(),self.raw)

    def test_git_head_origin_ref_and_frozen_blob_mismatches(self):
        cases=[(('rev-parse','HEAD'),b'b'*40),
               (('remote','get-url','origin'),b'https://github.com/wrong/research.git'),
               (('ls-remote','origin','refs/heads/main'),b'b'*40+b'\trefs/heads/main\n'),
               (('show',COMMIT+':bridge-or-bus/freeze.json'),b'wrong-parent'),
               (('show',COMMIT+':bridge-or-bus/freeze-d1.json'),b'wrong-d1'),
               (('show',COMMIT+':bridge-or-bus/config/prompts.json'),b'wrong-prompt')]
        for args,raw in cases:
            with self.subTest(args=args):
                self.overrides={args:raw}
                with self.assertRaises(Stop): self.attest()
                self.assertFalse((self.root/'collection/push.json').exists())
        self.overrides={}

    def test_invalid_repo_path_stops_before_git(self):
        for path in ['', '../bridge-or-bus','/absolute','path:escape','.',r'..\escape']:
            with self.subTest(path=path):
                with self.assertRaises(Stop): self.attest(path)
        self.assertFalse(self.commands)

    def test_server_record_must_follow_d1_freeze(self):
        event=activity(); event['timestamp']='1999-01-01T00:00:00Z'
        self.event.write_text(canonical(event))
        with self.assertRaisesRegex(Stop,'predates'): self.attest()
        self.assertFalse((self.root/'collection/push-event.json').exists())

    def test_evidence_and_receipt_tampering(self):
        push=self.attest()
        for key,value in [('commit','b'*40),('freeze_sha256','b'*64),
                          ('original_freeze_sha256','b'*64),('github_time','2025-01-01T00:00:00Z'),
                          ('server_event_id',999),('repo','wrong/repo'),
                          ('evidence_file','../external.json'),('remote_ref','refs/heads/other')]:
            with self.subTest(key=key):
                altered=dict(push); altered[key]=value
                with self.assertRaises(Stop): check_d1_push(self.root,verify(self.root),altered)
        p=self.root/'collection/push-event.json'; p.write_bytes(self.raw+b' ')
        with self.assertRaises(Stop): push_gate(self.root,verify(self.root))

    def test_push_before_call_and_d1_start_binding(self):
        push=self.attest()
        start=self.root/'collection/starts/fixture.json'
        write(start,dict(started='2023-01-01T00:00:00Z',amendment_freeze_sha256=push['freeze_sha256']))
        with self.assertRaises(Stop): push_gate(self.root,verify(self.root))
        write(start,dict(started='2025-01-01T00:00:00Z',amendment_freeze_sha256='wrong'))
        with self.assertRaises(Stop): push_gate(self.root,verify(self.root))
        write(start,dict(started='2025-01-01T00:00:00Z',amendment_freeze_sha256=push['freeze_sha256']))
        self.assertEqual(push_gate(self.root,verify(self.root)),push)

    def test_separate_clone_required(self):
        self.overrides={('rev-parse','--show-toplevel'):str(self.root).encode()}
        with self.assertRaises(Stop): self.attest()


class CollectorIntegrationTests(D1Fixture):
    def collection(self,mode=None):
        ep=next(e for e in read(self.root/'config/order.json') if e['model']=='claude')
        fake=FakeTransport(ep,mode=mode)
        original_read=read
        def fixture_plan(path):
            if Path(path)==self.root/'config/order.json':
                return [ep]  # Small fake plan; the on-disk frozen plan is intact.
            return original_read(path)
        with patch('bob_collect.read',side_effect=fixture_plan), \
             patch('bob_collect.ClaudeAdapter',return_value=fake), \
             patch('bob_collect.http') as network:
            if mode:
                with self.assertRaises(Stop): collect(self.root,('claude',))
                first_count=fake.calls
                with self.assertRaises(Stop): collect(self.root,('claude',))
                self.assertEqual(fake.calls,first_count)
            else:
                collect(self.root,('claude',))
                first_count=fake.calls
                collect(self.root,('claude',))
                self.assertEqual(fake.calls,first_count)
            network.assert_not_called()
        return ep,fake

    def test_attested_d1_dispatches_fake_then_resumes_without_resend(self):
        push=self.attest()
        ep,fake=self.collection()
        self.assertGreater(fake.calls,1)
        saved=read(self.root/'collection/episodes'/f"{ep['id']}.json")
        audit_episode(self.root,ep,saved,ORIGINAL_FREEZE_SHA256)
        self.assertEqual(push_gate(self.root,verify(self.root)),push)

    def test_first_envelope_failure_blocks_collector_resume(self):
        self.attest()
        ep,fake=self.collection('missing_payload')
        self.assertEqual(fake.calls,1)
        self.assertTrue(Ledger(self.root/'collection/cost.jsonl').blocked)
        saved=read(self.root/'collection/episodes'/f"{ep['id']}.json")
        self.assertEqual(len(saved['calls']),1)


class EnvelopeAndAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-d1-envelope-')
        self.root=Path(self.temp.name)
        self.ep=dict(id='claude-00-unit-registry',model='claude',seed=0,world='unit',arm='registry')
        self.ledger=Ledger(self.root/'collection/cost.jsonl')
        self.timer=ActiveTime(self.root/'collection/time.jsonl',7200)

    def tearDown(self):
        self.temp.cleanup()

    def run_fake(self,change=None,raw_change=None):
        base=FakeTransport(self.ep)
        class Fake:
            def generate(inner,*args):
                result=base.generate(*args)
                env=strict_load(result['stdout'])
                env['usage'].update(input_tokens=100,output_tokens=10)
                env['total_cost_usd']=0.0006
                if change is not None: change(env)
                raw=canonical(env).encode()
                result['stdout']=raw_change(raw) if raw_change else raw
                return result
        try:
            return run_episode(self.root,self.ep,Fake(),self.ledger,self.timer,ORIGINAL_FREEZE_SHA256)
        finally:
            self.generated=base.calls

    def test_valid_first_payload_continues_and_audits_actual_settlement(self):
        saved=self.run_fake()
        self.assertEqual(self.generated,6)
        self.assertEqual(self.ledger.spent,3600)
        self.assertEqual(self.ledger.exposure,3600)
        audit_episode(self.root,self.ep,saved,ORIGINAL_FREEZE_SHA256)
        self.assertEqual(reconcile_ledger(self.root,{self.ep['id']:saved})['spent_micro_usd'],3600)

    def test_first_missing_payload_stops_but_counts_and_settles(self):
        def missing(env):
            env['result']=canonical(env.pop('structured_output'))
        with self.assertRaises(Stop): self.run_fake(missing)
        self.assertEqual(self.generated,1)
        ledger=Ledger(self.ledger.path)
        self.assertEqual(ledger.spent,600)
        self.assertTrue(ledger.blocked)
        calls=list((self.root/'collection/calls').glob('*.json'))
        self.assertEqual(len(calls),1)
        self.assertEqual(read(calls[0])['usage']['micro_usd'],600)
        with self.assertRaises(Stop): ledger.reserve(dict(self.ep,id='another'))

    def test_first_string_or_array_payload_stops(self):
        # Each scenario gets a fresh project, preventing retry of any start.
        for value in ['{}',[],None]:
            with tempfile.TemporaryDirectory() as temp:
                original=self.root,self.ledger,self.timer
                self.root=Path(temp)
                self.ledger=Ledger(self.root/'collection/cost.jsonl')
                self.timer=ActiveTime(self.root/'collection/time.jsonl',7200)
                with self.assertRaises(Stop): self.run_fake(lambda e:e.update(structured_output=value))
                self.assertEqual(self.generated,1)
                self.root,self.ledger,self.timer=original

    def test_duplicate_payload_is_saved_and_unknown_usage_holds(self):
        with self.assertRaises(Stop):
            self.run_fake(raw_change=lambda raw:raw[:-1]+b',"structured_output":{}}')
        self.assertEqual(self.generated,1)
        self.assertTrue(Ledger(self.ledger.path).blocked)
        self.assertEqual(self.ledger.exposure,sum(x['micro_usd'] for x in subholds(self.ep)))
        receipt=read(next((self.root/'collection/calls').glob('*.json')))
        self.assertIsNone(receipt['usage'])
        self.assertTrue(receipt['response_sha256'])

    def test_missing_cost_stops_and_retains_holds(self):
        with self.assertRaises(Stop): self.run_fake(lambda e:e.pop('total_cost_usd'))
        self.assertEqual(self.generated,1)
        self.assertEqual(self.ledger.exposure,sum(x['micro_usd'] for x in subholds(self.ep)))
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_token_overrun_settles_known_actual_before_stop(self):
        with self.assertRaises(Stop): self.run_fake(lambda e:e['usage'].update(output_tokens=577))
        self.assertEqual(self.generated,1)
        self.assertEqual(Ledger(self.ledger.path).spent,600)
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_failed_outer_envelope_stops_even_with_payload_and_known_usage(self):
        with self.assertRaises(Stop): self.run_fake(lambda e:e.update(subtype='error',is_error=True))
        self.assertEqual(self.generated,1)
        self.assertEqual(Ledger(self.ledger.path).spent,600)
        self.assertTrue(Ledger(self.ledger.path).blocked)

    def test_d1_start_additionally_binds_amendment(self):
        # A fixture marker suffices for the shared harness; live guard verifies it.
        save(self.root/'freeze-d1.json',{'fixture':'not a live manifest'})
        saved=self.run_fake()
        expected=sha((self.root/'freeze-d1.json').read_bytes())
        for path in (self.root/'collection/starts').glob('*.json'):
            start=read(path)
            self.assertEqual(start['freeze_sha256'],ORIGINAL_FREEZE_SHA256)
            self.assertEqual(start['amendment_freeze_sha256'],expected)
            self.assertEqual(start['deviation'],'D1')
        audit_episode(self.root,self.ep,saved,ORIGINAL_FREEZE_SHA256)

    def test_rolling_settlement_reuses_only_released_holds(self):
        # A prospective full-plan hold is unnecessary: completed actual charges
        # replace their holds while all other reservations remain counted.
        self.ledger.reserve(self.ep)
        initial=self.ledger.exposure
        self.ledger.event(event='settle',id='paid',episode=self.ep['id'],slot=0,actual=1234)
        self.assertEqual(self.ledger.exposure,initial-subholds(self.ep)[0]['micro_usd']+1234)
        another=dict(self.ep,id='next')
        self.ledger.reserve(another)
        self.assertEqual(self.ledger.exposure,initial-subholds(self.ep)[0]['micro_usd']+1234+sum(x['micro_usd'] for x in subholds(another)))

    def test_actual_spend_plus_open_holds_and_protected_reserve_caps(self):
        # 23 dollars open + 2 protected exactly fits the frontier envelope.
        self.ledger.event(event='reserve',id='full',subholds=[23000000]+[0]*6)
        with self.assertRaises(Stop): self.ledger.reserve(self.ep)
        self.ledger.event(event='settle',id='paid',episode='full',slot=0,actual=22000000)
        self.ledger.reserve(self.ep)
        self.assertLessEqual(self.ledger.exposure+2000000,25000000)
        self.assertLess(self.ledger.exposure+2000000,39000000)

    def test_historical_basis_and_frozen_total_stay_empirical(self):
        basis=read(ROOT/'evidence/d1-cost-basis.json')
        self.assertIn('max 826',basis['measured']['prices']['overhead_source'])
        self.assertEqual(sizing()['frontier_micro_usd'],15493120)
        self.assertEqual(sizing()['prices']['status'],'UNKNOWN')
        self.assertEqual(sizing()['output_hold'],576)
