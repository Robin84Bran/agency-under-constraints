# Signal or Silence runbook

Offline build approved by Claude and Codex on 11 November 2026. This handoff stops before inference. Python 3.9+ and the standard library suffice for rebuild and tests. No package installation is needed.

Claude must first start the project-owned Ollama server at `127.0.0.1:11435`, using the existing model store and pins. Do not pull models, change settings, restart a shared server or use the default 11434 server. From the canonical workspace, the server command is:

```sh
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=<WORKSPACE>/ANTresidency/Honest_Agent/models/ollama /opt/homebrew/bin/ollama serve
```

Use the installed Ollama 0.33.3 executable if its installation path differs. The runner rejects version, tag, digest, template, system, parameters or model-info mismatch against the saved metadata. Server availability is UNKNOWN at freeze; this build made no probes.

Claude must also push this entire frozen project from a separate research clone before any inference, including any optional preflight. Preserve GitHub's server timestamp and commit receipt. Write a new, never replaced `collection/push.json` with this schema, filling actual values:

```json
{
  "freeze_sha256": "SHA256 of the exact freeze.json bytes",
  "github_time": "2026-11-11T00:00:00+00:00",
  "server_timestamp_source": "GitHub server receipt URL or preserved response",
  "remote": "private research repository URL",
  "commit": "pushed commit SHA"
}
```

To create that record exclusively from actual evidence, use:

```sh
python3 -B sos.py record-push --github-time '<GitHub UTC ISO timestamp>' --commit '<40-character pushed commit SHA>' --remote '<private research repository URL>' --source '<GitHub server evidence URL or saved receipt path>'
```

The example timestamp is a schema example, not a push attestation. Collection checks freeze integrity, the attested hash and timestamp before opening a transport. GitHub time must precede every saved start. No push or collection was performed during the build.

From this directory, start the complete serial collection with:

```sh
python3 -B sos.py collect
```

The order is Qwen 7B, Llama 8B, then Claude Opus 5.5 at medium effort. The schedule contains 5,604 jobs: 1,868 per judge across both instructions, with shared identical F requests deduplicated within each instruction. Primary scientific denominators remain 240 episodes per view per instruction. Receipt replication has 120 pairs (40 HA and 80 Rebel). The cutoff snapshot contains 5,760 sibling originals and 48 replays; zero plain-F requests match byte for byte. No sibling reply substitutes for a new request.

To run local collection separately, then resume all remaining jobs:

```sh
python3 -B sos.py collect --models qwen7b llama8b
python3 -B sos.py collect
```

The runtime reads only the `HONEST_AGENT_CLAUDE_BIN` setting from `<WORKSPACE>/ANTresidency/Honest_Agent/v0.3.1/local.env`. Never copy that file or credentials into a clone. Use the existing Claude subscription login. The transport follows the preserved Honest Agent v0.3.1 ClaudeCLI command, tool restrictions, system prompt, cache-token accounting and 420-second timeout. Claude has no seed switch or enforceable output cap; seeds and requested effort are saved, actual effort is UNKNOWN if the CLI does not echo it. An explicit mismatched effort or model stops dispatch.

Expected collection outputs: `collection/starts/<job>.json`, `collection/calls/<job>.json`, `collection/runtime-<model>.json` and append-only `collection/cost.jsonl`. Every start is durable before dispatch. Calls save exact prompt/request hashes, seed, tag/digest, timestamps, raw transport reply, text, usage, timing, failure and accounting. Neither starts nor receipts are overwritten. A start or reservation without a receipt remains uncertain and is never resent. Ordinary missing/invalid outcomes remain in every planned denominator.

The frontier ledger reserves at least the measured 1,282 input/393 output maxima, enlarged by the frozen UTF-8 prompt estimate, before each call. Saved source rates are USD 4/20 per million tokens, API-equivalent subscription accounting. Planned reservations total USD 24.261584, plus USD 5 planning reserve. This is an estimate, not a hard output/billing bound. Unknown usage keeps its entire reservation; actual spend is reported. No new reservation may pass USD 39; an observed maximum overrun stops further calls. Only one collector and one frontier call may be active. Local timeout is 180 seconds; cumulative active collection is capped at 12 hours. Three consecutive transport failures stop the batch without retries.

After collection, run the frozen analysis once:

```sh
python3 -B sos.py analyze
```

Expected outputs: `analysis/results.json`, `RESULTS.md` and `README.md`. Analysis uses 10,000 paired bootstrap replicates (seed 20261112), fixed denominators, both duplicate weightings, separate instruction pass decisions, receipt replication, predictions and archived census. It performs no inference and reads no credentials. Existing result outputs are never overwritten. For a later independent rebuild, use a new output directory:

```sh
python3 -B sos.py analyze --output analysis-rebuild-1
```

Offline fresh-clone verification and reconstruction:

```sh
python3 -B sos.py verify
python3 -B sos.py test
python3 -B sos.py import
python3 -B sos.py sample
python3 -B sos.py verify
```

Import checks portable evidence checksums and source freezes, replays ordered receipt truth and reconciles all historical judgments/ledgers. Sampling rebuilds certificates and selected IDs, verifies byte equality with saved artifacts and does not resnapshot sibling data. `evidence/work-or-proof/snapshot.json` and `config/reuse.json` permanently fix the cutoff. Offline build checks and a portable reconstruction certificate are saved under `build/`. The lossless `evidence/work-or-proof/receipts.tar.xz` preserves all sibling receipt bytes with their original SHA-256 values in `snapshot.json`; the renderer reads it with the standard library. Prospective results are absent at handoff.

For interruptions, rerun the same collection command under the unchanged freeze. Saved receipts are skipped; uncertain starts/reservations are charged conservatively and never resent. A stale `collection/collector.lock` requires offline inspection of its PID and evidence that the prior process has ended before removing that task-owned lock. Do not remove starts, ledgers or receipts. After diagnosing and addressing a three-failure stop offline, record the reason with `python3 -B sos.py recover --reason '<concrete diagnosis and remedy>'`, then resume the unchanged collection command. Recovery acknowledges the exact failed receipt hashes; it never retries them or replaces their outcomes. Any truth/hash, runtime identity, price/reservation or certificate mismatch stops collection. Preserve the failed evidence; do not repair prompts, replace responses, lower N or overwrite the freeze.

Final acceptance remains UNKNOWN until collection is complete, the frozen analysis rebuilds independently, and Claude reviews every claim. A negative scientific result can be accepted; an incomplete collection cannot.
