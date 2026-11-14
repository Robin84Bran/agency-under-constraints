# Portable Self v0.2

2026-11-11 HKT. Implementation delegated by Claude, the reviewer agent.
Scope: this folder's harness-only usage-limit deviation. No model calls, pushes,
Git commands or live attestation were performed in this task.

Implemented strict definite-non-start detection, saved refusal envelopes,
zero-cost settlement, durable clean pauses, timezone-aware reset gates, identical
request-byte continuation and mid-episode history replay. Refusal attempts appear
as operational events in analysis, never generated model failures. Other frozen
handling, budgets, time caps, schemas, prompts, order and scoring stay in force.

Reality verified: 1,020 sealed local terminals, zero Claude starts, no STOP file,
no blocked ledger and no saved refusal requiring re-disposition. Cost exposure
and unsettled calls are zero. All journal prefixes verify. All scientific score
fields match archived original analysis at all 1,080 schedule positions.
`revisions/usage-limit/clearance.json` retains the evidence and prefix hashes.

Verification: 125 tests pass under the network/subprocess denial guard, including
zero-usage 429, unchanged real Claude envelope and labeled payload derivatives,
first-call/mid-episode/repeated pauses, exact bytes, conservative crash recovery,
nonzero/ambiguous rejection, and successor attestation with old receipt retention.
Original frozen bytes are archived under revisions/usage-limit/parent-files/.

The active create-once freeze is freeze-usage-limit.json; freeze.json and all
original collection evidence remain intact. Its new push/attestation is pending.
Next: Claude reviews and pushes this exact revision in the separate research
clone, attests it, then runs only Claude collect. RUN.md supplies exact commands.
Reinvoke collect after any saved usage reset. No new cohort, tuning or v0.3.
