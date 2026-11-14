from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_core import ROOT, canonical
from trl_io import Stop, read, save
from trl_freeze import freeze,verify,attest


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        save(self.root/'evidence/test-report.json',{'status':'PASS','failures':0,'errors':0})
        save(self.root/'evidence/cli-contract.json',{'readiness':'UNKNOWN'})
        save(self.root/'config/sizing.json',{'frontier_micro_usd':18083840,'including_protected_reserve_micro_usd':19083840})
        save(self.root/'fixture.json',{'x':1})

    def test_freeze_exclusive_and_verifies(self):
        h=freeze(self.root);self.assertEqual(verify(self.root),h)
        with self.assertRaises(FileExistsError):freeze(self.root)

    def test_changed_input_rejected(self):
        freeze(self.root);(self.root/'fixture.json').write_text('{"x":2}')
        with self.assertRaises(Stop):verify(self.root)

    def test_added_unfrozen_code_rejected(self):
        freeze(self.root);(self.root/'new.py').write_text('print(1)')
        with self.assertRaises(Stop):verify(self.root)

    def test_escaping_symlink_rejected(self):
        (self.root/'outside').symlink_to('/etc/hosts')
        with self.assertRaises(Stop):freeze(self.root)

    def test_wrong_server_attestation_fails_before_git(self):
        freeze(self.root);save(self.root/'build/event.json',{'type':'PushEvent','repo':{'name':'wrong'}})
        with patch('trl_freeze.subprocess.check_output',side_effect=AssertionError('must not touch Git')):
            with self.assertRaises(Stop):attest(self.root,self.root/'build/event.json','a'*40,'three-rules-one-lunch')

    def test_design_counts_and_frozen_order(self):
        order=read(ROOT/'config/episodes.json')
        self.assertEqual(len(order),960);self.assertEqual(len({x['id'] for x in order}),960)
        self.assertEqual(sum(4 if e['regime']=='central' else 12 for e in order),8960)
        self.assertEqual(sum(e['actor']=='claude' for e in order),60)
        self.assertEqual({e['seed'] for e in order if e['actor']=='claude'},set(range(20)))
        self.assertTrue(all(e['actor']!='claude' for e in order[:900]))

    def test_server_event_selection_and_binding(self):
        from trl_freeze import select_event
        from trl_collect import push_gate
        import datetime as dt
        h=freeze(self.root)
        # An actual server event may occur within the same second as freezing;
        # fixture dates are explicitly synthetic, never used for collection.
        f=read(self.root/'freeze.json');f['created_at']='2020-01-01T00:00:00+00:00'
        (self.root/'freeze.json').write_text(canonical(f)+'\n')
        event={'id':'fake-server-event','type':'PushEvent','created_at':'2021-01-01T00:00:00Z',
               'repo':{'name':'Robin84Bran/research'},'payload':{'head':'a'*40,'ref':'refs/heads/claude/fixture'}}
        save(self.root/'build/events.json',[[event]])
        select_event(self.root/'build/events.json','a'*40,self.root/'build/event.json')
        def git(args,**kwargs):
            if args[1:]==['rev-parse','HEAD']:return ('a'*40+'\n').encode()
            if args[1:]==['remote','get-url','origin']:return b'git@github.com:Robin84Bran/research.git\n'
            if args[1]=='ls-remote':return ('a'*40+'\trefs/heads/claude/fixture\n').encode()
            if args[1]=='show':return (self.root/args[2].split(':three-rules-one-lunch/')[1]).read_bytes()
            raise AssertionError(args)
        with patch('trl_freeze.subprocess.check_output',side_effect=git):
            digest=attest(self.root,self.root/'build/event.json','a'*40,'three-rules-one-lunch')
        self.assertEqual(push_gate(self.root),digest)
        save(self.root/'collection/episodes/example/r1-j1.start.json',{'freeze_sha256':digest,'started_at':'2020-01-01T00:00:00Z'})
        with self.assertRaises(Stop):push_gate(self.root)

    def test_server_event_missing_commit_rejected(self):
        from trl_freeze import select_event
        save(self.root/'build/events.json',[])
        with self.assertRaises(Stop):select_event(self.root/'build/events.json','a'*40,self.root/'build/event.json')
