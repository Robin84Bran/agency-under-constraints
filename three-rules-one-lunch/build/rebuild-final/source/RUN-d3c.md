# D3c runbook and real-envelope audit

11 November 2026. Requested by Claude, the delegating reviewer; Codex is builder.
Scope: this folder, harness repair and offline evidence only. No model calls,
network requests, pushes, Git operations, collection writes or STOP clearances.

`positive_count` traverses dictionary values and JSON arrays, treating numeric
integer/float leaves greater than zero as subagent activity. Zero-only statistics
are permitted. Booleans and text are not numeric counts. Existing server-tool
checks already reject positive counts; their strict integer/type, required-key,
missing-evidence and nonzero checks are retained, as are all other checks.

The fixture is an exact copy of the saved `claude-s000-central` call and terminal
files under `fixtures/d3c/`. Its raw-record SHA-256 is
`4783953ac1b9d226d1d6dd2d2048f1d5859fdc0ddb8c48831b87a28cbe4ee04f`.
Tests reproduce the old rejection using the preserved validator, accept the exact
raw record with D3c, and mutate the real reply to exercise the remaining guards.

Every Claude-path check in `trl_validation.py`, in execution order:

| Check | Real saved envelope / D3c result |
|---|---|
| Raw dictionary, integer returncode zero, no transport error | PASS: object, 0, absent error |
| Strict base64, UTF-8, one strict JSON object; no duplicate keys/nonfinite numbers | PASS: exact saved stdout decodes |
| Usage object and four nonnegative integer token categories | PASS: input 2, cache read 0, cache creation 1460, output 195 |
| Optional reported cost parses as finite nonnegative Decimal | PASS: 0.015588 USD = 15,588 micro-USD |
| Result type | PASS: result |
| Result subtype | PASS: success |
| is_error exactly false | PASS: false |
| num_turns integer 1 or 2 | PASS: 2 |
| Stop reason end_turn/tool_use; two turns require tool_use | PASS: tool_use |
| modelUsage object with exactly the pinned model key | PASS: claude-opus-5-5 only |
| Per-model usage is an object | PASS |
| Four per-model counts are integers matching aggregate usage | PASS: 2 / 195 / 0 / 1460 |
| Returned effort absent/default medium or explicitly medium | PASS: absent; actual returned effort remains UNKNOWN |
| permission_denials exactly an empty array | PASS: [] |
| No truthy deferred_tool_use | PASS: absent |
| No positive numeric subagent_stats leaf, recursively | PASS: every counter zero; previously FAIL solely because object was nonempty |
| No truthy tool_uses | PASS: absent |
| No truthy tool_calls | PASS: absent |
| Server usage object contains web_search_requests and web_fetch_requests | PASS: both present |
| Every server-tool count is integer zero | PASS: 0 / 0 |
| Per-model webSearchRequests equals zero | PASS: 0 |
| No truthy errors or safety_stops | PASS: errors absent, safety_stops 0 |
| Sum of disjoint input categories within reservation | PASS: 1,462 <= 2,368 |
| Accounted output <= 1,024 | PASS: 195 |
| Greater of planning cost and reported cost within reservation | PASS: max(9,748, 15,588) <= 32,512 micro-USD |
| structured_output is an object | PASS: cells object; result prose never substituted |
| Strict action: exactly cells; quota 3; each integer 0..47 or null | PASS: [0,19,38] |

No other always-present field triggers a stop. `safety_stops:0` is falsey;
`permission_denials:[]` matches exactly. Additional timing/session/terminal/speed
metadata, usage breakdowns and model metadata are not independent validator
checks. `maxOutputTokens:128000` describes model capacity; the checked actual
accounted output is 195. Thinking tokens (134) are included in the 195 output,
not added again. This audit establishes acceptance of this saved reply, not
advance certainty about future CLI replies or unreported effort.

The frozen harness-stopped rule is **SCORED_NO_RERUN**, under PROTOCOL.md sections
4 (failure policy), 5 (fixed endpoints) and 8 (saved-evidence repair, no replacement).
The valid reply was never executed by the simulator. Keep the terminal incomplete,
with one attempted call, no receipts, three technical and nine missing slots;
Y=0/12,000=0, H=0/12=0, coverage=0. All factual rewards remain null. Keep this
scheduled central episode in its fixed 20-episode Claude central denominator.
Do not execute its saved action retroactively, finish the episode, retry, replace,
or relabel the model response as malformed. `deviations/d3c/disposition.json`
records the cause, scoring, usage, settled cost and preserved evidence hashes.
The historical parse, FAIL contract, fatal terminal, STOP, ledgers and timers
remain byte-identical; the disposition is not a collection clearance.

The pre-change full suite had one failure and two setup errors because D3/D3b
tests imported later live collection state. `tests/historical.py` reconstructs
only the exact D3 scan inventory and its verified ledger prefix, and retrieves
historical source bytes by frozen hash. Updated historical tests use that
snapshot. The original failing report/log remain in `build/`.

Offline reproduction, from this directory, using fresh output paths:

```sh
python3 -B trl_test.py --out build/test-report-d3c-NEW.json
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d3c-NEW
python3 -B trl_freeze.py verify
```

The builder creates `freeze-d3c.json` once with `python3 -B trl_freeze.py freeze-d3c`.
It binds the exact D3b parent and all earlier freezes, five before-change baselines,
fixture, tests, disposition and new documentation/evidence. Scientific inputs,
accounting and analysis code are unchanged. No frozen artifact is rewritten.

This package records no resume decision and makes no collector/provenance or
clearance changes. Existing dispatch gates continue to block collection. Any
subsequent continuation must account for the retained integrity STOP and first-call
FAIL contract and bind subsequent starts to the reviewed package. D3b's transport
pause-clearance command cannot clear this integrity STOP.

Final verification: 178 offline tests pass, zero failures/errors/skips, with
zero model/network calls. The archived fake-study analysis rebuilds identically.
All 7,347 pre-existing collection and parent-freeze files retain their hashes.
