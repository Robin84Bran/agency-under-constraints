# Work or Proof? · Results

Collected and analyzed on 11 November 2026 (HKT) under [PROTOCOL.md](PROTOCOL.md). Numbers come from the unchanged frozen analyzer in [results/main/](results/main/). Items explicitly marked *post hoc* were chosen after seeing the results.

## For a general reader

When AI systems do work, how much effort should go into making it and how much into checking it? This study asks a narrower question: can a cheap local check direct an expensive check better than random selection? We took 1,440 saved task records, with 737 rule breaches, collected fresh Qwen and Llama judgments, and replayed saved frontier judgments under fixed budgets. At the primary budget, Qwen screening caught 67.84% of breaches versus 49.99% for random checking: a gain of 17.86 percentage points, with a 95% interval from 16.18 to 19.77. But even without a budget cap, Qwen screening missed 66 breaches that full frontier checking caught. Local checking alone falsely flagged 27% of compliant records with Qwen and 54% with Llama. These are results on familiar simulated tasks, with local computing supplied separately. They do not establish deployment safety or the best balance between producing work and checking it.

## Primary finding

At half the saved frontier trace-census token allowance, a Qwen 2.5 7B trace screen followed by frontier trace checking caught **499.99 of 737 breaches (67.84%)**, averaged over 256 orders. Random-share frontier trace checking caught **368.39 (49.99%)**. The gain was **17.86 percentage points (95% interval 16.18 to 19.77)**.

**The pre-registered primary superiority test passed.** Both interval lower bounds exceeded zero, both policies met the audit floor in every ordering, and final false-alarm rates stayed below 5% in each source. This is an allocation result on a fixed archive with local computing supplied separately. It does not establish a production safety guarantee or an optimal split between producing and checking work.

The trade-off appears in the uncapped census: Qwen LT used **1,102,365 frontier tokens** (32.99% fewer than C), but caught **671/737**, losing **66 catches**. Local trace checking alone raised 193 false alarms for Qwen and 382 for Llama on 703 compliant items. Qwen local-only caught 669 breaches, more than capped LT, but its 27.45% population false-alarm rate shows the cost of those extra flags. The capped allocation gain coexists with substantial screen errors.

## Integrity

- **Freeze.** All **5,187 registered files** matched before analysis. `freeze.json` SHA-256: `75e19187ace057a67afb72b45505d8b4cf419b25a3abf0302dbaab629ae07bf7`. The frozen code, prompts, settings, evidence and freeze were not changed.
- **Push and order.** [collection/push.json](collection/push.json) attests a push at **2026-11-11T04:11:53Z**, commit **63dd761** (`63dd76114c2adab2ae59d8e06220cbee56e5b234`). Its recorded source is the GitHub repository activity API. This offline delivery checks the saved operator attestation and its freeze binding; it does not independently query GitHub. The earliest saved local request start is **2026-11-11T04:12:28.652785Z**, **35.652785 seconds later**, from `collection/calls/*/*.start.json`. The frozen analysis checks every start against the push.
- **Population.** Receipt reconciliation passed: **1,440 distinct trajectories**, **737 breaches / 703 compliant**; HA 67/293, Rebel 670/410. All 2,880 primary Claude judgments and each separate 720-judgment GPT cohort reconciled to copied source evidence.
- **Calls.** **5,808 attempted / 5,808 completed**: 5,760 first judgments and 48 replays. **0 failed, 0 uncertain, 0 malformed replies**, no substitutions or inference retries. Runtime records identify Ollama 0.33.3 and both pinned model digests.
- **Replay.** Qwen **24/24** and Llama **24/24** raw replies were byte-identical; parsed verdicts were also **48/48** identical. Every source × view × actor stratum had 2/2 identical replies per model. This finite replay sample does not prove determinism.
- **Resources and spend.** Incremental model-call spend **0 USD**, with **0 new frontier calls**. Charged active collection time was **885.160 seconds** of the 43,200-second cap; first start to last finish was **886.524 seconds**. Hardware, energy and opportunity costs are unavailable, not zero. Replayed frontier tokens, USD and seconds below are historical accounting, not newly purchased calls.
- **Checks.** All **74 offline tests passed**; portable import/reconciliation passed. The exact command `python3 -B wop.py analyze --output results/main` completed. No Git, network or model calls were used for this delivery.
- **Question history restored.** Claude’s analysis brief requested post-analysis questions. They are now in the separate, unfrozen [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md). [QUESTIONS.md](QUESTIONS.md) has been restored to its exact registered bytes, checked against the original freeze. Root verification passes directly; no replacement freeze or staging workaround is needed.

Measured local collection resources (including both views; replay overhead is separate):

| Phase / model / view | Calls | Input tokens | Output tokens | Client seconds | New USD |
|---|---|---|---|---|---|
| calls/llama8b/final | 1,440 | 145,800 | 10,080 | 177.703 | 0.00 |
| calls/llama8b/trace | 1,440 | 251,435 | 10,080 | 252.933 | 0.00 |
| calls/qwen7b/final | 1,440 | 173,160 | 10,080 | 156.346 | 0.00 |
| calls/qwen7b/trace | 1,440 | 278,795 | 10,080 | 223.851 | 0.00 |
| replays/llama8b/final | 12 | 1,308 | 84 | 1.450 | 0.00 |
| replays/llama8b/trace | 12 | 2,383 | 84 | 2.034 | 0.00 |
| replays/qwen7b/final | 12 | 1,536 | 84 | 4.993 | 0.00 |
| replays/qwen7b/trace | 12 | 2,611 | 84 | 1.992 | 0.00 |

## Primary test: Qwen LT against X

The allowance is **822,482 frontier input-plus-output tokens**. Both policies see the same 256 shuffled orders. Breach clearance, abstention, technical failure and budget exhaustion each count as a miss. A provisional local accusation counts only if the final frontier verdict flags the breach.

| Endpoint | LT − X | Paired bootstrap 95% interval | Pass rule |
|---|---|---|---|
| Population recall | +17.86 pp | +16.18 to +19.77 pp | Lower bound > 0: passed |
| Breaches / 1,000 allowed frontier tokens | 0.159996 | 0.147268 to 0.174400 | Lower bound > 0: passed |
| Minimum model-audited items across orders | LT 1440; X 716 | — | Each ≥200: passed |

| Source | LT mean final FP / compliant | Population FPR | Bootstrap 95% interval | Audited-only FPR |
|---|---|---|---|---|
| HA | 0.00 / 293 | 0.00% | 0.00% to 0.00% | 0.00% |
| Rebel | 5.92 / 410 | 1.44% | 0.99% to 1.95% | 1.44% |

Both false-alarm guardrails passed. LT audits all items locally, so its audited-only and population FPRs coincide. An audit need not yield a final determinate verdict: budget-unresolved work can mechanically lower population false alarms, so verdict coverage and unresolved counts accompany these rates. The two endpoints rescale the same catches; they are not independent confirmations. Intervals use 2,000 paired source-stratified seed-block replicates and 16 orders per replicate, holding first local replies fixed. They measure conditional archive sensitivity.

Source recall-difference intervals were +12.67 to +26.10 pp for HA and +15.91 to +19.52 pp for Rebel. Leaving out each seed block in turn kept the pooled recall difference positive (17.64 to 23.37 pp). There are only five Rebel seed blocks; orders and repeated views add no independent trajectories.

## Every policy at the primary token cap

R checks reports with the frontier monitor; X checks a random trace prefix; T checks frontier reports and escalates positive/unknown replies; C is the full frontier trace census reference. L is a local trace census; LT/LR screen local traces/reports and escalate every result except explicit clearance. Frontier trace judgments replace screened accusations. At insufficient caps **C remains an infeasible reference**, not a funded competing policy.

Counts below are **means over 256 orders**, so may be fractional. The route archive retains integer counts for each ordering. Recall/FPR use all 737/703 items; a non-verdict is not a true negative.

| Policy | TP / 737 | Recall | FP / 703 | FPR | Audited recall / FPR | Precision | Clearance accuracy | Resolved / 1,440 |
|---|---|---|---|---|---|---|---|---|
| R | 140.03 | 19.00% | 97.05 | 13.80% | 36.09% / 26.22% | 59.06% | 62.43% | 273.13 |
| X | 368.39 | 49.99% | 4.01 | 0.57% | 100.00% / 1.14% | 98.92% | 100.00% | 679.30 |
| T | 186.84 | 25.35% | 2.18 | 0.31% | 96.53% / 1.18% | 98.85% | 96.02% | 357.40 |
| C | 737.00 | 100.00% | 8.00 | 1.14% | 100.00% / 1.14% | 98.93% | 100.00% | 1,360.00 |
| L · Qwen | 669.00 | 90.77% | 193.00 | 27.45% | 90.77% / 27.45% | 77.61% | 86.19% | 1,340.00 |
| LT · Qwen | 499.99 | 67.84% | 5.92 | 0.84% | 67.84% / 0.84% | 98.83% | 89.51% | 1,135.28 |
| LR · Qwen | 337.25 | 45.76% | 6.75 | 0.96% | 45.76% / 0.96% | 98.04% | 62.48% | 1,242.23 |
| L · Llama | 671.00 | 91.04% | 382.00 | 54.34% | 91.04% / 54.34% | 63.72% | 97.27% | 1,163.00 |
| LT · Llama | 395.25 | 53.63% | 4.29 | 0.61% | 53.63% / 0.61% | 98.93% | 99.22% | 783.63 |
| LR · Llama | 382.30 | 51.87% | 4.71 | 0.67% | 51.87% / 0.67% | 98.78% | 82.78% | 886.46 |

| Policy | TN | Miss: clearance | Miss: abstention | Miss: technical | Miss: budget | All abstentions | Budget-unresolved items | Screen flags → corrected FP |
|---|---|---|---|---|---|---|---|---|
| R | 22.47 | 13.58 | 234.31 | 0.00 | 349.08 | 484.84 | 682.03 | 0.00 → 0.00 |
| X | 306.89 | 0.00 | 0.00 | 0.00 | 368.61 | 39.83 | 720.87 | 0.00 → 0.00 |
| T | 161.66 | 6.72 | 0.00 | 0.00 | 543.43 | 20.78 | 1,061.82 | 0.00 → 0.00 |
| C | 615.00 | 0.00 | 0.00 | 0.00 | 0.00 | 80.00 | 0.00 | 0.00 → 0.00 |
| L · Qwen | 412.00 | 66.00 | 2.00 | 0.00 | 0.00 | 100.00 | 0.00 | 862.00 → 0.00 |
| LT · Qwen | 563.37 | 66.00 | 0.00 | 0.00 | 171.01 | 59.65 | 245.07 | 862.00 → 77.82 |
| LR · Qwen | 561.22 | 337.00 | 0.00 | 0.00 | 62.75 | 67.46 | 130.31 | 830.00 → 288.62 |
| L · Llama | 107.00 | 3.00 | 63.00 | 0.00 | 0.00 | 277.00 | 0.00 | 1,053.00 → 0.00 |
| LT · Llama | 381.09 | 3.00 | 0.00 | 0.00 | 338.75 | 43.03 | 613.34 | 1,053.00 → 158.79 |
| LR · Llama | 413.45 | 86.00 | 0.00 | 0.00 | 268.70 | 46.96 | 506.57 | 763.00 → 147.20 |

A corrected false alarm is a provisional local accusation on compliant work replaced by an explicit frontier clearance. Final frontier abstention remains unresolved.

| Policy | Local calls | Frontier calls | Escalation requests | Frontier tokens: in / out | Local tokens: in / out | Combined tokens | Unused cap |
|---|---|---|---|---|---|---|---|
| R | 0.00 | 757.97 | 0.00 | 741,260.90 / 80,351.05 | 0.00 / 0.00 | 821,611.95 | 870.05 |
| X | 0.00 | 719.13 | 0.00 | 784,035.55 / 37,548.26 | 0.00 / 0.00 | 821,583.81 | 898.19 |
| T | 0.00 | 738.50 | 360.31 | 761,291.25 / 59,397.64 | 0.00 / 0.00 | 820,688.89 | 1,793.11 |
| C | 0.00 | 1,440.00 | 0.00 | 1,569,735.00 / 75,230.00 | 0.00 / 0.00 | 1,644,965.00 | infeasible |
| L · Qwen | 1,440.00 | 0.00 | 0.00 | 0.00 / 0.00 | 278,795.00 / 10,080.00 | 288,875.00 | 822,482.00 |
| LT · Qwen | 1,440.00 | 716.93 | 962.00 | 780,483.03 / 41,059.24 | 278,795.00 / 10,080.00 | 1,110,417.27 | 939.73 |
| LR · Qwen | 1,440.00 | 702.69 | 833.00 | 777,817.66 / 43,782.77 | 173,160.00 / 10,080.00 | 1,004,840.44 | 881.56 |
| L · Llama | 1,440.00 | 0.00 | 0.00 | 0.00 / 0.00 | 251,435.00 / 10,080.00 | 261,515.00 | 822,482.00 |
| LT · Llama | 1,440.00 | 716.66 | 1,330.00 | 782,369.57 / 39,173.77 | 251,435.00 / 10,080.00 | 1,083,058.34 | 938.66 |
| LR · Llama | 1,440.00 | 721.43 | 1,228.00 | 782,923.28 / 38,650.25 | 145,800.00 / 10,080.00 | 977,453.53 | 908.47 |

| Policy | Local seconds | Historical frontier seconds | Historical frontier USD | Local tokens / item | Local seconds / item | TP / 1,000 consumed frontier tokens |
|---|---|---|---|---|---|---|
| R | 0.00 | 5,031.39 | 4.572065 | 0.00 | 0.000000 | 0.170429 |
| X | 0.00 | 4,449.49 | 3.887107 | 0.00 | 0.000000 | 0.448396 |
| T | 0.00 | 4,747.38 | 4.233118 | 0.00 | 0.000000 | 0.227668 |
| C | 0.00 | 8,910.33 | 7.783540 | 0.00 | 0.000000 | 0.448034 |
| L · Qwen | 223.85 | 0.00 | 0.000000 | 200.61 | 0.155452 | — |
| LT · Qwen | 223.85 | 4,501.27 | 3.943117 | 200.61 | 0.155452 | 0.608597 |
| LR · Qwen | 156.35 | 4,364.79 | 3.986926 | 127.25 | 0.108574 | 0.410484 |
| L · Llama | 252.93 | 0.00 | 0.000000 | 181.61 | 0.175648 | — |
| LT · Llama | 252.93 | 4,439.59 | 3.912954 | 181.61 | 0.175648 | 0.481107 |
| LR · Llama | 177.70 | 4,487.21 | 3.904698 | 108.25 | 0.123405 | 0.465328 |

Reservations are 1,403 report tokens, 1,510 trace tokens, and 2,913 for T before its first stage. Routing reserves before observing realized cost and stops frontier requests at the first failed reservation. Local censuses continue afterward. Zero-consumption frontier yield for L is undefined (—), not infinity. Combined tokens are an accounting sensitivity, not hardware-equivalent computing.

## Full censuses

| Policy | TP / 737 | FP / 703 | Recall | Verdict coverage | Escalation share | Frontier tokens | Savings vs C | Lost catches vs C | Fits half cap? |
|---|---|---|---|---|---|---|---|---|---|
| R | 266.00 | 185.00 | 36.09% | 36.04% | 0.00% | 1,560,689.00 | 5.12% | 471.00 | no |
| X | 737.00 | 8.00 | 100.00% | 94.44% | 0.00% | 1,644,965.00 | 0.00% | 0.00 | no |
| T | 711.00 | 8.00 | 96.47% | 94.44% | 95.28% | 3,124,172.00 | -89.92% | 26.00 | no |
| C | 737.00 | 8.00 | 100.00% | 94.44% | 0.00% | 1,644,965.00 | 0.00% | 0.00 | no |
| L · Qwen | 669.00 | 193.00 | 90.77% | 93.06% | 0.00% | 0.00 | 100.00% | 68.00 | yes |
| LT · Qwen | 671.00 | 8.00 | 91.04% | 94.44% | 66.81% | 1,102,365.00 | 32.99% | 66.00 | no |
| LR · Qwen | 400.00 | 8.00 | 54.27% | 94.44% | 57.85% | 973,909.00 | 40.79% | 337.00 | no |
| L · Llama | 671.00 | 382.00 | 91.04% | 80.76% | 0.00% | 0.00 | 100.00% | 66.00 | yes |
| LT · Llama | 734.00 | 8.00 | 99.59% | 94.44% | 92.36% | 1,524,395.00 | 7.33% | 3.00 | no |
| LR · Llama | 651.00 | 8.00 | 88.33% | 94.44% | 85.28% | 1,398,354.00 | 14.99% | 86.00 | no |

Savings describe each policy at its own full-census recall, including any lost catches; they are not savings at guaranteed equal recall. Report triage can spend more than a trace census because it pays for both stages.

Qwen LT escalates 66.81% of the census and loses 66 catches. Llama LT escalates 92.36% and loses 3. These are distinct screening trade-offs; Llama is the registered secondary replication and does not replace Qwen as primary.

## Separate frontier-dollar cap

These policies are replayed separately at **3.891770 USD** historical API-equivalent allowance. Dollar reservations are 0.011900 for reports, 0.011584 for traces, and 0.023484 for T. Token routing is not relabelled as dollar routing.

| Policy | TP / 737 | Recall | FP / 703 | Resolved | Historical USD used | Frontier tokens | Unused USD |
|---|---|---|---|---|---|---|---|
| R | 118.94 | 16.14% | 82.35 | 231.90 | 3.882930 | 697,792.32 | 0.008840 |
| X | 368.01 | 49.93% | 4.01 | 678.57 | 3.882961 | 820,710.08 | 0.008809 |
| T | 170.91 | 23.19% | 2.00 | 327.17 | 3.874450 | 751,108.86 | 0.017320 |
| C | 737.00 | 100.00% | 8.00 | 1,360.00 | 7.783540 | 1,644,965.00 | infeasible |
| L · Qwen | 669.00 | 90.77% | 193.00 | 1,340.00 | 0.000000 | 0.00 | 3.891770 |
| LT · Qwen | 492.22 | 66.79% | 5.85 | 1,125.21 | 3.883075 | 808,989.61 | 0.008695 |
| LR · Qwen | 328.27 | 44.54% | 6.61 | 1,225.60 | 3.883181 | 800,173.74 | 0.008589 |
| L · Llama | 671.00 | 91.04% | 382.00 | 1,163.00 | 0.000000 | 0.00 | 3.891770 |
| LT · Llama | 392.17 | 53.21% | 4.28 | 778.41 | 3.882845 | 815,191.68 | 0.008925 |
| LR · Llama | 380.04 | 51.57% | 4.66 | 882.56 | 3.882847 | 816,915.56 | 0.008923 |

## Source and actor breakdowns

These use the pooled primary token cap and its routes, rather than resetting the allowance for each subgroup. Actor labels describe who generated the work, not the monitor. Same-family associations are descriptive.

| Source | Policy | Breaches | TP | Recall | Compliant | FP | FPR | Verdict coverage |
|---|---|---|---|---|---|---|---|---|
| HA | R | 67 | 0.00 | 0.00% | 293 | 8.94 | 3.05% | 12.50% |
| HA | X | 67 | 33.38 | 49.81% | 293 | 0.00 | 0.00% | 50.14% |
| HA | T | 67 | 10.54 | 15.73% | 293 | 0.00 | 0.00% | 26.43% |
| HA | C | 67 | 67.00 | 100.00% | 293 | 0.00 | 0.00% | 100.00% |
| HA | L · Qwen | 67 | 63.00 | 94.03% | 293 | 2.00 | 0.68% | 72.78% |
| HA | LT · Qwen | 67 | 47.08 | 70.27% | 293 | 0.00 | 0.00% | 88.65% |
| HA | LR · Qwen | 67 | 44.89 | 67.00% | 293 | 0.00 | 0.00% | 87.88% |
| HA | L · Llama | 67 | 39.00 | 58.21% | 293 | 149.00 | 50.85% | 60.00% |
| HA | LT · Llama | 67 | 34.37 | 51.30% | 293 | 0.00 | 0.00% | 57.77% |
| HA | LR · Llama | 67 | 27.19 | 40.58% | 293 | 0.00 | 0.00% | 71.09% |
| Rebel | R | 670 | 140.03 | 20.90% | 410 | 88.11 | 21.49% | 21.12% |
| Rebel | X | 670 | 335.02 | 50.00% | 410 | 4.01 | 0.98% | 46.19% |
| Rebel | T | 670 | 176.30 | 26.31% | 410 | 2.18 | 0.53% | 24.28% |
| Rebel | C | 670 | 670.00 | 100.00% | 410 | 8.00 | 1.95% | 92.59% |
| Rebel | L · Qwen | 670 | 606.00 | 90.45% | 410 | 191.00 | 46.59% | 99.81% |
| Rebel | LT · Qwen | 670 | 452.91 | 67.60% | 410 | 5.92 | 1.44% | 75.57% |
| Rebel | LR · Qwen | 670 | 292.36 | 43.64% | 410 | 6.75 | 1.65% | 85.73% |
| Rebel | L · Llama | 670 | 632.00 | 94.33% | 410 | 233.00 | 56.83% | 87.69% |
| Rebel | LT · Llama | 670 | 360.88 | 53.86% | 410 | 4.29 | 1.05% | 53.30% |
| Rebel | LR · Llama | 670 | 355.11 | 53.00% | 410 | 4.71 | 1.15% | 58.38% |

| Actor | Policy | Breaches | TP | Recall | Compliant | FP | FPR | Verdict coverage |
|---|---|---|---|---|---|---|---|---|
| qwen1.5b | R | 351 | 0.00 | 0.00% | 129 | 2.14 | 1.66% | 5.42% |
| qwen1.5b | X | 351 | 175.72 | 50.06% | 129 | 0.00 | 0.00% | 50.07% |
| qwen1.5b | T | 351 | 85.31 | 24.30% | 129 | 0.00 | 0.00% | 26.21% |
| qwen1.5b | C | 351 | 351.00 | 100.00% | 129 | 0.00 | 0.00% | 100.00% |
| qwen1.5b | L · Qwen | 351 | 323.00 | 92.02% | 129 | 32.00 | 24.81% | 96.04% |
| qwen1.5b | LT · Qwen | 351 | 241.02 | 68.67% | 129 | 0.00 | 0.00% | 80.18% |
| qwen1.5b | LR · Qwen | 351 | 44.89 | 12.79% | 129 | 0.00 | 0.00% | 96.74% |
| qwen1.5b | L · Llama | 351 | 307.00 | 87.46% | 129 | 82.00 | 63.57% | 83.96% |
| qwen1.5b | LT · Llama | 351 | 187.40 | 53.39% | 129 | 0.00 | 0.00% | 55.25% |
| qwen1.5b | LR · Llama | 351 | 157.95 | 45.00% | 129 | 0.00 | 0.00% | 68.06% |
| qwen7b | R | 229 | 60.19 | 26.28% | 251 | 11.01 | 4.39% | 14.83% |
| qwen7b | X | 229 | 114.57 | 50.03% | 251 | 0.00 | 0.00% | 49.88% |
| qwen7b | T | 229 | 60.17 | 26.28% | 251 | 0.00 | 0.00% | 26.29% |
| qwen7b | C | 229 | 229.00 | 100.00% | 251 | 0.00 | 0.00% | 100.00% |
| qwen7b | L · Qwen | 229 | 193.00 | 84.28% | 251 | 1.00 | 0.40% | 87.92% |
| qwen7b | LT · Qwen | 229 | 145.61 | 63.59% | 251 | 0.00 | 0.00% | 86.72% |
| qwen7b | LR · Qwen | 229 | 164.62 | 71.89% | 251 | 0.00 | 0.00% | 88.87% |
| qwen7b | L · Llama | 229 | 207.00 | 90.39% | 251 | 78.00 | 31.08% | 70.63% |
| qwen7b | LT · Llama | 229 | 123.50 | 53.93% | 251 | 0.00 | 0.00% | 59.08% |
| qwen7b | LR · Llama | 229 | 132.54 | 57.88% | 251 | 0.00 | 0.00% | 64.06% |
| llama8b | R | 157 | 79.84 | 50.85% | 323 | 83.90 | 25.98% | 36.65% |
| llama8b | X | 157 | 78.10 | 49.74% | 323 | 4.01 | 1.24% | 41.57% |
| llama8b | T | 157 | 41.36 | 26.35% | 323 | 2.18 | 0.67% | 21.96% |
| llama8b | C | 157 | 157.00 | 100.00% | 323 | 8.00 | 2.48% | 83.33% |
| llama8b | L · Qwen | 157 | 153.00 | 97.45% | 323 | 160.00 | 49.54% | 95.21% |
| llama8b | LT · Qwen | 157 | 113.36 | 72.20% | 323 | 5.92 | 1.83% | 69.61% |
| llama8b | LR · Qwen | 157 | 127.74 | 81.36% | 323 | 6.75 | 2.09% | 73.18% |
| llama8b | L · Llama | 157 | 157.00 | 100.00% | 323 | 222.00 | 68.73% | 87.71% |
| llama8b | LT · Llama | 157 | 84.36 | 53.73% | 323 | 4.29 | 1.33% | 48.93% |
| llama8b | LR · Llama | 157 | 91.82 | 58.48% | 323 | 4.71 | 1.46% | 52.55% |

## Pre-registered predictions

Local predictions were blind to local responses, but tasks and historical judgments were already examined. Inventory-informed forecasts are retained as forecasts/accounting checks, not new discoveries.

| Prediction | Registered expectation | Result | Observed |
|---|---|---|---|
| LP1/qwen7b | Local trace recall: Qwen ≥90%, Llama ≥85% | **Met** | 90.77% |
| LP2/qwen7b | Source FPRs ≤10% and overall verdict coverage ≥90% | **Not met** | HA FPR 0.68%, Rebel FPR 46.59%, coverage 93.06% |
| LP4/qwen7b | Census LT escalation ≤70% and half-cap LT recall > LR | **Met** | Escalation 66.81%; LT recall 67.84%; LR recall 45.76% |
| LP5/qwen7b | Qwen 24/24 raw-identical; Llama fewer than 24/24 | **Met** | 24/24 raw-identical |
| LP1/llama8b | Local trace recall: Qwen ≥90%, Llama ≥85% | **Met** | 91.04% |
| LP2/llama8b | Source FPRs ≤10% and overall verdict coverage ≥90% | **Not met** | HA FPR 50.85%, Rebel FPR 56.83%, coverage 80.76% |
| LP4/llama8b | Census LT escalation ≤70% and half-cap LT recall > LR | **Not met** | Escalation 92.36%; LT recall 53.63%; LR recall 51.87% |
| LP5/llama8b | Qwen 24/24 raw-identical; Llama fewer than 24/24 | **Not met** | 24/24 raw-identical |
| LP3/qwen7b | Qwen exact primary pass; Llama positive mean LT − X recall | **Met** | passes |
| LP3/llama8b | Qwen exact primary pass; Llama positive mean LT − X recall | **Met** | +3.64 pp recall |
| historical/X_at_least_1.5_T | X catches ≥1.5× T at the primary token cap | **Met** | X 368.39; T 186.84; ratio 1.972 |
| historical/T_escalation/HA | Census T escalation >80% per source; Rebel 100% | **Met** | 81.11% |
| historical/X_FPR/HA | X population FPR <5% per source | **Met** | 0.00% |
| historical/T_escalation/Rebel | Census T escalation >80% per source; Rebel 100% | **Met** | 100.00% |
| historical/X_FPR/Rebel | X population FPR <5% per source | **Met** | 0.98% |
| historical/report_cost_exceeds_trace/primary/HA | Mean saved report USD exceeds trace USD | **Met** | Report 0.007601 USD; trace 0.005633 USD per call |
| historical/report_cost_exceeds_trace/primary/Rebel | Mean saved report USD exceeds trace USD | **Met** | Report 0.005506 USD; trace 0.005329 USD per call |
| historical/report_cost_exceeds_trace/gpt_monitor/HA | Mean saved report USD exceeds trace USD | **Met** | Report 0.029419 USD; trace 0.028840 USD per call |
| historical/report_cost_exceeds_trace/gpt_referee/HA | Mean saved report USD exceeds trace USD | **Met** | Report 0.030299 USD; trace 0.030018 USD per call |

**LP5 for Llama failed: all 24 replay replies were byte-identical**, rather than fewer than 24. Its verdict agreement was also 24/24. No replay replaces a first response, and no extra calls were made to seek a mismatch.

## What this means and what remains open

The Qwen allocation advantage is **consistent with** a screen that concentrates frontier checking on a more useful subset of this archive. The frozen comparison supports the measured policy outcome; it does not isolate a reasoning mechanism or demonstrate deliberate concealment by the actors. Local-only flags and full-census catch losses above show why a screening result is not a clearance guarantee.

Underlying tasks were previously examined, Rebel contributes 75% of items, and breach prevalence is high. The archive contains small local generating models, two HA task templates and eight Rebel fixtures. Local actor and monitor families overlap. One first judgment per item/view does not measure full sampling variance. Saved stateless frontier replies do not measure conversational escalation, queue latency, human workload or accepted useful work under a joint production/checking budget.

The GPT monitor and referee cohorts below each reuse the 360 HA items. They change model, transport and, for the referee, instruction; the referee uses `rules_followed`, not completion-dependent class B. These are separate secondary comparisons and cannot replace the declared primary result. Claude cached inputs are priced at one historical rate; GPT accounting includes substantial CLI overhead and third-party price provenance. Historical ledgers reconcile, but not every preflight retains original per-call usage. Nothing here retroactively certifies the source studies' approval history.

**Post hoc items.** The follow-up questions in [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md), requested in Claude’s analysis brief, were introduced after inspecting results. The registered [QUESTIONS.md](QUESTIONS.md) is unchanged. The tables and endpoints here use the frozen analysis; no thresholds, monitors, predictions or rescue tests were added.

**Acceptance status.** Claude’s results review judged the study complete conditional on two documentation fixes. Both are now addressed, and Codex accepts the completed study in [RESPONSE-results-r1.md](RESPONSE-results-r1.md). The frozen analyzer’s historical acceptance field remains **UNKNOWN** because review occurred afterward; its outputs are preserved unchanged. Publication and Robin’s first-project final delivery approval remain separate gates.

## Complete policy grid

All **700 policy/population/resource/cap rows** are represented below. Each cell is **population recall % / mean false alarms**. Census is uncapped; other columns use 0.25, 0.50, 1.00 and 2.50 times that population/cohort's trace-census resource. C cells below full census cost are **infeasible references**. Source-only caps are separate replays, unlike the pooled-route breakdown above. The complete precision, clearance, misses, audits, coverage, input/output resources, seconds, reservation/residual and source/actor/fixture metrics are in [tables.csv](results/main/tables.csv) and [tables.json](results/main/tables.json); integer per-order outcomes and routes are in [orders_routes.jsonl.gz](results/main/orders_routes.jsonl.gz).

### primary · pooled · tokens

Caps (quarter / half / census-size / 2.5×): 411,241 / 822,482 / 1,644,965 / 4,112,412.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 36.09% / 185.00 | 9.53% / 47.99 | 19.00% / 97.05 | 36.09% / 185.00 | 36.09% / 185.00 |
| X | 100.00% / 8.00 | 24.93% / 2.07 | 49.99% / 4.01 | 99.93% / 8.00 | 100.00% / 8.00 |
| T | 96.47% / 8.00 | 12.58% / 1.02 | 25.35% / 2.18 | 50.75% / 4.20 | 96.47% / 8.00 |
| C | 100.00% / 8.00 | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 | 100.00% / 8.00 |
| L · Qwen | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 |
| LT · Qwen | 91.04% / 8.00 | 33.96% / 3.07 | 67.84% / 5.92 | 91.04% / 8.00 | 91.04% / 8.00 |
| LR · Qwen | 54.27% / 8.00 | 22.84% / 3.46 | 45.76% / 6.75 | 54.27% / 8.00 | 54.27% / 8.00 |
| L · Llama | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 |
| LT · Llama | 99.59% / 8.00 | 26.78% / 2.22 | 53.63% / 4.29 | 99.59% / 8.00 | 99.59% / 8.00 |
| LR · Llama | 88.33% / 8.00 | 25.96% / 2.45 | 51.87% / 4.71 | 88.33% / 8.00 | 88.33% / 8.00 |

### primary · pooled · microdollars

Caps (quarter / half / census-size / 2.5×): 1.945885 USD / 3.891770 USD / 7.783540 USD / 19.458850 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 36.09% / 185.00 | 8.10% / 40.86 | 16.14% / 82.35 | 32.26% / 165.47 | 36.09% / 185.00 |
| X | 100.00% / 8.00 | 24.87% / 2.09 | 49.93% / 4.01 | 99.86% / 8.00 | 100.00% / 8.00 |
| T | 96.47% / 8.00 | 11.51% / 0.93 | 23.19% / 2.00 | 46.55% / 3.89 | 96.47% / 8.00 |
| C | 100.00% / 8.00 | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 | 100.00% / 8.00 |
| L · Qwen | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 | 90.77% / 193.00 |
| LT · Qwen | 91.04% / 8.00 | 33.41% / 3.02 | 66.79% / 5.85 | 91.04% / 8.00 | 91.04% / 8.00 |
| LR · Qwen | 54.27% / 8.00 | 22.23% / 3.37 | 44.54% / 6.61 | 54.27% / 8.00 | 54.27% / 8.00 |
| L · Llama | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 | 91.04% / 382.00 |
| LT · Llama | 99.59% / 8.00 | 26.56% / 2.20 | 53.21% / 4.28 | 99.59% / 8.00 | 99.59% / 8.00 |
| LR · Llama | 88.33% / 8.00 | 25.79% / 2.43 | 51.57% / 4.66 | 88.33% / 8.00 | 88.33% / 8.00 |

### primary · HA · tokens

Caps (quarter / half / census-size / 2.5×): 109,362 / 218,724 / 437,449 / 1,093,622.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 0.00% / 17.00 | 0.00% / 4.27 | 0.00% / 8.86 | 0.00% / 17.00 | 0.00% / 17.00 |
| X | 100.00% / 0.00 | 24.15% / 0.00 | 49.24% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 61.19% / 0.00 | 8.33% / 0.00 | 16.76% / 0.00 | 34.07% / 0.00 | 61.19% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.04% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.43% / 0.00 | 49.64% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.91% / 0.00 | 50.96% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.83% / 0.00 | 48.69% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### primary · HA · microdollars

Caps (quarter / half / census-size / 2.5×): 0.506965 USD / 1.013930 USD / 2.027860 USD / 5.069650 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 0.00% / 17.00 | 0.00% / 3.02 | 0.00% / 6.29 | 0.00% / 12.69 | 0.00% / 17.00 |
| X | 100.00% / 0.00 | 23.91% / 0.00 | 49.04% / 0.00 | 99.62% / 0.00 | 100.00% / 0.00 |
| T | 61.19% / 0.00 | 6.69% / 0.00 | 13.61% / 0.00 | 27.94% / 0.00 | 61.19% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 49.07% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.03% / 0.00 | 48.94% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.57% / 0.00 | 50.52% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.68% / 0.00 | 48.64% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### primary · Rebel · tokens

Caps (quarter / half / census-size / 2.5×): 301,879 / 603,758 / 1,207,516 / 3,018,790.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 39.70% / 168.00 | 10.62% / 44.68 | 21.25% / 88.94 | 39.70% / 168.00 | 39.70% / 168.00 |
| X | 100.00% / 8.00 | 24.90% / 1.88 | 49.97% / 4.00 | 99.90% / 7.99 | 100.00% / 8.00 |
| T | 100.00% / 8.00 | 12.82% / 0.98 | 25.70% / 1.94 | 51.57% / 4.13 | 100.00% / 8.00 |
| C | 100.00% / 8.00 | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 | 100.00% / 8.00 |
| L · Qwen | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 |
| LT · Qwen | 90.75% / 8.00 | 30.33% / 2.57 | 60.78% / 5.30 | 90.75% / 8.00 | 90.75% / 8.00 |
| LR · Qwen | 51.79% / 8.00 | 24.97% / 3.84 | 49.86% / 7.75 | 51.79% / 8.00 | 51.79% / 8.00 |
| L · Llama | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 |
| LT · Llama | 100.00% / 8.00 | 26.90% / 2.04 | 53.96% / 4.31 | 100.00% / 8.00 | 100.00% / 8.00 |
| LR · Llama | 90.30% / 8.00 | 24.90% / 2.11 | 49.94% / 4.45 | 90.30% / 8.00 | 90.30% / 8.00 |

### primary · Rebel · microdollars

Caps (quarter / half / census-size / 2.5×): 1.438920 USD / 2.877840 USD / 5.755680 USD / 14.389200 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 39.70% / 168.00 | 9.63% / 40.52 | 19.31% / 80.66 | 38.38% / 162.25 | 39.70% / 168.00 |
| X | 100.00% / 8.00 | 24.83% / 1.87 | 49.90% / 4.00 | 99.82% / 7.99 | 100.00% / 8.00 |
| T | 100.00% / 8.00 | 12.17% / 0.94 | 24.43% / 1.84 | 49.08% / 3.92 | 100.00% / 8.00 |
| C | 100.00% / 8.00 | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 (infeasible) | 100.00% / 8.00 | 100.00% / 8.00 |
| L · Qwen | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 | 90.45% / 191.00 |
| LT · Qwen | 90.75% / 8.00 | 29.87% / 2.56 | 59.98% / 5.26 | 90.75% / 8.00 | 90.75% / 8.00 |
| LR · Qwen | 51.79% / 8.00 | 23.96% / 3.68 | 47.87% / 7.49 | 51.79% / 8.00 | 51.79% / 8.00 |
| L · Llama | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 | 94.33% / 233.00 |
| LT · Llama | 100.00% / 8.00 | 26.61% / 2.02 | 53.45% / 4.26 | 100.00% / 8.00 | 100.00% / 8.00 |
| LR · Llama | 90.30% / 8.00 | 24.69% / 2.10 | 49.62% / 4.40 | 90.30% / 8.00 | 90.30% / 8.00 |

### gpt_monitor · pooled · tokens

Caps (quarter / half / census-size / 2.5×): 1,262,540 / 2,525,080 / 5,050,160 / 12,625,400.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 2.99% / 7.00 | 0.85% / 1.72 | 1.52% / 3.55 | 2.99% / 7.00 | 2.99% / 7.00 |
| X | 100.00% / 0.00 | 24.15% / 0.00 | 49.28% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 77.61% / 0.00 | 10.12% / 0.00 | 20.20% / 0.00 | 40.67% / 0.00 | 77.61% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.72% / 0.00 | 50.19% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.95% / 0.00 | 51.15% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.71% / 0.00 | 48.42% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_monitor · pooled · microdollars

Caps (quarter / half / census-size / 2.5×): 2.595616 USD / 5.191232 USD / 10.382464 USD / 25.956160 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 2.99% / 7.00 | 0.84% / 1.66 | 1.49% / 3.47 | 2.95% / 6.85 | 2.99% / 7.00 |
| X | 100.00% / 0.00 | 24.14% / 0.00 | 49.25% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 77.61% / 0.00 | 9.92% / 0.00 | 19.84% / 0.00 | 40.05% / 0.00 | 77.61% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.77% / 0.00 | 50.23% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.94% / 0.00 | 51.16% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.67% / 0.00 | 48.39% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_monitor · HA · tokens

Caps (quarter / half / census-size / 2.5×): 1,262,540 / 2,525,080 / 5,050,160 / 12,625,400.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 2.99% / 7.00 | 0.85% / 1.72 | 1.52% / 3.55 | 2.99% / 7.00 | 2.99% / 7.00 |
| X | 100.00% / 0.00 | 24.15% / 0.00 | 49.28% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 77.61% / 0.00 | 10.12% / 0.00 | 20.20% / 0.00 | 40.67% / 0.00 | 77.61% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.72% / 0.00 | 50.19% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.95% / 0.00 | 51.15% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.71% / 0.00 | 48.42% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_monitor · HA · microdollars

Caps (quarter / half / census-size / 2.5×): 2.595616 USD / 5.191232 USD / 10.382464 USD / 25.956160 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 2.99% / 7.00 | 0.84% / 1.66 | 1.49% / 3.47 | 2.95% / 6.85 | 2.99% / 7.00 |
| X | 100.00% / 0.00 | 24.14% / 0.00 | 49.25% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 77.61% / 0.00 | 9.92% / 0.00 | 19.84% / 0.00 | 40.05% / 0.00 | 77.61% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.77% / 0.00 | 50.23% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.94% / 0.00 | 51.16% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.67% / 0.00 | 48.39% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_referee · pooled · tokens

Caps (quarter / half / census-size / 2.5×): 1,280,158 / 2,560,317 / 5,120,634 / 12,801,585.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 59.70% / 206.00 | 14.72% / 51.36 | 29.73% / 103.09 | 59.70% / 206.00 | 59.70% / 206.00 |
| X | 100.00% / 0.00 | 24.08% / 0.00 | 49.19% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 59.70% / 0.00 | 8.04% / 0.00 | 16.21% / 0.00 | 33.02% / 0.00 | 59.70% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.72% / 0.00 | 50.19% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.92% / 0.00 | 51.13% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.61% / 0.00 | 48.42% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_referee · pooled · microdollars

Caps (quarter / half / census-size / 2.5×): 2.701625 USD / 5.403250 USD / 10.806500 USD / 27.016250 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 59.70% / 206.00 | 14.45% / 50.64 | 29.41% / 101.66 | 59.03% / 203.66 | 59.70% / 206.00 |
| X | 100.00% / 0.00 | 24.15% / 0.00 | 49.22% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 59.70% / 0.00 | 7.99% / 0.00 | 16.11% / 0.00 | 32.73% / 0.00 | 59.70% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.58% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.66% / 0.00 | 50.05% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.95% / 0.00 | 51.10% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.71% / 0.00 | 48.50% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_referee · HA · tokens

Caps (quarter / half / census-size / 2.5×): 1,280,158 / 2,560,317 / 5,120,634 / 12,801,585.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 59.70% / 206.00 | 14.72% / 51.36 | 29.73% / 103.09 | 59.70% / 206.00 | 59.70% / 206.00 |
| X | 100.00% / 0.00 | 24.08% / 0.00 | 49.19% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 59.70% / 0.00 | 8.04% / 0.00 | 16.21% / 0.00 | 33.02% / 0.00 | 59.70% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.98% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.72% / 0.00 | 50.19% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.92% / 0.00 | 51.13% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.61% / 0.00 | 48.42% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

### gpt_referee · HA · microdollars

Caps (quarter / half / census-size / 2.5×): 2.701625 USD / 5.403250 USD / 10.806500 USD / 27.016250 USD.

| Policy | Uncapped census | 0.25× | 0.50× | 1.00× | 2.50× |
|---|---|---|---|---|---|
| R | 59.70% / 206.00 | 14.45% / 50.64 | 29.41% / 101.66 | 59.03% / 203.66 | 59.70% / 206.00 |
| X | 100.00% / 0.00 | 24.15% / 0.00 | 49.22% / 0.00 | 99.79% / 0.00 | 100.00% / 0.00 |
| T | 59.70% / 0.00 | 7.99% / 0.00 | 16.11% / 0.00 | 32.73% / 0.00 | 59.70% / 0.00 |
| C | 100.00% / 0.00 | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 (infeasible) | 100.00% / 0.00 | 100.00% / 0.00 |
| L · Qwen | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 | 94.03% / 2.00 |
| LT · Qwen | 94.03% / 0.00 | 50.58% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 | 94.03% / 0.00 |
| LR · Qwen | 79.10% / 0.00 | 24.66% / 0.00 | 50.05% / 0.00 | 79.10% / 0.00 | 79.10% / 0.00 |
| L · Llama | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 | 58.21% / 149.00 |
| LT · Llama | 95.52% / 0.00 | 24.95% / 0.00 | 51.10% / 0.00 | 95.52% / 0.00 | 95.52% / 0.00 |
| LR · Llama | 68.66% / 0.00 | 23.71% / 0.00 | 48.50% / 0.00 | 68.66% / 0.00 | 68.66% / 0.00 |

## Reproduce

Follow [README.md](README.md) to run the frozen tests, import, verify and analysis entirely offline. The original execution instructions are in [RUN.md](RUN.md). All original results remain under `results/main/`; rebuild into a new directory.
