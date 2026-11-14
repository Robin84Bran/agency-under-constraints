# Post-push usage-limit disposition — 2026-11-11

Delegating reviewer: Claude. This is an operational harness deviation in v0.2.
The reviewer's programme-wide decision treats an exact subscription usage-limit
refusal with status 429, error=true, all input/output/cache tokens zero and cost
zero as a definite non-start. The reviewer reported sibling incidents around
21:00 HKT with a 21:30 reset; this project itself has no saved Claude call.

A non-start produces no model observation and may later resend identical request
bytes. The implementation preserves each attempt and its prefix-bound start,
saves its complete raw transport envelope and a hashed pause record, settles
zero cost, and keeps the remaining reservation inside the existing episode hold.
It returns a clean durable pause, then resumes the same call after the reset.
Prior valid world events are replayed, never generated again. Partial calls with
any other error or uncertain output retain the original handling.

Operational counts are separate from model calls, usage and technical failures.
A paused episode is pending; predictions requiring it remain UNKNOWN. Frozen
operational denominators and all actual model observations remain unchanged.
The original real-envelope fixture retains its positive usage and its original
project-specific invalid-write disposition; it is never reclassified as a pause.

No original freeze, ledger, raw reply, episode record or push receipt is replaced.
The successor freeze binds the original freeze and original receipts. Revised
operational source bytes are explicitly listed; original versions are retained
and hash-checked. New dispatch requires a fresh pushed-commit attestation, while
old local starts retain their original freeze/push binding.

The locked prefix inspection found 1,020 local terminals, zero paid starts and no
STOP to clear. Thus no historical refusal or technical score required changing.
The clearance inspection is recorded, rather than deleting evidence or granting
a budget/time reset. All 1,080 original replay scores match on their original
scientific fields. Earlier failing test evidence is retained: the original byte
identity test correctly noticed the three operational modules had changed; it
now verifies their archived original bytes, with new behavioral regressions.
