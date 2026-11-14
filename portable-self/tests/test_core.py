import itertools
from collections import Counter
import unittest
from unittest.mock import patch
from ps_core import *
from ps_baselines import baseline

class CoreTests(unittest.TestCase):
    def test_independent_node_vectors(self):
        for f in json.loads((ROOT/'fixtures/generator-vectors.json').read_text()):
            self.assertEqual(f,fixture(f['seed'],f['world']))

    def test_seed_zero_vector(self):
        f=fixture(0,'different-stable')
        self.assertEqual(f['labels'],['c-401e8bb8','c-4280c13e','c-7392435e','c-a6fec45b'])
        self.assertEqual(f['calibration'],[[1,0,3,2],[1,3,2,0],[2,1,3,0],[0,1,2,3]])
        self.assertEqual(f['cal_order'],[0,3,2,1]);self.assertEqual(f['return_order'],[1,3,2,0])
        self.assertEqual(f['slots'],[1,4,3,2]);self.assertEqual(f['targets'][0],[3,2,1,0])

    def test_all_world_invariants(self):
        for s in range(100):
            a=fixture(s,'different-stable');b=fixture(s,'same-stable');c=fixture(s,'stale-remap')
            self.assertEqual(len(set(tuple(m) for m in a['calibration'])),4)
            self.assertEqual(len(set(tuple(m) for m in b['calibration'])),1)
            self.assertEqual(a['calibration'],c['calibration']);self.assertEqual(a['labels'],c['labels'])
            for f in (a,b,c):
                self.assertEqual(len(set(f['labels'])),4)
                for key in ('cal_order','return_order','slots'):
                    self.assertEqual(sorted(f[key]),[1,2,3,4] if key=='slots' else [0,1,2,3])
                for key in ('calibration','returns','targets'):
                    for row in f[key]: self.assertEqual(sorted(row),[0,1,2,3])
            for old,new in zip(a['calibration'],c['returns']): self.assertTrue(all(x!=y for x,y in zip(old,new)))

    def test_collision_blocks(self):
        with patch('ps_core.digest',return_value='a'*64):
            with self.assertRaisesRegex(ValueError,'collision'): fixture(0,'different-stable')

    def test_schedule(self):
        eps=schedule();self.assertEqual(len(eps),1080);self.assertEqual(len({e['id'] for e in eps}),1080)
        self.assertEqual(Counter(e['actor'] for e in eps),dict(qwen7b=420,llama8b=420,qwen1b=180,claude=60))
        self.assertEqual(sum(8 for e in eps if e['actor']!='claude'),8160)
        self.assertEqual(eps,schedule());self.assertEqual(eps[-1]['actor'],'claude')

    def test_strict_json(self):
        for text in ['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}','{"a":1e999}','{}{}','```json\n{}\n```','prefix {}','{"x":{"a":1,"a":2}}']:
            with self.subTest(text=text),self.assertRaises(ValueError): strict_load(text)
        self.assertEqual(strict_load(' \r\n {"controls":[null,1,1,4]}\t'),{'controls':[None,1,1,4]})

    def test_strict_actions(self):
        for controls in [[],[1]*3,[1]*5,[True,1,2,3],[1.,1,2,3],['1',1,2,3],[0,1,2,3],[5,1,2,3],None]:
            with self.subTest(controls=controls),self.assertRaises(ValueError): validate({'controls':controls},'act')
        for obj in [{'controls':[1]*4,'extra':1},{},[],None]:
            with self.assertRaises(ValueError): validate(obj,'act')
        validate({'controls':[None]*4},'act');validate({'controls':[1]*4},'act')

    def test_strict_notes(self):
        for obj in [{'slot':True,'note':''},{'slot':1.,'note':''},{'slot':5,'note':''},{'slot':1,'note':'x'*97},{'slot':1,'note':'\n'},{'slot':1,'note':'é'},{'slot':1,'note':None},{'slot':1,'note':'','other':0}]:
            with self.subTest(obj=obj),self.assertRaises(ValueError): validate(obj,'write')
        for note in ['', ' '*96, '\\'*96, '"'*96]: validate({'slot':1,'note':note},'write',1)
        with self.assertRaises(ValueError): validate({'slot':2,'note':'wrong'},'write',1)

    def test_routes_and_no_leakage(self):
        for arm in ARMS:
            w=World({'seed':0,'world':'different-stable','arm':arm})
            for i in range(8):
                p=w.payload();text=render(p)
                self.assertEqual(set(p),{'console','visit','mode','memory','writable_slot','calibration','targets'})
                self.assertNotIn('world',text);self.assertNotIn('seed',text);self.assertNotIn('feedback',p)
                self.assertEqual(len(p['memory']),1 if arm=='keyed' else 4)
                if arm=='discard': self.assertTrue(all(m['note']=='' for m in p['memory']))
                if i<4:
                    self.assertIsNone(p['targets']);w.step({'slot':p['writable_slot'] or (i+1),'note':p['console']})
                else:
                    self.assertIsNone(p['calibration']);self.assertIsNone(p['writable_slot']);w.step({'controls':[None]*4})
            if arm!='discard': self.assertEqual(set(w.notes),set(w.f['labels']))

    def test_no_raw_history_and_bound(self):
        for arm in ARMS:
            ep={'seed':0,'world':'different-stable','arm':arm};w=World(ep)
            for i in range(8):
                p=w.payload();phase=p['mode'];self.assertLessEqual(len(render(p).encode()),reservation(arm,phase)['prompt_bytes'])
                if i<4: w.step({'slot':p['writable_slot'] or i+1,'note':'\\'*96})
                else: w.step({'controls':[1]*4})

    def test_wrong_and_empty_notes_valid(self):
        w=World({'seed':0,'world':'different-stable','arm':'keyed'})
        w.step({'slot':w.payload()['writable_slot'],'note':'intentionally wrong'})
        w.step({'slot':w.payload()['writable_slot'],'note':''})
        self.assertEqual(w.index,2)

    def test_sizing_exact(self):
        self.assertEqual(len(P['instruction'].encode()),789);self.assertEqual(len(P['system'].encode()),68)
        self.assertEqual([len(canonical(SCHEMAS[k]).encode()) for k in ('write','act')],[199,218])
        self.assertEqual([(reservation(a,'write')['prompt_bytes'],reservation(a,'act')['prompt_bytes']) for a in ARMS],[(1160,1145),(1802,1784),(1034,1016)])
        self.assertEqual([episode_reservation({'arm':a}) for a in ARMS],[172032,194560,167936])
        self.assertEqual(sum(episode_reservation(e) for e in schedule() if e['actor']=='claude'),10690560)

    def test_baselines(self):
        for s in range(100):
            for w in WORLDS:
                oracle=baseline(s,w,'oracle');self.assertEqual((oracle['Y'],oracle['F']),(1,1))
                keyed=baseline(s,w,'keyed-ledger');self.assertEqual(keyed['Y'],0 if w=='stale-remap' else 1)
                if w=='same-stable': self.assertEqual(baseline(s,w,'last-console')['Y'],1)
        self.assertEqual(baseline(0,'different-stable','uniform'),baseline(0,'different-stable','uniform'))

    def test_literal_only(self):
        self.assertIsNotNone(literal_map('1=north 2=east 3=south 4=west'))
        for n in ['north:1 east:2 south:3 west:4','1=north 2=east 3=south 4=south','1=north 1=east 3=south 4=west','']:
            self.assertIsNone(literal_map(n))
