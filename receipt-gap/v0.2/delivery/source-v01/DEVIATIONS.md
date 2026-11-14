# D1 — server push provenance only

11 November 2026, before inference. Decision: **AGREED, Claude/Codex**, under
[`semi_autonomous.md`](../semi_autonomous.md). Codex implements Claude's requested
provenance amendment; Claude owns the subsequent push and collection.

The original r2 freeze is retained byte-for-byte as `freeze.json`, SHA-256
`289eaa2a465b82e889ee5e36406621ff336975cf5e14aa2f9db40c86b0a76269`.
Claude pushed it to `Robin84Bran/research` main in commit
`059a0258b86359d2564fd1e09bf4a4867b23353b`. The private repository's `/events`
response did not provide a matching PushEvent. The saved `/activity` record does:
activity id `49834798845`, `activity_type: push`, `ref: refs/heads/main`,
`after: 059a0258b86359d2564fd1e09bf4a4867b23353b`, server timestamp
`2026-11-11T09:13:51Z`. Codex inspected the raw record supplied in
`rg-activity-059a025.json` in the orchestration scratch folder. This record
documents the original push; it cannot attest the amended package.

`attest` now accepts either a full GitHub PushEvent, as before, or a full record
from `/repos/Robin84Bran/research/activity` with `activity_type == "push"`, a
branch `ref`, `after == commit`, and a timezone-aware past `timestamp`. Both forms
must retain their server id. Neither author/committer dates nor a fabricated
record are evidence. Activity records do not embed the repository name, so the
separate clone's origin must identify this exact GitHub repository. Both forms
also require the clone HEAD, committed original and active freeze blobs, and
current remote ref to match. The exact source bytes and their SHA-256 are retained
with the create-once receipt. The collector validates either retained record and
still requires the push to precede every call.

`--clone-root` selects the research clone for read-only Git checks; `--repo-path`
selects the project directory within that repository. `--root` selects the
RobinOS2 project that receives `collection/push.json` and `push-event.json`.
The clone receives no attestation writes. Collection runs from that same
RobinOS2 project so the receipt and subsequent starts share one collection root.

`freeze-d1.json` is a new, create-once manifest binding the original freeze hash
and all current inputs. Verification selects D1 when present and checks its
parent and allowed changes. Original-input changes are confined to provenance
code (`rg_freeze.py`, `rg_collect.py`'s `push_gate`), its existing positive test's
Git mock, `RUN.md`, and `PROJECT_STATE.md`; additions are this document and
`tests/test_freeze_d1.py`. All other original hashes must remain identical.
The protocol, scientific world, prompts, schemas, models, settings, seeds,
schedule, analysis, criteria, budget, ledger, timers and transport are unchanged.
No model call has occurred; prior model spend remains zero. No model call,
network request, push, collection or Git mutation is part of this D1 build.

Offline tests cover both server shapes, missing/mismatched fields, timestamps,
separate clone/output roots, exact raw retention, create-once writes, HEAD/origin/
freeze/ref mismatches, parent binding, scientific-input preservation, receipt
tampering, and push-before-call ordering. Claude must push the entire D1 package
again and obtain the matching fresh server record before attestation or inference.

# D2 — structured-output envelope only; pre-analysis

11 November 2026. **AGREED, Claude/Codex**, under
[`semi_autonomous.md`](../semi_autonomous.md). Claude's delegated request identifies
the CLI schema-tool envelope mismatch and asks Codex to implement this amendment.
This is after collection began, before study-wide analysis; it is not a new
pre-inference registration. No model call, push, Git change, credential access or
real attestation is part of this build.

Exposure: the local cohort has 1,800 terminal records; its outcomes were not
analyzed for D2. The first frontier episode is already terminal. Codex inspected
its raw/request/start/parsed/terminal bytes, STOP, ledger, timers and push receipt.
The saved envelope is `type: result`, `subtype: success`, `is_error: false`,
`num_turns: 2`, `stop_reason: tool_use`, sole model identity `claude-opus-5-5`,
and `structured_output: {"op":"send","job":1,"key":null}`. That object passes
the unchanged strict validator. The CLI's schema-output internal tool accounts
for the additional envelope turn. D1 rejected the envelope solely because it
required one turn; no simulated send was applied. The `result` string is not
used. The frozen request still uses `--max-turns 1` and all original controls.

Accept integer `num_turns == 2` only together with `stop_reason == "tool_use"`
and a present object `structured_output` that passes the frozen strict phase and
toolkit validator. Integer `num_turns == 1` stays accepted subject to all existing
gates. Other counts/types, two turns with another stop reason, missing/string/
invalid payloads, identity/effort conflicts, bad success envelope, truncation,
usage gaps and overruns remain fatal for frontier collection. No parser repair,
`result` fallback, retries, extra model turns or scientific relaxation is added.

Accounting already sums the disjoint `input_tokens`, `cache_creation_input_tokens`
and `cache_read_input_tokens` fields. Here 2 + 1,600 + 0 = **1,602 input**, with
199 output including 105 thinking tokens; neither cache subcategories nor thinking
are counted twice. The USD4/20 basis gives USD0.010388; the larger reported
USD0.016788 is already settled and retained. The original USD0.262912 episode
hold minus the USD0.022016 settled call subhold leaves USD0.240896 outstanding.
No hold is released in this amendment. Charged frontier time remains
0.237892084 + 3.845703041 = 4.083595125 seconds. Missing cache classes remain UNKNOWN.

**Disposition: retain the terminal harness action technical failure.** Protocol
§4 ends invalid actions without effects or replacement generation; §8 says
"Resume only definitely unstarted calls" and "Preserve all failed evidence."
The frozen RUN.md recovery contract additionally says "Terminal episodes are
skipped" and "an interrupted started episode is never rerun." The saved payload
is valid, and this is a harness bug, not a model-content failure. Nevertheless,
that episode already has an immutable failed terminal record, no executed event,
and no report. Continuing it would supersede that terminal disposition, beyond
this envelope-only correction. We take the conservative frozen recovery path:
no saved-byte effect, continuation or resend. Keep the original reason and report
the harness attribution separately. The unchanged scorer assigns D*=1, S*=0 and
J=0; its actual executed effects remain zero, distinct from benchmark penalties.
No replacement episode or seed is added; only the remaining 59 unstarted frontier
episodes can resume, in frozen order, after D2 is pushed and attested.

`freeze.json` remains SHA-256
`289eaa2a465b82e889ee5e36406621ff336975cf5e14aa2f9db40c86b0a76269`;
`freeze-d1.json` remains
`06d0707a7819f44fc1c9ec28cbb6beeb23230b3b2187b7986ae24093078b76cc`.
Create-once `freeze-d2.json` binds both parents and all amended inputs. The only
D1 input changes are collector envelope/recovery/provenance gates,
`rg_freeze.py`, `rg_analysis.py`'s provenance/envelope verification, this document
and `PROJECT_STATE.md`. Additions are `RUN-d2.md`, `tests/test_freeze_d2.py`,
`evidence/d2-baseline.json`, and the explicit D1 manifest binding. Analysis's
existing scientific functions and accounting remain unchanged; its earlier
single-original-freeze check also needed to recognize actual D1 call provenance.
The two-turn replay allowance is confined to D2 starts (or labelled fake tests).

The baseline binds all stopped-episode files, original STOP and receipts, and
ledger/timer prefixes, plus an aggregate checksum of all 44,890 collection files.
New D2 receipts use separate create-once paths. The original STOP is acknowledged
only through this frozen evidence binding; a future STOP-d2 always blocks.
Original charges/holds/timers carry forward. No pre-existing evidence is changed.
Tests cover strict positive/negative envelopes, both phases, cache accounting,
real saved-byte validation and retained failure scoring, immutable parent/scope
checks, separate receipts, before/after amendment provenance, narrow STOP recovery,
continued terminal rejection, persistent charges and future-stop blocking.
See RUN-d2.md for the exact attest and Claude-collect commands.

Verification before sealing: 108 offline tests pass; the independent code-only
package copy passes with one expected saved-data skip. AST comparison preserves
all scientific scoring/reconciliation functions and the original usage/cost
functions. Every one of the 44,890 pre-existing collection files is byte-identical
to the saved aggregate baseline. Independent saved-cost reconciliation confirms
16,788 settled and 240,896 outstanding microdollars with no unknown-usage calls.

# D3 — episode-local model technical failures; pre-analysis

11 November 2026. Claude, the delegating reviewer agent, requested this
harness-only correction. This is after saved-response exposure, before study-wide
analysis. Builder work stays in this folder; no model calls, network requests,
pushes, Git operations or real attestations were performed. Earlier D2 wording
that made invalid frontier payloads and model length stops fatal is superseded
below. The scientific contract and scoring remain frozen.

**Cause and correction.** `run_episode` previously set `fatal` for every paid
actor's decoder exception. Thus Claude's strict JSON object
`{"op":"send","job":4,"key":"job4"}` in the check toolkit was correctly rejected
by the conditional key rule, but incorrectly halted the cohort. `ModelOutputError`
now identifies only model-content failures. Wrong fields/types/enums, boolean job
IDs, toolkit/operation restrictions, finish fields, key nullability/ASCII/pattern/
length, malformed report booleans, missing/nonobject structured output, strict
payload JSON violations, and explicit model output-length stops end their episode
without effect, repair, replacement generation or report after an invalid action.
Bad reports preserve the valid action trajectory and its effects. Both local and
frontier cohorts then proceed in the frozen order.

Provider `error_max_structured_output_retries` is also a content failure when its
completed result has verified identity, effort, turn metadata, known usage and
in-bound accounting (including its known terminal exit code 1). This existing CLI
subtype appears in frozen `evidence/cli-contract.json`; it does not enable a retry.
Explicit local `done_reason: length` and frontier `stop_reason: max_tokens/length`
are technical failures after the other gates pass. Two-turn length stops end the
episode; two-turn *accepted* payloads still require `tool_use`. Other execution,
turn-count, budget, transport and malformed-envelope failures stay fatal. No
output, turn, context, token, budget or time allowance was increased.

A lossless object-pairs decoder checks metadata independently from the designated
`structured_output` field. Duplicate keys/nonfinite numbers in that payload are
rejected without losing valid usage settlement; metadata duplicates or invalid
outer JSON remain fatal integrity/accounting failures. No JSON substring, `result`
fallback, coercion or repair is used. Local payload strings retain the existing
strict JSON parser. Valid raw whitespace remains allowed, saved and canonicalized
for subsequent visible history; raw byte size alone is not a new rejection rule.
Accounting uncertainty, measured overruns, identity/effort/context conflicts and
transport uncertainty take precedence even when the payload is also invalid.

**Stopped-episode disposition.** Preserve every byte of
`collection/episodes/claude-s05-payment-r50-check/` and `STOP-d2.json`.
Call index 8 is attempted decision **9**; the ledger contains **8 valid executed
decisions**, counts `[1,1,1,0]`, no ninth event and no report. Retain its model action
technical failure (`error: key`), with actual D=0, S=0, D*=1, S*=0 and J=0. Do not
rerun, continue, apply the invalid send, request a report, replace the episode or
alter the existing terminal record. The original D1 harness failure also remains
terminal. Eight Claude episodes and 1,800 local episodes are already terminal;
only the **52 definitely unstarted Claude episodes** remain eligible.

`evidence/d3-baseline.json` binds the stopped episode, both STOP files, both
receipt/event pairs, and append-only ledger/timer prefixes. Its aggregate binds
all **45,259** existing collection files, excluding the mutable lock file, SHA-256
`1fc10743bdc12cc4e2ed98f64eed90396e06ba69e231b9494911f76ce899b7c6`.
The historical holds are retained: 994,339 microdollars settled, 293,888 outstanding
(240,896 from D1 and 52,992 from the D2 key stop), zero unknown-usage calls;
266.65199604199995 charged frontier seconds. Actual cash billing remains UNKNOWN.
No ledger or timer entry was appended by this builder. Newly completed, fully
accounted model failures release their unused future-call holds normally.

**Freeze and recovery.** `freeze-d3.json` is create-once and binds the unchanged
original (`289eaa2a465b82e889ee5e36406621ff336975cf5e14aa2f9db40c86b0a76269`),
D1 (`06d0707a7819f44fc1c9ec28cbb6beeb23230b3b2187b7986ae24093078b76cc`) and
D2 (`0c39d5a478880aa4037b0d5bfa55bc9c120514ca7994e3d43e08e84a5da4c197`)
freezes. Allowed edits are collector error/recovery/provenance gates, core error
typing and lossless envelope validation, freeze plumbing, analysis provenance and
raw-usage decoding, the superseded assertions in two existing tests, this document
and project state. Added inputs are the D3 runbook, tests, baseline and explicit
D2 manifest binding. World transitions, draws, prompts, schemas, settings, models,
schedule, scientific scoring, cost formulas, denominators and bootstrap criteria
are unchanged. Independent replay uses the shared strict envelope parser only to
preserve usable metadata on rejected payloads; it still reconstructs world effects
independently. No study-wide outcome analysis was run.

D3 uses new `push-d3.json` / `push-event-d3.json` receipts and requires a fresh push
attestation. Historical D1/D2 starts must precede their respective successor's
creation and follow their own pushes. The exact bound old stops are acknowledged
only for frontier recovery. Missing/changed baseline evidence or a continued
terminal episode blocks dispatch; there is no arbitrary STOP override. A new
`STOP-d3.json` remains fatal. See `RUN-d3.md` for the concrete handoff.

## D3 exhaustive Stop/raise audit

Each row below identifies one explicit AST `raise` site in the final collector or
core. **Episode content** means the phase-specific frozen technical failure;
**Fatal** means cohort dispatch cannot proceed. Contextual parser sites list both
routes explicitly: a rejected model payload is episode-local, while malformed
provider metadata, configuration or retained evidence is an integrity failure.
The regression suite checks that this inventory exactly covers all raise sites.

| Raise site | Function and exception | Class | Reason / route |
|---|---|---|---|
| `rg_collect.py:59` | `lock: Stop('concurrent collector admission rejected')` | Fatal harness/concurrency | Another collector already holds the lock. |
| `rg_collect.py:83` | `Ledger.apply: Stop('reservation cap or duplicate episode')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:88` | `Ledger.apply: Stop('invalid settlement')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:94` | `Ledger.apply: Stop('invalid release')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:98` | `Ledger.apply: Stop('unknown ledger operation')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:114` | `ActiveTime.__init__: Stop('duplicate timer')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:119` | `ActiveTime.__init__: Stop('invalid timer ledger')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:125` | `ActiveTime.begin: Stop('cumulative active-time cap')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:172` | `Local.preflight: Stop('local identity/template preflight failed')` | Fatal identity/harness | Pinned runtime identity, template, binary or schema capability mismatch. |
| `rg_collect.py:195` | `Claude.preflight: Stop('CLI binary changed since offline verification')` | Fatal identity/harness | Pinned runtime identity, template, binary or schema capability mismatch. |
| `rg_collect.py:198` | `Claude.preflight: Stop('schema flag disappeared')` | Fatal identity/harness | Pinned runtime identity, template, binary or schema capability mismatch. |
| `rg_collect.py:234` | `cost_micro: Stop('invalid reported API-equivalent cost')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:236` | `cost_micro: Stop('invalid reported API-equivalent cost')` | Fatal accounting/resource | Persistent money/time reservation, settlement, cap or ledger integrity. |
| `rg_collect.py:245` | `provider_envelope: Stop(str(exc))` | Fatal integrity | Cannot validate outer provider metadata; payload errors are returned separately. |
| `rg_collect.py:250` | `decode: Stop('transport failure or uncertain start')` | Fatal transport uncertainty | Uncertain/error start; no resend. Known completed schema rejection is separately classified. |
| `rg_collect.py:255` | `decode: Stop('transport failure or uncertain start')` | Fatal transport uncertainty | Uncertain/error start; no resend. Known completed schema rejection is separately classified. |
| `rg_collect.py:259` | `decode: Stop('unverified frontier identity')` | Fatal identity | Returned model, effort or running context conflicts with frozen identity. |
| `rg_collect.py:261` | `decode: Stop('conflicting frontier effort')` | Fatal identity | Returned model, effort or running context conflicts with frozen identity. |
| `rg_collect.py:267` | `decode: Stop('frontier envelope, turn limit or truncation mismatch')` | Fatal harness/integrity | Unrecognized result, execution failure, invalid turn metadata or stop condition; explicit model length has its own episode route. |
| `rg_collect.py:269` | `decode: Stop('unknown frontier usage; hold retained')` | Fatal accounting/resource | Usage unavailable, context exhausted or reservation exceeded. |
| `rg_collect.py:271` | `decode: Stop('frontier reservation overrun')` | Fatal accounting/resource | Usage unavailable, context exhausted or reservation exceeded. |
| `rg_collect.py:273` | `decode: ModelOutputError('provider rejected model structured output')` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:275` | `decode: ModelOutputError('truncated model output')` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:277` | `decode: ModelOutputError(payload_error)` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:280` | `decode: ModelOutputError('structured_output must be an object; no fallback')` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:283` | `decode: Stop('local identity, truncation or stop mismatch')` | Fatal identity | Returned model, effort or running context conflicts with frozen identity. |
| `rg_collect.py:285` | `decode: Stop('local context usage unknown or exhausted')` | Fatal accounting/resource | Usage unavailable, context exhausted or reservation exceeded. |
| `rg_collect.py:288` | `decode: Stop('returned running identity/context mismatch')` | Fatal identity | Returned model, effort or running context conflicts with frozen identity. |
| `rg_collect.py:290` | `decode: ModelOutputError('truncated model output')` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:294` | `decode: ModelOutputError(str(exc))` | Episode content | Invalid designated payload, schema rejection or explicit output truncation; all independent gates must pass. |
| `rg_collect.py:302` | `checked_receipt: Stop('push attestation mismatch')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:305` | `checked_receipt: Stop('invalid server push time')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:310` | `checked_receipt: Stop('retained server event differs from attestation')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:332` | `push_gate: Stop('call freeze outside attested amendment lineage')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:334` | `push_gate: Stop('push must precede every call')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:344` | `d2_resume_gate: Stop('D2 baseline symlink: ' + name)` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:349` | `d2_resume_gate: Stop('D2 retained evidence changed: ' + name)` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:353` | `d2_resume_gate: Stop('D2 terminal episode must not be continued')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:363` | `d3_resume_gate: Stop('D3 baseline symlink: ' + name)` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:368` | `d3_resume_gate: Stop('D3 retained evidence changed: ' + name)` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:372` | `d3_resume_gate: Stop('D3 terminal episode must not be continued')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:378` | `d3_resume_gate: Stop('D3 stopped-episode disposition mismatch')` | Fatal integrity/provenance | Push lineage, time, baseline bytes, terminal disposition or no-continuation invariant. |
| `rg_collect.py:390` | `run_episode: Stop('episode already terminal')` | Fatal integrity/recovery | Terminal or previously started episode cannot be retried. |
| `rg_collect.py:392` | `run_episode: Stop('started episode cannot be retried')` | Fatal integrity/recovery | Terminal or previously started episode cannot be retried. |
| `rg_collect.py:477` | `collect: Stop('durable STOP: ' + read(base / 'STOP.json')['reason'])` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:479` | `collect: Stop('durable amendment STOP: ' + read(base / stop_name)['reason'])` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:486` | `collect: Stop('local cohort must finish or be explicitly accounted before frontier')` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:491` | `collect: Stop('explicit verified Claude binary required')` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:508` | `collect: Stop('uncertain started episode')` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:512` | `collect: re-raise` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_collect.py:514` | `collect: Stop(read(base / stop_name)['reason'])` | Fatal admission/recovery | Durable stop, incomplete prerequisite, missing verified binary, uncertain start or propagated fatal stop. |
| `rg_core.py:35` | `strict_load.pairs: ValueError('duplicate JSON key')` | Episode content / Fatal integrity | Local payload parser → ModelOutputError; evidence/configuration parser → fatal. |
| `rg_core.py:39` | `strict_load.invalid: ValueError('nonfinite JSON constant: ' + value)` | Episode content / Fatal integrity | Local payload parser → ModelOutputError; evidence/configuration parser → fatal. |
| `rg_core.py:43` | `strict_load.finite_float: ValueError('nonfinite JSON number')` | Episode content / Fatal integrity | Local payload parser → ModelOutputError; evidence/configuration parser → fatal. |
| `rg_core.py:46` | `strict_load: ValueError('text required')` | Episode content / Fatal integrity | Local payload parser → ModelOutputError; evidence/configuration parser → fatal. |
| `rg_core.py:65` | `strict_envelope.convert: ValueError('duplicate JSON key')` | Episode content / Fatal integrity | Designated payload conversion → ModelOutputError; metadata conversion → fatal. |
| `rg_core.py:71` | `strict_envelope.convert: ValueError('nonfinite JSON number')` | Episode content / Fatal integrity | Designated payload conversion → ModelOutputError; metadata conversion → fatal. |
| `rg_core.py:77` | `strict_envelope: ValueError('provider envelope must be an object')` | Fatal integrity | Outer envelope unparseable, nonobject, duplicate field or unverifiable metadata. |
| `rg_core.py:81` | `strict_envelope: ValueError('duplicate envelope key')` | Fatal integrity | Outer envelope unparseable, nonobject, duplicate field or unverifiable metadata. |
| `rg_core.py:86` | `strict_envelope: re-raise` | Episode content / Fatal integrity | Designated payload conversion → ModelOutputError; metadata conversion → fatal. |
| `rg_core.py:90` | `strict_envelope: ValueError('invalid provider envelope: ' + str(exc))` | Fatal integrity | Outer envelope unparseable, nonobject, duplicate field or unverifiable metadata. |
| `rg_core.py:95` | `action: ValueError('toolkit')` | Fatal harness | Invalid configured toolkit or dispatch past the simulator horizon. |
| `rg_core.py:97` | `action: ModelOutputError('action fields')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:100` | `action: ModelOutputError('op')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:103` | `action: ModelOutputError('finish fields')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:106` | `action: ModelOutputError('job')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:108` | `action: ModelOutputError('status unavailable or key')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:110` | `action: ModelOutputError('key')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:116` | `report: ModelOutputError('report fields')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:118` | `report: ModelOutputError('report boolean/null required')` | Episode content | Strict frozen action/report rejection; no effect or repair. |
| `rg_core.py:140` | `World.step: ValueError('action horizon ended')` | Fatal harness | Invalid configured toolkit or dispatch past the simulator horizon. |

Audit total: **71 explicit raise sites** (51 collector, 20 core).

Additional non-raise stop paths were inspected: `run_episode` marks missing paid
usage and measured cost/token/exposure overruns fatal before content decoding,
then writes the durable stop; neither can be downgraded by `ModelOutputError`.
Provider generation exceptions/timeouts preserve raw/partial evidence and become
fatal uncertain transport. Local running-metadata retrieval failures are saved
and fail the running-identity check. `collect` aborts on the active STOP and never
starts the next episode. Filesystem, serialization, subprocess, network, missing
keys/types and unexpected simulator/accounting errors are harness/integrity
failures: they propagate or are wrapped as fatal, never repaired or treated as
model content. A crash with a saved start remains non-retriable and unknown until
its saved evidence establishes truth. No model payload reaches `World.step`
before strict validation. No remaining model-content rejection is deliberately
routed to a collection-wide STOP; independent fatal evidence still takes precedence.

D3 verification before sealing: **120 offline tests pass**, including cohort
continuation after content failures in both phases and both transports, schema
and conditional key legality, payload duplicates/nonfinite values, length stops,
no repair/report after invalid actions, retained trajectory/report scoring,
fully accounted hold release, fatal identity/usage/context/transport gates,
precise old-STOP recovery, no terminal continuation, D3 push lineage and parent
binding. An independent code-only package passes the same 120 tests with two
expected saved-data skips. The AST audit test covers all 71 raise sites. Removing
only the new core exception class/envelope helper and reversing the documented
validator exception/check placement reproduces the exact D2 core SHA-256
`0c1b42a8757a657efe6afdcdc41ac0e957c9471613f7399096575d3ad6988413`.
All 45,259 pre-existing collection files match the aggregate baseline; both old
STOPs, all episode records and ledger/timer bytes are unchanged. Targeted stopped
episode scoring and independent accounting reconciliation match the baseline.
