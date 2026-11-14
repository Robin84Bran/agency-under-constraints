# Signal or Silence · survey

11 November 2026 (HKT). Builder: Codex; reviewer: Claude. Scope: programme stages 1–2 only. No inference, paid calls, Git commands, pushes, service access or publication occurred. This survey is retrospective and informed by the saved results.

## What the playable experiment shows

Source, read-only: `<WORKSPACE>/00_identity_output/website/_releases/research-rebel-20261110/public/signal-or-silence/`, specifically `README.md`, `EXPERIMENT.md`, `model.mjs` and `results.json`.

This is a deterministic failure-detector game, not an AI-monitor study. A healthy service sends a heartbeat every four ticks; loss and delay make silence ambiguous. Three policies receive identical arrivals: a fixed timeout, an adaptive timeout, and a conservative rule with an UNKNOWN interval. No policy observes service truth or undelivered packets. All policies initially say UNKNOWN before their first arrival, including the nominally binary baselines.

The saved batch contains 640 seeded worlds (ten settings × 64 seeds) and 1,920 policy outcomes. In the default setting:

| Policy | Healthy false-DOWN ticks | Healthy UNKNOWN ticks | UP during outage | Delay to DOWN |
|---|---:|---:|---:|---:|
| Fixed | 4.516 | 2.328 | 7.844 | 7.844 |
| Adaptive | 3.750 | 2.328 | 9.625 | 9.625 |
| Keep UNKNOWN | 2.047 | 4.797 | 7.844 | 23.844 |

UNKNOWN reduces false accusation but delays a positive failure judgment. Keep UNKNOWN never detects the twelve-tick outage in any of 64 worlds. Missing detection is `null`, not zero. Adaptation also trades errors: under 30% loss, adaptive false-DOWN time falls from 14.141 to 7.484 ticks while outage-UP time rises from 6.750 to 12.516. These are synthetic ticks, not production losses, model calibration or proof of an optimal policy. No common utility function ranks abstention, false alarms and missed failures.

## Saved real-model evidence

Canonical archives are under `<WORKSPACE>/ANTresidency/`; release mirrors and scratch copies are excluded. `survey_inventory.py` reads saved JSON only, imports no providers, and writes nothing itself. `survey_inventory.json` retains exact totals, ranges, missing-value counts and SHA-256 hashes of the measured records and ledgers. Rebuild inside this folder with `python3 -B survey_inventory.py > survey_inventory.json`.

`final` means report-only. Token means below are **measured per call**, including reported CLI overhead and the adapter's accounted output tokens. Dollar amounts are **historical API-equivalent accounting**, not cash invoices, current price quotations or estimates from prompt length.

| Archive / judgment | View | Calls | Mean input | Mean output | Mean USD/call | Total USD | Explicit abstentions |
|---|---|---:|---:|---:|---:|---:|---:|
| HA v0.3.1 · Claude breach monitor | final | 360 | 1,006.475 | 178.753 | 0.007601 | 2.736344 | 275 |
| HA v0.3.1 · Claude breach monitor | trace | 360 | 1,166.861 | 48.275 | 0.005633 | 2.027860 | 0 |
| HA v0.3.2 · GPT breach monitor | final | 360 | 13,819.122 | 178.106 | 0.029419 | 10.590948 | 311 |
| HA v0.3.2 · GPT breach monitor | trace | 360 | 13,930.256 | 97.967 | 0.028840 | 10.382464 | 5 |
| HA v0.3.3 · GPT referee, compliance field | final | 360 | 13,926.203 | 244.678 | 0.030299 | 10.907706 | 44 |
| HA v0.3.3 · GPT referee, compliance field | trace | 360 | 14,027.722 | 196.261 | 0.030018 | 10.806500 | 0 |
| Rebel v0.2.2 · Claude breach monitor | final | 1,080 | 968.391 | 81.616 | 0.005506 | 5.946348 | 646 |
| Rebel v0.2.2 · Claude breach monitor | trace | 1,080 | 1,064.505 | 53.566 | 0.005329 | 5.755680 | 80 |

All listed main calls have recorded input/output usage and USD, one recorded attempt, and parseable verdicts under the archived JSON extractor's tolerance for surrounding prose/fences. The importer must still distinguish explicit null from a missing key or invalid value; the archive's generic “no verdict” convention is insufficient for new work. Historical table parsing is not an instruction to count malformed future replies as intentional abstention.

HA v0.3.1 additionally has 45 calibration trajectories and 90 monitor calls, excluded from the main population:

| Calibration view | Calls | Mean input | Mean output | Mean USD/call | Total USD | Explicit abstentions |
|---|---:|---:|---:|---:|---:|---:|
| final | 45 | 1,007.178 | 166.333 | 0.007355 | 0.330992 | 35 |
| trace | 45 | 1,164.644 | 43.156 | 0.005522 | 0.248476 | 0 |

Thus the requested four versions provide **4,320 main judgments**, plus **90 calibration judgments**: 4,410 experimental calls, not 5,600 independent runs. The larger approximate figure in `experiment_to_research.md` also mentioned HA v0.3, which this survey does not add. The main population is only **1,440 distinct trajectories**: 360 HA deployment/sharing items, reused in three judgment studies, and 1,080 Rebel main items. HA has 67 breaches/293 compliant; Rebel has 670/410. Combined: 737 breaches/703 compliant. The actors are Qwen 2.5 1.5B, Qwen 2.5 7B and Llama 3.1 8B; they are not the archived frontier judges.

Relevant paths:

- HA v0.3.1: `results/{deployment,sharing}/<actor>/<condition>/trial-*.json` holds traces, truth, reports, embedded monitor verdicts and the monitor `calls` list. `results/calibration/` is separate.
- HA v0.3.2 and v0.3.3: `results/judgments/` holds new judgments on those same 360 HA trajectories. Exclude `.start.json` markers, which are not responses.
- Rebel v0.2.2: `results/judgments/` holds the monitor responses; source trajectories are `Obedient_Rebel/v0.2.1/results/main/*.json`. Practice runs are excluded.
- Each version has its own protocol, config, freeze, saved analysis and spend ledger. No archived analysis or freeze was changed. Survey hashes identify current bytes; they do not independently authenticate historical pushes or certify every historical freeze.

The four historical ledgers sum to **USD 59.795598**: HA v0.3.1 5.347296; v0.3.2 21.000932; v0.3.3 21.741726; Rebel v0.2.2 11.705644. They include calibration where present and four preflights. This is sunk spend in other studies; reuse costs this project **USD 0**.

Saved prices were Claude input/output USD 4/20 per million and GPT USD 2/10 per million. GPT's source config explicitly cites third-party listings and an unavailable first-party page. Its high input counts include substantial CLI context. The saved provider also accounts reasoning output where reported. These transports, prices and instructions differ, so the table cannot establish intrinsic model cost or a causal family difference. A trace can cost less than a report: HA Claude report answers were much longer.

## The question this project can carry

**When a monitor says UNKNOWN, is that response concentrated where the visible evidence really permits both a breach and a lawful history, or does it withhold a verdict despite decisive evidence?**

The free retrospective arm can locate abstention by source, view, actor, true breach, report confession/denial and report–receipt conflict. It cannot establish calibration merely by finding more nulls in report-only views. Ground truth about what happened and sufficiency of what the judge saw are distinct variables. The saved five GPT trace abstentions already motivated a post hoc conflict analysis; that observation is prior exposure, not a new prediction. The v0.3.3 referee changed instructions and asked two questions; use `rules_followed`, never the combined B class, for breach comparisons.

A prospective paired arm should hold the underlying episode fixed while withholding evidence. Certify ambiguity by constructing **two simulator-valid complete histories with opposite compliance truth and identical visible evidence**. Full traces provide decisive controls. Prefix truncation retains the final event while hiding earlier events; receipt withholding hides authorization outcomes. A second decisive control with the actor's report withheld tests whether mere missingness triggers blanket abstention. The protocol makes calibration and abstention-as-miss detection co-primary, keeping false alarms separate.

Repeated templates create many duplicate visible prompts. Coverage of 240 source trajectories must never be presented as 240 independent evidence patterns. Record exact prompt-equivalence groups and show equal-group-weight results alongside trajectory-weight results.

## Reuse from Work or Proof?

The sibling's approved protocol schedules Qwen 2.5 7B and Llama 3.1 8B on both views of the same 1,440 trajectories: 5,760 original local judgments plus 48 replay checks. Its eventual `work-or-proof/collection/` output is **not assumed complete or inspected here**. Import original responses only after checking source IDs, exact prompt hashes, model digests, settings and provenance; preserve replay checks separately. Missing outputs remain UNKNOWN with a reason.

Their arrival does not gate this study. They can enlarge the descriptive arm later at zero marginal inference spend. They cannot replace prospective judgments with changed evidence/instructions. Do not recollect the sibling's baseline stream and do not access its busy Ollama server in this stage.

## Recommendation and remaining uncertainty

Draft a free retrospective census plus a prospective, paired, code-certified insufficiency test on 240 source episodes, with a smaller receipt-withholding replication. Use Qwen 7B and Llama 8B first, then one fixed Claude-family replication. Estimate **about USD 10 incremental frontier API-equivalent spend**, subject to pre-freeze transport/price verification; hard operational stop USD 39, below the programme's USD 40 ceiling. Local inference consumes time and hardware despite zero model-call USD.

The unresolved issues are the number of distinct constructed evidence patterns, the exact eligible receipt-mask population after witness certification, present transport/pricing availability, and whether the local models can separate partial from decisive evidence. These are build/review gates and research questions, not reasons to invent results. No new verdict exists for this protocol.
