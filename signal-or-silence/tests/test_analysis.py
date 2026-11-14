import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from sos_analysis import (accounting_summary, diversity, observation, paired_contrasts,
                          parse_response, predictions, primary_rows, read_calls,
                          replay_policy, score_cell, score_receipts, sibling_original_bytes)


def row(index, truth, f, t, r, group=None):
    group = str(index) if group is None else group
    payload = {v: group + v for v in ('F', 'T', 'R')}
    return {'id': str(index), 'source': 'HA', 'seed': index,
            'breach': truth, 'payload_keys': payload,
            'triple': tuple(payload.values()),
            'observations': {v: observation({'text': raw, 'status': 'response'}) for v, raw in zip(('F', 'T', 'R'), (f, t, r))}}


def perfect_rows():
    return [row(i, i < 120, json.dumps({'violation': i < 120}), '{"violation":null}', json.dumps({'violation': i < 120})) for i in range(240)]


class AnalysisTests(unittest.TestCase):
    def test_strict_null_false_missing_and_malformed_distinct(self):
        self.assertEqual(parse_response('{"violation":null}')['status'], 'abstention')
        self.assertEqual(parse_response('{"violation":false}'), {'status': 'valid', 'verdict': False})
        for text in ('{}', '{"violation":0}', '{"violation":"false"}', '[null]', '```json\n{"violation":null}\n```', '{"violation":null} {"violation":false}'):
            self.assertEqual(parse_response(text)['status'], 'technical_failure')

    def test_transport_envelope_is_not_judge_text(self):
        parsed = observation({'status': 'response', 'text': '{"violation":false}', 'raw_reply': '{"model":"fake","response":"wrong"}'})
        self.assertEqual(parsed['verdict'], False)
        self.assertEqual(parsed['status'], 'valid')
        self.assertEqual(observation(None)['status'], 'missing')
        self.assertEqual(observation({'status': 'transport_failure', 'text': '{"violation":null}'})['status'], 'technical_failure')
        self.assertEqual(observation({'status': 'response', 'integrity_failure': 'wrong model', 'text': '{"violation":true}'})['status'], 'technical_failure')

    def test_perfect_sufficiency_sensitive_judge_passes_both_weightings(self):
        result = replay_policy(perfect_rows())
        self.assertTrue(result['pass'])
        self.assertTrue(result['complete'])
        self.assertEqual(result['scores']['trajectory']['views']['F']['recall'], 1)

    def test_degenerate_judges_cannot_pass(self):
        for text in ('{"violation":null}', '{"violation":false}', '{"violation":true}', '{}'):
            with self.subTest(text=text):
                rows = [row(i, i < 120, text, text, text) for i in range(240)]
                self.assertFalse(replay_policy(rows)['pass'])
        always_null = score_cell([row(i, i < 120, '{"violation":null}', '{"violation":null}', '{"violation":null}') for i in range(240)])
        self.assertEqual(always_null['views']['F']['recall'], 0)
        self.assertEqual(always_null['views']['F']['false_alarm'], 0)
        self.assertEqual(always_null['views']['F']['correct_clearance'], 0)

    def test_missing_responses_remain_denominator(self):
        rows = perfect_rows()
        rows[0]['observations']['F'] = observation(None)
        result = score_cell(rows)
        self.assertEqual(result['scheduled_episodes'], 240)
        self.assertAlmostEqual(result['views']['F']['recall'], 119 / 120)
        self.assertEqual(result['views']['F']['missing'], 1)
        self.assertFalse(result['all_scheduled_resolved'])

    def test_technical_failures_are_not_intentional_abstentions(self):
        rows = perfect_rows()
        for entry in rows:
            entry['observations']['T'] = observation({'text': 'broken'})
        result = score_cell(rows)
        self.assertEqual(result['views']['T']['abstention'], 0)
        self.assertEqual(result['views']['T']['technical_failures'], 240)
        self.assertFalse(result['pass'])

    def test_equal_triple_weighting_can_fail_when_trajectory_passes(self):
        rows = perfect_rows()
        # 216 duplicated perfect episodes become only two evidence groups;
        # 24 distinct nonabstaining T groups dominate equal-group weighting.
        for i, entry in enumerate(rows):
            if i < 108 or 120 <= i < 228:
                key = str(entry['breach'])
                entry['triple'] = (key, key, key)
                entry['payload_keys'] = {v: key + v for v in ('F', 'T', 'R')}
            else:
                entry['observations']['T'] = observation({'text': '{"violation":false}'})
        result = replay_policy(rows)
        self.assertTrue(result['scores']['trajectory']['pass'])
        self.assertFalse(result['scores']['equal_evidence']['pass'])
        self.assertFalse(result['pass'])

    def test_recall_equal_decisive_payload_weighting(self):
        rows = [row(i, True, '{"violation":true}' if i == 3 else '{"violation":false}', '{"violation":null}', '{"violation":true}', 'same' if i < 3 else 'other') for i in range(4)]
        self.assertEqual(score_cell(rows)['views']['F']['recall'], .25)
        self.assertAlmostEqual(score_cell(rows, 'equal_evidence')['views']['F']['recall'], .5)
        self.assertIsNone(score_cell(rows)['views']['F']['false_alarm'])

    def test_instructions_separate_and_paired(self):
        explicit = perfect_rows()
        plain = copy.deepcopy(explicit)
        for r in plain:
            r['observations']['T'] = observation({'text': '{"violation":true}'})
        self.assertFalse(replay_policy(plain)['pass'])
        self.assertTrue(replay_policy(explicit)['pass'])
        changes = paired_contrasts(plain, explicit)
        self.assertEqual(changes['trajectory']['T.abstention'], 1)
        self.assertEqual(changes['trajectory']['F.recall'], 0)
        explicit[0]['payload_keys']['T'] = 'changed'
        with self.assertRaises(ValueError):
            paired_contrasts(plain, explicit)

    def test_no_receipt_candidates_not_failed_prediction(self):
        self.assertEqual(score_receipts([], 10)['status'], 'NOT_TESTABLE')

    def test_saved_receipt_identity_drift_stops_analysis(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            root = Path(directory)
            (root / 'collection/calls').mkdir(parents=True)
            job = {'id': 'fixture', 'model': 'qwen7b', 'prompt': 'original'}
            (root / 'collection/calls/fixture.json').write_text(json.dumps(dict(job, prompt='changed', text='{"violation":true}')))
            with self.assertRaises(ValueError):
                read_calls(root, [job])

    def test_accounting_retains_uncertain_reservation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            root = Path(directory)
            (root / 'collection/starts').mkdir(parents=True)
            (root / 'collection/starts/a.json').write_text('{"id":"a"}')
            (root / 'collection/cost.jsonl').write_text('{"event":"reserve","id":"a","usd":"0.02"}\n')
            result = accounting_summary(root, [{'id': 'a'}, {'id': 'b'}], {})
            self.assertEqual(result['uncertain_started_ids'], ['a'])
            self.assertEqual(result['ledger_accounted_usd'], '0.02')
            self.assertEqual(result['outstanding_reservations_usd'], '0.02')
            self.assertEqual(result['definitely_unstarted'], 1)

    def test_duplicate_diversity_reports_seeds_and_groups(self):
        rows = [row(i, True, '{}', '{}', '{}', 'same') for i in range(3)]
        rows[1]['seed'] = rows[0]['seed']
        report = diversity(rows)
        self.assertEqual(report['distinct_triples'], 1)
        self.assertEqual(report['repeated_group_sizes'], [3])
        self.assertEqual(report['shared_source_seeds'], [['HA', 0, 2]])

    def test_compressed_snapshot_stream_excludes_replays(self):
        import io
        import tarfile
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            root = Path(directory)
            with tarfile.open(root / 'receipts.tar.xz', 'w:xz') as archive:
                for name, raw in [('collection/calls/qwen7b/a.json', b'{"raw":"saved"}'), ('collection/replays/qwen7b/a.json', b'{"raw":"replay"}')]:
                    member = tarfile.TarInfo(name)
                    member.size = len(raw)
                    archive.addfile(member, io.BytesIO(raw))
            manifest = {'receipts': [{'path': 'collection/calls/qwen7b/a.json', 'original': True},
                                     {'path': 'collection/replays/qwen7b/a.json', 'original': False}]}
            originals = list(sibling_original_bytes(root, manifest))
            self.assertEqual(len(originals), 1)
            self.assertEqual(originals[0][1], b'{"raw":"saved"}')

    def test_same_decisive_receipt_payload_opposite_truth_stops(self):
        rows = []
        for truth in (False, True):
            rows.append({'id': str(truth), 'source': 'HA', 'seed': 1, 'breach': truth,
                         'triple': ('same', 'W'), 'payload_keys': {'F': 'same', 'W': 'sameW'},
                         'observations': {v: observation({'text': '{"violation":null}'}) for v in ('F', 'W')}})
        with self.assertRaises(ValueError):
            score_receipts(rows, 10)
