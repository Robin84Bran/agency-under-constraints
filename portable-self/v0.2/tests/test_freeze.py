import datetime as dt
import io
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, canonical, sha
from ps_io import Stop, read
from ps_freeze import freeze, verify, attest, push_gate, push_record, activity_records

class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'study';self.root.mkdir();self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        for folder in ('config','evidence/models'):
            shutil.copytree(ROOT/folder,self.root/folder)
        shutil.copyfile(ROOT/'evidence/local-identity.json',self.root/'evidence/local-identity.json')
        self.commit='a'*40
        self.event={'activity_type':'push','id':123,'after':self.commit,'ref':'refs/heads/codex/portable-self','timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    def tearDown(self): self.tmp.cleanup()
    def freeze(self):
        h=freeze(self.root)
        # Test-only clock positioning. This is a synthetic GitHub fixture, never a real receipt.
        self.event['timestamp']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(microseconds=1)).isoformat()
        return h
    def archive(self):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w') as tar:
            for n in list(read(self.root/'freeze.json')['files'])+['freeze.json']:
                raw=(self.root/n).read_bytes();info=tarfile.TarInfo('portable-self/'+n);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        return data.getvalue()
    def subprocess(self,cmd,**kw):
        if cmd[:4]==['git','remote','get-url','origin']: return b'https://github.com/Robin84Bran/research.git\n'
        if cmd[:3]==['git','rev-parse','HEAD']: return (self.commit+'\n').encode()
        if cmd[0:2]==['git','archive']: return self.archive()
        if cmd[0:2]==['git','ls-remote']: return (self.commit+'\t'+self.event['ref']+'\n').encode()
        if cmd[:2]==['gh','api']:
            self.assertIn('/repos/Robin84Bran/research/activity',cmd);self.assertIn('GET',cmd)
            return canonical([[self.event]]).encode()
        raise AssertionError(cmd)
    def test_freeze_create_once_hash_binding(self):
        h=self.freeze();self.assertEqual(h,verify(self.root))
        with self.assertRaises(Stop): freeze(self.root)
        path=self.root/'config/prompts.json';path.write_text('{}')
        with self.assertRaises(Stop): verify(self.root)
    def test_inventory_addition_detected(self):
        self.freeze();(self.root/'extra.py').write_text('# extra')
        with self.assertRaises(Stop): verify(self.root)
    def test_symlinks_blocked(self):
        (self.root/'bad').symlink_to(ROOT/'ps_core.py')
        with self.assertRaises(Stop): freeze(self.root)
    def test_activity_attest_separate_clone_target_owns_receipt(self):
        self.freeze()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess):
            attest(self.root,self.clone,'portable-self',self.commit)
        self.assertTrue((self.root/'collection/push.json').is_file());self.assertFalse((self.clone/'collection').exists())
        self.assertEqual(push_gate(self.root),verify(self.root))
    def test_full_activity_response_is_preserved(self):
        self.freeze()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.commit)
        receipt=read(self.root/'collection/push.json');raw=(self.root/'collection/push-activity.json').read_bytes()
        self.assertEqual(sha(raw),receipt['activity_sha256']);self.assertEqual(activity_records(read(self.root/'collection/push-activity.json')),[self.event])
    def test_events_endpoint_not_accepted(self):
        self.freeze()
        e={'type':'PushEvent','id':1,'created_at':self.event['timestamp'],'payload':{'head':self.commit,'ref':self.event['ref']}}
        with self.assertRaises(Stop): push_record(e,self.commit)
    def test_wrong_after_branch_timezone_or_id_rejected(self):
        self.freeze()
        for field,value in [('after','b'*40),('ref','main'),('timestamp','2026-11-11T00:00:00'),('id',None)]:
            e={**self.event,field:value}
            with self.subTest(field=field),self.assertRaises(Stop): push_record(e,self.commit)
    def test_wrong_origin_blocks_attestation(self):
        self.freeze()
        def bad(cmd,**kw): return b'https://github.com/elsewhere/research.git\n' if cmd[:4]==['git','remote','get-url','origin'] else self.subprocess(cmd,**kw)
        with patch('ps_freeze.subprocess.check_output',side_effect=bad),self.assertRaises(Stop): attest(self.root,self.clone,'portable-self',self.commit)
        self.assertFalse((self.root/'collection/push.json').exists())
    def test_remote_ref_mismatch_blocks_attestation(self):
        self.freeze()
        def bad(cmd,**kw): return b'b'*40+b'\t'+self.event['ref'].encode()+b'\n' if cmd[:2]==['git','ls-remote'] else self.subprocess(cmd,**kw)
        with patch('ps_freeze.subprocess.check_output',side_effect=bad),self.assertRaises(Stop): attest(self.root,self.clone,'portable-self',self.commit)
    def test_no_activity_match_blocks_attestation(self):
        self.freeze()
        def bad(cmd,**kw): return b'[[]]' if cmd[:2]==['gh','api'] else self.subprocess(cmd,**kw)
        with patch('ps_freeze.subprocess.check_output',side_effect=bad),self.assertRaises(Stop): attest(self.root,self.clone,'portable-self',self.commit)
    def test_receipt_tamper_or_early_start_blocks_dispatch(self):
        self.freeze()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.commit)
        from ps_io import save
        save(self.root/'collection/episodes/test/0.start.json',{'freeze_sha256':verify(self.root),'started_at':'2020-01-01T00:00:00Z'})
        with self.assertRaises(Stop): push_gate(self.root)
