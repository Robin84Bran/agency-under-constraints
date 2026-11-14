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
