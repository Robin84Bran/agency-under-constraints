"""Frozen, serial Ollama collection. Importing this module performs no I/O.

Tests inject a byte transport; only HTTPTransport can access the project endpoint.
A start without a receipt is uncertain and is never dispatched again.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import time
import uuid

MODELS = ("qwen7b", "llama8b")
ENDPOINT = "http://127.0.0.1:11435"
OPTIONS = {"temperature": 0.6, "top_k": 16, "num_predict": 192}
PINS = {
    "qwen7b": ("qwen2.5:7b", "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"),
    "llama8b": ("llama3.1:8b", "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"),
}


class IntegrityError(RuntimeError):
    pass


class ResourceStop(RuntimeError):
    pass


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def exclusive_json(path, value):
    """Exclusive creation: even partial saved files are never replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def key_for(item_id, view):
    return hashlib.sha256((item_id + "|" + view).encode()).hexdigest()


def parse_verdict(raw):
    """Exactly boolean or null; missing, integers and strings are failures."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return None, "TECHNICAL_FAILURE"
    if not isinstance(value, dict) or "violation" not in value:
        return None, "TECHNICAL_FAILURE"
    verdict = value["violation"]
    if verdict is None or type(verdict) is bool:
        return verdict, "OK"
    return None, "TECHNICAL_FAILURE"


def replay_sample(items):
    """Two response/truth-blind IDs per source/view/generating-actor stratum."""
    strata = {}
    for item in items:
        for view in ("final", "trace"):
            row = {"id": item["id"], "view": view, "source": item["source"], "actor": item["actor"]}
            strata.setdefault((item["source"], view, item["actor"]), []).append(row)
    if len(strata) != 12:
        raise IntegrityError("Replay selection requires exactly 12 source/view/actor strata")
    selected = []
    for stratum, rows in sorted(strata.items()):
        if len(rows) < 2:
            raise IntegrityError("Replay stratum has fewer than two IDs: " + str(stratum))
        rows.sort(key=lambda r: (hashlib.sha256(("work-or-proof-r2-replay|" + r["id"] + "|" + r["view"]).encode()).hexdigest(), r["id"]))
        selected.extend(rows[:2])
    return sorted(selected, key=lambda row: (row["id"], ("final", "trace").index(row["view"])))


class HTTPTransport:
    """No proxies, redirects or alternate host/port; never pulls a model."""
    def __init__(self, endpoint=ENDPOINT):
        if endpoint != ENDPOINT:
            raise IntegrityError("Only the project-owned Ollama endpoint is permitted")
        self.endpoint = endpoint

    def __call__(self, path, payload, timeout):
        if path not in ("/api/version", "/api/tags", "/api/show", "/api/generate"):
            raise IntegrityError("Disallowed API route")
        import urllib.request
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                raise IntegrityError("Redirect forbidden")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(self.endpoint + path, data=None if payload is None else canonical(payload), headers={"Content-Type": "application/json"}, method="GET" if payload is None else "POST")
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise OSError("Ollama HTTP status " + str(response.status))
            return response.read()


class ActiveBudget:
    """Persisted active seconds with conservative, crash-safe reservations.

    Each segment reserves all of its possible timed HTTP requests. A crash charges the whole reservation;
    completed segments settle to measured monotonic elapsed seconds. A segment
    begins before metadata and CPU work, so setup and failures are charged too.
    Only the final in-flight segment may exceed the 12-hour dispatch allowance.
    """
    def __init__(self, root, cap=43200, monotonic=time.monotonic):
        self.directory = Path(root) / "collection" / "activity"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cap = cap
        self.clock = monotonic
        self.segment = None
        self._cache_total = None
        self._cache_mtime = None

    def _remember(self, total):
        self._cache_total = total
        self._cache_mtime = self.directory.stat().st_mtime_ns

    def charged(self):
        if self._cache_mtime == self.directory.stat().st_mtime_ns and self._cache_total is not None:
            return self._cache_total
        total = 0.0
        for start in sorted(self.directory.glob("*.start.json")):
            data = read_json(start)
            settlement = start.with_name(start.name.replace(".start.json", ".settle.json"))
            if settlement.exists():
                elapsed = read_json(settlement)["elapsed_seconds"]
                if not isinstance(elapsed, (float, int)) or not math.isfinite(elapsed) or elapsed < 0:
                    raise IntegrityError("Invalid active-time settlement")
                total += elapsed
            else:
                reservation = data["reserved_seconds"]
                if type(reservation) not in (int, float) or not math.isfinite(reservation) or reservation <= 0:
                    raise IntegrityError("Invalid active-time reservation")
                total += reservation
        self._remember(total)
        return total

    def begin(self, reserved_seconds=180):
        if self.segment:
            raise IntegrityError("Active segment already open")
        previous = self.charged()
        if previous >= self.cap:
            raise ResourceStop("12-hour cumulative active collection cap exhausted")
        token = uuid.uuid4().hex
        self.segment = (token, self.clock(), reserved_seconds)
        exclusive_json(self.directory / (token + ".start.json"), {"started_at": utcnow(), "reserved_seconds": reserved_seconds, "crash_accounting": "unsettled segment conservatively charged in full"})
        self._remember(previous + reserved_seconds)

    def settle(self):
        if self.segment is None:
            return
        token, start, reservation = self.segment
        elapsed = max(0.0, self.clock() - start)
        previous = self.charged()
        exclusive_json(self.directory / (token + ".settle.json"), {"finished_at": utcnow(), "elapsed_seconds": elapsed})
        self.segment = None
        self._remember(previous + elapsed - reservation)

    def remaining(self):
        charged = self.charged()
        if self.segment is not None:
            token, start, reservation = self.segment
            charged += max(0.0, self.clock() - start) - reservation
        return self.cap - charged


def _timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone missing")
        return parsed
    except (TypeError, ValueError) as error:
        raise IntegrityError("Invalid timezone-aware timestamp") from error


def validate_config(config):
    if config.get("endpoint") != ENDPOINT or config.get("timeout_seconds") != 180 or config.get("active_cap_seconds") != 43200 or config.get("request_options") != OPTIONS:
        raise IntegrityError("Frozen collection settings do not match protocol")
    if config.get("stream", False) is not False or config.get("format", "json") != "json":
        raise IntegrityError("Frozen stream/format settings do not match protocol")
    models = config.get("models", [])
    if [m.get("name") for m in models] != list(MODELS):
        raise IntegrityError("Models must be Qwen then Llama")
    for model in models:
        if (model.get("tag"), model.get("digest", "").removeprefix("sha256:")) != PINS[model["name"]]:
            raise IntegrityError("Frozen model pin does not match protocol")


def validate_push(root):
    path = Path(root) / "freeze.json"
    if not path.is_file():
        raise IntegrityError("Missing freeze")
    freeze_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    push = read_json(Path(root) / "collection" / "push.json")
    if push.get("freeze_sha256") != freeze_hash:
        raise IntegrityError("Push attestation is for another freeze")
    for field in ("remote", "commit", "server_timestamp_source"):
        if not isinstance(push.get(field), str) or not push[field].strip():
            raise IntegrityError("Missing push attestation " + field)
    if _timestamp(push.get("pushed_at")) >= dt.datetime.now(dt.timezone.utc):
        raise IntegrityError("Push timestamp must precede dispatch")
    starts = list((Path(root) / "collection" / "calls").glob("*/*.start.json")) + list((Path(root) / "collection" / "replays").glob("*/*.start.json"))
    for start in starts:
        if _timestamp(push["pushed_at"]) >= _timestamp(read_json(start)["started_at"]):
            raise IntegrityError("Push did not precede first saved call")
    return freeze_hash, push


def _get_json(transport, path, payload=None):
    raw = transport(path, payload, 180)
    if not isinstance(raw, bytes):
        raise IntegrityError("Transport must return raw HTTP bytes")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise IntegrityError("Invalid metadata JSON for " + path) from error
    if not isinstance(result, dict):
        raise IntegrityError("Invalid metadata object for " + path)
    return result


def _identity(transport, model):
    tags = _get_json(transport, "/api/tags")
    matches = [m for m in tags.get("models", []) if m.get("name", m.get("model")) == model["tag"]]
    if len(matches) != 1 or matches[0].get("digest", "").removeprefix("sha256:") != model["digest"].removeprefix("sha256:"):
        raise IntegrityError("Ollama model digest mismatch: " + model["name"])
    shown = _get_json(transport, "/api/show", {"model": model["tag"]})
    # Preserve context/defaults and architecture; no inference readiness probe.
    return {"tag": model["tag"], "digest": model["digest"], "show": shown, "tag_details": matches[0]}


def _usage(response):
    values = [response.get("prompt_eval_count"), response.get("eval_count")]
    valid = [type(v) is int and v >= 0 for v in values]
    return {"input_tokens": values[0] if valid[0] else None, "output_tokens": values[1] if valid[1] else None,
            "total_tokens": sum(values) if all(valid) else None,
            "status": "OK" if all(valid) else "UNKNOWN", "reason": None if all(valid) else "Missing or invalid Ollama token counts"}


def _validate_existing(path, expected):
    data = read_json(path)
    for field in ("id", "view", "model", "seed", "prompt", "request", "digest", "freeze_sha256"):
        if data.get(field) != expected.get(field):
            raise IntegrityError("Saved call identity/config changed: " + str(path) + " field " + field)
    return data


def _job(root, item, view, model, replay, transport, runtime, freeze_hash, budget, clock):
    directory = Path(root) / "collection" / ("replays" if replay else "calls") / model["name"]
    stem = key_for(item["id"], view)
    receipt = directory / (stem + ".json")
    start = directory / (stem + ".start.json")
    prompt = item[view]["prompt"]
    if hashlib.sha256(prompt.encode()).hexdigest() != item[view]["prompt_sha256"]:
        raise IntegrityError("Prompt hash mismatch")
    request = {"model": model["tag"], "prompt": prompt, "stream": False, "format": "json", "options": dict(OPTIONS, seed=item["seed"])}
    record = {"id": item["id"], "view": view, "source": item["source"], "actor": item["actor"], "model": model["name"], "tag": model["tag"], "digest": model["digest"], "seed": item["seed"], "prompt": prompt, "prompt_sha256": item[view]["prompt_sha256"], "request": request, "freeze_sha256": freeze_hash, "replay": replay, "runtime": runtime, "endpoint": ENDPOINT}
    if receipt.exists():
        _validate_existing(receipt, record)
        if not start.exists():
            raise IntegrityError("Receipt without saved start")
        return "saved"
    if start.exists():
        _validate_existing(start, record)
        return "uncertain"
    if budget.remaining() <= 0:
        raise ResourceStop("12-hour cap exhausted before dispatch")
    # Bind observed digest and settings before every inference dispatch.
    if _get_json(transport, "/api/version") != runtime["version"]:
        raise IntegrityError("Runtime version drift")
    identity = _identity(transport, model)
    if identity != runtime["models"][model["name"]]:
        raise IntegrityError("Runtime model identity/defaults drift")
    if budget.remaining() <= 0:
        raise ResourceStop("12-hour cap exhausted during metadata checks")
    record["started_at"] = utcnow()
    exclusive_json(start, record)
    t0 = clock()
    raw = None
    response = None
    failure = None
    fatal = None
    try:
        raw = transport("/api/generate", request, 180)
        if not isinstance(raw, bytes):
            raise TypeError("Transport did not return bytes")
        response = json.loads(raw)
        if not isinstance(response, dict):
            raise ValueError("Response is not an object")
        if response.get("model") != model["tag"]:
            fatal = "Returned model identity mismatch"
        if response.get("done") is not True or response.get("error"):
            failure = "Incomplete/error Ollama response"
        if response.get("done_reason") not in (None, "stop", "length"):
            failure = "Unexpected Ollama stop reason"
    except Exception as error:
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        failure = type(error).__name__ + ": " + str(error)
    seconds = max(0.0, clock() - t0)
    raw_reply = response.get("response") if isinstance(response, dict) else None
    verdict, status = parse_verdict(raw_reply)
    if failure or fatal:
        verdict, status = None, "TECHNICAL_FAILURE"
    record.update({"finished_at": utcnow(), "seconds": seconds, "status": status, "verdict": verdict,
                   "error": fatal or failure, "raw_reply": raw_reply, "raw_http_reply": raw.decode("utf-8", errors="replace") if raw is not None else None,
                   "raw_http_reply_base64": base64.b64encode(raw).decode() if isinstance(raw, bytes) else None,
                   "response": response, "usage": _usage(response or {}), "usd": 0,
                   "stop_reason": response.get("done_reason") if isinstance(response, dict) else None})
    exclusive_json(receipt, record)
    if fatal:
        raise IntegrityError(fatal)
    return "completed" if status == "OK" else "failed"


def load_first_responses(root):
    result = {}
    directory = Path(root) / "collection" / "calls"
    for model in MODELS:
        for path in sorted((directory / model).glob("*.json")):
            if path.name.endswith(".start.json"):
                continue
            record = read_json(path)
            usage = record.get("usage", {})
            row = dict(record)
            row["call"] = {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"), "usd": record.get("usd"), "seconds": record.get("seconds")}
            result[(model, record["id"], record["view"])] = row
        for path in sorted((directory / model).glob("*.start.json")):
            record = read_json(path)
            key = (model, record["id"], record["view"])
            if key not in result:
                result[key] = dict(record, verdict=None, status="UNCERTAIN", call={"input_tokens": None, "output_tokens": None, "usd": 0, "seconds": None})
    return result


def collection_summary(root):
    summary = {"attempted": 0, "completed": 0, "failed": 0, "uncertain": 0, "replay_attempted": 0, "replay_completed": 0, "returned": 0, "technical_reply_failures": 0, "transport_or_protocol_failures": 0, "by_model": {}, "replays": {}}
    for model in MODELS:
        counts = {"attempted": 0, "completed": 0, "failed": 0, "uncertain": 0, "input_tokens": 0, "output_tokens": 0, "usage_status": "OK", "seconds": 0.0, "seconds_status": "OK", "returned": 0, "technical_reply_failures": 0, "transport_or_protocol_failures": 0, "by_phase": {}}
        replay_rows = {}
        for phase in ("calls", "replays"):
            phase_counts = {"attempted": 0, "returned": 0, "technical_reply_failures": 0, "transport_or_protocol_failures": 0, "uncertain": 0, "observed_input_tokens": 0, "observed_output_tokens": 0, "observed_seconds": 0.0, "resource_status": "OK"}
            counts["by_phase"][phase] = phase_counts
            for start in sorted((Path(root) / "collection" / phase / model).glob("*.start.json")):
                counts["attempted"] += 1
                phase_counts["attempted"] += 1
                summary["attempted"] += 1
                receipt = start.with_name(start.name.replace(".start.json", ".json"))
                if phase == "replays":
                    summary["replay_attempted"] += 1
                if not receipt.exists():
                    counts["uncertain"] += 1
                    summary["uncertain"] += 1
                    counts["usage_status"] = "UNKNOWN"
                    counts["seconds_status"] = "UNKNOWN"
                    phase_counts["uncertain"] += 1
                    phase_counts["resource_status"] = "UNKNOWN"
                    continue
                record = read_json(receipt)
                classification = "transport_or_protocol_failures" if record.get("error") else ("technical_reply_failures" if record["status"] != "OK" else None)
                if classification:
                    counts[classification] += 1
                    summary[classification] += 1
                    phase_counts[classification] += 1
                if not record.get("error"):
                    counts["returned"] += 1
                    summary["returned"] += 1
                    phase_counts["returned"] += 1
                outcome = "completed" if record["status"] == "OK" else "failed"
                counts[outcome] += 1
                summary[outcome] += 1
                if phase == "replays" and outcome == "completed":
                    summary["replay_completed"] += 1
                for token in ("input_tokens", "output_tokens"):
                    value = record["usage"][token]
                    if value is None:
                        counts["usage_status"] = "UNKNOWN"
                        phase_counts["resource_status"] = "UNKNOWN"
                    else:
                        counts[token] += value
                        phase_counts["observed_" + token] += value
                counts["seconds"] += record["seconds"]
                phase_counts["observed_seconds"] += record["seconds"]
                if phase == "replays":
                    first = Path(root) / "collection" / "calls" / model / receipt.name
                    original = read_json(first) if first.exists() else None
                    stratum = "|".join((record["source"], record["view"], record["actor"]))
                    row = replay_rows.setdefault(stratum, {"attempts": 0, "raw_identical": 0, "verdict_identical": 0})
                    row["attempts"] += 1
                    row["raw_identical"] += int(original is not None and record["raw_reply"] is not None and record["raw_reply"] == original["raw_reply"])
                    row["verdict_identical"] += int(original is not None and record["status"] == original["status"] == "OK" and record["verdict"] == original["verdict"])
        for phase_counts in counts["by_phase"].values():
            for field in ("input_tokens", "output_tokens", "seconds"):
                phase_counts[field] = phase_counts["observed_" + field] if phase_counts["resource_status"] == "OK" else None
        if counts["seconds_status"] == "UNKNOWN":
            counts["observed_seconds"] = counts["seconds"]
            counts["seconds"] = None
        if counts["usage_status"] == "UNKNOWN":
            counts["observed_input_tokens"] = counts["input_tokens"]
            counts["observed_output_tokens"] = counts["output_tokens"]
            counts["input_tokens"] = counts["output_tokens"] = None
        summary["by_model"][model] = counts
        summary["replays"][model] = replay_rows
    return summary


def _collect_locked(root, transport=None, monotonic=time.monotonic, verify=None):
    root = Path(root)
    if verify is None:
        from wop_freeze import verify_freeze
        verify = verify_freeze
    verify(root)
    config = read_json(root / "config" / "collector.json")
    validate_config(config)
    freeze_hash, push = validate_push(root)
    items = read_json(root / "imported" / "dataset.json")["items"]
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise IntegrityError("Duplicate source-qualified IDs")
    expected_sample = replay_sample(items)
    frozen_sample = read_json(root / "config" / "replay_sample.json")
    if isinstance(frozen_sample, dict):
        frozen_sample = frozen_sample.get("items", frozen_sample.get("sample"))
    if frozen_sample != expected_sample:
        raise IntegrityError("Frozen replay selection mismatch")
    transport = transport or HTTPTransport(config["endpoint"])
    budget = ActiveBudget(root, config["active_cap_seconds"], monotonic)
    runtime_path = root / "collection" / "runtime.json"
    stopped = None
    try:
        budget.begin(1260)
        version = _get_json(transport, "/api/version")
        expected_version = config.get("runtime_version", config.get("expected_runtime_version", "0.33.3"))
        if version.get("version") != expected_version:
            raise IntegrityError("Ollama runtime version mismatch")
        runtime = {"version": version, "models": {m["name"]: _identity(transport, m) for m in config["models"]}, "endpoint": ENDPOINT,
                   "environment": config.get("environment", config.get("runtime_identity", {}))}
        if runtime_path.exists():
            if read_json(runtime_path) != runtime:
                raise IntegrityError("Runtime identity/defaults changed across resume")
        else:
            exclusive_json(runtime_path, runtime)
        budget.settle()
        for replay in (False, True):
            sample_keys = {(r["id"], r["view"]) for r in expected_sample}
            for model in config["models"]:
                for item in sorted(items, key=lambda i: i["id"]):
                    for view in ("final", "trace"):
                        if replay and (item["id"], view) not in sample_keys:
                            continue
                        budget.begin(720)
                        try:
                            _job(root, item, view, model, replay, transport, runtime, freeze_hash, budget, monotonic)
                        finally:
                            budget.settle()
    except ResourceStop as error:
        stopped = str(error)
    finally:
        budget.settle()
    summary = collection_summary(root)
    summary.update({"active_seconds_charged": budget.charged(), "active_cap_seconds": config["active_cap_seconds"], "stop_reason": stopped,
                    "planned_primary": len(items) * 4, "planned_replays": len(expected_sample) * 2,
                    "freeze_sha256": freeze_hash, "push": push, "new_frontier_calls": 0, "new_model_call_usd": 0})
    exclusive_json(root / "collection" / "summaries" / (uuid.uuid4().hex + ".json"), summary)
    return summary


def collect(root, transport=None, monotonic=time.monotonic, verify=None):
    """One serial collector per project, with an OS lock released on crashes."""
    root = Path(root)
    directory = root / "collection"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "collector.lock").open("a+b") as handle:
        try:
            import fcntl
        except ImportError:
            import msvcrt
            handle.seek(0)
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise IntegrityError("Another collector holds the project lock") from error
            try:
                return _collect_locked(root, transport, monotonic, verify)
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise IntegrityError("Another collector holds the project lock") from error
            try:
                return _collect_locked(root, transport, monotonic, verify)
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(collect(args.root), indent=2))
