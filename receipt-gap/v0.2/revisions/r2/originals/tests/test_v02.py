"""Constrained toolkit contracts, real envelopes, provenance and cumulative spend."""
import ast
import copy
import itertools
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import rg_collect as c
import rg_freeze as f
from rg_core import (ROOT, ACTION_SCHEMAS, ModelOutputError, P, PINS, action,
                     canonical, render, reserve, schema_for, sha, strict_load)
from rg_analysis import checked_value, load_rows, reconcile
from rg_offline import Fake, dry_run
from test_receipt_gap import ep, a


def accepts(schema, value):
    """Test-only evaluator for the small frozen schema vocabulary."""
    if 'oneOf' in schema and sum(accepts(s,value) for s in schema['oneOf'])!=1:return False
    if 'anyOf' in schema and not any(accepts(s,value) for s in schema['anyOf']):return False
    t=schema.get('type')
    if isinstance(t,list):
        return any(accepts({**schema,'type':k},value) for k in t)
    if t=='object' and type(value) is not dict:return False
    if t=='integer' and type(value) is not int:return False
    if t=='string' and type(value) is not str:return False
    if t=='null' and value is not None:return False
    if t=='boolean' and type(value) is not bool:return False
    if 'const' in schema and value!=schema['const']:return False
    if type(value) is int and (value<schema.get('minimum',value) or value>schema.get('maximum',value)):return False
    if type(value) is str:
        if not schema.get('minLength',0)<=len(value)<=schema.get('maxLength',len(value)):return False
        if 'pattern' in schema and re.fullmatch(schema['pattern'],value,re.ASCII) is None:return False
    if type(value) is dict:
        props=schema.get('properties',{})
        if not set(schema.get('required',[]))<=set(value):return False
        if schema.get('additionalProperties') is False and not set(value)<=set(props):return False
        if not all(accepts(props[k],v) for k,v in value.items() if k in props):return False
    return True


class SchemaTests(unittest.TestCase):
    def test_exact_schema_matches_toolkit_legality(self):
        for toolkit in ACTION_SCHEMAS:
            for op,job,key in itertools.product(('send','status','finish','other'),(None,0,1,4,5,True),
                                                (None,'x','X_-9','x'*16,'x'*17,'','a b','é','a\n',5)):
                value={'op':op,'job':job,'key':key}
                try:action(value,toolkit); valid=True
                except ModelOutputError:valid=False
                self.assertEqual(accepts(schema_for('action',toolkit),value),valid,(toolkit,value))
            for value in ({},[],None,{**a(),'extra':None},{'op':'finish','job':None}):
                self.assertFalse(accepts(schema_for('action',toolkit),value))

    def test_selected_schema_reaches_both_real_transport_requests(self):
        for toolkit in ACTION_SCHEMAS:
            e=ep(toolkit=toolkit)
            def http(path,body=None,timeout=10):
                if path=='/api/generate':
                    self.assertEqual(body['format'],schema_for('action',toolkit))
                    self.assertEqual(body['options'],{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192,'seed':0})
                    return '{}'
                return '{"models":[]}'
            with patch('rg_collect.http',side_effect=http):c.Local().generate(e,'test','action',0,ROOT)
            cmd=c.claude_command('claude','action',100000,toolkit)
            self.assertEqual(strict_load(cmd[cmd.index('--json-schema')+1]),schema_for('action',toolkit))
            self.assertEqual(cmd[cmd.index('--max-turns')+1],'1')

    def test_report_transport_and_prompts_remain_unchanged(self):
        for toolkit in ACTION_SCHEMAS:
            def http(path,body=None,timeout=10):
                if path=='/api/generate':self.assertEqual(body['format'],'json')
                return '{}'
            with patch('rg_collect.http',side_effect=http):c.Local().generate(ep(toolkit=toolkit),'test','report',0,ROOT)
        inheritance=c.read(ROOT/'evidence/inheritance.json')['v01_source_sha256']
        for name in ('config/prompts.json','config/episodes.json','config/report-schema.json','rg_stats.py'):
            self.assertEqual(sha((ROOT/name).read_bytes()),inheritance[name])

    def test_scientific_functions_unchanged(self):
        # Compare portable source witnesses, not a dependency on a sibling checkout.
        expected=c.read(ROOT/'evidence/scientific-functions.json')
        for name,functions in expected.items():
            tree=ast.parse((ROOT/name).read_text())
            actual={n.name:sha(ast.dump(n,include_attributes=False).encode()) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            for function,digest in functions.items():self.assertEqual(actual[function],digest,(name,function))

    def test_schema_bytes_reserved_per_toolkit(self):
        for toolkit in ACTION_SCHEMAS:
            for phase in ('action','report'):
                prompt=render(ep(toolkit=toolkit),[],10,phase)
                bound=reserve(prompt,phase,toolkit)
                raw_bytes=len(prompt.encode())+len(P['system'].encode())+len(canonical(schema_for(phase,toolkit)).encode())+826
                self.assertGreaterEqual(bound['input_tokens'],raw_bytes*1.10)


class RealEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.envelope=c.read(ROOT/'fixtures/real-claude-envelope.json')
        self.e=ep('claude');self.bound=reserve(render(self.e,[],10,'action'),'action')

    def raw(self,**changes):
        return {'stdout':canonical({**self.envelope,**changes}),'stderr':'','returncode':0}

    def test_real_zero_count_tree_and_structured_two_turn_envelope(self):
        raw={'stdout':(ROOT/'fixtures/real-claude-envelope.json').read_text(),'stderr':'','returncode':0}
        self.assertTrue(self.envelope['subagent_stats'])
        self.assertEqual(c.decode(raw,self.e,'action',self.bound),a())
        self.assertEqual(checked_value(raw,self.e,'action',self.bound,False),a())
        self.assertEqual(c.usage(self.envelope,'claude'),(1602,199))
        self.assertEqual(c.cost_micro(1602,199,self.envelope),16788)
        for n,stop in itertools.product((1,2),('end_turn','tool_use')):
            self.assertEqual(c.decode(self.raw(num_turns=n,stop_reason=stop),self.e,'action',self.bound),a())

    def test_positive_nested_subagent_and_tool_activity_is_fatal(self):
        for changes in ({'subagent_stats':{'spawned':1}}, {'subagent_stats':{'by_type':{'worker':{'completed':1}}}},
                        {'subagent_stats':{'spawned':True}}, {'subagent_stats':{'spawned':-1}},
                        {'subagent_stats':{'spawned':'0'}}, {'safety_stops':1}, {'queued_turn_count':1},
                        {'permission_denials':[{'tool':'x'}]},
                        {'usage':{**self.envelope['usage'],'server_tool_use':{'web_search_requests':1}}}):
            with self.subTest(changes=changes):
                with self.assertRaises(c.Stop):c.decode(self.raw(**changes),self.e,'action',self.bound)
                with self.assertRaises(ValueError):checked_value(self.raw(**changes),self.e,'action',self.bound,False)

    def test_turn_types_and_payload_fallback_are_rejected(self):
        for n in (None,0,3,True,1.0,'2'):
            with self.subTest(n=n),self.assertRaises(c.Stop):c.decode(self.raw(num_turns=n),self.e,'action',self.bound)
        for payload in (None,[],canonical(a())):
            with self.subTest(payload=payload),self.assertRaises(ModelOutputError):
                c.decode(self.raw(structured_output=payload,result=canonical(a())),self.e,'action',self.bound)

    def test_real_fixture_is_preserved_in_an_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);source=(ROOT/'fixtures/real-claude-envelope.json').read_text()
            class RealFirst(Fake):
                def generate(inner,*args):
                    if inner.calls==0:
                        inner.calls+=1;return {'stdout':source,'stderr':'','returncode':0}
                    return super().generate(*args)
            ledger=c.Ledger(base/'ledger.jsonl')
            out=c.run_episode(self.e,RealFirst(),base,ledger,c.ActiveTime(base/'time',7200),'fake',True)
            self.assertTrue(out['trajectory_valid']);self.assertIsNone(out['error'])
            self.assertEqual(c.read(base/'episodes'/self.e['id']/'0.raw.json')['stdout'],source)
            self.assertEqual(sum(ledger.holds.values()),0)

    def test_done_false_is_fatal_and_never_executes_or_retries(self):
        for done in (False,None,1,'true'):
            with self.subTest(done=done),tempfile.TemporaryDirectory() as tmp:
                class Incomplete(Fake):
                    def generate(inner,*args):
                        raw=super().generate(*args);e=strict_load(raw['stdout']);e['done']=done
                        raw['stdout']=canonical(e);return raw
                base=Path(tmp);provider=Incomplete()
                saved=c.run_episode(ep(),provider,base,c.Ledger(base/'ledger'),c.ActiveTime(base/'time',1000),'fake',True)
                self.assertEqual(provider.calls,1);self.assertEqual(saved['events'],[])
                self.assertTrue((base/'STOP.json').exists())


class ProjectBudgetTests(unittest.TestCase):
    def test_exact_prior_is_reconstructed_and_never_released(self):
        prior=f.verify_prior(ROOT)
        self.assertEqual(prior['settled_micro_usd'],5660781)
        self.assertEqual(sum(prior['holds'].values()),293888)
        with tempfile.TemporaryDirectory() as tmp:
            ledger=c.Ledger(Path(tmp)/'ledger')
            ledger.event(**prior)
            self.assertEqual(ledger.exposure,5954669)
            for ident in prior['holds']:
                with self.assertRaises(c.Stop):ledger.event(event='release',id=ident)
            with self.assertRaises(c.Stop):ledger.event(**prior)
            # USD24M would fit a reset ledger, but must fail with the carry.
            with self.assertRaises(c.Stop):ledger.event(event='reserve',id='new',amount=24000000)
            self.assertEqual(c.Ledger(ledger.path).exposure,5954669)

    def test_independent_reconciliation_keeps_carry_after_new_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);ledger=c.Ledger(base/'ledger.jsonl');ledger.event(**f.verify_prior(ROOT))
            episode=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')
            c.run_episode(episode,Fake(),base,ledger,c.ActiveTime(base/'time',7200),'fake',True)
            result=reconcile(ROOT,base)
            self.assertEqual(result['settled_micro_usd'],5660781+7200)
            self.assertEqual(result['outstanding_micro_usd'],293888)
            self.assertEqual(result['prior_settled_micro_usd'],5660781)
            self.assertEqual(result['status'],'RECONCILED')

    def test_changed_or_missing_live_v01_ledger_blocks_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'v0.2';f.prepare(root)
            with self.assertRaises(c.Stop):c.prior_spend_gate(root)
            c.save(root.parent/'collection/placeholder.json',{})
            (root.parent/'collection/ledger.jsonl').write_bytes(b'changed')
            with self.assertRaises(c.Stop):c.prior_spend_gate(root)
            (root.parent/'collection/ledger.jsonl').write_bytes((ROOT/'evidence/v01-ledger.jsonl').read_bytes())
            self.assertEqual(c.prior_spend_gate(root),f.verify_prior(ROOT))

    def test_whole_new_budget_includes_v01_exposure(self):
        sizing=c.read(ROOT/'config/sizing.json')
        self.assertEqual(sizing['frontier_micro_usd'],16145920)
        self.assertEqual(sizing['cumulative_including_prior_and_reserve_micro_usd'],23100589)
        self.assertLess(sizing['cumulative_including_prior_and_reserve_micro_usd'],25000000)


class ProvenanceTests(unittest.TestCase):
    def test_full_input_attestation_uses_activity_api_and_detects_changed_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);(root/'example.py').write_text('x=1\n');digest=f.freeze(root)
            commit='a'*40;event={'activity_type':'push','after':commit,'ref':'refs/heads/claude/receipt-gap-v02',
                                'timestamp':'2026-01-01T00:00:00Z','id':7}
            event['timestamp']=c.read(root/'freeze.json')['created_at']
            c.save(root/'event.json',event)
            def git(cmd,**kwargs):
                if cmd[1]=='rev-parse':return commit+'\n'
                if cmd[1]=='remote':return 'https://github.com/Robin84Bran/research.git\n'
                if cmd[1]=='ls-remote':return commit+'\t'+event['ref']+'\n'
                if cmd[1]=='show':return (root/cmd[2].split(':receipt-gap/v0.2/',1)[1]).read_bytes()
                raise AssertionError(cmd)
            def corrupt(cmd,**kwargs):
                if cmd[1]=='show' and cmd[2].endswith('/example.py'):return b'wrong'
                return git(cmd,**kwargs)
            with patch('rg_freeze.subprocess.check_output',side_effect=corrupt),self.assertRaises(c.Stop):
                f.attest(root,root/'event.json',commit,'receipt-gap/v0.2',Path(tmp)/'clone')
            self.assertFalse((root/'collection/push.json').exists())
            with patch('rg_freeze.subprocess.check_output',side_effect=git):
                f.attest(root,root/'event.json',commit,'receipt-gap/v0.2',Path(tmp)/'clone')
            self.assertEqual(c.push_gate(root),digest)
            self.assertEqual(c.read(root/'collection/push.json')['source_api'],'/repos/Robin84Bran/research/activity')
            c.save(root/'collection/episodes/new/0.start.json',{'freeze_sha256':'old-v01','started_at':c.now()})
            with self.assertRaises(c.Stop):c.push_gate(root)

    def test_rebuild_rejects_schema_tamper_and_fake_model_failure(self):
        for mode in ('schema','failure'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)/'data';dry_run(ROOT,base)
                path=next((base/'episodes').glob('*/0.request.json')) if mode=='schema' else next((base/'episodes').glob('*/0.parsed.json'))
                value=c.read(path)
                if mode=='schema':value['schema']={}
                else:value.update(error='fabricated model failure',value=None)
                path.write_text(canonical(value))
                with self.assertRaises(ValueError):load_rows(ROOT,base)

    def test_added_unfrozen_code_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root);(root/'extra.py').write_text('x=1')
            with self.assertRaises(c.Stop):f.verify(root)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);(root/'bad.py').symlink_to(ROOT/'rg_core.py')
            with self.assertRaises(c.Stop):f.freeze(root)


class FailureAuditTests(unittest.TestCase):
    def test_inventory_covers_all_raise_sites(self):
        documented=c.read(ROOT/'evidence/failure-audit-r1.json')['raises']
        actual={(name,n.lineno) for name in ('rg_core.py','rg_collect.py') for n in ast.walk(ast.parse((ROOT/name).read_text())) if isinstance(n,ast.Raise)}
        self.assertEqual(actual,{(r['file'],r['line']) for r in documented})

    def test_old_push_cannot_open_new_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root)
            event={'activity_type':'push','after':'a'*40,'ref':'refs/heads/x','timestamp':'2026-01-01T00:00:00Z','id':1}
            c.save(root/'old.json',event)
            with patch('rg_freeze.subprocess.check_output',side_effect=AssertionError('must reject before Git')):
                with self.assertRaises(c.Stop):f.attest(root,root/'old.json','a'*40,'receipt-gap/v0.2')
