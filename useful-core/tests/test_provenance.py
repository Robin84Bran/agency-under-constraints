import copy
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uc_core import canonical,sha
from uc_store import read,save,Stop
from uc_freeze import prepare,freeze,verify,attest,push_record,push_gate

COMMIT='a'*40


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.root=self.base/'project';self.root.mkdir();self.clone=self.base/'clone';self.clone.mkdir()
        (self.root/'script.py').write_text('# frozen fixture\n')
        prepare(self.root)
        with patch('uc_freeze.identities',return_value={}):self.digest=freeze(self.root)
        self.event=dict(activity_type='push',id=1234,after=COMMIT,ref='refs/heads/main',timestamp=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=.001)).isoformat())
        # Simulated server is just after freeze, in the past by use time.
        import time;time.sleep(.003)
        self.source=self.base/'activity.json';self.raw=(canonical(self.event)+'\n').encode();self.source.write_bytes(self.raw)

    def git(self,cmd,**kwargs):
        self.assertEqual(Path(kwargs['cwd']),self.clone)
        op=cmd[1]
        if op=='rev-parse':return COMMIT+'\n'
        if op=='remote':return 'git@github.com:Robin84Bran/research.git\n'
        if op=='ls-remote':return COMMIT+'\trefs/heads/main\n'
        if op=='show':
            prefix=COMMIT+':useful-core/'
            self.assertTrue(cmd[2].startswith(prefix));return (self.root/cmd[2][len(prefix):]).read_bytes()
        self.fail('unexpected Git operation')

    def attest(self):return attest(self.root,self.source,COMMIT,'useful-core',self.clone)

    def test_activity_record_required_fields(self):
        self.assertEqual(push_record(self.event,COMMIT),('refs/heads/main',self.event['timestamp']))
        for update in ({'activity_type':'force_push'},{'after':'b'*40},{'ref':'main'},{'ref':'refs/heads/'},{'id':None},{'timestamp':'2026-11-11T10:00:00'},{'timestamp':'2999-01-01T00:00:00Z'}):
            with self.subTest(update=update),self.assertRaises(Stop):push_record(dict(self.event,**update),COMMIT)
        for key in ('id','after','ref','timestamp','activity_type'):
            bad=dict(self.event);del bad[key]
            with self.assertRaises(Stop):push_record(bad,COMMIT)
        with self.assertRaises(Stop):push_record(self.event,'a'*39)
        with self.assertRaises(Stop):push_record(dict(type='PushEvent'),COMMIT)

    def test_attestation_checks_all_blobs_and_writes_here_only(self):
        with patch('uc_freeze.subprocess.check_output',side_effect=self.git):self.assertEqual(self.attest(),self.digest)
        self.assertEqual((self.root/'collection/push-event.json').read_bytes(),self.raw)
        self.assertEqual(list(self.clone.iterdir()),[]);self.assertEqual(push_gate(self.root),self.digest)
        receipt=read(self.root/'collection/push.json');self.assertEqual(receipt['source_api'],'/repos/Robin84Bran/research/activity');self.assertEqual(receipt['repo_path'],'useful-core')
        with patch('uc_freeze.subprocess.check_output',side_effect=self.git),self.assertRaises(FileExistsError):self.attest()

    def test_rejects_wrong_committed_input(self):
        def mismatch(cmd,**kwargs):
            if cmd[1]=='show' and cmd[2].endswith('script.py'):return b'changed'
            return self.git(cmd,**kwargs)
        with patch('uc_freeze.subprocess.check_output',side_effect=mismatch),self.assertRaises(Stop):self.attest()
        self.assertFalse((self.root/'collection/push.json').exists())

    def test_rejects_wrong_origin_and_remote_head(self):
        for op,value in [('remote','git@github.com:other/research.git\n'),('ls-remote','b'*40+'\trefs/heads/main\n'),('rev-parse','b'*40+'\n')]:
            def mismatch(cmd,**kwargs):return value if cmd[1]==op else self.git(cmd,**kwargs)
            with self.subTest(op=op),patch('uc_freeze.subprocess.check_output',side_effect=mismatch),self.assertRaises(Stop):self.attest()

    def test_gate_detects_freeze_source_and_start_changes(self):
        with patch('uc_freeze.subprocess.check_output',side_effect=self.git):self.attest()
        save(self.root/'collection/episodes/fake/1.start.json',dict(freeze_sha256=self.digest,started_at='2026-01-01T00:00:00Z'))
        with self.assertRaises(Stop):push_gate(self.root)
        source=self.root/'script.py';source.write_text('changed')
        with self.assertRaises(Stop):verify(self.root)

    def test_inventory_added_source_and_symlink_rejected(self):
        extra=self.root/'extra.py';extra.write_text('extra')
        with self.assertRaises(Stop):verify(self.root)
        extra.unlink();extra.symlink_to(self.root/'script.py')
        with self.assertRaises(Stop):verify(self.root)

    def test_no_refreeze_or_nonseparate_clone(self):
        with patch('uc_freeze.identities',return_value={}),self.assertRaises(FileExistsError):freeze(self.root)
        with self.assertRaises(Stop):attest(self.root,self.source,COMMIT,'useful-core',self.root)
        with self.assertRaises(Stop):attest(self.root,self.source,COMMIT,'../useful-core',self.clone)
