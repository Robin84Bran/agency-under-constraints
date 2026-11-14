"""Exact saved bytes plus explicitly synthetic envelope-shape derivatives."""
import base64
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, World, canonical, reservation, sha
from ps_io import Stop, EpisodeFailure, UsageLimitPause, Ledger, read, save
from ps_transport import decode, usage_limit_refusal, definite_api_nonstart, provider_envelope
from ps_collect import collect
from ps_analysis import score, audit_accounting
from ps_offline import Fake
from test_v02 import episode

FIX=ROOT/'revisions/claude-envelope/fixtures'


class SavedEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.ep=episode(arm='discard');self.payload=World(self.ep).payload()
        self.bound=reservation('discard','write')
        self.dns=read(FIX/'stopped-episode/0.raw.json')
        self.real=(FIX/'real-claude-envelope.json').read_bytes()

    def raw(self,envelope,code=0):
        data=canonical(envelope).encode()
        return {'stdout':data.decode(),'stdout_b64':base64.b64encode(data).decode(),'stderr':'','returncode':code}

    def check(self,raw): return decode(raw,self.ep,self.payload,self.bound,True)

    def failure(self,raw):
        with self.assertRaises(EpisodeFailure) as caught: self.check(raw)
        self.assertNotIsInstance(caught.exception,Stop)
        return str(caught.exception)

    def test_exact_saved_stopping_bytes_and_decisive_fields(self):
        before=read(ROOT/'revisions/claude-envelope/before.json')
        self.assertEqual(sha((FIX/'stopped-episode/0.raw.json').read_bytes()),before['episode_files']['0.raw.json'])
        e,error=provider_envelope(self.dns['stdout'],'claude')
        self.assertIsNone(error);self.assertEqual(e['modelUsage'],{})
        self.assertEqual(e['api_error_status'],None);self.assertEqual(e['terminal_reason'],'api_error')
        self.assertEqual(e['total_cost_usd'],0);self.assertEqual(e['usage']['output_tokens'],0)
        self.assertTrue(definite_api_nonstart(self.dns));self.assertFalse(usage_limit_refusal(self.dns))
        self.assertIn('pre-generation API DNS failure',self.failure(self.dns))

    def test_exact_external_sibling_bytes_are_content_failure(self):
        before=read(ROOT/'revisions/claude-envelope/before.json')
        self.assertEqual(sha(self.real),before['external_fixture']['sha256'])
        self.assertIn('invalid write',self.failure({'stdout':self.real.decode(),'stdout_b64':base64.b64encode(self.real).decode(),'stderr':'','returncode':0}))

    def derivatives(self):
        original=provider_envelope(self.real.decode(),'claude')[0]
        for subtype in ('success','error_during_execution','error_max_turns','error_max_structured_output_retries'):
            for models in ('absent',None,{}):
                e=copy.deepcopy(original);e.update(is_error=True,subtype=subtype,stop_reason='max_tokens',num_turns=0)
                e.pop('structured_output');e['usage']['output_tokens']=512
                e['modelUsage']=models
                if models=='absent': del e['modelUsage']
                yield e
        for value in (None,[],{'slot':True,'note':''},{'slot':1,'note':'x'*97}):
            e=copy.deepcopy(original);e['structured_output']=value;yield e
        e=copy.deepcopy(original);del e['structured_output'];yield e
        e=copy.deepcopy(original);e.update(is_error=True,result='I cannot comply',stop_reason='refusal');yield e
        e=copy.deepcopy(original);e.update(is_error=False,result='I cannot comply',stop_reason='refusal',structured_output={'slot':1,'note':''});yield e
        e=copy.deepcopy(original);e.pop('structured_output');e.update(stop_reason=None,num_turns=0);yield e
        e=copy.deepcopy(original);e.update(is_error=True,api_error_status=429,result='limit after generation');yield e

    def test_generated_error_refusal_cap_invalid_and_missing_payload_are_episode_failures(self):
        for i,e in enumerate(self.derivatives()):
            with self.subTest(i=i):
                raw=self.raw(e,1 if e['is_error'] else 0)
                self.assertFalse(usage_limit_refusal(raw));self.assertFalse(definite_api_nonstart(raw));self.failure(raw)

    def test_every_failure_shape_continues_cohort_and_keeps_denominators(self):
        raws=[self.dns]+[self.raw(e,1 if e['is_error'] else 0) for e in self.derivatives()]
        for i,raw in enumerate(raws):
            with self.subTest(i=i),tempfile.TemporaryDirectory() as tmp:
                eps=[self.ep,episode(seed=1,arm='discard')];base=Path(tmp)/'fake'
                fake=Fake(mutate=lambda normal,ep,index:raw if ep['seed']==0 else normal)
                collect(ROOT,'claude',fake_transport=fake,output=base,episodes=eps)
                self.assertEqual(fake.calls,9);self.assertFalse((base/'STOP.json').exists())
                rows=[score(ep,base,True) for ep in eps];audit=audit_accounting(base,rows)
                self.assertEqual(rows[0]['valid_calls'],0);self.assertEqual(rows[0]['technical_missing'],16)
                self.assertEqual((rows[0]['Y'],rows[0]['F']),(0,0));self.assertTrue(rows[1]['technical_complete'])
                self.assertEqual(audit['held_micro_usd'],0);self.assertEqual(audit['unsettled_calls'],[])
                self.assertEqual(audit['usage_limit_refusals'],0)

    def test_success_two_turns_and_zero_nested_telemetry(self):
        e=provider_envelope(self.real.decode(),'claude')[0]
        e['structured_output']={'slot':1,'note':''}
        value,metrics=self.check(self.raw(e));self.assertEqual(value,e['structured_output'])
        self.assertEqual(metrics['num_turns'],2);self.assertEqual(metrics['input_tokens'],1602)

    def test_exact_429_with_absent_model_usage_still_pauses(self):
        raw=read(ROOT/'fixtures/usage-limit-refusal.json');e=provider_envelope(raw['stdout'],'claude')[0]
        for models in ('absent',None,{}, {'claude-opus-5-5':{'inputTokens':0,'outputTokens':0,'maxOutputTokens':128000,'contextWindow':1000000}}):
            e['modelUsage']=models
            if models=='absent': del e['modelUsage']
            with self.subTest(models=models),self.assertRaises(UsageLimitPause): self.check(self.raw(e,1))

    def test_unknown_errors_and_conflicting_or_missing_bytes_fail_closed(self):
        e=provider_envelope(self.dns['stdout'],'claude')[0]
        for changes in ({'result':'Unknown API error'},{'total_cost_usd':.01},{'duration_api_ms':1}):
            with self.subTest(changes=changes),self.assertRaises(Stop): self.check(self.raw({**e,**changes},1))
        for raw in ({'stdout':'','stderr':'','returncode':None,'transport_error':'timeout'},
                    {'stdout':'{','stderr':'','returncode':1},
                    {**self.dns,'stdout_b64':base64.b64encode(b'other').decode()}):
            with self.subTest(raw=raw),self.assertRaises(Stop): self.check(raw)

    def test_1024_sibling_cap_is_content_failure_with_its_own_bound(self):
        e=provider_envelope(self.real.decode(),'claude')[0]
        e.update(is_error=True,stop_reason='max_tokens');e['usage']['output_tokens']=1024
        with self.assertRaises(EpisodeFailure): decode(self.raw(e,1),self.ep,self.payload,{**self.bound,'output_tokens':1024},True)
        # Portable Self's frozen 576-token reservation is not enlarged by a sibling.
        with self.assertRaises(Stop): self.check(self.raw(e,1))

    def test_integrity_and_resource_failures_still_stop(self):
        original=provider_envelope(self.real.decode(),'claude')[0]
        for field,value in [('modelUsage',{'wrong':{}}),('effort','high'),('subagent_stats',{'requested':{'foreground':1}}),('tool_calls',[{}])]:
            e={**original,'is_error':True,field:value}
            with self.subTest(field=field),self.assertRaises(Stop): self.check(self.raw(e,1))


class ClearanceLedgerTests(unittest.TestCase):
    def test_clear_event_is_anchored_and_cannot_clear_a_different_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.jsonl';ledger=Ledger(path)
            ledger.event(event='stop',id='collection',reason='test')
            with self.assertRaises(Stop): ledger.event(event='clear-stop',id='collection',stop_seq=8,clearance_sha256='a'*64)
            ledger.event(event='clear-stop',id='collection',stop_seq=0,clearance_sha256='a'*64)
            self.assertFalse(Ledger(path).blocked)
            with self.assertRaises(Stop): Ledger(path).event(event='clear-stop',id='collection',stop_seq=0,clearance_sha256='a'*64)
            data=path.read_bytes();path.write_bytes(data.replace(b'"test"',b'"evil"'))
            with self.assertRaises(Stop): Ledger(path)


class EnvelopeFreezeTests(unittest.TestCase):
    def setUp(self):
        import test_usage_limit as usage_tests
        self.fixture=usage_tests.DeviationFreezeTests();self.fixture.setUp()
        self.root=self.fixture.root;self.clone=self.fixture.clone
        self.fixture.setup_deviation()
        from ps_freeze import attest,freeze_claude_envelope
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess):
            attest(self.root,self.clone,'portable-self',self.fixture.fixture.commit)
        name='ps_collect.py';source=self.root/name
        target=self.root/'revisions/claude-envelope/parent-files'/name
        target.parent.mkdir(parents=True);target.write_bytes(source.read_bytes())
        source.write_text('# corrected operational envelope handling\n')
        self.hash=freeze_claude_envelope(self.root)

    def tearDown(self): self.fixture.tearDown()

    def archive(self):
        import io,tarfile
        from ps_freeze import active_manifest
        manifest=active_manifest(self.root);value=read(manifest);data=io.BytesIO()
        names=set(value['files'])|set(value.get('parents',{}))|{manifest.name,'freeze.json'}
        with tarfile.open(fileobj=data,mode='w') as tar:
            for name in names:
                raw=(self.root/name).read_bytes();info=tarfile.TarInfo('portable-self/'+name)
                info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        return data.getvalue()

    def subprocess(self,cmd,**kwargs):
        if cmd[:2]==['git','archive']: return self.archive()
        return self.fixture.fixture.subprocess(cmd,**kwargs)

    def attest(self):
        import datetime as dt
        from ps_freeze import attest
        f=self.fixture.fixture;f.commit='c'*40
        f.event={**f.event,'after':f.commit,'id':789,'timestamp':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(microseconds=1)).isoformat()}
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess):
            return attest(self.root,self.clone,'portable-self',f.commit)

    def test_both_parent_freezes_receipts_and_predecessor_bytes_are_bound(self):
        from ps_freeze import verify
        self.assertEqual(self.hash,verify(self.root))
        for name in ('freeze.json','freeze-usage-limit.json','collection/push.json','collection/push-usage-limit.json','revisions/claude-envelope/parent-files/ps_collect.py'):
            path=self.root/name;original=path.read_bytes();path.write_bytes(original+b' ')
            with self.subTest(name=name),self.assertRaises(Stop): verify(self.root)
            path.write_bytes(original)

    def test_new_attestation_required_old_receipts_preserved(self):
        from ps_freeze import push_gate,freeze_claude_envelope
        originals={p.name:p.read_bytes() for p in (self.root/'collection').glob('push*.json')}
        with self.assertRaises(FileNotFoundError): push_gate(self.root)
        self.assertEqual(self.hash,self.attest());self.assertEqual(push_gate(self.root),self.hash)
        for name,data in originals.items(): self.assertEqual((self.root/'collection'/name).read_bytes(),data)
        with self.assertRaises(Stop): freeze_claude_envelope(self.root)

    def test_old_starts_cannot_cross_either_successor_boundary(self):
        from ps_freeze import push_gate
        self.attest()
        save(self.root/'collection/episodes/invalid/0.start.json',{
            'freeze_sha256':sha((self.root/'freeze.json').read_bytes()),
            'started_at':read(self.root/'freeze-usage-limit.json')['created_at']})
        with self.assertRaises(Stop): push_gate(self.root)


class RealClearanceTests(unittest.TestCase):
    def test_full_saved_collection_clearance_is_idempotent_and_never_replays_terminal(self):
        import shutil
        from ps_freeze import freeze_claude_envelope,verify
        from ps_claude_clearance import clear_stop,audit_clearances,EP,RECEIPT,ARCHIVED_STOP
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'study'
            # Independent copies: no linked writes into the source collection.
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__','.git','freeze-claude-envelope.json'))
            base=root/'collection'
            # Also works after the source project has recorded its clearance:
            # reconstruct the exact pre-clearance ledger from preserved prefixes.
            before=read(root/'revisions/claude-envelope/before.json')
            ledger_path=base/'ledger.jsonl';n=before['journals'][0]['prefix_bytes']
            ledger_path.write_bytes(ledger_path.read_bytes()[:n])
            for path in (base/'ledger.jsonl.prefixes').glob('*.json'):
                if int(path.stem)>=before['journals'][0]['events']: path.unlink()
            for name in (RECEIPT,ARCHIVED_STOP):
                path=base/name
                if path.exists(): path.unlink()
            if not (base/'STOP.json').exists():
                (base/'STOP.json').write_bytes((root/'revisions/claude-envelope/fixtures/STOP.json').read_bytes())
            frozen=freeze_claude_envelope(root);old_ledger=ledger_path.read_bytes()
            original_episode={p.name:p.read_bytes() for p in (base/'episodes'/EP).iterdir()}
            original_event=Ledger.event
            def interrupted_event(ledger,**event):
                if event['event']=='clear-stop': raise RuntimeError('synthetic crash after receipt')
                return original_event(ledger,**event)
            with patch.object(Ledger,'event',interrupted_event),self.assertRaises(RuntimeError): clear_stop(root)
            self.assertTrue(Ledger(ledger_path).blocked);self.assertTrue((base/RECEIPT).exists())
            with patch('ps_claude_clearance.os.rename',side_effect=RuntimeError('synthetic crash before archive')),self.assertRaises(RuntimeError): clear_stop(root)
            self.assertFalse(Ledger(ledger_path).blocked);self.assertTrue((base/'STOP.json').exists())
            result=clear_stop(root)
            self.assertFalse(result['blocked']);self.assertFalse(result['episode_replayed'])
            self.assertFalse((base/'STOP.json').exists());self.assertTrue((base/ARCHIVED_STOP).exists())
            self.assertTrue(ledger_path.read_bytes().startswith(old_ledger))
            ledger=Ledger(ledger_path);self.assertFalse(ledger.blocked);self.assertEqual(ledger.exposure,0)
            self.assertEqual(len(audit_clearances(root,base,ledger)),1)
            self.assertEqual(len(ledger.journal.rows),before['journals'][0]['events']+2)
            snapshot=ledger_path.read_bytes();clear_stop(root);self.assertEqual(ledger_path.read_bytes(),snapshot)
            self.assertEqual(verify(root),frozen)
            for name,data in original_episode.items(): self.assertEqual((base/'episodes'/EP/name).read_bytes(),data)
            from ps_analysis import load_timing
            timing=load_timing(base);eps=read(root/'config/episodes.json')
            rows=[score(ep,base,False,timing) for ep in eps]
            audit=audit_accounting(base,rows);self.assertFalse(audit['blocked'])
            self.assertEqual(audit['unsettled_calls'],[]);self.assertEqual(audit['held_micro_usd'],0)
            self.assertEqual([ep['id'] for ep in eps if ep['actor']=='claude' and (base/'episodes'/ep['id']/'episode.json').exists()],[EP])
            path=base/RECEIPT;old=path.read_bytes();path.write_bytes(old+b' ')
            with self.assertRaises(Stop): audit_clearances(root,base,Ledger(ledger_path))
            path.write_bytes(old)
            ledger=Ledger(ledger_path);ledger.event(event='stop',id='collection',reason='different later stop')
            save(base/'STOP.json',{'reason':'different later stop'})
            with self.assertRaises(Stop): clear_stop(root)
            self.assertTrue(Ledger(ledger_path).blocked)
