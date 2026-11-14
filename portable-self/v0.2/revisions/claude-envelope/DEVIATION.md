# Saved Claude envelope correction

Delegated by Claude, the reviewer agent, on 12 November 2026 HKT. This task
permits saved-byte diagnosis, a recorded harness correction, tests, a successor
freeze and offline STOP clearance. It excludes inference, model probes, Git,
pushes and live attestation. The scientific programme remains v0.2 and ends there.

The only saved Claude start is `claude-00-different-stable-discard-0`.
Its parseable CLI result reports `is_error:true`, `subtype:success`,
`terminal_reason:api_error`, `api_error_status:null`, `duration_api_ms:0`,
`modelUsage:{}`, zero input/cache/output usage and `total_cost_usd:0`.
Its result says `API Error: Can't reach the API server — check your internet or
DNS (ENOTFOUND)`. The harness stopped on `frontier identity mismatch`.
That attribution is a **HARNESS BUG**: an empty model map in a pre-generation
error is no contrary identity claim. The complete envelope and its explicit DNS
failure establish a pre-generation error; it is not genuine transport uncertainty.
It is also not the exact 429 usage refusal eligible for an identical resend.

The saved terminal, parsed error and every original episode byte remain intact.
Independent replay records the corrected diagnostic as a definite pre-generation
DNS error. This episode stays terminal, with no retry, replacement or additional
model failure attribution. Frozen operational denominators and unknown factual
values remain intact. The next unstarted episode can run after fresh attestation.

## Envelope dispositions

Generated replies (`input/cache usage > 0` or `output usage > 0`) with CLI errors,
refusals, max-token exhaustion or invalid/missing structured content end only the
episode. Error replies may omit modelUsage; a nonempty contrary model map still
violates identity. A valid success still needs pinned identity, strict object
content, complete usage and integer turns 1–2; two requires `tool_use`.
Zero nested tool/subagent telemetry is accepted; positive activity still stops.
Identity, effort, integrity, accounting, token reservations and cumulative resource
limits remain guards. The sibling's 1,024-token cap does not enlarge this project's
frozen 576-token output reservation or change its 512-token request setting.

An exact 429 usage refusal with complete zero usage and zero cost remains a clean
reset-gated pause and identical-request resend. Missing, null and empty model maps
are valid for this refusal. Model capacity metadata is not generated token usage.
Only the exact saved zero-generation DNS signature gets the terminal no-retry
operational disposition. Other unclassified errors remain blocked for review;
missing/malformed envelopes with no refusal evidence remain fatal uncertainty.

## Preservation and clearance

`before.json` binds the source freeze, original STOP, stopped episode, external
real-envelope fixture, and all three prefix-verified journals. `parent-files/`
preserves immediate predecessor source bytes; `fixtures/` preserves exact saved
bytes. Derivatives in tests are explicitly synthetic. `replay-comparison.json`
records equality of all scientific fields at every one of 1,080 positions.

`freeze-claude-envelope.json` binds both original freezes, both generations of
push evidence and all successor inputs. Attestation checks all these committed
bytes and requires a new genuine server push. Old starts must precede their
immediate successor freeze, including the original-to-usage-limit boundary.

`clear-claude-stop` verifies the successor and full saved replay before mutation,
creates a freeze-bound receipt, appends an anchored `clear-stop`, archives the
original STOP as `collection/STOP-cleared-claude-envelope.json`, and appends a
release of the unused settled episode reservation. Original ledger bytes remain
an exact prefix. No usage or active time is reset. The command is idempotent and
can finish an interrupted receipt/clearance/archive/release sequence. Collection
and analysis audit the clearance receipt and original evidence. A different or
later STOP is outside this clearance.

The recorded receipt is `collection/clearance-claude-envelope.json`; it is an
append-only operational artifact bound by its ledger event and successor freeze.
No live collection, new attestation or publication is part of this build.
