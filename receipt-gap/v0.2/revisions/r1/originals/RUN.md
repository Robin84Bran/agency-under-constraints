# Receipt Gap v0.2 · offline freeze and reviewer execution

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
python3 -B rg_freeze.py verify
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

Never rerun prepare/freeze or edit frozen inputs. `freeze.json` is create-once.
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
external activity, accounting, transport or resource failures are fatal. Invalid
model actions/reports, length stops and schema-output rejection end just their
episode, with no repair, retries, additional effects, replacement or report after
an invalid action. Every terminal trajectory is retained and scored. Missing usage
and uncertain starts retain holds and stop. Timers persist across resumes.

## Reviewer push, attest and collect

Copy the entire frozen v0.2 package, preserving its directory, into the separate
claimed research clone's `receipt-gap/v0.2`. Verify and run all offline tests from
that independent package. Include every file listed by `freeze.json` plus the
freeze itself in the later commit. Exclude production `collection/` outputs.
Keep all canonical collection here. No Git command runs against RobinOS2.

After the reviewer performs the fresh push, capture its full GitHub PushEvent or
repository activity-API push record. Set the three concrete handoff values below:

```sh
RG_V02='<WORKSPACE>/06_intelligence/AI_research/research/receipt-gap/v0.2'
RG_CLONE='<separate-research-clone-root>'
RG_COMMIT='<new-v0.2-pushed-40-character-commit>'
RG_EVENT='<absolute-path-to-new-full-server-push-record.json>'
python3 -B "$RG_V02/rg_freeze.py" attest --root "$RG_V02" --clone-root "$RG_CLONE" --repo-path receipt-gap/v0.2 --event "$RG_EVENT" --commit "$RG_COMMIT"
python3 -B "$RG_V02/rg.py" collect --cohort local
python3 -B "$RG_V02/rg.py" collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Attestation checks HEAD/origin/remote ref and every committed frozen blob. It
creates `collection/push.json` and exact-byte `push-event.json`; both are create-once.
The server push must follow the v0.2 freeze and precede every call. A v0.1 receipt
or stale push cannot open v0.2. No builder attestation exists yet.

Do not delete a STOP, receipt, start or terminal record. A new `collection/STOP.json`
blocks dispatch. Resuming the same collect command skips terminal episodes and
only runs definitely unstarted episodes. A partial episode never continues.
No change to v0.1 stops, data, charges, holds, timers, analyses or delivery files.

## Independent post-collection review

In the independent package, copy the saved v0.2 `collection/` outputs and run:

```sh
python3 -B rg_freeze.py verify
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
