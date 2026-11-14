import base64
import copy
import itertools
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from trl_core import ROOT, PINS, action, canonical, schema, render, sha, strict_load, world
from trl_io import Stop, read, save
from trl_contract import request, non_start, zero_limit
from trl_transport import Fake, Local, raw_record
from trl_replay import disposition, inspect
from trl_journal import Journal, prefix, verify_prefix
from trl_budget import ActiveTime
from trl_collect import episode, OperationalPause
from trl_analysis import replay, reused_rows


def schema_valid(value,s):
    """Independent evaluator of every keyword in this study's schema subset."""
    types=s.get('type',[]);types=[types] if isinstance(types,str) else types
    is_integer=type(value) is int or (type(value) is float and value.is_integer())
    matches={'object':type(value) is dict,'array':type(value) is list,'integer':is_integer,'null':value is None}
    if types and not any(matches[t] for t in types): return False
    if type(value) is dict:
        if not set(s.get('required',[]))<=set(value): return False
        if s.get('additionalProperties') is False and not set(value)<=set(s.get('properties',{})): return False
        if any(k in value and not schema_valid(value[k],sub) for k,sub in s.get('properties',{}).items()): return False
    if type(value) is list:
        if not s.get('minItems',0)<=len(value)<=s.get('maxItems',float('inf')): return False
        if any(not schema_valid(v,s.get('items',{})) for v in value): return False
    if type(value) in (int,float):
        if value<s.get('minimum',float('-inf')) or value>s.get('maximum',float('inf')): return False
    return True


def all_required(s):
    if type(s) is dict:
        if 'properties' in s:
            assert set(s.get('required',[]))==set(s['properties'])
            assert s.get('additionalProperties') is False
        for child in s.values(): all_required(child)
    elif type(s) is list:
        for child in s: all_required(child)


class SchemaProperties(unittest.TestCase):
    def test_required_in_every_object_branch(self):
        for q in (1,3): all_required(schema(q))
        with self.assertRaises(AssertionError):
            all_required({'anyOf':[schema(1),{'type':'object','properties':{'cells':{}},'required':[]}]})

    def test_exhaustive_schema_valid_instances_pass_shape_and_strict_action(self):
        # This schema's entire canonical JSON value space is finite: 49^1 + 49^3.
        checked=0
        for q in (1,3):
            s=schema(q)
            self.assertEqual(s,read(ROOT/'config/prompts.json')['schemas']['central' if q==3 else 'worker'])
            for cells in itertools.product([None,*range(48)],repeat=q):
                instance={'cells':list(cells)}
                self.assertTrue(schema_valid(instance,s))
                self.assertEqual(action(instance,q),instance)
                checked+=1
        self.assertEqual(checked,117698)

    def test_mathematical_integer_float_schema_validity_preserves_shape_only(self):
        for q in (1,3):
            for value in (0.0,1.0,47.0):
                instance={'cells':[value]*q}
                self.assertTrue(schema_valid(instance,schema(q)))
                # Exercise the actual validator's shape checks with value-type checks neutralized.
                action({**instance,'cells':[None for _ in instance['cells']]},q)
                with self.assertRaises(ValueError): action(instance,q)

    def test_invalid_shapes_rejected_by_schema_and_validator(self):
        for q in (1,3):
            for obj in ({},{'cells':[]},{'cells':[0]*(q+1)},{'cells':[0]*q,'extra':0},[],{'cells':None}):
                self.assertFalse(schema_valid(obj,schema(q)))
                with self.assertRaises(ValueError): action(obj,q)

    def test_only_request_change_is_format_object(self):
        for actor in PINS:
            for q in (1,3):
                p=render('central' if q==3 else 'shared',1,0 if q==3 else 1,[])
                new=request(actor,p,q,11)
                old={'model':PINS[actor][0],'prompt':p,'system':read(ROOT/'config/prompts.json')['system'],
                     'format':'json','stream':False,'options':dict(read(ROOT/'config/design.json')['local_options'],seed=11)}
                self.assertIs(type(new['format']),dict)
                self.assertEqual(new['format'],schema(q));new['format']='json'
                self.assertEqual(new,old)
        with self.assertRaises(Stop): request('claude','',1,0)

    def test_frozen_science_byte_identical(self):
        manifest=read(ROOT/'reuse/manifest.json')
        for name in ('trl_core.py','trl_validation.py','trl_budget.py','trl_io.py'):
            self.assertEqual(sha((ROOT/name).read_bytes()),manifest[name])
        self.assertEqual(sha((ROOT/'legacy_analysis.py').read_bytes()),manifest['trl_analysis.py'])
        for name in ('worlds.json','js-vectors.json','baselines.json','analysis-cases.json'):
            self.assertEqual(sha((ROOT/'fixtures'/name).read_bytes()),manifest['fixtures/'+name])
        self.assertEqual(read(ROOT/'config/episodes.json'),[e for e in read(ROOT/'config/v01-episodes.json') if e['actor']!='claude'])


class Episodes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)/'collection'
        self.timer=ActiveTime(self.base/'time-local.jsonl',43200);self.timer.begin('test')
        self.addCleanup(self.timer.end)
        self.journal=Journal(self.base/'dispatch.jsonl')
        self.ep={'actor':'qwen7b','seed':0,'regime':'shared','id':'qwen7b-s000-shared'}

    def run_episode(self,fault=None,ep=None):
        actor=Fake(fault)
        result=episode(ep or self.ep,actor,self.base,self.journal,self.timer,'TEST','test')
        return result,actor

    def test_complete_raw_replay_and_twelve_slots(self):
        t,actor=self.run_episode()
        self.assertTrue(t['complete']);self.assertEqual(len(actor.calls),12)
        row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertTrue(row['complete']);self.assertEqual(row['calls'],12)
        self.assertFalse(self.journal.open)

    def test_generated_malformed_is_episode_level_and_next_episode_runs(self):
        t,actor=self.run_episode('malformed')
        self.assertEqual(t['classification'],'MODEL_CAUSED');self.assertFalse(t['fatal'])
        self.assertEqual(len(actor.calls),1);self.assertEqual(len(t['events']),12)
        self.assertTrue(all(e['reward'] is None for e in t['events']))
        self.assertEqual(replay(self.ep,self.base/'episodes'/self.ep['id'])['Y'],0)
        e=dict(self.ep,seed=1,id='qwen7b-s001-shared')
        self.assertTrue(self.run_episode(ep=e)[0]['complete'])

    def test_length_is_model_failure(self):
        self.assertEqual(self.run_episode('length')[0]['classification'],'MODEL_CAUSED')

    def test_done_not_true_is_transport_failure_even_with_valid_payload(self):
        t,a=self.run_episode('incomplete')
        self.assertEqual(t['classification'],'TRANSPORT_FAILURE');self.assertFalse(t['fatal'])
        self.assertEqual(t['receipts'],[])

    def test_missing_usage_unknown_not_zero(self):
        self.run_episode('unknown-usage')
        row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertIsNone(row['input_tokens']);self.assertIsNone(row['output_tokens'])
        self.assertEqual(row['unknown_usage_calls'],1)

    def test_timeout_ends_episode_no_resend(self):
        t,a=self.run_episode('timeout');self.assertEqual(len(a.calls),1)
        self.assertEqual(t['classification'],'TRANSPORT_FAILURE')
        with self.assertRaises(Stop): self.run_episode()

    def test_wrong_identity_durable_stop(self):
        with self.assertRaises(Stop): self.run_episode('identity')
        self.assertTrue((self.base/'STOP.json').exists())

    def test_null_is_valid_all_scheduled_slots_score_zero(self):
        t,a=self.run_episode('null');row=replay(self.ep,self.base/'episodes'/self.ep['id'])
        self.assertTrue(t['complete']);self.assertEqual(len(a.calls),12)
        self.assertEqual((row['Y'],row['H'],row['null_rate']),(0,0,1))

    def test_invalid_central_never_executes_partial_array(self):
        ep=dict(self.ep,regime='central',id='qwen7b-s000-central')
        t,a=self.run_episode('malformed',ep)
        self.assertEqual(t['receipts'],[]);self.assertEqual(len(a.calls),1)
        self.assertEqual(sum(e['status']=='technical' for e in t['events']),3)

    def test_nonstarts_pause_no_terminal_then_exact_resume(self):
        for index,fault in enumerate(('dns','limit')):
            ep=dict(self.ep,seed=index,id=f'qwen7b-s{index:03}-shared')
            with self.assertRaises(OperationalPause): self.run_episode(fault,ep)
            d=self.base/'episodes'/ep['id']
            self.assertFalse((d/'episode.json').exists())
            row=replay(ep,d);self.assertEqual(row['status'],'UNKNOWN');self.assertNotIn('Y',row)
            t,a=self.run_episode(ep=ep)
            self.assertTrue(t['complete']);self.assertEqual(t['attempted_calls'],12)
            self.assertEqual(t['non_start_attempts'],1)
            p=d/'calls/r1-j1'
            self.assertEqual((p/'0001/request.json').read_bytes(),(p/'0002/request.json').read_bytes())
            row=replay(ep,d);self.assertEqual(row['calls'],12);self.assertEqual(row['operational_non_starts'],1)

    def test_nonstart_after_prior_generated_calls_preserves_round_buffer(self):
        class MidPause(Fake):
            def generate(self,actor,req,work):
                self.fault='dns' if len(self.calls)==1 else None
                return super().generate(actor,req,work)
        actor=MidPause()
        with self.assertRaises(OperationalPause): episode(self.ep,actor,self.base,self.journal,self.timer,'TEST','test')
        t,resumed=self.run_episode();self.assertEqual(len(resumed.calls),11)
        self.assertEqual(t['attempted_calls'],12);self.assertTrue(t['complete'])

    def test_prior_round_reward_retained_on_generated_failure(self):
        class LateFailure(Fake):
            def generate(self,actor,req,work):
                self.fault='malformed' if len(self.calls)==3 else None
                return super().generate(actor,req,work)
        t=episode(self.ep,LateFailure(),self.base,self.journal,self.timer,'TEST','test')
        self.assertEqual(len(t['receipts']),3);self.assertGreater(sum(e['operational_reward'] for e in t['events']),0)
        self.assertEqual(len([e for e in t['events'] if e['status']=='missing']),8)
        self.assertGreater(replay(self.ep,self.base/'episodes'/self.ep['id'])['Y'],0)

    def test_partial_start_is_not_retried(self):
        d=self.base/'episodes'/self.ep['id']/'calls/r1-j1/0001'
        save(d/'start.json',{'id':'uncertain'})
        with self.assertRaises(Stop): self.run_episode()

    def test_raw_or_terminal_tampering_rejected(self):
        self.run_episode();d=self.base/'episodes'/self.ep['id']
        terminal=read(d/'episode.json');terminal['events'][0]['reward']+=1
        (d/'episode.json').write_text(canonical(terminal))
        with self.assertRaises(Stop): replay(self.ep,d)

    def test_post_terminal_attempt_rejected(self):
        self.run_episode();d=self.base/'episodes'/self.ep['id']
        save(d/'calls/r4-j3/0002/start.json',{'id':'extra'})
        with self.assertRaises(Stop): replay(self.ep,d)


class NonStarts(unittest.TestCase):
    def test_typed_dns_before_dispatch(self):
        with patch('trl_transport.http',side_effect=urllib.error.URLError(socket.gaierror(socket.EAI_NONAME,'DNS'))):
            raw=Local().generate('qwen7b',{},None)
        self.assertEqual(non_start(raw),'DNS')

    def test_text_dns_timeout_or_connection_error_not_proven_nonstart(self):
        with patch('trl_transport.http',side_effect=urllib.error.URLError('DNS failed')):
            with self.assertRaises(urllib.error.URLError): Local().generate('qwen7b',{},None)
        self.assertIsNone(non_start(raw_record(transport_error='DNS')))

    def test_only_exact_zero_generation_limit_is_nonstart(self):
        e={'error':'usage_limit_reached','prompt_eval_count':0,'eval_count':0,'total_cost_usd':0}
        self.assertTrue(zero_limit(canonical(e).encode()))
        for k,v in (('eval_count',1),('eval_count',False),('prompt_eval_count',None),('total_cost_usd',1),('response','generated'),('tool_calls',[1])):
            self.assertFalse(zero_limit(canonical(dict(e,**{k:v})).encode()))
        self.assertFalse(zero_limit(b'bad json'))

    def test_local_cannot_dispatch_frontier(self):
        with patch('trl_transport.http',side_effect=AssertionError('no service access')):
            with self.assertRaises(Stop): Local().generate('claude',{},None)
            with self.assertRaises(Stop): Local().preflight('claude')


class LedgerProperties(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'dispatch.jsonl'

    def test_preserved_prefix_allows_append_verified_tail(self):
        j=Journal(self.p);j.event(event='start',id='a');frozen=prefix(self.p)
        j.event(event='finish',id='a');verify_prefix(self.p,frozen)
        self.assertFalse(Journal(self.p).open)

    def test_prefix_truncation_edit_and_torn_tail_rejected(self):
        j=Journal(self.p);j.event(event='start',id='a');frozen=prefix(self.p);raw=self.p.read_bytes()
        for bad in (b'',raw.replace(b'"a"',b'"b"'),raw+b'partial'):
            self.p.write_bytes(bad)
            with self.assertRaises(Stop): verify_prefix(self.p,frozen)
        self.p.write_bytes(raw)

    def test_hash_chain_and_duplicate_start_rejected(self):
        j=Journal(self.p);j.event(event='start',id='a')
        with self.assertRaises(Stop): j.event(event='start',id='a')
        self.p.write_text(self.p.read_text().replace('"a"','"b"'))
        with self.assertRaises(Stop): Journal(self.p)


class ReuseAndOffline(unittest.TestCase):
    def test_reused_claude_exact_population_and_historical_failures(self):
        rows=reused_rows(ROOT)
        self.assertEqual(len(rows),60)
        self.assertEqual(sum(r['complete'] for r in rows if r['episode']['regime']=='central'),17)
        for reg in ('private','shared'):
            self.assertEqual(sum(r['complete'] for r in rows if r['episode']['regime']==reg),20)
        self.assertTrue(all(r['source_version']=='v0.1-reused' for r in rows))

    def test_analysis_imports_no_transport_network_or_credentials(self):
        code="import sys; import trl_analysis; assert 'trl_transport' not in sys.modules; assert 'urllib.request' not in sys.modules; assert 'trl_collect' not in sys.modules"
        subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,check=True)

    def test_predictions_disclose_observed_v01(self):
        p=read(ROOT/'config/predictions.json')
        self.assertFalse(p['P6_prospective']);self.assertTrue(p['P7_already_failed'])
        self.assertEqual(p['stop_after'],'v0.2');self.assertEqual(set(p['evaluations']),{f'P{i}' for i in range(1,8)})


if __name__=='__main__': unittest.main()

class EvidenceKindAndIncomplete(unittest.TestCase):
    def test_done_false_without_running_record_is_transport_failure(self):
        ep={'actor':'qwen7b','regime':'shared'}
        e={'model':PINS['qwen7b'][0],'done':False,'response':'{"cells":[0]}'}
        self.assertEqual(disposition(raw_record(canonical(e).encode()),ep,1)['classification'],'TRANSPORT_FAILURE')

    def test_generated_refusal_is_episode_model_failure(self):
        raw=Fake().generate('qwen7b',request('qwen7b',render('shared',1,1,[]),1,11),None)
        e=strict_load(base64.b64decode(raw['stdout_b64']).decode());e['response']='I refuse.'
        raw['stdout_b64']=base64.b64encode(canonical(e).encode()).decode()
        self.assertEqual(disposition(raw,{'actor':'qwen7b','regime':'shared'},1)['classification'],'MODEL_CAUSED')
