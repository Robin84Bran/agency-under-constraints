from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_core import ROOT, canonical
from trl_io import Stop, read, save
from trl_collect import collect
from trl_transport import Fake
from trl_journal import Journal
from trl_audit import evidence_gate


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.order=read(ROOT/'config/episodes.json')[:4]
        save(self.root/'config/episodes.json',self.order)

    def run_collection(self,fault):
        fake=Fake(fault)
        with patch('trl_freeze.push_gate',return_value='TEST'), patch('trl_collect.Local',return_value=fake):
            collect(self.root)
        return fake

    def test_bad_attestation_blocks_transport_construction(self):
        with patch('trl_freeze.push_gate',side_effect=Stop('unattested')),patch('trl_collect.Local',side_effect=AssertionError('no provider construction')):
            with self.assertRaises(Stop): collect(self.root)

    def test_three_transport_failures_durable_pause_before_fourth(self):
        with self.assertRaises(Stop): self.run_collection('incomplete')
        self.assertEqual(len(list((self.root/'collection/episodes').glob('*/episode.json'))),3)
        self.assertEqual(len(list((self.root/'collection').glob('STOP-transport-*.json'))),1)
        with self.assertRaises(Stop): self.run_collection(None)

    def test_model_failures_do_not_trigger_transport_pause(self):
        fake=self.run_collection('malformed')
        self.assertEqual(len(fake.calls),4)
        self.assertEqual(len(list((self.root/'collection/episodes').glob('*/episode.json'))),4)
        self.assertFalse(list((self.root/'collection').glob('STOP*.json')))
        evidence_gate(self.root)

    def test_modified_start_or_time_prefix_rejected(self):
        self.run_collection('malformed')
        p=next((self.root/'collection/episodes').rglob('start.json'))
        raw=p.read_bytes();p.write_text(canonical(dict(read(p),run_id='changed')))
        with self.assertRaises(Stop): evidence_gate(self.root)
        p.write_bytes(raw)
        clock=self.root/'collection/time-local.jsonl'
        clock.write_text(clock.read_text().replace('"seconds":','"seconds":0,"original_seconds":'))
        with self.assertRaises(Stop): evidence_gate(self.root)

    def test_orphan_dispatch_blocks_resume(self):
        Journal(self.root/'collection/dispatch.jsonl').event(event='start',id='uncertain')
        with self.assertRaises(Stop): evidence_gate(self.root)


if __name__=='__main__': unittest.main()

class EvidenceIntegrityTests(unittest.TestCase):
    setUp=AdmissionTests.setUp
    run_collection=AdmissionTests.run_collection
    def test_fake_cannot_be_relabeled_model(self):
        self.run_collection('malformed')
        p=next((self.root/'collection/episodes').glob('*/episode.json'))
        p.write_text(canonical(dict(read(p),kind='MODEL')))
        with self.assertRaises(Stop): evidence_gate(self.root)

    def test_unplanned_episode_cannot_be_ignored(self):
        (self.root/'collection/episodes/unplanned').mkdir(parents=True)
        with self.assertRaises(Stop): evidence_gate(self.root)
