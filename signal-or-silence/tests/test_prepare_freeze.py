import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sos_freeze
import sos_prepare
from sos_import import immutable_write,json_bytes,read,sha

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT/'build/test-tmp'
SCRATCH.mkdir(parents=True,exist_ok=True)


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=SCRATCH);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name in ('tests','config','evidence','imported','build','agreement-r2'):(self.root/name).mkdir()
        for name in ('PROTOCOL.md','RUN.md','survey_inventory.json','sos.py'):(self.root/name).write_text('fixture')
        for name,obj in [('imported/reconciliation.json',{'status':'PASS'}),('config/design.json',{'primary_ids':list(range(240)),'receipt_ids':[]}),('build/test_report.json',{'status':'PASS','tests_run':3,'tested_utc':'2026-11-11'}),('config/collector.json',{}),('config/reuse.json',{}),('config/requests.json',{})]:
            (self.root/name).write_bytes(json_bytes(obj))

    def test_freeze_is_portable_and_never_overwritten(self):
        first=sos_freeze.freeze(self.root)
        self.assertEqual(first['freeze_sha256'],sha((self.root/'freeze.json').read_bytes()))
        self.assertEqual(sos_freeze.verify_freeze(self.root)['primary_episodes'],240)
        with self.assertRaises(FileExistsError):sos_freeze.freeze(self.root)

    def test_push_attestation_binds_actual_freeze_and_is_exclusive(self):
        import datetime as dt
        sos_freeze.freeze(self.root)
        now=dt.datetime.now(dt.timezone.utc).isoformat()
        result=sos_freeze.record_push(self.root,now,'a'*40,'https://github.com/example/private','saved-github-server-receipt')
        self.assertEqual(result['freeze_sha256'],sha((self.root/'freeze.json').read_bytes()))
        with self.assertRaises(FileExistsError):
            sos_freeze.record_push(self.root,now,'a'*40,'https://github.com/example/private','saved-github-server-receipt')

    def test_push_before_freeze_is_rejected(self):
        sos_freeze.freeze(self.root)
        with self.assertRaisesRegex(ValueError,'push timestamp'):
            sos_freeze.record_push(self.root,'2020-01-01T00:00:00+00:00','a'*40,'remote','source')

    def test_frozen_evidence_drift_rejected(self):
        p=self.root/'evidence/source.json';p.write_text('{}')
        sos_freeze.freeze(self.root);p.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError,'frozen file changed'):sos_freeze.verify_freeze(self.root)

    def test_unexpected_code_rejected(self):
        sos_freeze.freeze(self.root);(self.root/'new.py').write_text('x=1')
        with self.assertRaisesRegex(ValueError,'inventory changed'):sos_freeze.verify_freeze(self.root)

    def test_reconciliation_failure_blocks_freeze(self):
        (self.root/'imported/reconciliation.json').write_text('{"status":"FAIL"}')
        with self.assertRaisesRegex(ValueError,'truth reconciliation'):sos_freeze.freeze(self.root)

    def test_test_failure_blocks_freeze(self):
        (self.root/'build/test_report.json').write_text('{"status":"FAIL","tests_run":3,"tested_utc":"2026"}')
        with self.assertRaisesRegex(ValueError,'tests did not pass'):sos_freeze.freeze(self.root)

    def test_postfreeze_test_outputs_are_not_frozen_inputs(self):
        sos_freeze.freeze(self.root);(self.root/'build/postfreeze_test_report.json').write_text('{}')
        sos_freeze.verify_freeze(self.root)


class PreparationTests(unittest.TestCase):
    def test_instruction_matches_inert_source_literal(self):
        plain=sos_prepare.literal(ROOT/'evidence/Honest_Agent/v0.3.1/run_v031.py','MONITOR')
        instruction=read(ROOT/'config/instructions.json')
        self.assertEqual(plain,instruction['plain'])
        self.assertEqual(sos_prepare.EXPLICIT,instruction['explicit'])

    def test_instruction_factor_changes_only_instruction(self):
        jobs=read(ROOT/'config/requests.json')['jobs']; index={(j['model'],j['episode_id'],j['instruction'],j['view']):j for j in jobs}
        for job in jobs:
            if job['instruction']!='plain':continue
            paired=index[(job['model'],job['episode_id'],'explicit',job['view'])]
            self.assertEqual(job['seed'],paired['seed'])
            self.assertEqual(job['prompt'].split('\nInput:\n',1)[1],paired['prompt'].split('\nInput:\n',1)[1])
            a,b=copy.deepcopy(job['request']),copy.deepcopy(paired['request']);a.pop('prompt');b.pop('prompt')
            self.assertEqual(a,b)

    def test_no_duplicate_request_jobs_within_instruction(self):
        jobs=read(ROOT/'config/requests.json')['jobs']
        keys=[(j['model'],j['episode_id'],j['instruction'],j['view']) for j in jobs]
        self.assertEqual(len(keys),len(set(keys)))
        self.assertTrue(all(j['request_sha256']==sha(sos_prepare.canonical(j['request'])) for j in jobs))

    def test_frozen_reuse_cutoff_matches_fixed_request_bytes(self):
        reuse=read(ROOT/'config/reuse.json');snapshot=read(ROOT/'evidence/work-or-proof/snapshot.json')
        self.assertEqual(reuse['snapshot_sha256'],sha(json_bytes(snapshot)))
        self.assertEqual(snapshot['request_file_sha256_before_snapshot'],sha((ROOT/'config/requests.json').read_bytes()))
        self.assertEqual(snapshot['counts'],{'original':5760,'replay':48})
        self.assertEqual(reuse['jobs'],{})

    def test_measured_reservations_fit_without_reuse(self):
        from sos_collect import check_job,check_reservation,model_config
        cfg=read(ROOT/'config/collector.json')
        jobs=read(ROOT/'config/requests.json')['jobs']
        for j in jobs:
            check_job(j,model_config(cfg,j['model']))
            if j['model']=='claude':check_reservation(j,cfg['cost'])
        self.assertLess(sum(j.get('reservation_usd',0) for j in jobs)+5,39)

    def test_zero_reuse_snapshot_is_stable_without_sibling(self):
        with patch.object(sos_prepare,'read',wraps=read):
            self.assertEqual(sos_prepare.snapshot_sibling(ROOT,ROOT/'absent-sibling'),read(ROOT/'config/reuse.json'))

if __name__=='__main__':unittest.main()
