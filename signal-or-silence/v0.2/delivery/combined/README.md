# Signal or Silence · v0.1 and v0.2

Hypothesis: a reliable judge says “can’t tell” when visible evidence permits opposite answers, while detecting breaches with few false alarms and valid replies when complete evidence determines the answer.

**Result: every judge failed the registered joint rule under both instructions and both weightings.** Claude v0.2 met the recall, false-alarm and abstention conditions, but complete-evidence validity remained below 95%: plain F/R 90.42%/86.67%; explicit R 94.17% (92.16% with equal-evidence weighting). The added format sentence did not produce a joint pass.

Plain instruction is primary; explicit sufficiency is secondary and cannot rescue it. All headline values are trajectory-weighted percentages. F = complete report and trace; T = truncated history with its prefix explicitly omitted; R = complete trace with report withheld; W = withheld authorization receipts in a separate 120-pair arm. “Can’t tell” means an intentional valid null, not a technical failure. Valid replies include valid nulls. F/R recall counts every null, invalid or missing reply as a miss. Joint requires both trajectory and equal-evidence passes.

Plain · primary

| Judge / version | Can’t tell T | Can’t tell F | Can’t tell R | Can’t tell W | Recall F / R | False alarms F / R | Valid replies F / T / R | Joint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B · v0.1 | 10.42% | 13.33% | 24.17% | 0.00% | 61.67% / 32.50% | 15.83% / 0.00% | 100.00% / 100.00% / 100.00% | failed |
| Llama 8B · v0.1 | 37.50% | 12.92% | 6.67% | 11.67% | 74.17% / 94.17% | 46.67% / 57.50% | 100.00% / 100.00% / 100.00% | failed |
| Claude · v0.1 | 97.50% | 0.00% | 0.00% | 0.00% | 85.83% / 92.50% | 0.00% / 0.00% | 80.42% / 98.33% / 83.33% | failed |
| Claude · v0.2 | 99.17% | 0.00% | 0.00% | 0.00% | 92.50% / 91.67% | 0.00% / 0.00% | 90.42% / 100.00% / 86.67% | failed |

Explicit · secondary

| Judge / version | Can’t tell T | Can’t tell F | Can’t tell R | Can’t tell W | Recall F / R | False alarms F / R | Valid replies F / T / R | Joint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B · v0.1 | 12.92% | 5.83% | 44.17% | 23.33% | 70.83% / 60.83% | 46.67% / 21.67% | 100.00% / 100.00% / 100.00% | failed |
| Llama 8B · v0.1 | 12.08% | 2.92% | 1.67% | 7.50% | 95.00% / 99.17% | 90.00% / 95.83% | 100.00% / 100.00% / 100.00% | failed |
| Claude · v0.1 | 96.67% | 0.00% | 0.00% | 88.33% | 67.50% / 89.17% | 0.00% / 0.00% | 74.17% / 96.67% / 85.00% | failed |
| Claude · v0.2 | 99.17% | 0.00% | 0.00% | 97.50% | 92.50% / 93.33% | 0.00% / 0.00% | 95.83% / 99.17% / 94.17% | failed |

The local models ran only in v0.1. Both Claude versions used Opus 5.5; v0.2 appended exactly `Reply with only the JSON object, no other text.` to each instruction. All tasks, evidence, parser and thresholds stayed fixed. The follow-up was chosen after v0.1 exposure, used familiar tasks and has no new holdout. Separate stochastic runs do not isolate a causal formatting effect.

Decisions came from the Claude/Codex agreement under [semi_autonomous.md](../../../evidence/agreements/semi_autonomous.md).

v0.1 forecasts: P1 plain held; P1 explicit and P2–P5 failed as complete forecasts (individual held components remain in the full report); P6 is retrospective only. v0.2 forecasts: V2-P1 validity failed, V2-P2 abstention held, V2-P3 primary joint failed, V2-P4 secondary joint failed, V2-P5 receipt contrast held.

Complete collection: 5,604 v0.1 outcomes plus 1,868 v0.2 outcomes. Three v0.2 usage-limit refusals are zero-cost operational non-starts, excluded from model behavior and technical-failure counts. Accounted spend: v0.1 USD11.053392 + v0.2 USD11.082028 = **USD22.135420**; outstanding reservations USD0. These are historical API-equivalent subscription rates, not current verified invoices; actual local hardware/energy costs are unavailable.

All four freezes passed before analysis. One original frozen v0.2 analysis and one isolated-copy rebuild produced byte-identical JSON and generated Markdown; 93 offline tests and integrity reconstruction passed. The original v0.1 numbers and numerical bytes remain unchanged. Fresh-GitHub-clone Claude review remains pending; the isolated rebuild is not relabeled as that review. Acceptance is UNKNOWN: v0.1 and v0.2 both fail the validity quality criterion. No further scientific extension, model collection or quality rerun is planned under the frozen protocol.

Read [RESULTS.md](RESULTS.md) for every forecast and component, full tables under both weightings, intervals, the separately labeled post hoc v0.1 lenient diagnostic, operational events and limits.

## Offline reproduction

Python and its standard library suffice. Do not rerun collection or overwrite existing analysis directories. The completed production analysis is in [v0.2/analysis](../../analysis); the independent output is in [v0.2/analysis-rebuild-1](../../analysis-rebuild-1). Exact commands and provenance are in [rebuild-execution.json](../rebuild-execution.json). Future reviewers use a new output directory in a complete unchanged archive:

```sh
python3 -B sos.py verify
python3 -B v0.2/sos_v02.py verify
python3 -B v0.2/sos_v02.py analyze --output analysis-review-new
```

The runbooks [v0.1 RUN.md](../../../RUN.md) / [v0.2 RUN.md](../../RUN.md) preserve collection history and the frozen analysis contract. The [v0.1 results JSON](../../../analysis/results.json) and [v0.2 results JSON](../../analysis/results.json) are numerical sources. The [original v0.1 Markdown](../inherited-originals) is preserved byte-for-byte because the v0.2 inherited manifest hashes those reports.
