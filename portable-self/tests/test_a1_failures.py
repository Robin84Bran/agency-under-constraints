"""A1 regressions: provider fakes only; no credentials, sockets or model calls."""
import ast
import base64
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, World, PINS, canonical, sha, render, reservation, strict_load
from ps_io import Stop, EpisodeFailure, TransportFailure, Ledger, ActiveTime, read
from ps_collect import collect, run_episode
from ps_offline import Fake
from ps_transport import decode, MODEL, usage, identity, Local
from ps_analysis import score, audit_accounting


def episode(seed=0,actor='qwen7b'):
    return {'actor':actor,'seed':seed,'world':'different-stable','arm':'keyed',
            'id':f'{actor}-{seed:02d}-different-stable-keyed'}


class A1Failures(unittest.TestCase):
    def run_pair(self,actor,index,value=None,envelope=None,raw_change=None):
        a,b=episode(actor=actor),episode(1,actor)
        def mutate(raw,ep,i):
            if ep['seed']==0 and i==index:
                e=strict_load(raw['stdout'])
                if envelope is not None: e.update(envelope)
                else: e['structured_output' if actor=='claude' else 'response']=value if actor=='claude' else canonical(value)
                raw['stdout']=canonical(e)
                if raw_change: raw=raw_change(raw)
            return raw
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'fake';f=Fake(mutate=mutate)
            collect(ROOT,'claude' if actor=='claude' else 'local',fake_transport=f,output=base,episodes=[a,b])
            sa,sb=score(a,base,True),score(b,base,True)
            self.assertEqual(sa['calls_started'],index+1);self.assertEqual(sa['valid_calls'],index)
            self.assertEqual(sa['technical_missing'],16-max(0,index-4)*4)
            self.assertEqual(sa['Y'],max(0,index-4)/4)
            self.assertFalse(sa['technical_complete']);self.assertTrue(sb['technical_complete'])
            self.assertFalse((base/'STOP.json').exists());self.assertEqual(f.calls,index+9)
            self.assertFalse((base/'episodes'/a['id']/f'{index}.event.json').exists())
            self.assertEqual(audit_accounting(base,[sa,sb])['held_micro_usd'],0)
            return sa

    def test_every_write_validator_failure_first_paid_and_local(self):
        values=[None,[],1,{}, {'slot':True,'note':''},{'slot':0,'note':''},
                {'slot':5,'note':''},{'slot':1,'note':None},{'slot':1,'note':'x'*97},
                {'slot':1,'note':'\u4e2d'},{'slot':1,'note':'\n'},
                {'slot':1,'note':'','key':'not-allowed'}, {'slot':1,'note':'','report':False}]
        for actor in ('qwen7b','claude'):
            for value in values:
                with self.subTest(actor=actor,value=value): self.run_pair(actor,0,value)
            wrong_slot=1+World(episode(actor=actor)).payload()['writable_slot']%4
            with self.subTest(actor=actor,inaccessible=True): self.run_pair(actor,0,{'slot':wrong_slot,'note':''})

    def test_every_act_validator_failure_preserves_previous_returns(self):
        values=[None,[],{}, {'controls':None},{'controls':[1,2,3]},
                {'controls':[1,2,3,4,1]},{'controls':[True,1,1,1]},
                {'controls':[0,1,1,1]},{'controls':[5,1,1,1]},
                {'controls':['1',1,1,1]},{'controls':[1.,1,1,1]},
                {'controls':[1,1,1,1],'key':'illegal'}]
        for actor in ('qwen7b','claude'):
            for value in values:
                with self.subTest(actor=actor,value=value): self.run_pair(actor,5,value)

    def test_missing_or_wrong_structured_output_first_paid_continues(self):
        for val in (None,[],1,'{"slot":1,"note":""}'):
            with self.subTest(value=val): self.run_pair('claude',0,envelope={'structured_output':val})
        def remove(raw):
            e=strict_load(raw['stdout']);del e['structured_output'];raw['stdout']=canonical(e);return raw
        self.run_pair('claude',0,envelope={},raw_change=remove)

    def test_malformed_local_inner_json_is_content_failure(self):
        for val in ('{','{}{}','{"slot":1,"slot":2,"note":""}',
                    '{"slot":1,"note":NaN}','{"slot":1,"note":1e999}'):
            with self.subTest(value=val): self.run_pair('qwen7b',0,envelope={'response':val})

    def test_duplicate_nonfinite_structured_payload_settles_known_usage(self):
        for content in ('{"slot":1,"note":"","note":"x"}',
                        '{"slot":1,"note":NaN}', '{"slot":1,"note":1e999}'):
            def change(raw):
                e=strict_load(raw['stdout']);del e['structured_output']
                raw['stdout']=canonical(e)[:-1]+',"structured_output":'+content+'}'
                return raw
            with self.subTest(content=content):
                self.run_pair('claude',0,envelope={},raw_change=change)

    def test_length_stops_both_phases_and_all_claude_turn_counts(self):
        for actor in ('qwen7b','claude'):
            for index in (0,5):
                for turns in ((1,2) if actor=='claude' else (None,)):
                    for reason in (('length','max_tokens') if actor=='claude' else ('length',)):
                        fields={'stop_reason':reason,'num_turns':turns} if actor=='claude' else {'done_reason':reason}
                        with self.subTest(actor=actor,index=index,turns=turns,reason=reason): self.run_pair(actor,index,envelope=fields)

    def test_schema_tool_exhaustion_is_content_failure(self):
        for code in (0,1):
            with self.subTest(code=code):
                self.run_pair('claude',0,envelope={'subtype':'error_max_structured_output_retries','is_error':True,'structured_output':None,'stop_reason':None},raw_change=lambda raw:{**raw,'returncode':code})

    def test_cache_accounting_disjoint_categories(self):
        self.assertEqual(usage({'usage':{'input_tokens':2,'cache_creation_input_tokens':1600,'cache_read_input_tokens':7,'output_tokens':199,'thinking_tokens':105}},'claude'),(1609,199))
        for key in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens','output_tokens'):
            u={'input_tokens':2,'cache_creation_input_tokens':1600,'cache_read_input_tokens':7,'output_tokens':199};del u[key]
            tin,tout=usage({'usage':u},'claude')
            self.assertIsNone(tout if key=='output_tokens' else tin)

    def test_fatal_precedence_over_model_content(self):
        fields=[{'modelUsage':{'wrong':{}}},{'effort':'high'},{'usage':{}},
                {'permission_denials':[{}]},{'num_turns':3},{'stop_reason':'unexpected'},
                {'usage':{'input_tokens':1000000,'cache_creation_input_tokens':0,'cache_read_input_tokens':0,'output_tokens':1}},
                {'total_cost_usd':.9}]
        for extra in fields:
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as tmp:
                a,b=episode(actor='claude'),episode(1,'claude');base=Path(tmp)/'fake'
                def mutate(raw,ep,i):
                    e=strict_load(raw['stdout']);e.update(extra);e['structured_output']=None;raw['stdout']=canonical(e);return raw
                f=Fake(mutate=mutate)
                with self.assertRaises(Stop): collect(ROOT,'claude',fake_transport=f,output=base,episodes=[a,b])
                self.assertEqual(f.calls,1);self.assertTrue(Ledger(base/'ledger.jsonl').blocked)

    def test_duplicate_metadata_and_bad_outer_json_are_paid_fatal(self):
        for suffix in (',"num_turns":2}',',"usage":{}}',',"extra":NaN}'):
            with self.subTest(suffix=suffix),tempfile.TemporaryDirectory() as tmp:
                def mutate(raw,ep,i): raw['stdout']=raw['stdout'][:-1]+suffix;return raw
                with self.assertRaises(Stop): collect(ROOT,'claude',fake_transport=Fake(mutate=mutate),output=Path(tmp)/'fake',episodes=[episode(actor='claude')])

    def test_unknown_phase_is_harness_fatal(self):
        # The phase comes from the frozen world, never from generated content.
        ep=episode();payload=World(ep).payload();payload['mode']='unknown'
        f=Fake();req=f.request(ep,render(World(ep).payload()),'write',reservation('keyed','write'),0);raw=f.generate(req,Path('.'))
        with self.assertRaises(Stop): decode(raw,ep,payload,reservation('keyed','write'),True)

    def test_all_pinned_models_real_system_template(self):
        expected=identity(ROOT)
        for actor in PINS:
            def metadata(path,body=None,timeout=10):
                return canonical({'models':[{'name':PINS[actor][0],'digest':PINS[actor][1]}]}) if path=='/api/tags' else canonical({'template':expected[actor]['template'],'system':expected[actor]['system']}) if path=='/api/show' else '{}'
            with self.subTest(actor=actor),patch('ps_transport.http',side_effect=metadata): Local(ROOT).preflight(actor)
            def wrong(path,body=None,timeout=10):
                e=strict_load(metadata(path,body));
                if path=='/api/show': e['template']+='x'
                return canonical(e)
            with self.subTest(actor=actor,changed=True),patch('ps_transport.http',side_effect=wrong),self.assertRaises(Stop): Local(ROOT).preflight(actor)


class A1TransportPause(unittest.TestCase):
    def fault(self,kind):
        def mutate(raw,ep,i):
            e=strict_load(raw['stdout'])
            if kind=='done': e['done']=False
            elif kind=='eval': e.pop('eval_count')
            elif kind=='input': e.pop('prompt_eval_count')
            elif kind=='outer': raw['stdout']='{';return raw
            elif kind=='timeout': return {**raw,'transport_error':'timeout','returncode':None}
            raw['stdout']=canonical(e);return raw
        return mutate

    def test_three_transports_pause_no_fourth_and_no_resume_bypass(self):
        for kind in ('done','eval','input','outer','timeout'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)/'fake';eps=[episode(i) for i in range(4)];f=Fake(mutate=self.fault(kind))
                with self.assertRaises(Stop): collect(ROOT,'local',fake_transport=f,output=base,episodes=eps)
                self.assertEqual(f.calls,3);self.assertTrue(Ledger(base/'ledger.jsonl').blocked)
                for ep in eps[:3]:
                    self.assertTrue(read(base/'episodes'/ep['id']/'episode.json')['transport_failure'])
                    self.assertEqual(score(ep,base,True)['technical_missing'],16)
                self.assertFalse((base/'episodes'/eps[3]['id']).exists())
                with self.assertRaises(Stop): collect(ROOT,'local',fake_transport=f,output=base,episodes=eps)
                self.assertEqual(f.calls,3)

    def test_streak_survives_invocations_skips_and_crash_before_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'fake';eps=[episode(i) for i in range(4)]
            f=Fake(mutate=self.fault('done'))
            collect(ROOT,'local',fake_transport=f,output=base,episodes=eps[:2])
            self.assertEqual(f.calls,2)
            # Simulate third terminal sealed before collector gets to save STOP.
            run_episode(eps[2],f,base,Ledger(base/'ledger.jsonl'),ActiveTime(base/'local-time.jsonl',86400),'OFFLINE-FAKE',True)
            with self.assertRaises(Stop): collect(ROOT,'local',fake_transport=f,output=base,episodes=eps)
            self.assertEqual(f.calls,3);self.assertTrue((base/'STOP.json').exists())

    def test_content_and_complete_episodes_break_streak(self):
        for breaker in ('content','length','complete'):
            with self.subTest(breaker=breaker),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)/'fake';eps=[episode(i) for i in range(5)]
                def mutate(raw,ep,i):
                    if ep['seed']!=2: return self.fault('done')(raw,ep,i)
                    e=strict_load(raw['stdout'])
                    if breaker=='content': e['response']='{'
                    elif breaker=='length': e['done_reason']='length'
                    raw['stdout']=canonical(e);return raw
                collect(ROOT,'local',fake_transport=Fake(mutate=mutate),output=base,episodes=eps)
                self.assertFalse((base/'STOP.json').exists())

    def test_prefix_growth_allowed_rewrite_truncation_and_bad_tail_rejected(self):
        from ps_io import Journal
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.jsonl';j=Journal(path);j.append({'event':'example'});prefix=j.raw
            j.append({'event':'example-2'});self.assertEqual(path.read_bytes()[:len(prefix)],prefix)
            Journal(path)
            original=path.read_bytes()
            for bad in (b'',original.replace(b'example',b'changed',1),original+b'{}\n',original[:-1]):
                path.write_bytes(bad)
                with self.assertRaises(Stop): Journal(path)
                path.write_bytes(original)
