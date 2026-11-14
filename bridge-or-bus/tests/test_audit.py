import copy
from pathlib import Path
import tempfile
import unittest

from bob_core import canonical,strict_load
from bob_collect import Ledger,ActiveTime,run_episode,Stop
from bob_audit import audit_episode,reconcile_ledger
from bob_offline import FakeTransport


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-audit-')
        self.root=Path(self.temp.name)
        self.ledger=Ledger(self.root/'collection/cost.jsonl')
        self.timer=ActiveTime(self.root/'collection/time.jsonl',43200)
        self.ep=dict(id='claude-00-unit-registry',model='claude',seed=0,world='unit',arm='registry')
        self.saved=run_episode(self.root,self.ep,FakeTransport(self.ep),self.ledger,self.timer,'FIXTURE')

    def tearDown(self):
        self.temp.cleanup()

    def test_full_raw_provenance_and_ledger(self):
        result=audit_episode(self.root,self.ep,self.saved,'FIXTURE')
        self.assertEqual(result,dict(calls=6,events=5))
        ledger=reconcile_ledger(self.root,{self.ep['id']:self.saved})
        self.assertEqual(ledger['status'],'PASS')
        self.assertEqual(ledger['spent_micro_usd'],0)
        self.assertEqual(ledger['held_micro_usd'],0)

    def test_report_cannot_be_forged_in_episode(self):
        self.saved['report']={'submitted':False}
        with self.assertRaises(ValueError): audit_episode(self.root,self.ep,self.saved,'FIXTURE')

    def test_raw_bytes_tamper_detected(self):
        cid=self.saved['calls'][0]
        path=self.root/'collection/raw'/f'{cid}.stdout'
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError): audit_episode(self.root,self.ep,self.saved,'FIXTURE')

    def test_prompt_tamper_detected(self):
        cid=self.saved['calls'][0]
        path=self.root/'collection/requests'/f'{cid}.json'
        value=strict_load(path.read_bytes()); value['prompt']='forged'
        path.write_text(canonical(value))
        with self.assertRaises(ValueError): audit_episode(self.root,self.ep,self.saved,'FIXTURE')

    def test_usage_tamper_detected(self):
        cid=self.saved['calls'][0]
        path=self.root/'collection/calls'/f'{cid}.json'
        value=strict_load(path.read_bytes()); value['usage']['output_tokens']=999
        path.write_text(canonical(value))
        with self.assertRaises(ValueError): audit_episode(self.root,self.ep,self.saved,'FIXTURE')

    def test_ledger_settlement_tamper_detected(self):
        path=self.root/'collection/cost.jsonl'
        rows=[strict_load(x) for x in path.read_text().splitlines()]
        next(x for x in rows if x['event']=='settle')['actual']=1
        path.write_text(''.join(canonical(x)+'\n' for x in rows))
        with self.assertRaises(ValueError): reconcile_ledger(self.root,{self.ep['id']:self.saved})

    def test_freeze_mismatch_detected(self):
        with self.assertRaises(ValueError): audit_episode(self.root,self.ep,self.saved,'OTHER-FREEZE')

    def test_missing_collection_is_unknown(self):
        with tempfile.TemporaryDirectory() as other:
            value=reconcile_ledger(other,{})
            self.assertEqual(value['status'],'UNKNOWN')
            self.assertIsNone(value['spent_micro_usd'])
