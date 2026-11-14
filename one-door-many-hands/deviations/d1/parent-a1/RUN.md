# One Door, Many Hands · A1 runbook

This package is an offline build delegated by Claude, the reviewer. Robin has not reviewed this project. No model calls, real collection, push, or network attestation were performed. The eventual page is standalone and must explain that a pass means models use worked examples better than complete written rules in this task. The fixed sample is 3,600 local decisions followed by 120 Claude decisions; there is no pilot or retry.

`freeze-a1.json` is the active pre-registration revision and binds the unchanged original `freeze.json`. See [DEVIATIONS.md](DEVIATIONS.md) for the exhaustive routing audit and exact original-file archives. Neither freeze may be regenerated.

Use Python 3.9+ and Node for the original-toy parity check. Standard library only; no packages, provider initialization at import, daemons or service changes. Work in this project directory. Preserve every source and saved response after freeze; never rerun `od_prepare.py` or regenerate `freeze.json`. Preparation and freeze are create-once. Any future amendment needs a separately reviewed immutable freeze/push lineage and retained spend/uncertain holds.

Offline verification:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B od_freeze.py verify
python3 -B od_offline.py --output offline/recheck-UNIQUE
python3 -B -c 'from od_archive import verify_archive; print(verify_archive("offline/dry-run-a1.tar.gz"))'
```

Choose a new recheck directory each time. Existing `offline/build-*` directories are retained development evidence, excluded from the portable package in favor of their frozen archives. `offline/dry-run-r1.tar.gz` contains 48 successful fake decisions (one complete block per identity), plus ten failure scenarios, raw envelopes, starts, exact requests, timer/spend ledgers and replay outputs. `offline/failed-first-dry-run.tar.gz` retains the initial incomplete-fixture failure. `offline/dry-run-a1.tar.gz` adds the revised 48-success/ten-failure fake run: content failures continue from the first Claude episode; incomplete local transports pause at episode three. All archives contain only synthetic responses. `config/oracle.json` contains every exact rational oracle cell/tie count; `config/baselines.json` contains constant, expected-work, outage, oracle and all-null code baselines.

For a portable saved-evidence replay, use a new destination:

```sh
python3 -B od_rebuild.py --output offline/rebuild-UNIQUE
```

This safely unpacks the verified archive, replays raw evidence, compares the saved full analysis including bootstrap/pass decisions and confirms failed fixtures. Analysis imports no live transport and needs neither credentials nor the original absolute project location.

## Push and GitHub activity attestation — later reviewer operation

Use a separate `Robin84Bran/research` clone. Copy this portable package into its `one-door-many-hands/` directory, including every path in `freeze-a1.json`, `freeze-a1.json` itself and the byte-identical original `freeze.json`. This includes `deviations/a1/original/`. Exclude `.git`, `__pycache__`, `collection/`, temporary rechecks and the unpacked `offline/build-*` directories; retain the frozen offline archives, manifests and summaries. Run tests and `od_freeze.py verify` in the copied directory before committing. Do not commit, switch branches or push from the RobinOS2 Git tree. No push is performed by this build.

After the reviewer pushes the package, set `OD_CLONE` to that separate clone. Its HEAD must be the just-pushed commit. `OD_REF` must be the actual branch. The two activity paths below must not already exist. These commands collect the full API activity records and select the full matching push record without inventing a time:

```sh
OD_PROJECT='<WORKSPACE>/06_intelligence/AI_research/research/one-door-many-hands'
OD_CLONE='<absolute-research-clone-root>'
OD_REF='refs/heads/main'
OD_COMMIT="$(git -C "$OD_CLONE" rev-parse HEAD)"
OD_ACTIVITY="$OD_PROJECT/collection/activity-response-UNIQUE.jsonl"
OD_EVENT="$OD_PROJECT/collection/activity-selected-UNIQUE.json"
mkdir -p "$OD_PROJECT/collection"
(set -C; gh api --paginate repos/Robin84Bran/research/activity --jq '.[] | @json' > "$OD_ACTIVITY")
python3 -B -c 'import json,sys; from pathlib import Path; es=[json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()]; e=next(e for e in es if e.get("activity_type")=="push" and e.get("after")==sys.argv[3] and e.get("ref")==sys.argv[4]); f=Path(sys.argv[2]).open("x"); f.write(json.dumps(e)+"\n"); f.close()' "$OD_ACTIVITY" "$OD_EVENT" "$OD_COMMIT" "$OD_REF"
python3 -B "$OD_PROJECT/od_freeze.py" attest --root "$OD_PROJECT" --clone-root "$OD_CLONE" --repo-path one-door-many-hands --event "$OD_EVENT" --commit "$OD_COMMIT"
```

Attestation reads Git only in `--clone-root`: exact HEAD, canonical origin, every committed frozen blob, and `git ls-remote` for the exact branch/commit. Activity must be `push`, contain matching `after`, ref, id and a past timezone-aware server timestamp after A1 freeze. Both committed freeze blobs and every active manifest input must match. Commit dates are insufficient. It writes create-once **`collection/push.json` and `collection/push-event.json` here under `--root`**, with exact selected record bytes and their hash. It never writes into the clone. A missing matching API record means HOLD collection. Attestation does not send messages or push anything.

## Collect — local first, then Claude

From the attested RobinOS2 project directory, the exact commands are:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/one-door-many-hands
python3 -B od.py collect --cohort local
python3 -B od.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Qwen 7B, Llama 8B and Qwen 1.5B run serially on the existing endpoint `http://127.0.0.1:11435/api/generate`. Requests use `stream:false`, JSON, temperature .6, top_k 16, num_predict 192, num_ctx 8192, seed=block. Metadata preflight checks the pinned digest and exact manifest-backed template/default system; Qwen's Alibaba default is valid metadata and is not prepended to the explicit study system. Raw replies require `done:true`, integer `eval_count`, usage and actual running identity/context. Missing/incomplete local transport fails the episode and continues without retry until three consecutive episode transport failures create durable `STOP.json`; the fourth episode is not dispatched. The streak survives restarts and model boundaries; success or a content failure resets it. Length stops and exhausted output fail their replies. Identity, context, input-loss evidence or an unknown stop reason stops the cohort. Input completeness remains UNKNOWN without an independent expected count; byte sizing is not a tokenizer proof. No model pulls, startup/restart, store edits or tuning. Coordinate shared hardware outside the collector; it does not issue inference probes.

The Claude gate requires all 3,600 local terminal records. The installed binary's SHA-256 is bound to source-inspected version 2.1.312; hash drift stops before inference. Existing subscription sign-in is required; credentials are never copied. Requests fix `claude-opus-5-5`, medium effort, `--json-schema`, `--output-format json`, safe/restricted mode, no external tools/MCP/browser/skills/hooks, no session persistence, one main-loop turn and zero configured transport/schema retries. The CLI's schema tool may yield `num_turns:2, stop_reason:tool_use`; one or two turns are accepted only when `structured_output` is independently strict-valid. The first frozen scored call checks the same contract as every later call. Any model-content failure, including missing/nonobject structured output, illegal field/value, malformed designated payload or length stop, ends only that episode with the frozen technical score and permits the next scheduled episode. A completed provider schema rejection with verified metadata/accounting is also episode-local; it enables no retry. Harness, outer-envelope integrity, identity, usage/cost uncertainty and overruns stop dispatch immediately, including on the first call. Known usage settles before payload rejection; strict decoding preserves metadata when only the designated payload has duplicate/nonfinite values. No result-field parsing, compatibility probe, model substitution or fallback is permitted. Missing returned effort is UNKNOWN; conflicting effort is fatal. Raw stdout/stderr bytes are retained in base64.

Total frontier reservations: **USD2.580480**; protected reserve **USD1**; full envelope **USD3.580480**, below USD25. Every request has a unique whole-episode hold, fsynced start and exact request before dispatch. The rolling gate includes settled cost plus all open/uncertain holds plus the next hold plus USD1; it must fit USD25 and remain below USD39 (programme ceiling USD40). Stop at the first unfundable job. Sum uncached, cache-read and cache-creation input; charge the greater of USD4/20 planning accounting and the full reported API-equivalent cost. Cash billing remains UNKNOWN. Unknown usage/cost keeps the entire hold and stops. Overruns settle in full and stop; no clipping or imagined hard aggregate-token guarantee. Local model-call USD is zero; hardware/opportunity costs are UNKNOWN.

Persistent active-time budgets are eight hours local and two hours Claude. Admission reserves 190/310 seconds per local/frontier attempt and 40 seconds per metadata preflight; actual request timeouts are 180/300 seconds. Settled monotonic elapsed includes between-call work; interrupted segments keep their whole reservation. Locks reject concurrent collection. Spend and time logs are hash-chained, with a separately retained hash/length checkpoint for **every byte prefix**. Missing, rewritten or truncated prefixes fail closed. No ledger reset or timer reset on restart.

## Recovery and analysis

Never remove or edit `STOP.json`, prefixes, starts, holds or terminal records. Definitely unstarted jobs alone may resume under the same verified freeze; any interrupted start or reservation is not resent. Raw output is written before parsing. A crash between log fsync and its prefix checkpoint is intentionally a fail-closed integrity stop. Retain failed evidence and diagnose before a separately reviewed amendment; there is no override flag. All model-content failures fail only their episode, including first-call failures. Input/identity/outer-envelope/accounting failures and resource caps stop dispatch. A local three-transport pause is reconstructed from durable A1 terminals at admission, so a crash before STOP creation cannot reset it. There is no clearance API; a future separately reviewed clearance must bind byte-length/hash prefixes of append-only ledgers and validate their full appended tails. Never hash a growing ledger as an immutable whole-file clearance, reset a hold, rewrite a terminal, or resend a start. Scientific performance never changes scheduling.

After collection, copy the unchanged package and saved `collection/` to a fresh independent checkout and run:

```sh
python3 -B od_freeze.py verify
python3 -B -m unittest discover -s tests -v
python3 -B od_analysis.py --data collection --output collection/analysis-a1.json
```

Analysis reconstructs exact requests, choices, failures, operational penalties, factual nulls, costs, timer logs, schedule prefixes and attestation chronology from raw evidence. It checks terminal/ledger agreement, preserves assigned denominators, performs the frozen 10,000 paired block bootstrap with multiplicity, reports joint/technical gates, all predictions, common ties, failure reasons and resource categories. Complete-valid-pair sensitivity supplements the primary. Its output is create-once. Incomplete samples have UNKNOWN joint pass availability; this is not a positive or negative result. A negative complete study can meet delivery acceptance; independent reviewer acceptance and later publication remain separate.
