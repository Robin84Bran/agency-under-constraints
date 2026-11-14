# Bridge or Bus? v0.2 · RUN-r2

Current revision: r2, requested by Claude, the delegating reviewer agent.
**All 1,200 r1 local episodes are VOID-HARNESS: Qwen 7B 400, Llama 8B 400,
Qwen 1.5B 400; zero Claude starts.** No behavioural/scientific results may be
computed from collection/. Preserve every byte there and in freeze.json and
freeze-r1.json. Original build outputs are archived in evidence/r2/parent-build/;
any archived r1 empirical analysis is also VOID-HARNESS.

All commands below run from this v0.2/ directory. Offline verification:

```sh
python3 -B bob.py test
python3 -B bob.py dry-run
python3 -B bob.py rebuild
python3 -B bob.py verify
```

The builder created freeze-r2.json once with `python3 -B bob.py freeze-r2`
after final source-bound tests. Never recreate/overwrite a freeze to repair drift.
R2 binds both parent manifest hashes, VOID incident evidence, source, derived
schema inputs, tests and cumulative resource exposure. R2 currently has zero
model calls. Local live grammar enforcement and capacity readiness remain UNKNOWN.

The future reviewer supplies a genuine saved repository activity-API push object,
the pushed 40-hex commit and the separate research clone path. The push timestamp
must follow freeze-r2.json, and exact pushed bytes must include all three freezes
and the frozen source inventory. These commands were not executed by the builder:

```sh
python3 -B bob.py attest --freeze freeze-r2.json --event '<SAVED_ACTIVITY_OBJECT>' --commit '<40_HEX_PUSHED_COMMIT>' --clone-root '<RESEARCH_CLONE>' --repo-path bridge-or-bus/v0.2
python3 -B bob.py collect --freeze freeze-r2.json --models qwen7b llama8b qwen1b
python3 -B bob.py collect --freeze freeze-r2.json --models claude
python3 -B bob.py analyze
```

Attestation, runtime metadata, requests, starts, raw replies, calls, episodes,
ledgers, transport pauses and usage-limit evidence all go to collection-r2/.
The current analysis loader reads only r2, discloses r1 excluded counts and keeps
v0.1 historical replay separate. Original push receipts cannot admit r2.
A current post-r2 attestation plus existing runtime/identity/context/capacity and
accounting gates are still mandatory. No model/settings changes, JSON-mode
fallback, pilot generation, provider call for validation, or v0.3 extension.

R2 repeats the frozen 1,200 local + 80 Claude schedule in its own directory,
without pooling or selecting by r1 outcomes. Prompts, world rules, strict
validators, endpoints, predictions, sample sizes and usage-limit policy remain.
R2 canonical action/report schemas are 2,220 / 369 bytes. Conservative local
context bounds are 7,991 (Llama) / 7,992 (Qwen), below unchanged 8,192. Claude
plan hold USD19.179520 + USD2 reserve = USD21.179520 < USD25. Programme USD39
stop / strictly under USD40 remains. The 12h local cap carries 4,843.353130412996
seconds from v0.1 + VOID-HARNESS r1; frontier cap remains 2h, timeouts 180s/420s.
Known historical spend/unresolved holds are zero; actual billing remains UNKNOWN.

For a pure Claude usage-limit refusal, integer api_error_status 429, is_error
true, all four usage counters exactly integer zero, zero total_cost_usd and only
the exact refusal text establish a definite non-start. Save stdout/stderr and
pause evidence, settle the refused position at zero, leave remaining holds,
create no terminal/model failure, and return PAUSED. Run the identical Claude
collect command after the recorded reset time. Prefix/hash checks restore only
the original slot hold and resend only the saved pending request. Earlier
successful calls/history are never resent; repeated refusals remain operational
events. Unknown reset stays paused; any nonzero/missing/contradictory usage or
output retains conservative handling. Usage-limit wait time is not active time.
See REVISIONS.md for the unchanged exact boundary.

Resume other clean progress using the same collect command and freeze. Missing
terminals, orphan/partial starts, altered saved bytes or unresolved paid usage
stop without resend. Three transport failures remain a durable pause. Diagnose
saved bytes offline; never delete starts, clear stops, reset ledgers or overwrite
outputs. Model-content errors terminate an episode without a repair/report call.
The builder ran only offline checks and made no model, Git or push operations.
