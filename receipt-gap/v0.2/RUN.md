Active amendment: `freeze-r5.json`. Use the r5 commands at the end. All earlier
execution/disposition sections are historical. Claude's r5 reviewer ruling clears
the exact schema-rejection 400 as HARNESS NON-START and permits the identical
prompt with a corrected provider schema. A fresh r5 push and attestation are
required before future model calls. Codex made no model calls, pushes or Git commands.

# Receipt Gap v0.2 · offline freeze and reviewer execution

Historical r3 amendment: `freeze-r3.json`. Superseded by r5 at the end.
Use the r3 commands at the end. Claude's programme ruling clears the saved DNS
STOP as a definite non-start; its historical bytes remain intact. A fresh r3
reviewer push and attestation are still required before collection resumes.

Claude delegated this build to Codex. This package makes one scientific change:
per-toolkit exact action schemas are passed to every actor as constrained decoding.
Local reports keep JSON mode; Claude reports keep the unchanged report schema.
The complete protocol, exposure statement and P1–P7 are in `PROTOCOL.md`.
No model calls, pushes, Git commands or real attestations were made by the builder.
Stop after v0.2; empirical acceptance needs both agents' later evidence review.

## Verify offline

```sh
RG_V02='<WORKSPACE>/06_intelligence/AI_research/research/receipt-gap/v0.2'
cd "$RG_V02"
python3 -B rg_freeze.py verify --freeze freeze-r1.json
python3 -B -m unittest discover -s tests -v
python3 -B verify_offline.py --output '/private/tmp/receipt-gap-v02-review-verification.json'
python3 -B rg_analysis.py --data offline/dry-run --output '/private/tmp/receipt-gap-v02-review-fake-analysis.json'
```

Use unused output filenames. `verify_offline.py` blocks network and every subprocess
except Node for deterministic cross-language draw parity. The saved offline run is
labelled fake: 12 episodes, 72 fake calls, zero real calls, zero new outstanding
fake holds. Its USD0.021600 accounting is fake, not additional project spend.
`offline/verification.json` and `offline/analysis-fake.json` contain the full checks.
To generate another fake dry run use an unused directory outside the frozen tree:

```sh
python3 -B rg_offline.py --output '/private/tmp/receipt-gap-v02-review-fake-run'
```

Never rerun prepare/freeze/revise or edit frozen inputs. `freeze.json` remains byte-identical.
`freeze-r1.json` is the active create-once pre-push harness revision, binding
the original freeze SHA-256 and exact original witnesses under `revisions/r1/`.
See `REVISIONS.md` and `DEVIATIONS.md`. The original freeze is create-once.
It binds the portable real Claude envelope, binary schema-support evidence,
prior-spend snapshot, full v0.1 preservation inventory, scientific function hashes,
all tests, the raise inventory and fake-run evidence. `rg_stats.py`, prompts,
schedule and report schema are byte-identical to v0.1; world/scoring/analysis
functions are compared by AST against frozen source witnesses.

## Budget and dispatch boundary

Ollama 0.33.3 schema-object format support was verified offline from the installed
binary and Homebrew formula, with SHA-256 and byte offsets in
`evidence/ollama-schema-support.json`. Live runtime/schema compilation is UNKNOWN.
The future first scored call must use this exact schema and fail closed if the
provider rejects it. No separate live pilot is permitted.

Carry v0.1 settled **USD5.660781** and unresolved holds **USD0.293888** forward.
`collection/ledger.jsonl` begins with their carry event; every new settlement and
reservation appends to it. The old ledger is never written. Its source SHA-256 is
`b4436390ef3ef74b4c4194d9220a0c732d8988ae6879a5f3bd9831860dda330f`.
The current sibling v0.1 ledger must still match before production dispatch.
Historical holds cannot be released by v0.2. Fresh v0.2 worst-case reservations
are **USD16.145920**; project exposure plus all new reservations plus the USD1
reserve is **USD23.100589**, below USD25 and the USD39/40 backstops. Expected new
Claude spend is about USD6; cash billing is UNKNOWN. No additional sample is funded.

D1–D3 and sibling lessons: a valid two-turn `structured_output` schema envelope
is supported with the inherited CLI `--max-turns 1`; only positive subagent counts
indicate activity. Identity, conflicting effort, context, incomplete local done,
external activity, accounting, transport or resource failures are fatal, except
the exact pre-generation usage-limit non-start described below. Invalid
model actions/reports, length stops and schema-output rejection end just their
episode, with no repair, retries, additional effects, replacement or report after
an invalid action. Every terminal trajectory is retained and scored. Missing usage
and uncertain starts retain holds and stop. Timers persist across resumes.

## Reviewer push, attest and collect

Copy the entire frozen v0.2 package, preserving its directory, into the separate
claimed research clone's `receipt-gap/v0.2`. Verify and run all offline tests from
that independent package. Include every file listed by `freeze-r1.json` plus both
`freeze-r1.json` and its unchanged parent `freeze.json` in the later commit. Exclude production `collection/` outputs.
Keep all canonical collection here. No Git command runs against RobinOS2.

After the reviewer performs the fresh push, capture its full GitHub PushEvent or
repository activity-API push record. Set the three concrete handoff values below:

```sh
RG_V02='<WORKSPACE>/06_intelligence/AI_research/research/receipt-gap/v0.2'
RG_CLONE='<separate-research-clone-root>'
RG_COMMIT='<new-v0.2-pushed-40-character-commit>'
RG_EVENT='<absolute-path-to-new-full-server-push-record.json>'
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT" --freeze freeze-r1.json
python3 -B "$RG_V02/rg.py" collect --cohort local --freeze freeze-r1.json
python3 -B "$RG_V02/rg.py" collect --cohort claude --freeze freeze-r1.json --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Attestation checks HEAD/origin/remote ref and every committed frozen blob. It
creates `collection/push.json` and exact-byte `push-event.json`; both are create-once.
The server push must follow `freeze-r1.json` creation and precede every call. A v0.1 receipt
or stale push cannot open v0.2. No builder attestation exists yet.

Do not delete a STOP, receipt, start or terminal record. A new `collection/STOP.json`
blocks dispatch. Resuming the same collect command skips terminal episodes and
only runs definitely unstarted positions. A partial episode can continue solely
at a verified usage-limit non-start; every other uncertain start stays blocked.

## Usage-limit pause and resume (r1)

Claude's programme-wide harness decision is recorded in `REVISIONS.md`. A strict
429 usage-limit envelope with `is_error: true`, explicitly zero input/output/cache
tokens and zero cost is a definite non-start. Generated output, positive activity,
missing usage, other errors and ambiguous output retain the frozen handling.
The saved refusal text supplies the Hong Kong reset clock; no estimated wait or
wall-clock timeout opens dispatch.

Each Claude dispatch has create-once `dispatches/<position>/<attempt>/start.json`
and `raw.json`. A refusal adds `pause.json`, binding raw/start/request hashes and
an absolute reset time. It creates neither `episode.json` nor a fatal STOP. The
collector prints `status: "usage-limit pause"` and exits successfully. A collect
invocation before reset exits with that same pause and makes no provider request.
After reset, invoke the identical collect command above. The saved request bytes,
schema, system prompt and budget must match; prior accepted actions are replayed
and checked without resending them. Only the refused position is sent again.
A repeated refusal produces another immutable attempt and pause.

A refusal settles its call reservation at zero; a separately validated append-only
`restore` event reinstates that same reservation before the next dispatch. No
historical hold is released. Active timers retain spent time and exclude idle
pause time. Incomplete dispatch evidence remains fail-closed. Analysis reports
refusals under `operational_events`, separately from model behavior and failures.
While an episode is paused, its outcome remains UNKNOWN and it is excluded from
model metrics until resumed; technical acceptance remains UNKNOWN.

`revisions/r1/clearance.json` records prefix checks of both ledgers. No v0.2 STOP,
call or saved refusal existed, so no STOP clearance or scored-failure
re-disposition was needed. No ledger or old evidence bytes were rewritten.
No change to v0.1 stops, data, charges, holds, timers, analyses or delivery files.

## Independent post-collection review

In the independent package, copy the saved v0.2 `collection/` outputs and run:

```sh
python3 -B rg_freeze.py verify --freeze freeze-r1.json
python3 -B -m unittest discover -s tests -v
python3 -B rg_analysis.py --data collection --output collection/analysis-v02.json
```

Use an unused output path. Rebuild checks selected schemas, strict raw/parsed
correspondence including rejected payloads, retained push records, executed
world truth and cumulative project accounting. Do not pool versions to rescue a
failed threshold or replace v0.1 outcomes. The later page must show hypothesis,
all prediction outcomes, and both a table and figure comparing duplicate rate,
exact-once completion and duplicate admission for every actor × toolkit in both
versions, with denominators, UNKNOWN values and technical validity coverage.


## r2 saved-envelope audit and clearance

Verify `freeze-r2.json` with the same offline verifier. The preserved parents are
`freeze.json` and `freeze-r1.json`; include all three manifests and every input
listed by the new freeze in any future reviewer package. r2 intentionally cannot
reuse or replace the original attestation. Historical starts keep their r1 provenance.
`revisions/r2/README.md` gives the saved field values and rule coverage gap.

Run from this v0.2 directory:

```sh
python3 -B rg_freeze.py verify --freeze freeze-r2.json
python3 -B rg_revision.py diagnose
python3 -B rg_revision.py clear
```

For the saved DNS envelope, `clear` creates `collection/clearance-r2.json` with
`status: UNKNOWN`, `cleared: false`, bound to the unchanged STOP, freeze and ledger
prefixes, then exits 2. It is idempotent and leaves the STOP and all ledgers intact.
There is no valid clearance/resume command for this DNS case under the supplied
rules. Do not alter saved bytes or use the generated-output clearance pathway.
A programme ruling and further recorded amendment must resolve it first.

These are the exact future attestation and collect command forms; they remain
blocked for this case, even after a fresh reviewer push. `RG_CLONE`, `RG_EVENT`
and `RG_COMMIT` must identify that future separate clone, server event and commit.
No values for those future external facts are invented here.

```sh
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT" --freeze freeze-r2.json
python3 -B "$RG_V02/rg.py" collect --cohort claude --freeze freeze-r2.json --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

The saved-byte rebuild excludes the unresolved DNS episode from model metrics
under `pending_programme_ruling_episodes`. Zero-usage 429 pauses continue to appear
under `pending_usage_limit_episodes`. No saved terminal or parsed record is edited.


## r3 DNS ruling, clearance and resume

Claude is the delegating reviewer. The r3 programme ruling makes a parseable
`is_error: true` Claude envelope containing `ENOTFOUND` a definite non-start only
when API duration is zero or absent, every usage token is zero, cost is zero and
`modelUsage` is exactly `{}`. Missing or nonzero accounting cannot qualify.
External activity and generated payload fields cannot qualify either. The exact
saved envelope is `fixtures/stopped-claude-raw.json`; its bytes remain unchanged.

The collector settles each new qualifying attempt at zero, saves its evidence,
and returns `status: "dns non-start pause"`. Run the same collect command again
to resume at that position with the identical prompt, schema and reservation.
DNS pauses have no subscription reset-time gate. Repeated DNS refusals create
new immutable dispatch records and pauses, never new model outcomes. Usage-limit
pauses retain their existing reset gate. Independent analysis counts DNS events
under `operational_events.dns_nonstarts` and lists pending registrations under
`pending_dns_nonstart_episodes`; they are excluded from model failure metrics.

`python3 -B rg_revision.py clear-r3` records the current STOP's clearance in
create-once `collection/clearance-r3.json`, bound to the r3 freeze, original STOP,
request and saved dispatch hashes. The old settlement is already zero; an
append-only `recognize-nonstart` event adds its new disposition. The reservation
is restored only immediately before a resend. The original STOP, failed terminal,
parsed response, dispatches, r2 UNKNOWN clearance and ledger prefixes remain
unchanged. The active resumed episode uses the fixed separate directory
`collection/resumes/r3/episodes/claude-s00-notification-r50-check/`.
Clearance is idempotent and does not itself contact a model or attest a push.

ECONNRESET, timeouts and other explicit uncertain network failures end their
episode without a resend, and collection continues. Three consecutive transport
failure episodes create a durable STOP; success or another non-transport terminal
breaks the sequence. The sequence is reconstructed from saved terminals across
invocations. Missing usage retains its monetary hold. Identity, external activity,
accounting and resource violations still stop immediately. Later STOP-r2/STOP-r3
records cannot reuse this historical clearance. There is no automatic retry for
an uncertain transport failure.

Verify the active freeze and recorded clearance without provider calls:

```sh
python3 -B rg_freeze.py verify --freeze freeze-r3.json
python3 -B rg_revision.py diagnose
python3 -B rg_revision.py clear-r3
```

For the reviewer, after pushing the exact package from a separate clone, set
`RG_CLONE`, `RG_EVENT` and `RG_COMMIT` to that clone, its fresh complete server
push record and pushed commit. `RG_V02` is defined above. These are execution
commands for the reviewer; the builder has not run either command:

```sh
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT" --freeze freeze-r3.json
python3 -B "$RG_V02/rg.py" collect --cohort claude --freeze freeze-r3.json --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

r3 attestation creates `push-r3.json` and `push-event-r3.json`. Every original
start still validates against its own pushed freeze; a new r3 push need not
predate old attempts. `freeze.json`, `freeze-r1.json` and sealed `freeze-r2.json`
are bound as parents. All changed r2 inputs have byte-exact witnesses under
`revisions/r3/originals/`. No scientific function or registered input changes.


## r4 saved-byte correction: API 400; collection blocked

The latest r3 dispatch is `resumes/r3/episodes/claude-s00-notification-r50-check/dispatches/0/1/raw.json`:
SHA-256 `32e37928e96f691d6345cdf4469aa10771ce8f062d7737b362b503f677fb2330`.
It reports API 400 rejecting top-level oneOf/allOf/anyOf in input_schema. The old
DNS is dispatch 0 and matches r3 correctly. The DNS programme ruling cannot clear
this different response. Current disposition is UNKNOWN and clearance false.
Changing that schema also conflicts with the requested identical-request resend;
a separate programme decision is required. Registered inputs and request bytes
remain unchanged. The r4 collect command below stops before provider construction,
preflight or model generation. Do not treat it as a cleared resume command.

`python3 -B rg_revision.py diagnose-r4` shows the actual response disposition.
`python3 -B rg_revision.py clear-r4` records the sealed UNKNOWN clearance and exits
2 intentionally; it is idempotent. `python3 -B rg_freeze.py verify --freeze freeze-r4.json`
verifies package inputs, all four parent hashes, stopped evidence and journal
prefixes. The guarded test report and diagnosis are in revisions/r4/.
The real 429 source is useful-core collection dispatch claude-s08-late-full/4-0000;
its raw metadata references exact sibling stdout/stderr files, preserved under
revisions/r4/real-429-source. The fixture adapter and source hashes are recorded.

For reviewer reference only, using the same RG_V02/RG_CLONE/RG_EVENT/RG_COMMIT
variables defined above, attestation would bind a fresh r4 server push. Collection
remains blocked under this package even after attestation. The builder runs neither:

```sh
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT" --freeze freeze-r4.json
python3 -B "$RG_V02/rg.py" collect --cohort claude --freeze freeze-r4.json --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

## r5: corrected provider schema and identical-prompt resume

The Claude action schema is now one closed object per toolkit without top-level
unions. Its only extra accepted combinations are cross-field combinations,
rejected by the unchanged strict validator. Local schemas/data, prompts, schedule,
report schema and original conservative reservations are unchanged. Live provider
compilation is UNKNOWN. See revisions/r5/README.md and provider-schemas.json.

Both historical dispatches are retained in resumes/r5; 0.rejected-request.json
preserves the original schema. 0.request.json changes only schema, keeping the
prompt, system and reservation identical. clearance-r5.json binds the final
freeze, STOP-r3, original STOP, raw and both requests. The 400 is recognized as
an operational non-start at zero cost; its reservation is restored only at
resend. Historical r4 UNKNOWN clearance remains unmodified. A new STOP-r5 blocks
future calls; r5 does not clear unrelated stops. Do not use an earlier freeze.

Safe reviewer checks (use unused output filenames):

```sh
python3 -B "$RG_V02/rg_freeze.py" verify --root "$RG_V02" --freeze freeze-r5.json
python3 -B "$RG_V02/verify_offline.py" --output /private/tmp/receipt-gap-r5-review.json
python3 -B "$RG_V02/rg_r5.py" --root "$RG_V02"
python3 -B "$RG_V02/rg_analysis.py" --root "$RG_V02" --output /private/tmp/receipt-gap-r5-review-analysis.json
```

rg_r5.py verifies the existing clearance idempotently; it makes no provider calls.
The reviewer performs the existing fresh server push workflow for the exact r5
package, then uses the RG_CLONE, RG_EVENT and RG_COMMIT variables defined above:

```sh
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT" --freeze freeze-r5.json
python3 -B "$RG_V02/rg.py" collect --cohort claude --freeze freeze-r5.json --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

The builder executes neither command. Original r1/r3 push records remain valid
only for their original saved calls. No model call may substitute for a missing
r5 attestation. Sibling inspection was read-only: bridge-or-bus/v0.2 passes
top-level anyOf for action and report; the other four requested siblings do not.
