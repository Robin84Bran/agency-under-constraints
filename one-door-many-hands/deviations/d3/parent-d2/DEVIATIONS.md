# D2 — saved-envelope classification and verified STOP clearance

Requested by Claude, delegating reviewer, after the first saved Claude attempt.
D2 binds `freeze.json`, `freeze-a1.json`, `freeze-d1.json` and
`freeze-d1-final.json` without rewriting any parent. Changed parent sources are
archived under `deviations/d2/parent-d1-final/`. All original scientific inputs,
contracts, scoring, budgets, schedules, denominators and raw records are retained.

The decisive saved envelope is a complete zero-use/cost pre-generation DNS
failure (`ENOTFOUND`, `duration_api_ms:0`, `api_error_status:null`,
`terminal_reason:api_error`, `is_error:true`, `modelUsage:{}`). Under the reviewer's
rule, genuine transport uncertainty requires no parseable envelope. D2 records
**HARNESS BUG**, with a narrow verified transport nonstart disposition. It is
explicitly not relabeled as 429 or as a generated model failure. The interpretation
and its exact evidence hashes are retained in `evidence/d2-decision.json`.

The generated-response validator also misrouted most exit-code-1 errors before
checking generation, rejected valid two-turn end-turn success, and confused
possible error metadata with identity mismatch. D2 separates generated content
failure from accounting/identity/tool/integrity gates. It covers max-tokens,
refusals, invalid/missing structured payloads, omitted error attribution, safety
refusals and complete generated envelopes saved before timeout. Output cap is
512; the padded accounting reservation is 576. No resource cap is enlarged.

429 nonstart classification accepts the generic limit label, omitted attribution,
zero counters alongside descriptive model metadata, and fully saved limit
responses even if the process subsequently times out. Unknown dated resets pause
with null reset time and never trigger an inferred resend. Generated refusals
with any nonzero usage remain model failures, not operational limit events.

The new freeze binds exact prior collection files plus three ledger byte-prefix
snapshots; log tails retain all checkpoint, chain, settlement and timer checks.
Create-once clearance binds STOP, terminal, nonstart, freeze and ledger prefixes.
Local D2 attestation binds all parents, original push/D1 receipt, clearance and
prefixes. New starts require D2; old starts must lie in the saved baseline. A
later fatal STOP has its own immutable marker and invalidates historical clearance.
The saved-terminal-before-STOP crash window also invalidates clearance before
any new dispatch, even if the later STOP file was never written.
No model dispatch, Git, push, network probe or sibling edit occurs in this repair.

Verification: real saved bytes, derived shape variants, fake continuation and
identical-request resume, full-cost settlement, parent/science preservation,
create-once freeze, clearance/attestation, prefix/tail tampering and later-fatal
rejection are exercised by `tests/test_d2.py` and the retained regression suite.
`RUN.md` has the exact local clearance, attestation and later resume commands.

---

# D1 final recovery guard

Final review after sealing the unused local draft found that its narrow
historical clearance could remain accepted after a later fatal error. Corrected
before attestation or Claude calls: durable_stop now retains a later fatal event
as STOP-after-usage-clearance.json, and any such event blocks the old clearance.
A regression drives a post-clearance preflight identity failure and confirms no
subsequent dispatch. The sealed draft freeze and its verification record remain
untouched. Changed draft sources are archived in deviations/d1/sealed-draft/.
freeze-d1-final.json binds freeze.json, freeze-a1.json and freeze-d1.json. Its
only differences from the draft are the recovery guard, final-freeze lineage
support, its regression, documentation, and new final verification evidence.
No model calls, attestation or Git operations occurred during either seal.
Final evidence: evidence/d1-final-tests.txt, evidence/d1-final-validation.json
and collection/d1-final-verification.json. The original D1 records below remain
as historical context.

---

# D1 — exact zero-use Claude limit refusals are definite non-starts

11 November 2026. Requested by Claude, the delegating reviewer agent. Local
post-push deviation before this project's first Claude call; local cohort is
complete. This decision is harness-only. No model calls, Git operations, pushes,
credential changes or sibling writes were performed by this implementation.

The promotion criterion, fixed before final validation, is: strict zero-use 429
refusals retain evidence, settle cost at zero and pause cleanly; after the stated
reset only the identical pending request resumes, with no earlier generated call
resent. Other failures retain the frozen disposition; science and saved local
records remain byte-identical. Verify with synthetic refusal fixtures, the exact
supplied real envelope, fake resume sequences, accounting/integrity failures,
parent-lineage checks and independent replay of the existing local cohort.

The D1 baseline has 3,600 local terminals, zero Claude attempts, and no STOP.
There was no earlier refusal scored in this project, so no real failure needs
re-disposition and no real clearance is created. The generic recorded clearance
is tested against a synthetic historical failure with immutable original bytes.

Changes: od_usage.py adds strict nonstart classification, reset calculation,
create-once markers, retained attempt sequences and narrow recorded clearance.
od_collect.py pauses/resumes at the saved position with fresh unique accounting
IDs and byte-identical requests. od_analysis.py replays attempts and counts
refusals as operational events outside model failure counts; only the final
model reply is scored. od_recovery.py ignores nonstarts when reconstructing
model transport streaks. od_validation.py accepts recursively zero-valued
subagent telemetry observed in the supplied real envelope, while nonzero or
unknown activity still stops. od_d1.py/od_freeze.py/od_provenance.py bind both
parent freezes, exact parent archives, prefix-verified ledgers and the original
push receipt, and require a new local D1 attestation before any Claude start.
No new push or fabricated remote provenance is introduced. Historical A1 tests
now target their exact archived parent package; D1 tests separately preserve
scientific ASTs and all unchanged parent hashes. RUN, state and RESULTS explain
current operation. All other existing original inputs are unchanged.

The exact original A1 inputs are retained under `deviations/d1/parent-a1/`.
Both previous freezes and existing collection evidence are retained as-is.
`evidence/d1-tests.txt` records final offline tests; `evidence/d1-validation.json`
records collection replay and preservation checks. No empirical model-result
analysis, model selection or scientific promotion was performed. The following
A1 audit is preserved as historical context; its line references apply to the
archived A1 sources, not D1 source line numbers.

---

# A1 — pre-registration failure-scope audit

11 November 2026. Requested by **Claude, the delegating reviewer agent**;
implemented by Codex, builder. Scope: this folder only. No model calls, pushes,
Git changes, real attestation, clearance, credential access, or sibling writes
were performed. The original freeze has not been pushed and there has been no
real collection. This is a **pre-registration revision A1**, not a post-result
amendment. No study outcomes were inspected or analyzed.

`freeze.json` remains byte-identical, SHA-256
`d085baaf5975bed2eae54853e1f56d63427f4506ec9613c49c69a2aef1ad86ba`.
Create-once `freeze-a1.json` binds that parent, all current inputs and the exact
original bytes of the nine changed frozen files under `deviations/a1/original/`.
Original changed files: od_collect.py, od_validation.py, od_analysis.py,
od_freeze.py, od_provenance.py, tests/test_integrity.py,
tests/test_validation.py, RUN.md and PROJECT_STATE.md. All other original hashes
must remain identical. AST regression also preserves every scientific analysis
function outside raw-evidence replay. Prompts, schema, model pins, settings,
seeds, schedule, scientific scoring, denominators, bootstrap, acceptance criteria,
planning rates, reservations and budgets are unchanged.

Read-only sources: `../receipt-gap/DEVIATIONS.md` D1–D3,
`../three-rules-one-lunch/DEVIATIONS.md` D1–D3b and
`../bridge-or-bus/DEVIATIONS.md` D1–D2, inspected on this date. Their later/live
failures motivate this local pre-registration correction; none of their saved
results or recovery decisions are imported into this experiment.

## Decisions and lessons

1. Every model-content failure is episode-local, including the **first Claude
   call**: missing/nonobject structured_output, invalid field/type/enum, extra
   key, malformed local JSON, duplicate/nonfinite designated Claude payload,
   provider schema rejection and explicit output-length stops. There is no
   repair, fallback to result, resend or replacement. Invalid fleet has factual
   value/work/outage null, operational value 0, optimal 0 and frozen regret;
   it remains in all assigned denominators. This study has one fleet decision,
   so sibling action/report phases and conditional key rules do not apply; an
   extra key here fails its exact one-key schema.
2. Provider metadata is decoded separately from the designated payload in one
   complete lossless JSON parse. Payload duplicates/nonfinite numbers cannot
   discard known usage; duplicate metadata, invalid outer JSON or unverifiable
   paid accounting remain fatal. An actually syntactically incomplete outer
   document cannot establish metadata and is never substring-parsed.
3. Known completed `error_max_structured_output_retries`, with the frozen
   identity/effort/turn/tool/usage gates and exit 0 or 1, is model-content failure.
   Only descriptive string errors from that subtype are allowed. Other nonzero
   exits, execution failures, identity conflicts, unknown usage and overruns are
   fatal. No retry is enabled. Explicit length stops end the episode even with
   two turns; a **successful accepted** two-turn answer still requires tool_use
   and a strict-valid structured_output. Integer one-turn success is retained.
4. Local done != true or missing/invalid eval_count already failed only its
   episode. Three consecutive local episode transport failures now create a
   durable STOP and prevent the fourth dispatch. Success or content failure
   breaks the streak. It persists across invocations and model boundaries and
   is reconstructed at admission after ledger-prefix validation; a crash after
   the third terminal cannot evade it. Pending episodes stay unattempted/null.
   There is no clearance/override API. STOP is never deleted or rewritten;
   any future separately reviewed clearance must bind retained ledger **byte
   lengths and hashes of those prefixes**, permit valid appended tails and
   still replay the complete ledgers. No whole-growing-file clearance is added.
5. Arbitrary provider/harness/identity exceptions formerly became local
   transport failures. Known OS/HTTP transport errors keep that episode-local
   local route; unexpected exceptions retain a harness_error and stop dispatch.
   Paid uncertainty retains its full hold and stops immediately.
6. Already correct: cached input sums uncached + cache creation + cache read
   once (2 + 1600 + 7 = 1609); output includes reasoning once. Unknown fields
   stay null/UNKNOWN. Manifest/layer checks match real pinned Qwen templates
   and Alibaba systems and Llama's absent system. Append-only ledger readers
   verify every preserved prefix and reject rewritten/truncated/torn tails.
   Push evidence uses a complete server push record from
   `GET /repos/Robin84Bran/research/activity`, never commit dates. A1 attestation
   now verifies both freeze blobs, all current committed inputs, HEAD/origin/ref,
   exact retained activity bytes and push-after-A1/before-start chronology.

The superseded first-call content STOP and missing-payload assertions are updated
in the two archived tests. Original fake r1 evidence keeps its historical decoder
and first-call disposition only during explicitly fake offline replay, allowing
all eleven old saved analyses to rebuild without rewriting their bytes. All new
starts bind revision A1 and the active freeze; real legacy starts are forbidden
because none exist. Old-only push receipts cannot admit A1 calls.

## Exhaustive Stop/raise/fatal inventory

The table covers the collector, strict validation, parser/world bounds, ledger,
timer, identity, adapters, freeze/provenance, recovery, independent replay and
archive validation. Each explicit AST raise, non-null fatal assignment,
collector/adapter exception route and durable_stop call has its own row. The
regression test requires exact ordered site coverage; `python3 -B od_audit.py`
regenerates the machine inventory. “Fixed” counts changed existing routing
sites, including unchanged raise text whose admitting condition changed.
“Added split/guard” are new sites, not previously correct original paths.

Audit totals: **158 sites** = 141 raises + 8 fatal assignments + 6 exception routes + 3 durable stops. **9 fixed / 127 already right / 22 added safeguards or routing sites.**

| Site | Function / expression | Final classification | A1 disposition |
|---|---|---|---|
| `od_collect.py:15:raise` | `run_episode: Stop('existing episode cannot be replayed')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:26:exception route` | `run_episode: (OSError, HTTPException)` | Episode local transport / fatal paid unknown usage; retain error, never resend | Already right |
| `od_collect.py:28:exception route` | `run_episode: Exception` | Fatal harness; preserve failure and prevent later dispatch | Fixed |
| `od_collect.py:33:fatal assignment` | `run_episode: fatal = 'unknown frontier usage/cost; full hold retained'` | Fatal independent gate; content cannot override | Already right |
| `od_collect.py:36:fatal assignment` | `run_episode: fatal = 'frontier reservation/accounting overrun'` | Fatal independent gate; content cannot override | Already right |
| `od_collect.py:38:exception route` | `run_episode: (Stop, ReplyFailure, TransportFailure)` | Typed routing: Stop fatal; ReplyFailure episode; TransportFailure local episode | Fixed |
| `od_collect.py:40:fatal assignment` | `run_episode: fatal = fatal or str(exc)` | Fatal independent gate; content cannot override | Fixed |
| `od_collect.py:42:fatal assignment` | `run_episode: fatal = fatal or 'cumulative active time exceeded'` | Fatal independent gate; content cannot override | Already right |
| `od_collect.py:45:durable stop` | `run_episode: durable_stop(base, fatal)` | Fatal or durable pause; create once, no override | Already right |
| `od_collect.py:53:raise` | `check_existing: Stop('unexpected episode path')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:54:raise` | `check_existing: Stop('interrupted/reserved episode; never resend')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:55:raise` | `check_existing: Stop('existing start freeze mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:61:raise` | `collect: Stop('fake must use separate output')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:62:raise` | `collect: Stop('live fixed schedule/output only')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:64:raise` | `collect: Stop('durable STOP: ' + read(base / 'STOP.json')['reason'])` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:70:raise` | `collect: Stop('unresolved reserved episode; no resend')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:75:durable stop` | `collect: durable_stop(base, pause)` | Fatal or durable pause; create once, no override | Added guard |
| `od_collect.py:75:raise` | `collect: Stop(pause)` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_collect.py:82:raise` | `collect: Stop('finish all 3600 local episodes before Claude')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:95:raise` | `collect: Stop('cumulative preflight time exceeded')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:100:raise` | `collect: Stop('runtime/identity drift across resumes')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:104:raise` | `collect: Stop(result['fatal'])` | Fatal harness / integrity / identity / accounting | Already right |
| `od_collect.py:106:raise` | `collect: Stop(state['reason'])` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_collect.py:107:exception route` | `collect: Exception` | Fatal harness; preserve failure and prevent later dispatch | Already right |
| `od_collect.py:108:durable stop` | `collect: durable_stop(base, exc)` | Fatal or durable pause; create once, no override | Already right |
| `od_collect.py:108:raise` | `collect: re-raise` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:27:raise` | `envelope.convert: ValueError('duplicate JSON key: ' + key)` | Episode content for designated payload; fatal paid / local transport for metadata | Added split |
| `od_validation.py:32:raise` | `envelope.convert: ValueError('nonfinite JSON value')` | Episode content for designated payload; fatal paid / local transport for metadata | Added split |
| `od_validation.py:35:raise` | `envelope: ValueError('envelope object required')` | Fatal paid integrity / episode local transport; never extract partial JSON | Added split |
| `od_validation.py:38:raise` | `envelope: ValueError('duplicate envelope key: ' + key)` | Fatal paid integrity / episode local transport; never extract partial JSON | Added split |
| `od_validation.py:71:raise` | `validate: Stop('provider harness failure: ' + raw['harness_error'])` | Fatal harness / integrity / identity / accounting | Added split |
| `od_validation.py:73:raise` | `validate: (Stop if paid else TransportFailure)('transport failure/uncertain start; never resend')` | Fatal paid transport uncertainty / episode local transport | Fixed |
| `od_validation.py:76:raise` | `validate: (Stop if paid else TransportFailure)('unreadable transport envelope')` | Fatal paid transport uncertainty / episode local transport | Already right |
| `od_validation.py:77:raise` | `validate: (Stop if paid else TransportFailure)('envelope object required')` | Fatal paid transport uncertainty / episode local transport | Already right |
| `od_validation.py:79:raise` | `validate: Stop('transport failure/uncertain start; never resend')` | Fatal harness / integrity / identity / accounting | Added split |
| `od_validation.py:82:raise` | `validate: Stop('local model identity mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:83:raise` | `validate: TransportFailure('local done/eval_count missing or incomplete')` | Episode local transport; pause at three consecutive episodes | Already right |
| `od_validation.py:84:raise` | `validate: TransportFailure('local usage UNKNOWN')` | Episode local transport; pause at three consecutive episodes | Already right |
| `od_validation.py:85:raise` | `validate: Stop('unknown local stop reason')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:86:raise` | `validate: Stop('local input/context truncation')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:87:raise` | `validate: Stop('independent input count shortfall')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:89:raise` | `validate: Stop('running identity/context mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:90:raise` | `validate: Stop('local output usage overrun')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:91:raise` | `validate: ReplyFailure('local output-length stop')` | Episode content; frozen technical score, continue | Already right |
| `od_validation.py:93:raise` | `validate: ReplyFailure('invalid local reply')` | Episode content; frozen technical score, continue | Already right |
| `od_validation.py:97:raise` | `validate: Stop('unexpected Claude result/turn envelope')` | Fatal harness / integrity / identity / accounting | Fixed |
| `od_validation.py:98:raise` | `validate: Stop('unknown Claude stop reason')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:99:raise` | `validate: Stop('unexpected second turn')` | Fatal harness / integrity / identity / accounting | Fixed |
| `od_validation.py:101:raise` | `validate: Stop('Claude model identity UNKNOWN/mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:102:raise` | `validate: Stop('Claude identity/effort conflict')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:103:raise` | `validate: Stop('Claude usage/cost UNKNOWN; hold retained')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:105:raise` | `validate: Stop('aggregate/model usage mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:107:raise` | `validate: Stop('unexpected tools/errors')` | Fatal harness / integrity / identity / accounting | Fixed |
| `od_validation.py:109:raise` | `validate: Stop('server tool activity UNKNOWN/nonzero')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:110:raise` | `validate: Stop('Claude reservation overrun')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_validation.py:111:raise` | `validate: ReplyFailure('provider rejected model structured output')` | Episode content; frozen technical score, continue | Added split |
| `od_validation.py:112:raise` | `validate: ReplyFailure('Claude output-length stop')` | Episode content; frozen technical score, continue | Already right |
| `od_validation.py:113:raise` | `validate: ReplyFailure(payload_error)` | Episode content; frozen technical score, continue | Added split |
| `od_validation.py:115:raise` | `validate: (Stop if legacy else ReplyFailure)('structured_output object required; no result fallback')` | Episode content A1; fatal retained r1 fake replay only | Fixed |
| `od_validation.py:117:raise` | `validate: ReplyFailure('invalid Claude structured_output')` | Episode content; frozen technical score, continue | Already right |
| `od_core.py:37:raise` | `strict_load.pairs: ValueError('duplicate key: ' + k)` | Episode local payload; fatal evidence/config; provider envelopes use separate decoder | Already right |
| `od_core.py:40:raise` | `strict_load.bad: ValueError('nonfinite JSON: ' + x)` | Episode local payload; fatal evidence/config; provider envelopes use separate decoder | Already right |
| `od_core.py:45:raise` | `choice: ValueError('exact fleet object required')` | Episode content; exact fleet schema, no conditional action/report schema in this study | Already right |
| `od_core.py:47:raise` | `choice: ValueError('fleet integer 1/6/24 or null required')` | Episode content; exact fleet schema, no conditional action/report schema in this study | Already right |
| `od_core.py:52:raise` | `delivered: ValueError('world bounds')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_core.py:58:raise` | `oracle: ValueError('oracle bounds')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:21:raise` | `save_bytes: Stop('symlink output')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:30:raise` | `lock: Stop('symlink lock')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:33:raise` | `lock: Stop('concurrent collector rejected')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:45:raise` | `Log.__init__: Stop('symlink ledger')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:49:raise` | `Log.__init__: Stop('torn log')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:51:raise` | `Log.__init__: Stop('log chain changed')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:53:raise` | `Log.__init__: Stop('log prefix changed')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:56:raise` | `Log.__init__: Stop('log truncated or extra prefix checkpoint')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:60:raise` | `Log.append: Stop('log changed since admission')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:80:raise` | `Ledger.apply: Stop('rolling reservation/cap/duplicate gate')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:84:raise` | `Ledger.apply: Stop('invalid settlement')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:86:raise` | `Ledger.apply: Stop('unknown ledger event')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:95:raise` | `ActiveTime.__init__: Stop('invalid timer amount')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:97:raise` | `ActiveTime.__init__: Stop('timer admission exceeded frozen cap')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:102:raise` | `ActiveTime.__init__: Stop('invalid timer log')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_io.py:108:raise` | `ActiveTime.begin: Stop('cumulative active time limit')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:8:raise` | `identity: Stop('identity inventory mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:11:raise` | `identity: Stop('manifest pin mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:15:raise` | `identity: Stop('missing/extra pinned layer')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:18:raise` | `identity: Stop('pinned layer mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:19:raise` | `identity: Stop('pinned metadata byte mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:20:raise` | `identity: Stop('invented default system')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:25:raise` | `check_identity: Stop('pinned template/default system mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:32:raise` | `verify_preflight: Stop('CLI binary/version drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_identity.py:35:raise` | `verify_preflight: Stop('local digest mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_transport.py:32:exception route` | `Local.generate: Exception` | Fatal identity: failed ps lookup saved, then running metadata rejected | Already right |
| `od_transport.py:39:raise` | `Claude.preflight: Stop('CLI path drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_transport.py:45:raise` | `Claude.generate: Stop('unfrozen CLI request')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_transport.py:49:exception route` | `Claude.generate: subprocess.TimeoutExpired` | Fatal paid transport uncertainty; preserve partial stdout/stderr | Already right |
| `od_freeze.py:29:raise` | `verify: Stop('symlink freeze')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:33:raise` | `verify: Stop('A1 parent freeze mismatch')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:35:raise` | `verify: Stop('A1 amendment scope mismatch')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:36:raise` | `verify: Stop('A1 original metadata drift')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:40:raise` | `verify: Stop('A1 original archive mismatch: ' + name)` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:41:raise` | `verify: Stop('A1 changed frozen science/evidence: ' + name)` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:42:raise` | `verify: Stop('A1 must follow parent freeze')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:43:raise` | `verify: Stop('freeze input set drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:46:raise` | `verify: Stop('frozen input changed: ' + name)` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:47:raise` | `verify: Stop('schedule drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:49:raise` | `verify: Stop('frozen reservation mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:57:raise` | `freeze_a1: Stop('A1 revision must precede attestation/collection')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:62:raise` | `freeze_a1: Stop('missing exact A1 original: ' + name)` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:63:raise` | `freeze_a1: Stop('A1 forbidden original change: ' + name)` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_freeze.py:71:raise` | `freeze: Stop('freeze must precede collection')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:83:raise` | `attest: Stop('push predates freeze')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:84:raise` | `attest: Stop('invalid repo path')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:86:raise` | `attest: Stop('clone HEAD mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:88:raise` | `attest: Stop('repository origin mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:93:raise` | `attest: Stop('committed package mismatch: ' + name)` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:94:raise` | `attest: Stop('remote ref mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_freeze.py:96:raise` | `attest: Stop('attestation must precede starts')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:15:raise` | `timestamp: Stop('invalid server timestamp')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:16:raise` | `timestamp: Stop('timezone required')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:21:raise` | `push_record: Stop('invalid activity/commit')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:22:raise` | `push_record: Stop('GitHub activity push record required')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:24:raise` | `push_record: Stop('invalid push ref/id/time')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:32:raise` | `receipt_gate: Stop('push receipt binding mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_provenance.py:33:raise` | `receipt_gate: Stop('push must follow freeze')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_recovery.py:8:raise` | `record_transport: Stop('dispatch continued after three transport failures')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_analysis.py:25:raise` | `replay: Stop('unexpected paid ledger identity')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:26:raise` | `replay: Stop('reservation differs from frozen request')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:29:raise` | `replay: Stop('ledger/raw settlement disagreement')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:32:raise` | `replay: Stop('unplanned episode evidence')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:37:raise` | `replay: Stop('symlink evidence')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:40:raise` | `replay: Stop('start identity mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:42:raise` | `replay: Stop('attempt lacks complete timer evidence')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:43:raise` | `replay: Stop('fake evidence forbidden')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:45:raise` | `replay: Stop('start freeze mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:48:raise` | `replay: Stop('start predates push')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:50:raise` | `replay: Stop('realized request drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:57:raise` | `replay: Stop('paid start has no reservation')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:59:fatal assignment` | `replay: fatal = 'unknown frontier usage/cost; full hold retained'` | Fatal independent gate; content cannot override | Already right |
| `od_analysis.py:60:raise` | `replay: Stop('unknown cost was released')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:62:raise` | `replay: Stop('known usage unsettled')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:63:fatal assignment` | `replay: fatal = 'frontier reservation/accounting overrun'` | Fatal independent gate; content cannot override | Already right |
| `od_analysis.py:67:fatal assignment` | `replay: fatal = fatal or str(exc)` | Fatal independent gate; content cannot override | Fixed |
| `od_analysis.py:68:fatal assignment` | `replay: fatal = fatal or 'cumulative active time exceeded'` | Fatal independent gate; content cannot override | Already right |
| `od_analysis.py:71:raise` | `replay: Stop('terminal/raw replay disagreement: ' + ident)` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:72:raise` | `replay: Stop('fatal evidence lacks STOP')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:73:raise` | `replay: Stop('finish predates start')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:77:raise` | `replay: Stop('start precedes reservation')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:78:raise` | `replay: Stop('orphan reservation/interrupted start')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:84:raise` | `replay: Stop('attempted schedule is not a prefix')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:91:raise` | `replay: Stop('dispatch continued after fatal episode')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:97:raise` | `replay: Stop('missing preflight evidence')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:100:raise` | `replay: Stop('retained runtime drift')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_analysis.py:105:raise` | `replay: Stop('transport threshold lacks durable STOP')` | Fatal harness / integrity / identity / accounting | Added guard |
| `od_analysis.py:106:raise` | `replay: Stop('frontier evidence precedes complete locals')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_archive.py:9:raise` | `archive: Stop('archive exists')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_archive.py:26:raise` | `verify_archive: Stop('archive set mismatch')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_archive.py:28:raise` | `verify_archive: Stop('unsafe archive')` | Fatal harness / integrity / identity / accounting | Already right |
| `od_archive.py:29:raise` | `verify_archive: Stop('archive content mismatch')` | Fatal harness / integrity / identity / accounting | Already right |

Implicit failures were also traced: file I/O/create-once conflicts, missing keys,
wrong metadata container types, serialization errors, hashing/subprocess failures
and unexpected simulator errors are harness/integrity failures and stop; they
are never repaired into model content. The collector saves dispatch errors and
raw bytes before classification; a crash before complete terminal/timer evidence
is an interrupted non-retriable start. Exceptions during preflight are fatal;
there is no preflight retry. `usage`/`accounting` return None on missing/unusable
metadata: local validation yields episode transport failure, paid reservation
retains its hold and sets fatal. Metadata gates precede model-content rejection.
Unknown local stop reasons, context/input loss and output usage above 192 remain
fatal; done_reason length or exactly 192 is an episode content failure. Timer
and spend overrun settle known amounts fully and stop. Raw ps lookup failures
are retained and fail the running-identity gate. SIGINT/process death cannot
resend a saved start. CLI argument parser errors occur before dispatch.

## Verification and handoff

`evidence/a1-tests.json` and `evidence/a1-tests.txt` retain the offline test run;
`evidence/a1-rebuild.json` records byte-identical reconstruction of all eleven
original fake analyses. The tests cover content/transport/fatal precedence,
first-call continuation, full settlement and unknown holds, no resend, crash
reconstruction of the three-failure pause, streak resets, pinned identities,
ledger prefix growth/rewrite/truncation, strict Claude turns and cache classes,
complete activity receipt binding and amendment scope/parent/create-once checks.
RUN.md gives the current verify/attest/collect commands. Claude owns subsequent
review, push, genuine server activity capture, attestation and collection.
