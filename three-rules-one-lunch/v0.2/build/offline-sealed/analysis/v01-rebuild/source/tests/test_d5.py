"""Saved-byte regression matrix and D5 clearance, lineage, and collector checks."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from trl_core import ROOT, canonical, sha, strict_load
from trl_io import Stop, read, save, now, timestamp
from trl_transport import Fake, raw_record
from trl_budget import ActiveTime, Ledger, maximum
from trl_validation import stdout, usage, cost
from trl_d4 import refusal, UsageLimitPause
from trl_d5 import (validate, ModelReplyFailure, episode, clearance, record_clearance,
    terminal_path, provenance_layers, prepush_gate, stop_gate, CLEARANCE, DISPOSITION, EPISODE, STOP_NAME)

CAP = read(ROOT/'fixtures/d5/r4-j0.raw.json')
SUCCESS = read(ROOT/'fixtures/d5/success.raw.json')
LIMIT = read(ROOT/'fixtures/d5/usage-limit.raw.json')


def altered(raw,updates,remove=(),returncode=None):
    env = strict_load(stdout(raw))
    env.update(updates)
    for key in remove:
        env.pop(key,None)
    return raw_record(canonical(env).encode(),returncode=raw['returncode'] if returncode is None else returncode)


class SavedFake(Fake):
    def __init__(self,raw,at=0):
        super().__init__();self.saved,self.at=raw,at
    def generate(self,actor,req,work):
        normal=super().generate(actor,req,work)
        return deepcopy(self.saved) if len(self.calls)-1==self.at else normal


class EnvelopeTests(unittest.TestCase):
    def test_real_bytes_are_exact_including_sibling_envelope(self):
        for n in ('raw','parsed','request','start'):
            self.assertEqual((ROOT/f'fixtures/d5/r4-j0.{n}.json').read_bytes(),
                (ROOT/f'collection/episodes/{EPISODE}/r4-j0.{n}.json').read_bytes())
        supplied=Path('<SCRATCH>/orchestra/real-claude-envelope.json')
        data=(ROOT/'fixtures/d5/real-claude-envelope.json').read_bytes()
        self.assertEqual(sha(data),'a4e9f03ce0cd4cbde843924c06880082baaee6e58597fcad0f970022a9c6eb2c')
        if supplied.exists():self.assertEqual(data,supplied.read_bytes())

    def test_saved_cap_is_generated_not_transport_or_overrun(self):
        e=strict_load(stdout(CAP))
        self.assertEqual((CAP['returncode'],e['is_error'],e['stop_reason']),(1,True,'max_tokens'))
        self.assertEqual(e['modelUsage']['claude-opus-5-5']['outputTokens'],1024)
        self.assertEqual(cost(usage(e,'claude')),28699)
        self.assertIsNone(refusal(CAP))
        with self.assertRaises(ModelReplyFailure):validate(CAP,'claude',3,maximum('central'))

    def test_saved_success_two_turns_and_end_turn_variant(self):
        self.assertEqual(validate(SUCCESS,'claude',3,maximum('central'))[0],{'cells':[10,22,36]})
        self.assertEqual(validate(altered(SUCCESS,{'stop_reason':'end_turn'}),'claude',3,maximum('central'))[0],{'cells':[10,22,36]})

    def test_sibling_payload_is_schema_failure_not_identity_failure(self):
        raw=raw_record((ROOT/'fixtures/d5/real-claude-envelope.json').read_bytes())
        with self.assertRaisesRegex(ModelReplyFailure,'schema-invalid'):validate(raw,'claude',1,maximum('private'))
        adapted=altered(raw,{'structured_output':{'cells':[9]}})
        self.assertEqual(validate(adapted,'claude',1,maximum('private'))[0],{'cells':[9]})

    def test_limit_missing_identity_or_optional_denials_is_still_nonstart(self):
        for rc in (0,1):
            for remove in ((),('modelUsage',),('permission_denials',),('modelUsage','permission_denials'),('modelUsage','api_error')):
                with self.subTest(rc=rc,remove=remove):
                    self.assertIsNotNone(refusal(altered(LIMIT,{},remove,rc)))
        self.assertIsNotNone(refusal(altered(LIMIT,{'modelUsage':None,'permission_denials':None})))
        self.assertIsNotNone(refusal(dict(LIMIT,returncode=None,transport_error='timeout')))
        mu=deepcopy(strict_load(stdout(SUCCESS))['modelUsage'])
        for k,v in list(mu['claude-opus-5-5'].items()):
            if ('Token' in k and k != 'maxOutputTokens') or k in ('costUSD','webSearchRequests'):
                mu['claude-opus-5-5'][k]=0
        self.assertIsNotNone(refusal(altered(LIMIT,{'modelUsage':mu})))
        mu['claude-opus-5-5']['outputTokens']=1
        self.assertIsNone(refusal(altered(LIMIT,{'modelUsage':mu})))

        self.assertIsNone(refusal(altered(LIMIT,{'total_cost_usd':0.000001})))

    def test_unparseable_output_stays_fatal(self):
        for raw in (raw_record(b'',returncode=1),raw_record(b'{',returncode=1),raw_record(b'[]')):
            with self.subTest(raw=raw),self.assertRaises(Stop):validate(raw,'claude',3,maximum('central'))

    def test_identity_tool_accounting_guards_survive_generated_error(self):
        e=strict_load(stdout(CAP))
        wrong=deepcopy(e['modelUsage']);wrong['other-model']=wrong.pop('claude-opus-5-5')
        wrong_counter=deepcopy(e['modelUsage']);wrong_counter['claude-opus-5-5']['outputTokens']=1023
        for update in ({'modelUsage':wrong},{'modelUsage':wrong_counter},
                       {'tool_calls':[{'name':'real_tool'}]},{'subagent_stats':{'spawned':1}},
                       {'usage':dict(e['usage'],output_tokens=1025)}, {'total_cost_usd':99}):
            with self.subTest(update=update),self.assertRaises(Stop):
                validate(altered(CAP,update),'claude',3,maximum('central'))


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)/'collection'
        self.ledger=Ledger(self.base/'cost.jsonl')
        self.timer=ActiveTime(self.base/'time-claude.jsonl',10800);self.timer.begin('offline')
        self.addCleanup(self.timer.end)
        self.ep={'id':'claude-fixture-central','actor':'claude','regime':'central','seed':7}

    def run_reply(self,raw,at=0):
        fake=SavedFake(raw,at)
        result=episode(self.ep,fake,self.base,self.ledger,self.timer,'OFFLINE-D5',cohort_run_id='offline')
        self.assertFalse(result['fatal']);self.assertFalse(result['complete'])
        self.assertEqual(result['classification'],'MODEL-CAUSED')
        self.assertEqual(len(fake.calls),at+1)
        self.assertEqual(self.ledger.spent,at*1600+cost(usage(strict_load(stdout(raw)),'claude')))
        self.assertFalse(any(self.ledger.holds.values()));self.assertFalse(self.ledger.stopped)
        self.assertFalse((self.base/'STOP.json').exists())
        with self.assertRaisesRegex(Stop,'terminal episode'):
            episode(self.ep,Fake(),self.base,self.ledger,self.timer,'OFFLINE-D5')
        return result

    def test_first_generated_max_tokens_failure_is_not_fatal_contract(self):
        self.run_reply(CAP)
        self.assertEqual(read(self.base/'claude-contract.json')['status'],'FAIL')

    def test_later_max_tokens_failure_keeps_earlier_rounds(self):
        result=self.run_reply(CAP,3)
        self.assertEqual(sum(e['status']=='executed' for e in result['events']),9)

    def test_schema_invalid_ends_only_episode(self):
        self.run_reply(altered(SUCCESS,{'structured_output':{'cells':[99]}}))

    def test_missing_structured_output_after_generation_ends_only_episode(self):
        self.run_reply(altered(SUCCESS,{},('structured_output',)))

    def test_refusal_with_nonzero_usage_and_no_identity_is_model_failure(self):
        self.run_reply(altered(SUCCESS,{'is_error':True,'subtype':'error','result':'I cannot comply'},('structured_output','modelUsage'),1))

    def test_error_null_identity_statistics_do_not_crash_record_writer(self):
        self.run_reply(altered(CAP,{'modelUsage':None}))

    def test_zero_limit_missing_model_usage_pauses_then_resends_exact_bytes(self):
        raw=altered(LIMIT,{},('modelUsage',))
        with patch('trl_d4.now',return_value='2026-11-11T13:00:00+00:00'):
            with self.assertRaises(UsageLimitPause):
                episode(self.ep,SavedFake(raw),self.base,self.ledger,self.timer,'OFFLINE-D5')
        self.assertEqual(self.ledger.spent,0);self.assertFalse(any(self.ledger.holds.values()))
        self.assertFalse((self.base/'claude-contract.json').exists())
        request=(self.base/'episodes'/self.ep['id']/'r1-j0.request.json').read_bytes()
        fake=Fake()
        with patch('trl_d4.now',return_value='2026-11-11T13:31:00+00:00'):
            result=episode(self.ep,fake,self.base,self.ledger,self.timer,'OFFLINE-D5')
        self.assertTrue(result['complete']);self.assertEqual(len(fake.calls),4)
        self.assertEqual((self.base/'d4-episodes'/self.ep['id']/'attempts/r1-j0/0001/call.request.json').read_bytes(),request)

    def test_unknown_transport_keeps_hold_and_stops(self):
        with self.assertRaises(Stop):
            episode(self.ep,SavedFake(raw_record(b'',returncode=1)),self.base,self.ledger,self.timer,'OFFLINE-D5')
        self.assertTrue(self.ledger.stopped);self.assertTrue(any(self.ledger.holds.values()))
        self.assertTrue((self.base/'STOP.json').exists())


class RecordedTests(unittest.TestCase):
    def test_saved_disposition_and_all_original_bytes_preserved(self):
        c=clearance(ROOT)
        self.assertEqual(c['reviewer'],'Claude');self.assertEqual(c['stop_name'],STOP_NAME)
        self.assertEqual(c['settled_micro_usd'],28699)
        old=read(ROOT/f'collection/episodes/{EPISODE}/episode.json')
        effective=read(terminal_path(ROOT/f'collection/episodes/{EPISODE}'))
        self.assertTrue(old['fatal']);self.assertFalse(effective['fatal'])
        self.assertEqual(effective['classification'],'MODEL-CAUSED')
        self.assertEqual(effective['receipts'],old['receipts'])
        from trl_analysis import replay
        row=replay(old['episode'],ROOT/f'collection/episodes/{EPISODE}')
        self.assertEqual((row['classification'],row['coverage'],row['calls']),('MODEL-CAUSED',.75,4))
        self.assertFalse(row['complete']);stop_gate(ROOT)
        with self.assertRaises(FileExistsError):record_clearance(ROOT,'Claude','repeat')

    def test_lineage_assigns_all_saved_starts_to_parents_and_no_new_starts(self):
        c=clearance(ROOT);layers=provenance_layers(ROOT)
        self.assertEqual(layers[-1],('freeze-d5.json','-d5',set()))
        starts={n for n in c['preserved_files'] if n.endswith('.start.json')}
        self.assertEqual(set.union(*(s for _,_,s in layers)),starts)
        self.assertEqual(sum(len(s) for _,_,s in layers),len(starts))
        prepush_gate(ROOT)


class FreezeCollectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from historical import frozen_bytes
        from trl_freeze import D5_ADDED,D5_CHANGED,freeze_d5
        from trl_test import tested_inputs
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.template=Path(cls.tmp.name)/'template'
        parent=read(ROOT/'freeze-d4.json')
        for n,h in parent['files'].items():
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(frozen_bytes(n,h))
        shutil.copyfile(ROOT/'freeze-d4.json',cls.template/'freeze-d4.json')
        c=clearance(ROOT)
        for n,h in c['preserved_files'].items():
            data=(ROOT/n).read_bytes()
            if n in c['ledger_prefixes']:data=data[:c['ledger_prefixes'][n]['bytes']]
            assert sha(data)==h
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for n in D5_ADDED|D5_CHANGED:
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((ROOT/n).read_bytes() if (ROOT/n).exists() else b'{"fixture":true}\n')
        (cls.template/'evidence/test-report-d5.json').write_text(canonical({
            'status':'PASS','tests':1,'failures':0,'errors':0,'fixture':True,
            'tested_files':tested_inputs(cls.template)})+'\n')
        freeze_d5(cls.template)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';shutil.copytree(self.template,self.root)
        self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir();self.commit='e'*40

    def attest(self,bad=None):
        from trl_freeze import attest
        event={'id':'synthetic-d5','activity_type':'push','after':self.commit,
            'ref':'refs/heads/main','timestamp':(timestamp(read(self.root/'freeze-d5.json')['created_at'])+dt.timedelta(microseconds=1)).isoformat()}
        p=self.root/'build/event.json';save(p,event)
        def git(args,**kwargs):
            if args[1]=='rev-parse':return (self.commit+'\n').encode()
            if args[1]=='remote':return b'https://github.com/Robin84Bran/research.git\n'
            if args[1]=='ls-remote':return (self.commit+'\trefs/heads/main\n').encode()
            if args[1]=='show':
                n=args[2].split(':three-rules-one-lunch/')[1]
                return b'wrong bytes' if n==bad else (self.root/n).read_bytes()
            raise AssertionError(args)
        with patch('trl_freeze.subprocess.check_output',side_effect=git):
            return attest(self.root,p,self.commit,'three-rules-one-lunch',self.clone,'freeze-d5.json')

    def test_freeze_binds_parents_baselines_science_and_current_tests(self):
        from trl_freeze import verify,freeze_d5,d5_scope,D4_FREEZE_SHA256
        f=read(self.root/'freeze-d5.json');self.assertEqual(f['parent_freeze_sha256'],D4_FREEZE_SHA256)
        verify(self.root)
        with self.assertRaises(FileExistsError):freeze_d5(self.root)
        for n in ('config/prompts.json','trl_validation.py','deviations/d5/baseline/trl_d4.py'):
            bad=deepcopy(f);bad['files'][n]='0'*64
            with self.subTest(n=n),self.assertRaises(Stop):d5_scope(self.root,bad)
        (self.root/'freeze-d5.json').unlink()
        (self.root/'trl_d5.py').write_text('changed after tests')
        with self.assertRaisesRegex(Stop,'passing D5 tests'):freeze_d5(self.root)

    def test_attestation_requires_exact_committed_blobs_and_all_parent_receipts(self):
        from trl_collect import push_gate
        with self.assertRaisesRegex(Stop,'frozen file'):self.attest('trl_d5.py')
        (self.root/'build/event.json').unlink()
        self.attest();push_gate(self.root)
        (self.root/'collection/push-d4.json').unlink()
        with self.assertRaises((FileNotFoundError,Stop)):push_gate(self.root)

    def test_three_model_failures_continue_cohort_and_all_attempts_skipped_on_resume(self):
        from trl_collect import collect,push_gate
        self.attest()
        c=clearance(self.root)
        old={n:(self.root/n).read_bytes() for n in c['preserved_files'] if n not in c['ledger_prefixes']}
        eps=[{'id':f'claude-d5-{i}-central','actor':'claude','regime':'central','seed':i} for i in range(4)]
        eps.insert(0,read(self.root/DISPOSITION)['episode'])
        original=__import__('trl_collect').read
        def schedule(p):return eps if Path(p)==self.root/'config/episodes.json' else original(p)
        fake=SavedFake(CAP)
        # Fail every first call of an episode, not just the first episode.
        generate=fake.generate
        def always_fail(actor,req,work):
            generate(actor,req,work)
            return altered(SUCCESS,{'stop_reason':'end_turn'}) if Path(work).name=='claude-d5-3-central' else deepcopy(CAP)
        fake.generate=always_fail
        fake.preflight=lambda actor:read(sorted((self.root/'collection/runtime').glob('claude-*.json'))[0])
        with patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',return_value=fake):
            collect(self.root,'claude')
        self.assertEqual(len(fake.calls),7)
        for ep in eps[1:4]:
            t=read(self.root/'collection/episodes'/ep['id']/'episode.json')
            self.assertFalse(t['fatal']);self.assertEqual(t['classification'],'MODEL-CAUSED')
        from trl_analysis import replay
        self.assertTrue(replay(eps[-1],self.root/'collection/episodes'/eps[-1]['id'])['complete'])
        for n,data in old.items():self.assertEqual((self.root/n).read_bytes(),data)
        self.assertEqual(len(list((self.root/'collection').glob('STOP*.json'))),5)
        push_gate(self.root);clearance(self.root)
        with patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',side_effect=AssertionError('no rerun')):
            collect(self.root,'claude')

    def test_new_start_cannot_claim_parent_hash_or_attest_late(self):
        save(self.root/'collection/episodes/foreign/r1-j0.start.json',{
            'id':'foreign','started_at':now(),'freeze_sha256':sha((self.root/'freeze-d4.json').read_bytes())})
        self.assertEqual(len(provenance_layers(self.root)[-1][2]),1)
        with self.assertRaisesRegex(Stop,'precede all D5 starts'):self.attest()

    def test_orphan_continuation_blocks_before_service_access(self):
        from trl_collect import collect
        self.attest()
        save(self.root/'collection/d4-episodes/orphan/evidence.json',{'unknown':True})
        with patch('trl_collect.Claude',side_effect=AssertionError('no service access')):
            with self.assertRaisesRegex(Stop,'orphan D4 continuation'):collect(self.root,'claude')

    def test_future_integrity_stop_still_blocks(self):
        from trl_io import stop
        stop(self.root/'collection','wrong pinned model')
        self.assertEqual(read(self.root/'collection/STOP-d3b-004.json')['reason'],'wrong pinned model')
        with self.assertRaises(Stop):stop_gate(self.root)

    def test_ledger_prefixes_allow_appends_reject_rewrites_and_torn_tails(self):
        c=clearance(self.root)
        for n in c['ledger_prefixes']:
            p=self.root/n;original=p.read_bytes()
            p.write_bytes(original+b'{"fixture":"append"}\n');clearance(self.root)
            p.write_bytes(b'!'+original[1:])
            with self.assertRaisesRegex(Stop,'prefix'):clearance(self.root)
            p.write_bytes(original+b'{')
            with self.assertRaisesRegex(Stop,'prefix'):clearance(self.root)
            p.write_bytes(original)
