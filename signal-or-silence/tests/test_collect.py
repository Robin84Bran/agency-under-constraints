"""Offline collection failure-path tests. No sockets, models or login needed."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import sos_collect as c


class FakeMonitor:
    def __init__(self, outcome=None):
        self.calls, self.checked = [], []
        self.outcome = outcome

    def preflight(self, model, cfg):
        self.checked.append(model)
        return {"tag": cfg["tag"], "digest": cfg.get("digest"), "version": "0.33.3",
                "template": "frozen template", "system": "", "parameters": ""}

    def generate(self, job, cfg):
        self.calls.append(job["id"])
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        if callable(self.outcome):
            return self.outcome(job, cfg)
        return {"text": '{"violation":null}', "raw_reply": '{"response":"{\\"violation\\":null}"}',
                "returned_model": cfg["tag"], "input_tokens": 100, "output_tokens": 7,
                "usage": {"input_tokens": 100, "output_tokens": 7}, "stop_reason": "stop"}


class CollectorTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / "build/test-tmp"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "collection").mkdir()
        self.config = {"models": {}, "runtime": {"version": "0.33.3"},
                       "cost": {"measured_input_max": 1282, "measured_output_max": 393,
                                "input_usd_per_million": 4, "output_usd_per_million": 20, "cap_usd": "39"}}
        self.write("config/collector.json", self.config)
        self.write("freeze.json", {"files": {}, "content_sha256": "test"})
        self.write_push()
        module = types.ModuleType("sos_freeze")
        module.verify_freeze = lambda root: c.read_json(root / "freeze.json")
        self.modules = patch.dict(sys.modules, {"sos_freeze": module})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.no_socket = patch("socket.socket", side_effect=AssertionError("network forbidden in offline test"))
        self.no_socket.start()
        self.addCleanup(self.no_socket.stop)

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(c.canonical(value) + "\n", encoding="utf-8")

    def write_push(self):
        self.write("collection/push.json", {"freeze_sha256": c.sha((self.root / "freeze.json").read_bytes()),
            "github_time": "2026-01-01T00:00:00Z", "server_timestamp_source": "GitHub HTTP Date",
            "remote": "https://example.invalid/research", "commit": "f" * 40})

    def job(self, number=0, model="qwen7b"):
        tag = c.PINS[model][0] if model in c.PINS else "claude-opus-5-5"
        prompt = 'Evidence ' + str(number)
        request = {"model": tag, "prompt": prompt, "stream": False, "format": "json",
                   "options": {"temperature": 0.6, "top_k": 16, "num_predict": 192, "seed": 5}}
        if model == "claude":
            request = {"model": tag, "effort": "medium", "prompt": prompt, "seed": 5}
        result = {"id": hashlib.sha256((model + str(number)).encode()).hexdigest(), "episode_id": "HA:test",
                "model": model, "instruction": "plain", "view": "F", "seed": 5,
                "prompt": prompt, "request": request, "prompt_sha256": c.sha(prompt.encode()),
                "request_sha256": c.sha(c.canonical(request).encode())}
        if model == "claude":
            estimate = c.reservation(result, self.config["cost"])
            result.update(reservation_usd=estimate["usd"], reservation_input_tokens=estimate["input_tokens"])
        return result

    def run_jobs(self, jobs, monitor=None):
        self.write("config/requests.json", jobs)
        return c.run_collection(self.root, transport=monitor if monitor is not None else FakeMonitor())

    def test_response_retained_and_resume_does_not_overwrite(self):
        job = self.job()
        first = FakeMonitor()
        summary = self.run_jobs([job], first)
        receipt = self.root / "collection/calls" / (job["id"] + ".json")
        original = receipt.read_bytes()
        result = json.loads(original)
        self.assertEqual(summary["completed"], 1)
        for field in ("prompt", "seed", "tag", "digest", "raw_reply", "usage", "seconds", "started", "finished"):
            self.assertIn(field, result)
        resumed = FakeMonitor()
        self.assertEqual(self.run_jobs([job], resumed)["already_saved"], 1)
        self.assertEqual(resumed.calls, [])
        self.assertEqual(resumed.checked, [])
        self.assertEqual(receipt.read_bytes(), original)

    def test_crash_after_start_is_uncertain_never_resent(self):
        job = self.job()
        with self.assertRaises(KeyboardInterrupt):
            self.run_jobs([job], FakeMonitor(KeyboardInterrupt()))
        resumed = FakeMonitor()
        self.assertEqual(self.run_jobs([job], resumed)["uncertain"], 1)
        self.assertEqual(resumed.calls, [])
        budget = c.ActiveBudget(self.root / "collection/activity")
        self.assertEqual(budget.charged, 220)
        self.assertEqual(list((self.root / "collection/activity").glob("*.settle.json")), [])

    def test_digest_mismatch_stops_before_first_generation(self):
        monitor = FakeMonitor()
        original = monitor.preflight
        monitor.preflight = lambda model, cfg: dict(original(model, cfg), digest="wrong")
        with self.assertRaisesRegex(c.CollectionStop, "digest"):
            self.run_jobs([self.job()], monitor)
        self.assertEqual(monitor.calls, [])

    def test_runtime_resume_drift_stops_unstarted_job(self):
        self.run_jobs([self.job()])
        monitor = FakeMonitor()
        original = monitor.preflight
        monitor.preflight = lambda model, cfg: dict(original(model, cfg), template="changed")
        with self.assertRaisesRegex(c.CollectionStop, "metadata changed"):
            self.run_jobs([self.job(), self.job(1)], monitor)
        self.assertEqual(monitor.calls, [])

    def test_three_transport_failures_stop_batch_and_persist_across_resume(self):
        monitor = FakeMonitor(c.TransportError("failed", "partial reply"))
        jobs = [self.job(i) for i in range(4)]
        with self.assertRaisesRegex(c.CollectionStop, "three consecutive"):
            self.run_jobs(jobs, monitor)
        self.assertEqual(len(monitor.calls), 3)
        receipts = list((self.root / "collection/calls").glob("*.json"))
        self.assertEqual(len(receipts), 3)
        self.assertTrue(all(c.read_json(path)["raw_reply"] == "partial reply" for path in receipts))
        resumed = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "three consecutive"):
            self.run_jobs(jobs, resumed)
        self.assertEqual(resumed.calls, [])

    def test_wrong_returned_model_saved_then_stops_and_stays_stopped(self):
        def wrong(job, cfg):
            return {"text": "bad", "raw_reply": "wrong model bytes", "returned_model": "wrong"}
        monitor = FakeMonitor(wrong)
        jobs = [self.job(i) for i in range(2)]
        with self.assertRaisesRegex(c.CollectionStop, "identity mismatch"):
            self.run_jobs(jobs, monitor)
        self.assertEqual(len(monitor.calls), 1)
        resumed = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "saved integrity"):
            self.run_jobs(jobs, resumed)
        self.assertEqual(resumed.calls, [])

    def test_missing_or_wrong_push_blocks_transport(self):
        self.write("collection/push.json", {"freeze_sha256": "wrong"})
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "push receipt"):
            self.run_jobs([self.job()], monitor)
        self.assertEqual(monitor.checked, [])

    def test_request_hash_and_decoding_validation_before_transport(self):
        job = self.job()
        job["request"]["options"]["temperature"] = 0.9
        job["request_sha256"] = c.sha(c.canonical(job["request"]).encode())
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "generation request"):
            self.run_jobs([job], monitor)
        self.assertEqual(monitor.checked, [])

    def test_model_order_is_qwen_llama_claude(self):
        seen = []
        def response(job, cfg):
            seen.append(job["model"])
            return {"text": "{}", "raw_reply": "{}", "returned_model": cfg["tag"]}
        self.run_jobs([self.job(model="claude"), self.job(model="llama8b"), self.job()], FakeMonitor(response))
        self.assertEqual(seen, ["qwen7b", "llama8b", "claude"])

    def test_paid_unknown_usage_keeps_entire_reservation(self):
        def unknown(job, cfg):
            return {"text": "{}", "raw_reply": "{}", "returned_model": cfg["tag"], "input_tokens": None, "output_tokens": 7}
        job = self.job(model="claude")
        result = self.run_jobs([job], FakeMonitor(unknown))
        expected = c.reservation(job, self.config["cost"])["usd"]
        self.assertEqual(result["accounted_usd"], expected)
        events = (self.root / "collection/cost.jsonl").read_text().splitlines()
        self.assertEqual(len(events), 1)

    def test_paid_actual_usage_settles_decimal_cost(self):
        job = self.job(model="claude")
        result = self.run_jobs([job])
        self.assertEqual(c.D(result["accounted_usd"]), c.D("0.00054"))
        ledger = c.CostLedger(self.root / "collection/cost.jsonl")
        self.assertIn(job["id"], ledger.settled)

    def test_paid_transport_failure_keeps_reservation(self):
        job = self.job(model="claude")
        result = self.run_jobs([job], FakeMonitor(c.TransportError("timeout")))
        self.assertEqual(result["accounted_usd"], c.reservation(job, self.config["cost"])["usd"])

    def test_paid_reservation_prevents_exceeding_39(self):
        path = self.root / "collection/cost.jsonl"
        ledger = c.CostLedger(path)
        ledger.reserve("prior", {"usd": "38.9999"})
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "cap exceeded"):
            self.run_jobs([self.job(model="claude")], monitor)
        self.assertEqual(monitor.calls, [])
        self.assertEqual(c.CostLedger(path).total, c.D("38.9999"))

    def test_reservation_only_crash_never_retries_paid_job(self):
        job = self.job(model="claude")
        c.CostLedger(self.root / "collection/cost.jsonl").reserve(job["id"], c.reservation(job, self.config["cost"]))
        monitor = FakeMonitor()
        self.assertEqual(self.run_jobs([job], monitor)["uncertain"], 1)
        self.assertEqual(monitor.calls, [])

    def test_measured_max_overrun_is_saved_charged_and_stops(self):
        def overrun(job, cfg):
            return {"text": "{}", "raw_reply": "{}", "returned_model": cfg["tag"], "input_tokens": 1283, "output_tokens": 7}
        monitor = FakeMonitor(overrun)
        with self.assertRaisesRegex(c.CollectionStop, "reservation overrun"):
            self.run_jobs([self.job(model="claude"), self.job(1, "claude")], monitor)
        self.assertEqual(len(monitor.calls), 1)
        receipt = next((self.root / "collection/calls").glob("*.json"))
        self.assertEqual(c.read_json(receipt)["actual_usd"], "0.005272")

    def test_large_prompt_reservation_scales_input_maximum(self):
        job = self.job(model="claude")
        job["prompt"] = "a" * 10000
        reserve = c.reservation(job, self.config["cost"])
        self.assertEqual(reserve["input_tokens"], 4050)
        self.assertEqual(c.D(reserve["usd"]), c.D("0.02406"))

    def test_existing_exclusive_lock_prevents_calls(self):
        self.write("collection/collector.lock", {"pid": 123})
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "lock exists"):
            self.run_jobs([self.job()], monitor)
        self.assertTrue((self.root / "collection/collector.lock").exists())
        self.assertEqual(monitor.calls, [])

    def test_torn_ledger_blocks_collection(self):
        (self.root / "collection/cost.jsonl").write_text('{"event":', encoding="utf-8")
        with self.assertRaisesRegex(c.CollectionStop, "torn cost ledger"):
            self.run_jobs([self.job()])

    def test_binary_runtime_env_reads_only_literal_setting_without_execution(self):
        path = self.root / "runtime.env"
        path.write_text('SECRET=do-not-copy\nexport HONEST_AGENT_CLAUDE_BIN="/some path/claude"\n', encoding="utf-8")
        self.assertEqual(c.claude_binary(path), "/some path/claude")
        path.write_text('HONEST_AGENT_CLAUDE_BIN=$(touch /bad)\n', encoding="utf-8")
        with self.assertRaises(c.CollectionStop):
            c.claude_binary(path)

    def test_immutable_save_does_not_replace_existing_bytes(self):
        path = self.root / "one.json"
        c.save_new(path, {"first": True})
        with self.assertRaises(FileExistsError):
            c.save_new(path, {"first": False})
        self.assertEqual(c.read_json(path), {"first": True})

    def test_http_redirect_refused_without_opening_redirect(self):
        with self.assertRaisesRegex(c.TransportError, "redirect refused"):
            c.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://outside.invalid/")
        with self.assertRaisesRegex(c.CollectionStop, "route not allowed"):
            c.DefaultTransport._http("//outside.invalid/api/generate")

    def test_missing_and_changed_frozen_reservations_stop_before_transport(self):
        job = self.job(model="claude")
        job["reservation_usd"] = "0.00001"
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "frozen reservation"):
            self.run_jobs([job], monitor)
        self.assertEqual(monitor.checked, [])
        del job["reservation_usd"]
        with self.assertRaisesRegex(c.CollectionStop, "frozen reservation"):
            self.run_jobs([job], monitor)

    def test_push_cannot_be_after_even_one_saved_start_on_resume(self):
        job = self.job()
        self.run_jobs([job])
        start = self.root / "collection/starts" / (job["id"] + ".json")
        saved = c.read_json(start)
        saved["started"] = "2025-01-01T00:00:00+00:00"
        self.write(str(start.relative_to(self.root)), saved)
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "push timestamp"):
            self.run_jobs([job], monitor)
        self.assertEqual(monitor.checked, [])

    def test_selecting_claude_cannot_bypass_unstarted_local_calls(self):
        jobs = [self.job(), self.job(model="claude")]
        self.write("config/requests.json", jobs)
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "model order cannot be bypassed"):
            c.run_collection(self.root, models=["claude"], transport=monitor)
        self.assertEqual(monitor.checked, [])

    def test_frozen_request_order_is_preserved(self):
        jobs = [self.job(i) for i in (8, 1, 4, 0)]
        monitor = FakeMonitor()
        self.run_jobs(jobs, monitor)
        self.assertEqual(monitor.calls, [job["id"] for job in jobs])

    def test_default_http_transport_fake_monitor_exact_request_and_metadata(self):
        job = self.job()
        cfg = c.model_config(self.config, "qwen7b")
        captured = []

        class Reply(io.BytesIO):
            pass

        class OfflineOpener:
            def open(self, request, timeout):
                captured.append((request.full_url, request.data, timeout))
                route = request.full_url.removeprefix(c.ENDPOINT)
                body = {
                    "/api/tags": {"models": [{"name": cfg["tag"], "digest": cfg["digest"]}]},
                    "/api/version": {"version": "0.33.3"},
                    "/api/show": {"template": "frozen template", "system": "", "parameters": ""},
                    "/api/ps": {"models": []},
                    "/api/generate": {"model": cfg["tag"], "response": '{"violation":null}',
                                      "prompt_eval_count": 100, "eval_count": 7, "done_reason": "stop"},
                }[route]
                return Reply(c.canonical(body).encode())

        with patch("urllib.request.build_opener", return_value=OfflineOpener()):
            result = self.run_jobs([job], c.DefaultTransport(self.root))
        self.assertEqual(result["completed"], 1)
        self.assertEqual([url for url, _, _ in captured], [c.ENDPOINT + path for path in
            ("/api/tags", "/api/version", "/api/show", "/api/ps", "/api/generate")])
        self.assertEqual(captured[-1][1], c.canonical(job["request"]).encode())
        self.assertEqual(captured[-1][2], 180)

    def test_claude_adaptation_exact_flags_no_credential_env_and_local_temp(self):
        job = self.job(model="claude")
        cfg = c.model_config(self.config, "claude")
        transport = c.DefaultTransport(self.root)
        transport.binary = "/test/claude"
        seen = []

        def fake_run(cmd, **kwargs):
            seen.append((cmd, kwargs))
            return types.SimpleNamespace(returncode=0, stderr="", stdout=c.canonical({
                "result": '{"violation":false}', "num_turns": 1, "usage": {"input_tokens": 100,
                "cache_read_input_tokens": 2, "cache_creation_input_tokens": 3, "output_tokens": 7},
                "modelUsage": {"claude-opus-5-5": {}}, "subtype": "success"}))

        with patch.dict(c.os.environ, {"ANTHROPIC_API_KEY": "do-not-copy", "CLAUDE_CODE_OAUTH_TOKEN": "do-not-copy"}), patch("subprocess.run", side_effect=fake_run):
            result = transport.generate(job, cfg)
        cmd, kwargs = seen[0]
        self.assertEqual(cmd, ["/test/claude", "-p", "--safe-mode", "--restricted", "--strict-mcp-config", "--tools", "",
            "--disable-slash-commands", "--no-chrome", "--output-format", "json", "--model", "claude-opus-5-5",
            "--effort", "medium", "--system-prompt", c.SYSTEM])
        self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", kwargs["env"])
        self.assertTrue(Path(kwargs["cwd"]).is_relative_to(self.root / "collection/tmp"))
        self.assertEqual(kwargs["timeout"], 420)
        self.assertEqual(result["input_tokens"], 105)
        self.assertEqual(result["returned_model"], "claude-opus-5-5")

    def test_active_local_cap_refuses_call_with_insufficient_time_remaining(self):
        prior, pending = self.job(), self.job(1)
        self.write("collection/starts/" + prior["id"] + ".json", dict(prior,
            started="2026-01-02T00:00:00+00:00", freeze_sha256=c.sha((self.root / "freeze.json").read_bytes())))
        self.write("collection/calls/" + prior["id"] + ".json", dict(prior, status="response",
            text="{}", seconds=43100, finished="2026-01-02T12:00:00+00:00"))
        self.write("collection/activity/prior.start.json", {"reserved_seconds": 43200})
        self.write("collection/activity/prior.settle.json", {"elapsed_seconds": 43100})
        monitor = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "12-hour"):
            self.run_jobs([prior, pending], monitor)
        self.assertEqual(monitor.checked, [])

    def test_active_segment_counts_metadata_generation_and_receipt_fsync(self):
        clock = [0.0]
        monitor = FakeMonitor()
        original_preflight, original_generate, original_save = monitor.preflight, monitor.generate, c.save_new

        def preflight(model, cfg):
            clock[0] += 40
            return original_preflight(model, cfg)

        def generate(job, cfg):
            clock[0] += 180
            return original_generate(job, cfg)

        def save(path, value):
            result = original_save(path, value)
            clock[0] += 2
            return result

        monitor.preflight, monitor.generate = preflight, generate
        with patch("sos_collect.time.monotonic", side_effect=lambda: clock[0]), patch("sos_collect.save_new", side_effect=save):
            result = self.run_jobs([self.job()], monitor)
        receipt = next((self.root / "collection/calls").glob("*.json"))
        self.assertEqual(c.read_json(receipt)["seconds"], 180)
        self.assertGreaterEqual(result["local_active_seconds"], 228)
        self.assertEqual(c.ActiveBudget(self.root / "collection/activity").charged, result["local_active_seconds"])

    def test_unsettled_metadata_crash_reserves_full_timeout_and_cap(self):
        clock = [0.0]
        directory = self.root / "collection/activity"
        budget = c.ActiveBudget(directory, cap=220, clock=lambda: clock[0])
        with self.assertRaises(KeyboardInterrupt):
            with budget.segment(220, "fake-call"):
                clock[0] += 5
                raise KeyboardInterrupt()
        resumed = c.ActiveBudget(directory, cap=220, clock=lambda: clock[0])
        self.assertEqual(resumed.charged, 220)
        with self.assertRaisesRegex(c.CollectionStop, "12-hour"):
            resumed.begin(1)

    def test_activity_settlement_replaces_reservation_without_double_counting(self):
        clock = [0.0]
        directory = self.root / "collection/activity"
        budget = c.ActiveBudget(directory, clock=lambda: clock[0])
        with budget.segment(220):
            clock[0] = 12.5
        with budget.segment(180):
            clock[0] = 20
        self.assertEqual(budget.charged, 20)
        self.assertEqual(c.ActiveBudget(directory).charged, 20)

    def test_diagnosed_recovery_resumes_only_unstarted_jobs_and_keeps_failures(self):
        jobs = [self.job(i) for i in range(4)]
        with self.assertRaisesRegex(c.CollectionStop, "three consecutive"):
            self.run_jobs(jobs, FakeMonitor(c.TransportError("unavailable")))
        original = {path.name: path.read_bytes() for path in (self.root / "collection/calls").glob("*.json")}
        certificate = c.acknowledge_recovery(self.root, "Offline diagnosis: temporary monitor failure resolved.")
        self.assertTrue(certificate.is_relative_to(self.root / "collection/recoveries"))
        cert_bytes = certificate.read_bytes()
        monitor = FakeMonitor()
        result = self.run_jobs(jobs, monitor)
        self.assertEqual(result["completed"], 1)
        self.assertEqual(monitor.calls, [jobs[-1]["id"]])
        for name, raw in original.items():
            self.assertEqual((self.root / "collection/calls" / name).read_bytes(), raw)
        self.assertEqual(certificate.read_bytes(), cert_bytes)

    def test_old_recovery_cannot_bypass_three_new_failures_across_resumes(self):
        jobs = [self.job(i) for i in range(7)]
        with self.assertRaises(c.CollectionStop):
            self.run_jobs(jobs, FakeMonitor(c.TransportError("first outage")))
        certificate = c.acknowledge_recovery(self.root, "First outage diagnosed offline.")
        first_bytes = certificate.read_bytes()
        # A new batch with fewer than three failures remains resumable.
        first_next = jobs[:4]
        self.run_jobs(first_next, FakeMonitor(c.TransportError("second outage")))
        monitor = FakeMonitor(c.TransportError("second outage"))
        with self.assertRaisesRegex(c.CollectionStop, "three consecutive"):
            self.run_jobs(jobs, monitor)
        self.assertEqual(len(monitor.calls), 2)
        blocked = FakeMonitor()
        with self.assertRaisesRegex(c.CollectionStop, "three consecutive"):
            self.run_jobs(jobs, blocked)
        self.assertEqual(blocked.calls, [])
        second = c.acknowledge_recovery(self.root, "Second outage diagnosed independently offline.")
        self.assertNotEqual(second, certificate)
        self.assertEqual(certificate.read_bytes(), first_bytes)
        self.assertEqual(self.run_jobs(jobs)["completed"], 1)

    def test_recovery_requires_reason_idle_collector_and_unchanged_failure_hashes(self):
        jobs = [self.job(i) for i in range(4)]
        with self.assertRaises(c.CollectionStop):
            self.run_jobs(jobs, FakeMonitor(c.TransportError("outage")))
        with self.assertRaisesRegex(c.CollectionStop, "reason"):
            c.acknowledge_recovery(self.root, " ")
        cert = c.acknowledge_recovery(self.root, "Offline diagnosis completed.")
        changed = c.read_json(cert)
        changed["receipt_sha256"][jobs[0]["id"]] = "wrong"
        self.write(str(cert.relative_to(self.root)), changed)
        with self.assertRaisesRegex(c.CollectionStop, "receipt hash mismatch"):
            self.run_jobs(jobs)


if __name__ == "__main__":
    unittest.main()
