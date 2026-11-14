"""D3 accounting regressions; real saved envelope, fake transports only."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from od_core import ROOT,MODEL,render,reserve,schedule,canonical,sha
from od_io import Stop,read,save,Ledger,durable_stop
from od_validation import accounting,cost,validate,ReplyFailure,envelope
from od_transport import Fake,raw_record
from od_collect import collect
from od_analysis import replay
from od_d3 import (budget_usage,verify_model_counters,measured_bound,dispatch_bound,
    cap_check,forecast,clearance_valid,clear_accounting_stop,attest_d3,d3_gate,
    verify_d3,freeze_d3,D3_CHANGED,PARENTS,baseline,verify_baseline)


class Saved(Fake):
    d3=True
    def __init__(self,raw):super().__init__();self.raw=raw;self.requests=[]
    def generate(self,ep,req,work):
        self.calls.append(ep['id']);self.requests.append(copy.deepcopy(req));return copy.deepcopy(self.raw)


class D3(unittest.TestCase):
    def jobs(self,n=2):return [e for e in schedule() if e['actor']=='claude'][:n]
    def saved(self):return read(ROOT/'fixtures/d3-saved-raw.json')
    def raw(self,e):return raw_record(canonical(e).encode())
    def test_saved_budget_exhaustion_exact_cost_cache_and_thinking(self):
        r=self.saved();e,_=envelope(r,'claude');u=accounting(r,'claude',d3=True)
        self.assertEqual((u['input'],u['cache_creation'],u['cache_read'],u['output']),(2,1480,0,512))
        m=e['modelUsage'][MODEL]
        self.assertEqual(m['thinkingTokens'],512);self.assertEqual(m['cacheCreationEphemeral1hInputTokens'],1480)
        self.assertEqual(cost(u),2*4+1480*8+512*20)
        self.assertEqual(cost(u),22088);self.assertEqual(cost(u)-21248,840)
        self.assertEqual(accounting(r,'claude')['output'],0)
        with self.assertRaisesRegex(ReplyFailure,'output-length'):validate(r,'claude',reserve(render(self.jobs(1)[0])),d3=True)
        self.assertNotIn('structured_output',e) # Never manufacture a scored choice.
        p=ROOT/'collection/episodes/claude-b71-d24-independent-rules/raw.json'
        self.assertEqual(p.read_bytes(),(ROOT/'fixtures/d3-saved-raw.json').read_bytes())
    def test_zero_aggregate_recovery_requires_exact_budget_cost_and_identity(self):
        e=envelope(self.saved(),'claude')[0]
        edits=[lambda e:e.update(terminal_reason='api_error'),lambda e:e.update(subtype='error_during_execution'),lambda e:e['modelUsage'][MODEL].update(costUSD=0),lambda e:e['modelUsage'][MODEL].update(canonicalModel='other'),lambda e:e['modelUsage'][MODEL].update(thinkingTokens=513),lambda e:e['modelUsage'][MODEL].update(cacheCreationEphemeral1hInputTokens=1479),lambda e:e['usage'].update(input_tokens=1)]
        for edit in edits:
            v=copy.deepcopy(e);edit(v);self.assertIsNone(budget_usage(v))
            with self.assertRaises(Stop):validate(self.raw(v),'claude',reserve(render(self.jobs(1)[0])),d3=True)
    def valid_expensive(self,usd=.03):
        ep=self.jobs(1)[0];b=reserve(render(ep));r=Fake().generate(ep,{},None);e=envelope(r,'claude')[0]
        e['total_cost_usd']=usd
        # Reported cost is used even when larger than the conservative token floor.
        e['modelUsage'][MODEL]['costUSD']=usd
        return self.raw(e)
    def test_valid_overrun_reply_retained_settled_resized_and_not_resent(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();f=Saved(self.valid_expensive())
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            self.assertEqual(len(f.calls),2);self.assertFalse((base/'STOP.json').exists())
            l=Ledger(base/'ledger.jsonl');self.assertEqual(l.spent,60000)
            self.assertEqual(list(l.reservations.values()),[reserve(render(jobs[0]))['micro_usd'],33000])
            first=base/'episodes'/jobs[0]['id'];self.assertTrue(read(first/'episode.json')['schema_valid']);self.assertIsNone(read(first/'episode.json')['fatal'])
            self.assertEqual(read(first/'accounting.json')['actual_micro_usd'],30000)
            rows,a=replay(ROOT,base,True,jobs);self.assertTrue(all(r['schema_valid'] for r in rows));self.assertEqual(a['spent_micro_usd'],60000)
            self.assertEqual(f.requests[1]['argv'][-1],'0.033000')
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs);self.assertEqual(len(f.calls),2)
            event=read(first/'accounting.json');(first/'accounting.json').write_text(canonical(dict(event,actual_micro_usd=0)))
            with self.assertRaisesRegex(Stop,'accounting event'):replay(ROOT,base,True,jobs)
    def test_real_budget_error_settles_and_continues_without_resending(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();f=Saved(self.saved())
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            rows,a=replay(ROOT,base,True,jobs)
            self.assertEqual(len(f.calls),2);self.assertEqual(a['spent_micro_usd'],44176)
            self.assertTrue(all(r['choice_status']=='REPLY_FAILURE' and r['usage']['output']==512 for r in rows))
            self.assertEqual(list(Ledger(base/'ledger.jsonl').reservations.values())[1],24297)
    def test_input_reservation_excess_keeps_valid_reply_and_resizes_tokens(self):
        e=envelope(self.valid_expensive(.02),'claude')[0]
        e['usage'].update(input_tokens=4000,cache_creation_input_tokens=0,cache_read_input_tokens=0)
        e['modelUsage'][MODEL].update(inputTokens=4000,cacheCreationInputTokens=0,cacheReadInputTokens=0)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();f=Saved(self.raw(e))
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            rows,_=replay(ROOT,base,True,jobs);self.assertTrue(all(r['schema_valid'] for r in rows))
            self.assertEqual(read(base/'episodes'/jobs[1]['id']/'request.json')['reservation']['input_tokens'],4416)
            event=read(base/'episodes'/jobs[0]['id']/'accounting.json')
            self.assertTrue(event['exceeded']['input']);self.assertFalse(event['exceeded']['cost'])
    def test_independent_integrity_failures_and_envelope_caps_still_stop(self):
        e=envelope(self.valid_expensive(),'claude')[0]
        for edit in (lambda e:e['modelUsage'][MODEL].update(outputTokens=999),lambda e:e.update(effort='high'),lambda e:e['usage']['server_tool_use'].update(web_search_requests=1),lambda e:e.pop('total_cost_usd')):
            v=copy.deepcopy(e);edit(v)
            with self.assertRaises(Stop):validate(self.raw(v),'claude',reserve(render(self.jobs(1)[0])),d3=True)
        self.assertEqual(cap_check(24000000),25000000)
        with self.assertRaises(Stop):cap_check(24000001)
        with patch('od_d3.FRONTIER',50000000):
            self.assertEqual(cap_check(38000000),39000000)
            with self.assertRaises(Stop):cap_check(38000001)
        # Cost failure does not erase the otherwise-valid reply.
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';f=Saved(self.valid_expensive(25));jobs=self.jobs()
            with self.assertRaises(Stop):collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            self.assertEqual(len(f.calls),1);self.assertEqual(Ledger(base/'ledger.jsonl').spent,25000000)
            rows,_=replay(ROOT,base,True,jobs);self.assertTrue(rows[0]['schema_valid']);self.assertFalse(rows[1]['attempted'])
    def test_measured_margin_rounding_and_no_lookahead(self):
        u=accounting(self.saved(),'claude',d3=True);b=measured_bound(render(self.jobs(1)[0]),[u])
        self.assertEqual(b['micro_usd'],24297);self.assertEqual(b['output_tokens'],576)
        self.assertEqual(b['input_tokens'],2432)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();f=Saved(self.valid_expensive())
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            self.assertEqual(dispatch_bound(base,render(jobs[0]),before=jobs[0]['id']),reserve(render(jobs[0])))
            self.assertEqual(dispatch_bound(base,render(jobs[1]),before=jobs[1]['id'])['micro_usd'],33000)
    def test_d3_nonstart_resumes_with_identical_request_and_no_resend(self):
        class Once(Fake):
            d3=True
            def __init__(self):super().__init__();self.requests=[]
            def generate(self,ep,req,work):
                self.requests.append(copy.deepcopy(req))
                if len(self.requests)==1:
                    self.calls.append(ep['id']);return read(ROOT/'fixtures/d2-saved-raw.json')
                return super().generate(ep,req,work)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'out';jobs=self.jobs();f=Once()
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs)
            rows,a=replay(ROOT,base,True,jobs)
            self.assertTrue(all(r['schema_valid'] for r in rows));self.assertEqual(f.requests[0],f.requests[1])
            self.assertEqual(len(f.calls),3);self.assertEqual(a['operational_events']['verified_transport_nonstarts'],1)
            collect(ROOT,'claude',fake_transport=f,output=base,jobs_override=jobs);self.assertEqual(len(f.calls),3)
    def test_parent_science_and_existing_records_preserved(self):
        parent=read(ROOT/'freeze-d2.json')
        for n,h in parent['files'].items():
            p=ROOT/'deviations/d3/parent-d2'/n if n in D3_CHANGED else ROOT/n
            self.assertEqual(sha(p.read_bytes()),h,n)
        verify_baseline(ROOT)
    def test_real_clearance_attestation_and_prefixes(self):
        # Exercise the real collection without dispatching any transport. Sealed
        # verification is done by the final standalone integration check too.
        if (ROOT/'freeze-d3.json').exists():verify_d3(ROOT)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'collection'
            # Source files are read from the real sealed root by verification;
            # collection evidence is copied and can be damaged safely here.
            base.mkdir()
            # Copy the saved frontier cohort only; verify the full immutable
            # baseline separately without duplicating 3,600 local episodes.
            source=ROOT/'collection'
            for n in ('STOP.json','STOP-after-envelope-clearance.json','envelope-stop-clearance.json','push.json','push-event.json','d1-attestation.json','d2-attestation.json','ledger.jsonl','claude-time.jsonl'):
                shutil.copyfile(source/n,base/n)
            for n in ('ledger.jsonl.prefixes','claude-time.jsonl.prefixes','preflight/claude'):
                shutil.copytree(source/n,base/n)
            for q in (source/'episodes').glob('claude-*'):shutil.copytree(q,base/'episodes'/q.name)
            for name in ('config','evidence'):
                (root/name).mkdir()
            for n in ('freeze-d2.json','config/episodes.json','evidence/d3-baseline.json'):
                shutil.copyfile(ROOT/n,root/n)
            from od_usage import prefix_snapshot
            from od_io import now
            b=read(root/'evidence/d3-baseline.json')
            b['files']={p.relative_to(base).as_posix():sha(p.read_bytes()) for p in base.rglob('*.json') if '.jsonl.prefixes' not in str(p)}
            b['prefixes']=prefix_snapshot(base)
            (root/'evidence/d3-baseline.json').unlink();save(root/'evidence/d3-baseline.json',b)
            jobs=[e for e in read(root/'config/episodes.json') if e['actor']=='claude']
            (root/'config/episodes.json').unlink();save(root/'config/episodes.json',jobs)
            save(root/'freeze-d3.json',{'created_at':now(),'parents':{n:sha((ROOT/n).read_bytes()) for n in PARENTS},'files':{'evidence/d3-baseline.json':sha((root/'evidence/d3-baseline.json').read_bytes())}})
            before={p:p.read_bytes() for p in base.rglob('*.json')}
            from od_provenance import timestamp
            pushed=timestamp(read(ROOT/'collection/push.json')['pushed_at'])
            with patch('od_d3.verify_d3',return_value=sha((root/'freeze-d3.json').read_bytes())),patch('od_freeze.verify',return_value='SEALED-D3'),patch('od_provenance.parent_receipt_gate',return_value=pushed),patch('od_identity.verify_preflight'):
                c=clear_accounting_stop(root);self.assertEqual(clear_accounting_stop(root),c)
                self.assertTrue(clearance_valid(base));self.assertEqual(c['forecast']['total_micro_usd'],3563440)
                self.assertEqual(c['decoded']['status'],'REPLY_FAILURE');self.assertEqual(c['decoded']['usage']['output'],512)
                a=attest_d3(root);self.assertEqual(attest_d3(root),a);d3_gate(root)
                rows,account=replay(root,base)
                target=next(r for r in rows if r['id']=='claude-b71-d24-independent-rules')
                self.assertEqual(target['choice_status'],'REPLY_FAILURE');self.assertEqual(account['spent_micro_usd'],692571)
                data=(base/'ledger.jsonl').read_bytes();(base/'ledger.jsonl').write_bytes(data[:-1])
                with self.assertRaises(Stop):clearance_valid(base)
                (base/'ledger.jsonl').write_bytes(data)
                # Fatal terminal durable before its STOP must also invalidate.
                later=base/'episodes'/self.jobs(44)[43]['id']
                save(later/'episode.json',{'fatal':'later identity failure'})
                self.assertFalse(clearance_valid(base))
                shutil.rmtree(later)
                durable_stop(base,'later identity failure');self.assertFalse(clearance_valid(base))
                with self.assertRaises(Stop):clear_accounting_stop(root)
            for p,b in before.items():self.assertEqual(p.read_bytes(),b,str(p))
    def test_d3_freeze_parent_binding_scope_create_once(self):
        from od_freeze import inputs
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for n in inputs(ROOT)+list(PARENTS):
                p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
            with patch('od_d3.verify_baseline'),patch('od_d3.forecast'):
                h=freeze_d3(root);self.assertEqual(verify_d3(root),h)
                with self.assertRaises(FileExistsError):freeze_d3(root)
            p=root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
            f=read(root/'freeze-d3.json');f['files']['config/prompts.json']=sha(p.read_bytes());(root/'freeze-d3.json').write_text(canonical(f))
            with self.assertRaisesRegex(Stop,'science/evidence'):verify_d3(root)
            p=root/'freeze-d2.json';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(Stop,'parent freeze'):verify_d3(root)
