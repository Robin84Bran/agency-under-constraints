"""Saved real bytes plus controlled envelope variants; only fake dispatch."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from od_core import ROOT,MODEL,canonical,render,reserve,schedule,sha
from od_contract import controls
from od_io import Stop,read,save,Log,Ledger,ActiveTime,durable_stop
from od_transport import Fake,raw_record
from od_validation import validate,accounting,cost,ReplyFailure,envelope
from od_collect import collect
from od_analysis import replay
from od_usage import refusal,network_nonstart,nonstart,record_nonstart,episode_state,prefix_snapshot,verify_prefixes


class Saved(Fake):
    def __init__(self,r): super().__init__();self.r=r;self.requests=[]
    def generate(self,ep,req,work):
        self.calls.append(ep['id']);self.requests.append(copy.deepcopy(req));return copy.deepcopy(self.r)


class D2(unittest.TestCase):
    def jobs(self,n=2): return [e for e in schedule() if e['actor']=='claude'][:n]
    def bound(self): return reserve(render(self.jobs(1)[0]))
    def real(self): return read(ROOT/'fixtures/d2-real-claude-envelope.json')
    def raw(self,e,rc=0): return raw_record(canonical(e).encode(),returncode=rc)
    def test_real_saved_dns_decisive_bytes(self):
        r=read(ROOT/'fixtures/d2-saved-raw.json');e,p=envelope(r,'claude')
        self.assertEqual((r['returncode'],e['is_error'],e['api_error_status'],e['duration_api_ms'],e['total_cost_usd'],e['modelUsage']),(1,True,None,0,0,{}))
        self.assertEqual(e['usage']['output_tokens'],0);self.assertIn('ENOTFOUND',e['result'])
        self.assertIsNone(refusal(r));self.assertIsNotNone(network_nonstart(r));self.assertEqual(cost(accounting(r,'claude')),0)
        self.assertEqual((ROOT/'fixtures/d2-saved-raw.json').read_bytes(),(ROOT/'collection/episodes/claude-b84-d24-independent-rules/raw.json').read_bytes())
    def test_external_success_fixture_unchanged_and_schema_local(self):
        r=raw_record((ROOT/'fixtures/d2-real-claude-envelope.json').read_bytes());e=self.real()
        self.assertEqual(set(e['modelUsage']),{'claude-opus-5-5'})
        self.assertEqual((e['num_turns'],e['stop_reason'],e['usage']['output_tokens']),(2,'tool_use',199))
        self.assertEqual(cost(accounting(r,'claude')),16788)
        with self.assertRaises(ReplyFailure):validate(r,'claude',self.bound())
        e['structured_output']={'fleet':6}
        for stop in ('tool_use','end_turn','stop_sequence'):
            e['stop_reason']=stop
            self.assertTrue(validate(self.raw(e),'claude',self.bound())['schema_valid'])
    def test_max_tokens_error_at_real_configured_cap_continues_and_settles(self):
        e=self.real();cap=int(controls()['CLAUDE_CODE_MAX_OUTPUT_TOKENS']);self.assertEqual(cap,512)
        e.update(is_error=True,stop_reason='max_tokens',num_turns=1,subtype='success');e.pop('structured_output')
        e['usage']['output_tokens']=cap;e['modelUsage'][MODEL]['outputTokens']=cap
        self.assertLess(cap,self.bound()['output_tokens']) # reservation padding is not output cap
        for rc in (0,1):
            for attributed in (True,False):
                v=copy.deepcopy(e)
                if not attributed:v.pop('modelUsage')
                r=self.raw(v,rc)
                with self.assertRaisesRegex(ReplyFailure,'output-length'):validate(r,'claude',self.bound())
                self.assert_continues(r)
    def assert_continues(self,r):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';f=Saved(r);jobs=self.jobs()
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            self.assertEqual(len(f.calls),2);self.assertFalse((base/'STOP.json').exists())
            rows,ledger=replay(ROOT,base,True,jobs)
            self.assertTrue(all(x['choice_status']=='REPLY_FAILURE' for x in rows))
            self.assertEqual(ledger['spent_micro_usd'],2*cost(accounting(r,'claude')))
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            self.assertEqual(len(f.calls),2)
    def test_refusals_nonzero_usage_no_attribution_or_stop_reason(self):
        e=self.real();e.update(is_error=True,result='I cannot comply',subtype='error_during_execution',num_turns=0)
        for k in ('structured_output','modelUsage','stop_reason','permission_denials'):e.pop(k,None)
        self.assert_continues(self.raw(e,1))
        # Nonzero input alone is not an exact zero-use limit refusal.
        e=read(ROOT/'fixtures/usage-limit-envelope.json');e['usage']['input_tokens']=1
        self.assertIsNone(refusal(self.raw(e,1)));self.assert_continues(self.raw(e,1))
    def test_complete_generated_envelope_before_timeout_and_safety_refusal(self):
        e=self.real();e['structured_output']={'fleet':6}
        r=dict(self.raw(e),returncode=None,transport_error='timeout after complete output')
        self.assert_continues(r)
        e['safety_stops']=1;self.assert_continues(self.raw(e))
        e['safety_stops']=0;e['stop_reason']=None;e.pop('structured_output')
        self.assert_continues(self.raw(e))
    def test_payload_failures_with_real_metadata_are_episode_local(self):
        for payload in (None,[],{'fleet':True},{'extra':1}):
            e=self.real();e['structured_output']=payload;self.assert_continues(self.raw(e))
        e=self.real();e.pop('structured_output');self.assert_continues(self.raw(e))
    def test_limit_missing_or_zero_attribution_does_not_stop(self):
        e=read(ROOT/'fixtures/usage-limit-envelope.json')
        metadata=self.real()['modelUsage'][MODEL]
        for k in list(metadata):
            if 'Tokens' in k or k in ('webSearchRequests','costUSD'):metadata[k]=0
        for mode in ('absent','empty','metadata'):
            v=copy.deepcopy(e)
            if mode=='absent':v.pop('modelUsage')
            elif mode=='metadata':v['modelUsage']={MODEL:metadata}
            r=self.raw(v,1);self.assertIsNotNone(refusal(r))
            with tempfile.TemporaryDirectory() as d:
                base=Path(d)/'out';f=Saved(r)
                out=collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=self.jobs())
                self.assertEqual(out['kind'],'usage-limit pause');self.assertEqual(len(f.calls),1)
                self.assertFalse((base/'STOP.json').exists())
                rows,l=replay(ROOT,base,True,self.jobs());self.assertFalse(any(x['attempted'] for x in rows))
                self.assertEqual(l['spent_micro_usd'],0)
    def test_limit_generic_label_unknown_reset_and_complete_envelope_before_timeout(self):
        for message in ("You've hit your limit · resets 9:30pm (Asia/Hong_Kong)","You've hit your weekly limit · resets Nov 19 at 9pm (Asia/Hong_Kong)"):
            e=read(ROOT/'fixtures/usage-limit-envelope.json');e['result']=message
            for rc in (0,1,None):
                r=self.raw(e,rc)
                if rc is None:r['transport_error']='timeout after complete refusal'
                self.assertIsNotNone(refusal(r))
                with tempfile.TemporaryDirectory() as d:
                    base=Path(d)/'out';f=Saved(r);jobs=self.jobs()
                    out=collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
                    self.assertEqual(out['kind'],'usage-limit pause');self.assertFalse((base/'STOP.json').exists())
                    rows,l=replay(ROOT,base,True,jobs);self.assertEqual(l['operational_events']['usage_limit_refusals'],1)
                    if 'weekly' in message:
                        self.assertIsNone(out['pause']['reset_at'])
                        collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs);self.assertEqual(len(f.calls),1)
    def test_dns_nonstart_proof_rejects_uncertain_or_nonzero_variants(self):
        r=read(ROOT/'fixtures/d2-saved-raw.json');e=envelope(r,'claude')[0]
        edits=[lambda e:e.update(duration_api_ms=1),lambda e:e.update(total_cost_usd=0.0000001),lambda e:e.update(api_error_status=500),lambda e:e.update(terminal_reason='unknown'),lambda e:e.update(result='network timeout'),lambda e:e['usage'].update(output_tokens=1),lambda e:e['usage']['server_tool_use'].update(web_search_requests=1),lambda e:e.update(subagent_stats={'spawned':1}),lambda e:e.update(structured_output={'fleet':6})]
        for edit in edits:
            v=copy.deepcopy(e);edit(v);self.assertIsNone(network_nonstart(self.raw(v,1)))
        for v in (dict(r,returncode=None,transport_error='timeout'),raw_record(b'{',returncode=1)):
            self.assertIsNone(network_nonstart(v))
    def test_independent_identity_tools_accounting_still_fatal(self):
        edits=[lambda e:e.update(modelUsage={'other-model':e['modelUsage'][MODEL]}),lambda e:e.update(effort='high'),lambda e:e.update(subagent_stats={'spawned':1}),lambda e:e['usage']['server_tool_use'].update(web_fetch_requests=1),lambda e:e.pop('total_cost_usd'),lambda e:e.update(total_cost_usd=26),lambda e:e['modelUsage'][MODEL].update(outputTokens=1)]
        for edit in edits:
            e=self.real();e['is_error']=True;edit(e)
            with self.subTest(e=e),self.assertRaises(Stop):validate(self.raw(e,1),'claude',self.bound())
        with self.assertRaises(Stop):validate(raw_record(b'{',returncode=1),'claude',self.bound())
    def test_dns_restart_identical_request_no_resend_of_completed_episode(self):
        r=read(ROOT/'fixtures/d2-saved-raw.json')
        class Once(Fake):
            def __init__(self):super().__init__();self.requests=[]
            def generate(self,ep,req,work):
                self.requests.append(copy.deepcopy(req))
                if len(self.requests)==1:self.calls.append(ep['id']);return r
                return super().generate(ep,req,work)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';f=Once();jobs=self.jobs()
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            p=base/'episodes'/jobs[0]['id'];saved={q:q.read_bytes() for q in p.glob('*.json')}
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            rows,l=replay(ROOT,base,True,jobs)
            self.assertTrue(all(x['schema_valid'] for x in rows));self.assertEqual(l['operational_events']['verified_transport_nonstarts'],1)
            self.assertEqual(l['operational_events']['usage_limit_refusals'],0)
            self.assertEqual(f.requests[0],f.requests[1]);self.assertEqual(len(f.calls),3)
            for q,b in saved.items():self.assertEqual(q.read_bytes(),b)
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs);self.assertEqual(len(f.calls),3)
    def test_new_fatal_stop_never_reuses_historical_clearance(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);save(base/'STOP.json',{'reason':'original'})
            save(base/'envelope-stop-clearance.json',{'kind':'fixture'})
            durable_stop(base,'later identity failure')
            self.assertEqual(read(base/'STOP.json'),{'reason':'original'})
            self.assertEqual(read(base/'STOP-after-envelope-clearance.json')['reason'],'later identity failure')
            from od_d2 import clearance_valid
            self.assertFalse(clearance_valid(base))
    def test_scientific_contract_and_parent_hashes_preserved(self):
        from od_d2 import D2_CHANGED,PARENTS
        parent=read(ROOT/'freeze-d1-final.json')
        for name,h in parent['files'].items():
            p=ROOT/'deviations/d2/parent-d1-final'/name if name in D2_CHANGED else ROOT/name
            self.assertEqual(sha(p.read_bytes()),h,name)
        import ast
        old=ast.parse((ROOT/'deviations/d2/parent-d1-final/od_analysis.py').read_text());new=ast.parse((ROOT/'od_analysis.py').read_text())
        functions=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef) and n.name!='replay'}
        self.assertEqual(functions(old),functions(new))
    def test_real_saved_stop_clearance_attestation_resume_prefixes_and_later_stop(self):
        from od_d2 import clear_envelope_stop,clearance_valid,attest_d2,d2_gate
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'collection';jobs=self.jobs(1)
            collect(ROOT,'claude',fake_transport=Saved(read(ROOT/'fixtures/d2-saved-raw.json')),output=base,jobs_override=jobs)
            p=base/'episodes'/jobs[0]['id'];marker=read(p/'nonstart.json');(p/'nonstart.json').unlink()
            original=read(ROOT/'collection/episodes/claude-b84-d24-independent-rules/episode.json')
            original['finished_at']=marker['finished_at'];save(p/'episode.json',original)
            save(base/'STOP.json',{'reason':original['fatal']})
            save(root/'config/episodes.json',jobs)
            save(root/'evidence/d2-decision.json',{'disposition':'VERIFIED_TRANSPORT_NONSTART'})
            for name in ('push.json','push-event.json','d1-attestation.json'):save(base/name,read(ROOT/'collection'/name))
            saved={q:q.read_bytes() for q in base.rglob('*.json')}
            save(root/'evidence/d2-baseline.json',{'files':{q.relative_to(base).as_posix():sha(q.read_bytes()) for q in saved},'prefixes':prefix_snapshot(base)})
            save(root/'freeze-d2.json',{'files':{'evidence/d2-baseline.json':sha((root/'evidence/d2-baseline.json').read_bytes())},'created_at':'2026-01-01T00:00:00+00:00','parents':{}})
            h=sha((root/'freeze-d2.json').read_bytes())
            with patch('od_d2.verify_d2',return_value=h):
                c=clear_envelope_stop(root);self.assertEqual(clear_envelope_stop(root),c)
                self.assertTrue(clearance_valid(base));self.assertFalse(replay(ROOT,base,True,jobs)[0][0]['attempted'])
                with patch('od_provenance.parent_receipt_gate'),patch('od_analysis.replay',side_effect=lambda *args:replay(ROOT,base,True,jobs)):
                    a=attest_d2(root);self.assertEqual(attest_d2(root),a)
                d2_gate(root)
            for q,b in saved.items():self.assertEqual(q.read_bytes(),b)
            collect(ROOT,'claude',fake_transport=Fake(),output=base,jobs_override=jobs)
            rows,l=replay(ROOT,base,True,jobs);self.assertTrue(rows[0]['schema_valid'])
            self.assertTrue(clearance_valid(base));d2_gate(root)
            # Crash window: a new fatal terminal is durable before its STOP.
            later=episode_state(base,jobs[0]['id'])[0]/'episode.json';later_bytes=later.read_bytes()
            v=read(later);v['fatal']='fatal before STOP fsync';later.write_text(canonical(v))
            self.assertFalse(clearance_valid(base))
            with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=Fake(),output=base,jobs_override=jobs)
            later.write_bytes(later_bytes)
            data=(base/'ledger.jsonl').read_bytes();(base/'ledger.jsonl').write_bytes(data[:-1])
            with self.assertRaises(Stop):clearance_valid(base)
            (base/'ledger.jsonl').write_bytes(data)
            durable_stop(base,'later fatal');self.assertFalse(clearance_valid(base))
            with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=Fake(),output=base,jobs_override=jobs)
    def test_d2_freeze_create_once_scope_and_parent_binding(self):
        from od_d2 import freeze_d2,verify_d2,PARENTS
        from od_freeze import inputs
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for n in inputs(ROOT)+list(PARENTS):
                p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
            with patch('od_d2.verify_baseline'):
                h=freeze_d2(root);self.assertEqual(verify_d2(root),h)
                with self.assertRaises(FileExistsError):freeze_d2(root)
            p=root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
            f=read(root/'freeze-d2.json');f['files']['config/prompts.json']=sha(p.read_bytes())
            (root/'freeze-d2.json').write_text(canonical(f))
            with self.assertRaisesRegex(Stop,'forbidden science'):verify_d2(root)
            (root/'freeze-d1-final.json').write_bytes((root/'freeze-d1-final.json').read_bytes()+b' ')
            with self.assertRaisesRegex(Stop,'parent freeze'):verify_d2(root)
