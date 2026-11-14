# Portable Self · A1 runbook (pre-registration revision)

Claude delegated this build and reviewed the protocol as AGREED with notes. Codex records agreement in PROTOCOL.md; shared review transcription belongs to Claude because this session can write only this project. Robin has not reviewed this project. This package contains no real model observations. No model call, push, attestation or live collection was performed during build.

A1 supersedes the original first-call blanket-fatal rule. See DEVIATIONS.md for the exhaustive path audit and retained originals. `freeze-a1.json` is the active manifest and binds the byte-identical original `freeze.json`. Claude reports that neither push nor inference occurred before A1. This builder made no Git operations.

Python 3.9+ and Node, standard library only. The inherited Codex folder claim was verified read-only. All new durable files are here; sibling sources were read/copied, never edited. `evidence/provenance.json` records reuse. `evidence/original/PROTOCOL-v01-draft.md` preserves the previous draft. The two fake dry runs are pre-freeze engineering evidence; the first predates episode seals, and `offline/dry-run-v2/` is the final harness fixture. Both remain explicitly fake.

From this project, verify the immutable package and its fixtures:

```sh
python3 -B -m unittest discover -s tests -v
node --test evidence/toy/tests.mjs
node evidence/toy/batch.mjs --verify
node fixtures/generator-vectors.mjs --verify
python3 -B ps.py verify
shasum -a 256 freeze.json freeze-a1.json
PS_CHECK_DIR="$(mktemp -d /private/tmp/portable-self-check.XXXXXX)"
python3 -B revisions/a1/replay-check.py --output "$PS_CHECK_DIR/rebuild.json"
python3 -B ps.py dry-run --output "$PS_CHECK_DIR/fake"
python3 -B ps.py analyze --fake --data "$PS_CHECK_DIR/fake" --output "$PS_CHECK_DIR/fake-analysis.json"
```

The saved final dry run covers 33 model × world × arm cells at seed 0, 264 fake calls, both local and two-turn Claude-shaped envelopes. Tests additionally cover one-turn envelopes, malformed/null actions, wrong/inaccessible notes, duplicate keys, failures, missing usage, holds, overruns, crashes, prefix mutation, seals, push provenance, bootstrap multiplicity and joint primary guards. Toy checks replay all 640 worlds / 3,200 saved policy outcomes. Twelve Node-generated fixtures independently verify the new SHA-ranked world generator. The new study deliberately differs from the toy's exploration/feedback process.

`revisions/a1/replay-check.py` compares historical fake-analysis bytes with the original saved fixture while sockets, HTTP and subprocesses are forbidden. It performs no Git operation. The preserved `offline/rebuild-check.py` remains the historical Git-clone engineering method; A1 did not execute it. This proves fixture reproducibility; empirical acceptance still requires Claude's independent fresh research-clone review after data collection. Create new verification outputs outside frozen inputs; `verify` rejects changes or additions outside `collection/`. Never regenerate or overwrite either freeze, schedule, prompts, fixtures or analysis. `prepare`, `freeze` and `freeze-a1` are create-once build commands, already completed. A1 verifies its parent, original baselines and the narrow changed-file allowlist; verify rejects scientific drift.

## Later push and attestation · delegating reviewer

These commands are provided for a later execution stage; they were not run during build. In a separate research clone, copy the complete frozen package to `portable-self/`, including both freeze files, every A1 manifest input, retained originals and all offline evidence. Exclude `__pycache__`, `.git` and live `collection/`. Verify the package there before committing/pushing under the programme's applicable authority. Never change the RobinOS2 Git working tree. A local commit date is not push evidence.

After the reviewer has pushed the frozen commit to `Robin84Bran/research`, set only the clone path below. The attester itself obtains the full GitHub activity API response; no manually invented event file is accepted:

```sh
PS_PROJECT='<WORKSPACE>/06_intelligence/AI_research/research/portable-self'
PS_CLONE_ROOT='<absolute path to the separate research clone containing the pushed commit>'
PS_COMMIT="$(git -C "$PS_CLONE_ROOT" rev-parse HEAD)"
python3 -B "$PS_PROJECT/ps.py" attest --root "$PS_PROJECT" --clone-root "$PS_CLONE_ROOT" --repo-path portable-self --commit "$PS_COMMIT"
```

`attest` uses `gh api --method GET /repos/Robin84Bran/research/activity --paginate --slurp`. It verifies clone origin/HEAD, every active frozen committed file, both original and A1 freeze bytes, and the exact remote branch/ref. It requires a genuine matching `activity_type:push`, `after`, `ref`, id and timezone-aware past server timestamp after the A1 freeze. It writes create-once `collection/push-activity.json` (full raw response), `collection/push-event.json` (selected full record) and `collection/push.json` **here, under `--root`**. The clone supplies read-only Git checks. `/events`, absent PushEvents, commit dates and local clock claims do not substitute for the activity receipt. If no matching record exists, no call is admitted. The collector rechecks retained hashes and push-before-start on every resume.

## Later collection · local first, then Claude

Exact commands, after successful attestation and the later execution instruction:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/portable-self
python3 -B ps.py collect --cohort local
python3 -B ps.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

The serial frozen order is Qwen 7B, Llama 8B, Qwen 1.5B, then Claude; 1,020 local episodes / at most 8,160 calls, then 60 frontier episodes / at most 480 calls. Each episode has exactly four memory-writing opportunities followed by four return batches; failure leaves the remainder unstarted. No pilots, calibration inference, retries, repairs, replacement seeds or outcome-driven changes. Every request/prompt is saved and hashed before its durable start. Raw transport bytes (base64 alongside decoded text for actual transports) are saved before strict parsing.

Local endpoint is the existing `127.0.0.1:11435`. Metadata-only preflight checks manifest digest and the exact template/system layer chain against `evidence/models/`; Qwen retains its Alibaba system and Llama retains its empty system. Generation omits system/template overrides, uses `stream:false`, JSON mode, temperature .6, top_k 16, 192 predicted tokens, context 8192, seed `1000*seed+visit`. Returned running digest/context and input usage must establish integrity. Readiness is UNKNOWN until that stage. Wait through normal endpoint queueing within the time allowance; never pull models, start/restart services or parallelize collection. A timeout ends its episode without resend.

For local envelopes, `done` must be boolean true and input/output usage must be nonnegative integers; otherwise the episode is a transport failure. Unreadable/nonobject envelopes and failed requests/timeouts use the same scope. Three consecutive transport-failed episodes cause a durable pause before a fourth; the sealed-terminal streak survives invocations and a crash before STOP creation. Content failures and complete episodes break the streak. `done_reason:length` is a completed content failure for that episode. Identity, input truncation, known input/context or output reservation overruns, unexpected completed stop reasons/settings and corrupted evidence stop collection durably. Null controls and empty notes are valid behavior. Invalid batches execute no controls.

Claude's binary is pinned to version 2.1.312 / SHA-256 `6b5ec691195e551b02c41df9f7d723f4ea61eaa03c2df90acefe3736f1aeb620`. Help/version and relevant source were inspected offline, with no generation. Flags use `--json-schema`, `--output-format json`, medium effort, `--max-turns 2`, safe/restricted mode, empty real tools/MCP, no Chrome/slash commands/hooks/instruction discovery/session persistence, and an isolated empty temporary cwd. Only the terminal schema-output mechanism is allowed. Transport/schema retries and model fallback are disabled; no credentials are copied or changed. Existing subscription sign-in must already work. There is no provider/model fallback.

Every frontier call verifies exact model, complete usage and all integrity/accounting gates. Those failures stop dispatch immediately, including on the first call. Generated-content failures (including absent/nonobject/invalid `structured_output`, completed output-length stops and known completed schema-output exhaustion) end only their episode and the cohort continues. Known failed usage settles before content checks; unused future holds release when accounting is complete. The compatibility receipt binds the **first accepted frontier payload**, which may follow content-failed episodes. `num_turns` must be integer 1 or 2, with `tool_use` required for two turns. No `result` prose fallback. Missing returned effort remains UNKNOWN; conflicting effort is fatal. Input, cache-creation and cache-read tokens are summed; output includes charged aggregate usage. The runtime shape/accounting remains UNKNOWN until returned. Two-turn accepted payloads require tool_use; two-turn length/exhaustion envelopes may end an episode but are never accepted actions. Paid transport uncertainty and unknown paid usage remain immediately fatal.

## Budget, retention and recovery

The exact prospective frontier holds total **USD10.690560**, plus **USD1 protected reserve = USD11.690560**. `config/sizing.json` binds maximal escaped-note prompts, exact UTF-8 bytes, system/schema/outer wrapper bytes, historical 826-token hidden allowance, 10%/64 padding and 576 output-token reservations. Requested output setting 512 is best effort, not a proven bound on hidden/internal output. The binary matches the sibling mechanism; no larger hidden wrapper input was identified offline. Current cash billing and authoritative provider rates remain UNKNOWN; USD4/million all input and USD20/million output are an explicit API-equivalent planning/accounting basis, and any larger nonnegative CLI total_cost_usd controls settlement.

The whole eight-call episode is reserved before dispatch. Rolling admission includes settled spend, all outstanding/uncertain holds, the new reservation and USD1 reserve: frontier exposure ≤USD25 and project exposure <USD39. USD40 remains the outer programme line. Actual cost is rounded upward to integer microdollars and never clipped. Missing usage retains the whole unresolved hold. An overrun records actual spend and retains future holds, then durably stops dispatch. No cap extension is included. Local model-call accounting is USD0; hardware and opportunity costs are unpriced.

Persistent active caps are 24 hours local and 3 hours frontier, including preflight, queueing and collector overhead. Each 180s local / 420s frontier timeout must fit before dispatch; interrupted segments retain their full time reservation. Measured overrun stops dispatch. Disk/OS stalls and hidden provider behavior cannot be mathematically bounded by this harness.

Ledgers are locked and append-only. Each entry is hash-chained and gets a create-once byte-length/SHA-256 prefix anchor; starts bind the ledger prefix. Completed episode summaries bind every evidence file and are sealed into that journal. Resume verifies saved evidence, timing, usage/settlements, first-accepted-frontier contract and all prefixes before admitting work. Terminal episodes are skipped. Any prepared/started but unterminated episode, unresolved paid call, unsealed terminal or partial/unanchored journal tail requires diagnosis and a reviewed amendment. Never erase a start, STOP, hold, anchor, raw reply or frozen file to resume. A durable stop has no override or clearance flag. A transport pause also requires diagnosis and a separately reviewed amendment; no existing STOP is cleared in A1. Any later clearance must bind ledger byte-length/SHA-256 prefixes, permit only append-only growth, and independently verify appended semantics. Keep incomplete evidence.

## Offline empirical rebuild

After later collection, retain all `collection/` artifacts in the research repository and let Claude rebuild from a fresh clone without credentials or provider/network access:

```sh
cd "$PS_CLONE_ROOT/portable-self"
python3 -B ps.py verify
python3 -B -m unittest discover -s tests -v
python3 -B ps.py analyze --data collection --output collection/analysis-v01-r1.json
```

`analyze` is network-free and uses create-once output. It verifies push evidence locally, replays visible notes/requests/actions from raw responses, checks seals/prefixes/accounting, and reconstructs truth using the frozen generator. It includes all planned denominators, Y/F, answered-only accuracy, null/technical/missing/wrong counts, return positions, raw notes, slot selection/retention, literal-only fidelity, per-call usage/time/cost, paired contrasts, 10,000 seed-block bootstrap intervals, complete-pair sensitivity and all seven prediction decisions. Unknown factual outcomes stay null; their operational miss scores are explicit.

RESULTS must place each arm's prompt-token count/sum/mean/median/max and missing usage beside the effect. Keyed routing changes visible context as well as indexing. Do not claim equal compute, semantic mediation, consciousness, robotics or drift recovery. Unattempted data and incomplete mandatory cohorts cannot be presented as study acceptance. Negative or tied valid outcomes remain reportable. No scientific acceptance is asserted by these offline checks.
