import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uc_core import *
from uc_transport import *
from uc_store import *
from uc_collect import run_episode
from uc_offline import Fake,dry_run
from uc_analysis import score,analyze,audit_episode,audit_ledger


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.ep=dict(id='fixture',actor='claude',seed=3,world='early',framing='fallback')
        self.prompt=render(self.ep,[],6,'action');self.bound=reserve(self.prompt,'action')

    def envelope(self,kind='normal',actor='claude'):
        ep=dict(self.ep,actor=actor);f=Fake(actor,kind);req=f.request(ep,self.prompt,'action',1,self.bound);raw=f.generate(req,ROOT);return strict_load(raw.pop('stdout').decode()),raw,ep

    def test_two_turn_and_one_turn_strict_payload(self):
        for kind in ('normal','one_turn'):
            e,r,ep=self.envelope(kind);self.assertEqual(decode(e,r,ep,'action',self.bound,True),dict(op='read',ref=None,tier=None))
            self.assertEqual(usage(e,'claude'),(215,20))
        e,r,ep=self.envelope();e['result']='{"op":"wait","ref":null,"tier":null}'
        self.assertEqual(decode(e,r,ep,'action',self.bound,True)['op'],'read')

    def test_paid_contract_failures(self):
        for kind in ('missing_cost','missing_usage','wrong_model','wrong_effort','tools','overrun'):
            e,r,ep=self.envelope(kind)
            with self.subTest(kind=kind),self.assertRaises(Stop):decode(e,r,ep,'action',self.bound,True)
        for turns in (True,1.0,0,3):
            e,r,ep=self.envelope();e['num_turns']=turns
            with self.assertRaises(ModelOutputError):decode(e,r,ep,'action',self.bound,True)
        e,r,ep=self.envelope();e['stop_reason']='end_turn'
        self.assertEqual(decode(e,r,ep,'action',self.bound,True)['op'],'read') # D2: valid two-turn end_turn

    def test_missing_payload_is_model_failure(self):
        for kind in ('missing_payload','string_payload'):
            e,r,ep=self.envelope(kind)
            with self.assertRaises(ModelOutputError):decode(e,r,ep,'action',self.bound,True)

    def test_local_incomplete_and_length_episode_only(self):
        for kind in ('missing_eval','not_done','length'):
            e,r,ep=self.envelope(kind,'qwen7b')
            with self.subTest(kind=kind),self.assertRaises(EpisodeFailure):decode(e,r,ep,'action',self.bound,True)
        for kind in ('wrong_model','overrun','input_loss'):
            e,r,ep=self.envelope(kind,'qwen7b')
            with self.subTest(kind=kind),self.assertRaises(Stop):decode(e,r,ep,'action',self.bound,True)
        e,r,ep=self.envelope('length','qwen7b');e['model']='wrong'
        with self.assertRaises(Stop):decode(e,r,ep,'action',self.bound,True)

    def test_local_running_context(self):
        e,r,ep=self.envelope('normal','qwen7b');tag,digest=PINS['qwen7b'];r['running']={'models':[dict(name=tag,digest=digest,context_length=8192)]}
        self.assertEqual(decode(e,r,ep,'action',self.bound)['op'],'read')
        r['running']['models'][0]['context_length']=4096
        with self.assertRaises(Stop):decode(e,r,ep,'action',self.bound)

    def test_real_template_system_chain_and_override(self):
        models=identities()
        for actor,item in models.items():
            show=dict(template=item['template'],system=item['system']);check_identity(actor,show)
            bad=dict(show,system='') if actor!='llama8b' else dict(show,system='injected')
            with self.assertRaises(Stop):check_identity(actor,bad)
            with self.assertRaises(Stop):check_identity(actor,dict(show,template='wrong'))
            ep=dict(self.ep,actor=actor);req=local_request(ep,self.prompt,'action',1)
            self.assertIs(req['stream'],False);self.assertEqual(req['system'],P['system']);self.assertEqual(req['options']['seed'],301)
            self.assertEqual(local_request(ep,self.prompt,'report',7)['options']['seed'],307)

    def test_command_isolation_and_cost(self):
        cmd=claude_command(BINARY,'action',20000)
        for flag in ('--json-schema','--output-format','--safe-mode','--tools','--setting-sources','--settings','--strict-mcp-config','--no-session-persistence'):self.assertIn(flag,cmd)
        self.assertEqual(cmd[cmd.index('--tools')+1],'');self.assertEqual(cmd[cmd.index('--max-turns')+1],'1')
        self.assertEqual(clean_env()['MAX_STRUCTURED_OUTPUT_RETRIES'],'0')
        self.assertEqual(cost_micro(100,10,dict(total_cost_usd=.0010001)),1001)
        self.assertEqual(cost_micro(100,10,dict(total_cost_usd=0)),600)
        for v in (None,True,-1,float('inf'),'0.01'):
            with self.assertRaises(Stop):cost_micro(1,1,dict(total_cost_usd=v))


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def test_reservation_settlement_and_resume(self):
        path=self.base/'ledger.jsonl';l=Ledger(path);l.event(event='reserve',id='e',amount=10000)
        l.event(event='settle',id='c',episode='e',reserved=2000,actual=1000)
        self.assertEqual(l.exposure,9000);self.assertEqual(Ledger(path).exposure,9000)
        l.event(event='release',id='e');self.assertEqual(l.exposure,1000)
        with self.assertRaises(Stop):l.event(event='reserve',id='e',amount=1)

    def test_rolling_gate_and_full_overrun(self):
        l=Ledger(self.base/'l.jsonl')
        with self.assertRaises(Stop):l.event(event='reserve',id='too-much',amount=23000001)
        l.event(event='reserve',id='first',amount=2000)
        l.event(event='settle',id='c',episode='first',reserved=1000,actual=45000000)
        self.assertEqual(l.spent,45000000);self.assertTrue(l.blocked)
        with self.assertRaises(Stop):l.event(event='release',id='first')
        with self.assertRaises(Stop):l.event(event='reserve',id='later',amount=1)
        self.assertTrue(Ledger(self.base/'l.jsonl').blocked)

    def test_prefix_tamper_and_truncation(self):
        p=self.base/'l.jsonl';l=Ledger(p);l.event(event='reserve',id='e',amount=1000);prefix=p.read_bytes();l.event(event='release',id='e')
        self.assertTrue(p.read_bytes().startswith(prefix))
        before=p.read_bytes();p.write_bytes(before.replace(b'1000',b'1001'))
        with self.assertRaises(Stop):Ledger(p)
        p.write_bytes(prefix)
        with self.assertRaises(Stop):Ledger(p)

    def test_append_race_and_partial_tail(self):
        p=self.base/'l.jsonl';a=Journal(p);b=Journal(p);a.append(dict(ok=True))
        with self.assertRaises(Stop):b.append(dict(ok=False))
        p.write_bytes(p.read_bytes()+b'{')
        with self.assertRaises(Stop):Journal(p)

    def test_crash_timer_full_timeout_retained(self):
        p=self.base/'t.jsonl';t=ActiveTime(p,500);t.begin('uncertain',430);restored=ActiveTime(p,500)
        self.assertGreaterEqual(restored.charged,430)
        with self.assertRaises(Stop):restored.begin('next',180)

    def test_lock_rejects_second_collector(self):
        with lock(self.base):
            with self.assertRaises(Stop):
                with lock(self.base):pass


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def run_case(self,kind='normal',actor='claude',world='early',ident='fixture'):
        ep=dict(id=ident,actor=actor,seed=0,world=world,framing='fallback')
        l=Ledger(self.base/'ledger.jsonl');t=ActiveTime(self.base/'time.jsonl',100000);f=Fake(actor,kind)
        r=run_episode(ep,f,self.base,l,t,'OFFLINE-FAKE',True)
        return ep,r,l,f

    def test_valid_first_contract_and_independent_audit(self):
        ep,r,l,f=self.run_case();self.assertEqual(read(self.base/'claude-contract.json')['status'],'PASS');self.assertEqual(f.calls,4)
        self.assertEqual(score(ep,r)['U'],2);self.assertEqual(l.exposure,l.spent)
        calls=audit_episode(self.base,ep,r,True);audit_ledger(self.base,[ep],calls)
        prefix=(self.base/'ledger.jsonl').read_bytes()
        self.run_case(ident='second');self.assertTrue((self.base/'ledger.jsonl').read_bytes().startswith(prefix))

    def test_first_content_failure_continues_without_probe(self):
        ep,r,l,f=self.run_case('invalid_action');self.assertFalse(r['fatal']);self.assertEqual(f.calls,1)
        self.assertEqual(read(self.base/'claude-contract.json')['status'],'MODEL_FAILURE');self.assertFalse((self.base/'STOP.json').exists());self.assertGreater(l.spent,0)
        with self.assertRaises(Stop):run_episode(ep,f,self.base,l,ActiveTime(self.base/'again-time.jsonl',1000),'OFFLINE-FAKE',True)

    def test_later_bad_reply_is_episode_failure(self):
        self.run_case();ep,r,l,f=self.run_case('invalid_action',ident='second');self.assertFalse(r['fatal']);self.assertEqual(f.calls,1);self.assertEqual(l.holds['second'],0)
        self.assertFalse((self.base/'STOP.json').exists())

    def test_unknown_paid_usage_holds_and_stops(self):
        ep,r,l,f=self.run_case('missing_usage');self.assertTrue(r['fatal']);self.assertEqual(l.spent,0);self.assertEqual(l.holds[ep['id']],episode_reservation(ep));self.assertEqual(f.calls,1)
        self.assertTrue(Ledger(self.base/'ledger.jsonl').blocked)

    def test_overrun_settled_in_full(self):
        ep,r,l,f=self.run_case('cost_overrun');self.assertEqual(l.spent,45000000);self.assertTrue(r['fatal']);self.assertEqual(f.calls,1)

    def test_local_transport_ends_episode_without_report(self):
        for kind in ('missing_eval','not_done','timeout','length','invalid_action','duplicate_action'):
            with self.subTest(kind=kind):
                ep,r,l,f=self.run_case(kind,'qwen7b',ident=kind);self.assertEqual(f.calls,1);self.assertFalse(r['fatal']);self.assertIsNone(r['report']);self.assertEqual(score(ep,r)['U'],0)

    def test_report_failure_preserves_delivery(self):
        ep,r,l,f=self.run_case('bad_report','qwen7b');row=score(ep,r);self.assertEqual(row['U'],2);self.assertEqual(row['Y'],1/6);self.assertEqual(row['H'],0);self.assertFalse(row['technically_complete'])
        audit_episode(self.base,ep,r,True)

    def test_report_null_valid_abstention(self):
        ep,r,l,f=self.run_case('null_report','qwen7b');row=score(ep,r);self.assertTrue(row['technically_complete']);self.assertTrue(row['null_report']);self.assertEqual(row['H'],0)

    def test_ambiguous_start_never_resends(self):
        ep=dict(id='ambiguous',actor='qwen7b',seed=0,world='early',framing='full');save(self.base/'episodes/ambiguous/1.start.json',dict(ambiguous=True))
        f=Fake('qwen7b')
        with self.assertRaises(Stop):run_episode(ep,f,self.base,Ledger(self.base/'ledger.jsonl'),ActiveTime(self.base/'time.jsonl',1000),'OFFLINE-FAKE',True)
        self.assertEqual(f.calls,0)

    def test_independent_audit_rejects_forged_failure(self):
        ep,r,l,f=self.run_case('normal','qwen7b')
        parsed=self.base/'episodes/fixture/1.parsed.json';record=read(parsed);record.update(value=None,error='invented failure')
        parsed.write_text(canonical(record)+'\n')
        with self.assertRaises(ValueError):audit_episode(self.base,ep,r,True)

    def test_crash_after_paid_start_retains_unknown_hold_in_analysis(self):
        from uc_analysis import audit_episode,audit_ledger
        ep=dict(id='crashed',actor='claude',seed=0,world='calm',framing='full')
        l=Ledger(self.base/'ledger.jsonl');l.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
        p=render(ep,[],6,'action');b=reserve(p,'action');stem=self.base/'episodes/crashed/1'
        save(str(stem)+'.request.json',dict(phase='action',prompt=p,prompt_sha256=sha(p.encode()),system=P['system'],schema=SCHEMAS['action'],reservation=b,outer=dict(stdin=p,argv=claude_command('FAKE-CLAUDE','action',b['micro_usd']),environment={})))
        save(str(stem)+'.start.json',dict(id='crashed-1',started_at=now(),freeze_sha256='OFFLINE-FAKE'))
        calls=audit_episode(self.base,ep,None,True);account=audit_ledger(self.base,[ep],calls)
        self.assertEqual(account['unknown_paid_usage_calls'],1);self.assertEqual(account['outstanding_holds_micro_usd'],episode_reservation(ep))

    def test_fatal_and_known_episode_failures_audit(self):
        for i,kind in enumerate(('missing_usage','missing_payload','cost_overrun','length','timeout')):
            with self.subTest(kind=kind):
                ep,r,l,f=self.run_case(kind,ident='failure-'+str(i));calls=audit_episode(self.base,ep,r,True);audit_ledger(self.base,[ep],calls)
                # Each fatal path is isolated for subsequent cases.
                self.tmp.cleanup();self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def test_crash_after_settlement_reconciles_cost_without_terminal(self):
        ep,r,l,f=self.run_case()
        terminal=self.base/'episodes/fixture/episode.json'
        # Simulate loss before terminal write by retaining only the first call,
        # its durable settlement and original prefixes in an isolated fixture.
        with tempfile.TemporaryDirectory() as scratch:
            import shutil
            base=Path(scratch);l2=Ledger(base/'ledger.jsonl');l2.event(event='reserve',id=ep['id'],amount=episode_reservation(ep))
            for src in (self.base/'episodes/fixture').glob('1.*'):
                dest=base/'episodes/fixture'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            start_path=base/'episodes/fixture/1.start.json';start=read(start_path);start['started_at']=now();start_path.write_text(canonical(start)+'\n')
            parsed=base/'episodes/fixture/1.parsed.json';c=read(parsed);parsed.unlink()
            l2.event(event='settle',id=ep['id']+'-1',episode=ep['id'],reserved=reserve(render(ep,[],6,'action'),'action')['micro_usd'],actual=c['actual_micro_usd'])
            calls=audit_episode(base,ep,None,True);account=audit_ledger(base,[ep],calls)
            self.assertEqual(account['settled_micro_usd'],c['actual_micro_usd']);self.assertGreater(account['outstanding_holds_micro_usd'],0)
            self.assertEqual(score(ep,None,True)['truth_status'],'UNKNOWN')

    def test_raw_unicode_bytes_preserved(self):
        class BytesFake(Fake):
            def generate(self,request,work):
                self.calls+=1;return dict(stdout=b'\xff\xfe',stderr=b'\x80',returncode=0)
        ep=dict(id='bad-unicode',actor='qwen7b',seed=0,world='early',framing='full');f=BytesFake('qwen7b')
        r=run_episode(ep,f,self.base,Ledger(self.base/'ledger.jsonl'),ActiveTime(self.base/'time.jsonl',1000),'OFFLINE-FAKE',True)
        self.assertTrue(r['fatal']);self.assertEqual((self.base/'episodes/bad-unicode/1.stdout').read_bytes(),b'\xff\xfe')

    def test_analysis_import_does_not_load_providers(self):
        import subprocess
        subprocess.check_call(['python3','-B','-c','import uc_analysis,sys; assert "uc_transport" not in sys.modules; assert "urllib.request" not in sys.modules'],cwd=ROOT)

    def test_collector_pauses_three_failures_and_persists_no_resend(self):
        from uc_collect import collect
        eps=[dict(id='qwen7b-'+str(i),actor='qwen7b',seed=i,world='early',framing='full') for i in range(5)]
        save(self.base/'config/episodes.json',eps)
        f=Fake('qwen7b','not_done');f.preflight=lambda actor:dict(offline=True)
        actual=run_episode
        def offline_run(ep,transport,base,ledger,timer,freeze_hash,**kwargs):
            return actual(ep,transport,base,ledger,timer,freeze_hash,fake=True,gate=kwargs['gate'])
        with patch('uc_freeze.push_gate',return_value='OFFLINE-FAKE'),patch('uc_collect.Local',return_value=f),patch('uc_collect.run_episode',side_effect=offline_run):
            with self.assertRaises(EpisodeFailure):collect(self.base,'local')
            self.assertEqual(f.calls,3);self.assertTrue((self.base/'collection/STOP-local.json').exists())
            with self.assertRaises(Stop):collect(self.base,'local')
            self.assertEqual(f.calls,3)

    def test_collector_frontier_requires_local_accounting(self):
        from uc_collect import collect
        save(self.base/'config/episodes.json',[dict(id='unstarted-local',actor='qwen7b',seed=0,world='calm',framing='full')])
        with patch('uc_freeze.push_gate',return_value='OFFLINE-FAKE'),self.assertRaises(Stop):collect(self.base,'claude',BINARY)

    def test_frontier_contract_retained_and_revalidated(self):
        from uc_collect import check_frontier_contract
        ep,r,l,f=self.run_case()
        check_frontier_contract(self.base,'OFFLINE-FAKE',[ep])
        p=self.base/'claude-contract.json';contract=read(p);p.unlink()
        with self.assertRaises(Stop):check_frontier_contract(self.base,'OFFLINE-FAKE',[ep])
        save(p,dict(contract,call='changed'))
        with self.assertRaises(Stop):check_frontier_contract(self.base,'OFFLINE-FAKE',[ep])

    def test_nonobject_envelope_fails_closed_with_evidence(self):
        class ArrayFake(Fake):
            def generate(self,request,work):
                self.calls+=1;return dict(stdout=b'[]',stderr=b'',returncode=0)
        for actor in ('qwen7b','claude'):
            ep=dict(id='array-'+actor,actor=actor,seed=0,world='early',framing='full');f=ArrayFake(actor)
            l=Ledger(self.base/'ledger.jsonl');r=run_episode(ep,f,self.base,l,ActiveTime(self.base/'time.jsonl',1000),'OFFLINE-FAKE',True)
            self.assertTrue(r['fatal']);audit_episode(self.base,ep,r,True)

    def test_partial_local_transport_bytes_are_episode_failure(self):
        class PartialFake(Fake):
            def generate(self,request,work):
                self.calls+=1;return dict(stdout=b'{"done":',stderr=b'connection closed',returncode=None,transport_error='incomplete HTTP read')
        ep=dict(id='partial',actor='qwen7b',seed=0,world='early',framing='full');f=PartialFake('qwen7b')
        r=run_episode(ep,f,self.base,Ledger(self.base/'ledger.jsonl'),ActiveTime(self.base/'time.jsonl',1000),'OFFLINE-FAKE',True)
        self.assertFalse(r['fatal']);self.assertEqual(f.calls,1);audit_episode(self.base,ep,r,True)
