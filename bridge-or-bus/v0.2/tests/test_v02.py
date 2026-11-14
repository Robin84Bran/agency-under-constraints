"""v0.2 boundary, saved-byte regressions, identity, budget and freeze checks."""
import copy
import itertools
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,SCHEMAS,P,World,act,canonical,strict_load,sha,render,subholds
from bob_collect import request_for,usage,Stop,Ledger,collect,read
from bob_identity import identity,check_local_identity
from audit_v01 import validate


def matches(value,schema):
    """Small test-only evaluator of this schema's keywords, independent of action()."""
    if 'type' in schema:
        ts=schema['type'];ts=[ts] if type(ts) is str else ts
        checks={'object':type(value) is dict,'string':type(value) is str,'integer':type(value) is int,'null':value is None,'boolean':type(value) is bool}
        if not any(checks[t] for t in ts):return False
    if 'enum' in schema and not any(type(value) is type(v) and value==v for v in schema['enum']):return False
    if type(value) is dict:
        if set(schema.get('required',[]))-set(value):return False
        if schema.get('additionalProperties') is False and set(value)-set(schema['properties']):return False
        if any(not matches(value[k],s) for k,s in schema.get('properties',{}).items() if k in value):return False
    if type(value) is int:
        if value<schema.get('minimum',value) or value>schema.get('maximum',value):return False
    if type(value) is str:
        import re
        if not schema.get('minLength',0)<=len(value)<=schema.get('maxLength',len(value)):return False
        if 'pattern' in schema and re.search(schema['pattern'],value) is None:return False
    if 'anyOf' in schema and not any(matches(value,s) for s in schema['anyOf']):return False
    return True


class SchemaBoundaryTests(unittest.TestCase):
    def test_same_schema_both_arms_all_worlds_and_phases(self):
        for arm,world in itertools.product(('registry','stale'),('stable','rename','unit','required')):
            ep=dict(model='qwen7b',seed=0,world=world,arm=arm)
            for phase in ('action','report'):
                request=request_for(ep,render(ep,[],6,phase))
                self.assertEqual(request['format'],SCHEMAS[phase]);self.assertIsInstance(request['format'],dict)

    def test_legal_world_independent_shapes(self):
        for a in [act('lookup',item='item-000000'),act('convert',grams=1250),act('convert',mass_g=1250),act('submit',grams=1250),act('submit',grams=1250,revision=1),act('describe',target='convert'),act('finish')]:
            self.assertTrue(matches(a,SCHEMAS['action']),canonical(a))
        for a in [act('lookup',item='item-000000',mass_g=150),act('convert',grams=1,mass_g=1),act('convert',grams=1.25),act('finish',revision=1),act('submit',grams=True),act('lookup',item=None)]:
            self.assertFalse(matches(a,SCHEMAS['action']),canonical(a))

    def test_provider_contract_agrees_with_independent_six_field_spec(self):
        # Combinatorial operation shapes, including unused fields/permissions.
        for op,flags in itertools.product(('lookup','convert','submit','describe','finish'),itertools.product((False,True),repeat=5)):
            a=act(op,**{k:v if f else None for (k,v),f in zip([('item','item-000000'),('grams',1250),('mass_g',1250),('revision',1),('target','convert')],flags)})
            try:validate(a,'registry');expected=True
            except ValueError:expected=False
            self.assertEqual(matches(a,SCHEMAS['action']),expected,canonical(a))

    def test_stale_call_after_rename_reaches_tool_error_then_can_recover(self):
        w=World(0,'rename','stale');w.step(act('lookup',item=w.item))
        old=act('convert',grams=w.mass);new=act('convert',mass_g=w.mass)
        self.assertTrue(matches(old,SCHEMAS['action']));self.assertTrue(matches(new,SCHEMAS['action']))
        self.assertEqual(w.step(old)['code'],'SCHEMA');self.assertEqual(w.step(new)['code'],'OK')

    def test_required_revision_not_forced_and_new_fields_do_not_reveal_truth(self):
        for world in ('required','stable'):
            w=World(0,world,'stale');w.step(act('lookup',item=w.item));w.step(act('convert',grams=w.mass))
            a=act('submit',grams=w.mass)
            self.assertTrue(matches(a,SCHEMAS['action']))
            self.assertEqual(w.step(a)['code'],'SCHEMA' if world=='required' else 'OK')
        w=World(0,'rename','stale');a=act('convert',mass_g=w.mass)
        self.assertTrue(matches(a,SCHEMAS['action']));self.assertEqual(w.step(a)['code'],'SCHEMA')

    def test_describe_permission_remains_harness_enforced(self):
        a=act('describe',target='convert');self.assertTrue(matches(a,SCHEMAS['action']))
        with self.assertRaises(ValueError):World(0,'stable','stale').step(a)

    def test_raw_v01_rejection_reasons_and_legitimate_mass_g(self):
        data=read(ROOT/'evidence/v01-replay.json')
        self.assertEqual(data['counts']['falsely_rejected_legal_actions'],0)
        self.assertEqual(data['counts']['rejected_actions'],953)
        for label,n in [('mass_g',88),('cross-field legality or unavailable operation',311)]:
            rows=[r for r in data['rejections'] if r['id'].startswith('qwen7b') and r['recorded_error']=='ValueError: '+label]
            self.assertEqual(len(rows),n);self.assertTrue(all(not r['legal'] for r in rows))
        w=World(0,'rename','registry');w.step(act('lookup',item=w.item));self.assertEqual(w.step(act('convert',mass_g=w.mass))['code'],'OK')
        with self.assertRaises(ValueError):w.step(act('convert',mass_g=123.45))


class InheritanceTests(unittest.TestCase):
    def test_all_pinned_manifests_and_layers_are_verified(self):
        for model,show in identity(ROOT).items():
            check_local_identity(ROOT,model,show)
            with self.assertRaises(Stop):check_local_identity(ROOT,model,dict(show,system='wrong'))

    def test_cost_uses_larger_provider_or_api_value_without_counting_reasoning_twice(self):
        env=read(ROOT/'fixtures/real-claude-envelope.json');env['total_cost_usd']=0
        counted=usage(env,'claude')
        self.assertEqual(counted['micro_usd'],4*1602+20*199)
        env['total_cost_usd']=.02;self.assertEqual(usage(env,'claude')['micro_usd'],20000)

    def test_historical_spend_and_unresolved_holds_survive_carry(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cost.jsonl';ledger=Ledger(path)
            ledger.event(event='carry',id='v01',spent=3000000,held=1000000)
            self.assertEqual(Ledger(path).exposure,4000000)
            with self.assertRaises(Stop):Ledger(path).event(event='reserve',id='new',subholds=[3000000]*7)
            with self.assertRaises(Stop):Ledger(path).event(event='carry',id='v01',spent=0,held=0)

    def test_prior_archive_zero_is_verified_not_assumed(self):
        prior=read(ROOT/'config/prior-spend.json');raw=(ROOT/prior['ledger_file']).read_bytes()
        self.assertEqual(sha(raw),prior['ledger_sha256'])
        entries=[strict_load(x) for x in raw.splitlines()]
        self.assertEqual(sum(e['actual'] for e in entries if e['event']=='settle'),prior['settled_micro_usd'])
        self.assertEqual(prior['unresolved_hold_micro_usd'],0)

    def test_real_queued_work_is_fatal(self):
        from bob_validation import claude_contract
        env=read(ROOT/'fixtures/real-claude-envelope.json');env['queued_turn_count']=1
        with self.assertRaises(Stop):claude_contract(env)

    def test_ollama_evidence_contains_version_schema_object_and_grammar(self):
        data=read(ROOT/'evidence/ollama-schema-support.json')
        self.assertEqual((data['status'],data['version'],data['model_calls']),('VERIFIED','0.33.3',0))
        self.assertEqual(data['live_schema_compilation_status'],'UNKNOWN')
        self.assertTrue(any('anyOf'==s['text'] for f in data['sources'] for s in f['snippets']))


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        from bob_freeze import inventory
        for name in inventory(ROOT):
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        self.inventory=inventory
        from bob_offline import write
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256=sha(canonical(inventory(self.root)).encode()),kind='SYNTHETIC_TEST_FIXTURE'))
    def tearDown(self):self.tmp.cleanup()
    def test_create_verify_tamper_and_never_overwrite(self):
        from bob_freeze import create,verify
        create(self.root);self.assertEqual(verify(self.root)['version'],'0.2')
        with self.assertRaises(Stop):create(self.root)
        (self.root/'config/action-schema.json').write_text('{}')
        with self.assertRaises(Stop):verify(self.root)
    def test_no_push_no_network_and_no_starts(self):
        from bob_freeze import create
        create(self.root)
        with patch('bob_collect.http') as network,patch('bob_collect.subprocess.run') as process:
            with self.assertRaises(Stop):collect(self.root,['qwen7b'])
            network.assert_not_called();process.assert_not_called()
        self.assertFalse((self.root/'collection/episode-starts').exists())
    def test_wrong_freeze_and_predated_push_cannot_admit(self):
        import datetime as dt
        from bob_freeze import create,check_push
        from bob_offline import write
        create(self.root);record=read(self.root/'freeze.json')
        event=dict(activity_type='push',after='a'*40,id=42,ref='refs/heads/main',timestamp='2026-01-01T00:00:00+00:00')
        write(self.root/'collection/push-event.json',event)
        receipt=dict(commit='a'*40,repo='Robin84Bran/research',freeze_sha256='wrong',evidence_file='collection/push-event.json',evidence_sha256=sha((self.root/'collection/push-event.json').read_bytes()))
        with self.assertRaises(Stop):check_push(self.root,record,receipt)
        receipt.update(freeze_sha256=sha((self.root/'freeze.json').read_bytes()),github_time=event['timestamp'],remote_ref=event['ref'],server_event_id=42)
        with self.assertRaises(Stop):check_push(self.root,record,receipt)

class SavedReplyTests(unittest.TestCase):
    def test_all_953_raw_rejections_are_independently_invalid_at_saved_state(self):
        from audit_v01 import Replay,load
        from bob_core import DESCRIPTIONS,action
        rows=read(ROOT/'fixtures/v01-rejected-replies.json');self.assertEqual(len(rows),953)
        for row in rows:
            raw=row['raw_stdout'].encode();self.assertEqual(sha(raw),row['raw_sha256'])
            state=Replay(row['episode'],DESCRIPTIONS)
            for event in row['prior_events']:
                self.assertEqual(state.step(event['action']),event['observation'])
            response=load(raw)['response']
            with self.subTest(id=row['id']):
                with self.assertRaises(ValueError):validate(load(response),row['episode']['arm'])
                with self.assertRaises(ValueError):action(strict_load(response),row['episode']['arm'])

class HistoricalTimeTests(unittest.TestCase):
    def test_prior_local_charge_cannot_reset_across_versions_or_resume(self):
        from bob_collect import ActiveTime
        from bob_offline import write
        prior=read(ROOT/'config/prior-spend.json')
        raw=(ROOT/prior['local_time_file']).read_bytes();self.assertEqual(sha(raw),prior['local_time_sha256'])
        rows=[strict_load(x) for x in raw.splitlines()];starts={x['id']:x['seconds'] for x in rows if x['event']=='start'};settled={x['id']:x['seconds'] for x in rows if x['event']=='settle'}
        self.assertEqual(sum(settled.get(k,v) for k,v in starts.items()),prior['local_active_seconds'])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write(root/'config/prior-spend.json',prior)
            timer=ActiveTime(root/'collection/local-time.jsonl',prior['local_active_seconds']+100)
            self.assertEqual(timer.charged,prior['local_active_seconds'])
            with self.assertRaises(Stop):timer.begin('new-call',230)
            self.assertEqual(ActiveTime(timer.path,43200).charged,timer.charged)
