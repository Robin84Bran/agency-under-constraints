import multiprocessing
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_budget import *
from trl_core import ROOT
from trl_io import Stop, read


def contender(path,queue):
    try:
        Ledger(path).event(event='reserve',id=str(__import__('os').getpid()),amount=18000000)
        queue.put('won')
    except Stop:
        queue.put('refused')


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'cost.jsonl'

    def ledger(self):return Ledger(self.path)

    def test_reviewed_reservations(self):
        self.assertEqual(maximum('central')['input_tokens'],2368)
        self.assertEqual(maximum('shared')['input_tokens'],2368)
        self.assertEqual(maximum('private')['input_tokens'],2240)
        self.assertEqual(sum(episode_hold(r)*20 for r in ('central','shared','private')),18083840)

    def test_all_depth_sizing_components(self):
        sizing=read(ROOT/'config/sizing.json')
        for row in sizing['measurements']:
            self.assertEqual(row['input_tokens'],padded(row['prompt_utf8_bytes']+row['system_utf8_bytes']+row['schema_utf8_bytes']+826))
            self.assertGreater(row['outer_utf8_bytes'],row['prompt_utf8_bytes'])
            self.assertLessEqual(row['micro_usd'],maximum(row['regime'])['micro_usd'])
        self.assertEqual(len(sizing['measurements']),28)

    def test_protected_reserve_and_project_stop(self):
        self.ledger().event(event='reserve',id='a',amount=24000000)
        with self.assertRaises(Stop):self.ledger().event(event='reserve',id='b',amount=1)
        with patch('trl_budget.FRONTIER',50000000):
            other=Ledger(Path(self.tmp.name)/'other.jsonl')
            with self.assertRaises(Stop):other.event(event='reserve',id='x',amount=38000000)

    def test_entire_episode_and_subhold_not_doublecharged(self):
        l=self.ledger().event(event='reserve',id='e',amount=100000)
        l.event(event='start',id='c',episode='e',amount=40000)
        self.assertEqual(l.exposure,100000)
        l.event(event='settle',id='c',actual=1000)
        self.assertEqual(l.exposure,61000)
        l.event(event='release',id='e');self.assertEqual(l.exposure,1000)

    def test_unknown_usage_retains_hold(self):
        l=self.ledger().event(event='reserve',id='e',amount=100000)
        l.event(event='start',id='c',episode='e',amount=40000)
        l.event(event='unknown',id='c')
        self.assertTrue(self.ledger().stopped);self.assertEqual(self.ledger().exposure,100000)
        with self.assertRaises(Stop):l.event(event='release',id='e')
        with self.assertRaises(Stop):l.event(event='reserve',id='e2',amount=1)

    def test_actual_overrun_saved_unclipped(self):
        l=self.ledger().event(event='reserve',id='e',amount=1000)
        l.event(event='start',id='c',episode='e',amount=1000)
        l.event(event='settle',id='c',actual=99000)
        self.assertEqual(self.ledger().spent,99000);self.assertTrue(self.ledger().stopped)

    def test_output_overrun_stops_even_when_dollar_hold_sufficient(self):
        l=self.ledger().event(event='reserve',id='e',amount=100000)
        l.event(event='start',id='c',episode='e',amount=100000)
        l.event(event='settle',id='c',actual=10,overrun=True)
        self.assertTrue(self.ledger().stopped)

    def test_duplicate_start_no_resend(self):
        l=self.ledger().event(event='reserve',id='e',amount=1000)
        l.event(event='start',id='c',episode='e',amount=1000)
        with self.assertRaises(Stop):self.ledger().event(event='start',id='c',episode='e',amount=1000)

    def test_hash_chain_tamper_rejected(self):
        self.ledger().event(event='reserve',id='e',amount=1000)
        self.path.write_text(self.path.read_text().replace('1000','1001'))
        with self.assertRaises(Stop):self.ledger()

    def test_torn_record_rejected(self):
        self.path.write_text('{"partial":')
        with self.assertRaises(Stop):self.ledger()

    def test_atomic_admission_race(self):
        ctx=multiprocessing.get_context('spawn');q=ctx.Queue()
        ps=[ctx.Process(target=contender,args=(str(self.path),q)) for _ in range(2)]
        for p in ps:p.start()
        for p in ps:p.join(20);self.assertEqual(p.exitcode,0)
        self.assertEqual(sorted([q.get(timeout=2),q.get(timeout=2)]),['refused','won'])
        self.assertEqual(self.ledger().exposure,18000000)

    def test_cumulative_active_time_and_timeout_admission(self):
        p=Path(self.tmp.name)/'time.jsonl'
        clock=ActiveTime(p,1000);clock.begin('a')
        with patch('trl_budget.time.monotonic',return_value=clock.began+200):clock.end()
        resumed=ActiveTime(p,1000);self.assertEqual(resumed.used,200)
        resumed.begin('b')
        with self.assertRaises(Stop):resumed.admit(800)
        resumed.end()

    def test_crash_reserves_remaining_time(self):
        p=Path(self.tmp.name)/'time.jsonl'
        ActiveTime(p,1000).begin('crash')
        with self.assertRaises(Stop):ActiveTime(p,1000).begin('resume')
