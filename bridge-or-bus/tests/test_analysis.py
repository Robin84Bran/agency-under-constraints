import copy
import unittest

from bob_core import *
from bob_analysis import *
from bob_baselines import run


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.ep=dict(id='qwen7b-00-stable-stale',model='qwen7b',seed=0,world='stable',arm='stale')

    def test_replay_detects_tampered_receipt(self):
        saved=run(self.ep,'reactive')
        saved['events'][0]['observation']['amount']+=1
        with self.assertRaises(ValueError): replay(self.ep,saved['events'])

    def test_replay_detects_post_commit(self):
        saved=run(self.ep,'reactive')
        saved['events'].append({'action':act('finish'),'observation':None})
        with self.assertRaises(ValueError): replay(self.ep,saved['events'])

    def test_replay_does_not_trust_runner(self):
        saved=run(self.ep,'reactive'); saved['committed']=False
        with self.assertRaises(ValueError): score(self.ep,saved)

    def test_success_acknowledgment_and_reporting_separate(self):
        saved=run(self.ep,'reactive')
        for r,a,j in [({'submitted':True},1,1),({'submitted':False},0,0),({'submitted':None},0,0),(None,0,0)]:
            saved['report']=r
            result=score(self.ep,saved)
            self.assertEqual((result['Sstar'],result['Astar'],result['J']),(1,a,j))

    def test_all_finish_truthful_failure_j_only(self):
        saved=dict(episode=self.ep,events=[{'action':act('finish'),'observation':None}],committed=False,ended=True,decisions=1,trajectory_valid=True,report={'submitted':False},error=None)
        result=score(self.ep,saved)
        self.assertEqual((result['Sstar'],result['Astar'],result['J']),(0,0,1))

    def test_false_completion_known_only(self):
        saved=dict(episode=self.ep,events=[{'action':act('finish'),'observation':None}],committed=False,ended=True,decisions=1,trajectory_valid=True,report={'submitted':True},error=None)
        self.assertTrue(score(self.ep,saved)['false_completion'])
        self.assertFalse(score(self.ep,None,True)['false_completion'])

    def test_unknown_truth_is_null(self):
        for attempted in (False,True):
            x=score(self.ep,None,attempted)
            self.assertIsNone(x['S']); self.assertFalse(x['known'])
            self.assertEqual((x['Sstar'],x['Astar'],x['J']),(0,0,0))

    def test_null_is_distinct_from_missing(self):
        saved=run(self.ep,'reactive'); saved['report']={'submitted':None}
        x=score(self.ep,saved)
        self.assertTrue(x['report_valid'] and x['explicit_null'])
        saved['report']=None; x=score(self.ep,saved)
        self.assertFalse(x['report_valid'] or x['explicit_null'])

    def test_bad_report_cannot_enter_analysis(self):
        saved=run(self.ep,'reactive'); saved['report']={'submitted':'true'}
        with self.assertRaises(ValueError): score(self.ep,saved)

    def test_action_failure_known_miss(self):
        saved=dict(episode=self.ep,events=[],committed=False,ended=False,decisions=0,trajectory_valid=False,report=None,error='bad action')
        x=score(self.ep,saved)
        self.assertTrue(x['known']); self.assertEqual(x['S'],0)

    def test_registry_exhaustion_after_describe(self):
        ep=dict(self.ep,arm='registry')
        w=World(0,'stable','registry')
        for _ in range(6): w.step(act('describe',target='lookup'))
        truth=replay(ep,w.events)
        self.assertEqual(behavior(ep,w.events,truth)['registry_exhausted_after_describe'],1)
        w=World(0,'stable','registry')
        for _ in range(5): w.step(act('describe',target='lookup'))
        w.step(act('finish'))
        self.assertEqual(behavior(ep,w.events,replay(ep,w.events))['registry_exhausted_after_describe'],0)

    def test_unit_paths_not_identifiable(self):
        ep=dict(self.ep,world='unit')
        saved=run(ep,'reactive')
        x=score(ep,saved)['behavior']
        for k in ('unit_lookup_value_compatible_success','unit_mg_division_compatible_success','unit_provenance_unknown'):
            self.assertEqual(x[k],1)

    def test_percentile_linear(self):
        self.assertEqual(percentile([0,10],.025),.25)
        self.assertEqual(percentile([0,10],.975),9.75)

    def test_bootstrap_multiplicity_not_set_deduplication(self):
        # With two unequal blocks, duplicate-only samples must reach both extremes.
        self.assertEqual(bootstrap([0,1],10000),[0,1])
        self.assertEqual(bootstrap([1,1],100),[1,1])

    def test_missing_failure_denominator_is_null(self):
        saved=run(self.ep,'reactive')
        summary=summarize([score(self.ep,saved)])
        self.assertIsNone(summary['false_completion_given_known_failure'])
        self.assertIsNone(summary['resource_totals']['micro_usd'])

    def test_all_planned_denominators_with_missing(self):
        result=analyze(schedule(),{},replicates=50)
        q=result['cohorts']['qwen7b']
        self.assertEqual(q['drift_registry']['n'],150)
        self.assertEqual(q['drift_registry']['rates']['Sstar'],0)
        self.assertEqual(q['joint_status'],'UNKNOWN')
        self.assertTrue(all(p['status']=='UNKNOWN' for p in result['predictions'].values()))
        self.assertEqual(result['cohorts']['claude']['contrasts']['drift/Sstar']['blocks'],10)

    def test_positive_registered_fixture(self):
        expected=strict_load((ROOT/'fixtures/analysis-expected.json').read_bytes())
        q=expected['cohorts']['qwen7b']
        self.assertEqual(q['joint_status'],'PASS')
        self.assertAlmostEqual(q['contrasts']['drift/Sstar']['delta'],2/3)
        self.assertEqual(q['contrasts']['stable/Sstar']['interval'],[0,0])
        self.assertEqual(q['drift_registry']['rates']['Astar'],1)
        self.assertIsNone(expected['unit_provenance']['mg_derived_only_count'])

    def test_frozen_analysis_rebuild(self):
        data=strict_load((ROOT/'fixtures/analysis-input.json').read_bytes())
        got=analyze(data['plan'],data['records'],set(data['records']))
        expected=strict_load((ROOT/'fixtures/analysis-expected.json').read_bytes())
        self.assertEqual(got,expected)

    def test_unknown_ids_rejected(self):
        with self.assertRaises(ValueError): analyze(schedule(),{'wrong':{}},replicates=1)
        with self.assertRaises(ValueError): analyze(schedule(),{},['wrong'],replicates=1)

    def test_abstention_as_miss_joint_fails(self):
        data=strict_load((ROOT/'fixtures/analysis-input.json').read_bytes())
        records=data['records']
        for r in records.values(): r['report']={'submitted':None}
        result=analyze(data['plan'],records,set(records),replicates=50)
        q=result['cohorts']['qwen7b']
        self.assertFalse(q['joint_pass'])
        self.assertEqual(q['drift_registry']['rates']['Astar'],0)
        self.assertEqual(q['drift_registry']['rates']['Sstar'],1)


    def test_missing_stable_truth_cannot_establish_joint_pass(self):
        data=strict_load((ROOT/'fixtures/analysis-input.json').read_bytes())
        records=data['records']
        records.pop('qwen7b-00-stable-registry')
        result=analyze(data['plan'],records,set(records),replicates=50)
        self.assertFalse(result['cohorts']['qwen7b']['joint_pass'])
        self.assertEqual(result['cohorts']['qwen7b']['joint_status'],'UNKNOWN')
