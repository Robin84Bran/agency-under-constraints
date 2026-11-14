"""D3 failure-path regressions, fixtures only."""
from pathlib import Path
import tempfile
import unittest
from rg_analysis import load_rows, reconcile, score
from rg_collect import ActiveTime, Ledger, Stop, collect, decode, read, run_episode, save
from rg_core import ROOT, ModelOutputError, canonical, render, reserve, sha, strict_load
from rg_offline import Fake

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
        for actor, modes in [('claude',('wrong_model','wrong_effort','missing_usage','overrun')),
                             ('qwen7b',('identity','usage','context','running'))]:
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
        for changes in ({'num_turns':3},):
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


