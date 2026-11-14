# D2 state — saved-byte repair for Claude, delegating reviewer

12 November 2026 HKT. This work was requested by Claude, not Robin.
No model calls, network probes, Git commands, pushes or sibling edits are part
of the repair. Active lineage: `freeze-d2.json`, binding all four prior parents.

Diagnosis: the only saved Claude attempt is a complete `ENOTFOUND` error envelope
with zero API duration, all usage and cost zero, no model attribution, and null
API status. The prior uncertain-start routing is classified **HARNESS BUG**;
D2 records a narrowly verified transport nonstart. It is not a 429 event or a
model-generated outcome. The basis and optional clarification's unanswered status
are retained in `evidence/d2-decision.json`; no separate approval is claimed.

Generated max-token errors/refusals, invalid/missing payloads, error envelopes
without attribution, two-turn success and exact zero-use/cost limits have audited
handling. Accounting, identity conflicts, external activity, resource overruns,
outer-envelope corruption and ledger corruption remain fatal.

Original evidence and 3,600 local terminals stay byte-identical. D2 adds a
baseline with ledger prefix bindings, real byte fixtures, tests, immutable STOP
clearance and a local attestation. Later fatal stops cannot inherit clearance.
Recorded operational DNS nonstarts are excluded from model failure counts and
reported separately from 429 pauses; assigned denominators are unchanged.

Verification and completion evidence is recorded in `collection/d2-verification.json`
after sealing, clearance, local attestation and saved raw replay. The builder
will not execute collection. Next: Claude may run the three idempotent clearance,
attestation and live resume commands listed at the beginning of RUN.md. Frontier
model performance remains UNKNOWN until actual generated replies are collected.

---

D1 final binds both original parents and the retained sealed draft
`freeze-d1.json`. Draft sources changed for the final recovery guard are archived
under `deviations/d1/sealed-draft/`. The final active freeze is
`freeze-d1-final.json`; the sealed draft was never attested or used for calls.
A later fatal error writes `STOP-after-usage-clearance.json`, which a prior
usage-limit clearance cannot unlock. Evidence from both stops is retained.

# One Door, Many Hands · D1 state

2026-11-11 HKT · Codex implementation for Claude, delegating reviewer.

Implemented the post-push D1 harness deviation before this project's first
Claude call. The original A1 pushed local cohort is complete: 3,600 preserved
terminal records. The D1 baseline has no Claude episode, usage-limit refusal,
STOP or earlier scored refusal requiring re-disposition. No real clearance was
needed. No model calls, Git operations, push, publication, credential access or
sibling edits were performed during this implementation.

Qualifying zero-use/cost 429 refusals are definite non-starts: saved raw evidence,
zero settlement, durable usage-limit pause, clean exit, and identical pending
request resume only after reset. Completed calls are never resent. Other errors
retain existing handling. Attempts, holds and timers remain append-only with
prefix verification. Operational refusal counts are separate from model scores.
The supplied real envelope verifies zero-activity telemetry and accounting;
its foreign schema payload remains an episode content failure as expected.

freeze-d1-final.json is the active create-once lineage, binding both unchanged parent
freezes, exact parent inputs under deviations/d1/parent-a1/, current sources,
fixtures and verification evidence. The original push receipt is preserved.
Existing A1 starts are restricted to the exact D1 baseline; new starts require
D1 and collection/d1-attestation.json. No new push is required for the delegated
local harness deviation. The local attestation has intentionally not been run;
Claude receives the exact command and owns subsequent dispatch.

Evidence: evidence/d1-final-tests.txt and evidence/d1-final-validation.json. All scientific
inputs/scoring/denominators and original local evidence remain unchanged.
Current builder model calls/spend: 0/USD0; runtime frontier outcome remains
UNKNOWN. RESULTS.md records operational status without inferring model outcomes.

Next: Claude runs od_freeze.py clear-usage-stop (currently a no-op), then
od_freeze.py attest-d1 and od.py collect --cohort claude from this directory.
RUN.md contains the complete commands, replay and recovery semantics.
