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

freeze-d1.json is the active create-once lineage, binding both unchanged parent
freezes, exact parent inputs under deviations/d1/parent-a1/, current sources,
fixtures and verification evidence. The original push receipt is preserved.
Existing A1 starts are restricted to the exact D1 baseline; new starts require
D1 and collection/d1-attestation.json. No new push is required for the delegated
local harness deviation. The local attestation has intentionally not been run;
Claude receives the exact command and owns subsequent dispatch.

Evidence: evidence/d1-tests.txt and evidence/d1-validation.json. All scientific
inputs/scoring/denominators and original local evidence remain unchanged.
Current builder model calls/spend: 0/USD0; runtime frontier outcome remains
UNKNOWN. RESULTS.md records operational status without inferring model outcomes.

Next: Claude runs od_freeze.py clear-usage-stop (currently a no-op), then
od_freeze.py attest-d1 and od.py collect --cohort claude from this directory.
RUN.md contains the complete commands, replay and recovery semantics.
