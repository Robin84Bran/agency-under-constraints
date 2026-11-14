# The Useful Core · D1 runbook

Active amendment: **post-push D1**, delegated by Claude, the reviewer agent, before the first Claude call. `freeze-d1.json` binds both unchanged parents, `freeze.json` and `freeze-a1.json`, exact archived A1 files, and the pre-D1 collection inventory. The local cohort is complete: 900 retained terminals. There were no Claude starts, saved refusals, or STOP files at the D1 boundary, so no clearance or historical re-disposition is needed. D1 changes harness operations only; prompts, schedule, actors, scoring, budgets and statistical methods remain fixed.

The instructions in this D1 section supersede conflicting A1 instructions below. The original A1 push remains historical provenance, not a claim that D1 was pushed. No new push, activity API call or Git command is needed for the reviewer-delegated local deviation. The builder made no model calls, network requests, pushes or Git operations. D1 attestation and collection have not been run by the builder.

## Exact next commands

From the canonical project, once Claude's reviewer is ready to collect:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/useful-core
python3 -B uc_freeze.py verify
python3 -B uc_freeze.py attest-d1
python3 -B uc.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

`attest-d1` is offline and create-once. It verifies both parent bindings, the genuine saved A1 GitHub push, all frozen D1 inputs, every retained pre-D1 collection file, full current journals and their pinned prefixes, and completion of the local cohort. It writes `collection/d1-attestation.json`; it preserves `push.json` and `push-event.json`. It refuses a new Claude start before attestation. Subsequent starts must bind D1 and follow that local attestation. Old local starts remain bound to A1 and its push. Reinvoking attest after success fails create-once; invoke collect directly on subsequent resumes.

## Usage-limit pause and resume

Only a complete usage-limit refusal qualifies: return code 1, envelope `is_error: true`, integer `api_error_status: 429`, all four input/output/cache usage counters present as integer zero, numeric `total_cost_usd: 0`, usage-limit-only result text, and no contradictory output, detailed token/cost usage, tools or transport/harness errors. Missing or conflicting evidence keeps the previous fatal handling. Strict refusal parsing cannot hide malformed structured output. `fixtures/claude-usage-limit.json` is synthetic; `fixtures/claude-real-envelope.json` preserves the supplied real sibling envelope verbatim and is metadata-contract evidence only, not a Useful Core observation.

Paid dispatch evidence is create-once under `collection/episodes/<episode>/dispatches/<decision>-<attempt>/`: exact request JSON bytes, start, raw stdout/stderr bytes, their hashes, and either `accepted.json` or `usage-limit-pause.json`. A refusal is a **DEFINITE_NON_START**, has an explicit zero-cost `nonstart` ledger settlement, and does not create a canonical model call, episode terminal, first-model contract or fatal STOP. The existing whole-episode reservation still covers the identical future call; it is neither charged for the refusal nor duplicated. Actual wall time is charged. A crash before time settlement conservatively retains the original time reservation.

The collector returns JSON with `status: "usage-limit pause"` and exits successfully. The pause records the supplied reset, resolved UTC time where known, raw/request hashes, prior model-history hashes, and complete journal byte-length/SHA-256 prefixes. On the next collect invocation before that reset it exits paused without dispatch. After the reset, use the **same collect command above**, without re-attesting. It validates saved evidence and complete current journals, allows legitimate journal growth beyond pinned prefixes, reconstructs prior successful calls, and resends exactly the saved request at the refused call position. Earlier model calls are never resent. Repeated refusals create separate operational events and retain the same request. Unparseable reset text leaves the pause unresolved; no guessed reset or automatic dispatch is allowed.

All non-refusal errors, nonzero usage/cost, ambiguous starts and real model failures retain A1 handling. A process death can reconstruct a pause from complete exact refusal bytes; an incomplete dispatch or a crash after real generation cannot grant retry permission. Model output is published to the original canonical call files only after a non-refusal dispatch; saved accepted model calls are independently replayed and accounted by the existing analysis. Refusals do not contribute to model-call counts, first-call compatibility, technical failure streaks or model behavior. Analysis exposes them separately under `operational_events.usage_limit_refusals`; a paused unfinished row has reason `usage-limit pause` and retains the existing fixed-denominator/null treatment.

## Verify and recover

```sh
python3 -B -m unittest discover -s tests -v
python3 -B uc_freeze.py verify
python3 -B uc_analysis.py --data collection --output collection/analysis-d1-UNIQUE.json
```

Analysis of real collection requires the D1 attestation. Use a fresh analysis output path. `RESULTS.md` records operational dispositions and pending empirical gaps. `deviations/d1/README.md` records scope and retained evidence. Do not reseal D1 after exposure. Do not edit/delete old evidence, STOPs, journal tails or checkpoints; this package adds no general STOP override. No existing usage-limit STOP exists to clear. Any later legacy STOP requires a separately recorded, evidence-specific disposition with retained-prefix and current-ledger validation.

---

The following is the retained A1 runbook. Its original pre-push procedures and blanket no-resend language are superseded only by D1 above.

# The Useful Core · A1 runbook

Pre-registration revision **A1**, requested by Claude, the delegating reviewer. [DEVIATIONS.md](DEVIATIONS.md) supersedes the original blanket content-failure stops; `freeze.json` stays unchanged and `freeze-a1.json` is the active manifest. Reviewer-delegated build only. Robin has not reviewed this project. **No model calls, pushes or collection were performed by the builder.** Collection commands below are for a later reviewer delegation. `offline/` contains conspicuously labelled fake evidence. Current runtime, capacity, first-call Claude compatibility and cash billing are UNKNOWN.

Python 3.9+ and Node, standard library only. No package installation, daemon, import-time network or model initialization. Source reuse: Receipt Gap D1/D2 provenance, reservation, CLI isolation and cache-accounting patterns; Bridge or Bus D2 manifest/layer identity evidence. Reusable logic is local here, with no sibling runtime dependency. [REVISION.md](REVISION.md) records both agents’ AGREED decision and review notes.

Offline checks, from this directory:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B uc_freeze.py verify
node fixtures/toy-vectors.mjs > /private/tmp/useful-core-toy-recheck.json
cmp /private/tmp/useful-core-toy-recheck.json fixtures/toy-vectors.json
python3 -B uc_offline.py --output /private/tmp/useful-core-dry-run-UNIQUE
python3 -B uc_analysis.py --data offline/dry-run --offline-fake --output /private/tmp/useful-core-analysis-UNIQUE.json
cmp /private/tmp/useful-core-analysis-UNIQUE.json offline/analysis-final.json
```

Use new output names; all evidence writes create once. Never rerun prepare/freeze or modify registered files after inference exposure. `freeze-a1.json` binds the unchanged original freeze, archived originals, the A1 audit/tests/report and code, protocol, prompts, schemas, explicit 960-episode schedule, model manifests/layers, toy/vector fixtures, baselines, statistical fixtures and offline evidence. It excludes `collection/` and cache files. Its own SHA-256 identifies the package. New source files also invalidate inventory verification. Put later verification outputs outside this frozen directory or under `collection/`.

## Push provenance and attest (later reviewer action)

Use a **separate clone of `Robin84Bran/research`**. Copy this complete package into `useful-core/` there, excluding `.git`, `__pycache__` and `collection/`. Include every manifest input, `freeze.json` **and** `freeze-a1.json`. Test and verify the copy, commit and push there only. No branch/index/commit changes in RobinOS2. Never substitute commit author dates, HTTP Date or invented records for a GitHub activity timestamp.

After that push, capture a genuine record from the **activity API**, keeping the complete response as well as the selected complete record. Replace the explicit placeholders once; `UC_COMMIT` must be the full commit and `refs/heads/main` the actual pushed ref. These commands have not been executed:

```sh
UC_PROJECT='<WORKSPACE>/06_intelligence/AI_research/research/useful-core'
UC_CLONE='<separate-research-clone-root>'
UC_COMMIT='<40-character-pushed-commit>'
UC_ACTIVITY='/private/tmp/useful-core-activity-UNIQUE.jsonl'
UC_EVENT='/private/tmp/useful-core-push-UNIQUE.json'
gh api --paginate repos/Robin84Bran/research/activity --jq '.[] | select(.activity_type == "push") | @json' > "$UC_ACTIVITY"
python3 -B -c 'import json,sys; from pathlib import Path; es=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines()]; matches=[e for e in es if e.get("after")==sys.argv[3] and e.get("ref")==sys.argv[4]]; assert len(matches)==1, "one matching full activity record required"; f=Path(sys.argv[2]).open("x"); f.write(json.dumps(matches[0])+"\n"); f.close()' "$UC_ACTIVITY" "$UC_EVENT" "$UC_COMMIT" refs/heads/main
python3 -B "$UC_PROJECT/uc_freeze.py" attest --root "$UC_PROJECT" --clone-root "$UC_CLONE" --repo-path useful-core --event "$UC_EVENT" --commit "$UC_COMMIT"
```

Attest reads HEAD/origin/all committed manifest blobs and `git ls-remote` in `--clone-root`; no clone writes. It requires the branch, after commit, server id and timezone-aware server timestamp from the activity record. The push must follow the active A1 freeze, and the commit must contain both exact freeze blobs. It saves **create-once `collection/push.json` and the exact supplied source bytes as `collection/push-event.json` here**, binding the record hash, canonical repository, commit, manifest and freeze. Missing evidence means HOLD. No `/events` fallback. Before every start, the collector checks freeze and push-before-every-start ordering.

## Collect (later delegation; local first, then Claude)

Run from the canonical project where attestation was written:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/useful-core
python3 -B uc.py collect --cohort local
python3 -B uc.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Local serial order: Qwen 7B → Llama 8B → Qwen 1.5B; then the fixed 60 frontier episodes. Each episode finishes before another starts. Existing Ollama `http://127.0.0.1:11435` only. Coordinate shared capacity before collection; never pull/start/restart/reconfigure a server. Preflight reads tags/show/version, verifies exact manifest → template/system, checks model context and conservative complete-history byte allowance. Qwen’s real default system is retained; the explicit study system overrides it in the generation request. `/api/ps` verifies actual running model/digest/context after each local generation. Preflight metadata is retained and compared on resume. Full prompt/system/schema/request bytes and hashes are saved. Exact input tokenization remains UNKNOWN; any detected input loss stops collection.

Local requests use `stream:false`, JSON mode, temperature .6, top_k 16, 192 output, 8192 context and `seed=100*s+decision` (report decision 7). `done` must be true and `eval_count` present. Missing completion/count is a transport failure for that episode, after any known identity/context/input-loss gates. `done_reason=length` or output count exactly 192 is a reply failure even with parseable JSON. Overruns, identity or input loss stop collection. No report after failed action transport; failed report preserves committed work.

Claude binary is offline hash/version pinned to inspected 2.1.312. Only `--version` and `--help` were executed in this build; the print path was not exercised. CLI argv uses `--json-schema` **and** `--output-format json`, safe/restricted mode, empty real tools/MCP, hooks disabled, no Chrome/slash commands/persistent session/instruction settings, medium effort, no fallback/retries and empirical 512 output planning allowance. Existing subscription sign-in must already exist. No credential copying. `--max-turns 1` limits the main loop; the CLI’s internal schema tool can produce **num_turns 2 / stop_reason tool_use**. Accept integer turns 1 or 2 only with strict-valid object `structured_output`; never recover `result` prose. The first frozen scheduled call verifies this contract and writes `collection/claude-contract.json`; a model-content or output-length failure retains its scored/charged outcome with `MODEL_FAILURE` and continues to the next scheduled episode. It does not verify strict compatibility. Envelope/integrity/accounting failures retain their holds and stop frontier. Every later envelope is checked identically. Missing returned effort is UNKNOWN, conflicting effort/identity is fatal.

**Frontier whole-episode reservation total: USD10.083840; plus USD2 protected reserve = USD12.083840 ≤USD25.** Holds use integer microdollars, historical USD4 input / USD20 output per million, empirical hidden-input allowance 826, 10%/64 padding. These are planning estimates, not provider output or bill guarantees. The first generation is a scored observation, never a pilot. Count input/cache creation/cache read once each; output already includes reasoning. Settle at the greater of token accounting and valid aggregate `total_cost_usd`, rounded upward. Missing usage/cost retains the hold and stops paid dispatch; measured overruns settle in full and stop admission. Rolling gate: settled actual + open/uncertain holds + new episode hold + USD2 ≤USD25 and <USD39. USD40 is the programme ceiling. Local model-call cost is USD0; other resource costs are not zero.

Locked append-only ledgers hash every preceding byte prefix and retain create-once checkpoints, including the final append. Resume rejects changed/truncated prefixes, partial tails, duplicate starts or uncertain episodes. Complete terminal episodes are skipped, never replaced. An interrupted call/episode is never resent. Release only proven-unused holds after known terminal disposition without global failure. Only three consecutive **transport-failed episodes** pause that cohort. Content/schema/JSON/output-length failures break the transport streak and continue; successful episodes also break it. The streak spans local actors and is reconstructed from immutable terminals across resumes, including a crash before STOP creation. Pause evidence binds the three terminal hashes and byte-length/SHA-256 journal prefixes. Durable STOP records have no override or clearance flag; diagnose saved evidence and obtain a reviewed prospective amendment. Any later clearance must validate prefixes (allowing legitimate appends), complete current journals and unchanged terminal evidence, never whole mutable-ledger equality.

Cumulative active limits across resumes: local 12 hours, frontier 2 hours. Reserve the full 180s/420s call timeout plus 10s metadata/persistence allowance before start; metadata preflight reserves 40s. Unknown interrupted timer segments retain their entire reservation. Between-call overhead is charged. Disk/OS stalls and hidden provider activity are not claimed to have hard elapsed/spend bounds. Exhaustion leaves planned collection incomplete with fixed denominators and null facts.

## Offline rebuild after collection

Copy the frozen package and saved `collection/` to a fresh clone; no original absolute path, service, model or credentials are needed for analysis. Run:

```sh
python3 -B uc_freeze.py verify
python3 -B -m unittest discover -s tests -v
python3 -B uc_analysis.py --data collection --output collection/analysis-r1.json
```

Independent replay checks actions, prerequisites, artifacts, outage timing, receipts and delivery, then verifies realized prompts, raw replies, strict payloads, technical failure classes, ledger reservations/actuals/releases and retained prefixes. Analysis never initializes/imports providers or invokes Git/network. All 960 scheduled rows remain in tables, including unstarted/ambiguous cases with null factual utility and operational zero. Report Y/H, raw utility, oracle attainment, A/F with denominators and unknown-truth claims, waits/null/missing replies, recovery/retries, useful artifacts not delivered, delivery decision, calls/cache/output/reasoning/time/cost. It rebuilds fixed seed-block contrasts and 10,000-replicate bootstrap intervals, all seven predictions and calm fallback-only rates. Scripted full-only/highest-feasible/core-only fixtures and omniscient ceilings are diagnostic evidence, never model results. Publish limitations and incomplete coverage; offline success is not empirical acceptance.
