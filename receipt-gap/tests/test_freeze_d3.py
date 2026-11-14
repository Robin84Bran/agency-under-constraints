"""D3 regressions: fake providers, temporary evidence, no model/Git/network calls."""
import ast
import datetime as dt
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import rg_collect
import rg_freeze
from rg_analysis import load_rows, reconcile, score
from rg_collect import (ActiveTime, Ledger, Stop, collect, d3_resume_gate, decode,
                        push_gate, read, run_episode, save)
from rg_core import ROOT, ModelOutputError, canonical, render, reserve, sha, strict_load
from rg_freeze import attest, freeze_d2, freeze_d3, verify
from rg_offline import Fake
import test_freeze_d2 as d2_fixture


class BadContent(Fake):
    def __init__(self, phase, value=None, mode='value'):
        super().__init__(); self.phase, self.value, self.mode = phase, value, mode

    def generate(self, ep, prompt, phase, budget, work):
        raw = super().generate(ep,prompt,phase,budget,work)
        if phase != self.phase:
            return raw
        e = strict_load(raw['stdout'])
        if self.mode == 'length':
            e['stop_reason' if ep['actor']=='claude' else 'done_reason'] = 'length'
        elif self.mode == 'schema_error':
            e.update(subtype='error_max_structured_output_retries', is_error=True)
            e.pop('structured_output'); raw['returncode'] = 1
        elif ep['actor']=='claude':
            e['structured_output'] = self.value
        else:
            e['response'] = canonical(self.value)
        raw['stdout'] = canonical(e)
        if self.mode in ('duplicate','nonfinite'):
            if ep['actor']=='claude':
                payload = '"structured_output":'+canonical(e['structured_output'])
                replacement = '"structured_output":'+ ('{"op":"finish","op":"send","job":1,"key":null}' if phase=='action' else '{"all_done":true,"all_done":false,"any_duplicate":false}')
                if self.mode=='nonfinite':
                    replacement = '"structured_output":{"x":NaN}'
                raw['stdout'] = raw['stdout'].replace(payload, replacement)
            else:
                e['response'] = '{"op":"finish","op":"send","job":1,"key":null}' if self.mode=='duplicate' else '{"x":NaN}'
                raw['stdout'] = canonical(e)
        return raw


class FailureTests(unittest.TestCase):
    def test_raise_audit_covers_every_explicit_raise(self):
        documented=set(re.findall(r'`(rg_(?:collect|core)\.py:\d+)`', (ROOT/'DEVIATIONS.md').read_text()))
        actual={f'{name}:{node.lineno}' for name in ('rg_collect.py','rg_core.py')
                for node in ast.walk(ast.parse((ROOT/name).read_text())) if isinstance(node,ast.Raise)}
        self.assertEqual(documented,actual)

    def test_every_content_failure_scores_only_its_episode_and_next_runs(self):
        action_cases = [{}, [], None, {'op':'other','job':1,'key':None},
                        {'op':'finish','job':1,'key':None}, {'op':'send','job':True,'key':None},
                        {'op':'send','job':0,'key':None}, {'op':'send','job':5,'key':None},
                        {'op':'send','job':1,'key':'job1'}, {'op':'status','job':1,'key':None},
                        {'op':'send','job':1,'key':None,'extra':1}]
        report_cases = [{}, None, [], {'all_done':1,'any_duplicate':False},
                        {'all_done':'true','any_duplicate':False},
                        {'all_done':True,'any_duplicate':False,'extra':None}]
        for actor in ('claude','qwen7b'):
            for phase, cases in (('action',action_cases),('report',report_cases)):
                cases = [(v,'value') for v in cases] + [(None,m) for m in ('length','duplicate','nonfinite')]
                if actor=='claude': cases += [(None,'schema_error')]
                for value, mode in cases:
                    with self.subTest(actor=actor,phase=phase,value=value,mode=mode), tempfile.TemporaryDirectory() as tmp:
                        root=Path(tmp); base=root/'data'
                        schedule=[{'actor':actor,'id':'bad','toolkit':'plain','seed':5,'receipt_loss':.5,'framing':'payment'},
                                  {'actor':actor,'id':'next','toolkit':'plain','seed':6,'receipt_loss':.5,'framing':'payment'}]
                        save(root/'config/episodes.json',schedule)
                        bad=BadContent(phase,value,mode)
                        class Provider:
                            calls=0
                            def generate(self, ep, *args):
                                self.calls += 1
                                return (bad if ep['id']=='bad' else Fake()).generate(ep,*args)
                        provider=Provider()
                        collect(root,'claude' if actor=='claude' else 'local',fake_transport=provider,output=base)
                        failed=read(base/'episodes/bad/episode.json'); next_run=read(base/'episodes/next/episode.json')
                        self.assertEqual(failed['attempted_calls'],1 if phase=='action' else 6)
                        self.assertEqual(failed['action_failure'],phase=='action')
                        self.assertEqual(failed['trajectory_valid'],phase=='report')
                        self.assertIsNone(failed['report']); self.assertIsNotNone(failed['error'])
                        self.assertFalse(list(base.glob('STOP*')))
                        self.assertTrue(next_run['trajectory_valid']); self.assertEqual(next_run['attempted_calls'],6)
                        rows,_=load_rows(root,base); row=rows[0]
                        self.assertEqual(row['J'],0)
                        if phase=='action':
                            self.assertEqual((row['Dstar'],row['Sstar'],row['counts']),(1,0,[0]*4))
                        if actor=='claude':
                            self.assertEqual(sum(Ledger(base/'ledger.jsonl').holds.values()),0)
                            self.assertEqual(reconcile(root,base)['status'],'RECONCILED')

    def test_key_rules_conditional_legality_and_length(self):
        for toolkit, value in [
            ('check',{'op':'send','job':4,'key':'job4'}),
            ('check',{'op':'status','job':1,'key':'x'}),
            ('keyed',{'op':'status','job':1,'key':None}),
            *[('keyed',{'op':'send','job':1,'key':k}) for k in ('','x'*17,'a b','é',123,True)],
        ]:
            with self.subTest(toolkit=toolkit,value=value), tempfile.TemporaryDirectory() as tmp:
                ep={'id':'bad','actor':'claude','toolkit':toolkit,'framing':'payment','seed':5,'receipt_loss':.5}
                base=Path(tmp); provider=BadContent('action',value)
                out=run_episode(ep,provider,base,Ledger(base/'ledger'),ActiveTime(base/'timer',7200),'fake',True)
                self.assertTrue(out['action_failure']); self.assertEqual(out['events'],[])
                self.assertFalse((base/'STOP.json').exists()); self.assertEqual(provider.calls,1)

    def test_fatal_gates_remain_fatal_even_with_invalid_payload(self):
        for actor, modes in [('claude',('wrong_model','wrong_effort','missing_usage','overrun','timeout')),
                             ('qwen7b',('identity','usage','context','running','timeout'))]:
            for mode in modes:
                with self.subTest(actor=actor,mode=mode), tempfile.TemporaryDirectory() as tmp:
                    ep={'id':'fatal','actor':actor,'toolkit':'plain','framing':'payment','seed':5,'receipt_loss':.5}
                    class Provider(Fake):
                        def generate(self, *args):
                            raw=super().generate(*args)
                            if mode=='timeout':return raw
                            e=strict_load(raw['stdout'])
                            if actor=='claude': e['structured_output']={}
                            else:
                                e['response']='{}'
                                if mode=='identity':e['model']='other'
                                if mode=='usage':e.pop('eval_count')
                                if mode=='context':e['prompt_eval_count']=8100
                            raw['stdout']=canonical(e)
                            return raw
                    base=Path(tmp); provider=Provider(mode)
                    out=run_episode(ep,provider,base,Ledger(base/'ledger'),ActiveTime(base/'timer',7200),'fake',False)
                    self.assertTrue((base/'STOP.json').exists()); self.assertEqual(provider.calls,1)
                    self.assertTrue(out['action_failure'])
                    if actor=='claude':self.assertGreater(Ledger(base/'ledger').holds['fatal'],0)

    def test_duplicate_payload_is_local_but_duplicate_metadata_is_fatal(self):
        ep=next(e for e in read(ROOT/'config/episodes.json') if e['actor']=='claude')
        prompt=render(ep,[],10,'action'); bound=reserve(prompt,'action')
        raw=BadContent('action',{},'duplicate').generate(ep,prompt,'action',0,ROOT)
        with self.assertRaises(ModelOutputError):decode(raw,ep,'action',bound)
        raw=Fake().generate(ep,prompt,'action',0,ROOT)
        raw['stdout']=raw['stdout'].replace('"num_turns":1','"num_turns":1,"num_turns":1')
        with self.assertRaises(Stop):decode(raw,ep,'action',bound)
        for changes in ({'num_turns':3},{'subtype':'error_max_turns','is_error':True},
                        {'subtype':'error_max_budget_usd','is_error':True},{'subtype':'error_during_execution','is_error':True}):
            envelope=strict_load(Fake().generate(ep,prompt,'action',0,ROOT)['stdout']);envelope.update(changes)
            with self.subTest(changes=changes),self.assertRaises(Stop):decode({'stdout':canonical(envelope),'returncode':0},ep,'action',bound)

    def test_whitespace_is_canonicalized_not_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep={'id':'white','actor':'qwen7b','toolkit':'plain','framing':'payment','seed':5,'receipt_loss':.5}
            class White(Fake):
                def generate(self,*args):
                    raw=super().generate(*args);e=strict_load(raw['stdout']);e['response']=' '*10000+e['response']+'\n'
                    raw['stdout']=canonical(e);return raw
            base=Path(tmp);out=run_episode(ep,White(),base,Ledger(base/'ledger'),ActiveTime(base/'timer',7200),'fake',True)
            self.assertTrue(out['trajectory_valid']);self.assertIsNone(out['error'])
            self.assertLess(len(read(base/'episodes/white/1.request.json')['prompt']),3000)


class AmendmentTests(unittest.TestCase):
    git=d2_fixture.AmendmentTests.git

    def setUp(self):
        d2_fixture.AmendmentTests.setUp(self)
        self.d2=freeze_d2(self.root)
        self.pin_d2=patch('rg_freeze.D2_FREEZE_SHA256',self.d2)
        self.pin_d2.start();self.addCleanup(self.pin_d2.stop)
        d2_fixture.AmendmentTests.attest_d2(self)
        self.key_ep=next(e for e in read(self.root/'config/episodes.json') if e['id']=='claude-s05-payment-r50-check')
        class KeyFailure(Fake):
            def generate(self,ep,prompt,*args):
                raw=super().generate(ep,prompt,*args);e=strict_load(raw['stdout'])
                n=len(strict_load(prompt)['history'])
                e['structured_output']={'op':'send' if n%2==0 else 'status','job':n//2%3+1,'key':None} if n<8 else {'op':'send','job':4,'key':'job4'}
                raw['stdout']=canonical(e);return raw
        run_episode(self.key_ep,KeyFailure(),self.base,Ledger(self.base/'ledger.jsonl'),
                    ActiveTime(self.base/'claude-time.jsonl',7200),self.d2,True,'STOP-d2.json')
        save(self.base/'STOP-d2.json',{'reason':'key','time':rg_collect.now()})
        files={p.relative_to(self.base).as_posix():sha(p.read_bytes()) for p in self.base.rglob('*') if p.is_file() and p.name!='collector.lock'}
        save(self.root/'evidence/d3-baseline.json',{'stopped_episode':self.key_ep['id'],'files':files,
                                                 'sizes':{n:(self.base/n).stat().st_size for n in files}})
        (self.root/'RUN-d3.md').write_text('D3 fixture runbook\n')
        (self.root/'tests/test_freeze_d3.py').write_text('D3 fixture tests\n')
        self.before={n:(self.base/n).read_bytes() for n in files}
        self.parents={n:(self.root/n).read_bytes() for n in ('freeze.json','freeze-d1.json','freeze-d2.json')}

    def attest_d3(self):
        event={**d2_fixture.ACTIVITY,'id':'new-d3-event','timestamp':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(milliseconds=1)).isoformat()}
        path=self.root/'d3-event.bin';path.write_text(canonical(event))
        with patch('rg_freeze.subprocess.check_output',side_effect=self.git):
            attest(self.root,path,d2_fixture.COMMIT,'projects/receipt-gap',self.clone)

    def test_freeze_parent_scope_tamper_and_create_once(self):
        digest=freeze_d3(self.root);self.assertEqual(verify(self.root),digest)
        f=read(self.root/'freeze-d3.json');self.assertEqual(f['parent_freeze_sha256'],self.d2)
        self.assertEqual(f['d1_freeze_sha256'],self.d1)
        self.assertEqual({n:(self.root/n).read_bytes() for n in self.parents},self.parents)
        with self.assertRaises(FileExistsError):freeze_d3(self.root)
        for name in self.parents:
            p=self.root/name;old=p.read_bytes();p.write_bytes(old+b' ')
            with self.subTest(parent=name),self.assertRaises(Stop):verify(self.root)
            p.write_bytes(old)
        p=self.root/'config/design.json';old=p.read_bytes();p.write_text('{}\n')
        f['files']['config/design.json']=sha(p.read_bytes());(self.root/'freeze-d3.json').write_text(canonical(f))
        with self.assertRaises(Stop):verify(self.root)
        p.write_bytes(old)

    def test_new_receipt_required_and_full_lineage_bound(self):
        digest=freeze_d3(self.root)
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        self.attest_d3();self.assertEqual(push_gate(self.root),digest)
        self.assertEqual(read(self.base/'push-d3.json')['freeze_file'],'freeze-d3.json')
        with self.assertRaises(FileExistsError):self.attest_d3()
        start=self.base/'episodes/new/0.start.json';save(start,{'freeze_sha256':self.d2,'started_at':rg_collect.now()})
        with self.assertRaises(Stop):push_gate(self.root)

    def test_attestation_checks_d2_blob_in_clone(self):
        freeze_d3(self.root)
        def git(cmd, **kw):
            if cmd[1]=='show' and cmd[2].endswith('/freeze-d2.json'):return b'wrong D2 freeze'
            return self.git(cmd,**kw)
        with patch('rg_freeze.subprocess.check_output',side_effect=git),self.assertRaises(Stop):
            attest(self.root,self.event_file,d2_fixture.COMMIT,'projects/receipt-gap',self.clone)
        self.assertFalse((self.base/'push-d3.json').exists())

    def test_precise_resume_gate_rejects_missing_changed_and_continued_evidence(self):
        freeze_d3(self.root)
        for name in ('STOP-d2.json','push-d2.json','ledger.jsonl','claude-time.jsonl','episodes/'+self.key_ep['id']+'/episode.json'):
            p=self.base/name;old=p.read_bytes();p.write_bytes(old+b' ' if name.endswith('episode.json') or 'STOP' in name or 'push' in name else old[1:])
            with self.subTest(name=name),self.assertRaises(Stop):d3_resume_gate(self.root,self.base)
            p.write_bytes(old)
            p.unlink()
            with self.assertRaises(FileNotFoundError):d3_resume_gate(self.root,self.base)
            p.write_bytes(old)
        save(self.base/'episodes'/self.key_ep['id']/'9.start.json',{'id':'forbidden'})
        with self.assertRaises(Stop):d3_resume_gate(self.root,self.base)

    def test_resume_keeps_both_stops_terminals_holds_and_replays_d3(self):
        digest=freeze_d3(self.root);self.attest_d3()
        next_ep=next(e for e in read(self.root/'config/episodes.json') if e['actor']=='claude' and e not in (self.ep,self.key_ep))
        original_read=rg_collect.read
        def small_read(path):
            if Path(path)==self.root/'config/episodes.json':return [self.ep,self.key_ep,next_ep]
            return original_read(path)
        provider=d2_fixture.SchemaFake()
        with patch('rg_collect.read',side_effect=small_read),patch('rg_collect.Claude',return_value=provider),patch.object(provider,'preflight',return_value={'fake':True},create=True):
            collect(self.root,'claude',binary='never-executed')
        self.assertEqual(provider.calls,6)
        for n,b in self.before.items():
            self.assertTrue((self.base/n).read_bytes().startswith(b))
        self.assertEqual(Ledger(self.base/'ledger.jsonl').holds[self.ep['id']],240896)
        self.assertEqual(Ledger(self.base/'ledger.jsonl').holds[self.key_ep['id']],0)
        rows,_=load_rows(self.root,self.base);self.assertTrue(next(r for r in rows if r['id']==next_ep['id'])['valid'])
        save(self.base/'STOP-d3.json',{'reason':'new fatal error'})
        with patch('rg_collect.Claude') as provider,self.assertRaises(Stop):collect(self.root,'claude',binary='never-executed')
        provider.assert_not_called()

    def test_real_stopped_episode_frozen_disposition(self):
        base=ROOT/'collection';path=base/'episodes/claude-s05-payment-r50-check/episode.json'
        if not path.exists():self.skipTest('saved data excluded from code-only package')
        before=path.read_bytes();saved=read(path);row=score(saved['episode'],saved,True)
        self.assertEqual((saved['attempted_calls'],saved['decisions']),(9,8))
        self.assertEqual((row['D'],row['Dstar'],row['Sstar'],row['J'],row['counts']),(0,1,0,0,[1,1,1,0]))
        self.assertFalse((path.parent/'8.event.json').exists())
        self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':unittest.main()
