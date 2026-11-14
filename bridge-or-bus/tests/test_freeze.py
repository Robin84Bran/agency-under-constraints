from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,canonical,sha,schedule,sizing
from bob_collect import Stop,save,read,collect
from bob_freeze import inventory,create,verify,check_push,github_evidence
from bob_offline import write


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-freeze-')
        self.root=Path(self.temp.name)
        write(self.root/'config/order.json',schedule())
        write(self.root/'config/sizing.json',sizing())
        write(self.root/'fixture.json',{'fixture':True})

    def tearDown(self):
        self.temp.cleanup()

    def freeze(self):
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256=sha(canonical(inventory(self.root)).encode())))
        return create(self.root)

    def test_exclusive_creation_and_verification(self):
        result=self.freeze()
        self.assertEqual(result['freeze_sha256'],sha((self.root/'freeze.json').read_bytes()))
        self.assertEqual(verify(self.root)['status'],'FROZEN_OFFLINE_NO_INFERENCE')
        with self.assertRaises(Stop): create(self.root)

    def test_changed_source_prevents_dispatch(self):
        self.freeze()
        write(self.root/'fixture.json',{'fixture':False})
        with self.assertRaises(Stop): verify(self.root)
        with patch('bob_collect.http') as network:
            with self.assertRaises(Stop): collect(self.root,('qwen7b',))
            network.assert_not_called()

    def test_new_source_file_detected(self):
        self.freeze()
        write(self.root/'new-source.json',{'fixture':True})
        with self.assertRaises(Stop): verify(self.root)

    def test_collection_and_build_do_not_change_freeze(self):
        self.freeze()
        write(self.root/'collection/fixture.json',{'fixture':True})
        write(self.root/'build/offline.json',{'fixture':True})
        self.assertEqual(verify(self.root)['new_model_calls'],0)

    def test_freeze_requires_exact_tested_source(self):
        write(self.root/'build/test-report.json',dict(status='PASS',tests=1,source_sha256='wrong'))
        with self.assertRaises(Stop): create(self.root)

    def test_symlink_source_refused(self):
        (self.root/'link').symlink_to(self.root/'fixture.json')
        with self.assertRaises(Stop): inventory(self.root)

    def test_missing_push_blocks_all_network(self):
        self.freeze()
        with patch('bob_collect.http') as network:
            with self.assertRaises(FileNotFoundError): collect(self.root,('qwen7b',))
            network.assert_not_called()

    def push_fixture(self):
        self.freeze()
        freeze=read(self.root/'freeze.json')
        freeze['frozen_utc']='2000-01-01T00:00:00+00:00'
        write(self.root/'freeze.json',freeze)
        path='collection/push-evidence/FIXTURE-commit-response.http'
        body=dict(sha='a'*40,url='https://api.github.com/repos/fixture/research/commits/'+'a'*40)
        raw=b'HTTP/2.0 200 OK\r\nDate: Mon, 01 Jan 2024 00:00:00 GMT\r\n\r\n'+canonical(body).encode()
        file=self.root/path; file.parent.mkdir(parents=True); file.write_bytes(raw)
        return path,freeze

    def test_github_server_header_parsing_fixture(self):
        path,freeze=self.push_fixture()
        args=github_evidence(self.root,'https://github.com/fixture/research.git',path)
        self.assertEqual(args['github_time'],'2024-01-01T00:00:00+00:00')
        self.assertEqual(args['commit'],'a'*40)

    def test_github_repo_mismatch_refused(self):
        path,_=self.push_fixture()
        with self.assertRaises(Stop): github_evidence(self.root,'https://github.com/fixture/wrong.git',path)

    def test_push_evidence_binding_and_order(self):
        path,freeze=self.push_fixture()
        push=dict(github_time='2024-01-01T00:00:00+00:00',commit='a'*40,remote='https://github.com/fixture/research.git',
                  server_timestamp_source='https://api.github.com/repos/fixture/research/commits/'+'a'*40,evidence_file=path,evidence_sha256=sha((self.root/path).read_bytes()),freeze_sha256=sha((self.root/'freeze.json').read_bytes()))
        check_push(self.root,freeze,push)
        save(self.root/'collection/starts/fixture.json',{'started':'2023-01-01T00:00:00+00:00'})
        with self.assertRaises(Stop): check_push(self.root,freeze,push)

    def test_changed_push_evidence_refused(self):
        path,freeze=self.push_fixture()
        push=dict(github_time='2024-01-01T00:00:00+00:00',commit='a'*40,remote='fixture',server_timestamp_source='fixture',evidence_file=path,evidence_sha256='wrong',freeze_sha256=sha((self.root/'freeze.json').read_bytes()))
        with self.assertRaises(Stop): check_push(self.root,freeze,push)

    def test_push_cannot_reference_external_evidence(self):
        path,freeze=self.push_fixture()
        push=dict(github_time='2024-01-01T00:00:00+00:00',commit='a'*40,remote='fixture',server_timestamp_source='fixture',evidence_file='../external',freeze_sha256=sha((self.root/'freeze.json').read_bytes()))
        with self.assertRaises(Stop): check_push(self.root,freeze,push)


    def test_attested_git_commit_contains_exact_frozen_content(self):
        import subprocess
        from bob_freeze import git_proof
        self.freeze()
        commit='a'*40
        def git(argv,**kwargs):
            args=argv[3:]
            if args==['rev-parse','--show-toplevel']: raw=str(self.root).encode()
            elif args==['rev-parse','HEAD']: raw=commit.encode()
            elif args[0]=='show': raw=(self.root/args[1].split(':',1)[1]).read_bytes()
            else: raise AssertionError(args)
            return subprocess.CompletedProcess(argv,0,stdout=raw)
        with patch('bob_freeze.subprocess.run',side_effect=git):
            git_proof(self.root,commit)
            with self.assertRaises(Stop): git_proof(self.root,'b'*40)
