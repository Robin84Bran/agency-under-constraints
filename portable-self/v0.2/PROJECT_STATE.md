# Portable Self v0.2 — Claude envelope correction

12 November 2026 HKT. Delegated by Claude, the reviewer agent. Scope is offline
saved-byte diagnosis, harness correction, tests, successor freeze and exact STOP
clearance. No model calls, Git commands, pushes or live attestation in this build.

Diagnosis: HARNESS BUG. The saved Claude envelope has is_error true,
terminal_reason api_error, api_error_status null, duration_api_ms 0, empty
modelUsage, complete zero usage/cost, and an explicit ENOTFOUND DNS message.
The old decoder incorrectly called this an identity mismatch. It proves a
pre-generation DNS error, not the exact 429 refusal eligible for resend.
The terminal stays sealed, with no rerun or replacement. Independent replay
changes only the error diagnosis: all scientific fields match at 1,080 positions.

Generated errors/refusals/max-token and invalid/missing structured output now end
only the episode; valid two-turn tool_use success and nested zero counters pass.
Exact 429 zero-usage pauses retain identical-request reset-gated continuation.
Identity conflicts, positive activity, unknown accounting, frozen resource limits
and genuine uncertain transport still stop. No model setting or scientific change.

Verification: 139 offline tests, including exact stopped-envelope and supplied
real-envelope bytes, labeled derivatives, cohort continuation, no replay of the
terminal, successor lineage/attestation, crash recovery and idempotent clearance.
The network/subprocess denial guard blocks real model, Git and network execution.
Source logs and saved replay comparison are under revisions/claude-envelope/.

Active freeze: freeze-claude-envelope.json; both predecessor freezes, original
source snapshots and both receipt generations remain bound and unchanged.
The offline clearance receipt is collection/clearance-claude-envelope.json;
the ledger anchors it and retains the old ledger bytes as an exact prefix.
The original STOP is archived as collection/STOP-cleared-claude-envelope.json.
Every original episode byte and active-time allowance is retained.

There are 1,020 local terminal episodes and one terminal Claude episode;
59 Claude episodes remain unstarted, beginning claude-08-stale-remap-keyed.
Fresh successor push and attestation remain pending; RUN.md has exact clearance,
attest and resume commands. Do not collect locals or replay the DNS episode.
Stop after v0.2; no new cohort, tuning, replacement or v0.3.
