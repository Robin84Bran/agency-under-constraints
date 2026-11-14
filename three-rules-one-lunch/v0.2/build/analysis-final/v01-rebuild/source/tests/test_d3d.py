"""Offline continuation tests using real saved evidence and mocked Git/transport."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from historical import frozen_bytes
from trl_core import ROOT, canonical, sha
from trl_io import Stop, read, save, now, stop, timestamp
from trl_d3 import LEDGERS
from trl_d3c import CLEARANCE, EPISODE, clearance, record_clearance, stop_gate
from trl_freeze import (D3C_FREEZE_SHA256, D3D_ADDED, D3D_CHANGED, attest,
                        d3d_scope, freeze_d3d, verify)
from trl_collect import collect, push_gate
from trl_test import tested_inputs


class D3dTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.template=Path(cls.tmp.name)/'template'
        parent=read(ROOT/'freeze-d3c.json')
        for name,digest in parent['files'].items():
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(frozen_bytes(name,digest))
        shutil.copyfile(ROOT/'freeze-d3c.json',cls.template/'freeze-d3c.json')
        # A sealed clearance reconstructs the historical snapshot after later collection.
        historical=read(ROOT/CLEARANCE) if (ROOT/CLEARANCE).exists() else None
        files=historical['preserved_files'] if historical else {
            p.relative_to(ROOT).as_posix():sha(p.read_bytes())
            for p in (ROOT/'collection').rglob('*') if p.is_file() and not p.name.endswith('.lock')}
        for name,digest in files.items():
            data=(ROOT/name).read_bytes()
            if historical and name in LEDGERS:
                data=data[:historical['ledger_prefixes'][name]['bytes']]
            if sha(data)!=digest:raise AssertionError('snapshot changed: '+name)
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for name in D3D_ADDED|D3D_CHANGED:
            if name==CLEARANCE:continue
            p=cls.template/name;p.parent.mkdir(parents=True,exist_ok=True)
            sealed=read(ROOT/'freeze-d3d.json')
            p.write_bytes(frozen_bytes(name,sealed['files'][name]))
        record_clearance(cls.template,'Claude','Reviewed zero-count harness defect; skip attempted episode.')
        cls.report(cls.template)
        freeze_d3d(cls.template)

    @staticmethod
    def report(root):
        (root/'evidence/test-report-d3d.json').write_text(canonical({
            'status':'PASS','tests':1,'failures':0,'errors':0,'fixture':True,
            'tested_files':tested_inputs(root)})+'\n')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';shutil.copytree(self.template,self.root)
        self.clone=Path(self.tmp.name)/'clone';self.clone.mkdir()
        self.parent=read(self.root/'freeze-d3c.json')
        self.commit='c'*40
        self.current='freeze-d3c.json'
        self.bad=None

    def git(self,args,**kwargs):
        self.assertEqual(kwargs['cwd'],self.clone)
        if args[1]=='rev-parse':return (self.commit+'\n').encode()
        if args[1]=='remote':return b'https://github.com/Robin84Bran/research.git\n'
        if args[1]=='ls-remote':return (self.commit+'\trefs/heads/main\n').encode()
        if args[1]=='show':
            name=args[2].split(':three-rules-one-lunch/')[1]
            self.shown.add(name)
            if name==self.bad:return b'changed pushed blob'
            if self.current=='freeze-d3c.json' and name in self.parent['files']:
                return frozen_bytes(name,self.parent['files'][name])
            return (self.root/name).read_bytes()
        raise AssertionError(args)

    def attest(self,name='freeze-d3c.json'):
        self.current=name;self.commit=('c' if name=='freeze-d3c.json' else 'e')*40
        event={'id':'synthetic-'+name,'activity_type':'push','after':self.commit,
            'ref':'refs/heads/main','timestamp':(timestamp(read(self.root/name)['created_at'])+
                                                dt.timedelta(microseconds=1)).isoformat()}
        path=self.root/'build'/('event-'+name)
        path.parent.mkdir(exist_ok=True);path.write_text(canonical(event)+'\n')
        self.shown=set()
        with patch('trl_freeze.subprocess.check_output',side_effect=self.git):
            result=attest(self.root,path,self.commit,'three-rules-one-lunch',self.clone,name)
        self.assertEqual((self.root/('collection/push-event-'+name[7:-5]+'.raw.json')).read_bytes(),path.read_bytes())
        return result

    def new_start(self,digest=None,when=None):
        save(self.root/'collection/episodes/new/r1-j0.start.json',{
            'freeze_sha256':digest or verify(self.root),'started_at':when or now()})

    def test_parent_freezes_scope_and_create_once(self):
        self.assertEqual(sha((self.root/'freeze-d3c.json').read_bytes()),D3C_FREEZE_SHA256)
        f=read(self.root/'freeze-d3d.json');self.assertEqual(f['parent_freeze_sha256'],D3C_FREEZE_SHA256)
        with self.assertRaises(FileExistsError):freeze_d3d(self.root)
        with self.assertRaises(FileExistsError):record_clearance(self.root,'Claude','again')
        for name in ('config/prompts.json','trl_validation.py','deviations/d3c/disposition.json'):
            changed=deepcopy(f);changed['files'][name]='0'*64
            with self.subTest(name=name),self.assertRaises(Stop):d3d_scope(self.root,changed)

    def test_d3c_attestation_after_d3b_starts_checks_every_historical_blob(self):
        self.assertTrue(list((self.root/'collection/episodes').glob('*/*.start.json')))
        self.assertEqual(self.attest(),D3C_FREEZE_SHA256)
        self.assertEqual(self.shown,set(self.parent['files'])|{'freeze-d3c.json'})
        a=read(self.root/'collection/push-d3c.json')
        self.assertEqual(a['freeze_file'],'freeze-d3c.json');self.assertIn('attested_at',a)
        with self.assertRaises(FileExistsError):self.attest()
        with self.assertRaises(FileNotFoundError):push_gate(self.root)
        self.attest('freeze-d3d.json');self.assertEqual(push_gate(self.root),verify(self.root))

    def test_bad_committed_parent_manifest_file_or_freeze_is_rejected(self):
        for name in ('freeze-d3c.json','trl_validation.py','config/prompts.json'):
            self.bad=name
            with self.subTest(name=name),self.assertRaisesRegex(Stop,'frozen file'):self.attest()
            self.assertFalse((self.root/'collection/push-d3c.json').exists())

    def test_parent_receipt_is_required_even_with_d3d_receipt(self):
        with self.assertRaises(FileNotFoundError):self.attest('freeze-d3d.json')
        self.attest();self.attest('freeze-d3d.json')
        (self.root/'collection/push-d3c.json').unlink()
        with patch('trl_collect.Claude',side_effect=AssertionError('no service access')):
            with self.assertRaises(FileNotFoundError):collect(self.root,'claude')

    def test_new_starts_cannot_be_laundered_into_historical_provenance(self):
        self.new_start(D3C_FREEZE_SHA256)
        with self.assertRaisesRegex(Stop,'precede all new starts'):self.attest()
        with self.assertRaises(FileNotFoundError):push_gate(self.root)

    def test_start_before_attestation_or_with_parent_hash_blocks(self):
        self.attest();self.attest('freeze-d3d.json')
        a=read(self.root/'collection/push-d3d.json')
        self.new_start(when=a['attested_at'])
        with self.assertRaisesRegex(Stop,'push/start'):push_gate(self.root)
        p=self.root/'collection/episodes/new/r1-j0.start.json'
        p.write_text(canonical({'freeze_sha256':D3C_FREEZE_SHA256,'started_at':now()}))
        with self.assertRaisesRegex(Stop,'push/start'):push_gate(self.root)
        p.write_text(canonical({'freeze_sha256':verify(self.root),'started_at':now()}))
        push_gate(self.root)

    def test_missing_attestation_time_or_changed_raw_event_blocks(self):
        self.attest();self.attest('freeze-d3d.json')
        p=self.root/'collection/push-d3c.json';a=read(p);a.pop('attested_at');p.write_text(canonical(a))
        with self.assertRaisesRegex(Stop,'attestation time'):push_gate(self.root)

    def test_clearance_prefixes_allow_append_and_reject_rewrite_or_torn_tail(self):
        c=clearance(self.root)
        for name in LEDGERS:
            p=self.root/name;original=p.read_bytes()
            p.write_bytes(original+b'{"fixture":"append"}\n');clearance(self.root)
            p.write_bytes(b'!'+original[1:])
            with self.subTest(name=name),self.assertRaisesRegex(Stop,'prefix'):clearance(self.root)
            p.write_bytes(original+b'{')
            with self.assertRaisesRegex(Stop,'prefix'):clearance(self.root)
            p.write_bytes(original)
        self.assertIn(EPISODE,c['cleared_episodes'])

    def test_historical_stop_contract_and_episode_bytes_remain_binding(self):
        for name in ('collection/STOP-d3b.json','collection/claude-contract.json',
                     'collection/episodes/'+EPISODE+'/r1-j0.raw.json'):
            p=self.root/name;original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(name=name),self.assertRaises(Stop):clearance(self.root)
            p.write_bytes(original)
        save(self.root/'collection/episodes'/EPISODE/'new.json',{'no':'retroactive evidence'})
        with self.assertRaisesRegex(Stop,'additional evidence'):clearance(self.root)

    def test_clearance_refuses_other_fatal_partial_stop_or_uncertain_budget(self):
        # Re-run recording against independent temporary copies, before sealing.
        for fault in ('fatal','partial','stop','ledger'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'p';shutil.copytree(self.template,root)
                (root/CLEARANCE).unlink();(root/'freeze-d3d.json').unlink()
                if fault=='fatal':save(root/'collection/episodes/other/episode.json',{'fatal':True})
                if fault=='partial':save(root/'collection/episodes/other/request.json',{})
                if fault=='stop':save(root/'collection/STOP-other.json',{'reason':'other'})
                if fault=='ledger':
                    from trl_budget import Ledger
                    Ledger(root/'collection/cost.jsonl').event(event='reserve',id='other',amount=1)
                with self.assertRaises(Stop):record_clearance(root,'Claude','reviewed')
                self.assertFalse((root/CLEARANCE).exists())

    def test_resume_skips_attempted_episode_and_retains_fail_and_stop(self):
        self.attest();self.attest('freeze-d3d.json')
        old={n:(self.root/n).read_bytes() for n in clearance(self.root)['preserved_files'] if n not in LEDGERS}
        selected=read(self.root/'collection/episodes'/EPISODE/'episode.json')['episode']
        original=__import__('trl_collect').read
        def schedule(p):
            return [selected] if Path(p)==self.root/'config/episodes.json' else original(p)
        with patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',side_effect=AssertionError('no resend')):
            collect(self.root,'claude')
        for name,data in old.items():self.assertEqual((self.root/name).read_bytes(),data)
        self.assertEqual(read(self.root/'collection/claude-contract.json')['status'],'FAIL')
        clearance(self.root);push_gate(self.root)

    def test_new_unattempted_claude_episode_uses_d3d_with_original_fail_retained(self):
        from trl_transport import Fake
        self.attest();self.attest('freeze-d3d.json')
        selected=[e for e in read(self.root/'config/episodes.json')
                  if e['actor']=='claude' and e['id']!=EPISODE][:1]
        original=__import__('trl_collect').read
        def schedule(p):
            return selected if Path(p)==self.root/'config/episodes.json' else original(p)
        fake=Fake()
        runtime=read(sorted((self.root/'collection/runtime').glob('claude-*.json'))[0])
        fake.preflight=lambda actor:runtime
        with patch('trl_collect.read',side_effect=schedule),patch('trl_collect.Claude',return_value=fake):
            collect(self.root,'claude')
        directory=self.root/'collection/episodes'/selected[0]['id']
        self.assertTrue(read(directory/'episode.json')['complete']);self.assertTrue(fake.calls)
        for p in directory.glob('*.start.json'):
            self.assertEqual(read(p)['freeze_sha256'],verify(self.root))
        self.assertEqual(read(self.root/'collection/claude-contract.json')['status'],'FAIL')
        push_gate(self.root);stop_gate(self.root)

    def test_future_integrity_stop_gets_new_path_and_cannot_be_cleared_as_pause(self):
        old=(self.root/'collection/STOP-d3b.json').read_bytes()
        stop(self.root/'collection','wrong pinned model')
        self.assertEqual((self.root/'collection/STOP-d3b.json').read_bytes(),old)
        self.assertTrue((self.root/'collection/STOP-d3b-002.json').exists())
        with self.assertRaisesRegex(Stop,'integrity STOP'):stop_gate(self.root)
        from trl_d3b import record_clearance as clear_pause
        with self.assertRaisesRegex(Stop,'integrity STOP'):
            clear_pause(self.root,'STOP-d3b-002.json','Claude','no blanket exception')

    def test_missing_or_stale_tests_block_new_seal(self):
        (self.root/'freeze-d3d.json').unlink()
        (self.root/'evidence/test-report-d3d.json').write_text('{"status":"PASS"}')
        with self.assertRaisesRegex(Stop,'passing D3d tests'):freeze_d3d(self.root)
