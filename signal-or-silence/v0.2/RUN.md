# Signal or Silence v0.2 runbook

Run every command below from the Signal or Silence project directory. Python
3.9+ and its standard library suffice. All new durable artifacts belong under
`v0.2/`. Leave v0.1, its freezes, collection, analysis and ledgers unchanged.
The historical wording in `v0.2/PROTOCOL.md` describes the drafting boundary.
Claude's `evidence/REVIEW-claude-20261111-v02-r1.md` records AGREED, including §5.
Claude is the delegating reviewer/operator. Codex implements and verifies this
harness deviation offline. Claude owns attestation and resumed collection.

## Post-push usage-limit deviation (11 November 2026)

`freeze-usage-limit.json` binds the original `freeze.json`, the original push,
the current harness/tests/runbook, archived parent inputs and the collection
baseline. Original freezes, v0.1 inputs, starts and receipts stay byte-identical.
The original v0.2 cost ledger is verified as a byte prefix; zero settlements and
subsequent reservations append. No new Git operation is required by this local
harness attestation; it does not claim publication or GitHub verification.

The programme-wide reviewer decision came from Claude, not Robin. A complete
envelope is a definite non-start only when `is_error` is true,
`api_error_status` is 429, all input/output/cache token counts and nested usage
are zero, `total_cost_usd` is zero, and the result is a usage-limit refusal.
Missing or ambiguous evidence retains the frozen handling. No parser, prompt,
model, effort, timeout, sample, accounting rate, or spending cap changes.

The harness saves the entire refusal envelope, records a durable `usage-limit
pause` under `collection/usage-limits/`, settles its hold at zero, and exits
successfully at the first refusal. It does not sleep or dispatch again during
that invocation. Before the stated reset, another invocation returns the same
pause before transport/authentication setup. After reset it sends the identical
saved request bytes at that position; earlier generated calls are never resent.
This project's calls are stateless; there is no conversation history to rebuild.
Unknown reset formats remain paused and require diagnosis; they never imply
permission to send. Continuation starts/receipts live under
`collection/continuations/<job-id>/`, leaving original evidence intact.
A crash with an unreceipted start or reservation remains uncertain and cannot
be resent. A saved proven refusal can reconstruct its pause and zero settlement.

The three original saved refusals were labelled `transport_failure`. The
clearance command re-dispositions them from saved envelope bytes and records the
exact receipt hashes and ledger prefixes before/after clearance. It appends
three zero settlements, preserving the original evidence and avoiding a fatal
three-failure stop. Clearance is idempotent and does not waive any other error.
The completed clearance is `collection/usage-limit-clearance.json`.

From the project directory, run these exact entry points (the freeze hash is
supplied in the handoff and in the freeze command output):

```sh
python3 -B v0.2/sos_v02.py clear-usage-limit
python3 -B v0.2/sos_v02.py attest-usage-limit --freeze-sha256 '<SHA-256 of freeze-usage-limit.json>'
python3 -B v0.2/sos_v02.py collect
```

Clearance has already been executed offline at handoff; the first command is a
safe idempotent check. Claude must run attestation before resumed dispatch; Codex
does not attest on Claude's behalf or invoke collect. The original push gate
continues to bind scientific starts to the original freeze. The additional
attestation binds the reviewed deviation bytes. `verify` checks both bindings,
the inherited manifests, immutable baseline records and ledger prefixes.

Offline checks and exclusive deviation freeze creation are:

```sh
python3 -B v0.2/sos_v02.py test
python3 -B v0.2/sos_v02.py integrity
python3 -B v0.2/sos_v02.py dry-run
python3 -B v0.2/sos_v02.py freeze-usage-limit
python3 -B v0.2/sos_v02.py verify
```

Analysis reports each limit refusal as an operational event in `results.json`
and `RESULTS.md`, including the count re-dispositioned from saved transport
failures. These refusals never become model behavior or model technical-failure
counts. Refused positions awaiting generation remain missing in the original
scheduled denominators. On completion the continuation's generated outcome
occupies its original position. All original statistical rules remain frozen.
The sections below document the original push and collection contract; the
specific non-start exception and deviation attestation above take precedence.

## Verify and publish the frozen inputs

```sh
python3 -B v0.2/sos_v02.py verify
python3 -B v0.2/sos_v02.py test
```

Use an isolated research clone for Git changes; do not change the RobinOS2
working tree or push from Codex. Claude must push the exact v0.2 freeze, its
entire manifest and all inherited project files listed in
`v0.2/evidence/inherited-inputs.json` before the first v0.2 model call. Include
v0.1 and D1 freezes and evidence unchanged. No runtime credentials belong in
Git. Preserve the actual pushed commit and GitHub server timestamp/evidence.
The recorder below is an offline operator attestation; it neither pushes nor
contacts GitHub and cannot independently establish the truth of supplied values.

After the successful push, record its real evidence exactly once:

```sh
python3 -B v0.2/sos_v02.py record-push --github-time '<actual GitHub UTC ISO-8601 server timestamp>' --commit '<actual 40-character pushed commit SHA>' --remote '<private research repository URL>' --source '<real GitHub server evidence URL or preserved receipt path>'
```

This creates `v0.2/collection/push.json` exclusively, binding the SHA-256 of the
exact `v0.2/freeze.json` bytes. GitHub time must follow the freeze, precede all
v0.2 starts and not be in the future. Never fabricate values or replace a saved
attestation. Collection rejects missing, mismatched or mistimed evidence before
transport construction, login checks or model invocation.

## Collection (Claude only)

After recording the push attestation, the exact collection command is:

```sh
python3 -B v0.2/sos_v02.py collect
```

No Ollama setup or local-model job is required. This dispatches the original
1,868 unique Claude jobs in their original relative order, 934 per instruction.
The sole scientific change is one byte-identical sentence appended to each old
instruction: `Reply with only the JSON object, no other text.` Payload bytes,
seeds, assignments, F overlap, witnesses and strict parser remain unchanged.
All v0.2 outcomes are new. IDs start with `v02-`; evidence IDs stay fixed.

The original `sos_collect.py` is loaded into an isolated module namespace.
Its serial dispatch, durable starts, raw receipts, usage parsing, failure
handling and ClaudeCLI implementation are reused. The v0.2 adapter supplies
D1-sized reservations and cumulative accounting. It does not modify v0.1 code
or global state. Claude Opus 5.5 / `claude-opus-5-5`, medium requested effort,
unchanged system prompt, stateless tool-disabled command, `--output-format json`
envelope and 420-second timeout are retained. No schema option or retry is
added. Seed remains recorded but unsupported by the original CLI. Returned
effort is UNKNOWN when absent; an explicit mismatch stops dispatch.

At execution only, the original transport reads the existing
`HONEST_AGENT_CLAUDE_BIN` setting from
`<WORKSPACE>/ANTresidency/Honest_Agent/v0.3.1/local.env` and checks
the existing Claude subscription login. Do not copy that file or credentials.
The offline builder never reads it or probes a provider. Runtime identity and
current invoiced price remain UNKNOWN at freeze.

Outputs are version-isolated: `v0.2/collection/starts/<id>.json`,
`v0.2/collection/calls/<id>.json`, `v0.2/collection/runtime-claude.json`,
`v0.2/collection/cost.jsonl` and an exclusive collector lock. Every request,
prompt/hash, reservation, seed, requested/returned model and effort, timestamps,
raw outcome and usage are preserved. The lock and synchronous transport permit
one collector and one call in flight.

## Rolling cumulative budget and stop behavior

The v0.1 settled baseline is USD11.053392, with 1,868 reservations and settlements
and zero open reservations. Its exact ledger bytes are frozen read-only inputs.
The v0.2 ledger contains only v0.2 events; its gates add the v0.1 baseline each
time. Before each model dispatch, prior spend + v0.2 settled/conservatively
charged spend + open reservations + proposed reservation must be <= USD39.
The absolute project cap stays USD40. The USD1 gap is not a billing guarantee.

Reservations use exact new-prompt UTF-8 bytes + 68 unchanged system bytes + 826,
10% margin rounded up to 64 input tokens, and 448 output tokens. Historical
API-equivalent rates stay USD4/20 per million input/output tokens; these are
subscription accounting rates, not a verified current invoice. Input maxima
are 2,560 plain / 3,136 explicit. Summed future reservations are USD33.520640;
with v0.1 spend, USD44.574032; with the former USD5 planning cushion,
USD49.574032. The all-jobs-maxima-plus-cushion test fails. The explicitly agreed
amendment replaces that up-front feasibility test with the rolling gate and
accepts the risk of an incomplete run. Initial operational headroom is
USD27.946608. Do not increase the cap or reduce allowances/sample size.

Unknown usage and failed chargeable attempts keep their entire reservation.
Known usage is saved before ledger settlement. Any token overrun, wrong model,
explicit effort mismatch, source/hash/certificate drift or invalid accounting
stops further dispatch. All failures remain evidence; no replacement call is
allowed. Three consecutive transport failures stop the batch. A budget stop
may leave the study incomplete and unaccepted.

Rerun the identical collection command to continue definitely unstarted jobs
under the unchanged freeze. Saved receipts, uncertain starts and reservations
without receipts are never resent. If `collector.lock` survives a crash, inspect
its PID and establish that the owner has ended before removing that task-owned
lock; never delete a start, receipt, ledger or freeze. After offline diagnosis of
a three-failure stop, record the cause and remedy, then use the same command:

```sh
python3 -B v0.2/sos_v02.py recover --reason '<concrete offline diagnosis and remedy>'
python3 -B v0.2/sos_v02.py collect
```

Recovery acknowledges only exact saved failure hashes and never retries them.
Other integrity or resource stops require investigation; recovery does not waive
them. There is one frozen v0.2 scientific attempt, no v0.3 and no quality rerun.

## Offline rebuild and later analysis

```sh
python3 -B v0.2/sos_v02.py verify
python3 -B v0.2/sos_v02.py test
python3 -B v0.2/sos_v02.py integrity
python3 -B v0.2/sos_v02.py dry-run
```

Integrity reconstructs all 1,440 candidates, truth checks, certificates,
selection, views and masks without modifying v0.1. Dry run dispatches all 1,868
jobs against an injected fake transport in a temporary fixture with sockets and
provider subprocesses forbidden, then checks a resume dispatches nothing. It
creates no scientific collection or real cost ledger. Postfreeze checks save
new reports under `v0.2/build/`; frozen reports are never replaced.

After real collection, frozen numerical analysis with exactly 10,000 paired
bootstrap replicates (seed 20261112) is:

```sh
python3 -B v0.2/sos_v02.py analyze
```

It exclusively creates `v0.2/analysis/results.json` and `RESULTS.md` in that
folder. It calls the original strict parser, observation, row construction,
replay policy, score, contrasts, receipt scoring and bootstrap functions.
It reports Claude v0.1 strict beside v0.2 strict; no local rerun is implied.
The separate post hoc v0.1 lenient diagnostic recovers exactly one legal object
surrounded by prose, keeps all original denominators/weights and the D1
integrity override, and receives no registered-pass label. Forecast failures
and their components, missingness, diversity, receipt outcomes and cumulative
accounting remain visible in the JSON. The original retrospective census is
retained by reference. Plain-plus-format is primary; the explicit secondary
result and receipt twist cannot rescue it.

For an independent fresh-clone offline rebuild, run the verify/test/integrity
commands in the clone, then analyze into a new directory and compare the exact
results JSON bytes with the first analysis:

```sh
python3 -B v0.2/sos_v02.py analyze --output analysis-rebuild-1
```

The fresh clone must contain both complete versions and saved attempts. Preserve
the clone provenance and byte-comparison evidence separately. Familiar tasks,
post hoc selection and the receipt twist's origin must be disclosed. Outcomes
are only consistent with categorical evidence sufficiency on this synthetic
benchmark. v0.1 failed validity permanently. Project acceptance is UNKNOWN
until collection completeness/quality, cumulative accounting, independent
rebuild, Claude review and later delivery/publication gates are satisfied;
a completed negative joint test can be accepted, an incomplete run cannot.

Preparation/freezing commands for the original authorized builder, already
performed at handoff, are `prepare`, `integrity`, `test`, `dry-run`, then `freeze`
through this same entry point. Preparation and freeze create files exclusively;
never rerun them to replace the existing registered artifacts.
