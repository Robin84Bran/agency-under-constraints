"""D1 uses saved envelopes and fake transports only; no provider or Git calls."""
import ast
import copy
import datetime as dt
from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from od_core import ROOT,canonical,render,reserve,schedule,sha
from od_io import Stop,read,save,Ledger,Log
from od_transport import Fake,raw_record
from od_collect import collect
from od_analysis import replay,analyze_rows
from od_validation import validate,accounting,cost,ReplyFailure
from od_usage import refusal,reset_at,episode_state,directories,clear_usage_stop,stop_cleared,verify_prefixes,prefix_snapshot


@contextmanager
def at(hour,minute=0):
    class Clock(dt.datetime):
        @classmethod
        def now(cls,tz=None):
            v=cls(2026,11,11,hour,minute,tzinfo=dt.timezone.utc)
            return v.astimezone(tz) if tz else v.replace(tzinfo=None)
    with patch('od_usage.dt.datetime',Clock): yield


def raw(e=None): return raw_record(canonical(e if e is not None else read(ROOT/'fixtures/usage-limit-envelope.json')).encode(),returncode=1)


class Sequence(Fake):
    def __init__(self,refuse_on): super().__init__();self.refuse_on=set(refuse_on);self.requests=[]
    def generate(self,ep,req,work):
        self.requests.append(copy.deepcopy(req))
        if len(self.requests) in self.refuse_on:
            self.calls.append(ep['id']);return raw()
        return super().generate(ep,req,work)


class D1(unittest.TestCase):
    def jobs(self,n=3): return [e for e in schedule() if e['actor']=='claude'][:n]
    def test_classifier_exact_and_real_envelope(self):
        self.assertIsNotNone(refusal(raw()))
        e=read(ROOT/'fixtures/usage-limit-envelope.json')
        edits=[lambda e:e.update(api_error_status=500),lambda e:e.update(is_error=False),lambda e:e.update(total_cost_usd=0.000000001),lambda e:e.pop('total_cost_usd'),lambda e:e.update(total_cost_usd='0'),lambda e:e.update(structured_output={'fleet':6}),lambda e:e.update(result='other error'),lambda e:e.update(permission_denials=['tool']),lambda e:e.update(api_error_status=True),lambda e:e['usage'].update(server_tool_use={'web_search_requests':1}),lambda e:e.update(subagent_stats={'spawned':1})]
        for key in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            edits.extend([lambda e,k=key:e['usage'].update({k:1}),lambda e,k=key:e['usage'].pop(k),lambda e,k=key:e['usage'].update({k:False})])
        edits.append(lambda e:e['usage'].update(output_tokens_details={'thinking_tokens':1}))
        for edit in edits:
            bad=copy.deepcopy(e);edit(bad)
            with self.subTest(bad=bad): self.assertIsNone(refusal(raw(bad)))
        for modified in (dict(raw(),harness_error='bug'),dict(raw(),returncode=True),dict(raw(),returncode=2),raw_record(b'{',returncode=1)):
            self.assertIsNone(refusal(modified))
        real=read(ROOT/'fixtures/real-claude-envelope.json');r=raw_record((ROOT/'fixtures/real-claude-envelope.json').read_bytes())
        self.assertIsNone(refusal(r));self.assertEqual(cost(accounting(r,'claude')),16788)
        b=reserve(render(self.jobs()[0]))
        # Real metadata passes; this sibling payload is correctly rejected by our schema.
        with self.assertRaises(ReplyFailure): validate(r,'claude',b)
        real['structured_output']={'fleet':6}
        self.assertTrue(validate(raw_record(canonical(real).encode()),'claude',b)['schema_valid'])
        real['subagent_stats']['spawned']=1
        with self.assertRaises(Stop):validate(raw_record(canonical(real).encode()),'claude',b)
    def test_pause_restart_mid_cohort_identical_request_and_operational_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();fake=Sequence({2,3})
            with at(13):
                out=collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(out['kind'],'usage-limit pause');self.assertEqual(len(fake.calls),2)
                rows,l=replay(ROOT,base,True,jobs)
                self.assertEqual([r['attempted'] for r in rows],[True,False,False]);self.assertEqual(l['open_holds_micro_usd'],0)
                self.assertEqual(l['operational_events']['usage_limit_refusals'],1)
                self.assertEqual(sum(c['technical'] for c in analyze_rows(rows)['cells'].values()),0)
                self.assertFalse((base/'STOP.json').exists())
                saved={p:p.read_bytes() for p in (base/'episodes').rglob('*.json')}
                out=collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(out['kind'],'usage-limit pause');self.assertEqual(len(fake.calls),2)
            # A second daily refusal pauses again, retaining both attempts.
            with at(13,31):
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),3)
                rows,l=replay(ROOT,base,True,jobs)
                self.assertEqual(l['operational_events']['usage_limit_refusals'],2)
            with at(13,32):
                # The next same-day invocation is before tomorrow's stated reset.
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),3)
            # Move to the following day after reset.
            class Tomorrow(dt.datetime):
                @classmethod
                def now(cls,tz=None): return cls(2026,11,12,13,31,tzinfo=dt.timezone.utc)
            with patch('od_usage.dt.datetime',Tomorrow):
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                rows,l=replay(ROOT,base,True,jobs)
            self.assertEqual(fake.calls,[jobs[0]['id'],jobs[1]['id'],jobs[1]['id'],jobs[1]['id'],jobs[2]['id']])
            self.assertEqual(fake.requests[1],fake.requests[2]);self.assertEqual(fake.requests[1],fake.requests[3])
            self.assertTrue(all(r['schema_valid'] for r in rows));self.assertEqual(l['spent_micro_usd'],6000)
            for p,data in saved.items():self.assertEqual(p.read_bytes(),data)
            ds=directories(base,jobs[1]['id']);self.assertTrue(all((p/'request.json').read_bytes()==(ds[0]/'request.json').read_bytes() for p in ds))
            prefix=prefix_snapshot(base);Log(base/'ledger.jsonl').append({'event':'bad','id':'bad'})
            verify_prefixes(base,prefix) # Full valid append-only hash tail, semantic ledger still rejects.
            with self.assertRaises(Stop):Ledger(base/'ledger.jsonl')
    def test_first_nonstart_resumes_first_compatibility_call(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs(1);fake=Sequence({1})
            with at(13):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            with at(13,31):
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs);replay(ROOT,base,True,jobs)
            self.assertTrue(read(episode_state(base,jobs[0]['id'])[0]/'episode.json')['first_frozen_compatibility_check'])
    def test_ambiguous_errors_fatal_no_resend(self):
        for edit in (lambda e:e.update(total_cost_usd=1),lambda e:e.update(api_error_status=503)):
            e=read(ROOT/'fixtures/usage-limit-envelope.json');edit(e)
            class Bad(Fake):
                def generate(self,*args):self.calls.append(args[0]['id']);return raw(e)
            with tempfile.TemporaryDirectory() as d:
                base=Path(d)/'out';fake=Bad()
                with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=self.jobs())
                with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=self.jobs())
                self.assertEqual(len(fake.calls),1);self.assertTrue((base/'STOP.json').exists())
    def test_missing_pause_marker_is_uncertain_and_request_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs(1);fake=Sequence({1})
            with at(13):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            p=base/'episodes'/jobs[0]['id'];marker=(p/'nonstart.json').read_bytes();(p/'nonstart.json').unlink()
            with self.assertRaises(Stop):episode_state(base,jobs[0]['id'])
            (p/'nonstart.json').write_bytes(marker);(p/'request.json').write_bytes((p/'request.json').read_bytes()+b' ')
            with self.assertRaises(Stop):episode_state(base,jobs[0]['id'])
    def test_historical_clearance_retains_terminal_stop_and_prefixes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'collection';jobs=self.jobs(1);fake=Sequence({1})
            with at(13):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            p=base/'episodes'/jobs[0]['id'];m=read(p/'nonstart.json');(p/'nonstart.json').unlink()
            save(p/'episode.json',{'fatal':'transport failure/uncertain start; never resend','finished_at':m['finished_at']})
            save(base/'STOP.json',{'reason':'transport failure/uncertain start; never resend'})
            save(root/'config/episodes.json',jobs)
            old={x:x.read_bytes() for x in (p/'episode.json',base/'STOP.json',p/'raw.json',base/'ledger.jsonl')}
            with patch('od_freeze.verify',return_value='TEST'):
                clear_usage_stop(root);self.assertTrue(stop_cleared(base));clear_usage_stop(root)
            for x,data in old.items():self.assertEqual(x.read_bytes(),data)
            rows,l=replay(ROOT,base,True,jobs);self.assertFalse(rows[0]['attempted'])
            with at(13,31):
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs);replay(ROOT,base,True,jobs)
            self.assertTrue(stop_cleared(base));self.assertEqual(len(fake.calls),2)
            current=(base/'ledger.jsonl').read_bytes();(base/'ledger.jsonl').write_bytes(current.splitlines(keepends=True)[0])
            with self.assertRaises(Stop):stop_cleared(base)
    def test_science_unchanged(self):
        old=ast.parse((ROOT/'deviations/d1/parent-a1/od_analysis.py').read_text());new=ast.parse((ROOT/'od_analysis.py').read_text())
        functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name not in ('replay','analysis')}
        self.assertEqual(functions(old),functions(new))
        from od_d1 import D1_CHANGED
        from od_d2 import D2_CHANGED
        for n,h in read(ROOT/'freeze-a1.json')['files'].items():
            if n not in D1_CHANGED|D2_CHANGED:self.assertEqual(sha((ROOT/n).read_bytes()),h,n)
    def package(self,root):
        from od_freeze import inputs
        from od_d2 import D2_CHANGED
        for name in list(read(ROOT/'freeze-d1-final.json')['files'])+['freeze.json','freeze-a1.json']:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
            source=ROOT/'deviations/d2/parent-d1-final'/name if name in D2_CHANGED else ROOT/name
            shutil.copyfile(source,p)
    def test_d1_freeze_parent_scope_and_attestation_gate(self):
        from od_d1 import freeze_d1,verify_d1,d1_gate,attest_d1
        from od_freeze import push_gate
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.package(root)
            # Isolated offline runtime: no real study records are copied or changed.
            save(root/'collection/push.json',read(ROOT/'collection/push.json'))
            shutil.copyfile(ROOT/'collection/push-event.json',root/'collection/push-event.json')
            before={n:(root/n).read_bytes() for n in ('freeze.json','freeze-a1.json','collection/push.json')}
            with patch('od_d1.verify_baseline'):
                h=freeze_d1(root)
                self.assertEqual(verify_d1(root),h)
                with self.assertRaises(FileExistsError):freeze_d1(root)
                with self.assertRaises(FileNotFoundError):push_gate(root)
                with patch('od_analysis.replay',return_value=([],{})):
                    record=attest_d1(root);self.assertEqual(record['freeze_sha256'],h)
                    self.assertEqual(attest_d1(root),record)
                self.assertEqual(push_gate(root),h)
            for n,data in before.items():self.assertEqual((root/n).read_bytes(),data)
            # Attested prefixes allow growth, and fully validate each new prefix checkpoint.
            Ledger(root/'collection/ledger.jsonl').event(event='reserve',id='fake',amount=100)
            d1_gate(root)
            p=root/'collection/ledger.jsonl';p.write_bytes(p.read_bytes().replace(b'100',b'101'))
            with self.assertRaises(Stop):d1_gate(root)
            p=root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
            f=read(root/'freeze-d1.json');f['files']['config/prompts.json']=sha(p.read_bytes())
            (root/'freeze-d1.json').write_text(canonical(f))
            with self.assertRaisesRegex(Stop,'forbidden science'):verify_d1(root)
            (root/'freeze-a1.json').write_bytes(before['freeze-a1.json']+b' ')
            with self.assertRaisesRegex(Stop,'parent freeze'):verify_d1(root)
    def test_nonstart_settlement_timer_and_reset_evidence_required(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs(1);fake=Sequence({1})
            with at(13):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            ledger=base/'ledger.jsonl';data=ledger.read_bytes();ledger.write_bytes(data.splitlines(keepends=True)[0])
            with self.assertRaises(Stop):replay(ROOT,base,True,jobs)
            ledger.write_bytes(data)
            marker=base/'episodes'/jobs[0]['id']/'nonstart.json';m=read(marker);m['reset_at']='2026-11-11T13:01:00+00:00';marker.write_text(canonical(m))
            with self.assertRaises(Stop):episode_state(base,jobs[0]['id'])
    def test_clearance_never_unlocks_a_later_fatal_stop(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'collection';jobs=self.jobs(1);fake=Sequence({1})
            with at(13):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            p=base/'episodes'/jobs[0]['id'];m=read(p/'nonstart.json');(p/'nonstart.json').unlink()
            save(p/'episode.json',{'fatal':'transport failure/uncertain start; never resend','finished_at':m['finished_at']})
            save(base/'STOP.json',{'reason':'transport failure/uncertain start; never resend'})
            original=(base/'STOP.json').read_bytes();save(root/'config/episodes.json',jobs)
            with patch('od_freeze.verify',return_value='TEST'):clear_usage_stop(root)
            self.assertTrue(stop_cleared(base))
            class BrokenPreflight(Fake):
                def preflight(self,actor): raise Stop('later identity failure')
            with at(13,31),self.assertRaisesRegex(Stop,'later identity failure'):
                collect(ROOT,'claude',fake_transport=BrokenPreflight(),output=base,jobs_override=jobs)
            self.assertEqual((base/'STOP.json').read_bytes(),original)
            self.assertEqual(read(base/'STOP-after-usage-clearance.json')['reason'],'later identity failure')
            self.assertFalse(stop_cleared(base))
            with at(13,32),self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertEqual(len(fake.calls),1)
