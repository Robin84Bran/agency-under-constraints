"""Offline D1 provenance checks. Git is mocked; no models or network are used."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from rg_collect import Stop, push_gate, read, save
from rg_core import ROOT, canonical, sha
from rg_freeze import attest, freeze, freeze_d1, main, prepare, push_record, verify


COMMIT = '059a0258b86359d2564fd1e09bf4a4867b23353b'
ACTIVITY = {'activity_type':'push', 'after':COMMIT, 'before':'4'*40,
            'ref':'refs/heads/main', 'timestamp':'2026-11-11T09:13:51Z', 'id':49834798845}
EVENT = {'type':'PushEvent', 'repo':{'name':'Robin84Bran/research'},
         'payload':{'head':COMMIT, 'ref':ACTIVITY['ref']},
         'created_at':ACTIVITY['timestamp'], 'id':'server-event-id'}


class PushRecordTests(unittest.TestCase):
    def test_both_server_shapes(self):
        for event in (ACTIVITY, EVENT):
            self.assertEqual(push_record(event, COMMIT), (ACTIVITY['ref'], ACTIVITY['timestamp']))
        event = copy.deepcopy(EVENT)
        event['payload']['after'] = event['payload'].pop('head')
        self.assertEqual(push_record(event, COMMIT)[0], ACTIVITY['ref'])

    def test_activity_rejects_wrong_or_missing_required_fields(self):
        cases = [{'activity_type':'force_push'}, {'after':'b'*40}, {'ref':None}, {'ref':''},
                 {'ref':'main'}, {'ref':'refs/heads/'}, {'timestamp':None}, {'timestamp':'invalid'},
                 {'timestamp':'2026-01-01T00:00:00'}, {'timestamp':'2999-01-01T00:00:00Z'}, {'id':None}]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(Stop):
                push_record({**ACTIVITY, **change}, COMMIT)
        for key in ('activity_type', 'after', 'ref', 'timestamp'):
            record = dict(ACTIVITY); del record[key]
            with self.subTest(missing=key), self.assertRaises(Stop):
                push_record(record, COMMIT)

    def test_commit_and_event_repository(self):
        for commit in ('x'*40, 'a'*39, None):
            with self.subTest(commit=commit), self.assertRaises(Stop):
                push_record(ACTIVITY, commit)
        event = copy.deepcopy(EVENT); event['repo']['name'] = 'another/research'
        with self.assertRaises(Stop):
            push_record(event, COMMIT)
        event = copy.deepcopy(EVENT); event['payload']['head'] = 'b'*40
        with self.assertRaises(Stop):
            push_record(event, COMMIT)


class D1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT/'tests')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'project'
        self.clone = self.base/'separate-clone'
        self.clone.mkdir()
        prepare(self.root)
        (self.root/'rg_core.py').write_text('unchanged scientific implementation\n')
        (self.root/'RUN.md').write_text('original provenance instructions\n')
        self.parent_hash = freeze(self.root)
        self.original = (self.root/'freeze.json').read_bytes()
        # Fixtures have their own immutable parent; production pins the real r2 hash.
        self.pin = patch('rg_freeze.ORIGINAL_FREEZE_SHA256', self.parent_hash)
        self.pin.start(); self.addCleanup(self.pin.stop)
        (self.root/'DEVIATIONS.md').write_text('D1: provenance only\n')
        (self.root/'RUN.md').write_text('D1 provenance instructions\n')
        self.event_file = self.base/'activity.json'
        self.source = (json.dumps(ACTIVITY, indent=2)+'\n').encode()
        self.event_file.write_bytes(self.source)

    def git(self, cmd, **kw):
        self.assertEqual(Path(kw['cwd']), self.clone)
        if cmd[1] == 'rev-parse':
            return COMMIT+'\n'
        if cmd[1] == 'remote':
            return 'git@github.com:Robin84Bran/research.git\n'
        if cmd[1] == 'show':
            prefix = COMMIT+':projects/receipt-gap/'
            self.assertTrue(cmd[2].startswith(prefix))
            return (self.root/cmd[2][len(prefix):]).read_bytes()
        if cmd[1] == 'ls-remote':
            return COMMIT+'\t'+ACTIVITY['ref']+'\n'
        self.fail('unexpected Git command: '+repr(cmd))

    def attest(self):
        return attest(self.root, self.event_file, COMMIT, 'projects/receipt-gap', self.clone)

    def test_amendment_binds_parent_and_preserves_science(self):
        digest = freeze_d1(self.root)
        amendment = read(self.root/'freeze-d1.json')
        parent = read(self.root/'freeze.json')
        self.assertEqual((self.root/'freeze.json').read_bytes(), self.original)
        self.assertEqual(amendment['original_freeze_sha256'], self.parent_hash)
        self.assertEqual(amendment['files']['freeze.json'], self.parent_hash)
        for name, expected in parent['files'].items():
            if name != 'RUN.md':
                self.assertEqual(amendment['files'][name], expected)
        self.assertEqual(verify(self.root), digest)
        with self.assertRaises(FileExistsError):
            freeze_d1(self.root)

    def test_refreeze_rejects_scientific_change_or_unlisted_addition(self):
        for name in ('rg_core.py', 'config/design.json', 'extra.py'):
            path = self.root/name
            before = path.read_bytes() if path.exists() else None
            path.write_text('changed\n')
            with self.subTest(name=name), self.assertRaises(Stop):
                freeze_d1(self.root)
            if before is None:
                path.unlink()
            else:
                path.write_bytes(before)

    def test_refreeze_rejects_call_exposure(self):
        save(self.root/'collection/episodes/one/0.start.json', {'started_at':ACTIVITY['timestamp']})
        with self.assertRaises(Stop):
            freeze_d1(self.root)

    def test_parent_tamper_rejected(self):
        freeze_d1(self.root)
        (self.root/'freeze.json').write_bytes(self.original+b' ')
        with self.assertRaises(Stop):
            verify(self.root)

    def test_manifest_cannot_rebind_scientific_change(self):
        freeze_d1(self.root)
        path = self.root/'config/design.json'
        path.write_text('{}\n')
        f = read(self.root/'freeze-d1.json')
        f['files']['config/design.json'] = sha(path.read_bytes())
        (self.root/'freeze-d1.json').write_text(canonical(f))
        with self.assertRaises(Stop):
            verify(self.root)

    def test_tampered_input_and_metadata_rejected(self):
        freeze_d1(self.root)
        path = self.root/'RUN.md'; path.write_text('tampered\n')
        with self.assertRaises(Stop):
            verify(self.root)
        path.write_text('D1 provenance instructions\n')
        f = read(self.root/'freeze-d1.json'); f['planned_episodes'] += 1
        (self.root/'freeze-d1.json').write_text(canonical(f))
        with self.assertRaises(Stop):
            verify(self.root)

    def test_activity_attestation_writes_only_to_project_and_opens_gate(self):
        digest = freeze_d1(self.root)
        with patch('rg_freeze.subprocess.check_output', side_effect=self.git):
            self.assertEqual(self.attest(), digest)
        self.assertEqual(push_gate(self.root), digest)
        receipt = read(self.root/'collection/push.json')
        self.assertEqual(receipt['freeze_file'], 'freeze-d1.json')
        self.assertEqual(receipt['source_api'], '/repos/Robin84Bran/research/activity')
        self.assertEqual(receipt['source_event_sha256'], sha(self.source))
        self.assertEqual((self.root/'collection/push-event.json').read_bytes(), self.source)
        self.assertEqual(list(self.clone.iterdir()), [])
        with patch('rg_freeze.subprocess.check_output', side_effect=self.git), self.assertRaises(FileExistsError):
            self.attest()

    def test_push_event_still_works_with_d1(self):
        freeze_d1(self.root)
        self.event_file.write_text(json.dumps(EVENT))
        with patch('rg_freeze.subprocess.check_output', side_effect=self.git):
            self.attest()
        self.assertEqual(push_gate(self.root), verify(self.root))

    def test_attestation_checks_clone_head_origin_both_freezes_and_exact_ref(self):
        freeze_d1(self.root)
        failures = [('rev-parse', None, 'b'*40+'\n'),
                    ('remote', None, 'https://github.com/another/research.git\n'),
                    ('show', 'freeze.json', b'wrong original freeze'),
                    ('show', 'freeze-d1.json', b'wrong amended freeze'),
                    ('ls-remote', None, COMMIT+'\trefs/heads/other\n'),
                    ('ls-remote', None, 'b'*40+'\t'+ACTIVITY['ref']+'\n')]
        for operation, filename, result in failures:
            def git(cmd, **kw):
                if cmd[1] == operation and (filename is None or cmd[2].endswith('/'+filename)):
                    return result
                return self.git(cmd, **kw)
            with self.subTest(operation=operation, filename=filename):
                with patch('rg_freeze.subprocess.check_output', side_effect=git), self.assertRaises(Stop):
                    self.attest()
                self.assertFalse((self.root/'collection/push.json').exists())

    def test_invalid_repo_paths_rejected(self):
        freeze_d1(self.root)
        for path in ('', '/receipt-gap', '../receipt-gap', 'dir/../receipt-gap', 'bad:path'):
            with self.subTest(path=path), patch('rg_freeze.subprocess.check_output', side_effect=self.git), self.assertRaises(Stop):
                attest(self.root, self.event_file, COMMIT, path, self.clone)

    def test_gate_rejects_retained_activity_tamper_and_receipt_ref_mismatch(self):
        freeze_d1(self.root)
        with patch('rg_freeze.subprocess.check_output', side_effect=self.git):
            self.attest()
        receipt_path = self.root/'collection/push.json'
        receipt = read(receipt_path)
        receipt_path.write_text(canonical({**receipt, 'remote_ref':'refs/heads/other'}))
        with self.assertRaises(Stop):
            push_gate(self.root)
        receipt_path.write_text(canonical(receipt))
        (self.root/'collection/push-event.json').write_bytes(self.source+b' ')
        with self.assertRaises(Stop):
            push_gate(self.root)

    def test_gate_rejects_call_before_push(self):
        freeze_d1(self.root)
        with patch('rg_freeze.subprocess.check_output', side_effect=self.git):
            self.attest()
        save(self.root/'collection/episodes/one/0.start.json', {'started_at':'2026-01-01T00:00:00+00:00'})
        with self.assertRaises(Stop):
            push_gate(self.root)

    def test_cli_accepts_clone_root_and_project_output_root(self):
        freeze_d1(self.root)
        args = ['rg_freeze.py', 'attest', '--root', str(self.root), '--clone-root', str(self.clone),
                '--event', str(self.event_file), '--commit', COMMIT, '--repo-path', 'projects/receipt-gap']
        with patch.object(sys, 'argv', args), patch('rg_freeze.subprocess.check_output', side_effect=self.git), patch('builtins.print'):
            main()
        self.assertEqual(push_gate(self.root), verify(self.root))


if __name__ == '__main__':
    unittest.main()
