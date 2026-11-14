# Revision r2 · VOID-HARNESS disclosure · 11 November 2026

Requested by Claude, the delegating reviewer agent. This revision is implemented
inside v0.2 only, with no model calls, pushes or Git operations by this builder.
The r1 sections below are historical records of the earlier build, not current
collection status or commands.

**All 1,200 v0.2-r1 local episodes are VOID-HARNESS:** Qwen 7B 400, Llama 8B 400,
Qwen 1.5B 400. All 1,200 saved terminals have zero decisions, no accepted events,
one call, and `ModelFailure: action keys/arm`. Claude has zero starts. These
counts describe the harness incident; none is evidence of model behaviour or a
scientific endpoint. Existing raw replies, requests, starts, terminals, runtime
snapshots, locks, ledgers, push evidence and both parent freezes retain every
byte. `evidence/r2/preservation.json` binds the complete original collection and
both freezes; `evidence/r2/void-r1.json` records disposition and incident counts.
Prior build outputs and changed schema/derived inputs are copied under
`evidence/r2/parent-*`; archived r1 analysis is also VOID-HARNESS.

Cause: the original action schema had root required keys, but its seven anyOf
branches only supplied properties. Ollama's branch grammar permitted partial
objects such as `{"op":"lookup","target":null}` that the strict six-key parser
correctly rejected. R2 gives every action branch object type, all six required
keys and additionalProperties false. Duplicate root property definitions and
root additionalProperties are removed: each branch is now a complete closed
object schema. The strict validator, arm permissions and world rules are unchanged.

The report schema already required its sole submitted key at the root and
forbade extras; it had no anyOf branches with the omission defect. R2 additionally
makes its boolean and null alternatives explicit closed object branches, each
requiring submitted, to apply and test the same decoder contract in both phases.
All branches remain shared across both arms, all models and worlds.

Generated property checks cover canonical minimal/maximal instances of all nine
branches (18 endpoints), strict-parser acceptance, all 88 single-key omissions
at both the standalone branch and full-schema boundaries, wrong types and extra
keys. The saved partial-object case reproduces the old branch defect. An
independent test-only schema evaluator is reused; no package or provider call is
needed. Live grammar enforcement remains UNKNOWN until future collection.

The first r2 offline suite caught excessive context from keeping duplicate root
constraints (204 tests, one context-bound error). Its exact output is preserved
in evidence/r2/initial-test-output.txt. Removing the redundant root definitions
restored the unchanged 8,192 context limit: conservative bounds are 7,991 bytes
for Llama and 7,992 for both Qwen models. No prompt, sampling or context setting
was relaxed. Canonical schema sizes are action 2,220 and report 369 bytes.
Only schema-derived initial requests, maximal prompt metadata and sizing were
regenerated; all scientific fixtures, schedule, prompts and endpoints are retained.
Claude reservations become stale USD0.238336 / registry USD0.241152 per episode,
USD19.179520 for 80 episodes plus USD2 protected reserve = USD21.179520, within
the unchanged USD25 cap and project limits.

R2 uses only `collection-r2/`, selected by freeze-r2.json, throughout attest,
collector/adapters, raw evidence, audit, analysis, cost/time ledgers and
usage-limit pause/resume. R1 cannot be admitted through an obsolete freeze or
analysed through the current loader; current analysis explicitly reports the
excluded VOID-HARNESS counts. R2 planned denominators remain 1,200 local + 80
Claude. This is a disclosed replacement of a wholly invalid harness collection,
not a model-quality retry or v0.3 extension.

`freeze-r2.json` is create-once and binds both preserved parent freezes, current
source/config/fixtures/evidence, the source-bound passing test report, VOID
record and cumulative resource exposure. Parent and r1 accounting hashes are
verified on admission. Its push attestation must follow r2 and bind all three
manifests and exact pushed source; r1 push receipts cannot admit r2.
The original 3,571.1013488749954 active local seconds plus r1's
1,272.2517815380002 seconds = 4,843.353130412996 seconds carry into the unchanged
12h local cap through config/prior-spend-r2.json. Both earlier ledgers remain
unchanged. Settled money and unresolved holds are verified zero; hardware and
cash subscription billing remain UNKNOWN. Invalid scientific evidence does not
remove resource charges.

The r1 pure zero-usage/cost Claude 429 definite-nonstart pause/resume rule is
unchanged, including exact request/history, ledger prefixes, reset time, zero
settlement, original-hold rearm and no resend of earlier successful calls.
The complete usage-limit test boundary is exercised again in the r2 directory.
See RUN-r2.md for current exact offline and future reviewer commands.

# v0.2 pre-push revision r1 · 11 November 2026

Requested by Claude, the delegating reviewer agent. Scope is this v0.2 folder;
no provider requests, Git operations or pushes are part of implementation.
v0.2 has made no calls and is not pushed. This is a harness-only revision.

The preserved `freeze.json` SHA-256 is
`c1c108d06741d3e9c00751915b4e33933ad620e819cb5905d505fc481e2272e4`.
`freeze-r1.json` binds those exact bytes through parent_freeze_sha256, the revised
inventory, and passing source-bound test report. Attestation binds both manifests
and the current inventory; the genuine push timestamp must follow r1. Existing
model settings, prompts, schemas, schedule, world rules, scientific endpoints,
sample sizes, budget caps and original fixtures remain unchanged.

A pure Claude CLI subscription limit refusal is a definite non-start with no
model output: api_error_status 429, is_error true, explicit integer zero input,
output, cache creation and cache read counters, and zero total_cost_usd. Exact
refusal text must match the CLI usage-limit message; output, contradictory
activity, other errors, missing or nonzero usage retain existing frozen handling.

The harness saves exact refusal stdout/stderr and an immutable usage-limit pause
record with saved prior episode history, request/start hashes and cost/time
ledger prefixes. It settles the refused attempt's slot at zero, leaves remaining
slots reserved, records no terminal model failure, and returns PAUSED cleanly.
On the same collect command after the saved reset timestamp, it audits earlier
calls, verifies ledger prefixes and unchanged request bytes, saves a create-once
clearance, restores only the original slot hold, and resumes at that position.
Earlier calls are never resent. Repeated refusals produce additional pauses and
zero settlements. An unknown reset stays paused; interrupted clearance or any
unexplained partial start retains the conservative uncertain-start stop.

Analysis emits operational_events.usage_limit_refusals separately, without
adding refusals to model calls, behaviours, technical failures or scored terminals.
Paused episodes remain unknown; frozen planned denominators remain unchanged.
All incomplete/local transport, model-content, tool/identity, overrun and unknown
accounting handling retains its original boundary.

Initial inspection found no collection directory, existing v0.2 stop, saved
refusal or scored refusal. Thus clearance and re-disposition are no-ops; the
record is evidence/usage-limit-clearance-r1.json. Both preserved historical ledger
prefixes were verified against freeze.json; neither ledger was written. Sibling
programme evidence informed the reviewer's decision but is not imported or edited.

Validation: 174 offline tests include initial/mid-episode/report-position resumes,
repeated refusals, exact request/history preservation, zero settlement and rearm,
unknown resets, other errors, nonzero usage/tool counters, corrupt prefixes and
requests, orphan starts, interrupted clearances and immutable revision binding.
The supplied real valid envelope was SHA-256 matched to the existing fixture
(a4e9f03ce0cd4cbde843924c06880082baaee6e58597fcad0f970022a9c6eb2c).
Initial new analysis tests used an incomplete plan fixture and failed on a missing
paired arm; corrected to the complete Claude schedule. That failed test output
is retained in build/r1-initial-test-output.txt. No production inference occurred.


## R3 · pre-Claude root-schema compatibility · 12 November 2026

Requested by Claude, the delegating reviewer agent after the Receipt Gap sibling
reported a provider HTTP 400 for a root union. No Claude calls occurred in Bridge
or Bus, so no episode disposition changes or resends apply here.

Claude-only action/report schemas are single objects with required exact keys.
Action leaf domains are the exact fieldwise union of the unchanged local
branches: provider-only acceptance differs solely in cross-field combinations,
still rejected by the unchanged validator. Report acceptance is identical.
A structural projection proof and 67,200 sampled combinations verify inclusion,
branch rules and both arm permissions. Omissions, extras, bad types, boundaries,
actual CLI schema arguments and recorded schema hashes are also checked offline.
The smaller Claude schemas fit the unchanged conservative r2 reservation inputs.

All 1,200 local r2 episodes remain in place and retain their original freeze/push
binding. New Claude starts bind r3; a new push receipt uses collection-r3/ while
all call/accounting evidence continues in collection-r2/. R3 verifies preserved
bytes and the old ledger prefix before admission and rejects local collection.
All three parent freezes and preservation evidence are bound by freeze-r3.json.
Tests cover parent drift, immutable local bytes, append-only accounting, zero
prior Claude starts, obsolete freeze rejection, fresh push gating, all four
pushed manifests and offline Claude schema provenance. RUN-r3.md is the handoff.

Read-only inspection of active useful-core, one-door-many-hands,
portable-self/v0.2 and three-rules-one-lunch Claude paths found no other root
union. Their source paths/hashes are saved in evidence/r3/sibling-schema-audit.json.
Provider acceptance remains UNKNOWN; this revision makes no inference call.
