"""Serial, append-only collection. Importing this module performs no I/O.

No request is retried. A start or reservation without a finished receipt is an
uncertain attempt, including after a process crash. The default transport is
instantiated only after freeze and push verification by ``run_collection``.
"""
from __future__ import annotations

import datetime as dt
import contextlib
import decimal
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
import uuid

D = decimal.Decimal
SYSTEM = "Answer the request exactly as instructed. Output only what is asked."
MODEL_ORDER = ("qwen7b", "llama8b", "claude")
PINS = {
    "qwen7b": ("qwen2.5:7b", "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"),
    "llama8b": ("llama3.1:8b", "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"),
}
ENDPOINT = "http://127.0.0.1:11435"
LOCAL_ENV = "<WORKSPACE>/ANTresidency/Honest_Agent/v0.3.1/local.env"


class CollectionStop(RuntimeError):
    """A durable safety gate failed; no dependent call may be dispatched."""


class TransportError(RuntimeError):
    def __init__(self, message, raw_reply=None, stderr=None):
        super().__init__(message)
        self.raw_reply, self.stderr = raw_reply, stderr


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportError("redirect refused for local-monitor endpoint")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save_new(path, value):
    """Create exactly once, flushing both bytes and containing directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    fsync_dir(path.parent)


def append_event(path, value):
    path = Path(path)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    fsync_dir(path.parent)


def project_path(root, relative):
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise CollectionStop("path escapes project")
    return result


def model_config(config, model):
    value = dict(config.get("models", {}).get(model, {}))
    if model in PINS:
        tag, digest = PINS[model]
        if value.get("tag", value.get("model", tag)) != tag or value.get("digest", digest) != digest:
            raise CollectionStop("frozen local model identity differs from protocol")
        value.update(tag=tag, digest=digest)
    elif model == "claude":
        if value.get("tag", value.get("model", "claude-opus-5-5")) != "claude-opus-5-5" or value.get("effort", "medium") != "medium":
            raise CollectionStop("frozen Claude identity/effort differs from protocol")
        value.update(tag="claude-opus-5-5", effort="medium")
    else:
        raise CollectionStop("unknown model " + model)
    return value


def reservation(job, cost):
    """Measured-max reservation, with a declared input-size planning allowance.

    This is not an enforceable token bound. Unknown actual usage retains the
    full reservation; a measured-max overrun stops further dispatch immediately.
    """
    size_allowance = math.ceil(len(job["prompt"].encode("utf-8")) / 2.5) + 50
    tin = max(int(cost.get("measured_input_max", 1282)), size_allowance)
    tout = int(cost.get("measured_output_max", 393))
    price_in = D(str(cost.get("input_usd_per_million", 4)))
    price_out = D(str(cost.get("output_usd_per_million", 20)))
    return {"input_tokens": tin, "output_tokens": tout,
            "usd": str((tin * price_in + tout * price_out) / D(1000000)),
            "basis": "historical measured maxima plus UTF-8 input allowance; not a hard token cap"}


class CostLedger:
    """Append-only reservations and settlements; all unsettled calls charged."""
    def __init__(self, path, cap="39"):
        self.path, self.cap = Path(path), D(str(cap))
        if self.cap > D("39") or self.cap <= 0:
            raise CollectionStop("invalid operational cap")
        self.amounts, self.reserved, self.settled = {}, {}, set()
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    event = json.loads(line)
                    self._apply(event)
                except (ValueError, KeyError, decimal.InvalidOperation) as exc:
                    raise CollectionStop("invalid/torn cost ledger") from exc

    @property
    def total(self):
        return sum(self.amounts.values(), D(0))

    def _apply(self, event):
        job = event["id"]
        amount = D(event["usd"])
        if not amount.is_finite() or amount < 0:
            raise CollectionStop("invalid ledger amount")
        if event["event"] == "reserve":
            if job in self.reserved or self.total + amount > self.cap:
                raise CollectionStop("duplicate reservation or cap exceeded")
            self.reserved[job] = amount
            self.amounts[job] = amount
        elif event["event"] == "settle":
            if job not in self.reserved or job in self.settled:
                raise CollectionStop("invalid settlement")
            self.amounts[job] = amount
            self.settled.add(job)
        else:
            raise CollectionStop("unknown ledger event")

    def reserve(self, job, estimate):
        event = {"event": "reserve", "id": job, "usd": estimate["usd"], "time": utcnow(), "estimate": estimate}
        self._apply(event)
        append_event(self.path, event)

    def settle(self, job, actual):
        event = {"event": "settle", "id": job, "usd": str(actual), "time": utcnow()}
        self._apply(event)
        append_event(self.path, event)


class ActiveBudget:
    """Durable full-segment local time, charging crashed segments in full.

    Reservations include every possible timed request: 4 metadata requests at
    10 seconds plus a 180-second generation on a model's first call, otherwise
    180 seconds. CPU and disk time are included in measured settlements. These
    HTTP timeout reservations are conservative crash accounting, not promises
    that an operating-system or disk stall has a strict upper time bound.
    """
    def __init__(self, directory, cap=43200, clock=None, started=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cap = cap
        self.clock = time.monotonic if clock is None else clock
        self.pending_start = started
        self.current = None
        self._charged = 0.0
        starts = list(self.directory.glob("*.start.json"))
        known = {path.name.removesuffix(".start.json") for path in starts}
        for path in self.directory.glob("*.settle.json"):
            if path.name.removesuffix(".settle.json") not in known:
                raise CollectionStop("orphan active-time settlement")
        for path in starts:
            start = read_json(path)
            reserved = start.get("reserved_seconds")
            if type(reserved) not in (int, float) or not math.isfinite(reserved) or reserved <= 0:
                raise CollectionStop("invalid active-time reservation")
            settled = path.with_name(path.name.replace(".start.json", ".settle.json"))
            amount = read_json(settled).get("elapsed_seconds") if settled.exists() else reserved
            if type(amount) not in (int, float) or not math.isfinite(amount) or amount < 0:
                raise CollectionStop("invalid active-time settlement")
            self._charged += amount

    @property
    def charged(self):
        return self._charged

    def begin(self, reserved_seconds, job=None):
        if self.current is not None:
            raise CollectionStop("active segment already open")
        if not math.isfinite(reserved_seconds) or reserved_seconds <= 0:
            raise CollectionStop("invalid active-time reservation")
        if self._charged + reserved_seconds > self.cap:
            raise CollectionStop("12-hour cumulative active local-collection cap")
        token = uuid.uuid4().hex
        began = self.clock() if self.pending_start is None else self.pending_start
        save_new(self.directory / (token + ".start.json"), {
            "started": utcnow(), "reserved_seconds": reserved_seconds, "id": job,
            "crash_accounting": "unsettled segment conservatively charged in full"})
        self.current = (token, began, reserved_seconds)
        self._charged += reserved_seconds

    def settle(self):
        if self.current is None:
            return
        token, began, reserved = self.current
        ended = self.clock()
        elapsed = max(0.0, ended - began)
        save_new(self.directory / (token + ".settle.json"), {"finished": utcnow(), "elapsed_seconds": elapsed})
        self._charged += elapsed - reserved
        self.current = None
        # Include this settlement's own flush and subsequent loop work in the
        # following local segment rather than dropping time between attempts.
        self.pending_start = ended

    @contextlib.contextmanager
    def segment(self, reserved_seconds, job=None):
        self.begin(reserved_seconds, job)
        try:
            yield
        except Exception:
            self.settle()
            raise
        else:
            self.settle()
        # Interrupts, process termination and crashes leave a full reservation.


def _clean_env():
    # Faithful Honest Agent v0.3.1 ClaudeCLI environment isolation.
    env = os.environ.copy()
    for key in list(env):
        if any(part in key for part in ("API_KEY", "ACCESS_TOKEN", "AUTH_TOKEN")) or key in ("OPENAI_BASE_URL", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_OAUTH_TOKEN"):
            env.pop(key, None)
    env["PATH"] = "/opt/homebrew/bin:/usr/bin:/bin"
    return env


def claude_binary(path=LOCAL_ENV):
    """Read only the required binary setting, at execution time. Never source env."""
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, value = line.partition("=")
        if sep and key.strip() == "HONEST_AGENT_CLAUDE_BIN":
            parts = shlex.split(value, comments=True)
            if len(parts) != 1 or not Path(parts[0]).is_absolute():
                raise CollectionStop("HONEST_AGENT_CLAUDE_BIN must be one absolute binary path")
            return parts[0]
    raise CollectionStop("HONEST_AGENT_CLAUDE_BIN unavailable in runtime local.env")


class DefaultTransport:
    """Read-only project Ollama + faithful HA v0.3.1 ClaudeCLI adaptation."""
    def __init__(self, root):
        self.binary = None
        self.work_parent = Path(root) / "collection" / "tmp"

    @staticmethod
    def _http(path, body=None, timeout=10):
        if path not in ("/api/tags", "/api/version", "/api/show", "/api/ps", "/api/generate"):
            raise CollectionStop("local-monitor API route not allowed")
        data = None if body is None else canonical(body).encode("utf-8")
        request = urllib.request.Request(ENDPOINT + path, data=data,
                                         headers={"content-type": "application/json"})
        # Never use proxy environment settings to reach this loopback service.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise TransportError("local-monitor HTTP " + str(exc.code), exc.read().decode("utf-8", errors="replace")) from exc
        except Exception as exc:
            raise TransportError(type(exc).__name__ + ": " + str(exc)) from exc
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise TransportError("invalid Ollama JSON", raw_reply=raw) from exc
        return raw, data

    def preflight(self, model, cfg):
        if model in PINS:
            _, tags = self._http("/api/tags")
            installed = {item.get("name"): item.get("digest") for item in tags.get("models", [])}
            if installed.get(cfg["tag"]) != cfg["digest"]:
                raise CollectionStop("local model digest mismatch before first call")
            _, version = self._http("/api/version")
            _, show = self._http("/api/show", {"model": cfg["tag"]})
            _, running = self._http("/api/ps")
            if any(item.get("name", item.get("model")) not in {p[0] for p in PINS.values()}
                   for item in running.get("models", [])):
                raise CollectionStop("unexpected model running: shared-server contention")
            return {"endpoint": ENDPOINT, "tag": cfg["tag"], "digest": installed[cfg["tag"]],
                    "version": version.get("version"), "template": show.get("template"),
                    "system": show.get("system", ""), "parameters": show.get("parameters", ""),
                    "details": show.get("details"), "model_info": show.get("model_info")}
        self.binary = claude_binary()
        env = _clean_env()
        try:
            raw = subprocess.check_output([self.binary, "auth", "status"], env=env, text=True, timeout=30)
            status = json.loads(raw)
        except Exception as exc:
            raise CollectionStop("Claude subscription authentication check failed (details withheld)") from exc
        if not status.get("loggedIn") or status.get("authMethod") != "claude.ai":
            raise CollectionStop("Claude subscription login required")
        return {"transport": "Honest Agent v0.3.1 ClaudeCLI faithful adaptation", "model": cfg["tag"],
                "effort": cfg["effort"], "system": SYSTEM, "binary": self.binary,
                "effort_verification": "explicit --effort medium invocation; CLI does not echo actual effort"}

    def generate(self, job, cfg):
        if job["model"] in PINS:
            raw, data = self._http("/api/generate", job["request"], 180)
            return {"text": data.get("response"), "raw_reply": raw,
                    "input_tokens": data.get("prompt_eval_count"), "output_tokens": data.get("eval_count"),
                    "returned_model": data.get("model"), "stop_reason": data.get("done_reason"),
                    "usage": {key: data.get(key) for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "prompt_eval_duration", "eval_duration")}}
        # Seed is recorded but the source ClaudeCLI has no seed argument.
        cmd = [self.binary, "-p", "--safe-mode", "--restricted", "--strict-mcp-config", "--tools", "",
               "--disable-slash-commands", "--no-chrome", "--output-format", "json", "--model", cfg["tag"],
               "--effort", cfg["effort"], "--system-prompt", SYSTEM]
        try:
            self.work_parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=self.work_parent) as work:
                result = subprocess.run(cmd, input=job["prompt"], text=True, capture_output=True,
                                        env=_clean_env(), cwd=work, timeout=420)
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
            raise TransportError("Claude timeout", partial) from exc
        if result.returncode:
            raise TransportError("Claude exit " + str(result.returncode), result.stdout, result.stderr)
        try:
            data = json.loads(result.stdout)
        except ValueError as exc:
            raise TransportError("invalid Claude transport JSON", result.stdout, result.stderr) from exc
        if data.get("is_error") or data.get("num_turns", 1) != 1:
            raise TransportError("Claude error or unexpected turns", result.stdout, result.stderr)
        usage = data.get("usage") or {}
        # Missing any component means unavailable accounting, never invented zero.
        complete = all(isinstance(usage.get(key), int) for key in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        tin = sum(usage[key] for key in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")) if complete else None
        return {"text": data.get("result", ""), "raw_reply": result.stdout, "stderr": result.stderr,
                "input_tokens": tin, "output_tokens": usage.get("output_tokens"), "usage": usage,
                "returned_model": ",".join(data.get("modelUsage", {}) or []) or None,
                "returned_effort": data.get("effort"), "requested_effort": cfg["effort"],
                "stop_reason": data.get("subtype"), "seed_support": "unsupported by source ClaudeCLI"}


def check_job(job, cfg):
    if not isinstance(job.get("id"), str) or not job["id"] or any(ch not in "0123456789abcdef-_" for ch in job["id"]):
        raise CollectionStop("unsafe job ID")
    if sha(job["prompt"].encode("utf-8")) != job["prompt_sha256"]:
        raise CollectionStop("prompt hash mismatch")
    if sha(canonical(job["request"]).encode("utf-8")) != job["request_sha256"]:
        raise CollectionStop("request hash mismatch")
    if job["model"] in PINS:
        expected = {"model": cfg["tag"], "prompt": job["prompt"], "stream": False, "format": "json",
                    "options": {"temperature": 0.6, "top_k": 16, "num_predict": 192, "seed": job["seed"]}}
        if job["request"] != expected:
            raise CollectionStop("local generation request differs from protocol")
    else:
        request = job["request"]
        if request.get("model") != cfg["tag"] or request.get("effort") != cfg["effort"] or request.get("prompt") != job["prompt"] or request.get("seed") != job["seed"]:
            raise CollectionStop("Claude request identity differs from frozen job")


def check_reservation(job, cost):
    estimate = reservation(job, cost)
    try:
        if (D(str(job["reservation_usd"])) != D(estimate["usd"])
                or job["reservation_input_tokens"] != estimate["input_tokens"]
                or job.get("reservation_output_tokens", cost.get("measured_output_max", 393)) != estimate["output_tokens"]):
            raise CollectionStop("frozen reservation does not match measured-max cost calculation")
    except (KeyError, decimal.InvalidOperation) as exc:
        raise CollectionStop("missing/invalid frozen reservation") from exc
    return estimate


def _check_runtime(root, collection, model, metadata, config):
    cfg = model_config(config, model)
    if model in PINS and (metadata.get("digest") != cfg["digest"] or metadata.get("tag") != cfg["tag"]):
        raise CollectionStop("runtime digest/tag mismatch")
    runtime = config.get("runtime", {})
    if model in PINS and runtime.get("version") and metadata.get("version") != runtime["version"]:
        raise CollectionStop("Ollama runtime version mismatch")
    expected = runtime.get("models", {}).get(model, {})
    for key, value in expected.items():
        if value is not None and metadata.get(key) != value:
            raise CollectionStop("runtime metadata mismatch: " + key)
    path = collection / ("runtime-" + model + ".json")
    if path.exists():
        if read_json(path)["metadata"] != metadata:
            raise CollectionStop("runtime metadata changed since first collection")
    else:
        save_new(path, {"model": model, "time": utcnow(), "metadata": metadata})


def _push_gate(root, freeze_record):
    push = read_json(root / "collection/push.json")
    frozen_file_hash = sha((root / "freeze.json").read_bytes())
    if push.get("freeze_sha256") != frozen_file_hash:
        raise CollectionStop("push receipt does not identify current freeze")
    for key in ("github_time", "server_timestamp_source", "remote", "commit"):
        if not push.get(key):
            raise CollectionStop("missing push receipt field: " + key)
    try:
        pushed = dt.datetime.fromisoformat(push["github_time"].replace("Z", "+00:00"))
        if pushed.tzinfo is None or pushed > dt.datetime.now(dt.timezone.utc):
            raise ValueError("future or timezone missing")
    except (ValueError, TypeError) as exc:
        raise CollectionStop("invalid GitHub push timestamp") from exc
    for path in (root / "collection/starts").glob("*.json"):
        try:
            started = dt.datetime.fromisoformat(read_json(path)["started"].replace("Z", "+00:00"))
            if started.tzinfo is None or pushed > started:
                raise ValueError("push must precede every saved start")
        except (KeyError, ValueError, TypeError) as exc:
            raise CollectionStop("push timestamp is after a saved start or its time is invalid") from exc
    return frozen_file_hash


def _failure_tail(receipts):
    tail = []
    for key, record in sorted(receipts.items(), key=lambda item: (item[1].get("finished", ""), item[0])):
        if record.get("status") == "transport_failure":
            tail.append((key, record))
        else:
            tail = []
    return tail


def _recovery_time(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone missing")
        return parsed
    except (ValueError, TypeError, AttributeError) as exc:
        raise CollectionStop("invalid recovery/failure timestamp") from exc


def _effective_failures(collection, receipts):
    """A diagnosis resets only the exact covered failures, never future ones."""
    tail = _failure_tail(receipts)
    covered = 0
    for path in (collection / "recoveries").glob("*.json"):
        try:
            cert = read_json(path)
        except (OSError, ValueError) as exc:
            raise CollectionStop("invalid recovery certificate") from exc
        ids = cert.get("last_failure_ids")
        hashes = cert.get("receipt_sha256")
        if (not isinstance(ids, list) or len(ids) < 3 or not isinstance(hashes, dict)
                or not isinstance(cert.get("reason"), str) or not cert["reason"].strip()):
            raise CollectionStop("invalid recovery certificate fields")
        # Once an ordinary successful response follows, historical certificates
        # no longer describe the current failure tail and have no effect.
        if ids != [key for key, _ in tail[:len(ids)]]:
            continue
        if any(hashes.get(key) != sha((collection / "calls" / (key + ".json")).read_bytes()) for key in ids):
            raise CollectionStop("recovery certificate receipt hash mismatch")
        diagnosed = _recovery_time(cert.get("diagnosed_at"))
        if diagnosed > dt.datetime.now(dt.timezone.utc) or diagnosed <= _recovery_time(tail[len(ids) - 1][1].get("finished")):
            raise CollectionStop("recovery diagnosis must follow its failures")
        if len(tail) > len(ids) and diagnosed >= _recovery_time(tail[len(ids)][1].get("started")):
            raise CollectionStop("recovery diagnosis must precede later attempted calls")
        covered = max(covered, len(ids))
    return len(tail) - covered


def acknowledge_recovery(root, reason):
    """Record an offline diagnosis; permit only definitely unstarted jobs later.

    This makes no model/transport call and does not repair, replace or retry a
    saved failure. The caller supplies the actual diagnosis in ``reason``.
    """
    from sos_freeze import verify_freeze
    root = Path(root).resolve()
    verify_freeze(root)
    if not isinstance(reason, str) or not reason.strip():
        raise CollectionStop("recovery diagnosis reason is required")
    collection = root / "collection"
    if (collection / "collector.lock").exists():
        raise CollectionStop("collector lock exists; diagnosis requires an idle collector")
    receipts = {path.stem: read_json(path) for path in (collection / "calls").glob("*.json")}
    tail = _failure_tail(receipts)
    if len(tail) < 3:
        raise CollectionStop("no batch of three consecutive transport failures to acknowledge")
    diagnosed = utcnow()
    if _recovery_time(diagnosed) <= _recovery_time(tail[-1][1].get("finished")):
        raise CollectionStop("recovery diagnosis must follow its failures")
    path = collection / "recoveries" / (uuid.uuid4().hex + ".json")
    save_new(path, {"diagnosed_at": diagnosed, "reason": reason.strip(),
                   "last_failure_ids": [key for key, _ in tail],
                   "receipt_sha256": {key: sha((collection / "calls" / (key + ".json")).read_bytes()) for key, _ in tail}})
    return path


def run_collection(root, models=None, transport=None):
    """Collect definitely unstarted requests only; injectable transport stays offline.

    ``transport.preflight(model, cfg)`` returns runtime identity metadata;
    ``transport.generate(job, cfg)`` returns raw reply and normalized usage.
    """
    entered = time.monotonic()
    from sos_freeze import verify_freeze
    root = Path(root).resolve()
    freeze = verify_freeze(root)
    frozen_hash = _push_gate(root, freeze)
    config = read_json(root / "config/collector.json")
    jobs = read_json(project_path(root, config.get("requests_file", "config/requests.json")))
    if isinstance(jobs, dict):
        jobs = jobs.get("requests", jobs.get("jobs"))
    if not isinstance(jobs, list) or len({job["id"] for job in jobs}) != len(jobs):
        raise CollectionStop("request list invalid or duplicate IDs")
    # Validate the entire schedule before opening any transport.
    for job in jobs:
        check_job(job, model_config(config, job["model"]))
        if job["model"] == "claude":
            check_reservation(job, config.get("cost", {}))
    chosen = set(MODEL_ORDER if models is None else models)
    if not chosen.issubset(MODEL_ORDER):
        raise CollectionStop("unknown requested model")
    collection = root / "collection"
    collection.mkdir(exist_ok=True)
    lock = collection / "collector.lock"
    try:
        save_new(lock, {"pid": os.getpid(), "time": utcnow(), "freeze_sha256": frozen_hash})
    except FileExistsError as exc:
        raise CollectionStop("collector lock exists; inspect owner before explicit recovery") from exc
    try:
        return _collect(root, collection, jobs, config, chosen, transport, frozen_hash, entered)
    finally:
        lock.unlink()
        fsync_dir(collection)


def _collect(root, collection, jobs, config, chosen, transport, frozen_hash, entered=None):
    cost = config.get("cost", {})
    ledger = CostLedger(collection / "cost.jsonl", cost.get("cap_usd", "39"))
    starts = {path.stem: read_json(path) for path in (collection / "starts").glob("*.json")}
    receipts = {path.stem: read_json(path) for path in (collection / "calls").glob("*.json")}
    if any(record.get("integrity_failure") for record in receipts.values()):
        raise CollectionStop("saved integrity failure requires offline diagnosis before any further dispatch")
    schedule = {job["id"]: job for job in jobs}
    for key, record in starts.items():
        if key not in schedule or record.get("request_sha256") != schedule[key]["request_sha256"] or record.get("freeze_sha256") != frozen_hash:
            raise CollectionStop("saved start does not match frozen schedule")
    activity = ActiveBudget(collection / "activity", started=entered)
    failures = _effective_failures(collection, receipts)
    if failures >= 3:
        raise CollectionStop("three consecutive transport failures require offline diagnosis")
    if ledger.total > ledger.cap:
        raise CollectionStop("accounted project spend exceeds operational cap")
    reuse_file = root / "config/reuse.json"
    reuse = read_json(reuse_file).get("jobs", {}) if reuse_file.exists() else {}
    if activity.charged >= activity.cap:
        raise CollectionStop("12-hour cumulative active local-collection cap")
    transport = transport if transport is not None else DefaultTransport(root)
    summary = {"completed": 0, "reused": 0, "uncertain": 0, "already_saved": 0}
    for model in MODEL_ORDER:
        if model not in chosen:
            continue
        model_jobs = [job for job in jobs if job["model"] == model]
        # Requests were shuffled once, before freeze, by the sampling builder.
        predecessors = set(MODEL_ORDER[:MODEL_ORDER.index(model)])
        if model_jobs and any(job["model"] in predecessors and job["id"] not in receipts and job["id"] not in starts
                              for job in jobs):
            raise CollectionStop("earlier local model jobs remain unstarted; model order cannot be bypassed")
        ready = False
        cfg = model_config(config, model)
        for job in model_jobs:
            key = job["id"]
            if key in receipts:
                if receipts[key].get("request_sha256") != job["request_sha256"]:
                    raise CollectionStop("saved receipt request changed")
                summary["already_saved"] += 1
                continue
            if key in starts or key in ledger.reserved:
                summary["uncertain"] += 1
                continue
            reserve_seconds = 1 if key in reuse else (220 if not ready else 180)
            segment = activity.segment(reserve_seconds, key) if model in PINS else contextlib.nullcontext()
            with segment:
                if key in reuse:
                    saved = reuse[key]
                    raw = project_path(root, saved["receipt"]).read_bytes()
                    if sha(raw) != saved["sha256"]:
                        raise CollectionStop("reuse receipt hash mismatch")
                    original = json.loads(raw)
                    # The freeze-time matcher certifies original system/runtime/provenance.
                    if job.get("instruction") != "plain" or job.get("view") != "F" or model not in PINS:
                        raise CollectionStop("illegal sibling reuse mapping")
                    if saved.get("request_sha256") != job["request_sha256"] or saved.get("prompt_sha256") != job["prompt_sha256"]:
                        raise CollectionStop("reuse request mismatch")
                    record = dict(original, id=key, model=model, status="reused", reuse=saved,
                                  request_sha256=job["request_sha256"], prompt_sha256=job["prompt_sha256"], job=job)
                    save_new(collection / "calls" / (key + ".json"), record)
                    receipts[key] = record
                    summary["reused"] += 1
                    continue
                if not ready:
                    metadata = transport.preflight(model, cfg)
                    _check_runtime(root, collection, model, metadata, config)
                    ready = True
                estimate = check_reservation(job, cost) if model == "claude" else None
                if estimate:
                    ledger.reserve(key, estimate)
                started = utcnow()
                record = dict(job, started=started, freeze_sha256=frozen_hash,
                              tag=cfg["tag"], digest=cfg.get("digest"), reservation=estimate)
                save_new(collection / "starts" / (key + ".json"), record)
                starts[key] = record
                begin = time.monotonic()
                fatal = None
                try:
                    result = transport.generate(job, cfg)
                    if not isinstance(result, dict):
                        raise TransportError("invalid transport return", repr(result))
                    record.update(result, status="response")
                    if result.get("returned_model") != cfg["tag"]:
                        fatal = "returned model identity mismatch"
                    if model == "claude" and result.get("returned_effort") not in (None, cfg["effort"]):
                        fatal = "returned effort mismatch"
                    failures = 0
                except Exception as exc:
                    record.update(status="transport_failure", error=type(exc).__name__ + ": " + str(exc),
                                  raw_reply=getattr(exc, "raw_reply", None), stderr=getattr(exc, "stderr", None),
                                  input_tokens=None, output_tokens=None)
                    failures += 1
                record.update(finished=utcnow(), seconds=time.monotonic() - begin,
                              actual_usd=None, accounted_usd=estimate["usd"] if estimate else "0")
                if model == "claude" and record["status"] == "response":
                    tin, tout = record.get("input_tokens"), record.get("output_tokens")
                    if type(tin) is int and type(tout) is int and tin >= 0 and tout >= 0:
                        actual = (tin * D(str(cost.get("input_usd_per_million", 4))) + tout * D(str(cost.get("output_usd_per_million", 20)))) / D(1000000)
                        record.update(actual_usd=str(actual), accounted_usd=str(actual))
                        if tin > estimate["input_tokens"] or tout > estimate["output_tokens"]:
                            fatal = "measured-max reservation overrun; no more dispatch"
                    else:
                        record["accounting_status"] = "UNKNOWN; full reservation retained"
                if fatal:
                    record["integrity_failure"] = fatal
                # Receipt precedes settlement; a crash can over-account, never under-account.
                save_new(collection / "calls" / (key + ".json"), record)
                receipts[key] = record
                if record["actual_usd"] is not None:
                    ledger.settle(key, D(record["actual_usd"]))
                summary["completed"] += 1
                if fatal:
                    raise CollectionStop(fatal)
                if ledger.total > ledger.cap:
                    raise CollectionStop("actual cost exceeds operational cap")
                if failures >= 3:
                    raise CollectionStop("three consecutive transport failures; no retries")
            if activity.charged >= activity.cap:
                raise CollectionStop("12-hour cumulative active local-collection cap")
    summary.update(accounted_usd=str(ledger.total), local_active_seconds=activity.charged)
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--model", action="append", choices=MODEL_ORDER)
    args = parser.parse_args()
    try:
        print(json.dumps(run_collection(args.root, args.model), indent=2))
    except (CollectionStop, OSError, ValueError) as error:
        parser.exit(1, "STOP: " + str(error) + "\n")
