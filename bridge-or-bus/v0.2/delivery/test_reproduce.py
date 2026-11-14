"""Boundary checks for the additive fresh-clone adapter; no empirical analysis."""
import tempfile
from pathlib import Path
import unittest
from reproduce import check_hashes, digest, transient


class PreservationBoundary(unittest.TestCase):
    def test_absent_lock_requires_fresh_mode_and_keeps_saved_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            files = {'collection/cost.lock': digest(b'')}
            with self.assertRaises(ValueError):
                check_hashes(root, files)
            self.assertEqual(check_hashes(root, files, True), files)

    def test_missing_data_and_changed_present_lock_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(ValueError):
                check_hashes(root, {'raw.json': digest(b'')}, True)
            (root / 'cost.lock').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                check_hashes(root, {'cost.lock': digest(b'')}, True)

    def test_symlinks_cannot_be_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'cost.lock').symlink_to(root / 'missing')
            with self.assertRaises(ValueError):
                check_hashes(root, {'cost.lock': digest(b'')}, True)

    def test_only_documented_transient_patterns(self):
        for n in ['__pycache__/a.pyc', '.git/config', 'a/.DS_Store', 'a/cost.lock']:
            self.assertTrue(transient(n))
        for n in ['data.json', 'a/lock.json', '.gitignore', 'bob_analysis.py']:
            self.assertFalse(transient(n))


if __name__ == '__main__':
    unittest.main(verbosity=2)
