"""Claude r3 ruling, exact saved DNS fixture, no provider calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import rg_collect as c
import rg_analysis as a
import rg_revision as r
import rg_freeze as f
from rg_core import ROOT, canonical, sha
from rg_offline import Fake
from rg_usage_limit import dns_nonstart, operational_events, episode_directory


def dns():
    return c.read(ROOT/'fixtures/stopped-claude-raw.json')


class DNSRevisionTests(unittest.TestCase):
    def setUp(self):
        self.ep=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')

    def test_exact_saved_fixture_and_strict_near_misses(self):
        raw=dns();self.assertTrue(dns_nonstart(raw))
        self.assertEqual(r.classify(raw)['class'],'DEFINITE NON-START')
        e=c.provider_envelope(raw,'claude')[0]
        del e['duration_api_ms'];self.assertTrue(dns_nonstart({**raw,'stdout':canonical(e)}))
        for change in ({'duration_api_ms':1},{'duration_api_ms':None},{'duration_api_ms':False},
                       {'total_cost_usd':.01},{'total_cost_usd':False},{'is_error':False},
                       {'modelUsage':None},{'modelUsage':{'claude-opus-5-5':{}}},
                       {'structured_output':{}},{'usage':{}},{'subagent_stats':{'spawned':1}},
                       {'result':'ECONNRESET'},{'result':'request timeout'}):
            with self.subTest(change=change):
                self.assertFalse(dns_nonstart({**raw,'stdout':canonical({**e,**change})}))
        for key in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            for value in (1,None,False):
                self.assertFalse(dns_nonstart({**raw,'stdout':canonical({**e,'usage':{**e['usage'],key:value}})}))
        for change in ({'transport_error':'timeout'},{'returncode':None},{'stdout':'{}{}'}):
            self.assertFalse(dns_nonstart({**raw,**change}))
        e.pop('modelUsage');self.assertFalse(dns_nonstart({**raw,'stdout':canonical(e)}))

    def test_identical_resume_first_mid_report_and_repeated(self):
        for position in (1,3,6):
            with self.subTest(position=position),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);base=root/'collection';c.save(root/'config/episodes.json',[self.ep])
                class Provider(Fake):
                    def __init__(inner):super().__init__();inner.prompts=[]
                    def generate(inner,ep,prompt,phase,budget,work):
                        inner.prompts.append((prompt,phase,budget))
                        if len(inner.prompts) in (position,position+1):return dns()
                        return super().generate(ep,prompt,phase,budget,work)
                provider=Provider()
                for _ in range(2):
                    result=c.collect(root,'claude',fake_transport=provider)
                    self.assertEqual(result['status'],'dns non-start pause')
                    self.assertIsNone(result['reset_at']);self.assertFalse((base/'STOP.json').exists())
                c.collect(root,'claude',fake_transport=provider)
                self.assertEqual(provider.prompts[position-1],provider.prompts[position])
                self.assertEqual(provider.prompts[position],provider.prompts[position+1])
                self.assertTrue(c.read(base/'episodes'/self.ep['id']/'episode.json')['trajectory_valid'])
                self.assertEqual(a.reconcile(root,base)['status'],'RECONCILED')
                self.assertEqual(len(operational_events(base)),2)
                rows,_=a.load_rows(root,base);self.assertTrue(rows[0]['valid'])

    def test_transport_continues_and_stops_at_three_without_resending(self):
        for mode in ('ECONNRESET','timeout','other network error'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);base=root/'collection'
                eps=[{**self.ep,'id':'ep'+str(i)} for i in range(5)]
                c.save(root/'config/episodes.json',eps)
                class Provider(Fake):
                    def generate(inner,ep,*args):
                        inner.calls+=1
                        if mode=='timeout':return {'stdout':'','stderr':'','returncode':None,'transport_error':'timeout'}
                        e=c.provider_envelope(dns(),'claude')[0];e['result']=mode
                        return {**dns(),'stdout':canonical(e)}
                provider=Provider()
                with self.assertRaisesRegex(c.Stop,'three consecutive'):c.collect(root,'claude',fake_transport=provider)
                self.assertEqual(provider.calls,3)
                self.assertTrue(c.read(base/'episodes/ep2/episode.json')['transport_failure'])
                self.assertFalse((base/'episodes/ep3/episode.json').exists())
                with self.assertRaises(c.Stop):c.collect(root,'claude',fake_transport=provider)
                self.assertEqual(provider.calls,3)
                self.assertEqual(len(operational_events(base)),3)
                a.load_rows(root,base)
                self.assertEqual(a.reconcile(root,base)['status'],'UNKNOWN' if mode=='timeout' else 'RECONCILED')

    def test_success_breaks_transport_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'collection';eps=[{**self.ep,'id':'ep'+str(i)} for i in range(5)]
            c.save(root/'config/episodes.json',eps)
            class Provider(Fake):
                def generate(inner,ep,*args):
                    if ep['id']!='ep2':
                        inner.calls+=1;return {'stdout':'','stderr':'','returncode':None,'transport_error':'ECONNRESET'}
                    return super().generate(ep,*args)
            c.collect(root,'claude',fake_transport=Provider())
            self.assertFalse((base/'STOP.json').exists())
            self.assertTrue((base/'episodes/ep4/episode.json').exists())

    def prepare_stopped(self,root):
        ep=self.ep;base=root/'collection';source=ROOT/'revisions/r2/saved/collection'
        names=['STOP.json','episodes/'+ep['id']+'/episode.json',*['episodes/'+ep['id']+'/0.'+x+'.json' for x in ('raw','start','request','parsed')]]
        for name in names:
            dst=base/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((source/name).read_bytes())
        c.save(root/'config/episodes.json',[ep]);c.save(base/'OFFLINE-FAKE.json',{'real_model_calls':0})
        ledger=c.Ledger(base/'ledger.jsonl');ledger.event(event='reserve',id=ep['id'],amount=c.episode_reservation(ep))
        d=base/'episodes'/ep['id'];request=c.read(d/'0.request.json');start=c.read(d/'0.start.json')
        ledger.event(event='settle',id=start['id'],episode=ep['id'],reserved=request['reservation']['micro_usd'],actual=0)
        dst=root/'fixtures/stopped-claude-raw.json';dst.parent.mkdir();dst.write_bytes((d/'0.raw.json').read_bytes())
        c.save(root/'revisions/r2/preservation.json',{'files':{str((d/'0.raw.json').relative_to(root)):sha((d/'0.raw.json').read_bytes())},'prefixes':{},'parents':{}})
        return base,d

    def test_stopped_clearance_overlay_idempotence_exact_resend_and_old_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base,d=self.prepare_stopped(root)
            originals={p:p.read_bytes() for p in d.glob('*.json')};old_stop=(base/'STOP.json').read_bytes();prefix=(base/'ledger.jsonl').read_bytes()
            with patch('rg_freeze.verify',return_value='r3-digest'):
                record=r.clearance_r3(root);self.assertTrue(record['cleared']);self.assertTrue(r.r3_cleared(root,base))
                self.assertEqual(record,r.clearance_r3(root))
            self.assertTrue((base/'ledger.jsonl').read_bytes().startswith(prefix))
            self.assertEqual(c.Ledger(base/'ledger.jsonl').calls[record['call']],0)
            overlay=episode_directory(base,self.ep['id']);self.assertNotEqual(overlay,d)
            old_request=c.read(d/'0.request.json')
            class Provider(Fake):
                def generate(inner,ep,prompt,phase,budget,work):
                    if inner.calls==0:
                        self.assertEqual(prompt,old_request['prompt']);self.assertEqual(budget,old_request['reservation']['micro_usd'])
                    return super().generate(ep,prompt,phase,budget,work)
            provider=Provider()
            c.run_episode(self.ep,provider,base,c.Ledger(base/'ledger.jsonl'),c.ActiveTime(base/'time.jsonl',7200),'OFFLINE-FAKE',True)
            self.assertEqual(provider.calls,6);self.assertTrue(c.read(overlay/'episode.json')['trajectory_valid'])
            self.assertEqual(a.reconcile(root,base)['status'],'RECONCILED')
            rows,_=a.load_rows(root,base);self.assertTrue(rows[0]['valid'])
            self.assertEqual(len(operational_events(base)),1)
            self.assertEqual((base/'STOP.json').read_bytes(),old_stop)
            for p,data in originals.items():self.assertEqual(p.read_bytes(),data)
            (overlay/'0.request.json').write_text('{}')
            with self.assertRaises(ValueError):episode_directory(base,self.ep['id'])

    def test_collect_resumes_current_stop_with_only_mocked_provider_and_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base,d=self.prepare_stopped(root)
            with patch('rg_freeze.verify',return_value='r3-digest'):
                r.clearance_r3(root)
            (base/'OFFLINE-FAKE.json').unlink()
            ledger=c.Ledger(base/'ledger.jsonl');ledger.carried=True
            provider=Fake();provider.preflight=lambda actor: {'fixture':True}
            with patch('rg_freeze.verify',return_value='r3-digest'),patch('rg_collect.push_gate',return_value='r3-digest'),patch('rg_collect.prior_spend_gate',return_value={}),patch('rg_collect.Ledger',return_value=ledger),patch('rg_collect.Claude',return_value=provider):
                c.collect(root,'claude',binary='mocked-only',freeze_file='freeze-r3.json')
            self.assertEqual(provider.calls,6)
            self.assertTrue(c.read(episode_directory(base,self.ep['id'])/'episode.json')['trajectory_valid'])
            self.assertTrue((base/'STOP.json').exists())

    def test_transport_does_not_bypass_identity_activity_or_reservations(self):
        for changes in ({'modelUsage':{'wrong-model':{}}},{'subagent_stats':{'spawned':1}},
                        {'effort':'high'},{'num_turns':3},
                        {'usage':{**c.provider_envelope(dns(),'claude')[0]['usage'],'input_tokens':999999}}):
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);envelope=c.provider_envelope(dns(),'claude')[0]
                envelope.update(result='ECONNRESET',**changes)
                class Provider(Fake):
                    def generate(inner,*args):return {**dns(),'stdout':canonical(envelope)}
                c.run_episode(self.ep,Provider(),base,c.Ledger(base/'ledger.jsonl'),c.ActiveTime(base/'time.jsonl',7200),'OFFLINE-FAKE',True)
                self.assertTrue((base/'STOP.json').exists())

    def test_r3_freeze_binds_all_three_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root);f.revise(root)
            c.save(root/'revisions/r2/preservation.json',{'files':{},'parents':{},'prefixes':{}})
            f.revise_r2(root)
            parents={n:sha((root/n).read_bytes()) for n in ('freeze.json','freeze-r1.json','freeze-r2.json')}
            digest=f.revise_r3(root);self.assertEqual(c.read(root/'freeze-r3.json')['parents'],parents)
            self.assertEqual(f.verify(root,'freeze-r3.json'),digest)
            with self.assertRaises(FileExistsError):f.revise_r3(root)
