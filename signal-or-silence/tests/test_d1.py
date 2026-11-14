"""D1 uses fake monitors only; preserve the original freeze and every attempt."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sos_collect as c
import sos_d1 as d1
import sos_freeze as f
from test_collect import FakeMonitor

ROOT = Path(__file__).resolve().parents[1]


class D1Tests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / 'build/test-tmp'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('config', 'tests', 'build', 'imported', 'evidence', 'agreement-r2'):
            (self.root / folder).mkdir()
        for name in (*d1.CHANGED, 'PROJECT_STATE.md', 'PROTOCOL.md', 'survey_inventory.json'):
            (self.root / name).write_text('original fixture\n')
        self.write('imported/reconciliation.json', {'status': 'PASS'})
        self.write('config/design.json', {'primary_ids': list(range(240)), 'receipt_ids': []})
        self.write('config/reuse.json', {'jobs': {}})
        self.write('build/test_report.json', {'status': 'PASS', 'tests_run': 1, 'tested_utc': c.utcnow()})
        self.config = c.read_json(ROOT / 'config/collector.json')
        self.write('config/collector.json', self.config)
        self.jobs = [j for j in c.read_json(ROOT / 'config/requests.json')['jobs'] if j['model'] == 'claude'][:3]
        self.write('config/requests.json', {'jobs': self.jobs})
        f.freeze(self.root)
        self.original_freeze = (self.root / 'freeze.json').read_bytes()
        self.attest()
        no_socket = patch('socket.socket', side_effect=AssertionError('network forbidden'))
        no_socket.start()
        self.addCleanup(no_socket.stop)

    def write(self, name, obj):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(c.canonical(obj) + '\n')

    def attest(self, deviation=None):
        return f.record_push(self.root, c.utcnow(), 'a' * 40, 'https://example.invalid/research',
                             'offline fixture server receipt', deviation=deviation)

    def stopped_original(self):
        def response(job, cfg):
            tin = 1252 if job['id'] == self.jobs[0]['id'] else 1429
            return {'returned_model': cfg['tag'], 'input_tokens': tin, 'output_tokens': 77,
                    'text': '{}', 'raw_reply': '{}'}
        with self.assertRaisesRegex(c.CollectionStop, 'reservation overrun'):
            c.run_collection(self.root, transport=FakeMonitor(response))

    def prepare_d1(self):
        for name in (*d1.CHANGED, 'PROJECT_STATE.md'):
            p = self.root / 'deviations/d1/originals' / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((self.root / name).read_bytes())
        paths = [*self.root.glob('collection/starts/*.json'), *self.root.glob('collection/calls/*.json'), self.root / 'collection/push.json']
        raw = (self.root / 'collection/cost.jsonl').read_bytes()
        self.write('deviations/d1/collection-baseline.json', {
            'files': {p.relative_to(self.root).as_posix(): c.sha(p.read_bytes()) for p in paths},
            'ledger': {'path': 'collection/cost.jsonl', 'bytes': len(raw), 'sha256': c.sha(raw)}})
        for name in d1.CHANGED:
            (self.root / name).write_text('cost-only fixture change\n')
        for name in ('sos_d1.py', 'tests/test_d1.py', 'DEVIATIONS.md'):
            (self.root / name).write_text('D1 fixture\n')
        self.write('config/d1.json', d1.measure(self.root))
        self.write('build/postfreeze_test_report.json', {'status': 'PASS', 'tests_run': 1, 'tested_utc': c.utcnow()})
        return d1.create(self.root)

    def test_new_bounds_and_gated_resume_preserve_two_saved_calls(self):
        measurement = d1.measure(ROOT)
        self.assertEqual(measurement['by_instruction']['plain']['max_prompt_utf8_bytes'], 1328)
        self.assertEqual(measurement['by_instruction']['explicit']['max_prompt_utf8_bytes'], 1887)
        self.assertEqual(measurement['system_utf8_bytes'], 68)
        self.assertEqual(measurement['max_input_reservation'], 3072)
        self.assertEqual(measurement['output_reservation'], 448)
        self.assertEqual(measurement['planned_total_usd'], '38.092352')
        self.assertLess(c.D(measurement['planned_total_usd']), c.D(39))
        self.stopped_original()
        saved = {p: p.read_bytes() for p in self.root.glob('collection/calls/*.json')}
        original_ledger = (self.root / 'collection/cost.jsonl').read_bytes()
        self.prepare_d1()
        monitor = FakeMonitor()
        with self.assertRaises(FileNotFoundError):
            c.run_collection(self.root, transport=monitor)
        self.assertEqual(monitor.checked, [])
        self.attest('D1')
        with self.assertRaises(FileExistsError):
            self.attest('D1')
        def larger(job, cfg):
            return {'returned_model': cfg['tag'], 'input_tokens': 1429, 'output_tokens': 410,
                    'text': '{}', 'raw_reply': '{}'}
        monitor = FakeMonitor(larger)
        result = c.run_collection(self.root, transport=monitor)
        self.assertEqual(result['already_saved'], 2)
        self.assertEqual(monitor.calls, [self.jobs[2]['id']])
        self.assertEqual(result['completed'], 1)
        for path, raw in saved.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertEqual((self.root / 'freeze.json').read_bytes(), self.original_freeze)
        self.assertTrue((self.root / 'collection/cost.jsonl').read_bytes().startswith(original_ledger))
        receipt = c.read_json(self.root / 'collection/calls' / (self.jobs[2]['id'] + '.json'))
        self.assertEqual(receipt['freeze_sha256'], f.digest(self.root / 'freeze-d1.json'))
        self.assertEqual(receipt['reservation']['output_tokens'], 448)
        self.assertEqual(c.run_collection(self.root, transport=FakeMonitor())['already_saved'], 3)

    def test_d1_rejects_tampering_and_unrelated_scientific_change(self):
        self.stopped_original()
        self.prepare_d1()
        p = self.root / 'PROTOCOL.md'
        p.write_text('changed prediction')
        with self.assertRaisesRegex(ValueError, 'outside cost amendment'):
            f.verify_freeze(self.root)

    def test_original_attestation_still_required_and_bad_d1_timestamp_blocks(self):
        self.stopped_original()
        self.prepare_d1()
        self.attest('D1')
        p = self.root / 'collection/push-d1.json'
        value = c.read_json(p)
        value['github_time'] = '2020-01-01T00:00:00Z'
        self.write('collection/push-d1.json', value)
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, 'D1 push timestamp'):
            c.run_collection(self.root, transport=monitor)
        self.assertEqual(monitor.checked, [])
        original = c.read_json(self.root / 'collection/push.json')
        original['freeze_sha256'] = 'wrong'
        self.write('collection/push.json', original)
        with self.assertRaisesRegex(ValueError, 'pre-D1 collection evidence changed'):
            c.run_collection(self.root, transport=monitor)

    def test_new_d1_overrun_is_durable_and_cannot_be_acknowledged(self):
        self.stopped_original()
        self.prepare_d1()
        self.attest('D1')
        monitor = FakeMonitor(lambda job, cfg: {'returned_model': cfg['tag'],
            'input_tokens': 9999, 'output_tokens': 77, 'text': '{}', 'raw_reply': '{}'})
        with self.assertRaisesRegex(c.CollectionStop, 'reservation overrun'):
            c.run_collection(self.root, transport=monitor)
        next_monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, 'saved integrity failure'):
            c.run_collection(self.root, transport=next_monitor)
        self.assertEqual(next_monitor.checked, [])

    def test_amendment_bytes_and_new_start_push_order_are_enforced(self):
        self.stopped_original()
        self.prepare_d1()
        self.attest('D1')
        monitor = FakeMonitor()
        c.run_collection(self.root, transport=monitor)
        path = self.root / 'collection/starts' / (self.jobs[2]['id'] + '.json')
        start = c.read_json(path)
        start['started'] = '2020-01-01T00:00:00Z'
        self.write(path.relative_to(self.root).as_posix(), start)
        with self.assertRaisesRegex(c.CollectionStop, 'D1 push timestamp'):
            c.run_collection(self.root, transport=FakeMonitor())
        bound = c.read_json(self.root / 'config/d1.json')
        bound['max_input_reservation'] += 1
        self.write('config/d1.json', bound)
        with self.assertRaisesRegex(ValueError, 'D1 file changed'):
            f.verify_freeze(self.root)


if __name__ == '__main__':
    unittest.main()
