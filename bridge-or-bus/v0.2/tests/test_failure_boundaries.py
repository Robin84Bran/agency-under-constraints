"""D3 regressions: fake transports, real saved envelope, no live requests/Git."""
import ast
import copy
import datetime as dt
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,PINS,act,canonical,sha,strict_load,schedule,subholds
from bob_collect import (Stop,Ledger,ActiveTime,read,save,run_episode,collect,
                         payload,LocalAdapter,usage)
from bob_validation import ModelFailure,EpisodeTransport,envelope,claude_contract
from bob_offline import FakeTransport,write
from bob_audit import audit_episode,reconcile_ledger
from bob_analysis import score


def ep(model='qwen7b',seed=0,arm='registry'):
    return dict(id=f'{model}-{seed:02d}-stable-{arm}',model=model,seed=seed,world='stable',arm=arm)


class FailureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-d3-failure-')
        self.root=Path(self.temp.name)
        self.ledger=Ledger(self.root/'collection/cost.jsonl')
        self.timer=ActiveTime(self.root/'collection/time.jsonl',7200)

    def tearDown(self):self.temp.cleanup()

    def run_case(self,model,change=None,raw_change=None,phase='action',seed=0):
        e=ep(model,seed);base=FakeTransport(e)
        class Fake:
            def generate(inner,*args):
                result=base.generate(*args)
                if phase is None or args[1]==phase:
                    env=strict_load(result['stdout'])
                    if change:change(env)
                    raw=canonical(env).encode()
                    result['stdout']=raw_change(raw) if raw_change else raw
                return result
        saved=run_episode(self.root,e,Fake(),self.ledger,self.timer,'FIXTURE')
        audit_episode(self.root,e,saved,'FIXTURE')
        self.assertFalse(self.ledger.blocked)
        self.assertEqual(reconcile_ledger(self.root,{e['id']:saved})['status'],'PASS')
        return e,saved,base

    def test_illegal_action_arguments_and_schema_end_only_episode_both_models(self):
        invalids=[{},dict(act('finish'),key='forbidden'),act('finish',grams=1),
                  act('lookup',item='BAD!'),act('convert',grams=True),act('submit',revision=2),
                  act('describe',target='bad'),act('lookup',item='item-000000',grams=1)]
        for model in ('qwen7b','claude'):
            for value in invalids:
                with self.subTest(model=model,value=value),FailureTests() as case:
                    key='structured_output' if model=='claude' else 'response'
                    e,saved,base=case.run_case(model,lambda env:env.update({key:value if model=='claude' else canonical(value)}))
                    self.assertEqual(base.calls,1);self.assertEqual(saved['events'],[])
                    self.assertFalse(saved['transport_failure'])
                    scored=score(e,saved,True)
                    self.assertEqual((scored['Sstar'],scored['Astar'],scored['J']),(0,0,0))

    def __enter__(self):self.setUp();return self
    def __exit__(self,*args):self.tearDown()

    def test_unavailable_describe_is_model_failure(self):
        env=dict(model=PINS['qwen7b'][0],done=True,done_reason='stop',prompt_eval_count=1,eval_count=1,
                 response=canonical(act('describe',target='lookup')))
        with self.assertRaises(ModelFailure):payload(env,ep(arm='stale'),'action')

    def test_invalid_report_retains_trajectory_and_stops_without_repair(self):
        for model in ('qwen7b','claude'):
            for value in [{},{'submitted':1},{'submitted':True,'key':None}]:
                with self.subTest(model=model,value=value),FailureTests() as case:
                    key='structured_output' if model=='claude' else 'response'
                    e,saved,base=case.run_case(model,lambda env:env.update({key:value if model=='claude' else canonical(value)}),phase='report')
                    self.assertTrue(saved['committed']);self.assertTrue(saved['trajectory_valid'])
                    self.assertIsNone(saved['report']);self.assertEqual(base.calls,6)
                    scored=score(e,saved,True)
                    self.assertEqual((scored['Sstar'],scored['Astar'],scored['J']),(1,0,0))

    def test_malformed_local_payload_json_is_model_failure(self):
        for value in ['{','```json\n{}\n```','{"submitted":true,"submitted":false}','{"x":NaN}']:
            with self.subTest(value=value),FailureTests() as case:
                _,saved,base=case.run_case('qwen7b',lambda env:env.update(response=value))
                self.assertEqual(base.calls,1);self.assertFalse(saved['transport_failure'])

    def test_nested_claude_payload_duplicates_and_nonfinite_keep_known_usage(self):
        for text in [b'{"submitted":true,"submitted":false}',b'{"submitted":NaN}']:
            with self.subTest(text=text),FailureTests() as case:
                def alter(raw):
                    env=strict_load(raw);env.pop('structured_output')
                    return canonical(env).encode()[:-1]+b',"structured_output":'+text+b'}'
                _,saved,base=case.run_case('claude',raw_change=alter)
                self.assertEqual(base.calls,1);self.assertEqual(saved['resources']['micro_usd'],0)
                self.assertFalse(saved['transport_failure'])

    def test_length_is_model_failure_both_transports_and_phases(self):
        for model in ('qwen7b','claude'):
            for phase in ('action','report'):
                with self.subTest(model=model,phase=phase),FailureTests() as case:
                    key='stop_reason' if model=='claude' else 'done_reason'
                    value='max_tokens' if model=='claude' else 'length'
                    _,saved,_=case.run_case(model,lambda env:env.update({key:value}),phase=phase)
                    self.assertFalse(saved['transport_failure']);self.assertIn('length',saved['error'])

    def test_claude_schema_rejection_is_model_failure_after_settlement(self):
        _,saved,base=self.run_case('claude',lambda env:env.update(subtype='error_max_structured_output_retries',is_error=True))
        self.assertEqual(base.calls,1);self.assertIn('rejected model',saved['error'])

    def test_known_schema_error_with_nonzero_cli_exit_is_episode_content(self):
        e=ep('claude');base=FakeTransport(e)
        class Rejected:
            def generate(inner,*args):
                result=base.generate(*args)
                env=strict_load(result['stdout']);env.update(subtype='error_max_structured_output_retries',is_error=True)
                result.update(stdout=canonical(env).encode(),returncode=1)
                return result
        saved=run_episode(self.root,e,Rejected(),self.ledger,self.timer,'FIXTURE')
        self.assertFalse(self.ledger.blocked);self.assertEqual(base.calls,1)
        audit_episode(self.root,e,saved,'FIXTURE')
        self.assertFalse(saved['transport_failure'])

    def test_incomplete_and_missing_ollama_counts_are_episode_transport(self):
        cases=[lambda e:e.update(done=False),lambda e:e.pop('done'),lambda e:e.pop('eval_count'),
               lambda e:e.update(eval_count=True),lambda e:e.pop('prompt_eval_count')]
        for change in cases:
            with self.subTest(change=change),FailureTests() as case:
                _,saved,base=case.run_case('qwen7b',change)
                self.assertEqual(base.calls,1);self.assertTrue(saved['transport_failure'])
                self.assertIsNone(saved['resources']['output_tokens'])

    def test_unreadable_local_envelope_is_transport(self):
        _,saved,_=self.run_case('qwen7b',raw_change=lambda _:b'{')
        self.assertTrue(saved['transport_failure'])

    def test_identity_context_unknown_stop_and_bound_violation_remain_fatal(self):
        cases=[('qwen7b',dict(model='wrong',done=False)),('qwen7b',dict(prompt_eval_count=8192)),
               ('qwen7b',dict(eval_count=193)),('qwen7b',dict(done_reason='UNKNOWN')),
               ('claude',dict(modelUsage={})),('claude',dict(effort='high')),
               ('claude',dict(num_turns=3)),('claude',dict(stop_reason='UNKNOWN'))]
        for model,fields in cases:
            with self.subTest(model=model,fields=fields),FailureTests() as case:
                with self.assertRaises(Stop):case.run_case(model,lambda env:env.update(fields))
                self.assertTrue(Ledger(case.ledger.path).blocked)

    def test_paid_unknown_usage_outer_json_and_overruns_still_hold_and_stop(self):
        cases=[(lambda e:e.pop('usage'),None),(lambda e:e.update(total_cost_usd=None),None),
               (lambda e:e['usage'].update(cache_read_input_tokens=999999),None),
               (None,lambda _:b'{')]
        for change,raw_change in cases:
            with self.subTest(change=change),FailureTests() as case:
                with self.assertRaises(Stop):case.run_case('claude',change,raw_change)
                self.assertTrue(Ledger(case.ledger.path).blocked)
                self.assertTrue(Ledger(case.ledger.path).holds[ep('claude')['id']])

    def test_unexpected_simulator_and_adapter_exceptions_are_fatal(self):
        for target in ('bob_collect.World.step','bob_offline.FakeTransport.generate'):
            with self.subTest(target=target),FailureTests() as case:
                base=FakeTransport(ep())
                with patch(target,side_effect=ValueError('harness bug')):
                    with self.assertRaises(Stop):
                        run_episode(case.root,ep(),base,case.ledger,case.timer,'FIXTURE')
                self.assertTrue(Ledger(case.ledger.path).blocked)

    def test_runtime_context_failure_cannot_be_downgraded_by_incomplete_output(self):
        def fake(path,*args,**kwargs):
            if path=='/api/generate':return canonical(dict(model=PINS['qwen7b'][0],done=False)).encode()
            return b'{"models":[]}'
        adapter=LocalAdapter(self.root,'qwen7b');adapter.ready=True
        with patch('bob_collect.http',side_effect=fake):
            with self.assertRaises(Stop):run_episode(self.root,ep(),adapter,self.ledger,self.timer,'FIXTURE')
        self.assertTrue(Ledger(self.ledger.path).blocked)


class RealEnvelopeTests(unittest.TestCase):
    def setUp(self):self.raw=(ROOT/'fixtures/real-claude-envelope.json').read_bytes()

    def test_exact_saved_envelope_metadata_usage_and_zero_subagents_pass(self):
        env,problem=envelope(self.raw)
        self.assertIsNone(problem);self.assertIsNone(claude_contract(env))
        self.assertEqual((env['num_turns'],env['stop_reason']),(2,'tool_use'))
        counts=usage(env,'claude')
        self.assertEqual(sum(counts[k] for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens')),1602)
        self.assertEqual(counts['output_tokens'],199);self.assertEqual(counts['micro_usd'],16788)
        # Sibling payload uses its own schema. Strict study validation must reject it.
        with self.assertRaises(ModelFailure):payload(env,ep('claude'),'action')
        self.assertEqual(env['structured_output'],{'op':'send','job':1,'key':None})

    def test_real_metadata_with_our_strict_payload_passes_both_live_and_audit(self):
        with FailureTests() as case:
            real=strict_load(self.raw)
            def metadata(env):
                value=env['structured_output'];env.clear();env.update(copy.deepcopy(real));env['structured_output']=value
            _,saved,base=case.run_case('claude',metadata,phase=None)
            self.assertEqual(base.calls,6);self.assertTrue(saved['committed'])

    def test_two_turns_requires_tool_use_and_integer_counts(self):
        for turns,stop in [(2,'end_turn'),(2,None),(True,'tool_use'),(3,'tool_use'),(1.0,'tool_use')]:
            env=strict_load(self.raw);env.update(num_turns=turns,stop_reason=stop)
            with self.assertRaises(Stop):claude_contract(env)
        env=strict_load(self.raw);env.update(num_turns=1,stop_reason='end_turn')
        self.assertIsNone(claude_contract(env))

    def test_positive_nested_subagent_and_server_activity_are_fatal(self):
        for mutate in [lambda e:e['subagent_stats']['requested'].update(background=1),
                       lambda e:e['usage']['server_tool_use'].update(web_fetch_requests=1),
                       lambda e:e['modelUsage']['claude-opus-5-5'].update(webSearchRequests=1)]:
            env=strict_load(self.raw);mutate(env)
            with self.assertRaises(Stop):claude_contract(env)

    def test_all_three_input_token_classes_are_reserved_once(self):
        with FailureTests() as case:
            def cached(env):env['usage'].update(input_tokens=2,cache_creation_input_tokens=1600,cache_read_input_tokens=7,output_tokens=199)
            _,saved,_=case.run_case('claude',cached,phase=None)
            self.assertEqual(sum(saved['resources'][k] for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens')),6*1609)
            self.assertEqual(saved['resources']['output_tokens'],6*199)


class CohortTests(unittest.TestCase):
    def cohort(self,root,plan,modes):
        write(root/'freeze.json',{'fixture':'not an active seal'})
        write(root/'config/order.json',plan)
        write(root/'config/runtime.json',{'claude_binary':'NOT_EXECUTED'})
        factories=[]
        def adapter(directory,model):
            class Fake:
                def generate(inner,req,phase,budget):
                    index=len(list((root/'collection/episodes').glob('*.json')))
                    e=plan[index];base=FakeTransport(e,mode=modes[index])
                    result=base.generate(req,phase,budget)
                    if modes[index]=='incomplete':
                        env=strict_load(result['stdout']);env['done']=False;result['stdout']=canonical(env).encode()
                    return result
            f=Fake();factories.append(f);return f
        with patch('bob_collect.ClaudeAdapter',side_effect=adapter),patch('bob_collect.LocalAdapter',side_effect=adapter), \
             patch('bob_freeze.verify',return_value={}),patch('bob_freeze.push_gate'),patch('bob_collect.frontier_gate'):
            return collect(root,(plan[0]['model'],))

    def test_model_failures_continue_to_next_episode_for_each_cohort(self):
        for model in ('qwen7b','claude'):
            with self.subTest(model=model),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);plan=[ep(model,s) for s in range(4)]
                modes=['truncated']*4 if model!='claude' else ['missing_payload']*4
                self.cohort(root,plan,modes)
                self.assertEqual(len(list((root/'collection/episodes').glob('*.json'))),4)
                self.assertFalse((root/'collection/transport-pause.json').exists())
                self.assertFalse(Ledger(root/'collection/cost.jsonl').blocked)

    def test_three_incomplete_local_episodes_pause_and_crash_restart_cannot_bypass(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=[ep(seed=s) for s in range(4)]
            with self.assertRaisesRegex(Stop,'three consecutive'):self.cohort(root,plan,['incomplete']*4)
            self.assertEqual(len(list((root/'collection/episodes').glob('*.json'))),3)
            pause=root/'collection/transport-pause.json';self.assertTrue(pause.exists())
            pause.unlink()  # Simulate crash before create-once pause, only in fixture.
            with self.assertRaisesRegex(Stop,'three consecutive'):self.cohort(root,plan,['incomplete']*4)
            self.assertTrue(pause.exists())
            self.assertEqual(len(list((root/'collection/episodes').glob('*.json'))),3)

    def test_orphan_call_start_and_missing_episode_start_are_fatal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=[ep()]
            write(root/'collection/starts/orphan.json',{'fixture':'uncertain'})
            with self.assertRaisesRegex(Stop,'orphan/uncertain'):
                self.cohort(root,plan,['truncated'])
            self.assertFalse((root/'collection/episodes').exists())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=[ep()]
            self.cohort(root,plan,['truncated'])
            (root/'collection/episode-starts'/f"{plan[0]['id']}.json").unlink()
            with self.assertRaisesRegex(Stop,'uncertain start'):
                self.cohort(root,plan,['truncated'])

    def test_content_failure_breaks_transport_streak(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);plan=[ep(seed=s) for s in range(5)]
            self.cohort(root,plan,['incomplete','incomplete','truncated','incomplete','incomplete'])
            self.assertEqual(len(list((root/'collection/episodes').glob('*.json'))),5)
            self.assertFalse((root/'collection/transport-pause.json').exists())


