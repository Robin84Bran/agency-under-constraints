"""Offline usage-limit, continuation, preservation and freeze gate tests."""
import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import sos_v02 as v
import usage_limit as u
import usage_deviation as d
import test_v02 as old

FIXTURES = Path(__file__).parent / 'fixtures'
PAST = '2000-01-01T00:00:00+00:00'


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.raw = (FIXTURES / 'usage-limit-envelope.json').read_text()
        self.envelope = json.loads(self.raw)

    def test_real_refusal_fixture_is_definite_nonstart(self):
        self.assertIsNotNone(u.refusal(self.raw))
        self.assertEqual(u.reset_time(self.envelope, '2026-11-11T11:24:27+00:00'),
                         '2026-11-11T13:30:00+00:00')

    def test_incomplete_nonzero_or_other_errors_keep_frozen_handling(self):
        for key, value in [('is_error', False), ('api_error_status', 500), ('total_cost_usd', .01),
                           ('total_cost_usd', False), ('result', 'rate limit'), ('structured_output', {})]:
            e = dict(self.envelope, **{key: value})
            self.assertIsNone(u.refusal(json.dumps(e)), (key, value))
        for key in ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'):
            for value in (None, 1, False):
                e = copy.deepcopy(self.envelope)
                e['usage'][key] = value
                self.assertIsNone(u.refusal(json.dumps(e)), (key, value))
            e = copy.deepcopy(self.envelope)
            del e['usage'][key]
            self.assertIsNone(u.refusal(json.dumps(e)))

    def test_nested_usage_and_model_usage_cannot_hide_generation(self):
        for field, value in [('usage', dict(self.envelope['usage'], output_tokens_details={'thinking_tokens': 1})),
                             ('modelUsage', {'claude-opus-5-5': {'outputTokens': 1}}),
                             ('usage', dict(self.envelope['usage'], iterations=[{}]))]:
            self.assertIsNone(u.refusal(json.dumps(dict(self.envelope, **{field: value}))))

    def test_ambiguous_json_never_releases_hold(self):
        for raw in (None, '', '{}', '[]', 'null', self.raw + '{}',
                    self.raw.rstrip()[:-1] + ',"is_error":false}'):
            self.assertIsNone(u.refusal(raw))

    def test_unknown_reset_stays_unknown(self):
        self.envelope['result'] = "You've hit your weekly limit · resets someday"
        self.assertIsNotNone(u.refusal(json.dumps(self.envelope)))
        self.assertIsNone(u.reset_time(self.envelope, PAST))

    def test_reset_across_midnight(self):
        self.envelope['result'] = "You've hit your 5-hour limit · resets 1am (Asia/Hong_Kong)"
        self.assertEqual(u.reset_time(self.envelope, '2026-11-11T15:00:00Z'), '2026-11-11T17:00:00+00:00')

    def test_real_valid_envelope_is_not_nonstart_and_retains_frozen_turn_gate(self):
        raw = (FIXTURES / 'real-claude-envelope.json').read_text()
        self.assertIsNone(u.refusal(raw))
        # The supplied real envelope contains two turns. The original transport
        # rejects it; this deviation must not relax that unrelated frozen rule.
        module = v.collector(v.HERE, '0')
        with old.tempfile.TemporaryDirectory() as temp:
            transport = module.DefaultTransport(Path(temp))
            transport.binary = '/offline/claude'
            with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, raw, '')):
                with self.assertRaisesRegex(v.base.TransportError, 'unexpected turns') as caught:
                    transport.generate(v.read_json(v.HERE / 'config/requests.json')['jobs'][0],
                                       {'tag': 'claude-opus-5-5', 'effort': 'medium'})
            self.assertEqual(caught.exception.raw_reply, raw)


class ResumeTests(unittest.TestCase):
    setUp = old.CollectionTests.setUp
    collect = old.CollectionTests.collect

    def transport(self, at=0, raw=None):
        raw = raw or (FIXTURES / 'usage-limit-envelope.json').read_text()
        class Limited(v.FakeTransport):
            def generate(inner, job, cfg):
                if len(inner.ids) == at:
                    inner.ids.append(job['id'])
                    raise v.base.TransportError('Claude exit 1', raw, '')
                return super().generate(job, cfg)
        return Limited()

    def test_refusal_pauses_immediately_settles_zero_and_waits_without_preflight(self):
        fake = self.transport(at=1)
        result = self.collect(fake)
        self.assertEqual(result['status'], 'usage-limit pause')
        self.assertEqual(result['completed'], 1)
        self.assertEqual(len(fake.ids), 2)
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        self.assertEqual(ledger.amounts[self.jobs[1]['id']], 0)
        saved = {p: p.read_bytes() for p in self.collection.rglob('*') if p.is_file()}
        with patch.object(fake, 'preflight', side_effect=AssertionError('must wait')):
            self.assertEqual(self.collect(fake)['status'], 'usage-limit pause')
        self.assertTrue(all(p.read_bytes() == raw for p, raw in saved.items()))

    def test_resume_identical_bytes_only_at_refused_position(self):
        fake = self.transport(at=2)
        with patch.object(u, 'reset_time', return_value=PAST):
            self.collect(fake)
            saved = {p: p.read_bytes() for p in self.collection.rglob('*') if p.is_file()}
            received = []
            class Inspect(v.FakeTransport):
                def generate(inner, job, cfg):
                    received.append(copy.deepcopy(job))
                    return super().generate(job, cfg)
            next_transport = Inspect()
            self.assertEqual(self.collect(next_transport)['completed'], 2)
            self.assertEqual(received, self.jobs[2:])
            # Cost ledger appends; prior request/start/receipt evidence is immutable.
            self.assertTrue(all(p.read_bytes() == raw for p, raw in saved.items() if p.name != 'cost.jsonl'))
            self.assertTrue((self.collection / 'cost.jsonl').read_bytes().startswith(saved[self.collection / 'cost.jsonl']))
            calls, events = u.effective_calls(self.root, self.jobs,
                v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior), 'test-freeze')
            self.assertEqual(len(calls), 4)
            self.assertEqual(len(events), 1)
            self.assertEqual(self.collect()['already_saved'], 4)

    def test_repeated_refusal_retains_each_envelope_and_zero_charge(self):
        with patch.object(u, 'reset_time', return_value=PAST):
            self.collect(self.transport())
            self.collect(self.transport())
            self.assertEqual(len(list((self.collection / 'usage-limits').glob('*.json'))), 2)
            ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
            self.assertEqual(ledger.total, v.D(self.prior))
            self.assertEqual(self.collect()['completed'], 4)

    def test_nonzero_429_is_not_resubmitted(self):
        e = v.read_json(FIXTURES / 'usage-limit-envelope.json')
        e['usage']['input_tokens'] = 1
        self.collect(self.transport(raw=json.dumps(e)))
        second = v.FakeTransport()
        self.assertEqual(self.collect(second)['already_saved'], 4)
        self.assertEqual(second.ids, [])
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        self.assertNotIn(self.jobs[0]['id'], ledger.settled)

    def test_crash_after_saved_refusal_recovers_without_rewriting(self):
        with patch.object(u, 'reset_time', return_value=PAST):
            with patch.object(u, 'disposition', side_effect=OSError('fixture crash')):
                with self.assertRaises(OSError):
                    self.collect(self.transport())
            cp = self.collection / 'calls' / (self.jobs[0]['id'] + '.json')
            raw = cp.read_bytes()
            self.assertEqual(self.collect()['completed'], 4)
            self.assertEqual(cp.read_bytes(), raw)

    def test_crashed_continuation_reservation_remains_uncertain(self):
        with patch.object(u, 'reset_time', return_value=PAST):
            self.collect(self.transport())
            sp, cp, key = u.locations(self.collection, self.jobs[0]['id'], 1)
            ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
            ledger.reserve(key, v.allowance(self.jobs[0]))
            second = v.FakeTransport()
            self.assertEqual(self.collect(second)['uncertain'], 1)
            self.assertEqual(second.ids, [j['id'] for j in self.jobs[1:]])

    def test_pending_refusal_is_missing_and_excluded_from_technical_counts(self):
        self.collect(self.transport())
        calls, events = u.effective_calls(self.root, self.jobs,
            v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior), 'test-freeze')
        self.assertEqual(calls, {})
        self.assertEqual(len(events), 1)
        self.assertEqual(v.analysis.observation(calls.get(self.jobs[0]['id']))['status'], 'missing')

    def test_pause_evidence_tampering_rejected(self):
        self.collect(self.transport())
        event = next((self.collection / 'usage-limits').glob('*.json'))
        c = v.read_json(event)
        c['reset_utc'] = PAST
        event.write_text(v.canonical(c))
        with self.assertRaisesRegex(v.CollectionStop, 'evidence drift'):
            self.collect()

    def test_new_runner_pause_exits_cleanly_and_releases_lock(self):
        record = old.CollectionTests.setup_runner(self)
        with patch.object(v, 'verify', return_value=record), patch.object(v, 'collector', return_value=self.module):
            result = v.run_collection(self.root, self.transport())
        self.assertEqual(result['status'], 'usage-limit pause')
        self.assertFalse((self.collection / 'collector.lock').exists())

    def test_historical_three_failure_clearance_preserves_receipts_and_ledger_prefix(self):
        fake = self.transport()
        class AlwaysLimited:
            preflight = fake.preflight
            def generate(inner, job, cfg):
                raise v.base.TransportError('Claude exit 1', (FIXTURES / 'usage-limit-envelope.json').read_text(), '')
        # Reproduce the old frozen three-failure disposition from saved bytes.
        with patch.object(v.base, 'CostLedger', self.module.CostLedger), \
             patch.object(v.base, 'dispatch_reservation', self.module.dispatch_reservation):
            with self.assertRaisesRegex(v.CollectionStop, 'three consecutive'):
                v.base._collect(self.root, self.collection, self.jobs, self.config,
                                {'claude'}, AlwaysLimited(), 'test-freeze')
        saved = {p: p.read_bytes() for p in self.collection.rglob('*.json')}
        prefix = (self.collection / 'cost.jsonl').read_bytes()
        v.save_new(self.root / d.FREEZE, {})
        v.save_new(self.root / 'freeze.json', {})
        v.save_new(self.root / 'config/requests.json', {'jobs': self.jobs})
        ledger_path = self.root.parent / 'collection/cost.jsonl'
        ledger_path.parent.mkdir()
        ledger_path.write_bytes((v.PROJECT / 'collection/cost.jsonl').read_bytes())
        # History uses the exact original freeze hash, as the real clearance does.
        with patch.object(d, 'digest', side_effect=lambda p: 'test-freeze' if Path(p) == self.root / 'freeze.json' else v.digest(p)), \
             patch.object(v, 'verify', return_value={}), patch.object(d, 'verify', return_value={}):
            cleared = d.clear(self.root, v)
            self.assertEqual(d.clear(self.root, v), cleared)
        self.assertEqual(cleared['re_dispositioned_transport_failures'], 3)
        self.assertTrue((self.collection / 'cost.jsonl').read_bytes().startswith(prefix))
        self.assertTrue(all(p.read_bytes() == raw for p, raw in saved.items()))
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        self.assertEqual(ledger.total, v.D(self.prior))
        self.assertEqual(len(ledger.settled), 3)

    def test_continuation_cannot_change_request_or_run_before_reset(self):
        with patch.object(u, 'reset_time', return_value=PAST):
            self.collect(self.transport())
            self.collect()
            sp, cp, key = u.locations(self.collection, self.jobs[0]['id'], 1)
            start = v.read_json(sp)
            start['started'] = '1999-01-01T00:00:00+00:00'
            call = v.read_json(cp)
            call['started'] = start['started']
            sp.write_text(v.canonical(start))
            cp.write_text(v.canonical(call))
            with self.assertRaisesRegex(v.CollectionStop, 'before stated reset'):
                self.collect()

    def test_integrity_failure_remains_available_to_analysis(self):
        class Wrong(v.FakeTransport):
            def generate(inner, job, cfg):
                return dict(super().generate(job, cfg), returned_model='wrong')
        with self.assertRaises(v.CollectionStop):
            self.collect(Wrong())
        calls, events = u.effective_calls(self.root, self.jobs,
            v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior), 'test-freeze')
        self.assertEqual(v.analysis.observation(calls[self.jobs[0]['id']])['status'], 'technical_failure')

    def test_analysis_json_and_results_count_operational_event(self):
        self.collect(self.transport())
        for name in ('config/design.json', 'config/requests.json', 'collection/cost.jsonl'):
            target = self.root.parent / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((v.PROJECT / name).read_bytes())
        v.save_new(self.root / 'config/requests.json', v.read_json(v.HERE / 'config/requests.json'))
        v.save_new(self.root / 'freeze.json', {})
        numerical = v.score_version
        original_digest = v.digest
        with patch.object(v, 'verify', return_value={}), \
             patch.object(v, 'digest', side_effect=lambda p: 'test-freeze' if Path(p).resolve() == (self.root / 'freeze.json').resolve() else original_digest(p)), \
             patch.object(v, 'score_version', side_effect=lambda a, b, c: numerical(a, b, c, replicates=2)):
            v.run_analysis(self.root)
        report = v.read_json(self.root / 'analysis/results.json')
        self.assertEqual(report['operational_events']['usage_limit_refusals'], 1)
        self.assertEqual(report['v0.2_accounting']['transport_failures'], 0)
        self.assertEqual(report['v0.2_strict']['saved_calls'], 0)
        self.assertEqual(report['v0.2_strict']['missing_calls'], 1868)
        self.assertIn('Operational usage-limit refusals: 1', (self.root / 'analysis/RESULTS.md').read_text())

    def test_real_transport_failure_recovery_after_continuation_never_resends_it(self):
        with patch.object(u, 'reset_time', return_value=PAST):
            self.collect(self.transport())
            class Broken(v.FakeTransport):
                def generate(inner, job, cfg):
                    raise v.base.TransportError('offline unrelated failure', 'not a usage refusal')
            with self.assertRaisesRegex(v.CollectionStop, 'three consecutive'):
                self.collect(Broken())
            v.save_new(self.root / 'config/requests.json', {'jobs': self.jobs})
            ledger_path = self.root.parent / 'collection/cost.jsonl'
            ledger_path.parent.mkdir()
            ledger_path.write_bytes((v.PROJECT / 'collection/cost.jsonl').read_bytes())
            original_digest = v.digest
            with patch.object(v, 'verify', return_value={}), \
                 patch.object(v, 'digest', side_effect=lambda p: 'test-freeze' if Path(p) == self.root / 'freeze.json' else original_digest(p)):
                path = v.recover(self.root, 'Offline fixture unrelated failure diagnosed; transport restored.')
            recovery = v.read_json(path)
            self.assertIn('/continuations/', recovery['receipt_paths'][self.jobs[0]['id']])
            restored = v.FakeTransport()
            self.assertEqual(self.collect(restored)['completed'], 1)
            self.assertEqual(restored.ids, [self.jobs[3]['id']])


class PrefixGateTests(unittest.TestCase):
    def test_prefix_allows_append_and_rejects_rewrite_or_truncation(self):
        with old.tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'cost.jsonl'
            path.write_bytes(b'original\n')
            spec = {'path': 'cost.jsonl', 'size': path.stat().st_size, 'sha256': d.digest(path)}
            path.write_bytes(b'original\nappended\n')
            d.prefix(root, spec)
            for data in (b'original', b'tampered\nappended\n'):
                path.write_bytes(data)
                with self.assertRaisesRegex(v.CollectionStop, 'prefix drift'):
                    d.prefix(root, spec)

    def test_missing_or_wrong_attestation_prevents_transport(self):
        with old.tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            v.save_new(root / d.FREEZE, {})
            with self.assertRaises(FileNotFoundError):
                d.gate(root)
            v.save_new(root / 'collection/usage-limit-attestation.json', {'deviation_freeze_sha256': 'bad'})
            with self.assertRaisesRegex(v.CollectionStop, 'attestation'):
                d.gate(root)
