from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_core import *
from trl_io import Stop, read, save
from trl_budget import Ledger, ActiveTime
from trl_transport import Fake
from trl_collect import episode, readiness, collect
from trl_analysis import score, replay, paired, percentile, summarize


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.ledger=Ledger(self.base/'cost.jsonl')
        self.timer=ActiveTime(self.base/'time.jsonl',43200);self.timer.begin('fixture')

    def ep(self,actor='qwen7b',regime='shared'):
        return {'actor':actor,'seed':0,'regime':regime,'id':f'{actor}-s000-{regime}'}

    def run_ep(self,transport,actor='qwen7b',regime='shared'):
        ep=self.ep(actor,regime)
        return episode(ep,transport,self.base,self.ledger,self.timer,'FAKE')

    def test_full_shared_replays(self):
        v=self.run_ep(Fake());self.assertEqual(v['attempted_calls'],12)
        r=replay(self.ep(),self.base/'episodes'/self.ep()['id'])
        self.assertTrue(r['complete']);self.assertEqual(r['coverage'],1)

    def test_worker_calls_same_round_snapshot(self):
        f=Fake();self.run_ep(f)
        prompts=[strict_load(q['prompt'].split('\n')[-1]) for q in f.calls]
        self.assertTrue(all(p['receipts']==[] for p in prompts[:3]))
        self.assertTrue(all(len(p['receipts'])==3 for p in prompts[3:6]))
        self.assertEqual(prompts[3]['receipts'],prompts[5]['receipts'])

    def test_private_round_snapshot(self):
        f=Fake();self.run_ep(f,regime='private')
        for req in f.calls:
            p=strict_load(req['prompt'].split('\n')[-1])
            self.assertTrue(all(x[1]==p['role'] and x[0]<p['round'] for x in p['receipts']))

    def test_central_four_calls(self):
        r=self.run_ep(Fake(),regime='central')
        self.assertEqual(r['attempted_calls'],4);self.assertEqual(len(r['events']),12)

    def test_all_null_scores_zero(self):
        r=self.run_ep(Fake('null'))
        m=score(0,'shared',r['events'],r['complete'],True)
        self.assertEqual(m['Y'],0);self.assertEqual(m['H'],0)
        self.assertEqual(m['null_rate'],1);self.assertTrue(m['complete'])

    def test_malformed_worker_terminates_whole_episode(self):
        r=self.run_ep(Fake('malformed'))
        self.assertEqual(r['attempted_calls'],1)
        self.assertTrue(all(e['reward'] is None for e in r['events']))
        self.assertEqual(r['events'][0]['status'],'technical')
        m=replay(self.ep(),self.base/'episodes'/self.ep()['id'])
        self.assertEqual(m['Y'],0);self.assertEqual(m['technical_missing_rate'],1)

    def test_malformed_central_executes_nothing(self):
        r=self.run_ep(Fake('malformed'),regime='central')
        self.assertEqual(r['receipts'],[])
        self.assertTrue(all(e['status']=='technical' for e in r['events'][:3]))

    def test_frontier_fake_reconciles_holds(self):
        self.run_ep(Fake(),actor='claude')
        l=Ledger(self.base/'cost.jsonl')
        self.assertEqual(l.spent,12*1600);self.assertEqual(sum(l.holds.values()),0)
        r=replay(self.ep('claude'),self.base/'episodes'/self.ep('claude')['id'])
        self.assertTrue(r['complete'])

    def test_unknown_usage_stops_paid_dispatch(self):
        with self.assertRaises(Stop):self.run_ep(Fake('usage'),actor='claude')
        l=Ledger(self.base/'cost.jsonl')
        self.assertTrue(l.stopped);self.assertGreater(sum(l.holds.values()),0)
        self.assertTrue((self.base/'STOP.json').exists())

    def test_actual_overrun_durable_stop(self):
        with self.assertRaises(Stop):self.run_ep(Fake('overrun'),actor='claude')
        l=Ledger(self.base/'cost.jsonl')
        self.assertEqual(l.spent,300*4+2048*20);self.assertTrue(l.stopped)

    def test_timeout_preserves_raw_no_resend(self):
        f=Fake('timeout')
        with self.assertRaises(Stop):self.run_ep(f,actor='claude')
        with self.assertRaises(Stop):self.run_ep(f,actor='claude')
        self.assertEqual(len(f.calls),1)

    def test_crash_before_start_never_resends(self):
        ep=self.ep();d=self.base/'episodes'/ep['id'];d.mkdir(parents=True)
        save(d/'r1-j1.request.json',{'phase':'prepared, not dispatched'})
        with self.assertRaises(Stop):self.run_ep(Fake())

    def test_crash_after_start_never_resends(self):
        ep=self.ep();d=self.base/'episodes'/ep['id'];d.mkdir(parents=True)
        save(d/'r1-j1.start.json',{'id':'uncertain'})
        with self.assertRaises(Stop):self.run_ep(Fake())

    def test_saved_prompt_tamper_detected(self):
        self.run_ep(Fake());ep=self.ep();d=self.base/'episodes'/ep['id']
        p=d/'r2-j1.request.json';s=p.read_text();p.write_text(s.replace('"prompt_sha256":"','"prompt_sha256":"bad'))
        with self.assertRaises(Stop):replay(ep,d)

    def test_no_push_gate_prevents_all_service_access(self):
        with patch('trl_collect.push_gate',side_effect=Stop('no attestation')),patch('trl_collect.Local',side_effect=AssertionError('no service access')):
            with self.assertRaises(Stop):collect(self.base,'local')

    def test_readiness_requires_d1_before_results(self):
        # A project without the reviewed active D1 remains blocked.
        with self.assertRaises(Stop):readiness(self.base)


class AnalysisTests(unittest.TestCase):
    def row(self,seed,regime,policy='all-null',complete=True,attempted=True):
        sim=baseline(seed,policy)
        r=score(seed,regime,sim.events,complete,attempted)
        r.update(episode={'actor':'qwen7b','seed':seed,'regime':regime},kind='MODEL',calls=12 if regime!='central' else 4,
                 input_tokens=0,output_tokens=0,cache_read_tokens=0,cache_creation_tokens=0,unknown_usage_calls=0,elapsed_seconds=0)
        return r

    def test_fixture_analysis_endpoints(self):
        for case in read(ROOT/'fixtures/analysis-cases.json'):
            r=score(case['seed'],case['regime'],case['events'],case['complete'],case['attempted'])
            self.assertEqual({k:r[k] for k in case['expected']},case['expected'])

    def test_factual_unobserved_reward_rejected(self):
        sim=baseline(0,'all-null');sim.events[0]['reward']=0
        with self.assertRaises(Stop):score(0,'shared',sim.events,True,True)

    def test_twelve_opportunity_denominators(self):
        sim=Simulator(0);sim.execute('central',{0:{'cells':[0,None,None]}});sim.terminate('test',[1,2,3])
        r=score(0,'central',sim.events,False,True)
        self.assertEqual(r['coverage'],1/12);self.assertEqual(r['null_rate'],2/12)
        self.assertEqual(r['technical_missing_rate'],9/12)
        self.assertEqual(r['Y'],sim.events[0]['reward']/12000)

    def test_percentile_linear_interpolation(self):
        self.assertEqual(percentile([0,10],.025),.25)
        self.assertEqual(percentile([0,10],.975),9.75)

    def test_seed_bootstrap_multiplicity(self):
        r=paired([0,1],[0,0])
        self.assertEqual(r['difference'],.5)
        self.assertEqual(r['ci95'],[0,1]) # set-deduped blocks would incorrectly give [.5,.5].
        self.assertEqual(r['n'],2)

    def test_all_null_cannot_pass_joint(self):
        rows=[self.row(s,r) for s in range(100) for r in REGIMES]
        summary=summarize(rows,replicates=50)
        q=summary['cohorts']['qwen7b']
        self.assertTrue(q['technical_guardrails']);self.assertEqual(q['joint_status'],'joint criterion not met')
        self.assertEqual(summary['predictions']['P1']['status'],'failed')

    def test_joint_positive_and_baseline_ratios(self):
        rows=[self.row(s,r,'oracle' if r=='shared' else 'all-null') for s in range(100) for r in REGIMES]
        q=summarize(rows,replicates=50)['cohorts']['qwen7b']
        self.assertEqual(q['joint_status'],'passes')
        for reg in REGIMES:
            self.assertEqual(set(q['Y_fraction_of_baselines'][reg]),{'greedy-shared','greedy-private'})

    def test_unequal_failure_cannot_rescue_primary(self):
        rows=[self.row(s,r,'oracle' if r=='shared' else 'all-null',complete=(r!='private' or s>=6)) for s in range(100) for r in REGIMES]
        q=summarize(rows,replicates=50)['cohorts']['qwen7b']
        self.assertGreater(q['shared_minus_private_Y']['ci95'][0],0)
        self.assertFalse(q['technical_guardrails']);self.assertEqual(q['joint_status'],'joint criterion not met')

    def test_all_attempted_guard(self):
        rows=[self.row(s,r,'oracle' if r=='shared' else 'all-null',attempted=s!=0) for s in range(100) for r in REGIMES]
        s=summarize(rows,replicates=50)
        self.assertFalse(s['cohorts']['qwen7b']['technical_guardrails'])
        self.assertEqual(s['predictions']['P1']['status'],'UNKNOWN')

    def test_stale_old_peak_rounds_and_best_observed(self):
        w=world(0);c=w['fields'][0].index(1000);sim=Simulator(0)
        for _ in range(4):sim.execute('central',{0:{'cells':[c,c,c]}})
        r=score(0,'central',sim.events,True,True)
        self.assertEqual(r['stale_true_old_peak'],{'round_3_queries':3,'round_4_queries':3,'rounds_with_queries':2,'last_round_after_relocation':2})
        self.assertEqual(r['stale_best_observed'],r['stale_true_old_peak'])

    def test_all_baseline_fixtures_replay(self):
        for b in read(ROOT/'fixtures/baselines.json'):
            self.assertEqual(b['events'],baseline(b['seed'],b['policy']).events)
        for b in read(ROOT/'fixtures/baselines.json'):
            if b['policy']=='oracle':self.assertEqual(b['score']['Y'],1)
            if b['policy']=='all-null':self.assertEqual(b['score']['Y'],0)

    def test_duplicate_or_missing_seed_rejected(self):
        with self.assertRaises(Stop):summarize([self.row(0,'shared')]*2+[self.row(0,'central'),self.row(0,'private')],10)

    def test_unstarted_population_stays_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep={'actor':'qwen7b','seed':0,'regime':'shared','id':'qwen7b-s000-shared'}
            r=replay(ep,Path(tmp)/ep['id'])
            self.assertFalse(r['attempted']);self.assertFalse(r['complete'])
            self.assertEqual(r['Y'],0);self.assertEqual(r['H'],0)
            self.assertEqual(r['technical_missing_rate'],1)
