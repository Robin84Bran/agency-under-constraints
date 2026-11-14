# r2 saved-envelope deviation

Claude is the delegating reviewer; Codex is the builder. This revision uses saved
bytes only, with no model calls, Git commands, pushes or real attestations.

The latest and only saved STOP is `collection/STOP.json`, dated
2026-11-11T15:59:40.179390+00:00. The only Claude call is position zero of
`claude-s00-notification-r50-check`. Its exact raw wrapper and dispatch copies
are retained in `saved/`, and `fixtures/stopped-claude-raw.json` is byte-identical.
Its return code is 1; is_error true; api_error_status null; all four token
counters zero; cost zero; modelUsage empty; terminal_reason api_error; stop_reason
stop_sequence; num_turns 1; result reports ENOTFOUND before API reachability.

The four supplied programme classes do not cover this saved envelope. It is not
MODEL-CAUSED (no saved generation usage), not USAGE-LIMIT NON-START (no exact 429),
and not GENUINE TRANSPORT UNCERTAINTY as defined (the envelope is parseable).
There is no evidence of an identity mismatch: the existing harness exits on the
return code before reaching its identity check. The stopping reply's formal
status is UNKNOWN, pending a programme ruling. No retry or clearance is inferred.
This gap is distinct from the demonstrated harness bugs below.

The audit proves a general harness bug: exit code 1 was fatal before inspecting
generated error replies, except one schema-error subtype. The collector and
independent replay now treat generated refusals, error_max_turns,
error_max_budget_usd, error_during_execution, schema rejection, invalid or absent
structured output, and output at this project's 512-token cap as episode failures.
This does not change the token cap to the sibling project's 1024 tokens.
Parseable generation evidence survives a wrapper exit error; a missing modelUsage
on generated errors is not an identity mismatch. An explicit conflicting model,
external activity, unknown accounting or reservation overrun still stops.
Valid success with num_turns 2 remains accepted. An exact zero-cost, zero-usage
429 without modelUsage still pauses and resends identically after reset using r1.
Zero-generation errors outside that rule remain stopped and are excluded from
model metrics pending a programme ruling. No existing terminal or parsed evidence
is overwritten, and the saved DNS episode is never silently retried or scored as
a model failure by the revised analysis.

`preservation.json` binds both original freezes, all stopped Claude evidence,
the original STOP and original attestation, and full byte-prefix snapshots of
the cost, local-time and Claude-time ledgers. Verification permits append-only
extensions but rejects changes to any prefix or historical evidence.
`originals/` retains pre-r2 source bytes; original freezes and audits are untouched.
The new freeze inventories every changed r1 input and verifies its original witness.
Scientific world, prompts, schemas, schedule, score and statistical functions
remain unchanged; their existing byte/AST checks remain active.

The clearance command records eligibility under the new freeze in create-once
`collection/clearance-r2.json`. For this saved DNS envelope it records UNKNOWN and
cleared false, leaves the STOP, terminal, holds and ledgers untouched, and exits 2.
A future programme ruling requires a recorded additional amendment, never editing
this frozen result. For eligible generated content failures, clearance verifies
the stopped raw bytes, content-only rejection and settlement before appending a
release of unused future reservations. The historical STOP itself is never deleted.
A subsequent fatal failure gets its own `STOP-r2.json` and cannot reuse clearance.

A future reviewer push and attestation are separate actions. The r2 attestation
creates `push-r2.json` and `push-event-r2.json`, preserving original push records;
the collector and independent analysis validate each historical start against
its own original pushed freeze. A new push is not required to predate old calls.
The DNS STOP blocks collection even if a fresh r2 attestation exists.
