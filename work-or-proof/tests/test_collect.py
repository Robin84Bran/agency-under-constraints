"""No sockets, subprocesses, models or external evidence used by these tests."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import wop_collect as c

PROJECT = Path(__file__).resolve().parents[1]


class FakeMonitor:
    def __init__(self):
        self.calls = []
        self.generates = []
        self.version = "0.33.3"
        self.bad_digest = False
        self.generate_hook = None
        self.seconds = 0.0

    def clock(self):
        return self.seconds

    def __call__(self, path, payload, timeout):
        self.calls.append((path, copy.deepcopy(payload), timeout))
        self.seconds += 0.25
        if path == "/api/version":
            value = {"version": self.version}
        elif path == "/api/tags":
            value = {"models": [{"name": tag, "digest": ("bad" if self.bad_digest else digest)} for tag, digest in c.PINS.values()]}
        elif path == "/api/show":
            value = {"parameters": "num_ctx 4096", "model_info": {"context_length": 32768}, "details": {"family": payload["model"]}}
        elif path == "/api/generate":
            self.generates.append(copy.deepcopy(payload))
            value = {"model": payload["model"], "done": True, "done_reason": "stop", "response": '{"violation":false}', "prompt_eval_count": 15, "eval_count": 6, "total_duration": 250000000}
            if self.generate_hook:
                value = self.generate_hook(value, len(self.generates))
        else:
            raise AssertionError(path)
        return json.dumps(value).encode()


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="collect-test-", dir=PROJECT)
        self.root = Path(self.temp.name)
        self.config = {"endpoint": c.ENDPOINT, "timeout_seconds": 180, "active_cap_seconds": 43200, "request_options": c.OPTIONS,
                       "expected_runtime_version": "0.33.3", "models": [{"name": name, "tag": c.PINS[name][0], "digest": c.PINS[name][1]} for name in c.MODELS]}
        self.items = []
        for source in ("HA", "Rebel"):
            for actor in ("qwen1.5", "qwen7", "llama8"):
                for seed in (1, 2):
                    item = {"id": source + "/" + actor + "/" + str(seed), "source": source, "actor": actor, "seed": seed, "breach": False}
                    for view in ("final", "trace"):
                        prompt = "Saved prompt " + item["id"] + " " + view
                        item[view] = {"prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
                    self.items.append(item)
        c.exclusive_json(self.root / "config/collector.json", self.config)
        c.exclusive_json(self.root / "imported/dataset.json", {"items": self.items})
        c.exclusive_json(self.root / "config/replay_sample.json", c.replay_sample(self.items))
        c.exclusive_json(self.root / "freeze.json", {"fixture": True})
        c.exclusive_json(self.root / "collection/push.json", {"freeze_sha256": hashlib.sha256((self.root / "freeze.json").read_bytes()).hexdigest(),
                          "pushed_at": "2026-01-01T00:00:00+00:00", "remote": "fixture", "commit": "abc", "server_timestamp_source": "fixture server receipt"})
        self.monitor = FakeMonitor()

    def tearDown(self):
        self.temp.cleanup()

    def collect(self):
        return c.collect(self.root, self.monitor, self.monitor.clock, verify=lambda root: None)

    def test_full_serial_collection_exact_requests_and_resume(self):
        summary = self.collect()
        self.assertEqual(summary["attempted"], 96)
        self.assertEqual(summary["completed"], 96)
        self.assertEqual(summary["replay_attempted"], 48)
        self.assertEqual(len(self.monitor.generates), 96)
        first = self.monitor.generates[0]
        item = sorted(self.items, key=lambda i: i["id"])[0]
        self.assertEqual(first, {"model": "qwen2.5:7b", "prompt": item["final"]["prompt"], "stream": False, "format": "json", "options": dict(c.OPTIONS, seed=item["seed"])})
        self.assertEqual([r["model"] for r in self.monitor.generates[:24]], ["qwen2.5:7b"] * 24)
        self.assertEqual([r["model"] for r in self.monitor.generates[24:48]], ["llama3.1:8b"] * 24)
        receipts = sorted((self.root / "collection/calls").glob("*/*.json"))
        before = {str(p): p.read_bytes() for p in receipts}
        self.collect()
        self.assertEqual(len(self.monitor.generates), 96)
        self.assertEqual(before, {str(p): p.read_bytes() for p in receipts})
        row = next(iter(c.load_first_responses(self.root).values()))
        self.assertEqual(row["usage"]["total_tokens"], 21)
        self.assertIn("total_duration", row["response"])
        self.assertEqual(row["call"]["input_tokens"], 15)
        self.assertTrue(all(s["raw_identical"] == s["attempts"] for s in summary["replays"]["qwen7b"].values()))

    def test_digest_mismatch_stops_before_any_inference(self):
        self.monitor.bad_digest = True
        with self.assertRaisesRegex(c.IntegrityError, "digest mismatch"):
            self.collect()
        self.assertEqual(self.monitor.generates, [])

    def test_runtime_version_mismatch_before_inference(self):
        self.monitor.version = "wrong"
        with self.assertRaisesRegex(c.IntegrityError, "version mismatch"):
            self.collect()
        self.assertEqual(self.monitor.generates, [])

    def test_midstream_version_drift_stops(self):
        def hook(value, n):
            self.monitor.version = "new-version"
            return value
        self.monitor.generate_hook = hook
        with self.assertRaisesRegex(c.IntegrityError, "version drift"):
            self.collect()
        self.assertEqual(len(self.monitor.generates), 1)

    def test_returned_wrong_model_saved_and_stops(self):
        self.monitor.generate_hook = lambda value, n: dict(value, model="wrong")
        with self.assertRaisesRegex(c.IntegrityError, "Returned model"):
            self.collect()
        self.assertEqual(len(self.monitor.generates), 1)
        row = next(iter(c.load_first_responses(self.root).values()))
        self.assertEqual(row["status"], "TECHNICAL_FAILURE")
        self.assertEqual(row["response"]["model"], "wrong")

    def test_timeout_saved_no_automatic_retry(self):
        def hook(value, n):
            if n == 1:
                raise TimeoutError("fixture timeout")
            return value
        self.monitor.generate_hook = hook
        summary = self.collect()
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["attempted"], 96)
        row = next(r for r in c.load_first_responses(self.root).values() if r["status"] != "OK")
        self.assertIsNone(row["usage"]["input_tokens"])
        self.assertEqual(row["usage"]["status"], "UNKNOWN")
        self.assertIsNone(row["raw_reply"])
        self.collect()
        self.assertEqual(len(self.monitor.generates), 96)

    def test_ambiguous_started_call_never_resent(self):
        def hook(value, n):
            if n == 1:
                raise KeyboardInterrupt()
            return value
        self.monitor.generate_hook = hook
        with self.assertRaises(KeyboardInterrupt):
            self.collect()
        self.monitor.generate_hook = None
        summary = self.collect()
        self.assertEqual(summary["uncertain"], 1)
        self.assertEqual(summary["attempted"], 96)
        self.assertEqual(len(self.monitor.generates), 96)
        self.assertEqual(len([r for r in c.load_first_responses(self.root).values() if r["status"] == "UNCERTAIN"]), 1)

    def test_missing_usage_stays_unknown(self):
        def hook(value, n):
            value.pop("prompt_eval_count")
            return value
        self.monitor.generate_hook = hook
        summary = self.collect()
        self.assertIsNone(summary["by_model"]["qwen7b"]["input_tokens"])
        row = next(iter(c.load_first_responses(self.root).values()))
        self.assertIsNone(row["usage"]["total_tokens"])
        self.assertEqual(row["usage"]["output_tokens"], 6)

    def test_malformed_returned_reply_separate_from_transport_failure(self):
        self.monitor.generate_hook = lambda value, n: dict(value, response="not JSON")
        summary = self.collect()
        self.assertEqual(summary["returned"], 96)
        self.assertEqual(summary["technical_reply_failures"], 96)
        self.assertEqual(summary["transport_or_protocol_failures"], 0)
        self.assertEqual(summary["by_model"]["qwen7b"]["by_phase"]["replays"]["returned"], 24)

    def test_incomplete_response_is_technical_failure(self):
        self.monitor.generate_hook = lambda value, n: dict(value, done=False)
        summary = self.collect()
        self.assertEqual(summary["failed"], 96)

    def test_immutable_receipt_config_mismatch_stops(self):
        self.collect()
        item = self.items[0]
        item["final"]["prompt"] += " changed"
        item["final"]["prompt_sha256"] = hashlib.sha256(item["final"]["prompt"].encode()).hexdigest()
        # Deliberately corrupt a test-owned fixture to exercise resume validation.
        (self.root / "imported/dataset.json").write_text(json.dumps({"items": self.items}))
        with self.assertRaisesRegex(c.IntegrityError, "Saved call identity/config changed"):
            self.collect()
        self.assertEqual(len(self.monitor.generates), 96)

    def test_push_must_match_freeze_and_precede_calls(self):
        path = self.root / "collection/push.json"
        push = c.read_json(path)
        push["freeze_sha256"] = "wrong"
        path.write_text(json.dumps(push))
        with self.assertRaisesRegex(c.IntegrityError, "another freeze"):
            self.collect()
        self.assertEqual(self.monitor.calls, [])

    def test_exact_replay_selection_is_response_truth_independent(self):
        first = c.replay_sample(self.items)
        for item in self.items:
            item["breach"] = True
            item["trace"]["verdict"] = False
        self.assertEqual(first, c.replay_sample(list(reversed(self.items))))
        self.assertEqual(len(first), 24)
        with self.assertRaises(c.IntegrityError):
            c.replay_sample(self.items[:2])

    def test_active_budget_cap_persists_and_crash_reserves(self):
        budget = c.ActiveBudget(self.root, cap=180, monotonic=self.monitor.clock)
        budget.begin()
        resumed = c.ActiveBudget(self.root, cap=180, monotonic=self.monitor.clock)
        self.assertEqual(resumed.charged(), 180)
        with self.assertRaises(c.ResourceStop):
            resumed.begin()
        self.monitor.seconds = 12
        budget.settle()
        self.assertEqual(resumed.charged(), 12)
        resumed.begin()
        self.assertEqual(resumed.remaining(), 168)
        resumed.settle()

    def test_active_cap_stops_dispatch_and_remains_stopped(self):
        c.exclusive_json(self.root / "collection/activity/exhausted.start.json", {"reserved_seconds": 43200})
        result = self.collect()
        self.assertIn("exhausted", result["stop_reason"])
        self.assertEqual(self.monitor.calls, [])
        self.assertEqual(self.collect()["attempted"], 0)

    def test_strict_verdicts(self):
        for raw, expected in [('{"violation":true}', (True, "OK")), ('{"violation":false}', (False, "OK")), ('{"violation":null}', (None, "OK"))]:
            self.assertEqual(c.parse_verdict(raw), expected)
        for raw in ('{}', '{"violation":0}', '{"violation":"false"}', '[]', 'bad', None):
            self.assertEqual(c.parse_verdict(raw), (None, "TECHNICAL_FAILURE"))

    def test_allowlisted_endpoint_and_fixed_config(self):
        for endpoint in ("http://localhost:11435", "http://127.0.0.1:11434", "https://example.com"):
            with self.assertRaises(c.IntegrityError):
                c.HTTPTransport(endpoint)
        altered = copy.deepcopy(self.config)
        altered["request_options"]["temperature"] = 0
        with self.assertRaises(c.IntegrityError):
            c.validate_config(altered)

    def test_exclusive_files_never_replace(self):
        path = self.root / "saved.json"
        c.exclusive_json(path, {"value": 1})
        with self.assertRaises(FileExistsError):
            c.exclusive_json(path, {"value": 2})
        self.assertEqual(c.read_json(path), {"value": 1})


if __name__ == "__main__":
    unittest.main()
