"""Exact saved DNS, schema-400 and foreign 429 regressions. No provider calls."""
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import rg_collect as c
import rg_freeze as f
import rg_revision as r
from rg_core import ROOT, sha
from rg_offline import Fake
from rg_usage_limit import dns_nonstart, refusal, reset_at, operational_events


class SavedR4Tests(unittest.TestCase):
    def setUp(self):
        self.ep=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')

    def test_actual_r3_stop_is_400_and_old_dns_was_correctly_matched(self):
        path=ROOT/'fixtures/stopped-r3-claude-raw.json'
        self.assertEqual(sha(path.read_bytes()),'32e37928e96f691d6345cdf4469aa10771ce8f062d7737b362b503f677fb2330')
        raw=c.read(path);e=c.provider_envelope(raw,'claude')[0]
        self.assertEqual((raw['returncode'],raw['stderr'],e['api_error_status']),(1,'',400))
        self.assertEqual(c.usage(e,'claude'),(0,0));self.assertEqual(e['modelUsage'],{})
        self.assertFalse(dns_nonstart(raw));self.assertFalse(refusal(raw))
        self.assertEqual(r.classify_r4(raw)['class'],'UNKNOWN')
        self.assertTrue(dns_nonstart(c.read(ROOT/'fixtures/stopped-claude-raw.json')))

    def test_returncode_one_reaches_classifier_before_decode_for_dns_and_real_429(self):
        for name,status in [('stopped-claude-raw.json','dns non-start pause'),('real-429-raw.json','usage-limit pause')]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);c.save(root/'config/episodes.json',[self.ep])
                raw=c.read(ROOT/'fixtures'/name)
                class Provider(Fake):
                    def generate(inner,*args):inner.calls+=1;return raw
                provider=Provider()
                with patch('rg_collect.decode',side_effect=AssertionError('non-start reached decode')):
                    pause=c.collect(root,'claude',fake_transport=provider)
                self.assertEqual(pause['status'],status);self.assertEqual(provider.calls,1)
                ledger=c.Ledger(root/'collection/ledger.jsonl')
                self.assertEqual(ledger.calls[pause['id']],0);self.assertIn(pause['id'],ledger.nonstarts)
                self.assertFalse((root/'collection/STOP.json').exists())

    def test_actual_400_is_now_a_harness_pause_before_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.save(root/'config/episodes.json',[self.ep])
            class Provider(Fake):
                def generate(inner,*args):inner.calls+=1;return c.read(ROOT/'fixtures/stopped-r3-claude-raw.json')
            provider=Provider()
            with patch('rg_collect.decode',side_effect=AssertionError('non-start reached decode')):
                pause=c.collect(root,'claude',fake_transport=provider)
            self.assertEqual(pause['status'],'harness non-start pause')
            self.assertEqual(provider.calls,1)
            self.assertFalse((root/'collection/STOP.json').exists())
            self.assertEqual(c.Ledger(root/'collection/ledger.jsonl').calls[pause['id']],0)

    def test_real_429_source_bytes_reset_gate_identical_resume_and_accounting(self):
        source=ROOT/'revisions/r4/real-429-source'
        provenance=c.read(ROOT/'revisions/r4/real-429-provenance.json')
        for name,digest in provenance['files'].items():self.assertEqual(sha((source/name).read_bytes()),digest)
        raw=c.read(ROOT/'fixtures/real-429-raw.json')
        self.assertEqual(raw['stdout'].encode(),(source/'stdout').read_bytes())
        self.assertEqual(raw['stderr'].encode(),(source/'stderr').read_bytes())
        self.assertEqual(raw['returncode'],c.read(source/'raw.json')['returncode'])
        self.assertTrue(refusal(raw))
        self.assertEqual(reset_at(raw,c.read(source/'start.json')['started_at']),'2026-11-11T18:30:00+00:00')
        class Clock(dt.datetime):
            value=dt.datetime(2026,11,11,17,35,tzinfo=dt.timezone.utc)
            @classmethod
            def now(cls,tz=None):return cls.value if tz is None else cls.value.astimezone(tz)
        with tempfile.TemporaryDirectory() as tmp,patch('rg_collect.dt.datetime',Clock):
            root=Path(tmp);c.save(root/'config/episodes.json',[self.ep])
            class Provider(Fake):
                def __init__(inner):super().__init__();inner.requests=[]
                def generate(inner,*args):
                    inner.requests.append(args[:4])
                    return raw if len(inner.requests)==1 else super().generate(*args)
            provider=Provider();pause=c.collect(root,'claude',fake_transport=provider)
            self.assertEqual(c.collect(root,'claude',fake_transport=provider),pause)
            self.assertEqual(len(provider.requests),1)
            Clock.value=dt.datetime(2026,11,11,18,31,tzinfo=dt.timezone.utc)
            c.collect(root,'claude',fake_transport=provider)
            self.assertEqual(provider.requests[0],provider.requests[1])
            self.assertEqual(len(operational_events(root/'collection')),1)
            import rg_analysis as a
            self.assertEqual(a.reconcile(root,root/'collection')['status'],'RECONCILED')
            self.assertEqual(c.Ledger(root/'collection/ledger.jsonl').holds[self.ep['id']],0)

    def test_r4_seals_four_parents_and_is_create_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root);f.revise(root)
            c.save(root/'revisions/r2/preservation.json',{'files':{},'parents':{},'prefixes':{}})
            f.revise_r2(root);f.revise_r3(root)
            parents={n:sha((root/n).read_bytes()) for n in ('freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json')}
            c.save(root/'revisions/r4/preservation.json',{'files':{},'parents':parents,'prefixes':{}})
            digest=f.revise_r4(root)
            self.assertEqual(c.read(root/'freeze-r4.json')['parents'],parents)
            self.assertEqual(f.verify(root,'freeze-r4.json'),digest)
            with self.assertRaises(FileExistsError):f.revise_r4(root)
            c.save(root/'collection/push-r3.json',{'historical':'unchanged'})
            old=(root/'collection/push-r3.json').read_bytes()
            c.save(root/'event.json',{'activity_type':'push','after':'a'*40,'ref':'refs/heads/test',
                   'timestamp':c.read(root/'freeze-r4.json')['created_at'],'id':'r4-test'})
            checked=[]
            def fake_git(cmd,**kwargs):
                if cmd[1:]==['rev-parse','HEAD']:return 'a'*40+'\n'
                if cmd[1:]==['remote','get-url','origin']:return 'https://github.com/Robin84Bran/research.git\n'
                if cmd[1]=='show':
                    name=cmd[2].split(':receipt-gap/v0.2/')[1];checked.append(name)
                    return (root/name).read_bytes()
                if cmd[1]=='ls-remote':return 'a'*40+'\trefs/heads/test\n'
                raise AssertionError(cmd)
            with patch('rg_freeze.subprocess.check_output',side_effect=fake_git):
                self.assertEqual(f.attest(root,root/'event.json','a'*40,'receipt-gap/v0.2',root,'freeze-r4.json'),digest)
            self.assertTrue(set(parents)<=set(checked))
            self.assertEqual((root/'collection/push-r3.json').read_bytes(),old)
            self.assertEqual(c.read(root/'collection/push-r4.json')['freeze_sha256'],digest)

    def test_r4_unknown_clearance_is_bound_idempotent_and_cannot_collect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'collection'
            d=base/'resumes/r3/episodes'/self.ep['id']
            for src,name in [(ROOT/'fixtures/stopped-r3-claude-raw.json','dispatches/0/1/raw.json'),
                             (ROOT/'revisions/r2/saved/collection/episodes'/self.ep['id']/'0.request.json','0.request.json')]:
                target=d/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
            target=root/'fixtures/stopped-r3-claude-raw.json';target.parent.mkdir();target.write_bytes((d/'dispatches/0/1/raw.json').read_bytes())
            c.save(base/'STOP-r3.json',{'reason':'transport failure or uncertain start'})
            with patch('rg_freeze.verify',return_value='r4-digest'),patch('rg_revision.verify_r4_preservation'):
                record=r.clearance_r4(root);self.assertFalse(record['cleared']);self.assertEqual(record['status'],'UNKNOWN')
                self.assertEqual(record,r.clearance_r4(root))
            with patch('rg_collect.Claude',side_effect=AssertionError('provider constructed')):
                with self.assertRaisesRegex(c.Stop,'requires programme ruling'):
                    c.collect(root,'claude',binary='mocked-only',freeze_file='freeze-r4.json')
            self.assertFalse((base/'ledger.jsonl').exists())
