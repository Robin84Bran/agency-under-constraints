# D1 · Cost-control-only amendment

Agreed by Codex (builder) and Claude (reviewer) on 11 November 2026, after the
original collector stopped, under `evidence/agreements/semi_autonomous.md` and
Robin's standing pre-approval of up to USD40 per project. Robin's specific
approval of D1 was not sought because it was not required.
No model calls, git commands, network access or writes outside this project are
part of preparing D1. The existing Codex D1 claim covers the work; the shared
claim/log is left untouched under the project-only write restriction.

Original `freeze.json` exact-byte SHA-256:
`09e07d27f622d4470fe8c4a6910e819cdbd892913c391c9297f4a72212c1a0a8`.
It is preserved verbatim. `freeze-d1.json` links to that hash and hashes each
changed/new D1 file. Pre-D1 code/runbook/state copies and 7,477 original
start/call/push hashes plus the exact ledger prefix are retained under
`deviations/d1/`. Neither saved calls nor the original freeze are rewritten.

## What happened and why

Qwen 7B and Llama 8B each completed all 1,868 scheduled calls. The first Claude
call used 1,252 input / 43 output tokens (USD0.005868). The second, explicit
instruction, episode `HA/sharing/qwen1.5b/granted/trial-33.json`, R view, used
1,429 input / 77 output tokens (USD0.007256). It exceeded the original 1,282
measured input maximum. The collector saved and settled the call, then stopped
exactly as frozen. Total Claude accounted spend is USD0.013124.

The historical maximum came from different requests. The original prompt-size
allowance omitted the CLI's hidden input, whose Honest Agent v0.3 observations
were median 544 and maximum 826 tokens over 995 calls (source preserved in
`config/cost_basis.json`). A historical total-input maximum was insufficient
for the longer explicit instruction. This is a reservation-estimation failure,
not grounds to reject, replace or resend either observation.

## Measurement and changed bounds

`sos_d1.measure` enumerates every frozen Claude job, including both instructions,
without dispatch, tokenization services or external files. It measures exact
UTF-8 bytes; canonical request-envelope bytes are also recorded for audit. Only
the unchanged prompt is sent on stdin; request model/effort/seed metadata is not
added again as visible text. The unchanged system prompt contributes 68 bytes.

| Instruction | Jobs | Maximum prompt bytes | Maximum canonical request bytes | Maximum input reservation |
| --- | ---: | ---: | ---: | ---: |
| plain | 934 | 1,328 | 1,565 | 2,496 |
| explicit | 934 | 1,887 | 2,124 | 3,072 |

Both longest prompts are F view of
`HA/sharing/qwen1.5b/pending/trial-21.json`; IDs and every per-job bound are
recorded in `config/d1.json`. The largest visible prompt + system is 1,955 bytes;
adding the empirical hidden maximum gives 2,781 before margin.

For each request, input reservation is
`64 * ceil(1.10 * (prompt_utf8_bytes + 68 + 826) / 64)`.
The visible input allowance uses one token per UTF-8 byte, avoiding an optimistic
characters-per-token estimate. Exact Claude tokenization remains **UNKNOWN**:
there is no offline Claude tokenizer here, and hidden input may change. This
measures the real worst visible request bytes, not a claimed exact billed-token
maximum. Output reservation becomes `64 * ceil(1.10 * 393 / 64) = 448`.
Both margins are prospective reservation allowances; no prompt, output limit,
sampling or CLI setting is changed. Overruns remain observable stop conditions.

At the unchanged USD4 input / USD20 output per million token rates:

- Plain reservations: USD15.393024; explicit: USD17.699328.
- All 1,868 planned reservations: **USD33.092352**.
- Including unchanged USD5 planning reserve: **USD38.092352 < USD39**.
- Keeping the two actual settlements and reserving only the remaining 1,866
  Claude jobs: USD33.067332, or **USD38.067332** including USD5.

The operational stop remains USD39 and the absolute cap USD40. No cap, rate or
planning reserve is relaxed. Unknown/failed chargeable attempts retain their
reservations. Actual spend above the stop still blocks further dispatch.

## Integrity and resume changes

The frozen `config/collector.json` and `config/requests.json` remain byte-identical.
The new `config/d1.json` is a cost overlay, recomputed from the frozen bytes on
verification. The collector still validates all original request hashes and
reservation metadata before applying this overlay. Only four previously frozen
files change: `sos.py`, `sos_collect.py`, `sos_freeze.py`, and `RUN.md`. New D1
code/tests/documents and project state are included in the amendment manifest.
All other original frozen files must match their original checksums, and new
unlisted code/config/evidence files are rejected by the existing inventory rule.

D1 bounds cannot be used until `freeze-d1.json` verifies and a NEW
`collection/push-d1.json` attests its exact hash, linked original hash, real
GitHub server timestamp, commit and source evidence. No attestation is invented
by this amendment. Claude must push the complete D1 manifest and retained
collection evidence, then record the actual push with `record-push --deviation D1`.
The original attestation still precedes every pre-D1 start; D1 attestation must
follow D1 freeze and precede every D1 start. New starts identify D1; existing
starts retain the original freeze hash.

Only the exact hashed pre-D1 cost-overrun receipt is acknowledged for resumption,
provided its observed usage fits the new bounds and its model/effort are valid.
It remains a saved observation with its historical integrity flag and actual
settlement. All saved calls are skipped; uncertain starts/reservations are never
resent. A new overrun or any different integrity failure still stops and stays
stopped. The D1 baseline makes prior evidence changes detectable on every verify.

Resume after Claude's push and new attestation:
`python3 -B sos.py collect --models claude`.

## What did not change

Prompts, system instruction, request payloads, seeds, model identities, effort,
sampling, sample membership/order, reuse cutoff, source evidence, ground truth,
analysis, predictions, denominators, pass rules and acceptance criteria remain
exactly as frozen. Original analysis/statistics/import/preparation code is
unchanged. No saved output is edited or used to select a different sample or
scientific rule. Both Claude observations remain in their original files and
will not be sent again. No inference, git, network or publication occurs here.

## Verification

The full offline suite is run before D1 freeze. New fake-transport tests verify
the measured full-plan bounds, missing-attestation block, original attestation
preservation, invalid D1 timestamp/manifest rejection, unrelated scientific drift
rejection, exact saved-call preservation, larger prospective bounds, new-start
provenance and durable stopping on a new overrun. Exact run counts and results
are retained in append-only `build/postfreeze_test_report*.json` reports.
