"""Synthetic zero-usage fixture plus retained real-envelope regression; no model calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, World, canonical, render, reservation, episode_reservation, sha
from ps_io import Stop, UsageLimitPause, Ledger, read, save
from ps_transport import usage_limit_refusal, decode
from ps_usage_limit import call_location, reset_time
from ps_collect import collect
from ps_analysis import score, audit_accounting
from ps_offline import Fake
from test_v02 import episode


class UsageLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)/'fake'
        self.raw=read(ROOT/'fixtures/usage-limit-refusal.json');self.ep=episode()
    def tearDown(self): self.tmp.cleanup()
    def collect(self,fake):
        return collect(ROOT,'claude',fake_transport=fake,output=self.base,episodes=[self.ep])
    def limited(self,index=0,count=1):
        remaining=[count]
        def mutate(raw,ep,i):
            if i==index and remaining[0]:
                remaining[0]-=1;return copy.deepcopy(self.raw)
            return raw
        return Fake(mutate=mutate)
    def test_fixture_zero_refusal_is_nonstart(self):
        self.assertTrue(usage_limit_refusal(self.raw))
        with self.assertRaises(UsageLimitPause): decode(self.raw,self.ep,World(self.ep).payload(),reservation('keyed','write'))
    def test_other_errors_and_nonzero_usage_never_nonstart(self):
        original=read(ROOT/'fixtures/usage-limit-refusal.json')
        for key,value in [('api_error_status',500),('api_error_status','429'),('is_error',False),('total_cost_usd',.001),('total_cost_usd',None),('total_cost_usd',True),('result','rate limited'),('structured_output',{'slot':1,'note':'x'}),('modelUsage',{'model':{'outputTokens':1}})]:
            e=__import__('json').loads(original['stdout']);e[key]=value
            with self.subTest(key=key),self.assertRaises(Stop):
                raw={**original,'stdout':canonical(e)};self.assertFalse(usage_limit_refusal(raw));decode(raw,self.ep,World(self.ep).payload(),reservation('keyed','write'))
        for key in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'):
            for value in (1,None,True):
                e=__import__('json').loads(original['stdout']);e['usage'][key]=value
                self.assertFalse(usage_limit_refusal({**original,'stdout':canonical(e)}))
    def test_byte_conflicts_and_duplicate_envelopes_are_not_nonstarts(self):
        import base64
        for raw in ({**self.raw,'stdout_b64':base64.b64encode(b'other').decode()},
                    {**self.raw,'transport_error':'timeout'},
                    {**self.raw,'stdout':self.raw['stdout'][:-1]+',"is_error":true}'},
                    {**self.raw,'returncode':None}): self.assertFalse(usage_limit_refusal(raw))
    def test_reset_is_timezone_aware_and_unknown_stays_paused(self):
        self.assertEqual(reset_time(self.raw,'2026-11-11T13:00:00+00:00'),'2026-11-11T13:30:00+00:00')
        e=__import__('json').loads(self.raw['stdout']);e['result']="You've hit your 5-hour limit · resets tomorrow (Asia/Hong_Kong)"
        self.assertIsNone(reset_time({**self.raw,'stdout':canonical(e)},'2026-11-11T13:00:00+00:00'))
    def test_pause_zero_settlement_no_seal_no_model_failure(self):
        fake=self.limited();result=self.collect(fake)
        self.assertEqual(result['status'],'usage-limit pause');self.assertEqual(fake.calls,1)
        ledger=Ledger(self.base/'ledger.jsonl');self.assertEqual(ledger.spent,0)
        self.assertEqual(ledger.exposure,episode_reservation(self.ep));self.assertFalse(ledger.blocked)
        self.assertFalse((self.base/'STOP.json').exists());self.assertFalse(ledger.sealed)
        row=score(self.ep,self.base,True);self.assertEqual(row['calls_started'],0);self.assertEqual(row['calls'],[])
        audit=audit_accounting(self.base,[row]);self.assertEqual(audit['usage_limit_refusals'],1);self.assertEqual(audit['unsettled_calls'],[])
        self.assertEqual(audit['active_time']['claude']['unsettled'],0)
    def test_before_reset_clean_exit_without_dispatch(self):
        fake=self.limited();self.collect(fake)
        with patch('ps_collect.pause_ready',return_value=False): self.assertEqual(self.collect(fake)['status'],'usage-limit pause')
        self.assertEqual(fake.calls,1)
    def test_first_call_resume_identical_bytes_and_first_contract(self):
        fake=self.limited();self.collect(fake);directory=self.base/'episodes'/self.ep['id']
        saved={p.name:p.read_bytes() for p in directory.iterdir()}
        with patch('ps_collect.pause_ready',return_value=True): self.collect(fake)
        self.assertEqual(fake.calls,9)
        for name,data in saved.items(): self.assertEqual((directory/name).read_bytes(),data)
        self.assertEqual((directory/'0.request.json').read_bytes(),(directory/'0-attempt-1.request.json').read_bytes())
        row=score(self.ep,self.base,True);self.assertTrue(row['technical_complete']);self.assertEqual(row['calls_started'],8)
        audit=audit_accounting(self.base,[row]);self.assertEqual(audit['settled_micro_usd'],8*1020);self.assertEqual(audit['held_micro_usd'],0)
        self.assertEqual(read(self.base/'frontier-contract.json')['call_id'],self.ep['id']+'-0-attempt-1')
    def test_mid_episode_resume_prior_history_and_no_prior_call_resent(self):
        fake=self.limited(index=5);self.collect(fake);directory=self.base/'episodes'/self.ep['id']
        saved={p.name:p.read_bytes() for p in directory.iterdir()}
        row=score(self.ep,self.base,True);self.assertEqual(row['calls_started'],5);self.assertTrue(row['operational_pause'])
        with patch('ps_collect.pause_ready',return_value=True): self.collect(fake)
        self.assertEqual(fake.calls,9)
        for name,data in saved.items(): self.assertEqual((directory/name).read_bytes(),data)
        row=score(self.ep,self.base,True);self.assertTrue(row['technical_complete']);audit_accounting(self.base,[row])
        self.assertEqual((directory/'5.request.json').read_bytes(),(directory/'5-attempt-1.request.json').read_bytes())
    def test_repeated_refusals_each_saved_no_budget_growth(self):
        fake=self.limited(count=2);self.collect(fake)
        with patch('ps_collect.pause_ready',return_value=True):
            self.assertEqual(self.collect(fake)['status'],'usage-limit pause');self.collect(fake)
        self.assertEqual(fake.calls,10);row=score(self.ep,self.base,True);audit=audit_accounting(self.base,[row])
        self.assertEqual(audit['usage_limit_refusals'],2);self.assertEqual(audit['exposure_micro_usd'],8160)
    def test_mutated_pause_or_request_or_prefix_blocks_resume(self):
        for kind in ('raw','pause','request'):
            with tempfile.TemporaryDirectory() as tmp:
                self.base=Path(tmp)/'fake';fake=self.limited();self.collect(fake)
                directory=self.base/'episodes'/self.ep['id'];path=directory/f'0.{kind}.json'
                path.write_text(path.read_text()+' ')
                with patch('ps_collect.pause_ready',return_value=True),self.assertRaises(Stop): self.collect(fake)
                self.assertEqual(fake.calls,1)
    def test_real_envelope_preserves_accounting_and_content_failure(self):
        real=read(ROOT/'fixtures/real-claude-envelope.json');raw={'stdout':canonical(real),'stderr':'','returncode':0}
        self.assertFalse(usage_limit_refusal(raw))
        fake=Fake(mutate=lambda raw,ep,i: {'stdout':canonical(real),'stderr':'','returncode':0})
        self.collect(fake);row=score(self.ep,self.base,True);audit=audit_accounting(self.base,[row])
        self.assertEqual(row['calls_started'],1);self.assertFalse(row['technical_complete']);self.assertEqual(audit['usage_limit_refusals'],0)
        self.assertEqual(audit['settled_micro_usd'],16788)

    def test_saved_refusal_recovers_crash_without_releasing_active_time(self):
        from ps_io import ActiveTime,now
        ep=self.ep;directory=self.base/'episodes'/ep['id'];payload=World(ep).payload();prompt=render(payload)
        bound=reservation(ep['arm'],payload['mode']);fake=Fake();request=fake.request(ep,prompt,'write',bound,0)
        save(directory/'planned.json',ep)
        save(directory/'0.request.json',{'payload':payload,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),
             'transport_request':request,'reservation':bound,'generation_seed':None})
        ledger=Ledger(self.base/'ledger.jsonl');ledger.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
        ident=ep['id']+'-0';timer=ActiveTime(self.base/'claude-time.jsonl',10800);timer.begin(ident,420)
        ledger.event(event='start',id=ident,episode=ep['id'],reserved=bound['micro_usd'])
        save(directory/'0.start.json',{'id':ident,'started_at':now(),'freeze_sha256':'OFFLINE-FAKE',
             'request_sha256':sha((directory/'0.request.json').read_bytes()),'ledger_prefix_bytes':len(ledger.journal.raw),'ledger_prefix_sha256':sha(ledger.journal.raw)})
        save(directory/'0.raw.json',self.raw)
        with patch('ps_collect.pause_ready',return_value=False): self.assertEqual(self.collect(fake)['status'],'usage-limit pause')
        self.assertEqual(fake.calls,0);audit=audit_accounting(self.base,[score(ep,self.base,True)])
        self.assertGreaterEqual(audit['active_time']['claude']['seconds'],420);self.assertEqual(audit['usage_limit_refusals'],1)
        with patch('ps_collect.pause_ready',return_value=True): self.collect(fake)
        self.assertEqual(fake.calls,8);self.assertTrue(score(ep,self.base,True)['technical_complete'])


    def test_analysis_counts_refusal_as_operational_event_only(self):
        from ps_analysis import analyze,primary
        self.collect(self.limited())
        result=analyze(ROOT,self.base,True)
        self.assertEqual(len(result['operational_events']),1)
        self.assertEqual(result['accounting']['usage_limit_refusals'],1)
        self.assertEqual(result['attempted_episodes'],0)
        self.assertEqual(result['predictions']['P7']['status'],'UNKNOWN')
        rows=[{'seed':i,'Y':1,'F':1,'technical_complete':True,'attempted':True,'calls':[],'calls_started':8} for i in range(100)]
        paused=[{**r,'operational_pause':r['seed']==0} for r in rows]
        self.assertEqual(primary(paused,rows)['status'],'UNKNOWN')

    def test_nonzero_429_is_generated_failure_and_no_redispatch(self):
        e=__import__('json').loads(self.raw['stdout']);e['usage']['input_tokens']=1
        bad={**self.raw,'stdout':canonical(e)};fake=Fake(mutate=lambda raw,ep,i:bad)
        self.collect(fake)
        ledger=Ledger(self.base/'ledger.jsonl');self.assertFalse(ledger.blocked)
        self.assertEqual(ledger.spent,4);self.assertEqual(ledger.usage_pauses,{})
        self.collect(fake)
        self.assertEqual(fake.calls,1)


class DeviationFreezeTests(unittest.TestCase):
    def setUp(self):
        from test_freeze import FreezeTests
        self.fixture=FreezeTests();self.fixture.setUp()
        self.root=self.fixture.root;self.clone=self.fixture.clone
    def tearDown(self): self.fixture.tearDown()
    def archive(self):
        import io,tarfile
        from ps_freeze import active_manifest
        data=io.BytesIO();manifest=active_manifest(self.root)
        with tarfile.open(fileobj=data,mode='w') as tar:
            for name in set(read(manifest)['files'])|{manifest.name,'freeze.json'}:
                raw=(self.root/name).read_bytes();info=tarfile.TarInfo('portable-self/'+name);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        return data.getvalue()
    def subprocess(self,cmd,**kwargs):
        if cmd[:2]==['git','archive']: return self.archive()
        return self.fixture.subprocess(cmd,**kwargs)
    def setup_deviation(self):
        import datetime as dt
        from ps_freeze import attest,freeze_usage_limit
        (self.root/'ps_collect.py').write_text('# original operational harness\n')
        old=self.fixture.freeze()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.fixture.commit)
        save(self.root/'collection/episodes/old-local/0.start.json',{'freeze_sha256':old,'started_at':dt.datetime.now(dt.timezone.utc).isoformat()})
        self.preserved={p.name:p.read_bytes() for p in (self.root/'collection').glob('push*.json')}
        archive=self.root/'revisions/usage-limit/parent-files/ps_collect.py';archive.parent.mkdir(parents=True);archive.write_bytes((self.root/'ps_collect.py').read_bytes())
        (self.root/'ps_collect.py').write_text('# new operational harness\n')
        new=freeze_usage_limit(self.root)
        self.fixture.commit='b'*40;self.fixture.event={**self.fixture.event,'after':self.fixture.commit,'id':456,
                'timestamp':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(microseconds=1)).isoformat()}
        return new
    def test_new_freeze_requires_new_push_and_keeps_old_receipt_and_starts(self):
        from ps_freeze import attest,push_gate,verify,freeze_usage_limit
        new=self.setup_deviation();self.assertEqual(verify(self.root),new)
        with self.assertRaises(FileNotFoundError): push_gate(self.root)
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.fixture.commit)
        self.assertEqual(push_gate(self.root),new)
        for name,data in self.preserved.items(): self.assertEqual((self.root/'collection'/name).read_bytes(),data)
        self.assertTrue((self.root/'collection/push-usage-limit.json').exists())
        with self.assertRaises(Stop): freeze_usage_limit(self.root)
    def test_parent_receipt_original_and_archive_are_binding(self):
        from ps_freeze import verify
        self.setup_deviation()
        for path in [self.root/'freeze.json',self.root/'collection/push.json',self.root/'revisions/usage-limit/parent-files/ps_collect.py']:
            old=path.read_bytes();path.write_bytes(old+b' ')
            with self.assertRaises(Stop): verify(self.root)
            path.write_bytes(old)
    def test_new_starts_cannot_claim_parent_freeze(self):
        import datetime as dt
        from ps_freeze import attest,push_gate
        self.setup_deviation()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.fixture.commit)
        save(self.root/'collection/episodes/new/0.start.json',{'freeze_sha256':sha((self.root/'freeze.json').read_bytes()),'started_at':dt.datetime.now(dt.timezone.utc).isoformat()})
        with self.assertRaises(Stop): push_gate(self.root)
