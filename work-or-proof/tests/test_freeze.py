import json
import tempfile
import unittest
from pathlib import Path

from wop_freeze import make_freeze, verify_freeze, write_new


class FreezeTests(unittest.TestCase):
    def fixture(self, path):
        (path / 'imported').mkdir()
        write_new(path / 'imported/reconciliation.json', {'status': 'PASS'})
        (path / 'PROTOCOL.md').write_text('APPROVED')
        (path / 'agreement_sizing.json').write_text('{}')
        (path / 'survey_inventory.json').write_text('{}')

    def test_freeze_exclusive_and_tamper_detected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            root = Path(tmp)
            self.fixture(root)
            digest = make_freeze(root)
            self.assertEqual(len(digest), 64)
            verify_freeze(root)
            with self.assertRaises(FileExistsError):
                make_freeze(root)
            (root / 'PROTOCOL.md').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                verify_freeze(root)

    def test_added_code_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            root = Path(tmp)
            self.fixture(root)
            make_freeze(root)
            (root / 'new.py').write_text('')
            with self.assertRaisesRegex(ValueError, 'inventory'):
                verify_freeze(root)

    def test_failed_reconciliation_blocks_freeze(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            root = Path(tmp)
            (root / 'imported').mkdir()
            write_new(root / 'imported/reconciliation.json', {'status': 'UNKNOWN'})
            with self.assertRaisesRegex(ValueError, 'PASS'):
                make_freeze(root)

    def test_exclusive_evidence_write(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            path = Path(tmp) / 'call.json'
            write_new(path, {'raw': 'first'})
            with self.assertRaises(FileExistsError):
                write_new(path, {'raw': 'second'})
            self.assertEqual(json.loads(path.read_text())['raw'], 'first')
