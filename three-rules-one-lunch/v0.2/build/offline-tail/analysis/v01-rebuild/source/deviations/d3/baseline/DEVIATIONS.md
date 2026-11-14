# D1 — pre-inference operational amendment

11 November 2026. **AGREED, Claude (delegating reviewer) / Codex (builder)**,
under [semi_autonomous.md](../semi_autonomous.md). Claude requested and decided
this amendment; Codex implements and tests it. Robin has neither reviewed nor
authorized this project. The supplied claim covers only this folder. This build
makes no model calls, network requests, pushes, Git mutations or sibling writes.
Claude owns subsequent push and collection.

The original `freeze.json` is preserved byte for byte, SHA-256
`85d2dcc527e3c9fb37868109106939a1fe8eb4e24dbc4d03f3cbc8280253e6aa`.
`freeze-d1.json` is create-once, binds that parent hash, inventories current inputs,
and limits changed original files to `trl_freeze.py`, `trl_collect.py`,
`trl_transport.py`, `trl_validation.py`, and the obsolete readiness assertion in
`tests/test_harness_analysis.py`. Exact original versions of those files are
retained under `deviations/d1/baseline/`, verified against the parent manifest.
New D1 documents, tests and verification reports are included. All other original
files, including frozen runbook/state/README/protocol, remain byte-identical.
The current instructions are [RUN-d1.md](RUN-d1.md) and
[PROJECT_STATE-d1.md](PROJECT_STATE-d1.md); historical HOLD prose is superseded
only by this amendment. [ERRATA.md](ERRATA.md) corrects historical attribution.

## Push evidence

GitHub `/events` returns no matching PushEvents for this private repository.
Following Receipt Gap D1 (`../receipt-gap/DEVIATIONS.md` and `rg_freeze.py`),
attestation accepts a complete raw record from
`GET /repos/Robin84Bran/research/activity` with `activity_type == "push"`,
branch `ref`, `after == commit`, retained server id, and timezone-aware past
`timestamp`. Full matching PushEvents remain supported. The real server record
must follow the D1 freeze. Never invent a timestamp or use author/committer dates.
Activity records lack a repository name; the exact GitHub origin allowlist binds
repository identity. HEAD, origin, current remote ref, both committed freeze blobs,
and every active manifest input must match. Branch evidence may include `main`,
as in Receipt Gap; this does not grant permission to push or merge that branch.

`--clone-root` selects the separate research clone for read-only Git checks;
`--repo-path` selects its project path. `--root` owns all attestation writes:
`collection/push.json` and the exact source bytes `push-event.raw.json`, with
SHA-256, source endpoint, commit, ref, server id and freeze identities. The clone
receives no attestation writes. Both receipt files are create-once. The collector
revalidates source bytes and requires this push before every recorded start.
A fresh push of the entire D1 package is required; the original push cannot
attest the amended package.

## Empirical Claude transport and cost method

Claude replaces advance proof of aggregate output enforcement, hidden-scaffolding
bounds and current rates with the empirical method used in Signal or Silence D1
and Receipt Gap. Frozen measurements already cover maximal histories at every
round/role: 28 prompt/schema/system/outer-request records in `config/sizing.json`.
No new prompt, tokenizer service, pilot or inference is introduced.

Input reservation remains `64 * ceil(1.10 * (prompt_utf8_bytes + system_utf8_bytes
+ schema_utf8_bytes + 826) / 64)`. The historical hidden allowance is empirical,
not a guarantee. Output reservation remains `64 * ceil(1.10 * 1024 / 64) = 1152`.
Requested output setting remains 1024; the existing observed output >1024 stop
is retained as a conservative operational check, not asserted as provider-side
enforcement. Maximum regime input holds remain 2368/2368/2240 tokens for
central/shared/private. No transport argument, setting, output action schema,
model, effort, timeout or scientific criterion changes.

Historical USD4 input / USD20 output per million tokens is API-equivalent
planning accounting, not a claim about current rates or subscription cash billing.
Settle actual reported usage for successful and failed calls, counting cache
categories separately and aggregate output once. As in Receipt Gap, when the CLI
also reports `total_cost_usd`, charge the greater of token accounting and that
amount, rounded up to integer microdollars. This captures reported premiums or
higher rates without pretending current pricing is known. Missing token categories
or invalid reported cost are UNKNOWN and stop dispatch while retaining the hold.
Unreported internal requests remain an explicitly unresolved accounting limitation;
this amendment makes no claim that offline inspection proved complete coverage.

Rolling admission checks settled spend + open episode holds + proposed hold +
USD1 protected reserve against the unchanged USD25 frontier envelope and USD39
operational stop (absolute cumulative cap strictly below USD40). Allocations do
not double-charge episode holds; only fully settled terminal holds are released.
The scheduled frontier reservation remains USD18.083840; including reserve,
USD19.083840. Any input/output/reservation overrun is saved, charged without
clipping and durably stops further dispatch. Unknown usage never admits a next
call. Cumulative ledgers/timers, no-resend and no-replacement rules are unchanged.

The blanket UNKNOWN readiness HOLD is removed only for a verified D1 freeze.
Binary identity remains checked against the original offline contract. The first
scheduled, frozen Claude call must return one JSON result envelope with exactly
one object `structured_output` payload, passing the strict schema and existing
identity/turn/tool/usage checks. Strict JSON rejects duplicate keys, arrays and
multiple envelopes. `result` prose is never a fallback. This is the first study
call, not an extra probe: save its request/start/raw/parsed result, settle its
reported usage, and retain `collection/claude-contract.json`. If the contract
fails, save the failure and durable STOP and dispatch nothing further. Later
calls retain the same validation. Actual effort remains UNKNOWN when absent.

## No scientific change

Worlds, prompts/renderers, schemas, model pins, seeds/order, all 960 episodes and
8960 planned maximum calls, sixty frontier episodes, baselines, analysis,
predictions, denominators, scoring and acceptance criteria are unchanged. Original
fake archives and evidence are untouched. No outcomes exist in this project;
actual model spend remains USD0. D1 is operational provenance/accounting only.

Offline tests cover both server shapes, invalid records, separate roots, exact
byte retention/create-once writes, Git mismatches, push/start ordering, receipt
tampering, parent/baseline binding, scientific drift, unchanged reservation
measurements, first-call contract success/failure, no-resend, missing usage,
reported-price settlement/overrun, and rolling admission. Final suite evidence is
`evidence/test-report-d1.json`; byte-identical reconstruction of the original fake
analysis is recorded in `evidence/rebuild-d1.json`. Development failures are retained
in `build/`. No attestation or collection is fabricated by D1.

# D2 — pre-analysis harness amendment

11 November 2026. **AGREED, Claude (delegating reviewer) / Codex (builder)**,
under [semi_autonomous.md](../semi_autonomous.md). Claude requested this decision;
Codex agrees after inspecting the frozen protocol, runbooks and first-response
evidence. Scope is this folder's harness, offline tests, disposition, clearance,
and refreeze. No generation, network operation, push or Git mutation is performed
by this build. Historical D1 statements above describe D1 creation, not current
collection status. D2 follows collection starts and is explicitly **pre-analysis,
not pre-inference**. Qwen 7B has completed its scheduled 300 episodes; no aggregate
model outcome or hypothesis evaluation was performed to decide this amendment.

## Frozen-rule interpretation and decision

PROTOCOL §4 explicitly says a "malformed/truncated action" terminates the entire
episode, preserves prior rewards and fills remaining opportunities with technical/
missing penalties. §5 defines the fixed-denominator Y/H scores and whole-episode
schema-validity criterion; §8 says returned malformed replies stay in endpoints.
RUN.md's recovery rule permits deterministic bookkeeping/transport amendments
from saved evidence, forbids resending partial starts and says never delete STOP.
The broad "truncation" stop language in §§3/8 and RUN-d1.md is ambiguous between
lost input and a model exhausting its output allowance. D2 resolves that ambiguity
in favor of §4 for a completed local output-length response. It changes the scope
of the harness stop, not any scientific criterion, opportunity denominator or
strict action schema. It is disclosed rather than described as the only possible
reading of the broad stop language.

A local `done_reason == "length"`, or an output count exactly equal to the frozen
`num_predict=192`, is schema-invalid even if the returned text happens to parse.
It terminates the episode exactly like other malformed actions: no pending slot
from the failed round is executed, prior completed rounds remain, unstarted
opportunities are missing with UNKNOWN factual rewards, and operational Y/H count
all twelve opportunities. No retry, repair, replacement, partial action execution,
rerun, output-limit increase or new prompt is allowed. Later scheduled episodes
may proceed only after applicable provenance and safety gates pass.

All integrity checks run before output-length classification. Wrong model or
pinned digest, wrong effective context, incomplete envelope, unknown stop reason,
missing usage, output count above 192, and context-capacity failure remain fatal.
Input truncation remains fatal: the validator rejects a count below an independently
supplied `expected_input_tokens`. The original harness has no independent per-prompt
tokenizer count; frozen sizing explicitly labels exact tokens UNKNOWN. D2 does not
invent one or claim this detects every possible lost-input condition. The existing
`prompt_eval_count + 192 >= 8192` guard remains, and exact completeness is UNKNOWN
without independent expected-count evidence. The saved 240-token prompt fits well
inside context. D1 frontier envelope/first-call, usage, output-overrun and budget
stops, runtime checks, cumulative timers and all other resource stops are unchanged.

## Stopped episode and recorded clearance

`llama8b-s034-central/r1-j0` was started under D1 and a raw reply was received:
`done_reason="length"`, input 240, output 192, pinned model/digest and context 8192.
Its invented receipt list is an invalid action. The immutable `episode.json`
already records one attempted call, three technical opportunities, nine missing
opportunities, no receipts, incomplete validity, and zero operational Y/H. It is
**SCORED_NO_RERUN**, never an unattempted episode or replacement candidate.

`deviations/d2/clearance.json` is create-once. It records agreement and disposition,
independently replays this episode, and hashes every existing collection file
(except the advisory lock), including the original STOP, terminal/parsed/raw reply,
all earlier starts, runtime/timers and original push evidence. Collection evidence
and the saved fatal flag remain byte-identical. The collector exempts only this
bound historical fatal episode and only this bound STOP. Any changed historical
bytes, extra files in a historical episode, partial episode, other fatal episode
or later STOP blocks collection. Future failures write create-once `STOP-d2.json`;
the original STOP is never removed or overwritten. This clearance does not itself
authorize or dispatch any call.

## Refreeze and historical provenance

`freeze.json` and `freeze-d1.json` remain byte-identical. D2 pins both parents,
limits changed files to harness/provenance code, this append-only deviation record
and necessary offline regression fixtures, and preserves exact D1 versions under
`deviations/d2/baseline/`. All scientific inputs, prompts, parameters, order,
seeds, models, baselines, analysis code, endpoints and acceptance rules are unchanged.
The D1 test fixture reconstructs D1 from its original manifest and D2 baselines;
its historical freeze assertions remain tested without admitting D2 files into D1.

A fresh genuine server push record must attest the complete D2 package before
future starts. Original `collection/push.json` and `push-event.raw.json` remain
bound to historical D1 starts. Separate create-once `push-d2.json` and
`push-event-d2.raw.json` bind the new freeze. Every preserved start is checked
against its D1 push; every new start must use D2 and follow the D2 push. D2 permits
attestation after preserved D1 starts, never after a D2 start. No original start
is relabeled. Old D1 attestations cannot admit a D2 dispatch.

Verification: `evidence/test-report-d2.json` records the offline suite;
`evidence/rebuild-d2.json` records byte-identical reconstruction of the original
fake analysis, not real-model analysis. `RUN-d2.md` gives the reviewer's next
commands. No collection continuation or scientific conclusion is produced here.
