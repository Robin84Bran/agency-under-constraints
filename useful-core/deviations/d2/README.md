# D2: saved Claude envelope disposition

Delegation is from Claude, the reviewer agent. Work is folder-local diagnosis,
code/tests/docs/freeze and recorded offline clearance. No model calls, network,
pushes or Git operations are part of this work. Collection/resume is a reviewer
command, not executed by this builder.

The latest retained STOP says `frontier identity mismatch`. Its last call is
`claude-s04-calm-full-2`: returncode 1, parseable result JSON, `is_error: true`,
`terminal_reason: api_error`, `api_error_status: null`, `modelUsage: {}`,
`num_turns: 1`, `stop_reason: stop_sequence`, all four token counters zero,
`total_cost_usd: 0`, `duration_api_ms: 0`, and result text reports ECONNRESET.
The claimed identity mismatch is a HARNESS BUG: no returned model identity is
present to contradict the requested model. It is not the exact 429 limit refusal
and must not be resent. There is no evidence of generated output in this reply;
we do not label it a model-caused error or claim ECONNRESET proves a non-start.
Under the reviewer's supplied boundary, a complete parseable provider API-error
result is an episode transport failure; genuine fatal transport uncertainty is
retained for missing/unparseable envelopes. This operational interpretation is
an explicit D2 deviation from A1's blanket paid-transport stop. Three consecutive
transport episodes still pause the cohort. The current history is 11 successful
Claude terminals followed by this one transport episode; no retry is permitted.

D2 preserves all 38,675 collection files at its boundary, the exact STOP, all
calls/terminals/accepted-dispatch hashes, both original freezes and D1 freeze,
and their journals/checkpoints. A frozen disposition plan supplies a two-file
read overlay, rather than rewriting the original parsed or terminal files.
The new freeze binds all three parent manifests, explicit changed inputs and
exact archived D1 versions. Science, prompts, schemas, schedule, request settings,
budgets/reservations, scoring and statistical functions stay unchanged.

Clearance retains STOP.json and creates d2-clearance.json tied to its exact hash,
frozen plan, baseline and retained journal prefixes. Only the one frozen ledger
stop may be cleared, with a new append-only clear-stop-d2 event and release of
the known terminal episode's unused future-call hold. Previously settled cost
and charged time are unchanged. A repeated clear command completes interrupted
appends without duplicating events. No generic STOP bypass exists. Full current
journals, retained prefixes, source evidence and checkpoint tails are validated;
legitimate subsequent appends remain allowed. D2 attestation precedes every new
start, while historical A1/D1 starts retain their original bindings. The first
Claude contract stays pinned to its original D1 identity and saved bytes.

Generated errors/refusals, exhausted structured generation, cap-length replies,
missing structured output and invalid schemas become episode model failures and
continue, including returncode 1 / is_error true. Absent modelUsage is UNKNOWN,
not a mismatch; actual conflicting model/effort, tools, input loss and financial
or reservation overruns remain integrity stops. Success accepts integer turns
1 or 2 with end_turn or tool_use and validates only structured_output, never
result prose. Exact zero-usage zero-cost 429 limit refusals keep D1's identical
request pause/resume semantics; capacity metadata is not consumed token usage.

Tests use verbatim saved stopping envelope/request/raw/terminal bytes and the
supplied real sibling envelope (also at the original /private/tmp path).
Generated shape variants are explicitly synthetic. An isolated full saved-boundary
copy verifies seal/clear/attest, independent replay/accounting, immutable STOP,
append growth, tamper rejection and reaching the next scheduled episode without
a model dispatch. Source-bound test logs/report retain unsuccessful development
runs as well as final evidence. See RUN.md for exact commands.
