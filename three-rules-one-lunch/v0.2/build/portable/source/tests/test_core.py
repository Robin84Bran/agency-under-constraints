import json
from pathlib import Path
import shutil
import subprocess
import unittest
from trl_core import *


class WorldTests(unittest.TestCase):
    def test_toy_hash(self):
        self.assertEqual(sha((ROOT/'evidence/toy-model.mjs').read_bytes()),'b687e43d52ed57165684662bef48c982b3cedcdac69fec333d6268ac6200a5ad')

    def test_rng_cross_language_vectors(self):
        for row in json.loads((ROOT/'fixtures/js-vectors.json').read_text())['rng']:
            r=ToyRNG(row['seed'])
            self.assertEqual([r() for _ in row['values']],row['values'])

    def test_all_world_fixtures(self):
        expected=json.loads((ROOT/'fixtures/worlds.json').read_text())
        self.assertEqual(expected,[world(s) for s in range(100)])
        self.assertEqual(expected,json.loads((ROOT/'fixtures/js-vectors.json').read_text())['worlds'])

    @unittest.skipUnless(shutil.which('node'),'Node optional: saved JS vectors remain verified by Python')
    def test_js_independent_regeneration(self):
        result=json.loads(subprocess.check_output(['node',str(ROOT/'fixtures/world-vectors.mjs')]))
        self.assertEqual(result,json.loads((ROOT/'fixtures/js-vectors.json').read_text()))

    def test_wrapping(self):
        f=field([[0,0],[0,0]])
        self.assertEqual(f[1],f[7]);self.assertEqual(f[8],f[40])
        self.assertEqual(f[0],1000);self.assertEqual(f[1],717)
        self.assertEqual(f[9],513)

    def test_relocation_permutation(self):
        for seed in range(100):
            w=world(seed)
            for c in range(48):
                moved=((c//8+3)%6)*8+(c%8+4)%8
                self.assertEqual(w['fields'][0][c],w['fields'][1][moved])

    def test_coincident_centers_retained(self):
        w=next(world(s) for s in range(1000) if len({tuple(c) for c in world(s)['centers']})==1)
        self.assertEqual(len(w['centers']),2)
        self.assertEqual(max(w['fields'][0]),1000)

    def test_seed_bounds(self):
        for s in (-1,2**32,True,1.0):
            with self.assertRaises(ValueError):world(s)


class ContractTests(unittest.TestCase):
    def test_exact_literals(self):
        self.assertEqual(len(SYSTEM.encode()),68)
        self.assertEqual(len(INSTRUCTION.encode()),829)
        for q in (1,3):self.assertEqual(len(canonical(schema(q)).encode()),194)

    def test_valid_null_duplicates(self):
        self.assertEqual(action(strict_load(' \t\r\n{"cells":[12,12,null]}\n'),3),{'cells':[12,12,None]})

    def test_boolean_cells(self):
        for x in (True,False):
            with self.assertRaises(ValueError):action({'cells':[x]},1)

    def test_float_strings_bounds(self):
        for x in (1.,'1',-1,48,[],{}):
            with self.assertRaises(ValueError):action({'cells':[x]},1)

    def test_exact_keys_quota(self):
        for x in ({},{'cells':[]},{'cells':[0,1]},{'cells':[0],'x':0},[],{'cells':0}):
            with self.assertRaises(ValueError):action(x,1)

    def test_strict_json_edge_cases(self):
        for raw in ('{"cells":[0],"cells":[1]}','{"cells":[NaN]}','{"cells":[Infinity]}',
                    '```json\n{"cells":[1]}\n```','{"cells":[1]} {}','prose {"cells":[1]}','\ufeff{"cells":[1]}','\v{"cells":[1]}'):
            with self.assertRaises(ValueError):strict_load(raw)

    def test_worker_pair_first_round_identical(self):
        for j in (1,2,3):self.assertEqual(render('shared',1,j,[]),render('private',1,j,[]))
        self.assertEqual(generation_seed(19,4,3),19043)

    def test_visibility_private_shared(self):
        h=[[1,3,8,20],[1,1,9,40],[1,2,10,0]]
        self.assertEqual(visible('private',2,3,h),[[1,3,8,20]])
        self.assertEqual(visible('shared',2,3,h),sorted(h))

    def test_no_hidden_fields_in_prompt(self):
        p=render('shared',2,3,[[1,1,47,1000]])
        payload=strict_load(p.split('\n')[-1])
        self.assertEqual(set(payload),{'arm','quota','receipts','role','round'})
        for hidden in ('seed','centers','fields','threshold','shared'):
            self.assertNotIn('"'+hidden+'"',p)

    def test_current_round_rejected(self):
        with self.assertRaises(ValueError):render('shared',2,1,[[2,1,0,0]])
        with self.assertRaises(ValueError):render('private',2,1,[[1,2,0,0],[1,2,0,0]])

    def test_invalid_central_never_partly_executes(self):
        s=Simulator(0)
        with self.assertRaises(ValueError):s.execute('central',{0:{'cells':[1,2,True]}})
        self.assertEqual(s.events,[]);self.assertEqual(s.receipts,[])

    def test_invalid_worker_batch_never_executes(self):
        s=Simulator(0)
        with self.assertRaises(ValueError):s.execute('shared',{1:{'cells':[1]},2:{'cells':[2]},3:{'cells':[48]}})
        self.assertEqual(s.events,[])

    def test_duplicate_rewards_nondepleting(self):
        s=Simulator(0);s.execute('central',{0:{'cells':[0,0,0]}})
        self.assertEqual(len(s.receipts),3)
        self.assertEqual(len({e['reward'] for e in s.events}),1)

    def test_null_creates_no_receipt(self):
        s=Simulator(0);s.execute('central',{0:{'cells':[None,None,None]}})
        self.assertEqual(s.receipts,[]);self.assertTrue(all(e['reward'] is None for e in s.events))

    def test_failure_keeps_factual_unknown(self):
        s=Simulator(0);s.execute('central',{0:{'cells':[0,1,2]}});s.terminate('failure',[1])
        self.assertEqual(len(s.events),12)
        self.assertTrue(all(e['reward'] is None and e['operational_reward']==0 for e in s.events[3:]))
        self.assertEqual(s.events[3]['status'],'technical');self.assertEqual(s.events[4]['status'],'missing')
