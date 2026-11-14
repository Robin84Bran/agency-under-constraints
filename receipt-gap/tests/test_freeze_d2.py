"""D2 offline regressions. Fake transports and mocked Git only."""
import copy
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rg_collect
import rg_freeze
from rg_analysis import load_rows, reconcile, score
from rg_collect import (ActiveTime, Ledger, Stop, collect, cost_micro, d2_resume_gate,
                        decode, push_gate, read, run_episode, save, usage)
from rg_core import ROOT, canonical, render, reserve, sha, strict_load
from rg_freeze import attest, freeze_d1, freeze_d2, verify
from rg_offline import Fake
import test_freeze_d1 as d1_fixture

ACTIVITY, COMMIT = d1_fixture.ACTIVITY, d1_fixture.COMMIT


class SchemaFake(Fake):
    def generate(self, *args, **kwargs):
        raw = super().generate(*args, **kwargs)
        e = strict_load(raw['stdout'])
        e.update(num_turns=2, stop_reason='tool_use')
        raw['stdout'] = canonical(e)
        return raw


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.ep = next(e for e in read(ROOT/'config/episodes.json') if e['actor']=='claude')
        self.prompt = render(self.ep, [], 10, 'action')
        self.bound = reserve(self.prompt, 'action')
        self.raw = SchemaFake().generate(self.ep,self.prompt,'action',10000,ROOT)

    def changed(self, **changes):
        raw = dict(self.raw)
        e = strict_load(raw['stdout']); e.update(changes)
        raw['stdout'] = canonical(e)
        return raw

    def test_one_and_schema_tool_turns(self):
        for turns, reason in ((1,'end_turn'),(1,'tool_use'),(2,'tool_use')):
            with self.subTest(turns=turns, reason=reason):
                v = decode(self.changed(num_turns=turns, stop_reason=reason),self.ep,'action',self.bound)
                self.assertEqual(v, {'op':'send','job':1,'key':None})

    def test_all_other_turn_shapes_fatal(self):
        for turns in (None,0,3,4,-1,True,False,1.0,2.0,'1','2'):
            with self.subTest(turns=turns), self.assertRaises(Stop):
                decode(self.changed(num_turns=turns),self.ep,'action',self.bound)
        for reason in (None,'end_turn',''):
            with self.subTest(reason=reason), self.assertRaises(Stop):
                decode(self.changed(stop_reason=reason),self.ep,'action',self.bound)

    def test_no_missing_string_or_result_fallback(self):
        for value in (None,[],canonical({'op':'send','job':1,'key':None})):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode(self.changed(structured_output=value),self.ep,'action',self.bound)
        raw = self.changed(); e = strict_load(raw['stdout'])
        del e['structured_output']; e['result'] = '{"op":"send","job":1,"key":null}'
        raw['stdout'] = canonical(e)
        with self.assertRaises(ValueError): decode(raw,self.ep,'action',self.bound)

    def test_strict_frozen_action_and_report_validators(self):
        for value in ({'op':'send','job':True,'key':None}, {'op':'send','job':1,'key':'x'},
                      {'op':'send','job':1,'key':None,'extra':0}, {},
                      {'op':'status','job':None,'key':None}):
            with self.subTest(value=value), self.assertRaises((Stop,ValueError)):
                decode(self.changed(structured_output=value),self.ep,'action',self.bound)
        valid = {'all_done':None,'any_duplicate':False}
        self.assertEqual(decode(self.changed(structured_output=valid),self.ep,'report',self.bound),valid)
        for value in ({'all_done':1,'any_duplicate':False}, {'all_done':False},
                      {'all_done':True,'any_duplicate':False,'extra':None}):
            with self.subTest(value=value), self.assertRaises((Stop,ValueError)):
                decode(self.changed(structured_output=value),self.ep,'report',self.bound)

    def test_duplicate_keys_and_identity_usage_gates(self):
        for changes in ({'type':'assistant'}, {'subtype':'error_max_turns'}, {'is_error':True},
                        {'modelUsage':{'other':{}}}, {'effort':'high'},
                        {'usage':{'input_tokens':0,'output_tokens':1}},
                        {'usage':{'input_tokens':100000,'cache_read_input_tokens':0,'cache_creation_input_tokens':0,'output_tokens':1}}):
            with self.subTest(changes=changes), self.assertRaises(Stop):
                decode(self.changed(**changes),self.ep,'action',self.bound)
        raw = self.changed(); raw['stdout'] = raw['stdout'].replace('"num_turns":2','"num_turns":2,"num_turns":1')
        with self.assertRaises(Stop):decode(raw,self.ep,'action',self.bound)

    def test_cache_classes_and_thinking_not_double_counted(self):
        e = {'usage':{'input_tokens':2,'cache_creation_input_tokens':1600,'cache_read_input_tokens':300,
                     'output_tokens':199,'output_tokens_details':{'thinking_tokens':105},
                     'cache_creation':{'ephemeral_1h_input_tokens':1600}}}
        self.assertEqual(usage(e,'claude'),(1902,199))
        for key in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens'):
            for bad in (None,True,-1,'0',0.0):
                changed = copy.deepcopy(e); changed['usage'][key] = bad
                self.assertEqual(usage(changed,'claude'),(None,199))
        self.assertEqual(cost_micro(1602,199,{'total_cost_usd':0.016788}),16788)

    def test_real_saved_reply_valid_but_terminal_failure_preserved(self):
        d = ROOT/'collection/episodes'/self.ep['id']
        if not (d/'0.raw.json').exists():
            self.skipTest('saved study data is intentionally absent from code-only clone')
        raw = read(d/'0.raw.json'); req = read(d/'0.request.json')
        before = {p.name:p.read_bytes() for p in d.iterdir()}
        self.assertEqual(decode(raw,self.ep,'action',req['reservation']),{'op':'send','job':1,'key':None})
        self.assertEqual(usage(strict_load(raw['stdout']),'claude'),(1602,199))
        row = score(self.ep,read(d/'episode.json'),True)
        self.assertFalse(row['valid']); self.assertEqual(row['Dstar'],1)
        self.assertEqual((row['Sstar'],row['J'],row['counts']),(0,0,[0,0,0,0]))
        self.assertEqual({p.name:p.read_bytes() for p in d.iterdir()},before)


class AmendmentTests(unittest.TestCase):
    git = d1_fixture.D1Tests.git

    def setUp(self):
        d1_fixture.D1Tests.setUp(self)
        self.d1 = freeze_d1(self.root)
        self.pin_d1 = patch('rg_freeze.D1_FREEZE_SHA256',self.d1)
        self.pin_d1.start(); self.addCleanup(self.pin_d1.stop)
        with patch('rg_freeze.subprocess.check_output',side_effect=self.git):
            attest(self.root,self.event_file,COMMIT,'projects/receipt-gap',self.clone)
        self.base = self.root/'collection'
        self.ep = next(e for e in read(self.root/'config/episodes.json') if e['actor']=='claude')
        self.old_time = '2026-11-11T09:13:52+00:00'
        with patch('rg_collect.now',return_value=self.old_time):
            run_episode(self.ep,Fake('wrong_effort'),self.base,Ledger(self.base/'ledger.jsonl'),
                        ActiveTime(self.base/'claude-time.jsonl',7200),self.d1,True)
        files={p.relative_to(self.base).as_posix():sha(p.read_bytes()) for p in self.base.rglob('*') if p.is_file() and p.name!='collector.lock'}
        self.baseline={'stopped_episode':self.ep['id'],'files':files,
                       'sizes':{n:(self.base/n).stat().st_size for n in files}}
        save(self.root/'evidence/d2-baseline.json',self.baseline)
        (self.root/'RUN-d2.md').write_text('D2 fixture run instructions\n')
        (self.root/'tests').mkdir(exist_ok=True)
        (self.root/'tests/test_freeze_d2.py').write_text('D2 fixture tests\n')
        self.before={n:(self.base/n).read_bytes() for n in files}
        self.parents={n:(self.root/n).read_bytes() for n in ('freeze.json','freeze-d1.json')}

    def make(self):
        return freeze_d2(self.root)

    def attest_d2(self):
        # Emulate a server record after the amendment exists, without any network.
        event={**ACTIVITY,'id':'new-d2-event','timestamp':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(milliseconds=1)).isoformat()}
        event_file=self.root/'new-event.bin'
        event_file.write_text(canonical(event))
        with patch('rg_freeze.subprocess.check_output',side_effect=self.git):
            attest(self.root,event_file,COMMIT,'projects/receipt-gap',self.clone)

    def test_parent_binding_scientific_preservation_and_create_once(self):
        digest=self.make(); f=read(self.root/'freeze-d2.json'); parent=read(self.root/'freeze-d1.json')
        self.assertEqual(verify(self.root),digest)
        self.assertEqual(f['parent_freeze_sha256'],self.d1)
        self.assertEqual(f['original_freeze_sha256'],self.parent_hash)
        for name, expected in parent['files'].items():
            self.assertEqual(f['files'][name],expected)
        self.assertEqual({n:(self.root/n).read_bytes() for n in self.parents},self.parents)
        with self.assertRaises(FileExistsError): self.make()

    def test_scope_cannot_change_science_or_remove_input(self):
        for name in ('rg_core.py','config/design.json','config/action-schema.json','config/episodes.json'):
            p=self.root/name; old=p.read_bytes() if p.exists() else None; p.write_bytes((old or b'')+b' ')
            with self.subTest(name=name),self.assertRaises(Stop):self.make()
            if old is None:p.unlink()
            else:p.write_bytes(old)
        p=self.root/'rg_core.py'; old=p.read_bytes(); p.unlink()
        with self.assertRaises(Stop):self.make()
        p.write_bytes(old)
        (self.root/'extra.py').write_text('unlisted\n')
        with self.assertRaises(Stop):self.make()

    def test_rebinding_manifest_cannot_hide_scientific_change(self):
        self.make(); p=self.root/'config/design.json'; p.write_text('{}\n')
        f=read(self.root/'freeze-d2.json'); f['files']['config/design.json']=sha(p.read_bytes())
        (self.root/'freeze-d2.json').write_text(canonical(f))
        with self.assertRaises(Stop):verify(self.root)

    def test_parent_and_metadata_tamper_rejected(self):
        self.make()
        for name in self.parents:
            p=self.root/name; p.write_bytes(self.parents[name]+b' ')
            with self.subTest(name=name),self.assertRaises(Stop):verify(self.root)
            p.write_bytes(self.parents[name])
        p=self.root/'freeze-d2.json'; original=p.read_bytes(); f=read(p)
        for change in ({'parent_freeze_sha256':'0'*64},{'original_freeze_sha256':'0'*64},
                       {'deviation':'D3'},{'planned_episodes':1861}):
            p.write_text(canonical({**f,**change}))
            with self.subTest(change=change),self.assertRaises(Stop):verify(self.root)
        p.write_bytes(original)

    def test_d1_attestation_does_not_open_d2_gate(self):
        self.make()
        with self.assertRaises(FileNotFoundError):push_gate(self.root)

    def test_separate_attestation_gate_and_preserved_evidence(self):
        digest=self.make(); self.attest_d2()
        self.assertEqual(push_gate(self.root),digest)
        self.assertEqual(read(self.base/'push-d2.json')['freeze_file'],'freeze-d2.json')
        self.assertEqual({n:(self.base/n).read_bytes() for n in self.before},self.before)
        with self.assertRaises(FileExistsError):self.attest_d2()
        d2_resume_gate(self.root,self.base)

    def test_attestation_checks_middle_freeze_in_clone(self):
        self.make()
        def git(cmd,**kw):
            if cmd[1]=='show' and cmd[2].endswith('/freeze-d1.json'):return b'wrong middle freeze'
            return self.git(cmd,**kw)
        with patch('rg_freeze.subprocess.check_output',side_effect=git),self.assertRaises(Stop):
            attest(self.root,self.event_file,COMMIT,'projects/receipt-gap',self.clone)
        self.assertFalse((self.base/'push-d2.json').exists())

    def test_narrow_stop_and_terminal_binding(self):
        self.make()
        for name in ('STOP.json','episodes/'+self.ep['id']+'/episode.json','push.json'):
            p=self.base/name; old=p.read_bytes(); p.write_bytes(old+b' ')
            with self.subTest(name=name),self.assertRaises(Stop):d2_resume_gate(self.root,self.base)
            p.write_bytes(old)
        p=self.base/'episodes'/self.ep['id']/'1.start.json'; save(p,{'id':'forbidden continuation'})
        with self.assertRaises(Stop):d2_resume_gate(self.root,self.base)

    def test_ledger_and_timer_prefix_cannot_reset_but_may_append(self):
        self.make()
        for name in ('ledger.jsonl','claude-time.jsonl'):
            p=self.base/name; old=p.read_bytes(); p.write_bytes(old[1:])
            with self.subTest(name=name),self.assertRaises(Stop):d2_resume_gate(self.root,self.base)
            p.write_bytes(old+b' ')
            d2_resume_gate(self.root,self.base)
            p.write_bytes(old)

    def test_parent_starts_and_new_push_order(self):
        digest=self.make(); self.attest_d2()
        d=self.base/'episodes/new'; start=d/'0.start.json'
        pushed=read(self.base/'push-d2.json')['pushed_at']
        save(start,{'freeze_sha256':digest,'started_at':pushed})
        with self.assertRaises(Stop):push_gate(self.root)
        start.write_text(canonical({'freeze_sha256':digest,'started_at':rg_collect.now()}))
        self.assertEqual(push_gate(self.root),digest)
        start.write_text(canonical({'freeze_sha256':self.d1,'started_at':rg_collect.now()}))
        with self.assertRaises(Stop):push_gate(self.root)

    def test_resume_skips_terminal_preserves_charges_and_new_stop_blocks(self):
        digest=self.make(); self.attest_d2()
        # Only two scheduled frontier episodes are relevant to this offline fixture.
        schedule=read(self.root/'config/episodes.json')
        next_ep=next(e for e in schedule if e['actor']=='claude' and e!=self.ep)
        original_read=rg_collect.read
        def small_read(path):
            if Path(path)==self.root/'config/episodes.json':return [self.ep,next_ep]
            return original_read(path)
        transport=SchemaFake()
        with patch('rg_collect.read',side_effect=small_read), patch('rg_collect.Claude',return_value=transport), patch.object(transport,'preflight',return_value={'offline':True},create=True):
            result=collect(self.root,'claude',binary='never-executed')
        self.assertEqual(transport.calls,6)
        self.assertEqual({n:(self.base/n).read_bytes() for n in self.before if n not in ('ledger.jsonl','claude-time.jsonl')},
                         {n:b for n,b in self.before.items() if n not in ('ledger.jsonl','claude-time.jsonl')})
        ledger=Ledger(self.base/'ledger.jsonl')
        self.assertEqual(ledger.holds[self.ep['id']],262912-22016)
        self.assertEqual(ledger.calls[self.ep['id']+'-0'],1200)
        self.assertGreater(result['active_seconds'],0)
        rows,maxima=load_rows(self.root,self.base)
        row=next(r for r in rows if r['id']==next_ep['id'])
        self.assertTrue(row['valid'])
        costs=reconcile(self.root,self.base)
        self.assertEqual(costs['outstanding_micro_usd'],ledger.holds[self.ep['id']])
        save(self.base/'STOP-d2.json',{'reason':'new fatal stop'})
        with patch('rg_collect.Claude') as provider,self.assertRaises(Stop):collect(self.root,'claude',binary='never-executed')
        provider.assert_not_called()
        with self.assertRaises(Stop):run_episode(self.ep,SchemaFake(),self.base,ledger,ActiveTime(self.base/'claude-time.jsonl',7200),digest)

    def test_new_frontier_identity_mismatch_still_global_stop(self):
        self.make(); self.attest_d2()
        next_ep=next(e for e in read(self.root/'config/episodes.json') if e['actor']=='claude' and e!=self.ep)
        out=run_episode(next_ep,SchemaFake('wrong_model'),self.base,Ledger(self.base/'ledger.jsonl'),
                        ActiveTime(self.base/'claude-time.jsonl',7200),'offline',True,'STOP-d2.json')
        self.assertTrue((self.base/'STOP.json').exists())
        self.assertTrue((self.base/'STOP-d2.json').exists())
        self.assertFalse(out['trajectory_valid'])

    def test_schema_invalid_action_or_report_is_episode_local_without_resend(self):
        class Invalid(SchemaFake):
            def generate(self, ep, prompt, phase, budget, work):
                raw=super().generate(ep,prompt,phase,budget,work)
                if phase==self.bad_phase:
                    e=strict_load(raw['stdout']); e['structured_output']={}
                    raw['stdout']=canonical(e)
                return raw
        for phase in ('action','report'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp); provider=Invalid(); provider.bad_phase=phase
                out=run_episode(self.ep,provider,base,Ledger(base/'ledger.jsonl'),
                                ActiveTime(base/'time.jsonl',7200),'OFFLINE-FAKE',True)
                self.assertFalse((base/'STOP.json').exists())
                self.assertIsNone(out['report'])
                self.assertEqual(Ledger(base/'ledger.jsonl').holds[self.ep['id']],0)
                self.assertEqual(provider.calls,1 if phase=='action' else 6)
                self.assertEqual(out['trajectory_valid'],phase=='report')

    def test_deleted_original_stop_never_opens_collection(self):
        self.make(); self.attest_d2()
        (self.base/'STOP.json').unlink()  # Fixture copy only; production evidence is untouched.
        with patch('rg_collect.Claude') as provider,self.assertRaises(FileNotFoundError):
            collect(self.root,'claude',binary='never-executed')
        provider.assert_not_called()

    def test_replay_rejects_invalid_two_turn_reason_and_wrong_provenance(self):
        digest=self.make(); self.attest_d2()
        next_ep=next(e for e in read(self.root/'config/episodes.json') if e['actor']=='claude' and e!=self.ep)
        run_episode(next_ep,SchemaFake(),self.base,Ledger(self.base/'ledger.jsonl'),
                    ActiveTime(self.base/'claude-time.jsonl',7200),digest,True,'STOP-d2.json')
        d=self.base/'episodes'/next_ep['id']; path=d/'0.raw.json'; before=path.read_bytes()
        raw=read(path); envelope=strict_load(raw['stdout']); envelope['stop_reason']='end_turn'
        raw['stdout']=canonical(envelope); path.write_text(canonical(raw))
        with self.assertRaises(ValueError):load_rows(self.root,self.base)
        path.write_bytes(before)
        start=d/'0.start.json'; old=start.read_bytes(); value=read(start)
        value['freeze_sha256']=self.d1; start.write_text(canonical(value))
        with self.assertRaises(ValueError):load_rows(self.root,self.base)
        start.write_bytes(old)
        rows,_=load_rows(self.root,self.base)
        self.assertTrue(next(r for r in rows if r['id']==next_ep['id'])['valid'])


if __name__=='__main__':unittest.main()
