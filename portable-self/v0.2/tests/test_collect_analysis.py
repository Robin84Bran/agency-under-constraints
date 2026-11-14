from pathlib import Path
import tempfile
import unittest
from ps_core import *
from ps_io import *
from ps_collect import collect
from ps_offline import Fake
from ps_analysis import score, bootstrap, primary, contrast, audit_accounting


def episode(actor='qwen7b',arm='keyed',seed=0,world='different-stable'):
    return {'actor':actor,'seed':seed,'world':world,'arm':arm,'id':f'{actor}-{seed:02d}-{world}-{arm}'}

class CollectAnalysisTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)/'fake'
    def tearDown(self): self.tmp.cleanup()
    def run_eps(self,eps,transport=None):
        cohort='claude' if eps[0]['actor']=='claude' else 'local'
        return collect(ROOT,cohort,fake_transport=transport or Fake(),output=self.base,episodes=eps)
    def mutate(self,index,**fields):
        def fn(raw,ep,i):
            if i==index:
                e=strict_load(raw['stdout']);e.update(fields);raw['stdout']=canonical(e)
            return raw
        return Fake(mutate=fn)
    def test_offline_keyed_replay_success(self):
        ep=episode();self.run_eps([ep]);s=score(ep,self.base,True)
        self.assertEqual((s['Y'],s['F']),(1,1));self.assertTrue(s['technical_complete'])
        self.assertEqual(s['calls_started'],8);self.assertEqual(s['known_wrong'],0)
        self.assertTrue(all(n['literal_fidelity'] for n in s['notes']))
        self.assertEqual(audit_accounting(self.base,[s])['exposure_micro_usd'],0)
    def test_stale_old_map_zero(self):
        ep=episode(world='stale-remap');self.run_eps([ep]);s=score(ep,self.base,True)
        self.assertEqual((s['Y'],s['F']),(0,0));self.assertEqual(s['known_wrong'],16)
    def test_null_is_valid_and_miss(self):
        ep=episode();self.run_eps([ep],Fake(mode='null'));s=score(ep,self.base,True)
        self.assertTrue(s['technical_complete']);self.assertEqual(s['nulls'],16);self.assertIsNone(s['answered_only_accuracy']);self.assertEqual(s['F'],0)
    def test_unstarted_unknown_truth_operational_zero(self):
        s=score(episode(),self.base,True)
        self.assertEqual(s['Y'],0);self.assertFalse(s['attempted']);self.assertEqual(s['technical_missing'],16)
        self.assertTrue(all(x['correct'] is None for x in s['facts']))
    def test_length_fails_only_episode_next_runs(self):
        a=episode();b=episode(seed=1)
        def mutate(raw,ep,i):
            if ep['seed']==0 and i==4:
                e=strict_load(raw['stdout']);e['done_reason']='length';raw['stdout']=canonical(e)
            return raw
        self.run_eps([a,b],Fake(mutate=mutate))
        self.assertEqual(score(a,self.base,True)['calls_started'],5);self.assertTrue(score(b,self.base,True)['technical_complete'])
        self.assertFalse((self.base/'STOP.json').exists())
    def test_done_false_and_missing_eval_episode(self):
        for change in [{'done':False},{'eval_count':None}]:
            with tempfile.TemporaryDirectory() as tmp:
                ep=episode();collect(ROOT,'local',fake_transport=self.mutate(0,**change),output=Path(tmp)/'fake',episodes=[ep])
                self.assertFalse((Path(tmp)/'fake/STOP.json').exists())
                self.assertEqual(score(ep,Path(tmp)/'fake',True)['calls_started'],1)
    def test_bad_batch_never_partially_executes(self):
        ep=episode();self.run_eps([ep],self.mutate(4,response='{"controls":[1,2,3]}'))
        s=score(ep,self.base,True);self.assertEqual(s['Y'],0);self.assertEqual(s['technical_missing'],16);self.assertEqual(s['known_wrong'],0)
    def test_identity_failure_fatal(self):
        with self.assertRaises(Stop): self.run_eps([episode()],self.mutate(0,model='wrong'))
        self.assertTrue((self.base/'STOP.json').exists())
    def test_first_frontier_content_failure_is_episode_local(self):
        ep=episode('claude')
        self.run_eps([ep],self.mutate(0,structured_output={'slot':1,'note':'x','extra':1}))
        self.assertFalse((self.base/'frontier-contract.json').exists());self.assertFalse(Ledger(self.base/'ledger.jsonl').blocked)
    def test_frontier_second_invalid_episode_local(self):
        ep=episode('claude');self.run_eps([ep],self.mutate(1,structured_output={'slot':True,'note':''}))
        s=score(ep,self.base,True);self.assertEqual(s['calls_started'],2);self.assertFalse((self.base/'STOP.json').exists())
        self.assertEqual(sum(Ledger(self.base/'ledger.jsonl').holds.values()),0)
    def test_frontier_first_good_sets_contract_and_accounts_cache(self):
        ep=episode('claude');self.run_eps([ep]);s=score(ep,self.base,True)
        self.assertTrue(read(self.base/'frontier-contract.json')['strict_valid_structured_output'])
        self.assertEqual(Ledger(self.base/'ledger.jsonl').spent,8*1020)
        self.assertEqual(audit_accounting(self.base,[s])['held_micro_usd'],0)
    def test_timeout_unknown_paid_hold_no_retry(self):
        class Timeout(Fake):
            def generate(self,request,work):
                self.calls+=1;return {'stdout':'','stderr':'','returncode':None,'transport_error':'timeout'}
        ep=episode('claude');fake=Timeout()
        with self.assertRaises(Stop): self.run_eps([ep],fake)
        self.assertEqual(fake.calls,1);self.assertEqual(Ledger(self.base/'ledger.jsonl').exposure,episode_reservation(ep))
        with self.assertRaises(Stop): self.run_eps([ep],fake)
        self.assertEqual(fake.calls,1)
    def test_overrun_actual_never_clipped(self):
        ep=episode('claude')
        with self.assertRaises(Stop): self.run_eps([ep],self.mutate(0,total_cost_usd=.9))
        ledger=Ledger(self.base/'ledger.jsonl');self.assertEqual(ledger.spent,900000);self.assertTrue(ledger.blocked)
        self.assertEqual(ledger.holds[ep['id']],episode_reservation(ep)-reservation('keyed','write')['micro_usd'])
    def test_crash_started_never_regenerates(self):
        ep=episode();directory=self.base/'episodes'/ep['id'];save(directory/'0.start.json',{'fake':'crash'})
        fake=Fake()
        with self.assertRaises(Stop): self.run_eps([ep],fake)
        self.assertEqual(fake.calls,0)
    def test_terminal_episode_never_replayed(self):
        ep=episode();fake=Fake();self.run_eps([ep],fake);self.assertEqual(fake.calls,8)
        self.run_eps([ep],fake);self.assertEqual(fake.calls,8)
    def test_replay_rejects_prompt_or_event_tamper(self):
        ep=episode();self.run_eps([ep]);path=self.base/'episodes'/ep['id']/'4.event.json'
        obj=read(path);obj['value']['controls']=[1]*4;path.write_text(canonical(obj))
        with self.assertRaises(Stop): score(ep,self.base,True)
    def test_replay_ignores_success_flags(self):
        ep=episode();self.run_eps([ep]);path=self.base/'episodes'/ep['id']/'episode.json'
        obj=read(path);obj['success']=False;obj['Y']=0;path.write_text(canonical(obj))
        self.assertEqual(score(ep,self.base,True)['Y'],1)
    def test_start_binds_ledger_prefix(self):
        ep=episode('claude');self.run_eps([ep]);s=score(ep,self.base,True)
        path=self.base/'episodes'/ep['id']/'0.start.json';obj=read(path);obj['ledger_prefix_sha256']='0'*64;path.write_text(canonical(obj))
        with self.assertRaises(Stop): audit_accounting(self.base,[s])

    def test_sealed_raw_bytes_cannot_change(self):
        ep=episode();self.run_eps([ep]);row=score(ep,self.base,True)
        path=self.base/'episodes'/ep['id']/'0.raw.json';raw=read(path);raw['stderr']='tampered';path.write_text(canonical(raw))
        with self.assertRaises(Stop): audit_accounting(self.base,[row])
    def test_sealed_inventory_cannot_gain_or_lose_files(self):
        ep=episode();self.run_eps([ep]);row=score(ep,self.base,True)
        (self.base/'episodes'/ep['id']/'injected.json').write_text('{}')
        with self.assertRaises(Stop): audit_accounting(self.base,[row])
    def test_frontier_contract_raw_hash_checked(self):
        ep=episode('claude');self.run_eps([ep]);row=score(ep,self.base,True)
        path=self.base/'frontier-contract.json';v=read(path);v['raw_sha256']='0'*64;path.write_text(canonical(v))
        with self.assertRaises(Stop): audit_accounting(self.base,[row])

class StatisticsTests(unittest.TestCase):
    def rows(self,y,f,valid=100,attempted=True):
        return [{'seed':s,'Y':y,'F':f,'technical_complete':s<valid,'attempted':attempted,'calls':[],'calls_started':8 if attempted else 0} for s in range(100)]
    def test_primary_positive_and_zero(self):
        self.assertEqual(primary(self.rows(1,1),self.rows(.5,.25))['status'],'met')
        self.assertEqual(primary(self.rows(1,1),self.rows(1,1))['status'],'failed')
    def test_null_missing_cannot_pass(self):
        self.assertEqual(primary(self.rows(0,0),self.rows(0,0))['status'],'failed')
        self.assertEqual(primary(self.rows(0,0,attempted=False),self.rows(0,0,attempted=False))['status'],'UNKNOWN')
    def test_validity_guard(self):
        self.assertEqual(primary(self.rows(1,1,valid=94),self.rows(.5,.25))['status'],'failed')
    def test_complete_pair_guard(self):
        a=self.rows(1,1,valid=95);b=self.rows(.5,.25)
        for row in b: row['technical_complete']=row['seed']>=5
        p=primary(a,b);self.assertEqual(p['complete_pair_sensitivity']['Y']['n'],90);self.assertEqual(p['status'],'failed')
    def test_complete_pair_cannot_be_rescued_by_failures(self):
        a=self.rows(.5,.25);b=self.rows(.5,.25)
        for i in range(5): b[i]['technical_complete']=False;b[i]['Y']=b[i]['F']=0
        self.assertEqual(primary(a,b)['status'],'failed')
    def test_bootstrap_preserves_duplicate_blocks(self):
        r=bootstrap([0,1],10000)
        self.assertEqual(r['mean'],.5);self.assertEqual(r['interval'],[0,1])
        # A set-based resampling bug would collapse duplicate 0/1 draws and return [.5,.5].
        self.assertEqual(r,bootstrap([0,1],10000))
    def test_percentile_linear_interpolation(self):
        from ps_analysis import percentile
        self.assertEqual(percentile([0,10,20,30],.25),7.5)
    def test_effect_contains_arm_token_usage(self):
        c=contrast(self.rows(1,1),self.rows(0,0));self.assertIn('prompt_tokens',c);self.assertIn('missing_usage',c['prompt_tokens']['left'])
