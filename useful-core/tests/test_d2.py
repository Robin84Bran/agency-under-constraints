"""D2 regression fixtures are verbatim saved bytes; all dispatches here are fake."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uc_core import ROOT,sha,transport_load,render,reserve,canonical,ModelOutputError
from uc_store import read,save,Ledger,ActiveTime,Stop,TransportFailure,EpisodeFailure
from uc_transport import decode,usage,cost_micro
from uc_analysis import classify_reply,audit_episode,audit_ledger
from uc_usage_limit import is_usage_limit,run_paid_episode
from uc_offline import Fake

FIX=ROOT/'deviations/d2/fixtures'
REAL=Path('<SCRATCH>/orchestra/real-claude-envelope.json')

class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.ep=read(FIX/'episode.json')['episode'];self.req=read(FIX/'2.request.json');self.bound=self.req['reservation']
        self.env=transport_load((FIX/'2.stdout').read_text());self.raw=read(FIX/'2.raw.json')

    def check(self,e,raw,expected):
        cost=cost_micro(*usage(e,'claude'),e)
        self.assertEqual(classify_reply(e,raw,self.ep,'action',self.bound,cost,True)[1],expected)
        exception={'transport':TransportFailure,'content':(EpisodeFailure,ModelOutputError),'fatal':Stop}.get(expected)
        if exception:
            with self.assertRaises(exception):decode(e,raw,self.ep,'action',self.bound,True)
        else:self.assertEqual(decode(e,raw,self.ep,'action',self.bound,True),e['structured_output'])

    def test_exact_stopping_bytes_are_transport_not_identity_or_limit(self):
        self.assertEqual(sha((FIX/'2.stdout').read_bytes()),self.raw['stdout_sha256'])
        self.assertEqual(self.env['modelUsage'],{});self.assertIsNone(self.env['api_error_status'])
        self.assertEqual(usage(self.env,'claude'),(0,0));self.assertEqual(self.env['total_cost_usd'],0)
        self.assertFalse(is_usage_limit(self.env,self.raw));self.check(self.env,self.raw,'transport')
        e=copy.deepcopy(self.env);e.pop('modelUsage');self.check(e,self.raw,'transport')

    def test_supplied_real_sibling_bytes_and_two_turn_success(self):
        raw=(FIX/'real-claude-envelope.json').read_bytes()
        if REAL.exists():self.assertEqual(raw,REAL.read_bytes())
        e=transport_load(raw.decode());self.assertEqual(usage(e,'claude'),(1602,199))
        self.assertEqual(e['num_turns'],2)
        # Preserve sibling payload; only its task-specific schema differs.
        with patch('uc_core.action',side_effect=lambda v:v):
            self.assertEqual(decode(e,{'returncode':0},self.ep,'action',self.bound),e['structured_output'])
        for reason in ('tool_use','end_turn'):
            env=copy.deepcopy(e);env.update(stop_reason=reason,structured_output=dict(op='read',ref=None,tier=None))
            self.check(env,{'returncode':0},None)

    def test_generated_error_shapes_do_not_stop_cohort(self):
        good=read(FIX/'real-claude-envelope.json')
        cases=[]
        for model_map in ('present','empty','absent'):
            for kind in ('cap','max_tokens','refusal','missing','invalid','exhausted'):
                e=copy.deepcopy(good);e['structured_output']=dict(op='read',ref=None,tier=None)
                if model_map=='empty':e['modelUsage']={}
                if model_map=='absent':e.pop('modelUsage')
                if kind=='cap':e.update(is_error=True);e['usage']['output_tokens']=512
                if kind=='max_tokens':e.update(is_error=True,stop_reason='max_tokens')
                if kind=='refusal':e.update(is_error=True,result='I cannot comply.',subtype='error_during_execution')
                if kind=='missing':e.pop('structured_output')
                if kind=='invalid':e['structured_output']={}
                if kind=='exhausted':e.update(is_error=True,subtype='error_max_structured_output_retries')
                cases.append((kind,model_map,e))
        for kind,model_map,e in cases:
            with self.subTest(kind=kind,model_map=model_map):self.check(e,{'returncode':1 if e['is_error'] else 0},'content')
        e=copy.deepcopy(good);e.update(is_error=True);e['usage']['output_tokens']=0
        self.check(e,{'returncode':1},'content') # refusal with non-zero input usage

    def test_limit_missing_model_usage_and_capacity_metadata(self):
        for mode in ('absent','empty','metadata'):
            e=read(ROOT/'fixtures/claude-usage-limit.json')
            if mode=='absent':e.pop('modelUsage',None)
            elif mode=='empty':e['modelUsage']={}
            else:e['modelUsage']={'claude-opus-5-5':dict(inputTokens=0,outputTokens=0,costUSD=0,maxOutputTokens=128000,contextWindow=1000000)}
            self.assertTrue(is_usage_limit(e,{'returncode':1}),mode)
        e['usage']['output_tokens']=1;self.assertFalse(is_usage_limit(e,{'returncode':1}))

    def test_integrity_and_genuine_uncertainty_stay_fatal(self):
        for changes in ({'modelUsage':{'wrong':{}}},{'effort':'high'},{'context_truncated':True}):
            e=copy.deepcopy(self.env);e.update(changes);self.check(e,self.raw,'fatal')
        self.assertEqual(classify_reply(None,{'transport_error':'ECONNRESET'},self.ep,'action',self.bound,None,True)[1],'fatal')
        e=read(FIX/'real-claude-envelope.json');e['structured_output']=dict(op='read',ref=None,tier=None)
        self.check(e,{'returncode':1},'content')
        self.check(e,{'returncode':None,'transport_error':'timeout'},'content')
        e['num_turns']=3;self.check(e,{'returncode':0},'content')
        with tempfile.TemporaryDirectory() as temp:
            b=Path(temp);f=Fake('claude','timeout')
            t=run_paid_episode(self.ep,f,b,Ledger(b/'ledger.jsonl'),ActiveTime(b/'time.jsonl',100000),'OFFLINE-FAKE',True)
            self.assertTrue(t['fatal']);self.assertEqual(f.calls,1)
            self.assertGreater(sum(Ledger(b/'ledger.jsonl').holds.values()),0)
            with self.assertRaises(Stop):run_paid_episode(self.ep,f,b,Ledger(b/'ledger.jsonl'),ActiveTime(b/'time.jsonl',100000),'OFFLINE-FAKE',True)
            self.assertEqual(f.calls,1)

    def test_generated_cap_error_is_charged_model_failure_and_next_episode_runs(self):
        class Cap(Fake):
            def generate(s,request,work):
                s.calls+=1;e=read(FIX/'real-claude-envelope.json')
                e.update(is_error=True,subtype='error_during_execution');e['usage']['output_tokens']=512
                e.pop('structured_output');e.pop('modelUsage')
                return dict(stdout=canonical(e).encode(),stderr=b'',returncode=1)
        with tempfile.TemporaryDirectory() as temp:
            b=Path(temp);f=Cap('claude');ledger=Ledger(b/'ledger.jsonl');timer=ActiveTime(b/'time.jsonl',100000)
            r=run_paid_episode(self.ep,f,b,ledger,timer,'OFFLINE-FAKE',True)
            self.assertEqual(r['failure_kind'],'content');self.assertFalse(r['fatal']);self.assertEqual(f.calls,1)
            self.assertFalse((b/'STOP.json').exists());self.assertEqual(read(b/'claude-contract.json')['status'],'MODEL_FAILURE')
            self.assertGreater(ledger.spent,0);self.assertEqual(ledger.holds[self.ep['id']],0)
            calls=audit_episode(b,self.ep,r,True);audit_ledger(b,[self.ep],calls)
            ep=dict(self.ep,id='after-model-failure')
            self.assertFalse(run_paid_episode(ep,Fake('claude'),b,ledger,timer,'OFFLINE-FAKE',True)['fatal'])

    def test_saved_bytes_mid_episode_settle_without_retry_then_next_episode(self):
        class Saved(Fake):
            def generate(s,request,work):
                if s.current[3]==2:
                    s.calls+=1
                    return dict(stdout=(FIX/'2.stdout').read_bytes(),stderr=b'',returncode=1)
                return super().generate(request,work)
        with tempfile.TemporaryDirectory() as temp:
            b=Path(temp);f=Saved('claude');ledger=Ledger(b/'ledger.jsonl');timer=ActiveTime(b/'time.jsonl',100000)
            result=run_paid_episode(self.ep,f,b,ledger,timer,'OFFLINE-FAKE',True)
            self.assertEqual(result['failure_kind'],'transport');self.assertFalse(result['fatal'])
            self.assertEqual(f.calls,2);self.assertEqual(len(result['events']),1)
            self.assertFalse((b/'STOP.json').exists());self.assertEqual(ledger.holds[self.ep['id']],0)
            calls=audit_episode(b,self.ep,result,True);audit_ledger(b,[self.ep],calls)
            with self.assertRaises(Stop):run_paid_episode(self.ep,f,b,ledger,timer,'OFFLINE-FAKE',True)
            self.assertEqual(f.calls,2)
            ep=dict(self.ep,id='next-episode');next_result=run_paid_episode(ep,Fake('claude'),b,ledger,timer,'OFFLINE-FAKE',True)
            self.assertFalse(next_result['fatal'])

class ClearanceTests(unittest.TestCase):
    def test_real_saved_boundary_clearance_lineage_and_offline_resume(self):
        import shutil
        from uc_freeze import inputs,push_gate
        from uc_d2 import seal,clear,attest,effective_read,stop_cleared,provenance,contract_freeze
        from uc_collect import collect
        from uc_usage_limit import prefixes,check_prefixes
        from uc_analysis import analyze
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'project';root.mkdir();base=root/'collection'
            for name in inputs(ROOT)+['freeze.json','freeze-a1.json','freeze-d1.json']:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            shutil.copytree(ROOT/'collection',base)
            # The canonical boundary may already be cleared on a subsequent test run.
            # Reconstruct it exclusively from the retained exact file inventory.
            inventory=read(root/'deviations/d2/collection-baseline.json')
            for path in sorted(base.rglob('*'),reverse=True):
                if path.is_file() and path.relative_to(base).as_posix() not in inventory['files']:path.unlink()
            for name,pin in inventory['files'].items():
                path=base/name
                if name.endswith('.jsonl'):path.write_bytes(path.read_bytes()[:pin['bytes']])
            stop_bytes=(base/'STOP.json').read_bytes();old_prefix=prefixes(base)
            digest=seal(root)
            with self.assertRaises(FileExistsError):seal(root)
            with self.assertRaises(FileNotFoundError):push_gate(root)
            self.assertFalse(stop_cleared(root,base,base/'STOP.json'))
            class ClearanceCrash(BaseException):pass
            original_event=Ledger.event
            def crash_release(ledger,**event):
                if event['event']=='release':raise ClearanceCrash()
                return original_event(ledger,**event)
            with patch.object(Ledger,'event',crash_release),self.assertRaises(ClearanceCrash):clear(root)
            self.assertFalse(stop_cleared(root,base,base/'STOP.json'))
            self.assertEqual(clear(root),digest);self.assertEqual(clear(root),digest) # completes crash without duplicate events
            self.assertEqual((base/'STOP.json').read_bytes(),stop_bytes)
            self.assertTrue(stop_cleared(root,base,base/'STOP.json'));check_prefixes(base,old_prefix)
            ledger=Ledger(base/'ledger.jsonl');self.assertFalse(ledger.blocked)
            plan=read(root/'deviations/d2/disposition-plan.json');episode=plan['episode']
            self.assertIn(episode,ledger.finished);self.assertEqual(ledger.holds[episode],0)
            terminal=base/'episodes'/episode/'episode.json'
            self.assertTrue(read(terminal)['fatal']);self.assertFalse(effective_read(base,terminal)['fatal'])
            self.assertEqual(attest(root),digest);self.assertEqual(push_gate(root),digest)
            with self.assertRaises(FileExistsError):attest(root)
            self.assertEqual(contract_freeze(base,digest),read(base/'claude-contract.json')['freeze_sha256'])
            result=analyze(root,base,base/'analysis-d2-test.json',replicates=1)
            self.assertFalse(result['accounting']['blocked']);self.assertEqual(result['accounting']['outstanding_holds_micro_usd'],0)
            self.assertTrue(result['stop_clearances']['STOP.json']['effective'])
            self.assertEqual(result['accounting']['ledger_events'],plan['ledger_events']+2)
            # Reach the next unstarted scheduled episode without invoking a model.
            class ReachedNext(BaseException):pass
            visited=[]
            def next_episode(ep,*args,**kwargs):visited.append(ep['id']);raise ReachedNext()
            class OfflineClaude:
                def __init__(self,*args):pass
                def preflight(self,*args):return read(base/'runtime/claude.json')
            with patch('uc_collect.Claude',OfflineClaude),patch('uc_usage_limit.run_paid_episode',side_effect=next_episode),self.assertRaises(ReachedNext):
                collect(root,'claude','UNUSED-OFFLINE-BINARY')
            self.assertEqual(len(visited),1);self.assertNotEqual(visited[0],episode)
            self.assertFalse((base/'episodes'/visited[0]/'1.start.json').exists())
            # Legitimate journal growth was accepted; changed prefix and other STOPs fail.
            self.assertEqual(push_gate(root),digest)
            save(base/'STOP-claude.json',dict(reason='unrelated stop'))
            with self.assertRaises(Stop):collect(root,'claude','UNUSED-OFFLINE-BINARY')
            p=base/'ledger.jsonl';original=p.read_bytes();p.write_bytes(original[:-1])
            with self.assertRaises(Stop):push_gate(root)
            p.write_bytes(original)
            clearance=base/'d2-clearance.json';r=read(clearance);r['stop_sha256']='0'*64;clearance.write_text(canonical(r))
            with self.assertRaises(Stop):stop_cleared(root,base,base/'STOP.json')

if __name__=='__main__':unittest.main()
