from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_core import canonical, sha
from trl_io import Stop, read, save, now
from trl_freeze import freeze, verify, tested_inputs, attest, push_gate, select_event
from trl_journal import Journal, prefix


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.commit='a'*40;self.ref='refs/heads/main'
        (self.root/'PROTOCOL.md').write_text('# Protocol v0.2 AGREED\n')
        save(self.root/'config/settings.json',{'fixed':1})
        files=tested_inputs(self.root)
        save(self.root/'evidence/test-report.json',{'status':'PASS','failures':0,'errors':0,'skipped':0,'tested_files':files})
        save(self.root/'evidence/offline.json',{'status':'PASS','local_episodes':900,'model_calls':0,'tested_files':files})
        with patch('trl_freeze.now',return_value='2020-01-01T00:00:00+00:00'):
            self.digest=freeze(self.root)
        self.event={'id':'server-1','activity_type':'push','after':self.commit,
                    'ref':self.ref,'timestamp':'2020-01-02T00:00:00Z'}
        save(self.root/'build/event.json',self.event)
        self.git_calls=[]

    def git(self,args,**kwargs):
        self.git_calls.append(args)
        if args[1:]==['rev-parse','HEAD']: return (self.commit+'\n').encode()
        if args[1:]==['remote','get-url','origin']: return b'https://github.com/Robin84Bran/research.git\n'
        if args[1]=='show':
            name=args[2].split(':three-rules-one-lunch/v0.2/',1)[1]
            return (self.root/name).read_bytes()
        if args[1]=='ls-remote': return (self.commit+'\t'+self.ref+'\n').encode()
        raise AssertionError(args)

    def attest(self,git=None):
        with patch('trl_freeze.subprocess.check_output',side_effect=git or self.git):
            return attest(self.root,self.root/'build/event.json',self.commit,'three-rules-one-lunch/v0.2',self.root/'clone')

    def test_activity_commit_all_blobs_remote_ref_and_prefixes(self):
        self.assertEqual(self.attest(),self.digest)
        self.assertEqual(push_gate(self.root),self.digest)
        self.assertEqual(read(self.root/'collection/push.json')['source_api'],'/repos/Robin84Bran/research/activity')
        shown=[x[2] for x in self.git_calls if x[1]=='show']
        self.assertEqual(len(shown),len(read(self.root/'freeze.json')['files'])+1)
        with self.assertRaises(Stop): self.attest()

    def test_wrong_commit_event_rejected_before_git(self):
        self.event['after']='b'*40
        (self.root/'build/event.json').write_text(canonical(self.event))
        with patch('trl_freeze.subprocess.check_output',side_effect=AssertionError('must not run Git')):
            with self.assertRaises(Stop): self.attest()

    def test_freeze_blob_omitted_or_modified_rejected(self):
        def corrupted(args,**kwargs):
            value=self.git(args,**kwargs)
            return b'corrupt' if args[1]=='show' and args[2].endswith('/freeze.json') else value
        with self.assertRaises(Stop): self.attest(corrupted)

    def test_wrong_origin_and_remote_ref_rejected(self):
        for target in ('origin','ref'):
            def wrong(args,**kwargs):
                result=self.git(args,**kwargs)
                if target=='origin' and args[1]=='remote': return b'https://example.com/other.git\n'
                if target=='ref' and args[1]=='ls-remote': return ('b'*40+'\t'+self.ref+'\n').encode()
                return result
            with self.assertRaises(Stop): self.attest(wrong)

    def test_frozen_input_addition_or_change_rejected(self):
        (self.root/'new-code.py').write_text('changed')
        with self.assertRaises(Stop): verify(self.root)

    def test_starts_before_attestation_rejected(self):
        save(self.root/'collection/episodes/e/calls/c/0001/start.json',{'id':'bad'})
        with self.assertRaises(Stop): self.attest()

    def test_mutated_event_or_receipt_rejected(self):
        self.attest();p=self.root/'collection/push-event.raw.json'
        p.write_text(canonical(dict(self.event,id='changed')))
        with self.assertRaises(Stop): push_gate(self.root)

    def test_attested_ledger_prefix_append_and_torn_tail(self):
        self.attest();j=Journal(self.root/'collection/dispatch.jsonl')
        j.event(event='start',id='a',freeze_sha256=self.digest)
        self.assertEqual(push_gate(self.root),self.digest)
        with (self.root/'collection/dispatch.jsonl').open('ab') as f: f.write(b'torn')
        with self.assertRaises(Stop): push_gate(self.root)

    def test_paginated_activity_selects_exact_commit(self):
        save(self.root/'build/pages.json',[[dict(self.event,after='b'*40)],[self.event]])
        select_event(self.root/'build/pages.json',self.commit,self.root/'build/selected.json')
        self.assertEqual(read(self.root/'build/selected.json'),self.event)

    def test_push_must_follow_freeze(self):
        (self.root/'build/event.json').write_text(canonical(dict(self.event,timestamp='2019-01-01T00:00:00Z')))
        with self.assertRaises(Stop): self.attest()


if __name__=='__main__': unittest.main()
