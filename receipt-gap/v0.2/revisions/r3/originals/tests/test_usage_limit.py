"""Offline pause/resume, strict non-start boundaries and revision integrity."""
import copy
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import rg_collect as c
import rg_freeze as f
import rg_analysis as analysis
from rg_core import ROOT, canonical, sha, reserve, render, strict_load
from rg_offline import Fake
from rg_usage_limit import refusal, operational_events

BEFORE = dt.datetime(2026,11,11,13,0,tzinfo=dt.timezone.utc)
AFTER = dt.datetime(2026,11,11,13,31,tzinfo=dt.timezone.utc)


class Clock(dt.datetime):
    value = BEFORE
    @classmethod
    def now(cls, tz=None):
        return cls.value if tz is None else cls.value.astimezone(tz)


def limited():
    return {'stdout':(ROOT/'fixtures/usage-limit-envelope.json').read_text(),'stderr':'','returncode':1}


class Interrupted(Fake):
    def __init__(self, positions):
        super().__init__()
        self.positions = positions
        self.prompts = []
    def generate(self, ep, prompt, phase, budget, work):
        self.prompts.append((prompt,phase,budget))
        if len(self.prompts) in self.positions:
            return limited()
        return super().generate(ep,prompt,phase,budget,work)


class UsageLimitTests(unittest.TestCase):
    def setUp(self):
        Clock.value=BEFORE
        self.ep=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')

    def test_exact_predicate_and_near_misses(self):
        self.assertTrue(refusal(limited()))
        envelope=strict_load(limited()['stdout'])
        changes=[{'api_error_status':500},{'api_error_status':True},{'is_error':False},
                 {'total_cost_usd':0.01},{'total_cost_usd':None},{'total_cost_usd':False},
                 {'structured_output':{}},{'result':'rate limit'},
                 {'subagent_stats':{'calls':1}}, {'usage':{}},
                 {'result':"You've hit your 5-hour limit · resets 99:99pm (Asia/Hong_Kong)"}]
        for key in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            for value in (1,None,False):
                changes.append({'usage':{**envelope['usage'],key:value}})
        for change in changes:
            with self.subTest(change=change):
                raw={**limited(),'stdout':canonical({**envelope,**change})}
                self.assertFalse(refusal(raw))
        for change in ({'returncode':None},{'transport_error':'timeout'}, {'stdout':'{}{}'}):
            self.assertFalse(refusal({**limited(),**change}))

    def test_zero_usage_with_real_cli_metadata_and_capacities(self):
        raw=limited();envelope=strict_load(raw['stdout'])
        valid=c.read(ROOT/'fixtures/real-claude-envelope.json')
        model=copy.deepcopy(valid['modelUsage'])
        for fields in model.values():
            for key,value in fields.items():
                if type(value) in (int,float) and key not in ('contextWindow','maxOutputTokens'):
                    fields[key]=0
        envelope['modelUsage']=model;raw['stdout']=canonical(envelope)
        self.assertTrue(refusal(raw))
        fields=next(iter(model.values()));fields['thinkingTokens']=1
        raw['stdout']=canonical(envelope)
        self.assertFalse(refusal(raw))

    def test_supplied_real_valid_envelope_still_decodes(self):
        raw={'stdout':(ROOT/'fixtures/real-claude-envelope.json').read_text(),'stderr':'','returncode':0}
        self.assertFalse(refusal(raw))
        ep={**self.ep,'toolkit':'plain'}
        bound=reserve(render(ep,[],10,'action'),'action','plain')
        self.assertEqual(c.decode(raw,ep,'action',bound),{'op':'send','job':1,'key':None})
        self.assertEqual(analysis.checked_value(raw,ep,'action',bound,False),{'op':'send','job':1,'key':None})

    def check_resume(self, at, repeated=False):
        with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
            base=Path(tmp);c.save(base/'OFFLINE-FAKE.json',{'real_model_calls':0})
            ledger=c.Ledger(base/'ledger.jsonl');timer=c.ActiveTime(base/'time.jsonl',100000)
            provider=Interrupted({at,at+1} if repeated else {at})
            pause=c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
            d=base/'episodes'/self.ep['id']
            self.assertEqual(pause['status'],'usage-limit pause')
            self.assertEqual(pause['reset_at'],'2026-11-11T13:30:00+00:00')
            self.assertFalse((base/'STOP.json').exists());self.assertFalse((d/'episode.json').exists())
            self.assertEqual(ledger.calls[pause['id']],0)
            index=at-1
            self.assertNotIn(pause['id'],ledger.restored)
            self.assertFalse((d/(str(index)+'.parsed.json')).exists())
            old={p.relative_to(d):p.read_bytes() for p in d.rglob('*') if p.is_file()}
            spent=ledger.spent
            again=c.run_episode(self.ep,provider,base,c.Ledger(ledger.path),c.ActiveTime(timer.path,100000),'OFFLINE-FAKE',True)
            self.assertEqual(again,pause);self.assertEqual(len(provider.prompts),at)
            Clock.value=AFTER
            result=c.run_episode(self.ep,provider,base,c.Ledger(ledger.path),c.ActiveTime(timer.path,100000),'OFFLINE-FAKE',True)
            if repeated:
                self.assertEqual(result['status'],'usage-limit pause')
                self.assertEqual(len(provider.prompts),at+1)
                Clock.value=AFTER+dt.timedelta(days=1)
                result=c.run_episode(self.ep,provider,base,c.Ledger(ledger.path),c.ActiveTime(timer.path,100000),'OFFLINE-FAKE',True)
            self.assertTrue(result['trajectory_valid']);self.assertEqual(result['attempted_calls'],6)
            for rel, data in old.items():self.assertEqual((d/rel).read_bytes(),data)
            self.assertEqual(provider.prompts[at-1],provider.prompts[at])
            if repeated:self.assertEqual(provider.prompts[at],provider.prompts[at+1])
            self.assertEqual(len(operational_events(base)),2 if repeated else 1)
            account=analysis.reconcile(ROOT,base)
            self.assertEqual(account['new_settled_micro_usd'],7200)
            self.assertEqual(account['outstanding_micro_usd'],0)
            self.assertEqual(account['unknown_usage_calls'],[])
            rows,_=analysis.load_rows(ROOT,base)
            row=next(r for r in rows if r['id']==self.ep['id'])
            self.assertTrue(row['valid']);self.assertTrue(row['report_valid'])
            self.assertLess(spent,7200)

    def test_pause_first_call(self):self.check_resume(1)
    def test_pause_mid_episode(self):self.check_resume(3)
    def test_pause_report(self):self.check_resume(6)
    def test_repeated_pause(self):self.check_resume(3,True)

    def test_collect_pauses_cleanly_and_never_dispatches_before_reset(self):
        with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
            root=Path(tmp);c.save(root/'config/episodes.json',[self.ep]);base=root/'collection'
            provider=Interrupted({1})
            pause=c.collect(root,'claude',fake_transport=provider)
            self.assertEqual(pause['status'],'usage-limit pause')
            rows,_=analysis.load_rows(root,base)
            self.assertFalse(rows[0]['attempted']);self.assertTrue(rows[0]['operational_pending'])
            self.assertIsNone(rows[0]['Dstar'])
            self.assertEqual(c.collect(root,'claude',fake_transport=provider),pause)
            self.assertEqual(len(provider.prompts),1)
            Clock.value=AFTER
            result=c.collect(root,'claude',fake_transport=provider)
            self.assertEqual(result['settled_micro_usd'],7200)
            self.assertFalse((base/'STOP.json').exists())

    def test_results_keep_refusal_out_of_model_metrics(self):
        with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
            root=Path(tmp);c.save(root/'config/episodes.json',[self.ep])
            c.collect(root,'claude',fake_transport=Interrupted({1}))
            output=root/'analysis.json'
            with patch('sys.argv',['rg_analysis.py','--root',str(root),'--output',str(output)]):
                analysis.main()
            result=c.read(output)
            self.assertEqual(result['operational_events']['usage_limit_refusals'],1)
            self.assertEqual(result['pending_usage_limit_episodes'],[self.ep['id']])
            self.assertIsNone(result['technical_acceptance'])
            self.assertEqual(result['analysis_status'],'UNKNOWN')
            self.assertEqual(result['accounting']['new_settled_micro_usd'],0)
            self.assertTrue(all(cell['planned']==0 for cell in result['cells'].values()))

    def test_pause_with_unsettled_cost_cannot_resend(self):
        with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
            base=Path(tmp);provider=Interrupted({1});ledger=c.Ledger(base/'ledger.jsonl');timer=c.ActiveTime(base/'time.jsonl',10000)
            c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
            Clock.value=AFTER
            # A zero settlement must be reconstructed from the append-only ledger.
            ledger.nonstarts.clear()
            with self.assertRaises(c.Stop):
                c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
            self.assertEqual(len(provider.prompts),1)

    def test_generated_refusal_is_episode_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);provider=Interrupted({1})
            raw=limited();e=strict_load(raw['stdout']);e['usage']['output_tokens']=1;raw['stdout']=canonical(e)
            with patch.object(provider,'generate',return_value=raw):
                result=c.run_episode(self.ep,provider,base,c.Ledger(base/'ledger.jsonl'),c.ActiveTime(base/'time.jsonl',10000),'OFFLINE-FAKE',True)
            self.assertFalse((base/'STOP.json').exists());self.assertIsNotNone(result['error'])
            self.assertFalse(operational_events(base))

    def test_uncertain_dispatch_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
            base=Path(tmp);provider=Interrupted({1})
            ledger=c.Ledger(base/'ledger.jsonl');timer=c.ActiveTime(base/'time.jsonl',10000)
            c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
            Clock.value=AFTER
            with patch.object(provider,'generate',side_effect=KeyboardInterrupt),self.assertRaises(KeyboardInterrupt):
                c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
            with self.assertRaises((ValueError,OSError,c.Stop)):
                c.run_episode(self.ep,provider,base,c.Ledger(ledger.path),c.ActiveTime(timer.path,10000),'OFFLINE-FAKE',True)
            self.assertEqual(len(provider.prompts),1)

    def test_tampered_request_or_pause_cannot_resume(self):
        for target in ('request','raw','pause'):
            with tempfile.TemporaryDirectory() as tmp, patch('rg_collect.dt.datetime',Clock):
                base=Path(tmp);provider=Interrupted({1});ledger=c.Ledger(base/'ledger.jsonl');timer=c.ActiveTime(base/'time.jsonl',10000)
                c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
                d=base/'episodes'/self.ep['id'];attempt=d/'dispatches/0/0'
                p=d/'0.request.json' if target=='request' else attempt/(target+'.json')
                if target == 'pause':
                    value=c.read(p);value['reset_at']='2026-11-11T13:29:00+00:00';p.write_text(canonical(value))
                else:
                    p.write_text(p.read_text()+' ')
                Clock.value=AFTER
                with self.assertRaises((ValueError,c.Stop)):
                    c.run_episode(self.ep,provider,base,ledger,timer,'OFFLINE-FAKE',True)
                self.assertEqual(len(provider.prompts),1)


class RevisionTests(unittest.TestCase):
    def make_revision(self, root):
        f.prepare(root)
        source=root/'harness.py';source.write_text('original=1\n')
        f.freeze(root)
        original=(root/'freeze.json').read_bytes()
        witness=root/'revisions/r1/originals/harness.py';witness.parent.mkdir(parents=True)
        witness.write_bytes(source.read_bytes());source.write_text('revised=1\n')
        f.revise(root)
        self.assertEqual((root/'freeze.json').read_bytes(),original)
        return original

    def test_revision_binds_parent_and_preserved_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=self.make_revision(root)
            digest=f.verify(root,'freeze-r1.json')
            self.assertEqual(c.read(root/'freeze-r1.json')['parent_sha256'],sha(original))
            self.assertEqual(digest,sha((root/'freeze-r1.json').read_bytes()))
            with self.assertRaises(FileExistsError):f.revise(root)
            witness=root/'revisions/r1/originals/harness.py';witness.write_text('tampered')
            with self.assertRaises(c.Stop):f.verify(root,'freeze-r1.json')

    def test_revision_attestation_and_gate_bind_new_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_revision(root)
            event={'activity_type':'push','after':'a'*40,'ref':'refs/heads/test',
                   'timestamp':c.read(root/'freeze-r1.json')['created_at'],'id':42}
            source=root/'event.json';c.save(source,event)
            def fake_git(cmd,**kwargs):
                if cmd[1:]==['rev-parse','HEAD']:return 'a'*40+'\n'
                if cmd[1:]==['remote','get-url','origin']:return 'https://github.com/Robin84Bran/research.git\n'
                if cmd[1]=='show':return (root/cmd[2].split(':receipt-gap/v0.2/')[1]).read_bytes()
                if cmd[1]=='ls-remote':return 'a'*40+'\trefs/heads/test\n'
                raise AssertionError(cmd)
            with patch('rg_freeze.subprocess.check_output',side_effect=fake_git):
                digest=f.attest(root,source,'a'*40,'receipt-gap/v0.2',root,'freeze-r1.json')
            self.assertEqual(c.read(root/'collection/push.json')['freeze_file'],'freeze-r1.json')
            self.assertEqual(c.push_gate(root,'freeze-r1.json'),digest)
            analysis.check_saved_push(root,root/'collection',c.read(root/'collection/push.json'),digest)
            with self.assertRaises(c.Stop):c.push_gate(root)

    def test_revision_cannot_follow_any_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root)
            c.save(root/'collection/episodes/ep/dispatches/0/0/start.json',{'id':'ep-0'})
            with self.assertRaises(c.Stop):f.revise(root)
