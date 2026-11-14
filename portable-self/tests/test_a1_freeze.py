import datetime as dt
import io
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, canonical, sha
from ps_io import Stop, read, save
from ps_freeze import freeze_a1, verify, attest, push_gate, active_manifest, ORIGINAL_SHA256


class A1FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'study';self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('freeze-a1.json','__pycache__','collection','.git'))
        self.commit='a'*40
        self.event={'activity_type':'push','id':123,'after':self.commit,'ref':'refs/heads/codex/portable-self',
                    'timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    def tearDown(self): self.tmp.cleanup()
    def seal(self):
        h=freeze_a1(self.root)
        self.event['timestamp']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(microseconds=1)).isoformat()
        return h
    def archive(self,omit=None,bad=None):
        data=io.BytesIO();f=read(active_manifest(self.root))
        with tarfile.open(fileobj=data,mode='w') as tar:
            for n in list(f['files'])+['freeze.json','freeze-a1.json']:
                if n==omit: continue
                raw=b'bad' if n==bad else (self.root/n).read_bytes();info=tarfile.TarInfo('portable-self/'+n);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
        return data.getvalue()
    def subprocess(self,cmd,**kw):
        if cmd[:4]==['git','remote','get-url','origin']: return b'https://github.com/Robin84Bran/research.git\n'
        if cmd[:3]==['git','rev-parse','HEAD']: return (self.commit+'\n').encode()
        if cmd[:2]==['git','archive']: return self.archive()
        if cmd[:2]==['git','ls-remote']: return (self.commit+'\t'+self.event['ref']+'\n').encode()
        if cmd[:2]==['gh','api']:
            self.assertIn('/repos/Robin84Bran/research/activity',cmd);self.assertIn('GET',cmd)
            return b' \n'+canonical([[self.event]]).encode()+b'\n'
        raise AssertionError(cmd)
    def test_a1_binds_unchanged_parent_and_is_create_once(self):
        parent=(self.root/'freeze.json').read_bytes();h=self.seal()
        self.assertEqual(parent,(self.root/'freeze.json').read_bytes());self.assertEqual(sha(parent),ORIGINAL_SHA256)
        self.assertEqual(read(self.root/'freeze-a1.json')['parent_freeze_sha256'],ORIGINAL_SHA256)
        self.assertEqual(h,verify(self.root))
        with self.assertRaises(Stop): freeze_a1(self.root)
    def test_a1_rejects_parent_original_baseline_and_scientific_drift(self):
        for name in ('freeze.json','config/prompts.json','ps_core.py','revisions/a1/original/ps_collect.py'):
            with self.subTest(name=name):
                p=self.root/name;old=p.read_bytes();p.write_bytes(old+b'\n')
                with self.assertRaises(Stop): freeze_a1(self.root)
                p.write_bytes(old)
    def test_a1_rejects_undeclared_input_and_prior_collection(self):
        p=self.root/'other.py';p.write_text('# other')
        with self.assertRaises(Stop): freeze_a1(self.root)
        p.unlink()  # Task-owned temporary test fixture only.
        save(self.root/'collection/episodes/test/0.start.json',{})
        with self.assertRaises(Stop): freeze_a1(self.root)
    def test_sealed_a1_changed_input_and_parent_binding_rejected(self):
        self.seal();p=self.root/'ps_collect.py';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(Stop): verify(self.root)
    def test_a1_genuine_shape_mock_raw_retention_both_freezes_and_start_order(self):
        h=self.seal()
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.commit)
        self.assertEqual(push_gate(self.root),h);self.assertFalse((self.clone/'collection').exists())
        raw=(self.root/'collection/push-activity.json').read_bytes();self.assertTrue(raw.startswith(b' \n'))
        self.assertEqual(read(self.root/'collection/push.json')['activity_sha256'],sha(raw))
        save(self.root/'collection/episodes/test/0.start.json',{'freeze_sha256':h,'started_at':dt.datetime.now(dt.timezone.utc).isoformat()})
        self.assertEqual(push_gate(self.root),h)
        save(self.root/'collection/episodes/test/1.start.json',{'freeze_sha256':ORIGINAL_SHA256,'started_at':dt.datetime.now(dt.timezone.utc).isoformat()})
        with self.assertRaises(Stop): push_gate(self.root)
    def test_a1_attester_rejects_wrong_committed_parent_and_active_manifest(self):
        self.seal()
        for name in ('freeze.json','freeze-a1.json','ps_collect.py'):
            archive=self.archive(bad=name)
            def bad(cmd,**kw): return archive if cmd[:2]==['git','archive'] else self.subprocess(cmd,**kw)
            with self.subTest(name=name),patch('ps_freeze.subprocess.check_output',side_effect=bad),self.assertRaises(Stop): attest(self.root,self.clone,'portable-self',self.commit)
    def test_push_must_follow_a1_and_receipt_is_create_once(self):
        self.seal();new=self.event['timestamp'];self.event['timestamp']=read(self.root/'freeze.json')['created_at']
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess),self.assertRaises(Stop): attest(self.root,self.clone,'portable-self',self.commit)
        self.event['timestamp']=new
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess): attest(self.root,self.clone,'portable-self',self.commit)
        with patch('ps_freeze.subprocess.check_output',side_effect=self.subprocess),self.assertRaises(FileExistsError): attest(self.root,self.clone,'portable-self',self.commit)
    def test_parent_binding_field_rejected(self):
        self.seal();p=self.root/'freeze-a1.json';f=read(p);f['parent_freeze_sha256']='0'*64;p.write_text(canonical(f))
        with self.assertRaises(Stop): verify(self.root)
