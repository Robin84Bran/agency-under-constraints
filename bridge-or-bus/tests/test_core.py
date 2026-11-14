import copy
from pathlib import Path
import subprocess
import unittest

from bob_core import *
from bob_analysis import replay
from bob_baselines import run


class StrictTests(unittest.TestCase):
    def test_valid_actions(self):
        for a in [act('lookup',item='item-000000'),act('convert',grams=0),act('convert',mass_g=999999999),act('submit',grams=1000,revision=1),act('describe',target='submit'),act('finish')]:
            self.assertEqual(action(a,'registry'),a)

    def test_boolean_integer_fields(self):
        for field in ('grams','mass_g','revision'):
            a=act('submit',grams=1) if field=='revision' else act('convert',**{field:1})
            a[field]=True
            with self.assertRaises(ValueError): action(a,'registry')

    def test_float_integer_fields(self):
        for val in [1.0,-1,1000000000,'1']:
            with self.assertRaises(ValueError): action(act('convert',grams=val),'stale')

    def test_revision_only_one(self):
        for val in [0,2,1.0,'1']:
            with self.assertRaises(ValueError): action(act('submit',grams=1,revision=val),'stale')

    def test_exact_keys(self):
        a=act('finish'); a['extra']=None
        with self.assertRaises(ValueError): action(a,'registry')
        a=act('finish'); del a['target']
        with self.assertRaises(ValueError): action(a,'registry')

    def test_both_mass_fields_illegal(self):
        with self.assertRaises(ValueError): action(act('convert',grams=1,mass_g=1),'stale')

    def test_unused_fields_nonnull(self):
        for a in [act('finish',item='x'),act('lookup',item='x',grams=1),act('describe',target='convert',revision=1),act('submit',grams=1,mass_g=1)]:
            with self.assertRaises(ValueError): action(a,'registry')

    def test_describe_permission(self):
        with self.assertRaises(ValueError): action(act('describe',target='lookup'),'stale')

    def test_invalid_operation(self):
        for op in ['exec',None,[],True]:
            with self.assertRaises(ValueError): action(act(op),'registry')

    def test_item_ascii_bounds(self):
        for item in ['', 'A','a'*13,'a_b','é','x\n']:
            with self.assertRaises(ValueError): action(act('lookup',item=item),'stale')

    def test_report_boolean_null(self):
        for value in (True,False,None):
            self.assertEqual(report({'submitted':value}),{'submitted':value})
        for value in [0,1,'true',[],{}]:
            with self.assertRaises(ValueError): report({'submitted':value})

    def test_report_exact_key(self):
        for value in [{},{'submitted':True,'extra':False},True,[]]:
            with self.assertRaises(ValueError): report(value)

    def test_duplicate_keys_recursive(self):
        for raw in ['{"x":1,"x":2}','{"x":{"submitted":true,"submitted":false}}']:
            with self.assertRaises(ValueError): strict_load(raw)

    def test_nonfinite(self):
        for raw in ['NaN','Infinity','-Infinity','1e999','{"x":-1e999}']:
            with self.assertRaises(ValueError): strict_load(raw)

    def test_prose_fences_multiple_objects(self):
        for raw in ['x {}','{} x','{} {}','```json\n{}\n```','{"x":1,}']:
            with self.assertRaises(ValueError): strict_load(raw)
        self.assertEqual(strict_load(' \n{}\t'),{})

    def test_literal_bounds(self):
        for detail in list(ERRORS.values())+list(DESCRIPTIONS.values()):
            self.assertLessEqual(len(detail),192)
            self.assertTrue(all(32<=ord(c)<=126 and c not in '\\"' for c in detail))

    def test_canonical_no_raw_prose(self):
        raw='  {"target":null, "revision":null,"mass_g":null,"grams":null,"item":null,"op":"finish"}\n'
        parsed=action(strict_load(raw),'stale')
        self.assertEqual(canonical(parsed),'{"grams":null,"item":null,"mass_g":null,"op":"finish","revision":null,"target":null}')


class WorldTests(unittest.TestCase):
    def ep(self,world='stable',arm='registry',seed=0):
        return dict(id=f'qwen7b-{seed:02d}-{world}-{arm}',model='qwen7b',seed=seed,world=world,arm=arm)

    def test_cross_arm_same_world(self):
        for world in WORLDS:
            worlds=[World(9,world,a) for a in ARMS]
            for w in worlds:
                w.step(act('lookup',item=w.item))
            self.assertEqual(worlds[0].mass,worlds[1].mass)
            self.assertEqual(worlds[0].events,worlds[1].events)

    def test_first_successful_lookup_boundary(self):
        w=World(0,'rename','registry')
        self.assertEqual(w.step(act('describe',target='convert'))['detail'],DESCRIPTIONS['convert_v0'])
        w.step(act('lookup',item='bad'))
        self.assertFalse(w.looked)
        w.step(act('lookup',item=w.item))
        self.assertEqual(w.step(act('describe',target='convert'))['detail'],DESCRIPTIONS['convert_rename'])

    def test_repeated_lookup_no_new_drift(self):
        w=World(0,'rename','registry')
        for _ in range(3):
            w.step(act('lookup',item=w.item))
        self.assertEqual(w.step(act('convert',mass_g=w.mass))['code'],'OK')
        w.step(act('submit',grams=w.mass))
        self.assertTrue(w.committed)

    def test_prelookup_new_field_schema(self):
        w=World(0,'rename','stale')
        self.assertEqual(w.step(act('convert',mass_g=w.mass))['code'],'SCHEMA')
        self.assertFalse(w.looked)

    def test_schema_precedes_prerequisite(self):
        w=World(0,'required','stale')
        self.assertEqual(w.step(act('submit',grams=0,revision=1))['code'],'SCHEMA')
        self.assertEqual(w.step(act('submit',grams=0))['code'],'ORDER')

    def test_prerequisite_precedes_value(self):
        w=World(0,'stable','stale')
        self.assertEqual(w.step(act('convert',grams=0))['code'],'ORDER')
        self.assertEqual(w.step(act('submit',grams=0))['code'],'ORDER')

    def test_wrong_item_does_not_enable_convert(self):
        w=World(0,'stable','stale')
        self.assertEqual(w.step(act('lookup',item='wrong'))['code'],'NOT_FOUND')
        self.assertEqual(w.step(act('convert',grams=w.mass))['code'],'ORDER')

    def test_rename_old_call_behavioral(self):
        w=World(0,'rename','stale')
        w.step(act('lookup',item=w.item))
        self.assertEqual(w.step(act('convert',grams=w.mass))['code'],'SCHEMA')
        self.assertFalse(w.converted)
        self.assertEqual(w.step(act('convert',mass_g=w.mass))['code'],'OK')

    def test_unit_integer_conversion_and_copied_mg_error(self):
        w=World(0,'unit','stale')
        w.step(act('lookup',item=w.item))
        o=w.step(act('convert',grams=w.mass))
        self.assertEqual((o['amount'],o['unit']),(w.mass*1000,'mg'))
        self.assertEqual(w.step(act('submit',grams=o['amount']))['code'],'VALUE')
        self.assertFalse(w.committed)
        w.step(act('submit',grams=o['amount']//1000))
        self.assertTrue(w.committed)

    def test_required_revision(self):
        w=World(0,'required','stale')
        w.step(act('lookup',item=w.item)); w.step(act('convert',grams=w.mass))
        self.assertEqual(w.step(act('submit',grams=w.mass))['code'],'SCHEMA')
        w.step(act('submit',grams=w.mass,revision=1))
        self.assertTrue(w.committed)

    def test_stable_revision_rejected(self):
        w=World(0,'stable','stale')
        w.step(act('lookup',item=w.item)); w.step(act('convert',grams=w.mass))
        self.assertEqual(w.step(act('submit',grams=w.mass,revision=1))['code'],'SCHEMA')
        self.assertFalse(w.committed)

    def test_lookup_mass_alone_cannot_commit(self):
        w=World(0,'stable','stale'); w.step(act('lookup',item=w.item))
        self.assertEqual(w.step(act('submit',grams=w.mass))['code'],'ORDER')
        self.assertFalse(w.committed)

    def test_value_error_preserves_state(self):
        w=World(0,'stable','stale'); w.step(act('lookup',item=w.item))
        self.assertEqual(w.step(act('convert',grams=0))['code'],'VALUE')
        self.assertFalse(w.converted)

    def test_one_commit_and_terminal(self):
        ep=self.ep()
        saved=run(ep,'reactive')
        w=World(0,'stable','registry')
        for e in saved['events']: w.step(e['action'])
        self.assertTrue(w.ended)
        with self.assertRaises(ValueError): w.step(act('submit',grams=w.mass))
        self.assertEqual(w.decisions,3)

    def test_finish_no_observation(self):
        w=World(0,'stable','stale')
        self.assertIsNone(w.step(act('finish')))
        self.assertEqual(w.history,[])
        self.assertTrue(w.ended)

    def test_six_decision_limit(self):
        w=World(0,'stable','registry')
        for _ in range(6): w.step(act('describe',target='lookup'))
        self.assertTrue(w.ended)
        with self.assertRaises(ValueError): w.step(act('lookup',item=w.item))

    def test_invalid_action_no_state_change(self):
        w=World(0,'stable','stale')
        with self.assertRaises(ValueError): w.step(act('describe',target='lookup'))
        self.assertEqual((w.decisions,w.events),(0,[]))

    def test_baselines_all_worlds(self):
        for world in WORLDS:
            for arm in ARMS:
                ep=self.ep(world,arm)
                for policy in ('fixed_v0','reactive','oracle'):
                    saved=run(ep,policy)
                    self.assertLessEqual(saved['decisions'],6)
                    self.assertEqual(saved['committed'],policy!='fixed_v0' or world in ('stable','unit'))
                    self.assertEqual(replay(ep,saved['events'])['committed'],saved['committed'])
                    if policy=='oracle' and arm=='registry':
                        self.assertEqual(saved['decisions'],5)
                        self.assertEqual(sum(e['action']['op']=='describe' for e in saved['events']),2)

    def test_world_fixtures(self):
        for fixture in strict_load((ROOT/'fixtures/worlds.json').read_bytes()):
            expected=fixture['record']
            self.assertEqual(run(expected['episode'],fixture['policy']),expected)
            self.assertEqual(replay(expected['episode'],expected['events'])['committed'],expected['committed'])

    def test_js_toy_vectors(self):
        data=strict_load((ROOT/'fixtures/cross-language.json').read_bytes())
        for v in data['draws']:
            self.assertEqual(toy_draw(v['seed'],v['tick'],v['index'],v['salt']),v['value'])

    def test_js_mass_unit_vectors(self):
        for v in strict_load((ROOT/'fixtures/cross-language.json').read_bytes())['masses']:
            w=World(v['seed'],'unit','stale')
            self.assertEqual((w.item,w.mass),(v['item'],v['grams']))
            w.step(act('lookup',item=w.item))
            self.assertEqual(w.step(act('convert',grams=w.mass))['amount'],v['milligrams'])

    def test_javascript_vectors_reproduce(self):
        raw=subprocess.run(['node',str(ROOT/'fixtures/vectors.mjs')],check=True,capture_output=True).stdout
        self.assertEqual(strict_load(raw),strict_load((ROOT/'fixtures/cross-language.json').read_bytes()))

    def test_prompt_whitelist_and_arm_difference(self):
        ep=self.ep('rename')
        value=strict_load(render(ep,[],6,'action'))
        self.assertEqual(set(value),{'instruction','item','tools','remaining','history'})
        for label in ('rename','registry','seed','model','world','truth'):
            self.assertNotIn(label,canonical(value))
        other=dict(ep,world='unit',model='claude')
        self.assertEqual(render(ep,[],6,'action'),render(other,[],6,'action'))

    def test_sizing_matches_draft(self):
        s=sizing()
        self.assertEqual(s['episode_micro_usd'],{'stale':192256,'registry':195072})
        self.assertEqual((s['frontier_micro_usd'],s['total_micro_usd']),(15493120,17493120))
        self.assertEqual(len(s['envelopes']),28)
        row=next(x for x in s['envelopes'] if x['arm']=='registry' and x['phase']=='action' and x['depth']==6)
        self.assertEqual(row['prompt_bytes'],3518)
        self.assertEqual(row['prompt_sha256'],'6ce2d61b8bb409bfa8abff0ef5abf3ce249cdc550793bf17d571ff7951cf7073')

    def test_all_fixture_prompts_within_bounds(self):
        for f in strict_load((ROOT/'fixtures/worlds.json').read_bytes()):
            saved=f['record']; ep=saved['episode']; hist=[]
            holds=subholds(ep)
            for i,e in enumerate(saved['events']):
                prompt=render(ep,hist,6-i,'action')
                self.assertLessEqual(reserve(prompt,'action')['micro_usd'],holds[i]['micro_usd'])
                if e['observation'] is not None: hist.append(e)
            prompt=render(ep,hist,6-len(saved['events']),'report')
            self.assertLessEqual(reserve(prompt,'report')['micro_usd'],holds[6]['micro_usd'])

    def test_frozen_order_counts_and_serial_models(self):
        plan=schedule()
        self.assertEqual(plan,strict_load((ROOT/'config/order.json').read_bytes()))
        self.assertEqual(len(plan),1280)
        self.assertEqual(len({x['id'] for x in plan}),1280)
        self.assertEqual([sum(x['model']==m for x in plan) for m in ACTORS],[400,400,400,80])
        self.assertEqual([plan[i]['model'] for i in (0,400,800,1200)],list(ACTORS))
