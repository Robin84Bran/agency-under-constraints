"""R2 provenance, isolation, historical charges and offline collection properties."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,canonical,sha,schedule,sizing,strict_load
from bob_collect import Stop,ActiveTime,collect,read
from bob_freeze import create_r2,inventory,verify,freeze_path,check_push,attest
from bob_offline import write,FakeTransport
from bob_paths import collection_dir
from bob_analysis import load_collection


class R2RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        root=self.root
        write(root/'freeze.json',{'fixture':'original'})
        write(root/'freeze-r1.json',dict(format=1,version='0.2',revision='r1',status='FROZEN_OFFLINE_NO_INFERENCE',parent_freeze_sha256=sha((root/'freeze.json').read_bytes())))
        write(root/'collection/episodes/never-score.json',{'fixture':'VOID-HARNESS'})
        (root/'collection/cost.jsonl').write_bytes(b'')
        (root/'collection/local-time.jsonl').write_bytes(b'')
        files={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
        write(root/'evidence/r2/preservation.json',{'files':files})
        write(root/'evidence/r2/void-r1.json',dict(disposition='VOID-HARNESS',episodes=1200,behaviour_analysis_allowed=False))
        write(root/'config/order.json',schedule());write(root/'config/sizing.json',sizing())
        write(root/'config/prior-spend-r2.json',dict(local_active_seconds=100,frontier_active_seconds=0,settled_micro_usd=0,unresolved_hold_micro_usd=0,
              ledger_file='collection/cost.jsonl',ledger_sha256=sha(b''),local_time_file='collection/local-time.jsonl',local_time_sha256=sha(b'')))
        self.bind_tests()

    def tearDown(self):self.temp.cleanup()

    def bind_tests(self):
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256=sha(canonical(inventory(self.root)).encode()),kind='SYNTHETIC_TEST_FIXTURE'))

    def test_create_parent_binding_immutable_freezes_and_empty_r2(self):
        parents={n:(self.root/n).read_bytes() for n in ('freeze.json','freeze-r1.json')}
        create_r2(self.root);record=verify(self.root)
        self.assertEqual(freeze_path(self.root).name,'freeze-r2.json')
        self.assertEqual(record['parent_freezes'],{n:sha(raw) for n,raw in parents.items()})
        self.assertEqual(collection_dir(self.root),self.root/'collection-r2')
        self.assertEqual(list(collection_dir(self.root).iterdir()),[])
        self.assertEqual({n:(self.root/n).read_bytes() for n in parents},parents)
        with self.assertRaisesRegex(Stop,'never overwrite'):create_r2(self.root)
        (self.root/'freeze-r1.json').write_bytes(parents['freeze-r1.json']+b' ')
        with self.assertRaisesRegex(Stop,'parent'):verify(self.root)

    def test_changed_r1_or_started_r2_cannot_freeze(self):
        old=self.root/'collection/episodes/never-score.json';raw=old.read_bytes();old.write_bytes(raw+b' ')
        with self.assertRaisesRegex(Stop,'evidence changed'):create_r2(self.root)
        self.assertFalse((self.root/'freeze-r2.json').exists());old.write_bytes(raw)
        write(self.root/'collection-r2/starts/started.json',{})
        with self.assertRaisesRegex(Stop,'empty'):create_r2(self.root)

    def test_void_r1_cannot_be_analysed_or_admitted_before_r2(self):
        with self.assertRaisesRegex(ValueError,'VOID-HARNESS'):load_collection(self.root,schedule())
        with patch('bob_collect.http') as http,patch('bob_collect.subprocess.run') as process:
            with self.assertRaisesRegex(Stop,'VOID-HARNESS'):collect(self.root,['qwen7b'])
            http.assert_not_called();process.assert_not_called()
        self.assertFalse((self.root/'collection/collector.lock').exists())

    def test_obsolete_freeze_rejected_before_touching_any_ledger(self):
        create_r2(self.root)
        with self.assertRaisesRegex(Stop,'current revision'):collect(self.root,['qwen7b'],'freeze-r1.json')
        self.assertEqual(list(collection_dir(self.root).iterdir()),[])

    def test_attestation_checks_all_three_manifests_and_writes_only_r2(self):
        create_r2(self.root);commit='a'*40
        record=verify(self.root);record['frozen_utc']='2026-01-01T00:00:00+00:00'
        event=dict(activity_type='push',after=commit,id=42,ref='refs/heads/main',timestamp='2026-01-02T00:00:00+00:00')
        write(self.root/'build/event.json',event)
        clone=self.root.parent/'offline-research-clone';seen=[]
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
            receipt=attest(self.root,self.root/'build/event.json',commit,clone,'bridge-or-bus/v0.2','freeze-r2.json')
        self.assertEqual(receipt['evidence_file'],'collection-r2/push-event.json')
        self.assertTrue((collection_dir(self.root)/'push.json').is_file())
        self.assertFalse((self.root/'collection/push.json').exists())
        for name in ('freeze.json','freeze-r1.json','freeze-r2.json'):
            self.assertIn(['show',commit+':bridge-or-bus/v0.2/'+name],seen)

    def test_r1_push_cannot_admit_r2_and_runtime_gate_stays_closed(self):
        create_r2(self.root)
        with self.assertRaisesRegex(Stop,'push'):
            check_push(self.root,verify(self.root),dict(freeze_sha256=sha((self.root/'freeze-r1.json').read_bytes())))
        with patch('bob_collect.http') as http,patch('bob_collect.subprocess.run') as process:
            with self.assertRaisesRegex(Stop,'push'):collect(self.root,['qwen7b'])
            http.assert_not_called();process.assert_not_called()
        self.assertFalse((collection_dir(self.root)/'episode-starts').exists())

    def test_fake_r2_collection_analysis_and_time_preserve_r1(self):
        create_r2(self.root);ep=schedule()[0]
        before={p:p.read_bytes() for p in (self.root/'collection').rglob('*') if p.is_file()}
        write(self.root/'config/order.json',[ep])  # Fixture admission is explicitly mocked below.
        with patch('bob_freeze.verify',return_value={}),patch('bob_freeze.push_gate'),patch('bob_collect.LocalAdapter',return_value=FakeTransport(ep)):
            collect(self.root,[ep['model']],'freeze-r2.json')
        result=load_collection(self.root,schedule())
        self.assertEqual(result['collection_directory'],'collection-r2')
        self.assertEqual(result['excluded_collections'][0]['disposition'],'VOID-HARNESS')
        self.assertEqual(sum(x['attempted'] for x in result['episodes']),1)
        self.assertEqual(result['ledger']['status'],'PASS')
        self.assertEqual({p:p.read_bytes() for p in before},before)
        timer=ActiveTime(collection_dir(self.root)/'local-time.jsonl',150)
        self.assertGreaterEqual(timer.charged,100)
        with self.assertRaises(Stop):timer.begin('cannot-reset-cap',100)


class ActualR1PreservationTests(unittest.TestCase):
    def test_all_void_evidence_and_parent_freezes_match_saved_bytes(self):
        preserved=read(ROOT/'evidence/r2/preservation.json')['files']
        actual={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in (ROOT/'collection').rglob('*') if p.is_file()}
        actual.update({n:sha((ROOT/n).read_bytes()) for n in ('freeze.json','freeze-r1.json')})
        self.assertEqual(actual,preserved)
        rows=[strict_load(p.read_bytes()) for p in (ROOT/'collection/episodes').glob('*.json')]
        self.assertEqual(len(rows),1200)
        for model in ('qwen7b','llama8b','qwen1b'):
            self.assertEqual(sum(x['episode']['model']==model for x in rows),400)
        self.assertTrue(all(x['error']=='ModelFailure: action keys/arm' and x['decisions']==0 and not x['events'] for x in rows))
