import copy
import json
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from rg_core import *
from rg_collect import *
from rg_analysis import score, summarize, contrast, framing, analyze, replay, behavior, load_rows
from rg_stats import evaluate_sample, bootstrap_endpoints
from rg_offline import Fake, dry_run
from rg_freeze import prepare, freeze, verify, attest


def ep(actor='qwen7b',toolkit='plain',seed=0):
    return {'id':actor+'-'+toolkit+'-'+str(seed),'actor':actor,'toolkit':toolkit,'seed':seed,'receipt_loss':.5,'framing':'payment'}


def a(job=1,key=None,op='send'):
    return {'op':op,'job':job,'key':key}


def saved(world,episode,report_value=None,valid=True):
    return {'episode':episode,'events':world.events,'counts':world.counts,'decisions':world.decisions,
            'ended':world.ended,'trajectory_valid':valid,'report':report_value,'error':None,'attempted_calls':0}


class WorldTests(unittest.TestCase):
    def test_draw_vectors(self):
        vectors=read(ROOT/'fixtures/draw-vectors.json')['vectors']
        self.assertEqual(len(vectors),120)
        for v in vectors:
            self.assertEqual(draw(v['seed'],v['job'],v['attempt'],v['channel']),v['value'])

    def test_node_rebuild_vectors(self):
        js="import {draw} from './evidence/toy-model.mjs'; import fs from 'node:fs'; const vs=JSON.parse(fs.readFileSync('fixtures/draw-vectors.json')).vectors; if(vs.some(v=>draw(v.seed,v.job,v.attempt,v.channel)!==v.value))process.exit(1);"
        subprocess.run(['node','--input-type=module','-e',js],cwd=ROOT,check=True,capture_output=True)

    def test_request_receipt_unknown_equal(self):
        x=World(0,'plain',0,1);y=World(0,'plain',1,0)
        self.assertEqual(x.step(a()),y.step(a()))
        self.assertEqual(x.counts[0],0);self.assertEqual(y.counts[0],1)

    def test_no_loss_plain_duplicates(self):
        w=World(0,'plain',0,0);w.step(a());w.step(a())
        self.assertEqual(w.counts,[2,0,0,0])

    def test_keys_atomic(self):
        w=World(0,'keyed',0,0)
        self.assertEqual(w.step(a(key='x')),{'result':'ok'})
        self.assertEqual(w.step(a(key='x')),{'result':'ok'})
        self.assertEqual(w.counts[0],1)
        self.assertEqual(w.events[-1]['processed'],'suppressed')

    def test_conflict_no_effect(self):
        w=World(0,'keyed',0,0);w.step(a(key='X'))
        self.assertEqual(w.step(a(2,'X')),{'result':'conflict'})
        self.assertEqual(w.counts,[1,0,0,0])

    def test_conflict_receipt_lost(self):
        w=World(0,'keyed',1,0);w.step(a(key='x'))
        self.assertEqual(w.step(a(2,'x')),{'result':'unknown'})

    def test_suppression_receipt_lost(self):
        w=World(0,'keyed',1,0);w.step(a(key='x'));self.assertEqual(w.step(a(key='x')),{'result':'unknown'})
        self.assertEqual(w.counts[0],1)

    def test_lost_request_does_not_bind(self):
        w=World(0,'keyed',0,1);w.step(a(key='x'))
        self.assertEqual(w.keys,{})
        self.assertEqual(w.attempts,[1,0,0,0])

    def test_case_and_changed_keys(self):
        w=World(0,'keyed',0,0);w.step(a(key='x'));w.step(a(key='X'));w.step(a())
        self.assertEqual(w.counts[0],3)

    def test_status_draw_ordinal(self):
        w=World(0,'check',0,0);w.step(a(op='status'));w.step(a());w.step(a(op='status'));w.step(a())
        self.assertEqual(w.attempts[0],2)
        self.assertEqual(w.events[1]['attempt'],0);self.assertEqual(w.events[3]['attempt'],1)

    def test_status_no_count(self):
        w=World(0,'check',0,0);w.step(a());w.step(a())
        self.assertEqual(w.step(a(op='status')),{'result':'done'})

    def test_ten_decisions(self):
        w=World(0,'plain',0,0)
        for _ in range(10):w.step(a())
        self.assertTrue(w.ended)
        with self.assertRaises(ValueError):w.step(a())

    def test_finish_consumes_decision(self):
        w=World(0,'plain',0);w.step(a(None,op='finish'))
        self.assertEqual(w.decisions,1);self.assertEqual(w.history,[])
        with self.assertRaises(ValueError):w.step(a())

    def test_independent_replay_many(self):
        for toolkit in ('plain','keyed','check'):
            for seed in range(20):
                e=ep(toolkit=toolkit,seed=seed);w=World(seed,toolkit,.5)
                for i in range(10):
                    w.step(a(i%4+1,'k'+str(i%4) if toolkit=='keyed' else None,'status' if toolkit=='check' and i%3==0 else 'send'))
                self.assertEqual(replay(e,w.events)[0],w.counts)

    def test_replay_tamper(self):
        e=ep();w=World(0,'plain',.5);w.step(a());w.events[0]['processed']='invented'
        with self.assertRaises(ValueError):replay(e,w.events)

    def test_pairing(self):
        x=World(9,'plain',.5);y=World(9,'keyed',.5)
        for i in range(5):
            x.step(a());y.step(a(key='k'))
            self.assertEqual(x.events[-1]['request_lost'],y.events[-1]['request_lost'])
            self.assertEqual(x.events[-1]['receipt_lost'],y.events[-1]['receipt_lost'])


class ValidatorTests(unittest.TestCase):
    def test_bad_json(self):
        for raw in ['{"x":1,"x":2}','```json\n{}\n```','{}{}','before {}','{"x":NaN}','{"x":Infinity}','{"x":-Infinity}','{"x":1e999}']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):strict_load(raw)

    def test_whitespace_valid(self):
        self.assertEqual(report(strict_load(' \n {"all_done":true,"any_duplicate":null}\t')),{'all_done':True,'any_duplicate':None})

    def test_boolean_job(self):
        with self.assertRaises(ValueError):action(a(True),'plain')

    def test_invalid_actions(self):
        for v,t in [(a(0),'plain'),(a(5),'plain'),(a(1.0),'plain'),(a(key='k'),'plain'),(a(op='status'),'keyed'),(a(key='a'*17),'keyed'),(a(key='中文'),'keyed'),(a(key='a\n'),'keyed'),(a(key=''),'keyed'),(a(key=2),'keyed'),(a(1,op='finish'),'plain'),({'op':'finish','job':None},'plain')]:
            with self.subTest(v=v),self.assertRaises(ValueError):action(v,t)

    def test_report_no_coercion(self):
        for v in [[],{'all_done':1,'any_duplicate':False},{'all_done':'true','any_duplicate':False},{'all_done':None,'any_duplicate':None,'x':0},{}]:
            with self.subTest(v=v),self.assertRaises(ValueError):report(v)

    def test_valid_keys(self):
        for k in ['x','X','a_9-','x'*16,None]:self.assertEqual(action(a(key=k),'keyed')['key'],k)

    def test_renderer_information_boundary(self):
        e=ep();p=strict_load(render({**e,'hidden_secret':'bad','counts':[7]*4},[],10,'action'))
        self.assertEqual(set(p),{'instruction','task','tools','remaining','history'})
        for k in ('seed','actor','hidden_secret','counts','receipt_loss'):self.assertNotIn(k,p)

    def test_history_bound_all_depths(self):
        for t in ('plain','keyed','check'):
            for d in range(11):
                w=World(2,t,.5)
                for i in range(d):w.step(a(i%4+1,'X'*16 if t=='keyed' else None))
                for phase in ('action','report'):
                    self.assertLessEqual(len(render(ep(toolkit=t),w.history,10-d,phase)),len(render(ep(toolkit=t),maximal_history(d),10,phase)))

    def test_schema_and_bounds(self):
        self.assertEqual(len(P['system'].encode()),68)
        self.assertEqual(set(ACTION_SCHEMAS),{'plain','keyed','check'})
        self.assertEqual(len(canonical(SCHEMAS['report'])),184)
        self.assertEqual(len(canonical(maximal_history(1)[0])),93)
        self.assertEqual(reserve('x','action')['output_tokens'],576)

    def test_output_field_fail_closed(self):
        e=ep('claude');bound=reserve(render(e,[],10,'action'),'action')
        for kind in ['missing_payload','string_payload','wrong_model','wrong_effort','overrun','missing_usage']:
            raw=Fake(kind).generate(e,render(e,[],10,'action'),'action',10000,ROOT)
            with self.subTest(kind=kind),self.assertRaises(ValueError if kind in ('missing_payload','string_payload') else Stop):decode(raw,e,'action',bound,True)

    def test_result_prose_ignored(self):
        e=ep('claude');p=render(e,[],10,'action');raw=Fake().generate(e,p,'action',10000,ROOT)
        self.assertEqual(decode(raw,e,'action',reserve(p,'action'),True),a())

    def test_usage_missing_not_zero(self):
        self.assertEqual(usage({'usage':{'input_tokens':0,'output_tokens':0}},'claude'),(None,0))


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tests');self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def runfake(self,actor='qwen7b',kind='normal'):
        e=ep(actor);ledger=Ledger(self.base/'ledger.jsonl');timer=ActiveTime(self.base/'time.jsonl',10000)
        t=Fake(kind);out=run_episode(e,t,self.base,ledger,timer,'OFFLINE-FAKE',True)
        return out,t,ledger

    def test_end_to_end_harness(self):
        out,t,l=self.runfake();self.assertTrue(out['trajectory_valid']);self.assertEqual(t.calls,6)
        self.assertEqual(out['report'],{'all_done':None,'any_duplicate':None})

    def test_full_horizon_report_separate(self):
        class Ten(Fake):
            def generate(self,e,p,phase,budget,work):
                v=super().generate(e,p,phase,budget,work)
                if phase=='action':
                    x=strict_load(v['stdout']);x['response']=canonical(a());v['stdout']=canonical(x)
                return v
        e=ep();t=Ten();out=run_episode(e,t,self.base,Ledger(self.base/'ledger'),ActiveTime(self.base/'time',10000),'fake',True)
        self.assertEqual(t.calls,11);self.assertEqual(out['decisions'],10)

    def test_report_failure_keeps_trajectory(self):
        out,t,l=self.runfake(kind='bad_report');self.assertTrue(out['trajectory_valid']);self.assertIsNone(out['report'])
        self.assertEqual(t.calls,6)

    def test_invalid_action_no_effect(self):
        out,t,l=self.runfake(kind='invalid_action');self.assertEqual(out['counts'],[0]*4);self.assertEqual(t.calls,1)

    def test_paid_holds_release(self):
        out,t,l=self.runfake('claude');self.assertEqual(sum(l.holds.values()),0);self.assertEqual(l.spent,6*(200*4+20*20))
        self.assertEqual(Ledger(l.path).spent,l.spent)

    def test_missing_usage_holds_stop(self):
        out,t,l=self.runfake('claude','missing_usage');self.assertGreater(l.exposure,0);self.assertEqual(t.calls,1)
        self.assertTrue((self.base/'STOP.json').exists())

    def test_overrun_saved_not_clipped(self):
        out,t,l=self.runfake('claude','overrun');self.assertEqual(l.spent,100000*4+20*20)
        self.assertTrue((self.base/'STOP.json').exists());self.assertEqual(t.calls,1)

    def test_timeout_never_resend(self):
        out,t,l=self.runfake('claude','timeout');self.assertEqual(t.calls,1);self.assertEqual(l.spent,0)
        self.assertGreater(l.exposure,0)
        with self.assertRaises(Stop):run_episode(ep('claude'),t,self.base,l,ActiveTime(self.base/'t2',1000),'fake',True)

    def test_crash_after_start_blocks_resume(self):
        e=ep();directory=self.base/'episodes'/e['id'];save(directory/'0.start.json',{'started_at':now()})
        with self.assertRaises(Stop):run_episode(e,Fake(),self.base,Ledger(self.base/'l'),ActiveTime(self.base/'t',1000),'fake',True)

    def test_ledger_caps_and_duplicate(self):
        l=Ledger(self.base/'l');l.event(event='reserve',id='1',amount=24000000)
        with self.assertRaises(Stop):l.event(event='reserve',id='2',amount=1)
        with self.assertRaises(Stop):l.event(event='reserve',id='1',amount=0)
        self.assertEqual(Ledger(l.path).exposure,24000000)

    def test_torn_ledger(self):
        (self.base/'l').write_text('{')
        with self.assertRaises(ValueError):Ledger(self.base/'l')

    def test_concurrent_admission(self):
        with lock(self.base):
            with self.assertRaises(Stop):
                with lock(self.base):pass

    def test_time_crash_and_resume(self):
        t=ActiveTime(self.base/'t',500);t.begin('one',430)
        restored=ActiveTime(self.base/'t',500);self.assertEqual(restored.charged,430)
        with self.assertRaises(Stop):restored.begin('two',430)

    def test_local_truncation_ends_episode(self):
        out,t,l=self.runfake(kind='truncated');self.assertEqual(t.calls,1);self.assertFalse(out['trajectory_valid'])
        self.assertFalse((self.base/'STOP.json').exists())

    def test_cli_isolation(self):
        cmd=claude_command('claude','action',100000)
        for flag in ['--safe-mode','--restricted','--strict-mcp-config','--json-schema','--max-turns','--no-session-persistence']:self.assertIn(flag,cmd)
        self.assertEqual(cmd[cmd.index('--tools')+1],'')
        self.assertEqual(clean_env()['CLAUDE_CODE_MAX_OUTPUT_TOKENS'],'512')
        self.assertNotIn('ANTHROPIC_API_KEY',clean_env())


class AnalysisTests(unittest.TestCase):
    def test_missing_truth_not_zero(self):
        r=score(ep());self.assertIsNone(r['D']);self.assertEqual(r['Dstar'],1);self.assertEqual(r['Sstar'],0)
        self.assertEqual(summarize([r],100)['unknown_truth'],1)

    def test_never_send_null_cannot_pass(self):
        e=ep();w=World(0,'plain',.5);w.step(a(None,op='finish'))
        r=score(e,saved(w,e,{'all_done':None,'any_duplicate':None}),True)
        self.assertEqual(r['Sstar'],0);self.assertEqual(r['J'],0);self.assertEqual(r['D'],0)

    def test_duplicate_null_missing_recall_miss(self):
        # Choose a seed where the first two delivered sends create two effects.
        s=next(s for s in range(50) if draw(s,0,0,0)>=.2 and draw(s,0,1,0)>=.2)
        e=ep(seed=s);w=World(s,'plain',.5);w.step(a());w.step(a());w.step(a(None,op='finish'))
        for rep in [None,{'all_done':None,'any_duplicate':None}]:
            r=score(e,saved(w,e,rep),True);summary=summarize([r],100)
            self.assertEqual(summary['R'],0);self.assertEqual(summary['recall_denominator'],1)

    def test_action_failure_penalty_separate(self):
        e=ep();w=World(0,'plain',.5);r=score(e,saved(w,e,None,False),True)
        self.assertEqual(r['D'],0);self.assertEqual(r['Dstar'],1)

    def test_multiplicity(self):
        f=read(ROOT/'fixtures/analysis-cases.json')['cases']['multiplicity']
        self.assertEqual(evaluate_sample(f['terms'],[0,1],f['blocks']),f['estimate'])

    def test_interval_support(self):
        v=bootstrap_endpoints({'r': [[(1,1)]*9]},list(range(9)),100)['r']
        self.assertIsNone(v['interval'])

    def test_null_bootstrap_denominators(self):
        v=bootstrap_endpoints({'r':[[(1,1)]+[(0,0)]*19]},list(range(20)),100,minimum_blocks=1)['r']
        self.assertGreater(v['null_replicates'],0)

    def primary_rows(self,inaction=False,missing=False):
        rows=[]
        for seed in range(50):
            for f in ('payment','notification'):
                for t in ('plain','keyed','check'):
                    e={**ep(toolkit=t,seed=seed),'framing':f};r=score(e)
                    r.update(attempted=not missing,known=not missing,valid=not missing,D=(1 if t=='plain' else 0) if not missing else None,
                             Dstar=1 if t=='plain' or missing else 0,Sstar=0 if missing or inaction and t=='keyed' else 1)
                    rows.append(r)
        return rows

    def test_primary_positive_fixture(self):
        r=contrast(self.primary_rows(),'qwen7b',replicates=100)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['paired_scenarios'],100)
        self.assertEqual(r['difference_other_minus_plain']['Dstar'],-1)

    def test_safety_by_inaction_fails(self):
        r=contrast(self.primary_rows(inaction=True),'qwen7b',replicates=100)
        self.assertEqual(r['status'],'FAIL');self.assertFalse(r['gates']['completion_tolerance'])

    def test_missing_primary_unknown(self):
        r=contrast(self.primary_rows(missing=True),'qwen7b',replicates=100)
        self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['complete_pairs'],0)

    def test_primary_validity_gate(self):
        rows=self.primary_rows()
        for r in rows:
            if r['toolkit']=='keyed' and r['seed']<3:r['valid']=False
        out=contrast(rows,'qwen7b',replicates=100)
        self.assertEqual(out['status'],'FAIL');self.assertEqual(out['complete_pairs'],94)

    def test_framing_ties(self):
        rows=self.primary_rows();r=framing(rows,'qwen7b',100)
        self.assertEqual(r['difference_payment_minus_notification'],0)
        self.assertEqual(r['interval']['interval'],[0,0])

    def test_tool_use_opportunities(self):
        ev=[{'action':a(key='x'),'observation':{'result':'unknown'}},
            {'action':a(op='status'),'observation':{'result':'done'}},
            {'action':a(key='x'),'observation':{'result':'ok'},'processed':'suppressed'},
            {'action':a(key='y'),'observation':{'result':'ok'}}]
        b=behavior(ev);self.assertEqual(b['retries'],2);self.assertEqual(b['exact_original_key_reuse'],1)
        self.assertEqual(b['checked_done'],1);self.assertEqual(b['changed_keys'],1)

    def test_zero_opportunities_null(self):
        r=summarize([score(ep())],100);self.assertIsNone(r['original_key_reuse_rate'])


class RebuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tests');self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def test_full_saved_rebuild_and_cost_reconcile(self):
        from rg_analysis import reconcile
        dry_run(ROOT,self.base/'data')
        rows,maxima=load_rows(ROOT,self.base/'data')
        self.assertEqual(len(rows),1860);self.assertEqual(sum(r['attempted'] for r in rows),12)
        self.assertEqual(maxima['claude']['prompt_tokens'],200)
        costs=reconcile(ROOT,self.base/'data')
        self.assertEqual(costs['settled_micro_usd'],21600)
        self.assertEqual(costs['outstanding_micro_usd'],0)
        self.assertEqual(costs['status'],'RECONCILED')

    def test_rebuild_raw_tamper_rejected(self):
        dry_run(ROOT,self.base/'data')
        path=next((self.base/'data/episodes').glob('*/0.raw.json'))
        raw=read(path);env=strict_load(raw['stdout'])
        if 'response' in env:env['response']=canonical(a(4))
        else:env['structured_output']=a(4)
        raw['stdout']=canonical(env);path.write_text(canonical(raw))
        with self.assertRaises(ValueError):load_rows(ROOT,self.base/'data')

    def test_higher_reported_cost_not_ignored(self):
        self.assertEqual(cost_micro(200,20,{'total_cost_usd':.02}),20000)
        self.assertEqual(cost_micro(200,20,{'total_cost_usd':.00001}),1200)

    def test_independent_cost_tamper_rejected(self):
        from rg_analysis import reconcile
        dry_run(ROOT,self.base/'data')
        path=self.base/'data/ledger.jsonl';events=[strict_load(x) for x in path.read_text().splitlines()]
        next(e for e in events if e['event']=='settle')['actual']+=1
        path.write_text(''.join(canonical(e)+'\n' for e in events))
        with self.assertRaises(ValueError):reconcile(ROOT,self.base/'data')



class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tests');self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def test_counts_order_sizing(self):
        total=prepare(self.base);s=read(self.base/'config/episodes.json')
        self.assertEqual(len(s),1860);self.assertEqual(len({e['id'] for e in s}),1860)
        self.assertEqual(sum(e['actor']=='claude' for e in s),60)
        self.assertEqual(total,16145920);self.assertEqual(read(self.base/'config/sizing.json')['including_reserve_micro_usd'],17145920)
        self.assertEqual(len(read(self.base/'config/sizing.json')['measurements']),132)

    def test_freeze_tamper(self):
        prepare(self.base);freeze(self.base);verify(self.base)
        with (self.base/'config/design.json').open('a') as f:f.write(' ')
        with self.assertRaises(Stop):verify(self.base)

    def test_immutable_freeze(self):
        prepare(self.base);freeze(self.base)
        with self.assertRaises(FileExistsError):freeze(self.base)

    def test_push_gate_missing(self):
        prepare(self.base);freeze(self.base)
        with self.assertRaises(FileNotFoundError):push_gate(self.base)

    def test_attestation_wrong_event(self):
        prepare(self.base);freeze(self.base);save(self.base/'event.json',{'type':'PushEvent','payload':{'head':'bad'}})
        with self.assertRaises(Stop):attest(self.base,self.base/'event.json','x'*40,'receipt-gap')

    def test_push_future(self):
        prepare(self.base);h=freeze(self.base)
        save(self.base/'collection/push.json',{'freeze_sha256':h,'repo':'Robin84Bran/research','pushed_at':'2999-01-01T00:00:00Z'})
        with self.assertRaises(Stop):push_gate(self.base)

    def test_positive_attestation_and_retained_event(self):
        prepare(self.base);h=freeze(self.base)
        commit='a'*40
        event={'type':'PushEvent','repo':{'name':'Robin84Bran/research'},'payload':{'head':commit,'ref':'refs/heads/claude/receipt-gap-r2'},'created_at':'2026-01-01T00:00:00Z','id':'test-server-id'}
        event['created_at']=read(self.base/'freeze.json')['created_at']
        save(self.base/'event.json',event)
        def git(cmd,**kw):
            if cmd[1]=='rev-parse':return commit+'\n'
            if cmd[1]=='remote':return 'https://github.com/Robin84Bran/research.git\n'
            if cmd[1]=='show':return (self.base/cmd[2].split(':receipt-gap/',1)[1]).read_bytes()
            if cmd[1]=='ls-remote':return commit+'\trefs/heads/claude/receipt-gap-r2\n'
            raise AssertionError(cmd)
        with patch('rg_freeze.subprocess.check_output',side_effect=git):
            attest(self.base,self.base/'event.json',commit,'receipt-gap')
        self.assertEqual(push_gate(self.base),h)
        e=read(self.base/'collection/push-event.json');e['payload']['head']='b'*40
        (self.base/'collection/push-event.json').write_text(canonical(e))
        with self.assertRaises(Stop):push_gate(self.base)

    def test_offline_dryrun(self):
        out=dry_run(ROOT,self.base/'dry')
        self.assertEqual(out['episodes'],12);self.assertEqual(out['fake_calls'],72)
        self.assertEqual(out['real_model_calls'],0);self.assertEqual(out['outstanding_holds_micro_usd'],0)

if __name__=='__main__':unittest.main()
