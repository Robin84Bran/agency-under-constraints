# Three Rules, One Lunch runbook

The offline build is complete. No model has been called; no push or collection was performed. Robin authorized work in this folder only. Claude's AGREED review and both adopted notes are recorded in PROTOCOL.md. The original draft is preserved under evidence/; SURVEY.md and QUESTIONS.md describe the earlier drafting stage.

**Live collection is on HOLD.** Installed CLI 2.1.312 has the requested schema flags and candidate output/retry controls, but offline inspection did not establish complete startup/internal-request accounting, an enforced aggregate 1,024-output-token ceiling, a bound on schema/hidden scaffolding, or current accounting rates including cache-creation premiums. See evidence/cli-contract.json, with binary hash, source offsets and excerpts. This is missing evidence, not an observed provider failure. The protocol already requires a reviewed transport/budget revision in this situation. The adapter fails closed, and both cohort entry points reject dispatch before any inference. There is no bypass flag. Resolve this with Claude and a reviewed amendment/new freeze **before the first local call**; do not flip readiness after observing local results, shrink the frontier sample, change transport, or make a probe under this build's authority.

All commands below run from this project directory in an isolated checkout. Python 3.9+ standard library suffices; Node is needed only to regenerate the independent JavaScript oracle. No package install, service creation, model pull, restart, credential copying or scheduler is needed.

## Offline verification

```sh
python3 -B -m unittest discover -s tests -v
python3 -B trl_freeze.py verify
python3 -B trl_offline.py rebuild --out build/rebuild-check
```

The rebuild unpacks the frozen fake evidence into a temporary directory and recomputes all 960 planned episode rows, summaries, CSV/Markdown tables and twenty frontier seed rows. It compares them byte for byte with the archived analysis. The saved fake run contains **24 episodes / 224 invocations**, two seed blocks (0 and 19) in every cohort and regime; the remaining 936 episodes have UNKNOWN factual outcomes and zero operational scores. All predictions remain UNKNOWN. Fake ledger amounts are software accounting fixtures, never actual spend or model results. The frozen archive and its per-file hash manifest are evidence/offline-dryrun.tar.gz and evidence/offline-dryrun.tar.manifest.json.

To create another reversible fake run, use a **new** output directory:

```sh
python3 -B trl_offline.py dry-run --out build/another-offline-run
```

No live transport is constructed by that command. Existing evidence, trial files, ledgers, archives and freezes must never be overwritten. build/ contains retained development runs/logs and is excluded from the scientific manifest; the canonical fake evidence and verification reports are under evidence/ and are frozen.

## Push attestation (Claude, after the readiness amendment)

The builder does not push. Claude must work in a separate clone of `Robin84Bran/research`, on `claude/three-rules-one-lunch` or another authorized task branch. Never mutate the RobinOS2 working tree. Preserve the complete project manifest at repository path `three-rules-one-lunch/`; retain the prior freeze and evidence if producing an amendment. Push the exact reviewed inputs and new freeze before any inference. No credentials or build/ artifacts belong in the commit. Publication or merge to main remains outside this build.

After a real successful push of the intended commit, these are the exact attestation commands, from `three-rules-one-lunch/` in that clone:

```sh
mkdir -p build
python3 -B trl_freeze.py verify
gh api --paginate --slurp repos/Robin84Bran/research/events > build/github-events.json
python3 -B trl_freeze.py select-event --events build/github-events.json --commit "$(git rev-parse HEAD)" --out build/push-event.json
python3 -B trl_freeze.py attest --event build/push-event.json --commit "$(git rev-parse HEAD)" --repo-path three-rules-one-lunch
```

`select-event` requires a real GitHub PushEvent naming that exact repository and commit. If GitHub has not exposed it, retain the response and collect a new server response under a new filename later; never invent a time or substitute a Git author date. If the repository/API does not expose commit-bound PushEvents, attestation remains blocked pending a supported evidence-method revision. `attest` checks the current HEAD, origin allowlist, remote task ref, timestamp after freeze, the freeze blob and **every manifest file** in the pushed commit. It creates collection/push-event.raw.json and collection/push.json exclusively. Network access is read-only for those attestation checks; attestation does not push. The collector subsequently binds the preserved event, freeze and every call's start time. Re-recording after starts is forbidden.

## Collection commands (local first, then Claude)

Only after the documented readiness amendment and push attestation, the exact collection commands are:

```sh
python3 -B trl_collect.py --cohort local
python3 -B trl_collect.py --cohort claude
```

The current freeze intentionally rejects both commands at the pre-inference readiness gate. These are the fixed entry points, not clearance to execute this build. The first command runs Qwen 2.5 7B, Llama 3.1 8B, then Qwen 2.5 1.5B, each with 100 seeds and three regimes (900 episodes / 8,400 maximum calls). The second requires every local episode to be terminal, then runs the sixty Claude Opus 5.5 episodes / 560 maximum calls. The explicit shuffled order is config/episodes.json. No calibration, retry, repair, replacement or deduplication generation is scheduled.

Read-only Ollama preflight checks the pinned model digest, version, template and default parameters/system before generation; each saved response checks running identity and effective context 8192. The sole endpoint is `http://127.0.0.1:11435`; no model-store changes are permitted. Requested generation seeds and options are saved per call. CLI path is frozen in config/transport.json, points to the user-supplied executable, and is checked against evidence/cli-contract.json. The Claude command uses `--json-schema` **and** `--output-format json`, a replacement system prompt, disabled real tools/MCP/hooks/skills/instruction discovery, medium effort and candidate no-retry controls. Only the outer `structured_output` object can supply the action; `result` prose never supplies a fallback. Returned effort is UNKNOWN if absent. Live success and all-internal-generation accounting are unverified.

Every call has an immutable request, unique durable start, base64-preserved stdout/stderr bytes, full parsed envelope, payload/error, usage, elapsed time, and a prompt/request hash. All decisions in a round share a snapshot; no query executes until the full round's actions validate. Invalid central arrays execute no partial query. Null is valid and creates no receipt. Technical/missing opportunities keep factual rewards null with separate zero operational reward. Completed rounds, failed outputs and unstarted opportunities all remain accounted for.

## Money, time, stops and recovery

Current actual model spend is **USD0**. Conditional frontier reservations are **USD18.083840**, plus **USD1.000000 protected reserve = USD19.083840**. Maximum episode holds: central USD0.130048, shared USD0.390144, private USD0.384000. Input sizing includes full prompt, system, schema and the historical 826-token allowance, padded by 10% and rounded upward to 64 tokens; output hold is 1,152 tokens for the proposed 1,024 enforced maximum. Exact outer request bytes and per-depth maximal prompt fixtures are in config/sizing.json. USD4/20 per million is historical API-equivalent planning accounting; it does not establish current pricing or subscription cash charges. Cache creation and hidden request coverage remain readiness blockers. No extra calls are authorized by headroom.

A process lock and locked, hash-chained, append-only integer-microdollar cost ledger reserve a whole episode before its first call. Subholds allocate that reservation without charging it twice. Admission checks settled spend + outstanding holds + proposed hold + protected reserve against the **USD25 frontier envelope**, **USD39 operational stop**, and strictly-below-USD40 absolute cap. Missing usage keeps the uncertain hold and stops dispatch. Actual overruns are charged without clipping and trigger a durable stop. Known unused holds are released only after terminal disposition. The ledger must stay cumulative across any approved future version; a new version cannot reset prior spend/holds to zero.

Active-time ledgers count preflight/loading, transport waits and collector overhead across resumes: 12 hours local, 3 hours frontier; timeouts are 180/420 seconds, with additional admission headroom. A crash conservatively retains the remaining session time allowance. A partial start is never resent. A normal terminal episode is skipped on resume; a partial episode, unknown hold, durable STOP, identity/settings drift or fatal terminal integrity error blocks further dispatch. Do not delete a STOP or ledger to continue. Analyze saved evidence and bring any required deterministic bookkeeping/transport amendment back for review. Never generate replacement model evidence.

## Analysis and independent verification

After later collection or a resource/integrity stop:

```sh
python3 -B trl_analysis.py --base collection --out build/analysis-first
```

Analysis imports no provider adapter, network client or credential code. It replays raw first responses, regenerates the whitelisted prompt from prior-round receipts, compares request settings/hashes, checks all twelve opportunities against code truth, and reconciles known paid usage with the cost ledger. Unavailable numbers are null. It produces episodes.json, summary.json, tables.csv, tables.md and frontier-seeds.csv. The primary is the Qwen 7B paired seed-block ΔY/ΔH joint rule, including technical coverage, actually attempted episodes and complete-pair sensitivity; uncertainty uses 10,000 bootstrap draws with repeated-block multiplicity. Frontier is descriptive only. P1–P7, before/after relocation, per-round coverage/reward, repeats/new-cell queries, true-old-peak and best-observed stale exploitation, token/time/accounting summaries, baseline-normalized Y and greedy sharing gain are preserved. Explain plainly on any eventual page if a simple script also obtains most of the observed sharing benefit.

Claude must independently rebuild from a fresh clone containing the exact freeze and preserved collection evidence, and compare all outputs before scientific acceptance. A negative finding can be accepted; missing mandatory frontier evidence cannot. No results page, publication, scientific acceptance or model finding is produced by this offline build.
