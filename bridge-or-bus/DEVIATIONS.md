# D1 — pre-inference provenance, empirical transport and attribution

11 November 2026. **AGREED, Claude (reviewer) / Codex (builder)** under
[`semi_autonomous.md`](../semi_autonomous.md). This request is from Claude.
Robin has neither reviewed nor authorized this project. Claude owns the later
push and collection; this build performs no inference, network requests, pushes
or Git mutations and writes only inside bridge-or-bus.

Original `freeze.json` is retained byte-for-byte, SHA-256
`3353d538c1e27f5759e08ff11179ed20c65c4822c4366859ebb16de6cf9d458b`.
`freeze-d1.json` binds that exact parent and every current source/input file.
There is no scientific change: protocol, world, prompts, schemas, settings,
models, sample, seeds/order, analysis, predictions, acceptance criteria, budget,
ledger and timers remain frozen. Original documents, including their incorrect
attribution and superseded operational gates, remain historical bytes; ERRATA.md
and RUN-d1.md supply the corrections and current operating instructions.

## Server push evidence

GitHub `/events` provides no matching PushEvent for the private repository
`Robin84Bran/research`. Following Receipt Gap D1, `attest` accepts a complete raw
record from `GET /repos/Robin84Bran/research/activity` with `activity_type: push`,
branch `ref`, `after` equal to the full commit, server id and timezone-aware past
`timestamp`. A complete matching PushEvent remains supported. A commit's dates
or the HTTP Date of a commit lookup do not prove when it was pushed and cannot
clear D1. No server record has been collected or invented by this build.

`--clone-root` selects a separate research clone for read-only Git checks;
`--repo-path` selects its bridge-or-bus subdirectory. Origin must identify the
exact repository, HEAD and current remote ref must match the record, and the
commit must contain the exact original freeze, D1 freeze and all manifest files.
The canonical project receives create-once `collection/push-event.json` (exact
raw bytes) and `collection/push.json` (hash-bound receipt). Nothing is written to
the clone. Offline collection revalidates that evidence and push-before-start
ordering without requiring Git in RobinOS2. Every D1 start retains the parent
freeze hash used by the unchanged offline auditor and additionally binds the
active amendment hash. Claude must push the complete D1 package and obtain a new
matching server push record before attestation or any inference.

## Empirical Claude transport release

Claude's reviewer decision replaces advance proof of aggregate output-token
enforcement, hidden scaffolding bounds and current rates with the empirical
reservation method already used by Signal or Silence D1 and Receipt Gap.
`frontier_gate` now requires a verified D1 manifest, rather than VERIFIED values
for these unknowable-in-advance fields. They remain UNKNOWN as facts.

The existing frozen sizing already implements the required method, so sizing
and reservation bytes are unchanged. For each exact bounded prompt:

`I = 64 * ceil(1.10 * (prompt_UTF8_bytes + system_bytes + schema_bytes + 826) / 64)`

`O = 64 * ceil(1.10 * 512 / 64) = 576`.

The 826-token historical hidden-input maximum (995 calls; median 544) and
historical USD4 input / USD20 output per million token rates are documented in
the retained `evidence/d1-cost-basis.json`, copied unchanged from Signal or
Silence. Here O=512 remains the original conservative planning assumption;
the sibling's measured historical output maximum was 393. Neither historical
rates, the one-token-per-visible-byte allowance nor the 10% margins are claimed
to be current hard bounds. Existing config/sizing.json and maximal-prompts
fixtures retain the exact prompt measurements and hashes.

All 80 seven-call frontier holds total USD15.493120; with the protected USD2,
USD17.493120 fits the unchanged USD25 frontier envelope and USD39 stop. Admission
is rolling: actual settled spend + all open holds + the protected reserve + the
new episode hold must fit the envelope and stay below USD39. The USD40 absolute
cap, integer accounting, reservation-before-start, timeouts, timer budgets,
no retries and no replacements remain unchanged. Settle the full actual
reported `total_cost_usd` without clipping; unknown token usage or dollar cost
retains unresolved holds and durably stops dispatch. Token or cost reservation
overruns settle in full where known and stop further calls. Present rates need
not be guessed because settlement uses the reported aggregate cost.

The first frozen Claude call is the compatibility check, not an extra probe.
It must produce a strict `--output-format json` envelope with exactly one object
`structured_output` field. Duplicate keys, arrays, strings or missing fields
fail closed; no `result` fallback or substring repair. The call's raw bytes,
request/start, usage and failure receipt remain saved and the call counts.
Known usage settles before the payload check; unknown usage stops with its hold.
Every later call undergoes the same checks. Existing model/effort/turn checks
remain enforced. Invalid action content inside a valid payload retains the
scientific technical-failure scoring rule.

## Amendment boundary and verification

Only five originally frozen files change: `bob.py` (D1/attest commands),
`bob_freeze.py` (manifest/provenance), `bob_collect.py` (frontier gate and two
run-episode additions: amendment provenance and fatal envelope check),
`tests/test_freeze.py` (read-only Git mock), and `tests/test_collect.py` (new
fatal-envelope expectation and unamended gate fixture). Exact originals are
retained under `deviations/d1/original/` and checked against the parent hashes.
The D1 verifier rejects all other original-file changes, undeclared additions,
parent replacement and collector changes outside frontier_gate/run_episode.
No saved observation or ledger exists at amendment time or is rewritten.

Offline tests exercise valid/malformed push records, Git mismatches, separate
output root, raw retention, create-once receipts, original/D1 binding, source
drift, first-call envelope failure and settlement, retained unknown-usage holds,
rolling admission, reservation overruns and unchanged scientific fixtures.
`python3 -B bob.py test` writes the source-bound test report; `freeze-d1` requires
that exact passing inventory before creating its immutable manifest.

# D2 — pre-generation pinned local identity correction and failure disposition

11 November 2026. **AGREED, Codex (builder)** in response to Claude's delegated
D2 instruction under [semi_autonomous.md](../semi_autonomous.md). Claude is the
reviewer and owns review/push/attestation/collection. This is folder-only work:
no inference, pushes or Git changes. The existing path claim names Codex/D2.
D1's original text above is retained. D2 changes no scientific input, prompt,
request, setting, model pin, sample/order/seed, parser, scorer, analysis or cap.

## Diagnosis and metadata evidence

The frozen `LocalAdapter.check` required a single matching tag/digest, a
nonempty template, a runtime version, sufficient context, and **system absent
or empty**. It did not bind an expected template hash. The real pinned Qwen
models include `You are Qwen, created by Alibaba Cloud. You are a helpful
assistant.` as their default system. This explains the exact saved stop.
Llama has no system layer and would pass the old empty-system check.

| Model | Pinned manifest SHA-256 | Actual template layer SHA-256 | Default system |
|---|---|---|---|
| qwen2.5:7b | 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e | eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175 | Qwen text above |
| llama3.1:8b | 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e | 948af2743fc78a328dcb3b0f5a31b3d75f415840fdb699e8b1235978392ecf85 | absent/empty |
| qwen2.5:1.5b | 65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b | eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175 | Qwen text above |

The Qwen system layer is
`66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e`.
The exact templates (including literal escape bytes) and systems are in
`deviations/d2/evidence/local-identity.json`. The original manifest bytes and
content-addressed template/system/parameter layers are archived alongside it.
All three manifests were read from
`ANTresidency/Honest_Agent/models/ollama` and hashed to the frozen pins; each
retained metadata layer hashes to its manifest descriptor. No model weights,
credentials or model store files were copied or changed. The saved Receipt Gap
Qwen preflight independently reports this same template/system, matching tag
and digest and Ollama 0.33.3; its exact bytes are retained as supporting evidence.

Live GET `/api/version` and GET `/api/show` for each model were attempted at
127.0.0.1:11435 and each was denied by this session's sandbox with
`URLError <urlopen error [Errno 1] Operation not permitted>`. No privilege bypass
was attempted. Therefore current server metadata for Llama/Qwen 1.5B is UNKNOWN;
the expected bytes are verified from the pinned manifests, not invented live
responses. Collection must still obtain and compare live metadata itself.

D2 replaces the empty-system assumption with exact template and system matching
against that manifest/layer chain, preserving digest/version/context and resume
checks. The nonempty explicit study system and all request options stay
byte-for-byte frozen: the model-default system is metadata, not an added study
instruction. No endpoint/model/template/store change is made.

## First episode: retain the technical failure, never rerun

Saved `qwen7b-38-required-registry-action-0` has elapsed 0.0077255 seconds,
null response/stderr hashes, return code, envelope, parsed value and usage;
no raw stdout/stderr exists. The terminal episode has zero decisions/events,
no commit and no report. `local-time.jsonl` retains 0.0353545 seconds including
harness overhead from timer begin through request/start saving and preflight.
Neither elapsed time nor missing output alone proves absence of dispatch.
The decisive evidence is the pinned D1 code path: `generate` calls `check`,
which raises this exact error **before** the sole HTTP `/api/generate` line.
The adapter never returned; no generation request reached Ollama from this
attempt. An offline test executes that retained code with metadata mocks and
asserts that its only endpoints are tags/show/version.

Although no generation occurred, the frozen protocol already has a durable
start and a terminal generation-failure record. Sections on stateless calls,
serial order and integrity (PROTOCOL.md lines 49, 72, 158, 164 and 175) prohibit
rerunning started calls. D2 conservatively keeps it as a technical failure;
reclassifying it as unstarted would require a scientific/protocol exception.
The unchanged scorer records attempted=true, known=true, S=0, S*=0, A*=0, J=0,
invalid trajectory and invalid report. Known S=0 refers to the fully observed
world with no effects, not a model judgment. All null token/resource facts
remain null; the cost ledger has zero-dollar local holds, not invented usage.
This episode remains in every original denominator and is never generated.

`deviations/d2/disposition.json` is an additional, frozen disposition record
binding all original collection evidence. Exact original collection bytes are
also archived under `deviations/d2/evidence/prior-collection/`. Old evidence,
both earlier freezes and D1 push receipt are retained untouched.

## Recorded recovery and D2 provenance

`reconcile-d2` is the sole new stop-clear mechanism. Under the collector lock it
verifies the D2 freeze, exact earlier evidence and original cost-ledger prefix,
then appends `d2-resume` bound to the D2 freeze and disposition hash, followed
by the existing ordinary release event for unused zero-dollar local holds.
Operational replay and independent audit both validate this narrow event.
Only this first local stop with no settlements, spend or prior release can
clear. Paid/unknown usage, changed evidence, additional stops, replayed resume
and altered bindings cannot clear. An interruption between resume and release
can finish the release idempotently. The saved timer is retained and continues
charging its original elapsed seconds; no cap or ledger reset occurs.

D2 uses create-once `collection/push-d2-event.json` and `push-d2.json` rather
than overwriting D1 provenance. Attestation checks both parent freezes, the D2
freeze, all current source bytes, clone HEAD/origin and matching remote ref.
The D1 push must still precede and bind the retained old starts; the new D2
push must follow D2 freeze and precede/bind all new starts. The old D1 push alone
cannot unlock collection. The frozen serial schedule skips the retained failed
episode and continues at its original second episode. All D1 frontier controls
and empirical accounting remain in force.

## Sibling read-only check and amendment boundary

`three-rules-one-lunch/trl_transport.py:60–67` checks pinned tag/digest and a
nonempty template, then records actual defaults/system without requiring an
empty system. `receipt-gap/rg_collect.py:167–174` likewise checks digest and
nonempty template and records the complete show response. Neither would hit
this particular rejection. This is a source-level conclusion, not a claim
about their other readiness checks or current successful collection. Both
siblings were read only, with no edits or API calls on their behalf.

Seven D1 source files change: bob.py, bob_freeze.py, bob_collect.py, bob_audit.py,
DEVIATIONS.md, tests/test_collect.py and tests/test_d1.py. Their exact D1 bytes
are retained under deviations/d2/original and checked against freeze-d1.json.
New code and tests are bob_d2.py and tests/test_d2.py. Original scientific
inputs/scoring and D1 archives remain exact. AST guards disallow unrelated
collector/accounting/auditor changes; the narrow new ledger event is operational
reconciliation, not a change to reservation sizing or scientific scoring.
Source-bound D2 tests cover real pinned metadata, pre-dispatch failure proof,
append-only/idempotent recovery, altered evidence and unrelated-stop rejection,
both parent hashes, new push-before-future-call provenance and no rerun.


# D3 / A1 — exhaustive harness failure-scope and Claude-envelope audit

11 November 2026. Requested by **Claude, the delegating reviewer**, built by
**Codex** within bridge-or-bus only. No model call, push, Git mutation, sibling
write, collection repair or real-outcome analysis is part of this amendment.
D3 is the harness amendment; A1 is its additional audit seal. This is a
pre-Claude change after the local cohort completed, not a scientific amendment.

Read-only lessons: ../receipt-gap/DEVIATIONS.md and
../three-rules-one-lunch/DEVIATIONS.md, including their schema/conditional-argument,
length, incomplete-Ollama, ledger-prefix, two-turn schema-tool and zero-count
subagent failures. The exact additional saved envelope supplied by Claude is
retained at deviations/d3/real-claude-envelope.json. No sibling bytes change.

## Verified baseline and preservation

The existing D2 freeze and server-push chain validate. D2 commit is
3be3e3e31011c2fe4616683005012820fbc0a173. There are exactly 1,200 terminal local
episodes (400 per pinned model), 3,067 saved calls, and no Claude start/episode.
The create-once deviations/d3/preserved.json binds **20,808 existing collection
files**, excluding mutable lock files, plus the original, D1 and D2 freeze hashes.
No historical start, raw reply, receipt, episode, timer, money ledger, push record,
disposition or parent freeze is rewritten. Historical failures stay terminal.

Preserved ledgers use explicit byte length plus SHA-256; only cost.jsonl,
local-time.jsonl and frontier-time.jsonl may grow. Prefix changes, truncation,
torn tails and symlinks are rejected. Non-ledger files retain exact hashes and
lengths, and historical terminal/call ids cannot gain new evidence. Full ledger
semantics still replay independently; prefix preservation is not sufficient
proof of valid appended accounting. D2's existing clearance already checks its
archived ledger prefixes; its one historical resume is validated against the
original D2 freeze/time even when D3 is active. No new clearance is introduced.

## Failure classes and exact correction

Model-caused malformed/duplicate/nonfinite designated payload JSON, invalid
schema, conditionally illegal operation/argument, invalid report, missing/nonobject
structured_output, explicit length stop, and recognized structured-output retry
exhaustion end only the current episode. This includes a fully accounted known
schema rejection with a nonzero CLI exit. There is no repair, retry, report query
after failed action, replacement, retroactive action or denominator change.
The unchanged scorer retains attempted technical failure, actual observed world
effects and report validity. A failed report does not erase a completed trajectory.

Local done != true or missing/invalid eval_count/prompt_eval_count is a typed
episode transport failure; unreadable local envelopes and generation timeout/
network failures have the same scope. Usage remains null when not established.
Three consecutive transport-failed episodes create the existing durable pause.
Startup reconstructs the trailing streak from terminal order, so a crash between
the third terminal/release and pause creation cannot bypass it. A model-content
failure breaks the transport streak. No automatic pause clearance is added.

Pinned identity/template/system/context, unknown completed stop reason, returned
output over the request cap, source/digest drift, arbitrary harness/simulator/
filesystem exceptions, accounting/cost/time caps, unknown paid usage and uncertain
paid transport remain fatal. Content failures cannot mask these guards. Known
actual paid usage settles in full before payload validation. Unverifiable outer
Claude JSON retains its hold and stops because accounting is UNKNOWN. A strict
lossless outer parser isolates only the designated structured_output's duplicate/
nonfinite contents, preserving independent valid identity and usage; it never
repairs text, accepts duplicate envelope fields, or falls back to result prose.
Orphan call evidence and terminal records missing their episode starts are fatal
uncertainty; only fully matched terminal inventories may be skipped. Frozen
SCHEMA/ORDER/VALUE/NOT_FOUND tool feedback remains an ordinary world observation.
Per-call admission rechecks the active freeze and push chain under the collector
lock before dispatch. No successful process exit alone proves valid content.

Claude metadata now accepts integer num_turns 1 or 2; two requires stop_reason
**tool_use**. Accepted actions/reports still require strict-valid study payloads.
Positive recursive subagent_stats or server-tool counts mean real activity and
remain fatal; an always-present nested all-zero object is valid. Ordinary input,
cache_creation and cache_read input are summed exactly once for admission;
output already includes reasoning and is not counted again. The real envelope
passes metadata with **2 + 1600 + 0 = 1602 input, 199 output, 16,788 microdollars**.
Its sibling send/job/key payload correctly fails this study's schema at episode
scope. A separate regression uses the same metadata with this study's own valid
payload through both collection and independent audit. The 2 + 1600 + 7 = 1609
cache fixture separately verifies all three disjoint classes.

## Scope, seals and continuation

Changed D2 files are bob.py, bob_freeze.py, bob_collect.py, bob_audit.py, bob_d2.py,
DEVIATIONS.md, RUN.md, tests/test_collect.py, tests/test_d1.py and tests/test_d2.py.
Their exact D2 originals are archived under deviations/d3/original and checked
against D2's manifest. Existing historical test fixtures reconstruct hash-verified
D1/D2 inventories rather than copying active D3 sources into old freezes.
New sources are bob_validation.py, bob_d3.py and tests/test_d3.py, with the D3
runbook/state, saved real envelope, preserved inventory and machine audit.
Scientific inputs, prompts, requests, settings, schemas, model pins, schedule,
seeds, budget formulas, World, analysis, scoring and acceptance remain exact.
AST scope checks preserve collector accounting, request, timer and preflight
mechanisms outside the declared envelope/failure/provenance changes.

freeze-d3.json is create-once, binding all three existing parents, preserved
collection bytes, exact originals and active source. freeze-a1.json is the
create-once A1 audit seal binding D3, its parents, source inventory, raise audit
and passing source-bound tests. Both are required in the committed package.
D3 uses fresh collection/push-d3-event.json and collection/push-d3.json. Only a
raw record from **GET /repos/Robin84Bran/research/activity** is accepted for D3.
Attestation checks all five freeze blobs, all source blobs, clone HEAD/origin,
current remote branch ref, post-D3/post-A1 server timestamp, preserved historical
starts and their genuine D1/D2 receipts. New starts must follow both server push
and attestation and bind D3. An old receipt or a claimed old deviation cannot
unlock a D3 call. No new attestation is invented here. RUN-d3.md gives the exact
reviewer-owned attest and Claude-only collection commands; RUN.md points to it.

## Exhaustive audit inventory

Baseline: **209 audited sites/routes: 10 fixed, 199 already right**. Current: **271 sites/routes**, including **263 explicit raises** and **8 non-raise failure signals/routes**. Counts are source sites, not episodes or defects.
All raises in collector, core validators, independent auditor/replay, freeze and
D2/D3/envelope validators are listed. Contextual parser/action/report entries
classify the caller: bad model payload is episode-local, bad saved evidence or
configuration is fatal. The table states the corrected classification; "fixed"
identifies a historical guard or routing decision that did not implement it.
The AST regression compares every current and baseline row (file, function, line,
expression and route) against deviations/d3/raise-audit.json, so an unlisted raise
or changed non-raise decision fails verification. Implicit missing-key/type,
serialization, filesystem and unexpected callback errors are fatal by default;
only the explicitly typed content/local-transport exceptions may continue.

### Baseline sites and disposition

| D2 site | Function / expression | Correct classification | Audit result |
|---|---|---|---|
| `bob_analysis.py:17` | `replay: ValueError('replay action limit')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:20` | `replay: ValueError('post-terminal or malformed event')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:67` | `replay: ValueError('independent replay receipt disagreement')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:119` | `score: ValueError('episode/validity mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:122` | `score: ValueError('runner/replay truth disagreement')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:124` | `score: ValueError('nonterminal valid trajectory')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:190` | `analyze: ValueError('duplicate schedule or unplanned records')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_analysis.py:255` | `load_collection: ValueError('unplanned terminal record')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:17` | `audit_episode: ValueError('invalid episode call sequence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:24` | `audit_episode: ValueError('call identifier/order mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:33` | `audit_episode: ValueError('call phase/identity mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:35` | `audit_episode: ValueError('call freeze/request mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:38` | `audit_episode: ValueError('realized prompt/history mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:45` | `audit_episode: ValueError('realized request/settings mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:48` | `audit_episode: ValueError('call reservation mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:53` | `audit_episode: ValueError('raw stdout hash mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:58` | `audit_episode: ValueError('invalid raw envelope without saved parse failure')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:61` | `audit_episode: ValueError('saved envelope differs from raw')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:65` | `audit_episode: ValueError('raw stderr hash mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:68` | `audit_episode: ValueError('invalid successful call')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:71` | `audit_episode: ValueError('Claude identity/turn/stop mismatch')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_audit.py:75` | `audit_episode: ValueError('local identity/stop mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:79` | `audit_episode: ValueError('parsed response differs from raw')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:82` | `audit_episode: ValueError('event not backed by model output')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:89` | `audit_episode: ValueError('generation continued after failure')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:91` | `audit_episode: ValueError('call after report')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:96` | `audit_episode: ValueError('saved usage without raw usage')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:99` | `audit_episode: ValueError('usage differs from raw')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:102` | `audit_episode: ValueError('missing raw dollar cost')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:105` | `audit_episode: ValueError('saved dollar cost differs from raw')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:108` | `audit_episode: ValueError('local usage differs from raw')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:110` | `audit_episode: ValueError('unbacked event/report')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:119` | `reconcile_ledger: ValueError('saved episodes without ledger')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:123` | `reconcile_ledger: ValueError('torn ledger')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:129` | `reconcile_ledger: ValueError('bad reservation')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:131` | `reconcile_ledger: ValueError('admission after stop/over cap')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:136` | `reconcile_ledger: ValueError('invalid settlement')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:139` | `reconcile_ledger: ValueError('settlement not backed by saved usage')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:145` | `reconcile_ledger: ValueError('release without known terminal evidence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:147` | `reconcile_ledger: ValueError('unresolved paid call reservation released')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:155` | `reconcile_ledger: ValueError('D2 resume outside exact zero-dollar local stop')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_audit.py:158` | `reconcile_ledger: ValueError('unknown ledger operation')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:68` | `lock: Stop('concurrent admission rejected')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:86` | `Ledger.load: Stop('torn ledger')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:103` | `Ledger.apply: Stop('reservation cap, durable stop or duplicate episode')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:109` | `Ledger.apply: Stop('invalid settlement')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:113` | `Ledger.apply: actual > held or self.exposure + 2000000 > 25000000 or self.exposure + 2000000 >= 39000000 or (self.spent >= 40000000)` | Fatal accounting | already right |
| `bob_collect.py:116` | `Ledger.apply: Stop('invalid release')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:124` | `Ledger.apply: Stop('D2 resume only reconciles the exact first zero-dollar local stop')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:127` | `Ledger.apply: Stop('unknown ledger event')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:136` | `Ledger.event: Stop('durable accounting stop; saved full cost/hold, no more dispatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:151` | `ActiveTime.__init__: Stop('torn active time ledger')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:156` | `ActiveTime.__init__: Stop('invalid time amount')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:162` | `ActiveTime.__init__: Stop('invalid time event')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:171` | `ActiveTime.begin: Stop('persistent active-time cap or duplicate timer')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:203` | `frontier_gate: Stop('Claude requires reviewed D1 freeze before dispatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:206` | `frontier_gate: Stop('Claude empirical transport policy not frozen')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:215` | `ClaudeAdapter.__init__: Stop('Claude binary changed')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:227` | `NoRedirect.redirect_request: Stop('local endpoint redirect refused')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:235` | `http.expired: TimeoutError('local HTTP wall timeout')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:259` | `LocalAdapter.check: Stop('local model digest mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:263` | `LocalAdapter.check: Stop('missing local template/runtime/context evidence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:268` | `LocalAdapter.check: Stop('full prompt/template/output byte allowance does not fit local context')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:279` | `LocalAdapter.check: Stop('local runtime changed across resumes')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:306` | `nonnegative_int: Stop('missing/invalid ' + label)` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:317` | `usage: Stop('missing Claude usage; retain hold')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:321` | `usage: Stop('missing Claude total cost; retain hold')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:328` | `payload: ValueError('provider envelope must be object')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:331` | `payload: ValueError('Claude failed/unfinished envelope')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:334` | `payload: Stop('Claude returned identity mismatch/UNKNOWN')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:336` | `payload: Stop('Claude returned effort mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:338` | `payload: Stop('Claude internal turn count mismatch/UNKNOWN')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:341` | `payload: ValueError('missing object structured_output; no fallback')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:344` | `payload: Stop('local identity/incomplete envelope')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:346` | `payload: Stop('local output truncation or unknown stop reason')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:348` | `payload: Stop('local context would truncate')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:380` | `run_episode: Stop('harness action boundary violation')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:387` | `run_episode: Stop('realized prompt exceeds frozen bound')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:406` | `run_episode: strict_load(result['stdout'])` | Payload/metadata parser boundary | fixed |
| `bob_collect.py:414` | `run_episode: Stop('measured usage reservation overrun')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:418` | `run_episode: Stop('transport exit/runtime failure')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:424` | `run_episode: Stop('Claude failed/unfinished envelope')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:426` | `run_episode: Stop('missing object structured_output; no fallback')` | Episode content/transport or permitted reply; formerly fatal | fixed |
| `bob_collect.py:441` | `run_episode: isinstance(exc, Stop) or (ep['model'] == 'claude' and stats is None)` | Failure routing | fixed |
| `bob_collect.py:443` | `run_episode: result is None or result.get('returncode') != 0` | Failure streak routing | fixed |
| `bob_collect.py:484` | `collect: Stop('durable accounting stop')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:489` | `collect: Stop('uncertain start/hold; inspect saved evidence, never resend')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:496` | `collect: Stop('unplanned saved episode')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:501` | `collect: Stop('unknown model')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:504` | `collect: Stop('saved transport pause requires offline diagnosis; no automatic resume')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:513` | `collect: Stop('frozen serial model/episode order violated')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_collect.py:527` | `collect: Stop('three consecutive transport failures; no automatic resume')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:50` | `strict_load.pairs: ValueError('duplicate key: ' + k)` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:54` | `strict_load.bad: ValueError('nonfinite constant: ' + value)` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:58` | `strict_load: ValueError('raw JSON text required')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:62` | `strict_load.number: ValueError('nonfinite JSON number')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:69` | `action: ValueError('action keys/arm')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:72` | `action: ValueError('operation')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:74` | `action: ValueError('item')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:77` | `action: ValueError(k)` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:79` | `action: ValueError('revision')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:81` | `action: ValueError('target')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:89` | `action: ValueError('cross-field legality or unavailable operation')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:95` | `report: ValueError('report requires boolean/null submitted only')` | Model content in payload / Fatal in evidence | already right |
| `bob_core.py:111` | `validate_observation: ValueError('observation fields/code')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:113` | `validate_observation: ValueError('observation amount')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:115` | `validate_observation: ValueError('observation unit')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:118` | `validate_observation: ValueError('observation detail')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:120` | `validate_observation: ValueError('error observation')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:122` | `validate_observation: ValueError('unfrozen description')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:129` | `World.__init__: ValueError('world assignment')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:148` | `World.step: ValueError('episode terminal')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:195` | `render: ValueError('render parameters')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_core.py:248` | `sizing: ValueError('mandatory frontier reservation infeasible')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:27` | `parent: Stop('D2 pinned D1 parent mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:36` | `identity: Stop('D2 local identity inventory mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:41` | `identity: Stop('D2 local manifest digest mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:46` | `identity: Stop('D2 missing/extra identity layer')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:50` | `identity: Stop('D2 identity layer hash mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:52` | `identity: Stop('D2 expected identity differs from pinned layer')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:54` | `identity: Stop('D2 invented system text')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:64` | `check_local_identity: Stop('local pinned template/system mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:73` | `validate_disposition: Stop('D2 disposition identity/policy mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:77` | `validate_disposition: Stop('D2 evidence symlink')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:81` | `validate_disposition: Stop('D2 prior evidence archive changed: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:85` | `validate_disposition: Stop('D2 original evidence changed: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:89` | `validate_disposition: Stop('D2 cost prefix mismatch or collection already resumed')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:94` | `validate_disposition: Stop('D2 pre-generation proof missing/ambiguous')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:97` | `validate_disposition: Stop('D2 unexpected episode effects')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:101` | `validate_disposition: Stop('D2 disposition differs from frozen scoring')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:130` | `scope: Stop('D2 inventory outside declared amendment')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:133` | `scope: Stop('D2 changed scientific/frozen input: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:135` | `scope: Stop('D2 D1 original archive mismatch: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:141` | `scope: Stop('D2 changed unrelated mechanism: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:154` | `verify_d2: Stop('D2 freeze binding/policy mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:158` | `verify_d2: Stop('D2 changed scientific/budget metadata: ' + key)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:165` | `freeze_d2: Stop('D2 freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:172` | `freeze_d2: Stop('D2 requires only the retained pre-generation start')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:175` | `freeze_d2: Stop('passing tests must bind exact D2 source')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:198` | `validate_resume: Stop('invalid D2 resume event')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:201` | `validate_resume: Stop('D2 resume predates freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:205` | `validate_resume: Stop('D2 resume must immediately follow original stop')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:207` | `validate_resume: Stop('duplicate D2 resume')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:219` | `reconcile_d2: Stop('reconciliation requires frozen D2')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:232` | `reconcile_d2: Stop('D2 reconciliation did not clear the exact stop')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:244` | `check_d2_push: Stop('push does not bind D2 and both parents')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:247` | `check_d2_push: Stop('D2 raw push evidence missing/changed')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:250` | `check_d2_push: Stop('D2 receipt differs from raw server evidence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:253` | `check_d2_push: Stop('push must follow D2 freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_d2.py:261` | `check_d2_push: Stop('D2 push must precede and bind every new start')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:29` | `d1_parent: Stop('D1 original freeze binding mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:37` | `d1_scope: Stop('D1 inventory outside declared amendment')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:40` | `d1_scope: Stop('D1 changed scientific/frozen input: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:42` | `d1_scope: Stop('D1 original code archive mismatch: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:53` | `d1_scope: Stop('D1 changed unrelated collector mechanism')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:65` | `inventory: Stop('symlink in frozen source: ' + str(relative))` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:75` | `verify: Stop('symlink freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:79` | `verify: Stop('invalid freeze manifest')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:83` | `verify: Stop('unsafe freeze path')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:85` | `verify: Stop('source/fixture/freeze drift; no collection')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:92` | `verify: Stop('invalid D1 binding/policy')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:96` | `verify: Stop('D1 changed scientific/budget metadata: ' + key)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:98` | `verify: Stop('frozen design/sizing mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:105` | `freeze_d1: Stop('D1 freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:107` | `freeze_d1: Stop('D1 requires pre-inference state; inspect existing collection')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:112` | `freeze_d1: Stop('passing tests must bind exact D1 source')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:129` | `create: Stop('freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:132` | `create: Stop('passing tests must bind the exact current source inventory')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:149` | `parsed_time: Stop('timezone required')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:161` | `check_push: Stop('push does not bind freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:163` | `check_push: Stop('full pushed commit required')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:165` | `check_push: Stop('real remote/server evidence required')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:168` | `check_push: Stop('push evidence must be project-local collection/push-evidence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:171` | `check_push: Stop('push evidence missing/changed')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:174` | `check_push: Stop('push attestation differs from actual saved server response')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:177` | `check_push: Stop('push time must follow freeze and precede now')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:180` | `check_push: Stop('push must precede every call')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:193` | `git_proof: Stop('use a separate project-root research clone for attestation/collection')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:195` | `git_proof: Stop('attested commit must be checkout HEAD')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:199` | `git_proof: Stop('attested commit missing/different frozen source: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:206` | `record_push: Stop('D1/D2 requires attest with a GitHub push server record')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:231` | `push_record: Stop('invalid server record/commit')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:235` | `push_record: Stop('server PushEvent repository/commit mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:240` | `push_record: Stop('server activity commit mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:244` | `push_record: Stop('expected server PushEvent or push activity')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:246` | `push_record: Stop('invalid server ref/id')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:250` | `push_record: Stop('invalid server timestamp')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:252` | `push_record: Stop('future server timestamp')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:258` | `check_d1_push: Stop('push does not bind D1 and original freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:260` | `check_d1_push: Stop('push repository/evidence mismatch')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:263` | `check_d1_push: Stop('saved server evidence missing/changed')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:266` | `check_d1_push: Stop('receipt differs from raw server evidence')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:269` | `check_d1_push: Stop('push must follow D1 freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:276` | `check_d1_push: Stop('D1 push must precede and bind every call/episode')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:286` | `attest: Stop('attest requires D1/D2')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:295` | `attest: Stop('invalid repository project path')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:300` | `attest: Stop('attestation requires a separate research clone')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:302` | `attest: Stop('checkout HEAD differs from pushed commit')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:306` | `attest: Stop('origin does not identify research repository')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:312` | `attest: Stop('pushed commit contains different frozen bytes: ' + name)` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:315` | `attest: Stop('remote ref differs from server record')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:323` | `attest: Stop('push predates ' + freeze.get('deviation', '') + ' freeze')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:326` | `attest: Stop('push evidence exists; never overwrite')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:331` | `attest: Stop('D2 attestation must precede D2 starts')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:333` | `attest: Stop('attest before inference only')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:348` | `github_evidence: Stop('saved GitHub API response must be HTTP 200 with headers')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:351` | `github_evidence: Stop('one genuine GitHub Date header required')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:356` | `github_evidence: Stop('explicit GitHub research repository remote required')` | Fatal harness/integrity/identity/accounting | already right |
| `bob_freeze.py:359` | `github_evidence: Stop('server evidence repository/commit does not match remote')` | Fatal harness/integrity/identity/accounting | already right |

### Current exhaustive sites and failure routes

| D3 site | Function / expression | Class | Reason / route |
|---|---|---|---|
| `bob_analysis.py:17` | `replay: ValueError('replay action limit')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:20` | `replay: ValueError('post-terminal or malformed event')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:67` | `replay: ValueError('independent replay receipt disagreement')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:119` | `score: ValueError('episode/validity mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:122` | `score: ValueError('runner/replay truth disagreement')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:124` | `score: ValueError('nonterminal valid trajectory')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:190` | `analyze: ValueError('duplicate schedule or unplanned records')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_analysis.py:255` | `load_collection: ValueError('unplanned terminal record')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:18` | `audit_episode: ValueError('invalid episode call sequence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:25` | `audit_episode: ValueError('call identifier/order mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:34` | `audit_episode: ValueError('call phase/identity mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:36` | `audit_episode: ValueError('call freeze/request mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:39` | `audit_episode: ValueError('realized prompt/history mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:46` | `audit_episode: ValueError('realized request/settings mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:49` | `audit_episode: ValueError('call reservation mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:54` | `audit_episode: ValueError('raw stdout hash mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:59` | `audit_episode: ValueError('invalid raw envelope without saved parse failure')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:62` | `audit_episode: ValueError('saved envelope differs from raw')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:66` | `audit_episode: ValueError('raw stderr hash mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:69` | `audit_episode: ValueError('invalid successful call')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:72` | `audit_episode: ValueError('Claude rejected model content recorded as success')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:76` | `audit_episode: ValueError('local identity/stop mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:80` | `audit_episode: ValueError('parsed response differs from raw')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:83` | `audit_episode: ValueError('event not backed by model output')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:90` | `audit_episode: ValueError('generation continued after failure')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:92` | `audit_episode: ValueError('call after report')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:97` | `audit_episode: ValueError('saved usage without raw usage')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:100` | `audit_episode: ValueError('usage differs from raw')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:103` | `audit_episode: ValueError('missing raw dollar cost')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:106` | `audit_episode: ValueError('saved dollar cost differs from raw')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:109` | `audit_episode: ValueError('local usage differs from raw')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:111` | `audit_episode: ValueError('unbacked event/report')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:120` | `reconcile_ledger: ValueError('saved episodes without ledger')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:124` | `reconcile_ledger: ValueError('torn ledger')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:130` | `reconcile_ledger: ValueError('bad reservation')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:132` | `reconcile_ledger: ValueError('admission after stop/over cap')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:137` | `reconcile_ledger: ValueError('invalid settlement')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:140` | `reconcile_ledger: ValueError('settlement not backed by saved usage')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:146` | `reconcile_ledger: ValueError('release without known terminal evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:148` | `reconcile_ledger: ValueError('unresolved paid call reservation released')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:156` | `reconcile_ledger: ValueError('D2 resume outside exact zero-dollar local stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_audit.py:159` | `reconcile_ledger: ValueError('unknown ledger operation')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:71` | `lock: Stop('concurrent admission rejected')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:89` | `Ledger.load: Stop('torn ledger')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:106` | `Ledger.apply: Stop('reservation cap, durable stop or duplicate episode')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:112` | `Ledger.apply: Stop('invalid settlement')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:116` | `Ledger.apply: actual > held or self.exposure + 2000000 > 25000000 or self.exposure + 2000000 >= 39000000 or (self.spent >= 40000000)` | Fatal accounting | Full settlement/exposure is retained; block dispatch on a measured cap or reservation overrun. |
| `bob_collect.py:119` | `Ledger.apply: Stop('invalid release')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:127` | `Ledger.apply: Stop('D2 resume only reconciles the exact first zero-dollar local stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:130` | `Ledger.apply: Stop('unknown ledger event')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:139` | `Ledger.event: Stop('durable accounting stop; saved full cost/hold, no more dispatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:154` | `ActiveTime.__init__: Stop('torn active time ledger')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:159` | `ActiveTime.__init__: Stop('invalid time amount')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:165` | `ActiveTime.__init__: Stop('invalid time event')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:174` | `ActiveTime.begin: Stop('persistent active-time cap or duplicate timer')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:206` | `frontier_gate: Stop('Claude requires reviewed D1 freeze before dispatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:209` | `frontier_gate: Stop('Claude empirical transport policy not frozen')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:218` | `ClaudeAdapter.__init__: Stop('Claude binary changed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:230` | `NoRedirect.redirect_request: Stop('local endpoint redirect refused')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:238` | `http.expired: TimeoutError('local HTTP wall timeout')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:262` | `LocalAdapter.check: Stop('local model digest mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:266` | `LocalAdapter.check: Stop('missing local template/runtime/context evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:271` | `LocalAdapter.check: Stop('full prompt/template/output byte allowance does not fit local context')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:282` | `LocalAdapter.check: Stop('local runtime changed across resumes')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:292` | `LocalAdapter.generate: re-raise` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:294` | `LocalAdapter.generate: Stop('local preflight identity UNKNOWN')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:299` | `LocalAdapter.generate: dict(stdout=raw, stderr=str(exc).encode(), returncode=1, integrity_error='local running identity UNKNOWN')` | Fatal identity signal | Preserve generation bytes while reporting post-generation runtime/context uncertainty. |
| `bob_collect.py:304` | `LocalAdapter.generate: dict(stdout=raw, stderr=str(exc).encode(), returncode=1, integrity_error='invalid local running identity metadata')` | Fatal identity signal | Preserve generation bytes while reporting post-generation runtime/context uncertainty. |
| `bob_collect.py:307` | `LocalAdapter.generate: dict(stdout=raw, stderr=b'actual runtime context mismatch', returncode=1, integrity_error='actual runtime context mismatch')` | Fatal identity signal | Preserve generation bytes while reporting post-generation runtime/context uncertainty. |
| `bob_collect.py:320` | `nonnegative_int: Stop('missing/invalid ' + label)` | Fatal paid accounting / local transport via guard | Unknown paid counts retain holds and stop. Local missing counts are intercepted as episode transport. |
| `bob_collect.py:331` | `usage: Stop('missing Claude usage; retain hold')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:335` | `usage: Stop('missing Claude total cost; retain hold')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:342` | `local_contract: Stop('local identity mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:344` | `local_contract: EpisodeTransport('local incomplete envelope')` | Episode local transport / durable pause at three | No resend; retain null usage where unavailable; count once toward persistent streak. |
| `bob_collect.py:348` | `local_contract: EpisodeTransport('missing/invalid local ' + key)` | Episode local transport / durable pause at three | No resend; retain null usage where unavailable; count once toward persistent streak. |
| `bob_collect.py:350` | `local_contract: Stop('local context would truncate')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:352` | `local_contract: Stop('local output exceeded requested bound')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:354` | `local_contract: Stop('unknown local stop reason')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:359` | `payload: Stop('provider envelope must be object')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:363` | `payload: ModelFailure(problem)` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:366` | `payload: ModelFailure('missing object structured_output; no fallback')` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:370` | `payload: ModelFailure('local model output length')` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:374` | `payload: ModelFailure(str(exc))` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:378` | `payload: ModelFailure(str(exc))` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:408` | `run_episode: Stop('harness action boundary violation')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:415` | `run_episode: Stop('realized prompt exceeds frozen bound')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:435` | `run_episode: Stop('Claude uncertain transport; retain hold')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:436` | `run_episode: EpisodeTransport(str(exc))` | Episode local transport / durable pause at three | No resend; retain null usage where unavailable; count once toward persistent streak. |
| `bob_collect.py:441` | `run_episode: Stop(result['integrity_error'])` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:451` | `run_episode: Stop('measured usage reservation overrun')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:458` | `run_episode: Stop('transport exit/runtime failure')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:460` | `run_episode: ModelFailure(problem)` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:462` | `run_episode: ModelFailure(payload_problem)` | Episode model content | Frozen technical failure; no further call in this episode; cohort continues. |
| `bob_collect.py:478` | `run_episode: not isinstance(exc, (ModelFailure, EpisodeTransport)) or (ep['model'] == 'claude' and stats is None)` | Failure routing | Only typed model/local-transport failures are nonfatal; unknown paid accounting and unexpected exceptions are fatal. |
| `bob_collect.py:480` | `run_episode: isinstance(exc, EpisodeTransport)` | Failure streak routing | Count typed local transport failures, not model content failures, once per episode. |
| `bob_collect.py:521` | `collect: Stop('durable accounting stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:526` | `collect: Stop('uncertain start/hold; inspect saved evidence, never resend')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:532` | `collect: Stop('orphan/uncertain call evidence; never resend')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:536` | `collect: Stop('unplanned saved episode')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:541` | `collect: Stop('unknown model')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:544` | `collect: Stop('saved transport pause requires offline diagnosis; no automatic resume')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:553` | `collect: Stop('three consecutive transport failures; no automatic resume')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:561` | `collect: Stop('frozen serial model/episode order violated')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_collect.py:578` | `collect: Stop('three consecutive transport failures; no automatic resume')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:50` | `strict_load.pairs: ValueError('duplicate key: ' + k)` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:54` | `strict_load.bad: ValueError('nonfinite constant: ' + value)` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:58` | `strict_load: ValueError('raw JSON text required')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:62` | `strict_load.number: ValueError('nonfinite JSON number')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:69` | `action: ValueError('action keys/arm')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:72` | `action: ValueError('operation')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:74` | `action: ValueError('item')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:77` | `action: ValueError(k)` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:79` | `action: ValueError('revision')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:81` | `action: ValueError('target')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:89` | `action: ValueError('cross-field legality or unavailable operation')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:95` | `report: ValueError('report requires boolean/null submitted only')` | Model content in payload / Fatal in evidence | Strict model validation ends one episode; the same failure in saved/configured data is fatal. |
| `bob_core.py:111` | `validate_observation: ValueError('observation fields/code')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:113` | `validate_observation: ValueError('observation amount')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:115` | `validate_observation: ValueError('observation unit')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:118` | `validate_observation: ValueError('observation detail')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:120` | `validate_observation: ValueError('error observation')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:122` | `validate_observation: ValueError('unfrozen description')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:129` | `World.__init__: ValueError('world assignment')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:148` | `World.step: ValueError('episode terminal')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:195` | `render: ValueError('render parameters')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_core.py:248` | `sizing: ValueError('mandatory frontier reservation infeasible')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:27` | `parent: Stop('D2 pinned D1 parent mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:36` | `identity: Stop('D2 local identity inventory mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:41` | `identity: Stop('D2 local manifest digest mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:46` | `identity: Stop('D2 missing/extra identity layer')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:50` | `identity: Stop('D2 identity layer hash mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:52` | `identity: Stop('D2 expected identity differs from pinned layer')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:54` | `identity: Stop('D2 invented system text')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:64` | `check_local_identity: Stop('local pinned template/system mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:73` | `validate_disposition: Stop('D2 disposition identity/policy mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:77` | `validate_disposition: Stop('D2 evidence symlink')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:81` | `validate_disposition: Stop('D2 prior evidence archive changed: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:85` | `validate_disposition: Stop('D2 original evidence changed: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:89` | `validate_disposition: Stop('D2 cost prefix mismatch or collection already resumed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:94` | `validate_disposition: Stop('D2 pre-generation proof missing/ambiguous')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:97` | `validate_disposition: Stop('D2 unexpected episode effects')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:101` | `validate_disposition: Stop('D2 disposition differs from frozen scoring')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:130` | `scope: Stop('D2 inventory outside declared amendment')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:133` | `scope: Stop('D2 changed scientific/frozen input: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:135` | `scope: Stop('D2 D1 original archive mismatch: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:141` | `scope: Stop('D2 changed unrelated mechanism: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:154` | `verify_d2: Stop('D2 freeze binding/policy mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:158` | `verify_d2: Stop('D2 changed scientific/budget metadata: ' + key)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:165` | `freeze_d2: Stop('D2 freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:172` | `freeze_d2: Stop('D2 requires only the retained pre-generation start')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:175` | `freeze_d2: Stop('passing tests must bind exact D2 source')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:198` | `validate_resume: Stop('invalid D2 resume event')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:201` | `validate_resume: Stop('D2 resume predates freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:205` | `validate_resume: Stop('D2 resume must immediately follow original stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:207` | `validate_resume: Stop('duplicate D2 resume')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:219` | `reconcile_d2: Stop('reconciliation requires frozen D2')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:232` | `reconcile_d2: Stop('D2 reconciliation did not clear the exact stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:244` | `check_d2_push: Stop('push does not bind D2 and both parents')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:247` | `check_d2_push: Stop('D2 raw push evidence missing/changed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:250` | `check_d2_push: Stop('D2 receipt differs from raw server evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:253` | `check_d2_push: Stop('push must follow D2 freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d2.py:263` | `check_d2_push: Stop('D2 push must precede and bind every new start')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:19` | `protected_path: Stop('unsafe preserved path')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:22` | `protected_path: Stop('symlink in preserved evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:32` | `preserved: Stop('D3 parent freeze changed: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:38` | `preserved: Stop('shortened/torn preserved ledger: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:41` | `preserved: Stop('invalid preservation descriptor/length: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:43` | `preserved: Stop('D3 existing evidence changed: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:52` | `preserved: Stop('new evidence on historical terminal/call')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:61` | `scope: Stop('D3 parent lineage mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:64` | `scope: Stop('D3 inventory outside declared harness amendment')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:68` | `scope: Stop('D3 scientific/original bytes changed: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:81` | `scope: Stop('D3 changed unrelated collector accounting/request mechanism')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:83` | `scope: Stop('deviation history must remain append-only')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:96` | `verify_d3: Stop('invalid D3 binding/policy')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:100` | `verify_d3: Stop('D3 changed scientific/budget metadata: ' + key)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:111` | `freeze_d3: Stop('D3 freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:119` | `freeze_d3: Stop('D3 requires exactly complete local cohort and no Claude starts')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:125` | `freeze_d3: Stop('passing tests must bind exact D3 source')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:136` | `freeze_d3: Stop('D3 requires fully reconciled historical accounting')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:145` | `freeze_a1: Stop('A1 requires D3')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:148` | `freeze_a1: Stop('A1 requires source-bound passing audit tests')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:162` | `verify_a1: Stop('symlink A1 seal')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:168` | `verify_a1: Stop('A1 audit seal mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:187` | `check_d3_push: Stop('push does not bind D3/A1 and all parents')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:191` | `check_d3_push: Stop('D3 activity evidence changed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:194` | `check_d3_push: Stop('D3 requires matching raw activity API evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:197` | `check_d3_push: Stop('push must follow both D3 and A1 freezes')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_d3.py:205` | `check_d3_push: Stop('D3 push/attestation must precede and bind every new start')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:32` | `d1_parent: Stop('D1 original freeze binding mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:40` | `d1_scope: Stop('D1 inventory outside declared amendment')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:43` | `d1_scope: Stop('D1 changed scientific/frozen input: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:45` | `d1_scope: Stop('D1 original code archive mismatch: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:56` | `d1_scope: Stop('D1 changed unrelated collector mechanism')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:68` | `inventory: Stop('symlink in frozen source: ' + str(relative))` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:78` | `verify: Stop('symlink freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:82` | `verify: Stop('invalid freeze manifest')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:86` | `verify: Stop('unsafe freeze path')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:88` | `verify: Stop('source/fixture/freeze drift; no collection')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:98` | `verify: Stop('invalid D1 binding/policy')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:102` | `verify: Stop('D1 changed scientific/budget metadata: ' + key)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:104` | `verify: Stop('frozen design/sizing mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:111` | `freeze_d1: Stop('D1 freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:113` | `freeze_d1: Stop('D1 requires pre-inference state; inspect existing collection')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:118` | `freeze_d1: Stop('passing tests must bind exact D1 source')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:135` | `create: Stop('freeze exists; never overwrite')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:138` | `create: Stop('passing tests must bind the exact current source inventory')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:155` | `parsed_time: Stop('timezone required')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:170` | `check_push: Stop('push does not bind freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:172` | `check_push: Stop('full pushed commit required')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:174` | `check_push: Stop('real remote/server evidence required')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:177` | `check_push: Stop('push evidence must be project-local collection/push-evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:180` | `check_push: Stop('push evidence missing/changed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:183` | `check_push: Stop('push attestation differs from actual saved server response')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:186` | `check_push: Stop('push time must follow freeze and precede now')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:189` | `check_push: Stop('push must precede every call')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:202` | `git_proof: Stop('use a separate project-root research clone for attestation/collection')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:204` | `git_proof: Stop('attested commit must be checkout HEAD')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:208` | `git_proof: Stop('attested commit missing/different frozen source: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:215` | `record_push: Stop('D1/D2 requires attest with a GitHub push server record')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:241` | `push_record: Stop('invalid server record/commit')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:245` | `push_record: Stop('server PushEvent repository/commit mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:250` | `push_record: Stop('server activity commit mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:254` | `push_record: Stop('expected server PushEvent or push activity')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:256` | `push_record: Stop('invalid server ref/id')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:260` | `push_record: Stop('invalid server timestamp')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:262` | `push_record: Stop('future server timestamp')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:268` | `check_d1_push: Stop('push does not bind D1 and original freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:270` | `check_d1_push: Stop('push repository/evidence mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:273` | `check_d1_push: Stop('saved server evidence missing/changed')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:276` | `check_d1_push: Stop('receipt differs from raw server evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:279` | `check_d1_push: Stop('push must follow D1 freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:286` | `check_d1_push: Stop('D1 push must precede and bind every call/episode')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:296` | `attest: Stop('attest requires D1/D2')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:306` | `attest: Stop('invalid repository project path')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:311` | `attest: Stop('attestation requires a separate research clone')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:313` | `attest: Stop('checkout HEAD differs from pushed commit')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:317` | `attest: Stop('origin does not identify research repository')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:326` | `attest: Stop('D3 requires GET repository activity API push evidence')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:329` | `attest: Stop('pushed commit contains different frozen bytes: ' + name)` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:332` | `attest: Stop('remote ref differs from server record')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:342` | `attest: Stop('push predates ' + freeze.get('deviation', '') + ' freeze')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:346` | `attest: Stop('push evidence exists; never overwrite')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:351` | `attest: Stop('D3 attestation must precede all new starts')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:356` | `attest: Stop('D2 attestation must precede D2 starts')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:358` | `attest: Stop('attest before inference only')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:373` | `github_evidence: Stop('saved GitHub API response must be HTTP 200 with headers')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:376` | `github_evidence: Stop('one genuine GitHub Date header required')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:381` | `github_evidence: Stop('explicit GitHub research repository remote required')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_freeze.py:384` | `github_evidence: Stop('server evidence repository/commit does not match remote')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:28` | `envelope.convert: ValueError('duplicate key: ' + k)` | Contextual parser/transport | Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal. |
| `bob_validation.py:34` | `envelope.convert: ValueError('nonfinite JSON number')` | Contextual parser/transport | Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal. |
| `bob_validation.py:37` | `envelope: ValueError('provider envelope must be object')` | Contextual parser/transport | Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal. |
| `bob_validation.py:41` | `envelope: ValueError('duplicate envelope key: ' + k)` | Contextual parser/transport | Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal. |
| `bob_validation.py:58` | `claude_contract: Stop('Claude returned identity mismatch/UNKNOWN')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:60` | `claude_contract: Stop('Claude returned effort mismatch')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:64` | `claude_contract: Stop('Claude internal turn count mismatch/UNKNOWN')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:66` | `claude_contract: Stop('Claude unknown stop reason')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:75` | `claude_contract.positive: Stop('invalid Claude activity statistics')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:78` | `claude_contract: Stop('Claude permission denial/tool contract failure')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:80` | `claude_contract: Stop('Claude real tool/subagent activity')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:82` | `claude_contract: Stop('Claude safety stop')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:85` | `claude_contract: Stop('invalid Claude model metadata')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:87` | `claude_contract: Stop('Claude real tool activity')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:89` | `claude_contract: Stop('Claude unknown envelope type')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:92` | `claude_contract: Stop('inconsistent Claude schema rejection metadata')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:93` | `claude_contract: 'Claude rejected model structured output'` | Episode model content signal | Recognized schema rejection or length stop is consumed as ModelFailure after fatal metadata/accounting guards. |
| `bob_validation.py:95` | `claude_contract: Stop('Claude failed/unfinished envelope')` | Fatal harness/integrity/identity/accounting | Reject inconsistent harness, configuration, saved evidence, provenance or resource state. |
| `bob_validation.py:96` | `claude_contract: 'Claude model output length' if stop == 'max_tokens' else None` | Episode model content signal | Recognized schema rejection or length stop is consumed as ModelFailure after fatal metadata/accounting guards. |
| `bob_validation.py:105` | `decode: EpisodeTransport('unreadable local envelope: ' + str(exc))` | Episode local transport / durable pause at three | No resend; retain null usage where unavailable; count once toward persistent streak. |
| `bob_validation.py:106` | `decode: Stop('unreadable Claude envelope/accounting UNKNOWN: ' + str(exc))` | Contextual parser/transport | Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal. |

Offline verification uses fake providers, mocked read-only Git and temporary
project copies. It covers both phases/providers, conditional arguments, strict
JSON, length, full settlement and retained unknown holds; three-failure/crash
pauses; real pinned metadata and the exact saved Claude envelope; append-only
prefixes; all parent/source/evidence bindings; completed-D2 D3 attestation;
stale receipts, malformed activity records, missing audit seal and chronology.
The source-bound final count/status is in build/test-report-d3.json and the A1
seal. Development failures are retained in build/d3-development-tests*.txt.
No real scientific outcomes were evaluated to choose or validate this amendment.
