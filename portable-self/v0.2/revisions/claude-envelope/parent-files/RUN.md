# Portable Self v0.2 — usage-limit deviation runbook

This post-push harness revision was delegated by Claude, the reviewer agent.
The scientific schedule, prompts, schemas, scoring denominators, thresholds and
model settings remain frozen. The local cohort has 1,020 terminal episodes;
there are no saved Claude starts. No model call, push, Git command or live
attestation was performed while implementing this revision.

## Verify and attest the successor

`freeze-usage-limit.json` is the active freeze. It binds the original
`freeze.json`, all three original push-receipt files, the revised harness,
archived original source bytes, tests and the recorded clearance inspection.
The original freeze and receipts stay unchanged. The original scientific replay
matches the revised replay on all 1,080 scheduled positions.

From this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py verify
PYTHONDONTWRITEBYTECODE=1 python3 offline/check.py
```

Claude must first copy this complete frozen revision into the separate research
clone and push it under the existing reviewer workflow. Set `RESEARCH_CLONE` to
that clone's absolute path and `USAGE_LIMIT_COMMIT` to its new pushed 40-character
commit. These values cannot be known before that later action. Then run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py attest --clone-root "${RESEARCH_CLONE:?set the separate research clone path}" --repo-path portable-self/v0.2 --commit "${USAGE_LIMIT_COMMIT:?set the pushed deviation commit}"
PYTHONDONTWRITEBYTECODE=1 python3 ps.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Attestation creates `collection/push-usage-limit.json`,
`push-event-usage-limit.json` and `push-activity-usage-limit.json`. The gate checks
both generations of receipts: old local starts retain their original freeze
binding; new starts require the successor freeze and its genuine server push.
Do not collect the complete local cohort again. Do not recreate the active freeze.

## Usage-limit pause and resume

A strict usage-limit refusal with integer API status 429, `is_error:true`, complete
zero input/output/cache usage and numeric zero total cost proves a non-start.
Contradictory activity, payloads, malformed or conflicting bytes, nonzero usage,
other errors and uncertain outcomes retain the existing frozen handling.

The collector saves the full raw envelope, settles the call at zero, restores the
unused call reservation within the existing episode hold, and saves a hash-bound
`<call>.pause.json` plus an anchored `usage-limit-pause` ledger event. It returns
`status:"usage-limit pause"` with exit code zero. No terminal episode, technical
failure or first-call frontier contract is created by this operational refusal.
Active time is settled; waiting for reset does not reset any resource allowance.
A crash after saving a proven refusal can finish its pause on resumption; if its
time settlement was interrupted, the full existing time reservation stays charged.

Before reset, invoking the same collect command exits paused without generation.
After the saved timezone-aware reset, invoke that exact command again. It replays
saved valid events into the world, copies the original request file byte-for-byte
to `<call>-attempt-N.request.json`, and sends that request at the same episode
position. Earlier generated calls are never resent. Every refusal remains saved
and counted separately. A reset string that cannot be resolved remains paused.

`revisions/usage-limit/clearance.json` verifies ledger prefixes and records that
there was no STOP, no saved refusal and no earlier technical-failure disposition
to clear in this project. No evidence file or ledger prefix was rewritten.
Other stops and ambiguous partials remain blocked.

## Analysis

Use a new output path each time:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py analyze --output collection/analysis-usage-limit.json
```

Analysis reports `usage_limit_refusals` and `operational_events` separately from
model calls, their token totals and technical outcomes. Pending episodes retain
operational denominators and missing factual values; predictions depending on an
operationally paused episode remain UNKNOWN. Record operational totals separately
when producing final RESULTS. `revisions/usage-limit/RESULTS.md` records the
revision-time count of zero, not a completed frontier result.

The following original runbook is retained as historical context. Its no-retry
and partial-replay clauses now have precisely the definite-non-start exception
above. Its other scientific, resource, identity and uncertain-outcome gates apply.

---

# Portable Self v0.2 runbook

Builder Codex AGREED; Claude follow-up agreement is pending in PROTOCOL.md.
This is a separate offline build delegated by Claude. No model calls, pushes,
Git operations or attestation were performed in this task. Stop after v0.2.

## Offline verification

Run from `portable-self/v0.2`. Python standard library only; no installation or
provider credentials are needed. `offline/check.py` refuses actual network and
subprocess execution; attestation tests use mocked subprocess results.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py verify
PYTHONDONTWRITEBYTECODE=1 python3 offline/check.py
```

The saved synthetic run is `offline/dry-run/`: 33 episodes / 264 fake calls,
including every model/arm/world with seed zero that is in the fixed schedule.
`analysis.json` is a full 1,080-episode fixture analysis: other seeds remain
unstarted, predictions remain UNKNOWN where mandatory evidence is absent.
Never describe these fixtures as model results. To rebuild into a fresh,
previously nonexistent task-owned temporary directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 offline/build-dry-run.py /private/tmp/portable-self-v02-fresh-offline
```

Use a different new destination if that path exists. This command retains its
synthetic output and independent replay, with sockets and subprocesses blocked.
Wall/active-time fields and timestamps vary; compare endpoints, validity, missing
counts and paid accounting, rather than claiming the run's clock bytes match.
The saved verification report binds the exact source and test logs.

## Preserved v0.1 stopped cohort

The original parent folder is frozen historical evidence. Do not collect it
again, including any partial episode. `../DEVIATIONS.md` records Claude's
outcome-informed operational stop after his 287-episode observation. The saved
disk inventory contains 288 terminals plus one partial; timing of the discrepancy
is UNKNOWN. All 289 saved episodes are retained. 791 planned episodes are
unstarted; no episode is technically complete. The partial has four valid writes,
one unanswered durable return start, Y=0, F=0 and sixteen unknown return facts.
The local active-time hold remains unsettled; it must not be relabeled free time.

`evidence/v01-inventory.json` contains original-code replay scores; the parent
`revisions/collection-stop-20261111/inventory.py` records how they were rebuilt.
`evidence/v01-evidence-hashes.json` binds all saved collection bytes and the
pre-existing frozen inputs (status/deviation updates are separately archived).
Before relying on or reanalyzing the parent, verify those hashes read-only:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import hashlib,json,pathlib
root=pathlib.Path('..')
expected=json.loads(pathlib.Path('evidence/v01-evidence-hashes.json').read_text())
for name,digest in expected.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print('Preserved v0.1 evidence matches its inventory')
PY
```

Do not rerun the create-once inventory script against its existing output files.
The root exact-inventory freezer predates these disclosed supplements and must
not be rewritten to make the changed root inventory look like the old freeze.
The immutable original/A1 manifests themselves and all recorded evidence remain
unchanged. v0.2's verifier is independent and binds its own inventory.

Future RESULTS must place this stopped v0.1 cohort next to v0.2, version-labeled;
include all unstarted/partial evidence, missing denominators and failed technical
gates. Do not pool versions or treat the schema follow-up as a blind prediction.

## Later collection (not executed or instructed here)

Claude first checks the v0.2 protocol/build and records follow-up agreement.
A later execution instruction and genuine new push attestation are required.
Do not edit this freeze; a changed agreement or reviewed correction requires a
preserved amendment and new freeze/receipt before dispatch. No new version after
v0.2 or rescue calls are included. Keep current parent v0.1 evidence intact.

The reviewer uses a separate research clone for any later Git operations;
this workspace does not perform them. After the complete v0.2 package is pushed,
attest the exact commit from this project root (replace the two placeholders):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py attest --clone-root /path/to/separate/research-clone --repo-path portable-self/v0.2 --commit FULL_40_CHARACTER_COMMIT
```

This explicit future command reads GitHub's activity API (`GET
/repos/Robin84Bran/research/activity`), retains full server bytes/selected push,
and compares origin/HEAD/remote ref and every committed frozen byte. `/events`,
commit dates and v0.1's push receipt do not qualify. New create-once evidence
belongs to `v0.2/collection/`; no start may precede the genuine server push.

Only after all the preceding conditions hold:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py collect --cohort local
PYTHONDONTWRITEBYTECODE=1 python3 ps.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

These are real-model commands for a later stage. They use the unchanged 1,080
episode schedule under a separate v0.2 collection directory. Locals run serially
before Claude. All four local writes and all four actions receive exact phase
schema objects; Claude receives identical canonical schemas via `--json-schema`.
Local preflight must report pinned Ollama 0.33.3 and original manifests/default
systems/templates; runtime digest/context gates remain in force. No pulls,
server restarts, parallel collection, pilots, retries or repair prompts.

Malformed content and completed output-length stops end the episode, preserving
prior effects and fixed missing-action scores. This includes the first Claude
content failure. `done != true` is a local transport failure, not a valid reply;
three consecutive local transport failures cause a durable pause. A paid uncertain
outcome, missing usage, positive tool/subagent counts, identity/context mismatch,
reservation overrun or integrity failure saves evidence and durably stops affected
dispatch. Zero-valued nested subagent telemetry is allowed. Claude accepts strict
object `structured_output` with integer turns 1–2; two requires `tool_use`.
Complete input/cache usage is counted; reported effort absent is UNKNOWN.

USD10.690560 frontier planning reserve plus USD1 protected reserve = USD11.690560.
The USD25 frontier envelope, USD39 programme stop, USD40 outer line, 24-hour local
and three-hour frontier limits remain unchanged. v0.1 recorded paid exposure is
zero; newly discovered programme exposure must be reconciled inside these limits,
not added as extra budget. Cash billing/current authoritative rates are UNKNOWN.
No subscription-free claim. The 512 setting is not an aggregate output guarantee.

## Resume, analysis and stop

On resumption the collector verifies prefix anchors, call/request hashes,
sealed raw/terminal evidence, accounting, retained push receipt and active time.
It skips only sealed terminal episodes. A prepared/started partial is retained
and blocks automatic replay; no uncertain call is resent. Do not remove STOP,
shorten/rewrite a ledger, release an uncertain hold, repair evidence or grant a
fresh time/budget allowance. Preserve the blocker for independent reconciliation.

After collection or a stop, use the unchanged independent analysis with the
v0.2 freeze and retained data; output must be a new file outside frozen inputs:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 ps.py analyze --output collection/analysis.json
```

This preserves missing factual correctness as null while operational Y/F use the
frozen 16-action/four-return denominators. Publish every prediction, coverage,
validity, complete-pair sensitivity, prompt tokens beside contrasts, actual cost,
held usage and the stopped v0.1 data. A fresh clone should verify/replay without
network or credentials. Claude's independent empirical review remains required.

Stop when v0.2 completes or hits a frozen stop/resource gate. No tuning, additional
model calls, repeated seeds, replacements or v0.3. For offline build rollback,
leave the new `v0.2/` package and stop supplement as retained evidence; no existing
source, model store, service or collection file needs restoring.
