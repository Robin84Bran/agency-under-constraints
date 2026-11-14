"""Guard tests for the new transient adapter, using tiny synthetic inventories only."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('uc_delivery_reproduce',HERE/'reproduce.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
import uc_d2
from uc_core import sha
from uc_store import Stop


class TransientGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.original_baseline=uc_d2.baseline;self.original_read=uc_d2.read
        self.base=self.root/'collection';(self.base/'delivery').mkdir(parents=True)
        self.lockpin={'bytes':0,'sha256':sha(b'')}
        self.normalpin={'bytes':3,'sha256':sha(b'yes')}
        (self.base/'evidence.json').write_bytes(b'yes')
        b=self.root/uc_d2.BASELINE;b.parent.mkdir(parents=True)
        b.write_text(json.dumps({'files':{'collector.lock':self.lockpin,'evidence.json':self.normalpin}}))
        self.declare({'collection/collector.lock':self.lockpin})

    def declare(self,files):
        (self.base/'delivery/transient-exclusions.json').write_text(json.dumps({'files':files}))

    def tearDown(self):
        uc_d2.baseline=self.original_baseline;uc_d2.read=self.original_read;self.tmp.cleanup()

    def check(self):
        return uc_d2.baseline(self.root,self.base)

    def test_absent_declared_lock_only_is_skipped(self):
        omitted=adapter.fresh_clone_mode(self.root)
        self.assertEqual(omitted,{'collection/collector.lock':self.lockpin})
        self.check();self.assertIs(uc_d2.read,self.original_read)
        self.assertFalse((self.base/'collector.lock').exists())

    def test_missing_normal_evidence_is_fatal(self):
        adapter.fresh_clone_mode(self.root);(self.base/'evidence.json').unlink()
        with self.assertRaises(FileNotFoundError):self.check()
        self.assertIs(uc_d2.read,self.original_read)

    def test_modified_normal_evidence_is_fatal(self):
        adapter.fresh_clone_mode(self.root);(self.base/'evidence.json').write_bytes(b'bad')
        with self.assertRaises(Stop):self.check()

    def test_undeclared_lock_is_fatal(self):
        self.declare({})
        with self.assertRaises(Stop):adapter.fresh_clone_mode(self.root)

    def test_sidecar_hash_must_match_frozen_pin(self):
        self.declare({'collection/collector.lock':{'bytes':0,'sha256':'0'*64}})
        with self.assertRaises(Stop):adapter.fresh_clone_mode(self.root)

    def test_present_lock_is_still_verified(self):
        (self.base/'collector.lock').write_bytes(b'changed')
        self.assertEqual(adapter.fresh_clone_mode(self.root),{})
        with self.assertRaises(Stop):self.check()

    def test_declared_normal_file_cannot_be_exempted(self):
        self.declare({'collection/collector.lock':self.lockpin,'collection/evidence.json':self.normalpin})
        (self.base/'evidence.json').unlink();adapter.fresh_clone_mode(self.root)
        with self.assertRaises(FileNotFoundError):self.check()

if __name__=='__main__':unittest.main(verbosity=2)
