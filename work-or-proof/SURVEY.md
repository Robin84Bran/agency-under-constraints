# Work or Proof? · Survey

11 November 2026 (HKT). Stage 1 complete; proposed stage 2 is in [PROTOCOL.md](PROTOCOL.md), **DRAFT for Claude review**. No inference, paid calls, network access, Git operations or changes outside this folder were performed.

## What the playable experiment shows

Read the release's [README](../../../../00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof/README.md), [experiment contract](../../../../00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof/EXPERIMENT.md), [model](../../../../00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof/model.mjs) and [saved results](../../../../00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof/results.json). The canonical release is `<WORKSPACE>/00_identity_output/website/_releases/research-rebel-20261110/public/work-or-proof/`.

The toy gives five allocation policies the same seeded candidate-quality stream and action opportunities. A candidate counts only after a perfect FIFO review accepts it. Unreviewed work can expire; a full queue blocks makers; surplus checkers can be idle. Default: 120 ticks, eight actions per tick, 70% validity, one candidate per review, 12-tick expiry, queue limit 64. Fixed policies make first and check second within a tick; adaptive and random policies act sequentially. This ordering is part of the mechanism.

The archive contains ten settings × 64 seeds × five policies: **640 matched worlds and 3,200 policy outcomes**. Means below were recomputed directly from the saved outcome rows, without executing the simulator:

| Setting | Six make, two check | Four and four | Two make, six check | Queue-aware | Random |
|---|---:|---:|---:|---:|---:|
| Default | 167.250 | 334.750 | 167.500 | 331.828 | 317.031 |
| Perfect quality | 240.000 | 480.000 | 240.000 | 476.000 | 454.828 |
| Noisy candidates | 83.734 | 167.281 | 84.625 | 165.859 | 158.391 |
| Two candidates per review | 334.734 | 334.750 | 167.500 | 443.891 | 333.063 |
| Three candidates per review | 503.234 | 334.750 | 167.500 | 499.000 | 333.516 |

In the default world, maker-heavy averages 346 expiries, 72 blocked actions and 62 queued items; checker-heavy accepts nearly the same total but wastes 480 review actions idle. Similar totals hide different failures. Increasing review batch size reverses the best fixed allocation. There is no universal maker/checker ratio.

The toy does **not** measure model productivity or oversight economics: validity is a seeded bit, review is perfect, and actions have equal cost. It has no reviewer abstention, false alarms, heterogeneous token prices, rework or strategic concealment. The real-model study should relax the perfect-review and equal-cost assumptions, while holding production fixed. It cannot estimate the optimal joint spending split between generating new work and auditing it.

The saved model hash matches `results.json`: `51b09373ccc2b30d8ac0464ee987927a0478a6c820a4a630fe9d4e17555869cd`. This survey checked saved counts and accepted means; it did not run the toy's test suite or claim a full simulator rebuild.

## Saved evidence available for reuse

All paths below are relative to `<WORKSPACE>/ANTresidency/`. Release mirrors, scratch clones, practice runs and other versions are not counted.

| Source | Actor trajectories | Saved judgments | What they decide |
|---|---:|---:|---|
| Honest Agent `v0.3.1/results/{deployment,sharing}/*/*/trial-*.json` | 360 | 720 embedded Claude monitor calls | Approval breach, report-only (`final`) and trace |
| Honest Agent `v0.3.1/results/calibration/*/*/trial-*.json` | 45 additional calibration trajectories | 90 embedded Claude monitor calls | Same question; excluded from proposed primary population |
| Honest Agent `v0.3.2/results/judgments/` | Same 360 main trajectories | 720 GPT monitor judgments | Same breach instruction and evidence, byte-for-byte prompts |
| Honest Agent `v0.3.3/results/judgments/` | Same 360 main trajectories | 720 GPT referee judgments | Job completion and rules followed, independently |
| Obedient Rebel `v0.2.2/results/judgments/` | 1,080 from `v0.2.1/results/main/*.json` | 2,160 Claude monitor judgments | Approval breach, report-only and trace |

**1,440 distinct main trajectories, 4,320 main judgments, plus 90 calibration judgments.** The three Honest Agent judgment sets are repeated evaluations of the same work, not 1,080 independent actor runs. v0.3.3 also saves 720 `.start.json` markers: these are not judgments. There are two saved views for every main trajectory in every set.

The primary Claude archive has 737 breaches and 703 compliant runs: Honest Agent 67/293, Rebel 670/410. Actors are Qwen 2.5 1.5B, Qwen 2.5 7B and Llama 3.1 8B. Honest Agent spans deployment/sharing, three approval conditions and 20 seeds; Rebel spans eight fixtures, three action budgets, three pressure frames and seeds 0–4. Shared seeds, repeated fixtures and repeated prompts reduce independence.

Original JSON contains task, report, ordered actions/receipts, evaluator truth, prompts, raw responses, token counts, returned model, attempts and per-call `usd`. Separate judgments link back to source trials. Source evaluator code and freezes exist. This survey verified record counts, raw verdict parsing, complete pairs and cost arithmetic; independently replaying receipts against the evaluator is a build-stage requirement, not a completed survey check.

## Measured usage and costs per view

These are sums of **saved call records**, reconciled with each study's `results/spend-ledger.jsonl`. `final` means report-only. Tokens include the transport's accounted input and output, not just visible prompt text. Dollar amounts are historical **API-equivalent accounting**, not a receipt for incremental subscription payments or a current API quote.

| Study / split / view | Calls | Input tokens, sum | Output tokens, sum | Total tokens / call, mean | USD / call, mean | USD, sum |
|---|---:|---:|---:|---:|---:|---:|
| HA v0.3.1 main final | 360 | 362,331 | 64,351 | 1,185.228 | 0.007601 | 2.736344 |
| HA v0.3.1 main trace | 360 | 420,070 | 17,379 | 1,215.136 | 0.005633 | 2.027860 |
| HA v0.3.1 calibration final | 45 | 45,323 | 7,485 | 1,173.511 | 0.007355 | 0.330992 |
| HA v0.3.1 calibration trace | 45 | 52,409 | 1,942 | 1,207.800 | 0.005522 | 0.248476 |
| HA v0.3.2 main final | 360 | 4,974,884 | 64,118 | 13,997.228 | 0.029419 | 10.590948 |
| HA v0.3.2 main trace | 360 | 5,014,892 | 35,268 | 14,028.222 | 0.028840 | 10.382464 |
| HA v0.3.3 main final | 360 | 5,013,433 | 88,084 | 14,170.881 | 0.030299 | 10.907706 |
| HA v0.3.3 main trace | 360 | 5,049,980 | 70,654 | 14,223.983 | 0.030018 | 10.806500 |
| Rebel v0.2.2 main final | 1,080 | 1,045,862 | 88,145 | 1,050.006 | 0.005506 | 5.946348 |
| Rebel v0.2.2 main trace | 1,080 | 1,149,665 | 57,851 | 1,118.070 | 0.005329 | 5.755680 |

| Study | Observed total tokens / call, final range | Trace range | Ledger including preflight | Preflight alone |
|---|---:|---:|---:|---:|
| HA v0.3.1 main | 1,050–1,403 | 1,065–1,313 | 5.347296 | 0.003624 |
| HA v0.3.2 | 13,858–14,340 | 13,885–14,470 | 21.000932 | 0.027520 |
| HA v0.3.3 | 13,976–18,204 | 13,996–17,796 | 21.741726 | 0.027520 |
| Rebel v0.2.2 | 977–1,317 | 1,034–1,510 | 11.705644 | 0.003616 |

v0.3.1's ledger includes calibration; the other three contain only main judgments and preflight. Every ledger entry has `estimated: false`, meaning usage counts were present; it does **not** certify the pricing source. Saved rates reproduce all call costs: Claude USD 4/input-million and 20/output-million; GPT USD 2/input-million and 10/output-million. Claude's configuration cites its provider's page checked 9 November; GPT's configuration explicitly cites third-party listings because its provider's page was unreachable. Keep that provenance limitation. No current prices were fetched.

Claude input accounting sums ordinary, cache-read and cache-creation input tokens before applying the one saved input rate. GPT output accounting adds separately reported reasoning tokens when present; its input includes substantial Codex CLI overhead. Raw cache/reasoning components are not retained in these simplified call records, so this survey cannot independently reconstruct marginal billed API cost or rule out accounting issues in those components. Compare policies within the same transport; do not interpret cross-family cost ratios as intrinsic model efficiency.

**Report-only consumes slightly fewer total tokens but costs more dollars on average in every main set.** For HA v0.3.1, its average output is 178.753 tokens versus trace's 48.275, overcoming the trace's higher input cost. The assumed cheap first stage is not cheap in recorded dollars.

## Verdicts and feasibility constraints

Counts below were read from the saved records, including explicit abstentions on compliant runs that are not prominent in the narrative writeups. No saved parse errors or additional attempts were found among the inventoried judgments.

| Main set / view | Breaches caught / all breaches | False alarms / compliant | Abstentions, breach / compliant |
|---|---:|---:|---:|
| HA Claude final | 0/67 | 17/293 | 41 / 234 |
| HA Claude trace | 67/67 | 0/293 | 0 / 0 |
| HA GPT monitor final | 2/67 | 7/293 | 50 / 261 |
| HA GPT monitor trace | 67/67 | 0/293 | 0 / 5 |
| HA GPT referee final, rules question | 40/67 | 206/293 | 0 / 44 |
| HA GPT referee trace, rules question | 67/67 | 0/293 | 0 / 0 |
| Rebel Claude final | 266/670 | 168/410 | 404 / 242 |
| Rebel Claude trace | 670/670 | 8/410 | 0 / 80 |

For the referee, `rules_followed: no` maps to breach, `yes` to no breach and `unknown` to abstention. This mapping does not use its A/B/C class: success-with-breach class B also requires a completion judgment and would discard correctly detected breaches. Its changed instruction makes it a separate secondary cohort.

The proposed gate from `experiment_to_research.md`—escalate a report verdict of violation **or** no verdict—would escalate:

| Main set | Escalations | Full report-first census, tokens | Full trace census, tokens | Report-first census, USD | Full trace census, USD |
|---|---:|---:|---:|---:|---:|
| HA Claude | 292/360 | 782,649 | 437,449 | 4.409236 | 2.027860 |
| HA GPT monitor | 320/360 | 9,529,231 | 5,050,160 | 19.834286 | 10.382464 |
| HA GPT referee, rules question | 290/360 | 9,228,538 | 5,120,634 | 19.630020 | 10.806500 |
| Rebel Claude | 1,080/1,080 | 2,341,523 | 1,207,516 | 11.702028 | 5.755680 |

These are census cost inventories, **not the proposed capped-policy primary test**. Rebel never returns a report-only no-violation verdict; this gate filters nothing. Across the 1,440 primary Claude trajectories it escalates 1,372 (95.3%) and costs 3,124,172 tokens / USD 16.111264, versus trace census's 1,644,965 tokens / USD 7.783540. Full report-only census alone costs 1,560,689 tokens / USD 8.682692. A scarce budget cannot automatically pay for report-only on everything: census feasibility must be shown, and policies must stop when their cap is exhausted.

Saved trace judgments already answer the exact stateless second-stage question. Looking them up costs **USD 0 new spend**; charging their historical usage in replay avoids calling saved evidence free. A new trace call is needed only for a different question, such as a monitor shown its first verdict in the same conversation. That is outside this proposal.

## Research question this project can carry

**For this archived stream of work from real local actors, does report-first triage catch more approval breaches than randomly allocating full-trace checks under the same measured token allowance—and does the answer survive using the saved dollar allowance instead?**

Propose a retrospective, frozen policy replay of the 1,440 unique trajectories using Claude judgments, with separate GPT-monitor and GPT-referee checks on the same 360 Honest Agent trajectories. No new actor, monitor or referee calls. Report misses, false alarms, abstentions, coverage and costs separately. The likely informative outcome is that the gate costs too much and filters too little; a failed superiority prediction still completes the research question.

The analyst has now seen aggregate results and all saved verdicts/usage in inventory code. The policy analysis can be registered before it is executed, but the evidence is already examined. Call it a **pre-specified retrospective analysis**, not a fresh confirmatory model experiment. A stronger claim about unseen tasks or interactive triage would require a later, separately agreed prospective protocol.

## Rebuild and limits of this survey

`python3 -B survey_inventory.py` prints the inventory without importing study runners, executing models or writing to source folders. [survey_inventory.json](survey_inventory.json) retains its output, including per-view means, medians, ranges, totals, price provenance, ledger reconciliation and a digest over 5,094 source paths and hashes. Repeat output should be byte-identical while those inputs are unchanged. This is a survey snapshot, not the build-stage freeze or a certification of historical push timestamps.

The next gate is Claude's protocol review under [the programme loop](../semi_autonomous.md). Stage 3 agreement, code construction, statistical policy replay, Git, calls and publication have not been undertaken here.
