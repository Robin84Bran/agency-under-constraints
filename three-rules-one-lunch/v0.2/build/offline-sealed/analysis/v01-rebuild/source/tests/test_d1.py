"""Offline D1 regressions: fake transports, mocked Git, temporary output roots."""
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from historical import frozen_bytes
from trl_core import ROOT, canonical, sha, strict_load, render
from trl_io import Stop, read, save, timestamp
from trl_freeze import (D1_ADDED, D1_CHANGED, ORIGINAL_FREEZE_SHA256, active_freeze,
                        attest, freeze_d1, inputs, push_record, select_event, verify)
from trl_collect import episode, readiness, push_gate
from trl_budget import Ledger, ActiveTime, maximum, episode_hold
from trl_transport import Claude, Fake, request, raw_record, stdout
from trl_validation import usage, cost
from trl_test import tested_inputs


class D1FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'project'
        self.clone = Path(self.tmp.name)/'clone'
        self.clone.mkdir()
        # Copy current inputs, never collection state or a pre-existing D1 freeze.
        # D1 regression fixtures must reconstruct D1, not include D2 additions.
        for name,digest in read(ROOT/'freeze-d1.json')['files'].items():
            p = self.root/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(frozen_bytes(name,digest))
        for name in D1_ADDED:
            p = self.root/name
            if not p.exists():
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text('{"fixture":true}\n')
        self.report()
        parent = read(self.root/'freeze.json')
        self.when = (timestamp(parent['created_at'])+dt.timedelta(seconds=1)).isoformat()
        with patch('trl_freeze.now',return_value=self.when):
            freeze_d1(self.root)
        self.commit = 'a'*40
        self.event = {'id':'synthetic-activity','activity_type':'push','ref':'refs/heads/main',
                      'after':self.commit,'timestamp':(timestamp(self.when)+dt.timedelta(seconds=1)).isoformat()}
        self.raw = ('  '+canonical(self.event)+'\n').encode()
        self.event_path = self.root/'build/activity.json'
        self.event_path.parent.mkdir()
        self.event_path.write_bytes(self.raw)
        self.git_calls = []

    def report(self):
        p = self.root/'evidence/test-report-d1.json'
        p.write_text(canonical({'status':'PASS','failures':0,'errors':0,'tests':1,
                              'fixture':True,'tested_files':tested_inputs(self.root)})+'\n')

    def git(self,args,**kwargs):
        self.assertEqual(kwargs['cwd'],self.clone)
        self.git_calls.append(args)
        if args[1:]==['rev-parse','HEAD']:return (self.commit+'\n').encode()
        if args[1:]==['remote','get-url','origin']:return b'git@github.com:Robin84Bran/research.git\n'
        if args[1]=='ls-remote':return (self.commit+'\t'+push_record(self.event,self.commit)[0]+'\n').encode()
        if args[1]=='show':return (self.root/args[2].split(':three-rules-one-lunch/')[1]).read_bytes()
        raise AssertionError(args)

    def attest(self,git=None):
        with patch('trl_freeze.subprocess.check_output',side_effect=git or self.git):
            return attest(self.root,self.event_path,self.commit,'three-rules-one-lunch',self.clone)

    def manifest_edit(self,edit):
        p = self.root/'freeze-d1.json'
        f = read(p);edit(f)
        f['content_sha256'] = sha(canonical(f['files']).encode())
        p.write_text(canonical(f)+'\n')

    def test_activity_exact_bytes_separate_roots_create_once(self):
        digest = self.attest()
        self.assertEqual(push_gate(self.root),digest)
        self.assertEqual((self.root/'collection/push-event.raw.json').read_bytes(),self.raw)
        self.assertEqual(list(self.clone.iterdir()),[])
        receipt = read(self.root/'collection/push.json')
        self.assertEqual(receipt['original_freeze_sha256'],ORIGINAL_FREEZE_SHA256)
        self.assertEqual(receipt['source_api'],'/repos/Robin84Bran/research/activity')
        self.assertTrue(any(x[2].endswith('/freeze.json') for x in self.git_calls if x[1]=='show'))
        self.assertTrue(any(x[2].endswith('/freeze-d1.json') for x in self.git_calls if x[1]=='show'))
        with self.assertRaises(FileExistsError):self.attest()
        self.assertEqual((self.root/'collection/push-event.raw.json').read_bytes(),self.raw)

    def test_d1_readiness_replaces_unknown_legacy_contract(self):
        self.assertEqual(read(self.root/'evidence/cli-contract.json')['readiness'],'UNKNOWN')
        readiness(self.root)
        with patch('trl_transport.CLAUDE_BIN',str(self.root/'evidence/claude-help.txt')):
            with self.assertRaisesRegex(Stop,'binary hash drift'):Claude(self.root).preflight('claude')

    def test_push_event_still_accepted(self):
        e = {'id':4,'type':'PushEvent','repo':{'name':'Robin84Bran/research'},
             'payload':{'head':self.commit,'ref':'refs/heads/claude/test'},'created_at':self.event['timestamp']}
        self.event=e;self.raw=canonical(e).encode();self.event_path.write_bytes(self.raw)
        digest=self.attest()
        self.assertEqual(push_gate(self.root),digest)

    def test_server_record_selection_activity_pages(self):
        save(self.root/'build/pages.json',[[{'activity_type':'push','after':'b'*40},self.event]])
        select_event(self.root/'build/pages.json',self.commit,self.root/'build/selected.json')
        self.assertEqual(read(self.root/'build/selected.json'),self.event)

    def test_bad_activity_fields_and_timestamps(self):
        changes = [{'after':'b'*40},{'activity_type':'force_push'},{'ref':'main'},
                   {'timestamp':'2021-01-01T00:00:00'},{'timestamp':'garbage'},
                   {'timestamp':'2999-01-01T00:00:00Z'},{'id':None},{'id':''}]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(Stop):push_record(dict(self.event,**change),self.commit)
        for key in ('ref','after','timestamp','activity_type','id'):
            e=dict(self.event);e.pop(key)
            with self.subTest(missing=key),self.assertRaises(Stop):push_record(e,self.commit)
        with self.assertRaises(Stop):push_record(self.event,'short')

    def test_push_before_active_freeze_blocked(self):
        self.event['timestamp']=read(self.root/'freeze.json')['created_at']
        self.event_path.write_text(canonical(self.event))
        with self.assertRaisesRegex(Stop,'follow active freeze'):self.attest()

    def test_head_origin_ref_and_committed_file_mismatches(self):
        for which in ('head','origin','ref','original','active','science'):
            def bad(args,**kwargs):
                result=self.git(args,**kwargs)
                if which=='head' and args[1]=='rev-parse':return b'bad\n'
                if which=='origin' and args[1]=='remote':return b'https://example.com/research.git\n'
                if which=='ref' and args[1]=='ls-remote':return b''
                targets={'original':'/freeze.json','active':'/freeze-d1.json','science':'/config/prompts.json'}
                if which in targets and args[1]=='show' and args[2].endswith(targets[which]):return b'wrong blob'
                return result
            with self.subTest(which=which),self.assertRaises(Stop):self.attest(bad)
        self.assertFalse((self.root/'collection/push.json').exists())

    def test_invalid_repo_paths(self):
        for name in ('../escape','/absolute','', 'repo:other'):
            with self.subTest(name=name),self.assertRaises(Stop):
                attest(self.root,self.event_path,self.commit,name,self.clone)

    def test_receipt_tamper_detected(self):
        self.attest()
        path=self.root/'collection/push.json';original=path.read_bytes()
        for key,value in (('server_event_id','other'),('remote_ref','refs/heads/other'),
                          ('freeze_sha256','x'),('original_freeze_sha256','x'),
                          ('source_api','/invented'),('pushed_at','2021-01-01T00:00:00Z')):
            a=strict_load(original.decode());a[key]=value;path.write_text(canonical(a))
            with self.subTest(key=key),self.assertRaises(Stop):push_gate(self.root)
        path.write_bytes(original)
        (self.root/'collection/push-event.raw.json').write_bytes(self.raw+b' ')
        with self.assertRaises(Stop):push_gate(self.root)

    def test_push_must_precede_every_start_and_no_late_attest(self):
        digest=self.attest()
        save(self.root/'collection/episodes/example/r1-j1.start.json',
             {'freeze_sha256':digest,'started_at':self.event['timestamp']})
        with self.assertRaises(Stop):push_gate(self.root)
        with self.assertRaises(Stop):self.attest()

    def test_parent_binding_and_scientific_drift_not_refreezable(self):
        self.assertEqual(sha((self.root/'freeze.json').read_bytes()),ORIGINAL_FREEZE_SHA256)
        p=self.root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
        self.manifest_edit(lambda f:f['files'].update({'config/prompts.json':sha(p.read_bytes())}))
        with self.assertRaisesRegex(Stop,'scope'):verify(self.root)

    def test_scientific_metadata_unchanged(self):
        self.manifest_edit(lambda f:f.update(planned_calls=1))
        with self.assertRaisesRegex(Stop,'scientific'):verify(self.root)

    def test_parent_tamper_and_baseline_tamper(self):
        p=self.root/'freeze.json';original=p.read_bytes();p.write_bytes(original+b' ')
        with self.assertRaisesRegex(Stop,'original freeze'):verify(self.root)
        p.write_bytes(original)
        self.manifest_edit(lambda f:f['files'].update({'deviations/d1/baseline/trl_collect.py':'x'}))
        with self.assertRaisesRegex(Stop,'baseline'):verify(self.root)

    def test_unlisted_input_and_amendment_create_once(self):
        with self.assertRaises(FileExistsError):freeze_d1(self.root)
        (self.root/'extra.py').write_text('unexpected')
        with self.assertRaises(Stop):verify(self.root)

    def test_d1_freeze_requires_current_passing_tests_and_no_starts(self):
        (self.root/'freeze-d1.json').unlink()  # Temporary fixture only.
        (self.root/'evidence/test-report-d1.json').write_text('{"status":"PASS"}')
        with self.assertRaisesRegex(Stop,'passing D1 tests'):freeze_d1(self.root)
        self.report()
        save(self.root/'collection/episodes/example/r1-j1.start.json',{'fixture':True})
        with self.assertRaisesRegex(Stop,'precede inference'):freeze_d1(self.root)

    def test_original_scientific_hashes_preserved(self):
        f=read(self.root/'freeze-d1.json');parent=read(self.root/'freeze.json')
        self.assertEqual({n for n,h in parent['files'].items() if f['files'][n]!=h},D1_CHANGED)
        for n in ('RUN.md','PROTOCOL.md','PROJECT_STATE.md','SURVEY.md','README.md','config/transport.json','trl_analysis.py','trl_budget.py'):
            self.assertEqual(f['files'][n],parent['files'][n])


class D1TransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.ep={'actor':'claude','seed':0,'regime':'shared','id':'claude-s000-shared'}
        self.timer=ActiveTime(self.base/'time.jsonl',10800);self.timer.begin('fixture')
        self.ledger=Ledger(self.base/'cost.jsonl')

    def run_ep(self,transport):
        return episode(self.ep,transport,self.base,self.ledger,self.timer,'FAKE-D1')

    def fake_edit(self,edit):
        class Edited(Fake):
            def generate(inner,*args):
                raw=super().generate(*args);e=strict_load(stdout(raw));edit(e)
                return raw_record(canonical(e).encode())
        return Edited()

    def test_first_scheduled_call_verifies_and_saves_payload_contract(self):
        f=Fake();result=self.run_ep(f)
        self.assertTrue(result['complete']);self.assertEqual(len(f.calls),12)
        c=read(self.base/'claude-contract.json')
        self.assertEqual(c['status'],'PASS');self.assertTrue(c['call_id'].endswith('r1-j1'))
        self.assertEqual(self.ledger.spent,12*1600)
        self.assertEqual(self.ledger.exposure,self.ledger.spent)

    def test_missing_or_multiple_payloads_stop_after_one_counted_call(self):
        for change in (lambda e:e.pop('structured_output'),lambda e:e.update(structured_output=[{},{}]),
                       lambda e:e.update(structured_output='{"cells":[1]}')):
            with tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);f=self.fake_edit(change);ledger=Ledger(base/'cost.jsonl')
                with self.assertRaises(Stop):episode(self.ep,f,base,ledger,self.timer,'FAKE-D1')
                self.assertEqual(len(f.calls),1);self.assertEqual(ledger.spent,1600)
                self.assertEqual(read(base/'claude-contract.json')['status'],'FAIL')
                self.assertTrue((base/'STOP.json').exists())
                self.assertTrue((base/'episodes'/self.ep['id']/'r1-j1.raw.json').exists())
                self.assertTrue((base/'episodes'/self.ep['id']/'r1-j1.parsed.json').exists())
                with self.assertRaises(Stop):episode(self.ep,f,base,ledger,self.timer,'FAKE-D1')
                self.assertEqual(len(f.calls),1)

    def test_first_envelope_array_duplicate_payload_or_multiple_envelopes_stops(self):
        class Wire(Fake):
            def __init__(inner,kind):
                super().__init__();inner.kind=kind
            def generate(inner,*args):
                text=stdout(super().generate(*args))
                if inner.kind=='array':text='['+text+']'
                if inner.kind=='multiple':text=text+'\n'+text
                if inner.kind=='duplicate':text=text[:-1]+',"structured_output":{"cells":[1]}}'
                return raw_record(text.encode())
        for kind in ('array','multiple','duplicate'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);f=Wire(kind);ledger=Ledger(base/'cost.jsonl')
                with self.assertRaises(Stop):episode(self.ep,f,base,ledger,self.timer,'FAKE-D1')
                self.assertEqual(len(f.calls),1);self.assertTrue(ledger.stopped)
                self.assertGreater(ledger.exposure,0)
                self.assertEqual(read(base/'claude-contract.json')['status'],'FAIL')
                self.assertTrue((base/'STOP.json').exists())

    def test_first_payload_schema_failure_also_stops_without_replacement(self):
        f=Fake('malformed')
        with self.assertRaises(Stop):self.run_ep(f)
        self.assertEqual(len(f.calls),1);self.assertEqual(self.ledger.spent,1600)
        self.assertEqual(read(self.base/'claude-contract.json')['status'],'FAIL')

    def test_reported_cost_settles_greater_amount_rounded_up(self):
        f=self.fake_edit(lambda e:e.update(total_cost_usd='0.0020001'))
        self.run_ep(f)
        self.assertEqual(self.ledger.spent,12*2001)

    def test_reported_cost_overrun_saved_before_stop(self):
        f=self.fake_edit(lambda e:e.update(total_cost_usd='0.05'))
        with self.assertRaises(Stop):self.run_ep(f)
        self.assertEqual(len(f.calls),1);self.assertEqual(self.ledger.spent,50000)
        self.assertTrue(Ledger(self.base/'cost.jsonl').stopped)

    def test_missing_usage_stops_dispatch_and_retains_reservation(self):
        f=Fake('usage')
        with self.assertRaises(Stop):self.run_ep(f)
        self.assertEqual(len(f.calls),1)
        l=Ledger(self.base/'cost.jsonl')
        self.assertTrue(l.stopped);self.assertEqual(l.exposure,episode_hold('shared'))

    def test_invalid_reported_cost_is_unknown(self):
        req=request('claude',render('shared',1,1,[]),1,0,maximum('shared'))
        e=strict_load(stdout(Fake().generate('claude',req,self.base)))
        for value in (None,-1,True,'NaN','Infinity','garbage'):
            with self.subTest(value=value):self.assertIsNone(usage(dict(e,total_cost_usd=value),'claude'))
        self.assertEqual(cost(usage(dict(e,total_cost_usd='0'),'claude')),1600)

    def test_rolling_holds_prevent_dispatch_over_frontier_envelope(self):
        self.ledger.event(event='reserve',id='prior',amount=24000000)
        f=Fake()
        with self.assertRaises(Stop):self.run_ep(f)
        self.assertEqual(f.calls,[])
