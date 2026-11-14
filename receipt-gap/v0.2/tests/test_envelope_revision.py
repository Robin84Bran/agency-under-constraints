"""r2 real saved byte regressions and explicit derived-envelope shape audit."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import rg_collect as c
import rg_analysis as a
import rg_freeze as f
import rg_revision as r
from rg_core import ROOT, ModelOutputError, canonical, render, reserve, sha
from rg_offline import Fake

EXTERNAL=Path('<SCRATCH>/orchestra/real-claude-envelope.json')


class EnvelopeRevisionTests(unittest.TestCase):
    def setUp(self):
        self.ep=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')
        self.ep={**self.ep,'toolkit':'plain'}
        self.bound=reserve(render(self.ep,[],10,'action'),'action','plain')
        self.real=(ROOT/'fixtures/real-claude-envelope.json').read_text()

    def test_exact_saved_dns_bytes_are_not_limit_generation_or_unparseable(self):
        raw=c.read(ROOT/'fixtures/stopped-claude-raw.json')
        preserved=ROOT/'revisions/r2/saved/collection/episodes/claude-s00-notification-r50-check/0.raw.json'
        self.assertEqual((ROOT/'fixtures/stopped-claude-raw.json').read_bytes(),preserved.read_bytes())
        e=c.read(ROOT/'fixtures/stopped-claude-raw.json');envelope=c.provider_envelope(e,'claude')[0]
        self.assertEqual(c.usage(envelope,'claude'),(0,0))
        self.assertEqual(envelope['total_cost_usd'],0)
        self.assertIsNone(envelope['api_error_status'])
        self.assertEqual(envelope['modelUsage'],{})
        self.assertIn('ENOTFOUND',envelope['result'])
        self.assertEqual(r.classify(raw)['class'],'DEFINITE NON-START')
        with self.assertRaises(c.Stop):c.decode(raw,self.ep,'action',self.bound)

    def test_real_external_two_turn_fixture_and_portable_copy(self):
        sources=[self.real]
        if EXTERNAL.exists():
            self.assertEqual(EXTERNAL.read_bytes(),self.real.encode())
            sources.append(EXTERNAL.read_text())
        for source in sources:
            raw={'stdout':source,'stderr':'','returncode':0}
            self.assertEqual(c.decode(raw,self.ep,'action',self.bound),{'op':'send','job':1,'key':None})
            self.assertEqual(a.checked_value(raw,self.ep,'action',self.bound,False),{'op':'send','job':1,'key':None})

    def shapes(self):
        real=c.read(ROOT/'fixtures/real-claude-envelope.json')
        for label, changes, remove, rc in [
            ('max-tokens',{'is_error':True,'subtype':'error_during_execution','stop_reason':None,'usage':{**real['usage'],'output_tokens':512}},['structured_output'],1),
            ('refusal',{'is_error':True,'subtype':'success','stop_reason':'refusal','result':'I cannot comply'},['structured_output','modelUsage'],1),
            ('nonzero-input-refusal',{'is_error':True,'stop_reason':None,'usage':{**real['usage'],'output_tokens':0}},['structured_output','modelUsage'],1),
            ('schema-rejection',{'is_error':True,'subtype':'error_max_structured_output_retries'},['structured_output'],1),
            ('invalid-structured-output',{'structured_output':{}},[],0),
            ('missing-structured-output',{},['structured_output'],0),
            ('error-max-turns',{'is_error':True,'subtype':'error_max_turns'},['structured_output'],1),
            ('error-max-budget',{'is_error':True,'subtype':'error_max_budget_usd'},['structured_output'],1),
        ]:
            e=copy.deepcopy(real);e.update(changes)
            for k in remove:e.pop(k,None)
            yield label,{'stdout':canonical(e),'stderr':'','returncode':rc}

    def test_generated_shapes_fail_episode_and_continue_cohort(self):
        for label,raw in self.shapes():
            with self.subTest(shape=label):
                self.assertEqual(r.classify(raw)['class'],'MODEL-CAUSED')
                with self.assertRaises(ModelOutputError):c.decode(raw,self.ep,'action',self.bound)
                with self.assertRaises(ModelOutputError):a.checked_value(raw,self.ep,'action',self.bound,False)
            with self.subTest(integration=label),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);bad={**self.ep,'id':'bad'};good={**self.ep,'id':'next'}
                c.save(root/'config/episodes.json',[bad,good])
                class Provider(Fake):
                    def generate(inner,ep,*args):
                        if ep['id']=='bad':inner.calls+=1;return raw
                        return super().generate(ep,*args)
                p=Provider();c.collect(root,'claude',fake_transport=p)
                base=root/'collection'
                self.assertFalse((base/'STOP.json').exists())
                self.assertTrue(c.read(base/'episodes/next/episode.json')['trajectory_valid'])
                self.assertEqual(c.read(base/'episodes/bad/episode.json')['attempted_calls'],1)
                self.assertEqual(p.calls,7)
                self.assertEqual(a.reconcile(root,base)['status'],'RECONCILED')
                rows,_=a.load_rows(root,base);self.assertFalse(rows[0]['valid']);self.assertTrue(rows[1]['valid'])

    def test_limit_without_identity_is_nonstart_and_transport_stays_fatal(self):
        e=c.read(ROOT/'fixtures/usage-limit-envelope.json');e.pop('modelUsage',None)
        raw={'stdout':canonical(e),'returncode':1,'stderr':''}
        self.assertEqual(r.classify(raw)['class'],'USAGE-LIMIT NON-START')
        raw={'stdout':'{unparseable','returncode':None,'transport_error':'timeout'}
        self.assertEqual(r.classify(raw)['class'],'GENUINE TRANSPORT UNCERTAINTY')
        with self.assertRaises(c.Stop):c.decode(raw,self.ep,'action',self.bound)

    def test_generated_error_explicit_wrong_model_or_external_activity_still_blocks(self):
        raw=next(self.shapes())[1]
        for change in ({'modelUsage':{'wrong-model':{}}},{'subagent_stats':{'spawned':1}}):
            e=c.provider_envelope(raw,'claude')[0];e.update(change);bad={**raw,'stdout':canonical(e)}
            with self.assertRaises(c.Stop):c.decode(bad,self.ep,'action',self.bound)

    def test_prefixes_allow_append_and_detect_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prefix=b'{"event":"old"}\n';c.save(root/'revisions/r2/preservation.json',{
                'prefixes':{'collection/ledger.jsonl':{'snapshot':'prefix.jsonl','bytes':len(prefix),'sha256':sha(prefix)}},'files':{},'parents':{}})
            (root/'prefix.jsonl').write_bytes(prefix);(root/'collection').mkdir()
            ledger=root/'collection/ledger.jsonl';ledger.write_bytes(prefix+b'{"event":"new"}\n')
            r.verify_prefixes(root);ledger.write_bytes(b'X'+ledger.read_bytes()[1:])
            with self.assertRaises(ValueError):r.verify_prefixes(root)

    def test_dns_clearance_retains_stop_and_ledgers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.save(root/'collection/STOP.json',{'reason':'transport failure or uncertain start'})
            fixture=root/'fixtures/stopped-claude-raw.json';fixture.parent.mkdir();fixture.write_bytes((ROOT/'fixtures/stopped-claude-raw.json').read_bytes())
            old=(root/'collection/STOP.json').read_bytes()
            with patch('rg_freeze.verify',return_value='r2-digest'),patch('rg_revision.verify_prefixes',return_value={'prefixes':{}}):
                record=r.clearance(root)
                self.assertFalse(record['cleared']);self.assertEqual(record['status'],'UNKNOWN')
                self.assertEqual(r.clearance(root),record)
            self.assertEqual((root/'collection/STOP.json').read_bytes(),old)
            self.assertFalse((root/'collection/ledger.jsonl').exists())

    def test_r2_freeze_attestation_preserves_parent_receipt_and_old_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root);f.revise(root)
            def fake_git(cmd,**kwargs):
                if cmd[1:]==['rev-parse','HEAD']:return 'a'*40+'\n'
                if cmd[1:]==['remote','get-url','origin']:return 'https://github.com/Robin84Bran/research.git\n'
                if cmd[1]=='show':return (root/cmd[2].split(':receipt-gap/v0.2/')[1]).read_bytes()
                if cmd[1]=='ls-remote':return 'a'*40+'\trefs/heads/test\n'
                raise AssertionError(cmd)
            def attest(name,event_name):
                c.save(root/event_name,{'activity_type':'push','after':'a'*40,'ref':'refs/heads/test',
                       'timestamp':c.read(root/name)['created_at'],'id':event_name})
                with patch('rg_freeze.subprocess.check_output',side_effect=fake_git):
                    return f.attest(root,root/event_name,'a'*40,'receipt-gap/v0.2',root,name)
            old_digest=attest('freeze-r1.json','old-event.json')
            receipt=(root/'collection/push.json').read_bytes()
            c.save(root/'collection/episodes/old/0.start.json',{'id':'old-0','started_at':c.now(),'freeze_sha256':old_digest})
            parents={n:sha((root/n).read_bytes()) for n in ('freeze.json','freeze-r1.json')}
            c.save(root/'revisions/r2/preservation.json',{'parents':parents,'prefixes':{},'files':{}})
            digest=f.revise_r2(root)
            self.assertEqual(c.read(root/'freeze-r2.json')['parents'],parents)
            self.assertEqual(attest('freeze-r2.json','new-event.json'),digest)
            self.assertEqual((root/'collection/push.json').read_bytes(),receipt)
            self.assertEqual(c.push_gate(root,'freeze-r2.json'),digest)
            a.check_saved_push(root,root/'collection',c.read(root/'collection/push-r2.json'),digest)
            self.assertFalse(r.stop_cleared(root,root/'collection','freeze-r2.json'))
            with self.assertRaises(FileExistsError):f.revise_r2(root)
            r2_receipt=(root/'collection/push-r2.json').read_bytes()
            c.save(root/'collection/episodes/r2/0.start.json',{'id':'r2-0','started_at':c.now(),'freeze_sha256':digest})
            r3_digest=f.revise_r3(root)
            self.assertEqual(attest('freeze-r3.json','r3-event.json'),r3_digest)
            self.assertEqual(c.push_gate(root,'freeze-r3.json'),r3_digest)
            self.assertEqual((root/'collection/push-r2.json').read_bytes(),r2_receipt)
            self.assertEqual((root/'collection/push.json').read_bytes(),receipt)
            a.check_saved_push(root,root/'collection',c.read(root/'collection/push-r3.json'),r3_digest)

    def test_saved_dns_is_pending_and_excluded_from_model_failure_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'collection';ep={**self.ep,'id':'dns'}
            c.save(root/'config/episodes.json',[ep]);c.save(base/'OFFLINE-FAKE.json',{'real_model_calls':0})
            raw=c.read(ROOT/'fixtures/stopped-claude-raw.json')
            class Saved(Fake):
                def generate(inner,*args):return raw
            c.run_episode(ep,Saved(),base,c.Ledger(base/'ledger.jsonl'),c.ActiveTime(base/'time.jsonl',10000),'OFFLINE-FAKE',True)
            rows,_=a.load_rows(root,base)
            self.assertTrue(rows[0]['operational_pending']);self.assertIsNone(rows[0]['Dstar'])
            output=root/'analysis.json'
            with patch('sys.argv',['rg_analysis.py','--root',str(root),'--output',str(output)]):a.main()
            result=c.read(output);self.assertEqual(result['pending_dns_nonstart_episodes'],['dns'])
            self.assertEqual(result['pending_usage_limit_episodes'],[])
            self.assertEqual(result['cells'],{});self.assertIsNone(result['technical_acceptance'])

    def test_forged_clearance_cannot_reclassify_saved_dns_as_model_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'collection'
            c.save(base/'STOP.json',{'reason':'DNS'})
            target=root/'fixtures/stopped-claude-raw.json';target.parent.mkdir()
            target.write_bytes((ROOT/'fixtures/stopped-claude-raw.json').read_bytes())
            c.save(base/'clearance-r2.json',{'cleared':True,'status':'PASS','freeze_sha256':'r2',
                'stop_sha256':sha((base/'STOP.json').read_bytes()),'disposition':{'class':'MODEL-CAUSED'}})
            with patch('rg_freeze.verify',return_value='r2'),patch('rg_revision.verify_prefixes'):
                self.assertFalse(r.stop_cleared(root,base,'freeze-r2.json'))
