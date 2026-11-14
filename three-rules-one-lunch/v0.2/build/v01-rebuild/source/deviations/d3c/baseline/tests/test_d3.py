"""D3 offline regressions. HTTP responses are in-memory; Git and providers mocked."""
import http.client
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from trl_core import ROOT, canonical, sha, strict_load, render
from trl_io import Stop, read, save, append, stop, timestamp
from trl_transport import Fake, raw_record, request, http as http_request
from trl_validation import LocalTransportFailure, validate, stdout
from trl_budget import ActiveTime, Ledger, maximum
from trl_collect import episode, collect, push_gate
from trl_analysis import replay
from trl_d3 import (EPISODE, CLEARANCE, clearance, stop_gate, scan, verify_prefix,
                    recover_prefix, record_clearance)
from trl_freeze import D3_ADDED, D3_CHANGED, D2_FREEZE_SHA256, freeze_d3, inputs, verify, attest
from trl_test import tested_inputs


class IncompleteFake(Fake):
    def __init__(self,at=1,changes=None):
        super().__init__();self.at=at;self.changes=changes

    def generate(self,actor,req,work):
        raw=super().generate(actor,req,work)
        if len(self.calls)==self.at:
            env=strict_load(stdout(raw))
            if self.changes is None:
                env.update(done=False);env.pop('eval_count');env.pop('done_reason')
            else:
                env.update(self.changes)
            return raw_record(canonical(env).encode(),running=raw['running'])
        return raw


class TransportTests(unittest.TestCase):
    def test_nonstreaming_reads_entire_http_body_across_wire_chunks(self):
        body=b'{"model":"fixture","done":true,"response":"complete"}'
        class Socket:
            def makefile(self,*args):
                parts=[body[:5],body[5:23],body[23:]]
                wire=b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
                return io.BytesIO(wire+b''.join(format(len(b),'x').encode()+b'\r\n'+b+b'\r\n' for b in parts)+b'0\r\n\r\n')
        response=http.client.HTTPResponse(Socket());response.begin()
        with patch('trl_transport.urllib.request.urlopen',return_value=response) as opened:
            req=request('qwen1b',render('central',1,0,[]),3,7,maximum('central'))
            self.assertEqual(http_request('/api/generate',req,180),body)
        self.assertIs(strict_load(opened.call_args.args[0].data.decode())['stream'],False)

    def test_short_content_length_raises_instead_of_accepting_first_chunk(self):
        class Socket:
            def makefile(self,*args):
                return io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 40\r\n\r\n{"done":false}')
        response=http.client.HTTPResponse(Socket());response.begin()
        with patch('trl_transport.urllib.request.urlopen',return_value=response):
            with self.assertRaises(http.client.IncompleteRead):http_request('/api/generate',{'stream':False})

    def test_local_incomplete_and_missing_usage_end_episode_no_retry(self):
        for actor in ('qwen7b','llama8b','qwen1b'):
            for changes in (None,{'done':False},{'eval_count':None}):
                with self.subTest(actor=actor,changes=changes),tempfile.TemporaryDirectory() as t:
                    base=Path(t);timer=ActiveTime(base/'time.jsonl',43200);timer.begin('fixture')
                    ep={'actor':actor,'seed':0,'regime':'central','id':actor+'-s000-central'}
                    fake=IncompleteFake(at=2,changes=changes)
                    result=episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
                    self.assertFalse(result['fatal']);self.assertFalse(result['complete'])
                    self.assertEqual(len(fake.calls),2)
                    self.assertEqual([e['status'] for e in result['events']],['executed']*3+['technical']*3+['missing']*6)
                    self.assertEqual(len(result['receipts']),3)
                    self.assertFalse((base/'STOP.json').exists())
                    row=replay(ep,base/'episodes'/ep['id']);self.assertEqual(row['calls'],2)
                    if changes is None or 'eval_count' in changes:
                        self.assertIsNone(row['output_tokens']);self.assertEqual(row['unknown_usage_calls'],1)
                    with self.assertRaises(Stop):episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
                    self.assertEqual(len(fake.calls),2)

    def test_wrong_identity_is_fatal_even_when_incomplete(self):
        req=request('qwen1b',render('central',1,0,[]),3,7,maximum('central'))
        raw=IncompleteFake(changes={'done':False,'model':'wrong','eval_count':None}).generate('qwen1b',req,Path('.'))
        with self.assertRaises(Stop):validate(raw,'qwen1b',3,maximum('central'))

    def test_known_digest_context_and_limits_stay_fatal_when_incomplete(self):
        req=request('qwen1b',render('central',1,0,[]),3,7,maximum('central'))
        for changes in ({'done':False,'eval_count':193},{'done':False,'prompt_eval_count':8000}):
            raw=IncompleteFake(changes=changes).generate('qwen1b',req,Path('.'))
            with self.assertRaises(Stop):validate(raw,'qwen1b',3,maximum('central'))
        for field,value in (('digest','wrong'),('context_length',2048)):
            raw=IncompleteFake().generate('qwen1b',req,Path('.'))
            raw['running']['models'][0][field]=value
            with self.assertRaises(Stop):validate(raw,'qwen1b',3,maximum('central'))

    def test_local_timeout_unknown_start_is_terminal_without_resend(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);timer=ActiveTime(base/'time.jsonl',43200);timer.begin('fixture')
            ep={'actor':'qwen1b','seed':0,'regime':'central','id':'qwen1b-s000-central'}
            fake=Fake('timeout');result=episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
            self.assertFalse(result['fatal']);self.assertEqual(len(fake.calls),1)
            self.assertEqual([e['status'] for e in result['events']],['technical']*3+['missing']*9)
            self.assertIsNone(replay(ep,base/'episodes'/ep['id'])['input_tokens'])
            with self.assertRaises(Stop):episode(ep,fake,base,Ledger(base/'cost.jsonl'),timer,'FAKE')
            self.assertEqual(len(fake.calls),1)

    def test_no_first_json_object_or_line_extraction(self):
        raw=raw_record(b'{"done":false}\n{"done":true}')
        with self.assertRaises(LocalTransportFailure):validate(raw,'qwen1b',3,maximum('central'))

    def test_saved_scan_reproduces_counts_and_no_accepted_incomplete_reply(self):
        actual=scan(ROOT);saved=read(ROOT/'deviations/d3/scan.json')
        for actor in actual['counts']:
            for k,v in saved['counts'][actor].items():self.assertEqual(actual['counts'][actor][k],v)
            self.assertEqual(actual['counts'][actor]['decode_errors'],0)
            self.assertEqual(actual['counts'][actor]['parsed_missing'],0)
            self.assertEqual(actual['counts'][actor]['accepted_done_not_true'],0)
            self.assertEqual(actual['counts'][actor]['accepted_usage_missing'],0)
        self.assertEqual(actual['anomalies'],saved['anomalies'])
        self.assertEqual(actual['collection_files'],saved['collection_files'])


class D3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.template=Path(cls.tmp.name)/'template'
        for n in read(ROOT/'freeze-d3.json')['files']:
            p=cls.template/n;p.parent.mkdir(parents=True,exist_ok=True)
            baseline=ROOT/'deviations/d3b/baseline'/n
            p.write_bytes((baseline if baseline.exists() else ROOT/n).read_bytes())
        for n in D3_ADDED:
            p=cls.template/n
            if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{"fixture":true}\n')
        shutil.copytree(ROOT/'collection',cls.template/'collection',ignore=shutil.ignore_patterns('collector.lock'))
        cls.report(cls.template)
        freeze_d3(cls.template)

    @staticmethod
    def report(root):
        (root/'evidence/test-report-d3.json').write_text(canonical({'status':'PASS','failures':0,'errors':0,
            'tests':1,'fixture':True,'tested_files':tested_inputs(root)})+'\n')

    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)/'project';shutil.copytree(self.template,self.root)
        self.clone=Path(self.t.name)/'clone';self.clone.mkdir()
        self.commit='c'*40
        import datetime as dt
        self.when=(timestamp(read(self.root/'freeze-d3.json')['created_at'])+dt.timedelta(microseconds=1)).isoformat()
        self.event={'id':'synthetic-d3','activity_type':'push','after':self.commit,'ref':'refs/heads/claude/d3','timestamp':self.when}
        self.eventpath=self.root/'build/activity.json';self.eventpath.parent.mkdir(exist_ok=True)
        self.eventpath.write_text(canonical(self.event))

    def git(self,args,**kw):
        self.assertEqual(kw['cwd'],self.clone)
        if args[1]=='rev-parse':return (self.commit+'\n').encode()
        if args[1]=='remote':return b'https://github.com/Robin84Bran/research.git\n'
        if args[1]=='ls-remote':return (self.commit+'\t'+self.event['ref']+'\n').encode()
        if args[1]=='show':return (self.root/args[2].split(':three-rules-one-lunch/')[1]).read_bytes()
        raise AssertionError(args)

    def attest(self):
        with patch('trl_freeze.subprocess.check_output',side_effect=self.git):
            return attest(self.root,self.eventpath,self.commit,'three-rules-one-lunch',self.clone)

    def test_parent_binding_baselines_and_create_once(self):
        f=read(self.root/'freeze-d3.json');self.assertEqual(f['parent_freeze_sha256'],D2_FREEZE_SHA256)
        self.assertEqual(f['files']['freeze-d2.json'],D2_FREEZE_SHA256)
        for n in D3_CHANGED:self.assertEqual(f['files']['deviations/d3/baseline/'+n],read(self.root/'freeze-d2.json')['files'][n])
        with self.assertRaises(FileExistsError):freeze_d3(self.root)
        with self.assertRaises(FileExistsError):record_clearance(self.root)

    def test_prefix_append_passes_but_edit_truncation_and_torn_tail_fail(self):
        c=clearance(self.root);n='collection/time-local.jsonl';p=self.root/n;original=p.read_bytes()
        self.assertEqual(c['d2_ledger_prefixes'][n]['bytes'],253)
        append(p,{'fixture':'appended complete row'})
        self.assertEqual(clearance(self.root)['disposition'],'SCORED_NO_RERUN')
        for raw in (b'X'+original[1:],original[:100],original+b'{"torn":'):
            p.write_bytes(raw)
            with self.assertRaisesRegex(Stop,'prefix'):clearance(self.root)
        p.write_bytes(original)
        bad=dict(c['ledger_prefixes'][n],bytes=10)
        with self.assertRaises(Stop):verify_prefix(self.root,n,bad)
        with self.assertRaises(Stop):verify_prefix(self.root,'collection/STOP.json',c['ledger_prefixes'][n])
        with self.assertRaises(Stop):recover_prefix(self.root,n,'0'*64)

    def test_disposition_unknown_usage_and_original_bytes_remain(self):
        c=clearance(self.root)
        self.assertEqual((c['Y'],c['H'],c['technical_opportunities'],c['missing_opportunities']),(0,0,3,9))
        self.assertEqual(c['usage_status'],'UNKNOWN');self.assertIsNone(c['output_tokens'])
        terminal=read(self.root/'collection/episodes'/EPISODE/'episode.json')
        self.assertTrue(terminal['fatal']);self.assertEqual(replay(terminal['episode'],self.root/'collection/episodes'/EPISODE)['unknown_usage_calls'],1)
        for n,h in c['preserved_files'].items():self.assertEqual(sha((self.root/n).read_bytes()),h)

    def test_three_push_layers_and_new_starts_require_new_attestation(self):
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        digest=self.attest();self.assertEqual(push_gate(self.root),digest)
        c=clearance(self.root)
        for n in ('collection/push.json','collection/push-d2.json'):
            self.assertEqual(sha((self.root/n).read_bytes()),c['preserved_files'][n])
        save(self.root/'collection/episodes/new/r1-j0.start.json',{'freeze_sha256':digest,'started_at':__import__('trl_io').now()})
        self.assertEqual(push_gate(self.root),digest)
        p=self.root/'collection/episodes/new/r1-j0.start.json';v=read(p);v['freeze_sha256']=D2_FREEZE_SHA256;p.write_text(canonical(v))
        with self.assertRaisesRegex(Stop,'push/start'):push_gate(self.root)

    def test_attestation_rejects_preexisting_d3_start_and_is_create_once(self):
        self.attest()
        with self.assertRaises(FileExistsError):self.attest()
        (self.root/'collection/push-d3.json').unlink();(self.root/'collection/push-event-d3.raw.json').unlink() # temp fixture
        save(self.root/'collection/episodes/new/r1-j0.start.json',{'freeze_sha256':verify(self.root),'started_at':__import__('trl_io').now()})
        with self.assertRaisesRegex(Stop,'precede all D3 starts'):self.attest()
        self.assertFalse((self.root/'collection/push-d3.json').exists())

    def test_all_old_stops_bound_and_future_stop_not_cleared(self):
        for n in ('STOP.json','STOP-d2.json'):
            p=self.root/'collection'/n;original=p.read_bytes();p.write_bytes(original+b' ')
            with self.assertRaisesRegex(Stop,'preserved evidence'):clearance(self.root)
            p.write_bytes(original)
        old=(self.root/'collection/STOP-d2.json').read_bytes()
        stop(self.root/'collection','new integrity failure')
        self.assertEqual((self.root/'collection/STOP-d2.json').read_bytes(),old)
        self.assertTrue((self.root/'collection/STOP-d3.json').exists())
        with self.assertRaisesRegex(Stop,'uncleared'):stop_gate(self.root)

    def test_skip_cleared_fatal_episode_and_resume_timer_without_transport(self):
        digest=self.attest();ep=read(self.root/'collection/episodes'/EPISODE/'episode.json')['episode']
        original=__import__('trl_collect').read
        def selected(path):
            return [ep] if Path(path)==self.root/'config/episodes.json' else original(path)
        with patch('trl_collect.read',side_effect=selected),patch('trl_collect.Local',side_effect=AssertionError('no resend')):
            collect(self.root,'local')
        self.assertEqual(push_gate(self.root),digest)
        self.assertEqual(stop_gate(self.root)['disposition'],'SCORED_NO_RERUN')

    def test_new_partial_and_other_fatal_block_before_transport(self):
        self.attest();d=self.root/'collection/episodes/other';d.mkdir()
        with patch('trl_collect.Local',side_effect=AssertionError('no dispatch')):
            with self.assertRaisesRegex(Stop,'nonterminal'):collect(self.root,'local')
            save(d/'episode.json',{'fatal':True})
            with self.assertRaisesRegex(Stop,'terminal integrity'):collect(self.root,'local')

    def test_historical_extra_call_and_missing_tests_or_scientific_drift_rejected(self):
        p=self.root/'collection/episodes'/EPISODE/'r2-j0.start.json';save(p,{'fixture':True})
        with self.assertRaisesRegex(Stop,'additional'):clearance(self.root)
        p.unlink() # temp fixture
        (self.root/'freeze-d3.json').unlink()
        (self.root/'evidence/test-report-d3.json').write_text('{"status":"PASS"}')
        with self.assertRaisesRegex(Stop,'passing D3 tests'):freeze_d3(self.root)
        self.report(self.root)
        p=self.root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
        self.report(self.root)
        with self.assertRaisesRegex(Stop,'scope'):freeze_d3(self.root)
