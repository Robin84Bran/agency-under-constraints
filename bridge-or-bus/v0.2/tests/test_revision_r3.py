"""Offline r3 parent binding, immutable locals, attestation and Claude audit."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,sha,canonical,schedule,sizing
from bob_collect import read,Stop,Ledger,ActiveTime,run_episode,collect
from bob_freeze import create_r2,verify,inventory,attest,check_push
from bob_offline import write,FakeTransport
from bob_revision_r3 import create_r3,check_preserved
from bob_audit import audit_episode
import test_revision_r2 as r2tests


class R3RevisionTests(unittest.TestCase):
    bind_tests=r2tests.R2RevisionTests.bind_tests

    def setUp(self):
        r2tests.R2RevisionTests.setUp(self)
        create_r2(self.root)
        self.ep=schedule()[0]
        directory=self.root/'collection-r2'
        ledger=Ledger(directory/'cost.jsonl')
        timer=ActiveTime(directory/'local-time.jsonl',43200)
        self.saved=run_episode(self.root,self.ep,FakeTransport(self.ep),ledger,timer,sha((self.root/'freeze-r2.json').read_bytes()))
        write(directory/'push.json',dict(freeze_sha256=sha((self.root/'freeze-r2.json').read_bytes()),github_time='2026-01-01T00:00:00+00:00'))
        self.snapshot()

    def tearDown(self):self.temp.cleanup()

    def snapshot(self):
        directory=self.root/'collection-r2'
        files={p.relative_to(self.root).as_posix():sha(p.read_bytes()) for p in directory.rglob('*') if p.is_file() and p.name!='cost.jsonl'}
        cost=directory/'cost.jsonl'
        write(self.root/'evidence/r3/preservation.json',dict(files=files,unchanged_inputs={},
              parent_freezes={n:sha((self.root/n).read_bytes()) for n in ('freeze.json','freeze-r1.json','freeze-r2.json')},
              append_only={'collection-r2/cost.jsonl':dict(bytes=cost.stat().st_size,sha256=sha(cost.read_bytes()))}))
        self.bind_tests()

    def create(self):
        # Tiny explicit synthetic cohort; production requires all schedule locals.
        with patch('bob_revision_r3.schedule',return_value=[self.ep]):return create_r3(self.root)

    def test_parent_binding_preservation_no_overwrite_and_wrong_freeze_gate(self):
        self.create();record=verify(self.root)
        self.assertEqual(record['revision'],'r3')
        self.assertEqual(record['parent_freezes'],read(self.root/'evidence/r3/preservation.json')['parent_freezes'])
        check_preserved(self.root)
        audit_episode(self.root,self.ep,self.saved,sha((self.root/'freeze-r3.json').read_bytes()))
        with self.assertRaisesRegex(Stop,'never overwrite'):self.create()
        with patch('bob_collect.subprocess.run') as proc,patch('bob_collect.http') as http:
            with self.assertRaisesRegex(Stop,'current revision'):collect(self.root,['claude'],'freeze-r2.json')
            with self.assertRaisesRegex(Stop,'only Claude'):collect(self.root,['qwen7b'],'freeze-r3.json')
            with self.assertRaisesRegex(Stop,'push'):collect(self.root,['claude'],'freeze-r3.json')
            proc.assert_not_called();http.assert_not_called()
        self.assertFalse((self.root/'collection-r3/push.json').exists())
        parent=self.root/'freeze-r2.json';parent.write_bytes(parent.read_bytes()+b' ')
        with self.assertRaisesRegex(Stop,'parent'):verify(self.root)

    def test_preserved_bytes_and_ledger_prefix_reject_changes(self):
        cost=self.root/'collection-r2/cost.jsonl';raw=cost.read_bytes()
        with cost.open('ab') as f:f.write(b'future append')
        check_preserved(self.root)
        cost.write_bytes(b'!'+raw)
        with self.assertRaisesRegex(Stop,'ledger prefix'):check_preserved(self.root)
        cost.write_bytes(raw)
        terminal=self.root/'collection-r2/episodes'/f"{self.ep['id']}.json"
        terminal.write_bytes(terminal.read_bytes()+b' ')
        with self.assertRaisesRegex(Stop,'r2 bytes'):self.create()

    def test_missing_local_or_existing_claude_cannot_freeze(self):
        with self.assertRaisesRegex(Stop,'1200'):create_r3(self.root)
        write(self.root/'collection-r2/starts/claude-forbidden.json',{})
        with self.assertRaisesRegex(Stop,'zero Claude'):self.create()
        self.assertFalse((self.root/'freeze-r3.json').exists())

    def test_new_attestation_checks_four_manifests_and_preserves_r2_receipt(self):
        self.create();record=verify(self.root)
        record.update(frozen_utc='2026-01-01T00:00:00+00:00',transport_policy='D3_ACCOUNT_ACTUAL_NO_REPAIR')
        commit='a'*40;clone=self.root.parent/'offline-r3-clone';seen=[]
        event=dict(activity_type='push',after=commit,id=43,ref='refs/heads/main',timestamp='2026-01-02T00:00:00+00:00')
        write(self.root/'build/event.json',event)
        old=(self.root/'collection-r2/push.json').read_bytes()
        def fake_git(argv,**kwargs):
            args=argv[3:];seen.append(args)
            if args==['rev-parse','--show-toplevel']:out=str(clone).encode()
            elif args==['rev-parse','HEAD']:out=commit.encode()
            elif args==['remote','get-url','origin']:out=b'https://github.com/Robin84Bran/research'
            elif args[0]=='show':out=(self.root/args[1].split(':bridge-or-bus/v0.2/',1)[1]).read_bytes()
            elif args==['ls-remote','origin','refs/heads/main']:out=(commit+'\trefs/heads/main\n').encode()
            else:raise AssertionError(args)
            return SimpleNamespace(stdout=out)
        with patch('bob_freeze.verify',return_value=record),patch('bob_freeze.subprocess.run',side_effect=fake_git):
            receipt=attest(self.root,self.root/'build/event.json',commit,clone,'bridge-or-bus/v0.2','freeze-r3.json')
        self.assertEqual(receipt['evidence_file'],'collection-r3/push-event.json')
        self.assertEqual((self.root/'collection-r2/push.json').read_bytes(),old)
        for name in ('freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json'):
            self.assertIn(['show',commit+':bridge-or-bus/v0.2/'+name],seen)
        check_push(self.root,record,receipt)
        check_preserved(self.root)
        # New Claude calls bind r3 and its actual provider schema, locals bind r2.
        ep=next(e for e in schedule() if e['model']=='claude')
        directory=self.root/'collection-r2'
        original_read=read
        def fixture_read(path):
            if Path(path)==self.root/'config/order.json':return [self.ep,ep]
            if Path(path)==self.root/'config/runtime.json':return {'claude_binary':'FAKE_NOT_EXECUTED'}
            return original_read(path)
        with patch('bob_freeze.verify',return_value=record),patch('bob_collect.read',side_effect=fixture_read),patch('bob_collect.ClaudeAdapter',return_value=FakeTransport(ep)):
            collect(self.root,['claude'],'freeze-r3.json')
        saved=read(directory/'episodes'/f"{ep['id']}.json")
        audit_episode(self.root,ep,saved,receipt['freeze_sha256'])
        check_push(self.root,record,receipt)
        check_preserved(self.root)
        start=directory/'starts'/f"{saved['calls'][0]}.json"
        obj=read(start);obj['schema_sha256']='wrong';start.write_text(canonical(obj))
        with self.assertRaisesRegex(ValueError,'schema/argv'):audit_episode(self.root,ep,saved,receipt['freeze_sha256'])


class ActualR2PreservationTests(unittest.TestCase):
    def test_all_r2_local_bytes_inputs_and_parent_freezes_preserved(self):
        record=check_preserved(ROOT)
        self.assertEqual(record['local_episodes'],1200)
        self.assertEqual(record['claude_starts'],0)
