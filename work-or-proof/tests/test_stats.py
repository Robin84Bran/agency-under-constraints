import random
import unittest
from wop_stats import bootstrap_draw, interval, primary_order, replay_sample, shuffled


def data():
    return [dict(id=f'{s}/{seed}/{actor}/{n}',source=s,seed=seed,actor=actor,breach=n==0,
                 _trace_cost=10,_trace_verdict=n==0,_trace_valid=True)
            for s in ['HA','Rebel'] for seed in [1,2] for actor in ['a','b','c'] for n in [0,1]]


class StatsTests(unittest.TestCase):
    def test_shared_order_deterministic(self):
        self.assertEqual(shuffled(data(),46000),shuffled(list(reversed(data())),46000))

    def test_duplicate_blocks_get_distinct_ids(self):
        class AlwaysFirst:
            def choice(self,keys): return keys[0]
        sample,draws=bootstrap_draw(data(),AlwaysFirst())
        self.assertEqual(len(sample),len({x['id'] for x in sample}))
        self.assertEqual(len(sample),len(data()))
        self.assertLess(len({x['original_id'] for x in sample}),len(sample))

    def test_unequal_block_weights_rejected(self):
        population=data()[:-1]
        class AlwaysFirst:
            def choice(self,keys): return keys[0]
        with self.assertRaises(ValueError): bootstrap_draw(population,AlwaysFirst())

    def test_percentile_interpolation(self):
        self.assertEqual(interval([0,100]),[2.5,97.5])

    def test_replay_sample_24_distinct_stratified_calls(self):
        sample=replay_sample(data())
        self.assertEqual(len(sample),24)
        self.assertEqual(len({(x['id'],x['view']) for x in sample}),24)
        altered=[dict(x,breach=not x['breach']) for x in data()]
        self.assertEqual(sample,replay_sample(altered))

    def test_bootstrap_uses_original_response_for_duplicates(self):
        class AlwaysFirst:
            def choice(self,keys): return keys[0]
        population=data()
        sample,_=bootstrap_draw(population,AlwaysFirst())
        local={x['id']:dict(verdict=x['breach'],valid=True) for x in population}
        score=primary_order(sample,local,cap=100000)
        self.assertEqual(score['LT_TP'],sum(x['breach'] for x in sample))
        self.assertEqual(score['X_TP'],score['LT_TP'])

    def test_fast_primary_no_provisional_catches(self):
        population=data()
        local={x['id']:dict(verdict=True,valid=True) for x in population}
        score=primary_order(population,local,cap=0)
        self.assertEqual(score['LT_TP'],0)
        self.assertEqual(score['LT_audited'],len(population))

    def test_fast_primary_agrees_with_full_replay(self):
        from wop_policy import replay
        from tests.test_policy import item, record
        population=[item(str(i),breach=i%2==0,trace=i%3==0,tokens=1000) for i in range(8)]
        local={}
        compiled={}
        for i,row in enumerate(population):
            row['_trace_cost']=1000
            row['_trace_verdict']=row['trace']['verdict']
            row['_trace_valid']=True
            value=[False,True,None][i%3]
            local[(row['id'],'trace')]=record(value)
            compiled[row['id']]=dict(verdict=value,valid=True)
        for seed in range(5):
            order=shuffled(population,seed)
            fast=primary_order(order,compiled,cap=3000)
            for policy in ['LT','X']:
                full=replay(order,policy,3000,local=local)
                self.assertEqual(fast[policy+'_TP'],full['counts']['TP'])
                self.assertEqual(fast[policy+'_audited'],full['counts']['audited'])
