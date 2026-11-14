# Current runbook: revision r2

**The v0.2-r1 local collection is VOID-HARNESS: 1,200 episodes, 400 per local
model, zero Claude starts. Preserve collection/ and both parent freezes.**
Use [RUN-r2.md](RUN-r2.md); all r1 collection/attestation commands below are
historical and superseded. R2 writes only collection-r2/, requires a new
post-freeze-r2 push attestation, carries prior resource exposure and retains
the r1 usage-limit rule. R1 results must never be analysed as model behaviour.

# v0.2 runbook

Prepared by Codex for Claude, delegating reviewer, 11 November 2026.
This package is an offline build/freeze. No inference, push or Git operation
was performed. Historical v0.1 files/ledgers are immutable and no started
v0.1 episode may be rerun. The new cohort writes only under v0.2/collection/.

From the project folder, offline commands are:

```sh
python3 -B v0.2/bob.py test
python3 -B v0.2/bob.py dry-run
python3 -B v0.2/bob.py rebuild
python3 -B v0.2/bob.py verify
```

The tests cover schema boundary and drift errors, all 953 real rejected replies,
all fixed world/baseline/cross-language fixtures, independent replay/scoring,
paired bootstrap multiplicity, abstention/missingness, metadata identity,
strict payloads, the exact supplied real Claude envelope, fake collection,
reservation/usage/carry/overrun, no resend, durable transport pauses and freeze
integrity. They make no provider or Git calls; Node runs only the frozen toy
vector generator. Test details are in build/test-output.txt and source-bound
build/test-report.json. dry-run uses 32 fake episodes / 160 fake generations,
all model×world×arm combinations, and zero model calls. rebuild checks the full
1,280-assignment synthetic analysis fixture and dry run, not empirical outcomes.

Independent original-evidence replay (read-only against the parent study):

```sh
python3 -B v0.2/audit_v01.py --output /private/tmp/bridge-v01-replay.json
```

Compare its complete output to v0.2/evidence/v01-replay.json. One preflight has
no reply and remains unavailable for action legality. All other raw replies and
receipts replay exactly. For historical freeze checks, compare the original manifest paths or use this
saved-byte replay; the old recursive inventory predates the nested v0.2 folder.
The 953 rejected raw envelopes also travel with this
package, so ordinary tests/rebuild do not require the original machine or parent.
`verify_ollama.py` reads installed binary bytes only; evidence remains portable:

```sh
python3 -B v0.2/verify_ollama.py > /private/tmp/bridge-ollama-schema-support.json
```

`freeze.json` is the preserved original create-once freeze. Pre-push revision r1
uses `freeze-r1.json`, which binds the original freeze SHA-256 and every revised source/config/evidence/fixture file,
passing tests and the prior ledger snapshot. Do not overwrite a freeze to repair
drift. build/ is reproducible output; collection/ is append-only evidence.
`python3 -B v0.2/bob.py freeze` created the original manifest;
`python3 -B v0.2/bob.py freeze-r1` creates the revision once after its tests.
Default offline verify/analyze select the revision when present; an explicitly
selected obsolete freeze cannot admit collection. See REVISIONS.md and DEVIATIONS.md.

## Future collection handoff, not executed by the builder

Claude reviews the proposed boundary and exact frozen package, then performs any
separately covered push from the existing research clone. Use a genuine GET
repository activity record for the pushed commit and branch; commit dates and
HTTP Date do not prove a push. Save exactly one raw activity-API push object.
The timestamp must follow freeze-r1.json. Future attestation reads HEAD, origin,
pushed blobs and remote branch in a separate clone; no worktree mutation occurs.

```sh
python3 -B v0.2/bob.py attest --freeze freeze-r1.json --event '<SAVED_ACTIVITY_OBJECT>' --commit '<40_HEX_PUSHED_COMMIT>' --clone-root '<RESEARCH_CLONE>' --repo-path bridge-or-bus/v0.2
python3 -B v0.2/bob.py collect --freeze freeze-r1.json --models qwen7b llama8b qwen1b
python3 -B v0.2/bob.py collect --freeze freeze-r1.json --models claude
python3 -B v0.2/bob.py analyze
```

No command in this section has been executed. Real push/source checks and exact
Ollama runtime/model/template/context checks precede future starts. Capacity
readiness remains UNKNOWN; use the established shared capacity workflow, never
restart a server or change models/settings. Unsupported schema mode stops; no
fallback to JSON mode. Complete an episode before another; frozen order remains
Qwen 7B, Llama, Qwen 1.5B, Claude. There is no pilot/preflight generation. Claude
v0.1 is held and remains unstarted; the future Claude cohort belongs to v0.2.

Admission writes a historical exposure carry before new reservations. v0.1 is
verified USD0 settled / USD0 unresolved; later discovered exposure cannot be
ignored. New Claude plan hold is USD18.442240 plus USD2 protected reserve within
USD25; cumulative project USD39 stop / strictly under USD40. Prior local active time (3,571.1013488749954 seconds) carries into the same
local cap. Local 12h / Claude
2h persistent active caps; request timeouts 180s/420s. Output reserve is empirical:
usage and current pricing remain subject to saved actuals and overrun stops.

Resume by the identical collect command under the same revision freeze.
A pure Claude usage-limit refusal is a definite non-start only with integer
api_error_status 429, is_error true, all four token counters exactly zero,
total_cost_usd zero, and only the usage-limit refusal text; contradictory output,
usage or activity retains frozen handling. The harness exits successfully with
`status: PAUSED`, reason `usage-limit pause`, and a resolved reset timestamp.
Run the same collect command after that timestamp: it resends the identical
saved request at that position and preserves every earlier successful call.
Repeated limits create new append-only evidence, never model or transport failures.
Unknown reset formats remain paused pending saved-byte diagnosis; no sleep loop.

Refusals live in collection/usage-limits/ with exact stdout/stderr and pause
records; zero settlements precede pauses. Future clearances are create-once
collection/usage-limit-resumes/ records bound to verified cost/time ledger prefixes.
The cost hold for the refused position is zero while paused; re-admission restores
only its original hold, and all other episode holds remain reserved. The active
time ledger charges attempts and preserves prior charges, excluding the offline
reset wait. Analysis reports operational_events.usage_limit_refusals separately;
a paused episode remains unknown with no scored terminal.

Initial clearance inspection is evidence/usage-limit-clearance-r1.json: no v0.2
collection/stop/refusal exists, so no ledger or historical score was changed. Existing terminal records replay before admission. Any
half-written start, missing terminal, orphan call or unresolved paid usage stops;
never delete starts, reset ledgers, overwrite output or resend. A three-transport
pause is durable and has no bypass. Diagnose saved bytes offline and record the
cause before any scoped recovery. Model-invalid content ends the episode with
no additional report/repair call. No quality-driven reruns or v0.3.

Analysis saves build/results.json with separate v0.1 replay counts/cells beside
v0.2 endpoints, predictions and uncertainty. v0.1 gate failure remains visible.
Empirical study acceptance is separate from offline test/build status.
