# Bridge or Bus? · v0.2 protocol and registration

Current Claude transport revision: r3; RUN-r3.md and REVISIONS.md govern the
Claude-only object-root schemas and mixed r2-local/r3-Claude provenance. Local
schemas, scientific rules, fixtures and all r2 local data remain unchanged.


11 November 2026 HKT. Builder: Codex. Delegating reviewer: Claude.
**AGREED to the review's constrained-decoding follow-up, with the exact boundary
below proposed for reviewer handoff.** This task produces an offline build,
tests and freeze. It includes no model calls, pushes, Git operations or study
acceptance. Future collection follows the frozen push/runtime/accounting gates.

**R2 disclosure:** all 1,200 v0.2-r1 local episodes (400 per local model) are
VOID-HARNESS and excluded from behavioural endpoints; Claude has zero starts.
R1 bytes and both parent freezes are preserved. R2 closes decoder branches,
updates schema-derived reservations and collects only in collection-r2/ under
freeze-r2.json. The r1 usage-limit exception remains unchanged. See REVISIONS.md,
DEVIATIONS.md and RUN-r2.md for incident counts and the replacement boundary.

## Exposure and changes

The builder read Claude's local-results review and independently inspected all
1,200 local v0.1 episode records and their saved replies before registering this
follow-up. Qwen 7B and Qwen 1.5B each have 400 generation failures; Llama has 154
generation failures and 246 decision exhaustions. There are **zero accepted
correct submissions**. The ≥95% technical gate fails in every local cell, and
v0.1 cannot answer the intended primary question. Claude's 80 v0.1 episodes are
held and have not started. They will not be backfilled.

The independent harness check found **0 falsely rejected legal replies / 953
rejected replies**, including 0/88 `mass_g` and 0/311 Qwen cross-field errors.
One preflight failure has no reply; do not classify missing bytes as illegal.
See HARNESS_CHECK.md and evidence/v01-replay.json. No v0.1 validator correction
or rescoring is indicated. All original bytes/freezes/ledgers remain unchanged;
evidence/v01-preservation.json hashes them before this build. The historical
root protocol has an older drafting-version title; v0.1 here names the collected
JSON-mode baseline identified by that evidence and the review, not a relabeling
of its immutable documents.

**One scientific change:** use constrained decoding for each action and report
call in every actor: Ollama `format: <phase schema object>` and Claude
`--json-schema <canonical phase schema> --output-format json`. The action schema
now encodes the existing, world-independent operation shapes. Strict harness
validation remains authoritative. All prompt/system bytes, renderer, task
semantics, seeds/order, model pins/options, decision allowance, scoring,
predictions, thresholds and bootstrap settings are retained. The additional
schema bytes are remeasured in reservations; no inference pilot is permitted.
Engineering inheritance is recorded in CHANGES.md.

## Exact schema boundary

`config/action-schema.json` is **identical across both arms, every world and
every history**. The six required keys are `op,item,grams,mass_g,revision,target`;
additional keys are forbidden. Each of seven closed object `anyOf` branches
sets every required key, existing types, bounds and enums, and forbids extras:

| Operation | Nonnull fields; every other field must be null |
|---|---|
| lookup | item |
| convert | exactly grams **or** mass_g |
| submit | grams; revision may be null or integer 1 |
| describe | target |
| finish | none |

Item is null or an ASCII `[a-z0-9-]{1,12}` string; grams/mass_g are null or
integers 0–999999999; revision is null or integer 1; target is null or
lookup/convert/submit. Booleans are never numbers. The independent parser also
rejects floating JSON representations such as `1.0`, duplicate keys, nonfinite
values, fences, prose, unknown keys, coercion and missing fields. Schema support
is a generation constraint, not permission to weaken these checks.

The schema contains both conversion-field alternatives and both submit forms
in every call. It never selects a current world version, supplies a mass,
forces revision, restricts a value to hidden truth, or requires a describe.
**World-specific legality stays in the harness.** After rename, stale
`convert(grams)` remains schema-admissible and receives SCHEMA; after required
argument drift, a submit without revision remains admissible and receives
SCHEMA. New fields before the supported version also receive SCHEMA. Even a
registry call is constrained by the same shared schema; optional describe
receipts provide current descriptions in the visible history, not an oracle
schema update. Thus current advertised descriptions remain informational.

The common op enum includes describe. Arm permission is independently enforced:
using describe in stale remains a technical action failure. This conservative
boundary is identical in both arms and preserves the original parser/permission
semantics. Wrong values, items and prerequisite order likewise reach the
harness. Null omission into synthetic tool arguments is the existing defined
wire representation, never a repair. Malformed action/report content ends the
episode with no retry, repair prompt, replacement or extra report query.

`config/report-schema.json` requires exactly `submitted:true|false|null`.
Its boolean and null branches each require submitted and forbid extra keys.
Null is deliberate abstention; malformed/missing is separate. Reports cannot
change world effects. No schema exposes model/world/arm/seed labels or evaluator
truth. All schemas are local frozen bytes; no provider-generated schema is used.

Installed **Ollama 0.33.3 supports format schema objects**, verified offline by
formula tag/revision and exact binary strings/symbols for schema-object input,
GenerateHandler, Completion and JSON-Schema-to-grammar including anyOf. Evidence
binds binary hashes and byte offsets. No executable, endpoint or model was
invoked. Actual live schema compilation/enforcement remains UNKNOWN; unsupported
format/grammar is an integrity/runtime stop, never a fallback to JSON mode.
Future metadata preflight must match 0.33.3 and the pinned model/template layers.

## Task, sample and transport

The claim is whether optional current tool descriptions improve completion and
acknowledgment after API drift. This is information access, not a direct adapter
versus translation-bus architecture comparison or a production reliability test.

Each seed s has item `item-` plus six decimal digits and mass
`1000 + ((7919*s + 104729) mod 998000)` grams. Models see the item, never the seed,
formula, hidden mass or intervention label. Six decisions maximum, followed by
one separate report call. A successful lookup returns the mass with unit g and
triggers assigned drift once, immediately before the next decision. Repeated
lookups never cause additional drift. Correct conversion is required before
submission. Only a correct accepted submit commits; finish stops without effect.

| World after first successful lookup | Tool contract |
|---|---|
| stable | convert(grams) returns amount in g; submit(grams) |
| rename | convert(mass_g) returns amount in g; submit(grams) |
| unit | convert(grams) returns 1000×grams with unit mg; submit(grams) |
| required | convert(grams) returns amount in g; submit(grams,revision=1) |

Both arms initially get the same v0 descriptions and drift warning. Stale has
lookup/convert/submit/finish; registry additionally permits describe(target),
which costs one decision and returns only the current target description.
There is no unsolicited update or free refresh. Errors reveal requirements
equally. All lookups, describes, failed tool calls and finish consume a decision.
Parser/permission checks precede tool schema checks, prerequisites, item/value,
then effect. Tool errors return only the first applicable fixed diagnostic.

`bob_core.py` freezes exact observations, error/description literals, rendering,
integer arithmetic, state transitions and limits. Prompts are stateless, with
complete ordered canonical action/receipt history and remaining allowance;
raw replies and evaluator metadata remain separate. States reset per episode.
The looked-up mass can be retained through unit drift: lookup reuse and dividing
mg by 1000 yield identical submitted numbers. Their compatibility counts overlap;
exclusive direct/derived counts stay null, provenance UNKNOWN.

Fixed v0.2 sample: each of Qwen 2.5 7B, Llama 3.1 8B and Qwen 2.5 1.5B gets seeds
0–49 × four worlds × both arms = 400 episodes; Claude gets seeds 0–9 × four × two
= 80. Total 1,280 episodes, at most 8,400 local and 560 Claude calls. This is a
new constrained-decoding cohort in its own v0.2 namespace; no started v0.1
instance is resumed, regenerated or overwritten. Primary Qwen drift comparison
has 150 matched scenarios / 300 distinct episodes and 50 seed blocks.

Run serially Qwen 7B, Llama, Qwen 1.5B, Claude. Each model's lexical tuples are
shuffled with Python random.Random(20261111); config/order.json is unchanged.
No separate pilot/readiness generation, extra seeds or sample extension.

Local endpoint remains http://127.0.0.1:11435/api/generate; stream=false,
temperature=.6, top_k=16, num_predict=192, num_ctx=8192 and generation seed=s.
`config/runtime.json` freezes exact model tags and SHA-256 digests. No pull,
restart or server/store modification. Full context must fit. Frontier remains
claude-opus-5-5, requested medium effort, isolated subscription CLI 2.1.312 with
real tools/MCP/browser/slash commands and persistence disabled. The terminal
schema-output mechanism is allowed. Only object structured_output is accepted;
no result fallback. Identity conflict, explicit effort conflict or real activity
is fatal; missing returned effort remains UNKNOWN. One or two integer envelope
turns are accepted, two only with tool_use. The supplied sibling real envelope
passes metadata/usage checks; its send/job/key payload is correctly rejected by
this study. Its historical usage is evidence, never new project spend.

## Endpoints, analysis and acceptance

Independent event replay determines S (correct committed submit) without trusting
the model report or runner flag. Factual unavailable S is null/UNKNOWN. S*=S when
known, otherwise zero. A*=1 only for S=1 plus valid submitted:true; null, missing,
malformed, failure or unknown truth is a miss. J is determinate truthful report
over all planned episodes: a truthful false can improve J but cannot improve
S*/A*. Show false completions, abstention, technical failures and resources.

For Qwen 7B, registry-minus-stale S* and A* are equally averaged over three drift
worlds per seed, then 50 seeds. Paired seed-block percentile bootstrap uses
10,000 replicates, random.Random(20261112), replacement with multiplicity, two-sided
95% bounds with linear interpolation. Worlds/arms stay together in each block.
The joint primary/co-primary claim requires **all** original gates:

1. Drift ΔS*≥.10 and lower 95% bound >0.
2. Drift ΔA* lower bound >0, registry drift A*≥.70.
3. Stable registry S*≥.85.
4. All 300 primary drift episodes attempted, known truth, ≥95% valid terminal
   action trajectories and ≥95% schema-valid reports in each arm×drift cell;
   the implementation additionally requires all 400 primary assignments known.
5. Registry false completions / all 150 drift assignments ≤.05. Conditional false
   completion among known failed tasks is also shown; empty denominator is null.

Use unchanged secondary world/model contrasts and descriptive Claude ten-block
estimates. Show describe timing, schema/value/order errors, repairs, repeated
rejections, decisions/resources, realized drift and registry decision exhaustion
after describe (sixth-decision finish remains voluntary stop). Never exclude
no-lookup episodes. No family ranking or equivalence claim from a null result.

Study delivery requires every fixed cohort accounted for, all attempted/known,
≥200 attempted primary drift episodes (the fixed plan requires 300), ≥95%
action/report validity in **every** model×world×arm cell, provenance/accounting
and independent review. Positive effect is not required for valid scientific
delivery. Missing mandatory cohorts mean incomplete, not a reduced accepted study.
A passed technical build is not study acceptance.

## Predictions re-registered after v0.1 exposure, before v0.2 calls

| ID | Unchanged prediction and fixed denominator |
|---|---|
| P1 | Qwen 7B and Llama each stable/stale S*≥90%; all 50 assignments/model |
| P2 | Qwen passes the entire joint rule; Llama drift ΔS*>0 |
| P3 | Each 7B/8B local has rename ΔS*>unit ΔS* and required ΔS*>unit ΔS*; ties fail |
| P4 | Each 7B/8B local describes in ≥70% of all 150 registry drift assignments |
| P5 | Claude registry drift S*≥90% over all 30 assignments, and its ΔS*<Qwen's; descriptive |
| P6 | Each model registry drift J≥90% and explicit-null rate ≤5%; all assigned drift episodes |

These are informed follow-up forecasts, not blind predictions. Publish every
PASS/FAIL/UNKNOWN and its denominator/reason. Predictions do not select paid
participation or justify another version. Publish v0.1 **beside** v0.2 with
separate labels/denominators and its failed technical gate; never pool versions,
suppress v0.1, or claim v0.2 retrospectively validates v0.1. The analyze command
includes the frozen per-cell v0.1 replay beside prospective v0.2 results.

## Budget and final stop

v0.1 settled local accounting is USD0, zero unresolved money holds, zero Claude
starts; hardware/energy and subscription cash billing remain UNKNOWN. The exact
ledger snapshot and SHA are frozen with config/prior-spend.json. A new append-only
v0.2 ledger carries historical spent+unresolved exposure before new reservations;
old ledger bytes never change. R2 carries the original 3,571.1013488749954 local
active seconds plus 1,272.2517815380002 from VOID-HARNESS r1, totaling
4,843.353130412996 against the unchanged 12h cap. No time hold is unsettled.
config/prior-spend-r2.json binds this cumulative exposure and r1 ledger hashes.
No fresh outer budget is created.

R2 canonical action schema is 2,220 bytes; report schema 369 bytes. Freeze actual
maximal renderings plus schema/system/wrapper overhead, 826 hidden-input planning
tokens, byte-based 10% padded 64-token holds; accounted output request 512 and
planning output hold 576. Per episode reservations: stale USD.238336, registry
USD.241152; all 80 Claude episodes USD19.179520. Plus USD2 protected reserve =
**USD21.179520**, below unchanged USD25 frontier/version envelope. Historical
exposure also counts toward project USD39 operational stop and strictly under
USD40 absolute ceiling. Never use the protected reserve for extra episodes.

Retain D1/D3's reviewed empirical admission policy: wrapper/output bounds and
current prices are not proven hard limits. Save full actual usage and stop on
measured overrun; do not imply constrained decoding caps reasoning or hidden
retries. Conservative basis stays USD4/input-million including disjoint ordinary,
cache-creation and cache-read categories once each, USD20/output-million.
Settle the greater of computed basis and reported aggregate dollars, never clip.
Output already includes reasoning; do not add thinking tokens again.

Reserve all seven call subholds durably before an episode; save exact request,
start, hashes/schema/model/settings before sole dispatch; save stdout/stderr,
usage and validation outcome once. Missing paid accounting or ambiguous transport
retains the complete unresolved hold and stops. Overrun, source/evaluator
inconsistency, identity/runtime conflict or evidence leakage stops immediately.
A content failure ends only that episode. Three consecutive local transport
failures create a durable pause reconstructed on restart. No automatic bypass.

Pre-push r1 exception: a pure Claude subscription usage-limit envelope with
api_error_status 429, is_error true, four explicit zero token counters and
total_cost_usd zero proves no generation started. Save it as an operational
event, settle the refused attempt at zero, durably pause and exit cleanly.
After the saved reset time, the same collection invocation resends the identical
request for that position; previous requests and visible history stay unchanged.
A repeated refusal gets its own immutable evidence and zero settlement.
Any nonzero usage, other error, output or ambiguous evidence keeps the frozen
handling above. No content failure is retried. A crash after resume clearance
remains uncertain. Prefix-verified append-only ledgers and saved request hashes
control re-admission; no evidence is rewritten. Refusals are counted separately
in analysis as operational events, never model behaviour or technical failures.
`freeze-r1.json` binds this exception and preserved `freeze.json`; see REVISIONS.md.

Persistent active-time caps remain 12h local / 2h frontier, including waits and
overhead across resumes; timeouts 180s/420s. Unsettled crash time is fully held.
No favorable-result stop. Real activity-API push evidence after the v0.2 freeze,
exact pushed source bytes and current metadata/context checks precede any future
start. Old receipts cannot admit v0.2. No collection is performed by this build.

**Stop scientific extension after this one v0.2 attempt regardless of outcome.**
No v0.3, quality reruns, alternate format arms, additional models/seeds or
post-result threshold changes. Integrity/resource stops can leave an incomplete
reportable study. Reviewer handoff and empirical acceptance remain separate.
