from pathlib import Path
import tempfile
import unittest
from ps_io import *

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'ledger.jsonl'
    def tearDown(self): self.tmp.cleanup()
    def test_reserve_start_settle_release(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=10000);l.event(event='start',id='a-0',episode='a',reserved=1000)
        l.event(event='settle',id='a-0',actual=1200);self.assertEqual(l.exposure,10200)
        l.event(event='release',id='a');self.assertEqual(l.exposure,1200)
        r=Ledger(self.path);self.assertEqual(r.spent,1200);self.assertEqual(r.finished,{'a'})
    def test_unknown_hold_persists_no_release(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=10000);l.event(event='start',id='a-0',episode='a',reserved=1000)
        with self.assertRaises(Stop): l.event(event='release',id='a')
        self.assertEqual(Ledger(self.path).exposure,10000)
    def test_rolling_admission_includes_spend_and_holds(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=24000000)
        with self.assertRaises(Stop): l.event(event='reserve',id='b',amount=1)
        l.event(event='start',id='a-0',episode='a',reserved=1000000);l.event(event='settle',id='a-0',actual=2000000)
        self.assertEqual(l.exposure,25000000)
        with self.assertRaises(Stop): l.event(event='reserve',id='b',amount=0)
    def test_all_allocations_must_fit_episode_hold(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100)
        l.event(event='start',id='c1',episode='a',reserved=80)
        with self.assertRaises(Stop): l.event(event='start',id='c2',episode='a',reserved=21)
    def test_duplicate_reserve_start_settle(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100)
        with self.assertRaises(Stop): l.event(event='reserve',id='a',amount=1)
        l.event(event='start',id='c',episode='a',reserved=10)
        with self.assertRaises(Stop): l.event(event='start',id='c',episode='a',reserved=10)
        l.event(event='settle',id='c',actual=1)
        with self.assertRaises(Stop): l.event(event='settle',id='c',actual=1)
    def test_prefix_mutation_is_detected(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100)
        original=self.path.read_bytes();self.path.write_bytes(original.replace(b'100',b'101'))
        with self.assertRaises(Stop): Ledger(self.path)
    def test_prefix_truncation_is_detected(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100);self.path.write_bytes(b'')
        with self.assertRaises(Stop): Ledger(self.path)
    def test_unanchored_tail_fails_closed(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100)
        with self.path.open('ab') as f: f.write(b'{}\n')
        with self.assertRaises(Stop): Ledger(self.path)
    def test_concurrent_mutation_fails(self):
        l=Ledger(self.path);l.event(event='reserve',id='a',amount=100)
        self.path.write_bytes(b'')
        with self.assertRaises(Stop): l.event(event='release',id='a')
    def test_durable_stop(self):
        l=Ledger(self.path);l.event(event='stop',id='collection',reason='overrun')
        with self.assertRaises(Stop): l.event(event='reserve',id='a',amount=1)
        self.assertTrue(Ledger(self.path).blocked)
    def test_timer_persistent_and_crash_charged(self):
        t=ActiveTime(self.path,100);t.begin('call',90)
        resumed=ActiveTime(self.path,100);self.assertGreaterEqual(resumed.charged,90)
        with self.assertRaises(Stop): resumed.begin('next',11)
    def test_timer_settles_measured_overhead(self):
        t=ActiveTime(self.path,100);began=t.begin('call',90);t.end('call',began)
        resumed=ActiveTime(self.path,100);self.assertLess(resumed.charged,90)
    def test_lock_rejects_concurrent_writer(self):
        with lock(self.path.parent):
            with self.assertRaises(Stop):
                with lock(self.path.parent): pass
