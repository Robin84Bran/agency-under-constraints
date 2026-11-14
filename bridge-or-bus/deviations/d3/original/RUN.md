# Bridge or Bus? runbook

This handoff is offline only. No model, push, collection, provider probe, model pull, server start/restart or publication was performed. The folder claim is supplied by Robin. Shared claim/review/website paths are outside this writer's boundary.

Python 3.9+ and Node.js (for toy/cross-language fixtures) suffice; no packages or credentials are needed for offline work. Commands run from this project root. Existing evidence, starts, calls, ledgers, freezes and attestations are never overwritten.

## Offline checks

```sh
python3 -B bob.py test
python3 -B bob.py verify
python3 -B bob.py dry-run
python3 -B bob.py rebuild
node --test evidence/toy/tests.mjs
```

`dry-run` uses fake transports through the same harness, covering 32 episodes and 160 fixture generations. It contacts no provider and does not instantiate a live adapter. `rebuild` recomputes the full 10,000-replicate frozen analysis fixture and compares exact canonical output. Its code-policy outcomes are test evidence only. Results, SURVEY and the local page template state the information-access claim boundary.

`prepare` and `freeze` were builder commands. `prepare` now refuses because a freeze exists. `freeze` creates exclusively and requires tests bound to the exact source inventory. Do not rerun either to replace frozen evidence. Changes require preserved originals, reviewed amendment and a new freeze/push.

## Readiness and budget

The plan is 1,200 local + 80 Claude episodes, at most 8,400 + 560 generations, serially Qwen 7B → Llama 8B → Qwen 1.5B → Claude. Within-model order is frozen in config/order.json. Action limits are six decisions plus one final report; no pilot, model substitution, retries, salvage or replacement queries.

Claude call reservations are **USD15.493120**; protected reserve **USD2**; total **USD17.493120**, within the USD25 frontier envelope and below the USD39 project stop / strictly-under-USD40 ceiling. config/frontier-reservations.json contains all 80 seven-call subhold schedules; config/sizing.json and fixtures/maximal-prompts.json reproduce prompt/history/schema/system/envelope measurements. H=826 and O=512 are planning assumptions, not verified hard bounds. Historical USD4/20 prices are API-equivalent, not verified current cash rates.

**Claude dispatch remains blocked.** --help and offline strings establish candidate controls and structured_output, not the complete tool-disabled print path, one-generation/retry semantics, enforced total charged-output bound or current rates. evidence/claude-transport.json records these UNKNOWNs. Both flags `--json-schema` and `--output-format json` are mandatory. The adapter accepts only one object structured_output, never result text, coercion or a repaired substring. Environment controls for output/retries and --max-turns 1 are candidates, not proof. A Claude-reviewed evidence amendment/new freeze must resolve the gates before frontier execution. Missing effort remains UNKNOWN; conflicting effort/model or internal turn counts stop.

Local readiness is checked with metadata only at 127.0.0.1:11435: frozen tag/digest, runtime, model template/system/context, then actual 8192-token loaded context after generation. No redirect, environment proxy, pull or server change is allowed. Obtain shared model capacity through the existing operator coordination before the future collection command; a loaded-model listing alone cannot prove an idle server. Do not contend with sibling jobs. The collector records runtime bytes/identity and refuses a changed runtime across resumes.

The collection lock rejects concurrent runners. Every episode reserves all seven possible paid calls before its durable episode start; every request/hash and call start is flushed before dispatch. Known actual usage settles the appropriate subhold; unused subholds release only after known terminal evidence. Unknown usage or ambiguous starts retain holds, stop dispatch and cannot be retried. An overrun is charged in full and causes a durable stop. Settlement never clips cost. Use the same collection/cost.jsonl across resumes and amendments; no version can reset project spend. Include any newly discovered historical charge before resuming, under a reviewed reconciliation. Protected reserve does not fund more episodes.

Active collection budgets persist across resumes: 12 hours local / 2 hours frontier. Per-generation wall timeouts are 180 / 420 seconds. Time ledgers reserve local 230 / frontier 460 seconds per segment to include metadata/process overhead; a crashed segment retains the full time hold. Three consecutive transport failures create a durable pause. A malformed model action is a scored technical failure, not an invitation to repair it.

## Future push and exact attestation

These are instructions for a later authorized operator. Do not execute from canonical RobinOS2. Use a **separate project-root research clone** containing the complete frozen project; Git mutations of the RobinOS2 tree are prohibited. `RESEARCH_REPO` is the real owner/repository chosen for this project, not an invented URL. The clone root must be this project, since the verifier checks every manifest file in the attested commit.

In that clone, after review/readiness and later push authorization:

```sh
export RESEARCH_REPO='OWNER/PRIVATE_BRIDGE_OR_BUS_REPO'
export RESEARCH_REMOTE="https://github.com/${RESEARCH_REPO}.git"
git switch -c codex/bridge-or-bus
python3 -B bob.py test
python3 -B bob.py verify
git add --all
git commit -m "Freeze bridge-or-bus offline implementation"
git push origin HEAD:refs/heads/codex/bridge-or-bus
mkdir -p collection/push-evidence
commit="$(git rev-parse HEAD)"
gh api --include "repos/${RESEARCH_REPO}/commits/${commit}" > "collection/push-evidence/commit-${commit}.http"
python3 -B bob.py record-push --remote "$RESEARCH_REMOTE" --evidence "collection/push-evidence/commit-${commit}.http"
```

The private remote must already be configured as origin and match RESEARCH_REMOTE. No repository creation or visibility change is implied. The Date header and commit body come from a real successful GitHub API response, never a local clock substituted as server evidence. `record-push` derives the pushed commit/server UTC time from those saved bytes, checks repository/commit identity, exact frozen Git content and chronology, and creates collection/push.json once. Server Date must follow freeze and precede every call start. The offline builder has created no push receipt. A later amendment needs its own reviewed attestation mechanism and new saved evidence; do not overwrite the original.

## Exact collection order

Only after valid freeze/push/runtime/capacity gates and future collection authorization:

```sh
python3 -B bob.py collect --models local
python3 -B bob.py collect --models claude
```

The local command runs all three local cohorts in order; it skips only known completed episodes after auditing their raw evidence and ledger. It never resends a started/uncertain episode. The Claude command also verifies all local episodes are complete; **under this freeze it fails closed at the unresolved frontier gate**. No configuration edit can bypass freeze verification.

After a complete or stopped batch, offline analysis is created exclusively:

```sh
python3 -B bob.py analyze
```

Analysis independently replays task transitions, binds events/reports to raw responses and exact adaptive prompts, reconciles settlements against raw usage, and retains unstarted/ambiguous truth as null/UNKNOWN. It reports all planned denominators, S*/A*/J, technical validity, intervals, predictions, unit compatibility/provenance, registry decision exhaustion and resources. Missing usage/time/cache/reasoning data is null. No study ACCEPTED status follows automatically from successful code execution or a positive primary effect.

## Stops and recovery

Stop on source/freeze/prompt mismatch, wrong identity/context, truncation, replay disagreement, missing push order, accounting UNKNOWN, retained hold, time/cost cap or saved transport pause. Diagnose from saved bytes. Never delete/rewrite evidence, reset a ledger, relax parsing, change settings, start another provider or rerun a started call. A process crash leaves an ambiguous start and conservative holds; only a reviewed saved-evidence reconciliation can establish a definitely unstarted continuation. Recovering budget is not a reason to change the sample.

Independent Claude review of this build and a fresh-clone offline verification remain distinct from the earlier protocol agreement. No model-generated review was requested during this build.
