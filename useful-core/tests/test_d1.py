"""D1 offline evidence and resume tests. No real CLI, model, Git or network calls."""
import copy
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from uc_core import ROOT,canonical,sha,render,reserve,episode_reservation
from uc_store import Stop,Ledger,ActiveTime,Journal,read,save
from uc_offline import Fake
from uc_transport import decode,usage,cost_micro
from uc_usage_limit import is_usage_limit,reset_time,run_paid_episode,audit_nonstarts,check_prefixes,prefixes
from uc_analysis import audit_episode,audit_ledger,audit_contract,analyze

REFUSAL=read(ROOT/'fixtures/claude-usage-limit.json')


class Limited(Fake):
    def __init__(self,position=1,limits=1,envelope=None,raw_changes=None):
        super().__init__('claude');self.position=position;self.limits=limits
        self.envelope=envelope or REFUSAL;self.raw_changes=raw_changes or {};self.requests=[]
    def preflight(self,actor):return dict(offline=True)
    def generate(self,request,work):
        self.requests.append((self.current[3],canonical(request)))
        if self.current[3]==self.position and self.limits:
            self.limits-=1
            return dict(stdout=canonical(self.envelope).encode(),stderr=b'',returncode=1,**self.raw_changes)
        return super().generate(request,work)


class ClassifierTests(unittest.TestCase):
    def test_exact_zero_usage_fixture_and_reset(self):
        self.assertTrue(is_usage_limit(REFUSAL,dict(returncode=1)))
        self.assertEqual(reset_time(REFUSAL,'2026-11-11T13:00:00+00:00'),'2026-11-11T13:30:00+00:00')
        self.assertEqual(reset_time(REFUSAL,'2026-11-11T14:00:00+00:00'),'2026-11-12T13:30:00+00:00')
    def test_near_misses_and_ambiguous_envelopes_keep_frozen_handling(self):
        mutations=[lambda e:e.update(total_cost_usd=.001),lambda e:e.update(total_cost_usd=False),
            lambda e:e.update(api_error_status=500),lambda e:e.update(is_error=False),lambda e:e.pop('usage'),
            lambda e:e.update(result='some other error'),lambda e:e.update(structured_output={'op':'read'}),lambda e:e.update(structured_output={}),
            lambda e:e.update(modelUsage={'claude-opus-5-5':{'inputTokens':1}}),
            lambda e:e['usage'].update(output_tokens_details={'thinking_tokens':1}),
            lambda e:e['usage'].update(server_tool_use={'web_search_requests':1})]
        for key in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'):
            mutations.extend([lambda e,k=key:e['usage'].update({k:1}),lambda e,k=key:e['usage'].pop(k),lambda e,k=key:e['usage'].update({k:False})])
        for mutation in mutations:
            env=copy.deepcopy(REFUSAL);mutation(env)
            self.assertFalse(is_usage_limit(env,dict(returncode=1)),env)
        for raw in ({'returncode':0},{'returncode':None},{'returncode':1,'transport_error':'timeout'},{'returncode':1,'harness_error':'bug'}):
            self.assertFalse(is_usage_limit(REFUSAL,raw))
    def test_real_envelope_preserves_valid_two_turn_metadata(self):
        env=read(ROOT/'fixtures/claude-real-envelope.json');self.assertFalse(is_usage_limit(env,dict(returncode=0)))
        self.assertEqual(usage(env,'claude'),(1602,199));self.assertEqual(cost_micro(1602,199,env),16788)
        ep=dict(actor='claude',seed=0,framing='full');bound=reserve(render(ep,[],6,'action'),'action')
        # Fixture's schema belongs to a sibling task. Exercise all frozen metadata
        # checks, replacing only the task-specific action schema validator.
        with patch('uc_core.action',side_effect=lambda value:value):
            self.assertEqual(decode(env,dict(returncode=0),ep,'action',bound),env['structured_output'])


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.ep=dict(id='claude-fixture',actor='claude',seed=0,world='early',framing='fallback')
    def run_it(self,f):
        return run_paid_episode(self.ep,f,self.base,Ledger(self.base/'ledger.jsonl'),ActiveTime(self.base/'time.jsonl',100000),'OFFLINE-FAKE',True)
    def audit(self,result=None):
        calls=audit_episode(self.base,self.ep,result,True)
        account=audit_ledger(self.base,[self.ep],calls)
        audit_contract(self.base,calls)
        return calls,account
    def test_pause_zero_cost_no_contract_no_fatal_stop_no_model_call(self):
        f=Limited()
        with patch('uc_usage_limit.ready',return_value=False):
            result=self.run_it(f);again=self.run_it(f)
        self.assertIn('usage_limit_pause',result);self.assertIn('usage_limit_pause',again)
        self.assertEqual(len(f.requests),1)
        self.assertFalse(list(self.base.glob('STOP*.json')));self.assertFalse((self.base/'claude-contract.json').exists())
        self.assertFalse(list(self.base.glob('episodes/*/*.start.json')))
        calls,account=self.audit();self.assertEqual(calls,[]);self.assertEqual(account['settled_micro_usd'],0)
        self.assertEqual(account['outstanding_holds_micro_usd'],episode_reservation(self.ep))
        self.assertEqual(len(audit_nonstarts(self.base)),1)
    def test_identical_resume_at_first_midway_and_report(self):
        for position in (1,3,7):
            with self.subTest(position=position),tempfile.TemporaryDirectory() as temp:
                self.base=Path(temp);f=Limited(position)
                paused=self.run_it(f);self.assertIn('usage_limit_pause',paused)
                before={p.name:p.read_bytes() for p in (self.base/'episodes'/self.ep['id']).glob('*.*')}
                with patch('uc_usage_limit.ready',return_value=True):result=self.run_it(f)
                self.assertTrue(result['technically_complete'])
                for name,value in before.items():self.assertEqual((self.base/'episodes'/self.ep['id']/name).read_bytes(),value)
                self.assertEqual([d for d,r in f.requests].count(position),2)
                for earlier in set(d for d,r in f.requests if d<position):self.assertEqual([d for d,r in f.requests].count(earlier),1)
                requests=[r for d,r in f.requests if d==position];self.assertEqual(requests[0],requests[1])
                self.audit(result)
                self.assertEqual(len(audit_nonstarts(self.base)),1)
    def test_repeated_limit_same_position_releases_no_model_hold_and_counts_events(self):
        f=Limited(3,2);self.run_it(f)
        with patch('uc_usage_limit.ready',return_value=True):
            self.assertIn('usage_limit_pause',self.run_it(f));result=self.run_it(f)
        calls,account=self.audit(result)
        self.assertEqual(len(audit_nonstarts(self.base)),2);self.assertEqual(len(calls),len(result['calls']))
        self.assertEqual(account['outstanding_holds_micro_usd'],0)
        self.assertEqual(len(set(r for d,r in f.requests if d==3)),1)
        save(self.base/'OFFLINE-FAKE.json',dict(fake=True));schedule=read(ROOT/'config/episodes.json')
        schedule=[self.ep if e['actor']=='claude' and e['seed']==0 and e['world']=='early' and e['framing']=='fallback' else e for e in schedule]
        save(self.base/'config/episodes.json',schedule)
        analysis=analyze(self.base,self.base,self.base/'result.json',replicates=10,fake=True)
        self.assertEqual(analysis['operational_events']['usage_limit_refusals'],2)
        self.assertEqual(analysis['resources']['claude']['calls'],len(calls))
        self.assertTrue(next(r for r in analysis['rows'] if r['id']==self.ep['id'])['technically_complete'])
    def test_legitimate_journal_appends_allowed_prefix_tamper_rejected(self):
        f=Limited(3);self.run_it(f);pins=prefixes(self.base)
        timer=ActiveTime(self.base/'time.jsonl',100000);began=timer.begin('later-overhead',1);timer.end('later-overhead',began)
        check_prefixes(self.base,pins)
        with patch('uc_usage_limit.ready',return_value=True):result=self.run_it(f)
        self.audit(result)
        path=self.base/'ledger.jsonl';raw=path.read_bytes();path.write_bytes(raw[:-1])
        with self.assertRaises(Stop):check_prefixes(self.base,pins)
    def test_prior_history_and_identical_request_are_pinned(self):
        for filename in ('1.parsed.json','dispatches/3-0000/request.json'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as temp:
                self.base=Path(temp);f=Limited(3);self.run_it(f);n=len(f.requests)
                path=self.base/'episodes'/self.ep['id']/filename;path.write_bytes(path.read_bytes()+b' ')
                with patch('uc_usage_limit.ready',return_value=True),self.assertRaises(Stop):self.run_it(f)
                self.assertEqual(len(f.requests),n)
    def test_crash_before_pause_reconstructs_only_exact_refusal(self):
        class Crash(BaseException):pass
        f=Limited()
        with patch('uc_usage_limit.ensure_pause',side_effect=Crash),self.assertRaises(Crash):self.run_it(f)
        with patch('uc_usage_limit.ready',return_value=False):self.assertIn('usage_limit_pause',self.run_it(f))
        self.assertEqual(len(f.requests),1);self.audit()
        with patch('uc_usage_limit.ready',return_value=True):result=self.run_it(f)
        self.audit(result)
    def test_generated_error_is_content_and_unclassified_zero_error_stays_fatal(self):
        for expected_fatal,mutation in ((False,lambda e:e['usage'].update(output_tokens=1)),(True,lambda e:e.update(api_error_status=500))):
            with tempfile.TemporaryDirectory() as temp:
                self.base=Path(temp);env=copy.deepcopy(REFUSAL);mutation(env);f=Limited(envelope=env)
                result=self.run_it(f);self.assertEqual(result['fatal'],expected_fatal);self.assertEqual((self.base/'STOP.json').exists(),expected_fatal)
                self.assertEqual(audit_nonstarts(self.base),[]);self.audit(result)
    def test_partial_dispatch_or_crash_after_generation_never_resends(self):
        class Crash(BaseException):pass
        f=Limited(limits=0)
        original=save
        def crash(path,value):
            if Path(path).name=='accepted.json':raise Crash()
            return original(path,value)
        with patch('uc_usage_limit.save',side_effect=crash),self.assertRaises(Crash):self.run_it(f)
        n=len(f.requests)
        with self.assertRaises(Stop):self.run_it(f)
        self.assertEqual(len(f.requests),n)
    def test_d1_retains_existing_success_content_and_fatal_accounting(self):
        kinds=('normal','missing_payload','string_payload','bad_report','invalid_action','length',
               'missing_cost','missing_usage','wrong_model','wrong_effort','bad_turns','tools','overrun','cost_overrun','timeout')
        for kind in kinds:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                self.base=Path(temp);result=self.run_it(Fake('claude',kind))
                self.audit(result)
                expected=kind not in ('normal','missing_payload','string_payload','bad_report','invalid_action','length','bad_turns')
                self.assertEqual(result['fatal'],expected)
                self.assertEqual(audit_nonstarts(self.base),[])
    def test_real_clock_gate_and_unknown_reset_remain_paused(self):
        from uc_usage_limit import ready
        now=dt.datetime.now(dt.timezone.utc)
        self.assertTrue(ready({'reset_at':(now-dt.timedelta(seconds=1)).isoformat()}))
        self.assertFalse(ready({'reset_at':(now+dt.timedelta(seconds=60)).isoformat()}))
        self.assertFalse(ready({'reset_at':None}))
        env=copy.deepcopy(REFUSAL);env['result']="You've hit your weekly limit · resets Nov 15"
        self.assertTrue(is_usage_limit(env,dict(returncode=1)))
        self.assertIsNone(reset_time(env,now.isoformat()))
        f=Limited(envelope=env);self.assertIn('usage_limit_pause',self.run_it(f))
        self.assertIn('usage_limit_pause',self.run_it(f));self.assertEqual(len(f.requests),1)
    def test_collector_pauses_cleanly_without_stop(self):
        from uc_collect import collect
        save(self.base/'config/episodes.json',[self.ep]);(self.base/'freeze-d1.json').write_text('{}')
        f=Limited();actual=run_paid_episode
        def offline(*args,**kwargs):return actual(*args,**kwargs,fake=True)
        with patch('uc_freeze.push_gate',return_value='OFFLINE-FAKE'),patch('uc_collect.Claude',return_value=f),patch('uc_usage_limit.run_paid_episode',side_effect=offline):
            result=collect(self.base,'claude','FAKE-CLAUDE')
            self.assertEqual(result['status'],'usage-limit pause');self.assertFalse(list((self.base/'collection').glob('STOP*.json')))
            with patch('uc_usage_limit.ready',return_value=True):collect(self.base,'claude','FAKE-CLAUDE')
            n=len(f.requests);collect(self.base,'claude','FAKE-CLAUDE');self.assertEqual(len(f.requests),n)


class LineageTests(unittest.TestCase):
    def setUp(self):
        from uc_freeze import freeze,freeze_a1,prepare
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);base=self.root/'collection'
        prepare(self.root)
        self.episodes=[dict(id='local-1',actor='qwen7b',seed=0,world='early',framing='full'),dict(id='claude-1',actor='claude',seed=0,world='early',framing='full')]
        (self.root/'config/episodes.json').write_text(canonical(self.episodes)+'\n')
        (self.root/'uc_collect.py').write_text('# original\n')
        with patch('uc_freeze.identities',return_value={}):freeze(self.root)
        original=sha((self.root/'freeze.json').read_bytes())
        for name in ('uc_manifest.PARENT_SHA256','uc_freeze.PARENT_SHA256'):
            p=patch(name,original);p.start();self.addCleanup(p.stop)
        archive=self.root/'deviations/a1/original/uc_collect.py';archive.parent.mkdir(parents=True);archive.write_bytes((self.root/'uc_collect.py').read_bytes())
        (self.root/'uc_collect.py').write_text('# A1\n')
        with patch('uc_freeze.identities',return_value={}):freeze_a1(self.root)
        self.a1=sha((self.root/'freeze-a1.json').read_bytes())
        p=patch('uc_lineage.A1_SHA256',self.a1);p.start();self.addCleanup(p.stop)
        a1=read(self.root/'freeze-a1.json');pushed=dt.datetime.now(dt.timezone.utc).isoformat();commit='a'*40
        event=dict(activity_type='push',id=17,after=commit,ref='refs/heads/main',timestamp=pushed)
        save(base/'push-event.json',event)
        save(base/'push.json',dict(repo='Robin84Bran/research',source_api='/repos/Robin84Bran/research/activity',freeze_file='freeze-a1.json',freeze_sha256=self.a1,
            manifest_sha256=a1['content_sha256'],event_sha256=sha((base/'push-event.json').read_bytes()),commit=commit,remote_ref=event['ref'],pushed_at=pushed,server_event_id=17))
        save(base/'episodes/local-1/1.start.json',dict(id='local-1-1',freeze_sha256=self.a1,started_at=dt.datetime.now(dt.timezone.utc).isoformat()))
        save(base/'episodes/local-1/episode.json',dict(episode=self.episodes[0]))
        t=ActiveTime(base/'local-time.jsonl',43200);began=t.begin('local-1',2);t.end('local-1',began)
        files={p.relative_to(base).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in base.rglob('*') if p.is_file()}
        save(self.root/'deviations/d1/collection-baseline.json',dict(files=files))
        archive=self.root/'deviations/d1/original/uc_collect.py';archive.parent.mkdir(parents=True);archive.write_bytes((self.root/'uc_collect.py').read_bytes())
        (self.root/'uc_collect.py').write_text('# D1\n')
    def seal(self):
        from uc_freeze import freeze_d1
        return freeze_d1(self.root)
    def test_post_push_local_attest_preserves_parent_and_orders_new_starts(self):
        from uc_lineage import attest_d1
        from uc_freeze import verify,push_gate
        from uc_analysis import audit_provenance
        old=(self.root/'collection/push.json').read_bytes();digest=self.seal()
        self.assertEqual(verify(self.root),digest)
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        self.assertEqual(attest_d1(self.root),digest)
        self.assertEqual(push_gate(self.root),digest);self.assertEqual(audit_provenance(self.root,self.root/'collection'),digest)
        self.assertEqual((self.root/'collection/push.json').read_bytes(),old)
        save(self.root/'collection/episodes/claude-1/1.start.json',dict(id='claude-1-1',freeze_sha256=digest,started_at=dt.datetime.now(dt.timezone.utc).isoformat()))
        self.assertEqual(push_gate(self.root),digest)
        p=self.root/'collection/episodes/claude-1/1.start.json';value=read(p);value['freeze_sha256']=self.a1;p.write_text(canonical(value))
        with self.assertRaises(Stop):push_gate(self.root)
    def test_science_parent_and_preexisting_evidence_cannot_change(self):
        from uc_freeze import freeze_d1
        for name in ('config/design.json','deviations/d1/original/uc_collect.py'):
            p=self.root/name;raw=p.read_bytes();p.write_bytes(raw+b' ')
            with self.assertRaises(Stop):freeze_d1(self.root)
            p.write_bytes(raw)
        p=self.root/'collection/episodes/local-1/episode.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(Stop):self.seal()
    def test_no_reseal_or_new_d1_dispatch_before_attestation(self):
        from uc_lineage import attest_d1
        self.seal()
        with self.assertRaises(FileExistsError):self.seal()
        save(self.root/'collection/episodes/claude-1/dispatches/1-0000/start.json',dict(id='claude-1-1-dispatch-0000',started_at=dt.datetime.now(dt.timezone.utc).isoformat()))
        with self.assertRaises(Stop):attest_d1(self.root)
    def test_baseline_valid_prefix_accepts_growth_rejects_tail_damage(self):
        from uc_lineage import attest_d1
        from uc_freeze import push_gate
        self.seal();attest_d1(self.root)
        t=ActiveTime(self.root/'collection/local-time.jsonl',43200);began=t.begin('later',1);t.end('later',began)
        self.assertTrue(push_gate(self.root))
        p=self.root/'collection/local-time.jsonl';p.write_bytes(p.read_bytes()[:-1])
        with self.assertRaises(Stop):push_gate(self.root)
