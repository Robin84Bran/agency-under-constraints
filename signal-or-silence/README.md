# Signal or Silence

When should an AI judge say “unknown”? This study tests whether judges abstain
when visible evidence permits opposite answers, while still detecting breaches
from complete receipts. The protocol and D1 decisions came from Claude/Codex
agreement under [semi_autonomous.md](evidence/agreements/semi_autonomous.md).

## For a general reader

Hiding decisive history made Claude say unknown on 97.50% of records, compared
with 10.42% for Qwen and 37.50% for Llama under the original instruction.
Nevertheless, **all three failed the full registered test**, which also required
reliable detection, low false alarms and valid output on complete evidence.
Claude’s strict-format failures contributed to its misses. Explicit sufficiency
instructions produced no joint pass. These results concern repeated simulated
tasks and do not establish real-world safety or an internal reasoning mechanism.

## Results at a glance

The primary abstention contrast (truncated minus full) was Qwen −2.92 percentage
points, Llama +24.58 pp and Claude +97.50 pp. The respective 95% paired seed-block
bootstrap intervals, co-primary breach recall/false alarms, both duplicate
weightings, and every passed/failed forecast are in [RESULTS.md](RESULTS.md).
Both plain and explicit joint tests failed for every judge. P1 plain passed;
P1 explicit and P2–P5 failed as complete forecasts; P6 is retrospective only.
The secondary receipt contrast for Claude changed from 0 pp plain to +88.33 pp
explicit. This is **consistent with** instruction/presentation sensitivity;
the mechanism was not independently tested.

Collection is complete: **5,604 calls, 1,868 per judge**, zero reuse, zero missing
and zero transport failures. The settled ledger is **USD11.053392** (USD11.05
rounded). Local accounted model-call USD is zero; actual hardware/energy costs
are unavailable. [DEVIATIONS.md](DEVIATIONS.md) records D1: a reservation overrun
after the second Claude call led to a cost-control-only amendment, with no
scientific change or repeated call. The original overrun remains a scored
technical failure. Scientific acceptance is **UNKNOWN**: Claude primary F/R
validity is below the acceptance threshold and fresh-clone Claude review remains
pending. Post hoc diagnostics and questions are labeled separately.

Primary plain-instruction results below use trajectory weighting and 95% paired
source-seed-block bootstrap intervals. All cells failed; equal-evidence scores
and the false-alarm co-primary guardrails are reported in RESULTS.md.

| Judge | T−F abstention | F breach recall | R breach recall | F false alarms | R false alarms |
|---|---|---|---|---|---|
| Qwen 2.5 7B | -2.92 pp [-8.94 to +2.02 pp] | 61.67% [51.92–73.56%] | 32.50% [20.99–43.41%] | 15.83% [5.26–23.18%] | 0.00% [0.00–0.00%] |
| Llama 3.1 8B | +24.58 pp [+10.28 to +43.92 pp] | 74.17% [62.96–84.00%] | 94.17% [85.27–100.00%] | 46.67% [37.17–61.22%] | 57.50% [45.04–75.29%] |
| Claude Opus 5.5 | +97.50 pp [+95.94 to +99.12 pp] | 85.83% [80.18–91.75%] | 92.50% [85.85–98.04%] | 0.00% [0.00–0.00%] | 0.00% [0.00–0.00%] |

## Rebuild offline

Python 3.9+ and the standard library suffice. Retain all evidence, collection and
freeze files. No model, server, credentials, network or package installation is
needed. **Do not run collection again.** The first analysis already ran once;
retain its outputs and choose a new directory for every numerical rebuild.

```sh
python3 -B sos.py verify
python3 -B sos.py analyze --output analysis-rebuild-2
```

This delivery’s independent rebuild command is
`python3 -B sos.py analyze --output analysis-rebuild-1`.
Compare its `analysis/results.json` with root `analysis/results.json`, and its
generated `RESULTS.md` and `README.md` with `delivery/frozen-analysis/`.
The root Markdown contains expanded delivery prose and is intentionally distinct
from the frozen analyzer’s original short report. Byte comparisons and checksums
are recorded in [delivery/verification.json](delivery/verification.json).
**All three generated artifacts were byte-identical**, and both freezes passed
final verification. The numerical SHA-256 is
`0ac4d9486e96ac10c661b2bc951126bbb5bef356ace85caf4986543c646f6861`.
A second same-workspace execution does not satisfy the separate fresh-clone
review requirement. The full build/collection runbook is [RUN.md](RUN.md).

## File map

| Path | Contents |
|---|---|
| `RESULTS.md` | Primary/co-primary intervals, both weightings, secondary contrasts, predictions, D1, spend and limits |
| `PROTOCOL.md` | Frozen design, forecasts and acceptance criteria |
| `freeze.json`, `freeze-d1.json` | Original integrity manifest and cost-only amendment manifest |
| `DEVIATIONS.md`, `deviations/d1/` | D1 rationale, original backups and pre-amendment collection baseline |
| `config/`, `imported/`, `evidence/` | Frozen requests, selected views, certificates, source archives and agreements |
| `collection/` | All saved starts/replies, runtime identities, push attestations and append-only ledger |
| `analysis/results.json` | Complete frozen numerical results, intervals, support/null counts, decisions and historical census |
| `analysis-rebuild-1/` | Separate offline rebuild outputs |
| `delivery/frozen-analysis/` | Byte-exact original generated Markdown before delivery prose |
| `delivery/render_reports.py` | Post-analysis prose/table renderer reading saved results only |
| `delivery/verification.json` | Rebuild comparison and final integrity checks |
| `QUESTIONS.md` | Unchanged registered questions |
| `QUESTIONS-post-analysis.md` | Append-only post hoc questions |
| `PROJECT_STATE.md` | Frozen D1-era state; current state is recorded separately to preserve integrity |
| `PROJECT_STATE-post-analysis.md` | Current post-analysis outcome, evidence and pending gates |

No frozen analysis, prompt, response, question history or freeze is revised.
