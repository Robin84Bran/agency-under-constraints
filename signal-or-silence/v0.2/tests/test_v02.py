"""Offline format, policy, cumulative cost, provenance and restart fixtures."""
import copy
import datetime as dt
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sos_v02 as v
from sos_collect import CollectionStop
from sos_stats import bootstrap_endpoints, evaluate_sample


class FormatTests(unittest.TestCase):
    def test_fixed_sentence_bytes(self):
        self.assertEqual(v.SENTENCE.encode(), b'Reply with only the JSON object, no other text.')

    def test_transform_preserves_order_ids_and_payload_bytes(self):
        old = [j for j in v.read_json(v.PROJECT / 'config/requests.json')['jobs'] if j['model'] == 'claude']
        new = v.transform(v.PROJECT)['jobs']
        instructions = v.read_json(v.PROJECT / 'config/instructions.json')
        self.assertEqual(len(new), 1868)
        self.assertEqual([j['original_id'] for j in new], [j['id'] for j in old])
        for a, b in zip(old, new):
            self.assertEqual(a['prompt'].split('\nInput:\n', 1)[1].encode(), b['prompt'].split('\nInput:\n', 1)[1].encode())
            self.assertEqual(b['prompt'].split('\nInput:\n', 1)[0], instructions[a['instruction']] + ' ' + v.SENTENCE)
            self.assertEqual(b['prompt'].count(v.SENTENCE), 1)
            self.assertEqual(b['request'], dict(a['request'], prompt=b['prompt']))
            self.assertNotEqual(a['id'], b['id'])
            for key in ('episode_id', 'model', 'instruction', 'view', 'seed'):
                self.assertEqual(a[key], b[key])

    def test_hashes_are_version_specific_and_exact(self):
        for job in v.transform(v.PROJECT)['jobs']:
            self.assertEqual(job['prompt_sha256'], v.sha(job['prompt'].encode()))
            self.assertEqual(job['request_sha256'], v.sha(v.canonical(job['request']).encode()))
            self.assertTrue(job['id'].startswith('v02-'))

    def test_scheduled_cells_and_existing_F_overlap(self):
        jobs = v.transform(v.PROJECT)['jobs']
        design = v.read_json(v.PROJECT / 'config/design.json')
        self.assertEqual(len(design['primary_ids']), 240)
        self.assertEqual(len(design['receipt_ids']), 120)
        for i in ('plain', 'explicit'):
            subset = [j for j in jobs if j['instruction'] == i]
            self.assertEqual(len(subset), 934)
            for view in ('F', 'T', 'R'):
                self.assertEqual(sum(j['view'] == view and j['episode_id'] in design['primary_ids'] for j in subset), 240)
            self.assertEqual(sum(j['view'] == 'W' for j in subset), 120)

    def test_strict_true(self):
        self.assertEqual(v.analysis.parse_response('{"violation":true}'), {'status': 'valid', 'verdict': True})

    def test_strict_false(self):
        self.assertEqual(v.analysis.parse_response('{"violation":false}'), {'status': 'valid', 'verdict': False})

    def test_strict_null(self):
        self.assertEqual(v.analysis.parse_response('{"violation":null}'), {'status': 'abstention', 'verdict': None})

    def test_prose_fails(self):
        self.assertEqual(v.analysis.parse_response('Here: {"violation":false}')['status'], 'technical_failure')

    def test_fences_fail(self):
        self.assertEqual(v.analysis.parse_response('```json\n{"violation":false}\n```')['status'], 'technical_failure')

    def test_duplicate_keys_fail(self):
        self.assertEqual(v.analysis.parse_response('{"violation":false,"violation":true}')['status'], 'technical_failure')

    def test_multiple_objects_fail(self):
        self.assertEqual(v.analysis.parse_response('{"violation":true}{"violation":false}')['status'], 'technical_failure')

    def test_malformed_and_wrong_values_fail(self):
        for raw in (None, '', 'oops', '{}', '[]', '{"violation":0}', '{"violation":1}', '{"violation":"false"}', '{"violation":', '{"violation":NaN}'):
            with self.subTest(raw=raw):
                self.assertEqual(v.analysis.parse_response(raw)['status'], 'technical_failure')

    def test_inherited_parser_extra_keys_policy_unchanged(self):
        self.assertEqual(v.analysis.parse_response('{"violation":true,"other":1}')['status'], 'valid')

    def test_integrity_override_survives_lenient_diagnostic(self):
        calls = {'x': {'text': 'Explanation {"violation":true}', 'integrity_failure': 'D1 overrun', 'status': 'response'}}
        diagnostic, counts = v.lenient_calls(calls)
        self.assertEqual(counts['recovered_raw_texts'], 1)
        self.assertEqual(v.analysis.observation(diagnostic['x'])['status'], 'technical_failure')
        self.assertEqual(calls['x']['text'], 'Explanation {"violation":true}')

    def test_lenient_rejects_multiple_nested_or_illegal_objects(self):
        for text in ('{"violation":false}{"violation":true}', 'text {"x":{"violation":true}}', '{"violation":0}', '{"violation":true,"violation":false}'):
            self.assertEqual(v.lenient_calls({'x': {'text': text}})[1]['recovered_raw_texts'], 0)

    def test_actual_v01_format_diagnostic_census(self):
        jobs = [j for j in v.read_json(v.PROJECT / 'config/requests.json')['jobs'] if j['model'] == 'claude']
        calls = v.analysis.read_calls(v.PROJECT, jobs)
        diagnostic, counts = v.lenient_calls(calls)
        self.assertEqual(counts, {'strict_valid_raw_texts': 1594, 'recovered_raw_texts': 274, 'unrecovered_raw_texts': 0})
        self.assertEqual(sum(v.analysis.observation(c)['status'] == 'technical_failure' for c in calls.values()), 275)
        self.assertEqual(sum(v.analysis.observation(c)['status'] == 'technical_failure' for c in diagnostic.values()), 1)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sos-v02-test-')
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'cost.jsonl'

    def test_independent_all_job_reservation_arithmetic(self):
        # Independently compute with Decimal ceiling, not allowance()'s integer formula.
        from decimal import Decimal, ROUND_CEILING
        jobs = v.transform(v.PROJECT)['jobs']
        amounts, maxima = [], {'plain': 0, 'explicit': 0}
        for job in jobs:
            n = len(job['prompt'].encode()) + 68 + 826
            tin = int((Decimal(n) * Decimal('1.10') / 64).to_integral_value(rounding=ROUND_CEILING)) * 64
            estimate = v.allowance(job)
            self.assertEqual(estimate['input_tokens'], tin)
            amount = (Decimal(tin) * 4 + Decimal(448) * 20) / 1000000
            self.assertEqual(Decimal(estimate['usd']), amount)
            amounts.append(amount)
            maxima[job['instruction']] = max(maxima[job['instruction']], tin)
        self.assertEqual(maxima, {'plain': 2560, 'explicit': 3136})
        self.assertEqual(sum(amounts), Decimal('33.520640'))
        self.assertEqual(sum(amounts) + Decimal('11.053392'), Decimal('44.574032'))

    def test_real_v01_reconciliation(self):
        prior = v.reconcile(v.PROJECT / 'collection/cost.jsonl')
        self.assertEqual(prior['accounted_usd'], '11.053392')
        self.assertEqual(prior['settled_usd'], '11.053392')
        self.assertEqual(prior['outstanding_usd'], '0')
        self.assertEqual((prior['reserves'], prior['settlements']), (1868, 1868))

    def test_equality_at_gate_is_permitted(self):
        ledger = v.RollingLedger(self.path, prior='11.053392')
        ledger.reserve('x', {'usd': '27.946608'})
        self.assertEqual(ledger.total, v.D('39'))

    def test_prior_spend_causes_rejection(self):
        ledger = v.RollingLedger(self.path, prior='11.053392')
        with self.assertRaises(CollectionStop):
            ledger.reserve('x', {'usd': '27.946609'})
        self.assertFalse(self.path.exists())

    def test_outstanding_reserve_is_fully_charged(self):
        ledger = v.RollingLedger(self.path, prior='11.053392')
        ledger.reserve('x', {'usd': '20'})
        self.assertEqual(v.RollingLedger(self.path, prior='11.053392').total, v.D('31.053392'))
        with self.assertRaises(CollectionStop):
            ledger.reserve('y', {'usd': '8'})

    def test_actual_usage_releases_only_settled_reserve(self):
        ledger = v.RollingLedger(self.path, prior='11.053392')
        ledger.reserve('x', {'usd': '20'})
        ledger.settle('x', v.D('0.01'))
        ledger.reserve('y', {'usd': '20'})
        self.assertEqual(ledger.total, v.D('31.063392'))

    def test_corrupt_duplicate_and_negative_events_stop(self):
        for events in ([{'event': 'settle', 'id': 'x', 'usd': '1'}],
                       [{'event': 'reserve', 'id': 'x', 'usd': '-1'}],
                       [{'event': 'reserve', 'id': 'x', 'usd': 'NaN'}],
                       [{'event': 'reserve', 'id': 'x', 'usd': '1'}] * 2):
            self.path.write_text('\n'.join(json.dumps(e) for e in events))
            with self.assertRaises(CollectionStop):
                v.RollingLedger(self.path, prior='11.053392')

    def test_torn_ledger_stops(self):
        self.path.write_text('{torn')
        with self.assertRaises(CollectionStop):
            v.RollingLedger(self.path)

    def test_cap_cannot_increase(self):
        with self.assertRaises(CollectionStop):
            v.RollingLedger(self.path, cap='40')

    def test_unknown_prior_is_rejected(self):
        for prior in ('NaN', '-1', 'Infinity'):
            with self.assertRaises(CollectionStop):
                v.RollingLedger(self.path, prior=prior)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sos-v02-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'v0.2'
        self.collection = self.root / 'collection'
        self.collection.mkdir(parents=True)
        self.jobs = v.read_json(v.HERE / 'config/requests.json')['jobs'][:4]
        self.config = v.read_json(v.HERE / 'config/collector.json')
        self.prior = '11.053392'
        self.module = v.collector(v.HERE, self.prior)
        self.fake = v.FakeTransport()
        self.no_subprocess = patch('subprocess.run', side_effect=AssertionError('provider subprocess forbidden'))
        self.no_subprocess.start()
        self.addCleanup(self.no_subprocess.stop)

    def collect(self, transport=None, jobs=None):
        return self.module._collect(self.root, self.collection, self.jobs if jobs is None else jobs,
                                    self.config, {'claude'}, self.fake if transport is None else transport, 'test-freeze')

    def test_fake_dispatch_and_durable_receipt(self):
        result = self.collect()
        self.assertEqual(result['completed'], 4)
        for job in self.jobs:
            start = v.read_json(self.collection / 'starts' / (job['id'] + '.json'))
            call = v.read_json(self.collection / 'calls' / (job['id'] + '.json'))
            for key in job:
                self.assertEqual(start[key], job[key])
            for key in ('raw_reply', 'usage', 'started', 'finished', 'returned_model', 'returned_effort', 'reservation'):
                self.assertIn(key, call)
            self.assertEqual(call['returned_effort'], None)
        self.assertEqual(v.validate_history(self.root, self.jobs, 'test-freeze', self.prior).total, v.D('11.055552'))

    def test_resume_never_resends_saved_receipts(self):
        self.collect()
        before = {p: p.read_bytes() for p in self.collection.rglob('*.json')}
        self.assertEqual(self.collect()['already_saved'], 4)
        self.assertEqual(len(self.fake.ids), 4)
        self.assertEqual(before, {p: p.read_bytes() for p in self.collection.rglob('*.json')})

    def test_reservation_without_start_is_never_dispatched(self):
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        ledger.reserve(self.jobs[0]['id'], v.allowance(self.jobs[0]))
        self.assertEqual(self.collect()['uncertain'], 1)
        self.assertNotIn(self.jobs[0]['id'], self.fake.ids)

    def test_start_without_receipt_is_never_dispatched(self):
        job = self.jobs[0]
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        ledger.reserve(job['id'], v.allowance(job))
        v.save_new(self.collection / 'starts' / (job['id'] + '.json'), dict(job, freeze_sha256='test-freeze'))
        self.assertEqual(self.collect()['uncertain'], 1)
        self.assertNotIn(job['id'], self.fake.ids)

    def test_unknown_usage_keeps_full_reserve(self):
        class Unknown(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), input_tokens=None)
        self.collect(Unknown())
        ledger = v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior)
        self.assertEqual(len(ledger.settled), 0)
        self.assertEqual(ledger.total, v.D(self.prior) + sum(v.D(v.allowance(j)['usd']) for j in self.jobs))

    def test_three_transport_failures_stop_and_remain_saved(self):
        class Failing(v.FakeTransport):
            def generate(self, job, cfg):
                raise v.base.TransportError('offline fixture failure', 'raw failure')
        for _ in range(2):
            with self.assertRaisesRegex(CollectionStop, 'three consecutive'):
                self.collect(Failing())
        self.assertEqual(len(list((self.collection / 'calls').glob('*.json'))), 3)
        self.assertEqual(len(v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior).settled), 0)

    def test_wrong_model_stops_after_one_and_on_resume(self):
        class Wrong(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), returned_model='wrong')
        with self.assertRaisesRegex(CollectionStop, 'model identity'):
            self.collect(Wrong())
        with self.assertRaisesRegex(CollectionStop, 'saved integrity'):
            self.collect()
        self.assertEqual(len(list((self.collection / 'calls').glob('*.json'))), 1)

    def test_wrong_effort_stops(self):
        class Wrong(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), returned_effort='high')
        with self.assertRaisesRegex(CollectionStop, 'effort mismatch'):
            self.collect(Wrong())

    def test_input_overrun_is_saved_and_settled_then_stops(self):
        class Overrun(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), input_tokens=job['reservation_input_tokens'] + 1)
        with self.assertRaisesRegex(CollectionStop, 'reservation overrun'):
            self.collect(Overrun())
        self.assertEqual(len(list((self.collection / 'calls').glob('*.json'))), 1)
        self.assertEqual(len(v.RollingLedger(self.collection / 'cost.jsonl', prior=self.prior).settled), 1)

    def test_output_overrun_stops(self):
        class Overrun(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), output_tokens=449)
        with self.assertRaisesRegex(CollectionStop, 'reservation overrun'):
            self.collect(Overrun())

    def test_budget_rejects_before_any_generation(self):
        self.module = v.collector(v.HERE, '38.999999')
        with self.assertRaises(CollectionStop):
            self.collect()
        self.assertEqual(self.fake.ids, [])
        self.assertFalse((self.collection / 'starts').exists())

    def test_prices_or_reservations_cannot_drift(self):
        self.config['cost']['input_usd_per_million'] = 3
        with self.assertRaisesRegex(CollectionStop, 'rate drift'):
            self.collect()
        self.config['cost']['input_usd_per_million'] = 4
        jobs = copy.deepcopy(self.jobs)
        jobs[0]['reservation_output_tokens'] = 447
        with self.assertRaisesRegex(CollectionStop, 'reservation drift'):
            self.collect(jobs=jobs)

    def test_orphan_start_rejected(self):
        v.save_new(self.collection / 'starts' / (self.jobs[0]['id'] + '.json'), self.jobs[0])
        with self.assertRaisesRegex(CollectionStop, 'start without reservation'):
            v.validate_history(self.root, self.jobs, 'test-freeze', self.prior)

    def test_receipt_and_start_drift_rejected(self):
        self.collect()
        callpath = self.collection / 'calls' / (self.jobs[0]['id'] + '.json')
        call = v.read_json(callpath)
        call['prompt'] += 'tampered'
        callpath.write_text(v.canonical(call))
        with self.assertRaises(ValueError):
            v.validate_history(self.root, self.jobs, 'test-freeze', self.prior)

    def test_isolated_module_does_not_change_v01_globals(self):
        self.assertIsNot(v.base.CostLedger, self.module.CostLedger)
        self.assertEqual(v.base.dispatch_reservation.__module__, 'sos_collect')
        self.assertEqual(self.module.DefaultTransport.__init__.__code__.co_filename, str(v.PROJECT / 'sos_collect.py'))

    def test_unchanged_CLI_command_timeout_and_envelope(self):
        transport = self.module.DefaultTransport(self.root)
        transport.binary = '/offline/fake/claude'
        envelope = {'result': '{"violation":null}', 'usage': {'input_tokens': 1, 'cache_read_input_tokens': 2,
                    'cache_creation_input_tokens': 3, 'output_tokens': 7}, 'modelUsage': {'claude-opus-5-5': {}}}
        result = subprocess.CompletedProcess([], 0, json.dumps(envelope), '')
        with patch('subprocess.run', return_value=result) as run:
            response = transport.generate(self.jobs[0], {'tag': 'claude-opus-5-5', 'effort': 'medium'})
        command = run.call_args.args[0]
        self.assertEqual(command, ['/offline/fake/claude', '-p', '--safe-mode', '--restricted', '--strict-mcp-config',
                         '--tools', '', '--disable-slash-commands', '--no-chrome', '--output-format', 'json',
                         '--model', 'claude-opus-5-5', '--effort', 'medium', '--system-prompt', v.SYSTEM])
        self.assertEqual(run.call_args.kwargs['timeout'], 420)
        self.assertTrue(Path(run.call_args.kwargs['cwd']).is_relative_to(self.collection))
        self.assertEqual(response['input_tokens'], 6)
        self.assertEqual(response['returned_effort'], None)

    def setup_runner(self):
        v.save_new(self.root / 'config/collector.json', self.config)
        v.save_new(self.root / 'config/requests.json', {'jobs': self.jobs})
        prior = self.root.parent / 'collection/cost.jsonl'
        prior.parent.mkdir()
        prior.write_bytes((v.PROJECT / 'collection/cost.jsonl').read_bytes())
        record = {'frozen_utc': '2026-01-01T00:00:00Z'}
        v.save_new(self.root / 'freeze.json', record)
        v.save_new(self.collection / 'push.json', {'freeze_sha256': v.digest(self.root / 'freeze.json'),
                   'github_time': '2026-01-02T00:00:00Z', 'commit': 'a' * 40,
                   'remote': 'https://github.com/fixture/research', 'server_timestamp_source': 'OFFLINE FIXTURE ONLY'})
        return record

    def test_full_runner_uses_fake_transport_and_releases_lock(self):
        record = self.setup_runner()
        with patch.object(v, 'verify', return_value=record), patch.object(v, 'collector', return_value=self.module):
            first = v.run_collection(self.root, self.fake)
            second = v.run_collection(self.root, self.fake)
        self.assertEqual(first['completed'], 4)
        self.assertEqual(second['already_saved'], 4)
        self.assertEqual(len(self.fake.ids), 4)
        self.assertFalse((self.collection / 'collector.lock').exists())

    def test_existing_lock_is_preserved_and_prevents_dispatch(self):
        record = self.setup_runner()
        v.save_new(self.collection / 'collector.lock', {'owner': 'fixture'})
        with patch.object(v, 'verify', return_value=record), patch.object(v, 'collector', return_value=self.module):
            with self.assertRaises(FileExistsError):
                v.run_collection(self.root, self.fake)
        self.assertEqual(self.fake.ids, [])
        self.assertEqual(v.read_json(self.collection / 'collector.lock'), {'owner': 'fixture'})

    def test_full_runner_stop_releases_lock_but_keeps_failure(self):
        record = self.setup_runner()
        class Wrong(v.FakeTransport):
            def generate(self, job, cfg):
                return dict(super().generate(job, cfg), returned_model='wrong')
        with patch.object(v, 'verify', return_value=record), patch.object(v, 'collector', return_value=self.module):
            with self.assertRaisesRegex(CollectionStop, 'model identity'):
                v.run_collection(self.root, Wrong())
        self.assertFalse((self.collection / 'collector.lock').exists())
        self.assertEqual(len(list((self.collection / 'calls').glob('*.json'))), 1)

    def test_orphan_receipt_rejected(self):
        v.save_new(self.collection / 'calls/orphan.json', {'id': 'orphan'})
        with self.assertRaisesRegex(CollectionStop, 'orphan receipt'):
            v.validate_history(self.root, self.jobs, 'test-freeze', self.prior)

    def test_settlement_receipt_disagreement_rejected(self):
        self.collect()
        ledger = self.collection / 'cost.jsonl'
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        for event in events:
            if event['event'] == 'settle':
                event['usd'] = '0.000001'
                break
        ledger.write_text(''.join(v.canonical(e) + '\n' for e in events))
        with self.assertRaisesRegex(CollectionStop, 'settlement/receipt'):
            v.validate_history(self.root, self.jobs, 'test-freeze', self.prior)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sos-v02-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'v0.2'
        self.root.mkdir()
        self.record = {'frozen_utc': '2026-01-01T00:00:00Z'}
        v.save_new(self.root / 'freeze.json', self.record)
        self.push = {'freeze_sha256': v.digest(self.root / 'freeze.json'), 'github_time': '2026-01-02T00:00:00Z',
                     'commit': 'a' * 40, 'remote': 'https://github.com/fixture/research', 'server_timestamp_source': 'OFFLINE FIXTURE ONLY'}

    def test_no_push_blocks_before_transport(self):
        with patch.object(v, 'verify', return_value=self.record), patch.object(v.base, 'DefaultTransport', side_effect=AssertionError('must not instantiate')):
            with self.assertRaises(FileNotFoundError):
                v.run_collection(self.root)

    def test_wrong_push_hash_rejected(self):
        v.save_new(self.root / 'collection/push.json', dict(self.push, freeze_sha256='wrong'))
        with self.assertRaisesRegex(CollectionStop, 'wrong push'):
            v.push_gate(self.root, self.record)

    def test_push_before_freeze_rejected(self):
        v.save_new(self.root / 'collection/push.json', dict(self.push, github_time='2025-01-01T00:00:00Z'))
        with self.assertRaisesRegex(CollectionStop, 'follow freeze'):
            v.push_gate(self.root, self.record)

    def test_push_after_first_start_rejected(self):
        v.save_new(self.root / 'collection/push.json', self.push)
        v.save_new(self.root / 'collection/starts/a.json', {'started': '2026-01-01T12:00:00Z', 'freeze_sha256': self.push['freeze_sha256']})
        with self.assertRaisesRegex(CollectionStop, 'provenance'):
            v.push_gate(self.root, self.record)

    def test_attestation_creates_exclusively_and_records_freeze(self):
        with patch.object(v, 'verify', return_value=self.record):
            result = v.record_push(self.root, self.push['github_time'], self.push['commit'], self.push['remote'], self.push['server_timestamp_source'])
            self.assertEqual(result['freeze_sha256'], self.push['freeze_sha256'])
            with self.assertRaises(FileExistsError):
                v.record_push(self.root, self.push['github_time'], self.push['commit'], self.push['remote'], self.push['server_timestamp_source'])

    def test_invalid_attestation_fields_rejected(self):
        with patch.object(v, 'verify', return_value=self.record):
            for timestamp, commit, remote, source in [('2099-01-01T00:00:00Z', 'a'*40, 'r', 's'),
                   ('2026-01-02T00:00:00', 'a'*40, 'r', 's'), ('2026-01-02T00:00:00Z', 'bad', 'r', 's'),
                   ('2026-01-02T00:00:00Z', 'a'*40, ' ', 's'), ('2026-01-02T00:00:00Z', 'a'*40, 'r', '')]:
                with self.assertRaises(CollectionStop):
                    v.record_push(self.root, timestamp, commit, remote, source)

    def test_freeze_never_overwrites(self):
        before = (self.root / 'freeze.json').read_bytes()
        with self.assertRaisesRegex(CollectionStop, 'never replace'):
            v.freeze(self.root)
        self.assertEqual((self.root / 'freeze.json').read_bytes(), before)

    def test_drift_rejected_before_dispatch(self):
        with patch.object(v, 'verify', side_effect=CollectionStop('input drift')), patch.object(v, 'collector', side_effect=AssertionError('no transport')):
            with self.assertRaisesRegex(CollectionStop, 'drift'):
                v.run_collection(self.root)

    def test_collection_symlink_refused(self):
        target = self.root.parent / 'other'
        target.mkdir()
        (self.root / 'collection').symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(CollectionStop, 'symlink'):
            v.output_boundary(self.root)

    def test_rechecks_preserve_registered_reports(self):
        v.save_check(self.root, 'dry-run.json', {'status': 'PASS', 'first': True})
        v.save_check(self.root, 'dry-run.json', {'status': 'PASS', 'second': True})
        self.assertEqual(len(list((self.root / 'build').glob('postfreeze-dry-run-*.json'))), 2)


class PolicyTests(unittest.TestCase):
    def rows(self, constant=None):
        rows = []
        for i in range(240):
            truth = i < 120
            values = [constant] * 3 if constant is not None else [json.dumps({'violation': truth}), '{"violation":null}', json.dumps({'violation': truth})]
            rows.append({'id': str(i), 'source': 'HA', 'seed': i, 'breach': truth,
                'payload_keys': {k: str(i) + k for k in ('F', 'T', 'R')}, 'triple': (str(i),) * 3,
                'observations': {k: v.analysis.observation({'text': raw, 'status': 'response'}) for k, raw in zip(('F', 'T', 'R'), values)}})
        return rows

    def test_perfect_policy_passes_both_weightings(self):
        self.assertTrue(v.analysis.replay_policy(self.rows())['pass'])

    def test_all_null_cannot_pass(self):
        self.assertFalse(v.analysis.replay_policy(self.rows('{"violation":null}'))['pass'])

    def test_all_clear_cannot_pass(self):
        self.assertFalse(v.analysis.replay_policy(self.rows('{"violation":false}'))['pass'])

    def test_all_breach_cannot_pass(self):
        self.assertFalse(v.analysis.replay_policy(self.rows('{"violation":true}'))['pass'])

    def test_prose_is_technical_failure_not_abstention(self):
        rows = self.rows('Explanation {"violation":null}')
        score = v.analysis.score_cell(rows)
        self.assertEqual(score['views']['T']['abstention'], 0)
        self.assertEqual(score['views']['T']['technical_failures'], 240)

    def test_missing_remains_in_all_denominators(self):
        rows = self.rows()
        rows[0]['observations']['F'] = v.analysis.observation(None)
        score = v.analysis.replay_policy(rows)
        self.assertFalse(score['complete'])
        for w in ('trajectory', 'equal_evidence'):
            self.assertEqual(score['scores'][w]['scheduled_episodes'], 240)
            self.assertAlmostEqual(score['scores'][w]['views']['F']['recall'], 119/120)

    def test_exact_triple_weights_can_defeat_trajectory_pass(self):
        rows = self.rows()
        for i, row in enumerate(rows):
            if i < 108 or 120 <= i < 228:
                key = str(row['breach'])
                row['triple'] = (key,) * 3
                row['payload_keys'] = {w: key + w for w in ('F', 'T', 'R')}
            else:
                row['observations']['T'] = v.analysis.observation({'text': '{"violation":false}'})
        score = v.analysis.replay_policy(rows)
        self.assertTrue(score['scores']['trajectory']['pass'])
        self.assertFalse(score['scores']['equal_evidence']['pass'])
        self.assertFalse(score['pass'])

    def test_decisive_weights_apply_within_truth_subset(self):
        rows = self.rows()[:4]
        for i, row in enumerate(rows):
            row['payload_keys']['F'] = 'same' if i < 3 else 'other'
            row['observations']['F'] = v.analysis.observation({'text': '{"violation":false}' if i < 3 else '{"violation":true}'})
        self.assertAlmostEqual(v.analysis.score_cell(rows)['views']['F']['recall'], .25)
        self.assertAlmostEqual(v.analysis.score_cell(rows, 'equal_evidence')['views']['F']['recall'], .5)

    def test_bootstrap_support_and_multiplicity(self):
        self.assertEqual(evaluate_sample([(1, 1), (0, 1)], ['a', 'b'], ['a', 'a', 'b']), 2/3)
        result = bootstrap_endpoints({'rate': [[(1, 1)] * 4]}, [1, 2, 3, 4], replicates=10)
        self.assertIsNone(result['rate']['interval'])
        self.assertEqual(result['rate']['support_blocks'], 4)

    def test_forecasts_unknown_until_completion(self):
        rows = self.rows()
        rows[0]['observations']['F'] = v.analysis.observation(None)
        scores = {'primary': {i: v.analysis.replay_policy(rows) for i in ('plain', 'explicit')},
                  'receipt_replication': {i: {'status': 'INCOMPLETE'} for i in ('plain', 'explicit')}}
        self.assertTrue(all(p['status'] == 'UNKNOWN' for p in v.forecasts(scores).values()))

    def test_complete_forecast_components_and_secondary_cannot_rescue(self):
        scores = {'primary': {'plain': v.analysis.replay_policy(self.rows('{"violation":false}')),
                              'explicit': v.analysis.replay_policy(self.rows())},
                  'receipt_replication': {i: {'status': 'COMPLETE', 'scores': {'trajectory': {'W': {'abstention': value}}}}
                                          for i, value in [('plain', .1), ('explicit', .7)]}}
        forecasts = v.forecasts(scores)
        self.assertEqual(forecasts['V2-P3']['status'], 'FAIL')
        self.assertEqual(forecasts['V2-P4']['status'], 'PASS')
        self.assertEqual(forecasts['V2-P5']['status'], 'PASS')

    def test_real_schedule_analysis_adapter_incomplete_counts(self):
        design = v.read_json(v.PROJECT / 'config/design.json')
        jobs = v.transform(v.PROJECT)['jobs']
        scores = v.score_version(design, jobs, {}, replicates=2)
        self.assertEqual(scores['scheduled_calls'], 1868)
        self.assertEqual(scores['missing_calls'], 1868)
        for instruction in ('plain', 'explicit'):
            self.assertFalse(scores['primary'][instruction]['complete'])
            self.assertEqual(scores['primary'][instruction]['scores']['trajectory']['scheduled_episodes'], 240)
            self.assertEqual(scores['receipt_replication'][instruction]['episodes'], 120)

    def test_report_renderer_writes_only_versioned_outputs(self):
        with tempfile.TemporaryDirectory(prefix='sos-v02-analysis-test-') as directory:
            project = Path(directory)
            root = project / 'v0.2'
            for name in ('config/design.json', 'config/requests.json', 'collection/cost.jsonl'):
                target = project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((v.PROJECT / name).read_bytes())
            v.save_new(root / 'config/requests.json', v.transform(v.PROJECT))
            numerical = v.score_version
            with patch.object(v, 'verify', return_value={}), patch.object(v, 'score_version', side_effect=lambda d, j, c: numerical(d, j, c, replicates=2)):
                result = v.run_analysis(root)
            self.assertEqual(result['status'], 'INCOMPLETE')
            report = v.read_json(root / 'analysis/results.json')
            self.assertEqual(report['v0.2_strict']['scheduled_calls'], 1868)
            self.assertNotIn('qwen7b', report['v0.2_strict'])
            self.assertTrue(all(p['status'] == 'UNKNOWN' for p in report['forecasts'].values()))
            self.assertNotIn('"pass"', json.dumps(report['post_hoc_v0.1_lenient']))
            self.assertFalse((project / 'analysis').exists())
            with patch.object(v, 'verify', return_value={}), patch.object(v, 'score_version', side_effect=lambda d, j, c: numerical(d, j, c, replicates=2)):
                with self.assertRaises(FileExistsError):
                    v.run_analysis(root)


if __name__ == '__main__':
    unittest.main()
