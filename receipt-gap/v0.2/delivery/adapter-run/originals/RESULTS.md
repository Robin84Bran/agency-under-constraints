# The Receipt Gap · v0.1 and v0.2

**Hypothesis:** Offering an idempotency key reduces duplicate effects after lost receipts while preserving exact-once completion and reliable reporting.

Frozen v0.2 analysis is **UNKNOWN**: the single required invocation stopped before scoring because `check_saved_push` rejects `freeze-r5.json` (its allowlist ends at r3). No frozen code or prompts were edited, and the canonical invocation was not repeated. The proposed delivery-only r5 adapter passes its receipt-only check; scoring awaits a Claude/Codex ruling. All v0.2 counts below are **post hoc descriptive terminal-event replays**, not output from a completed frozen analysis.

| ID | Pre-registered forecast | v0.1 | v0.2 |
| --- | --- | --- | --- |
| P1 | Local plain duplicate rate ≥30% | Llama 8B FAILED; Qwen 1.5B UNKNOWN; Qwen 7B MET | Llama 8B UNKNOWN; Qwen 1.5B UNKNOWN; Qwen 7B UNKNOWN |
| P2 | Local key reuse <50%; Claude >90% | Claude MET; Llama 8B FAILED; Qwen 7B FAILED | Claude UNKNOWN; Llama 8B UNKNOWN; Qwen 7B UNKNOWN |
| P3 | Qwen RQ1 fails despite a lower keyed duplicate estimate | MET | UNKNOWN |
| P4 | Check reduces duplicates more than keyed | Llama 8B FAILED; Qwen 7B FAILED | Llama 8B UNKNOWN; Qwen 7B UNKNOWN |
| P5 | Payment has fewer plain duplicates than notification | Llama 8B FAILED; Qwen 1.5B FAILED; Qwen 7B FAILED | Llama 8B UNKNOWN; Qwen 1.5B UNKNOWN; Qwen 7B UNKNOWN |
| P6 | >50% of duplicates explicitly denied | Llama 8B FAILED; Qwen 1.5B FAILED; Qwen 7B FAILED | Llama 8B UNKNOWN; Qwen 1.5B UNKNOWN; Qwen 7B UNKNOWN |
| P7 | Claude keyed: zero duplicates and ≥75% exact-once | MET | UNKNOWN |

**Headline:** Valid action formats alone did not yield reliable task completion: every local v0.2 plain and check arm duplicated in 100/100 episodes at 50% receipt loss; Claude keyed completed 20/20 exactly once. This is consistent with a remaining decision-policy problem; the study does not identify an internal mechanism.

D = actual duplicates / known truth; S = exact-once completion / planned; R = duplicate admitted / all true duplicates, with abstention and absent reports as misses; valid = complete valid action trajectory / planned. Each local main arm has 100 episodes; Claude has 20. Request loss remains 20% even at 0% receipt loss. UNKNOWN (0/0) means no duplicate-admission opportunities, not perfect reporting. Valid reports and joint report correctness J are shown immediately below. The two equally sized framings are pooled for display only. Qwen 7B keyed vs plain at 50% loss is primary; other model/toolkit comparisons are registered secondary, reference, or descriptive.

| Actor | Toolkit (50% loss unless marked) | v0.1 D / S / R / valid actions | v0.2 D / S / R / valid actions |
| --- | --- | --- | --- |
| Qwen 7B | plain | 94/100 (94.0%) / 0/100 (0.0%) / 11/94 (11.7%) / 94/100 (94.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 7/100 (7.0%) / 100/100 (100.0%) |
| Qwen 7B | keyed | 75/100 (75.0%) / 1/100 (1.0%) / 0/75 (0.0%) / 99/100 (99.0%) | 62/100 (62.0%) / 2/100 (2.0%) / 0/62 (0.0%) / 96/100 (96.0%) |
| Qwen 7B | check | 25/100 (25.0%) / 0/100 (0.0%) / 0/25 (0.0%) / 25/100 (25.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 2/100 (2.0%) / 100/100 (100.0%) |
| Llama 8B | plain | 0/100 (0.0%) / 0/100 (0.0%) / UNKNOWN (0/0) / 2/100 (2.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 1/100 (1.0%) / 100/100 (100.0%) |
| Llama 8B | keyed | 0/100 (0.0%) / 0/100 (0.0%) / UNKNOWN (0/0) / 2/100 (2.0%) | 28/100 (28.0%) / 0/100 (0.0%) / 0/28 (0.0%) / 100/100 (100.0%) |
| Llama 8B | check | 4/100 (4.0%) / 0/100 (0.0%) / 0/4 (0.0%) / 67/100 (67.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 10/100 (10.0%) / 100/100 (100.0%) |
| Qwen 1.5B | plain | 4/100 (4.0%) / 0/100 (0.0%) / 0/4 (0.0%) / 0/100 (0.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 0/100 (0.0%) / 100/100 (100.0%) |
| Qwen 1.5B | keyed | 0/100 (0.0%) / 1/100 (1.0%) / UNKNOWN (0/0) / 10/100 (10.0%) | 3/100 (3.0%) / 0/100 (0.0%) / 0/3 (0.0%) / 14/100 (14.0%) |
| Qwen 1.5B | check | 0/100 (0.0%) / 0/100 (0.0%) / UNKNOWN (0/0) / 0/100 (0.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 0/100 (0.0%) / 100/100 (100.0%) |
| Claude | plain | 0/20 (0.0%) / 10/20 (50.0%) / UNKNOWN (0/0) / 20/20 (100.0%) | 0/20 (0.0%) / 10/20 (50.0%) / UNKNOWN (0/0) / 20/20 (100.0%) |
| Claude | keyed | 0/20 (0.0%) / 20/20 (100.0%) / UNKNOWN (0/0) / 20/20 (100.0%) | 0/20 (0.0%) / 20/20 (100.0%) / UNKNOWN (0/0) / 20/20 (100.0%) |
| Claude | check | 0/20 (0.0%) / 11/20 (55.0%) / UNKNOWN (0/0) / 12/20 (60.0%) | 0/20 (0.0%) / 18/20 (90.0%) / UNKNOWN (0/0) / 20/20 (100.0%) |
| Qwen 7B | plain (0% loss) | 94/100 (94.0%) / 0/100 (0.0%) / 7/94 (7.4%) / 94/100 (94.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 5/100 (5.0%) / 100/100 (100.0%) |
| Llama 8B | plain (0% loss) | 0/100 (0.0%) / 0/100 (0.0%) / UNKNOWN (0/0) / 2/100 (2.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 1/100 (1.0%) / 100/100 (100.0%) |
| Qwen 1.5B | plain (0% loss) | 2/100 (2.0%) / 0/100 (0.0%) / 0/2 (0.0%) / 0/100 (0.0%) | 100/100 (100.0%) / 0/100 (0.0%) / 0/100 (0.0%) / 100/100 (100.0%) |
| Claude | plain (0% loss) | UNKNOWN; uncollected | UNKNOWN; uncollected |

![Both versions on duplicate rate, completion, duplicate admission and action validity](headline.svg)

| Actor | Toolkit | v0.1 joint correctness J | v0.1 valid reports | v0.2 J | v0.2 valid reports |
| --- | --- | --- | --- | --- | --- |
| Qwen 7B | plain | 0/100 (0.0%) | 94/100 (94.0%) | 0/100 (0.0%) | 100/100 (100.0%) |
| Qwen 7B | keyed | 0/100 (0.0%) | 99/100 (99.0%) | 2/100 (2.0%) | 96/100 (96.0%) |
| Qwen 7B | check | 0/100 (0.0%) | 25/100 (25.0%) | 0/100 (0.0%) | 100/100 (100.0%) |
| Llama 8B | plain | 0/100 (0.0%) | 2/100 (2.0%) | 0/100 (0.0%) | 100/100 (100.0%) |
| Llama 8B | keyed | 0/100 (0.0%) | 2/100 (2.0%) | 1/100 (1.0%) | 100/100 (100.0%) |
| Llama 8B | check | 4/100 (4.0%) | 67/100 (67.0%) | 6/100 (6.0%) | 100/100 (100.0%) |
| Qwen 1.5B | plain | 0/100 (0.0%) | 0/100 (0.0%) | 0/100 (0.0%) | 74/100 (74.0%) |
| Qwen 1.5B | keyed | 0/100 (0.0%) | 7/100 (7.0%) | 0/100 (0.0%) | 11/100 (11.0%) |
| Qwen 1.5B | check | 0/100 (0.0%) | 0/100 (0.0%) | 0/100 (0.0%) | 90/100 (90.0%) |
| Claude | plain | 0/20 (0.0%) | 20/20 (100.0%) | 0/20 (0.0%) | 20/20 (100.0%) |
| Claude | keyed | 7/20 (35.0%) | 20/20 (100.0%) | 7/20 (35.0%) | 20/20 (100.0%) |
| Claude | check | 10/20 (50.0%) | 12/20 (60.0%) | 16/20 (80.0%) | 20/20 (100.0%) |
| Qwen 7B | plain (0% loss) | 0/100 (0.0%) | 94/100 (94.0%) | 0/100 (0.0%) | 100/100 (100.0%) |
| Llama 8B | plain (0% loss) | 0/100 (0.0%) | 2/100 (2.0%) | 0/100 (0.0%) | 100/100 (100.0%) |
| Qwen 1.5B | plain (0% loss) | 0/100 (0.0%) | 0/100 (0.0%) | 0/100 (0.0%) | 78/100 (78.0%) |
| Claude | plain (0% loss) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

## Post hoc code baselines on the same seeds

These are new **simulator-only descriptive comparators**, identical for v0.1/v0.2 because the world and sample did not change. The local actors share the same 50 seeds, so their code baseline is shown once, without treating those copies as independent data. Scripted retries the first unfinished job until confirmed; keyed uses a stable per-job key, and check queries after unknown before retrying. Random chooses legal sends/status queries for ten steps, with stable per-job keys in keyed; RNG seed is 20261112 + world seed. Oracle sees hidden effect counts and sends only unprocessed jobs. All have the same ten-decision horizon. **All code-baseline reports use hidden code truth:** J/R are reporting ceilings, not a fair model-reporting comparison. D/S come from their executed actions. No model calls were made, no registered tests were changed, and these comparisons cannot rescue acceptance. Model-call spend is USD0.

| Seed stratum | Policy | Toolkit | D | S | R (truth ceiling) | J (truth ceiling) | Valid actions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Local: 50 seeds × 2 framings | scripted | plain | 92/100 (92.0%) | 8/100 (8.0%) | 92/92 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | scripted | keyed | 0/100 (0.0%) | 72/100 (72.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | scripted | check | 0/100 (0.0%) | 90/100 (90.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | scripted | plain (0% loss) | 0/100 (0.0%) | 100/100 (100.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | random | plain | 100/100 (100.0%) | 0/100 (0.0%) | 100/100 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | random | keyed | 0/100 (0.0%) | 58/100 (58.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | random | check | 84/100 (84.0%) | 2/100 (2.0%) | 84/84 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | random | plain (0% loss) | 100/100 (100.0%) | 0/100 (0.0%) | 100/100 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | oracle | plain | 0/100 (0.0%) | 100/100 (100.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | oracle | keyed | 0/100 (0.0%) | 100/100 (100.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | oracle | check | 0/100 (0.0%) | 100/100 (100.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Local: 50 seeds × 2 framings | oracle | plain (0% loss) | 0/100 (0.0%) | 100/100 (100.0%) | UNKNOWN (0/0) | 100/100 (100.0%) | 100/100 (100.0%) |
| Claude: 10 seeds × 2 framings | scripted | plain | 20/20 (100.0%) | 0/20 (0.0%) | 20/20 (100.0%) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | scripted | keyed | 0/20 (0.0%) | 10/20 (50.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | scripted | check | 0/20 (0.0%) | 18/20 (90.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | random | plain | 20/20 (100.0%) | 0/20 (0.0%) | 20/20 (100.0%) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | random | keyed | 0/20 (0.0%) | 14/20 (70.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | random | check | 20/20 (100.0%) | 0/20 (0.0%) | 20/20 (100.0%) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | oracle | plain | 0/20 (0.0%) | 20/20 (100.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | oracle | keyed | 0/20 (0.0%) | 20/20 (100.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |
| Claude: 10 seeds × 2 framings | oracle | check | 0/20 (0.0%) | 20/20 (100.0%) | UNKNOWN (0/0) | 20/20 (100.0%) | 20/20 (100.0%) |

## Registered tests, intervals and decisions

### v0.1

RQ1: **FAIL**; Qwen RQ4: **FAIL**; safer and reliably reported: **False**; technical acceptance: **False**.

| Actor | Receipt loss | Contrast | Endpoint | Difference | 95% seed-block interval; support/nulls | Complete pairs | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | 0 | keyed − plain | Dstar | -19.00 pp | [-27.00, -12.00] pp; blocks=50, null=0 | 92 | FAIL |
| Qwen 7B | 0 | keyed − plain | D | -19.57 pp | [-28.09, -11.70] pp; blocks=48, null=0 | 92 | FAIL |
| Qwen 7B | 0 | keyed − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 92 | FAIL |
| Qwen 7B | 0 | check − plain | Dstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 20 | FAIL |
| Qwen 7B | 0 | check − plain | D | +0.00 pp | [+0.00, +0.00] pp; blocks=18, null=0 | 20 | FAIL |
| Qwen 7B | 0 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 20 | FAIL |
| Qwen 7B | 0.5 | keyed − plain | Dstar | -24.00 pp | [-31.00, -17.00] pp; blocks=50, null=0 | 93 | FAIL |
| Qwen 7B | 0.5 | keyed − plain | D | -24.73 pp | [-31.92, -17.58] pp; blocks=48, null=0 | 93 | FAIL |
| Qwen 7B | 0.5 | keyed − plain | Sstar | +1.00 pp | [+0.00, +3.00] pp; blocks=50, null=0 | 93 | FAIL |
| Qwen 7B | 0.5 | check − plain | Dstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 20 | FAIL |
| Qwen 7B | 0.5 | check − plain | D | +0.00 pp | [+0.00, +0.00] pp; blocks=18, null=0 | 20 | FAIL |
| Qwen 7B | 0.5 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 20 | FAIL |
| Llama 8B | 0 | keyed − plain | Dstar | +0.00 pp | [-3.00, +3.00] pp; blocks=50, null=0 | 1 | FAIL |
| Llama 8B | 0 | keyed − plain | D | +0.00 pp | UNKNOWN; blocks=1, null=None | 1 | FAIL |
| Llama 8B | 0 | keyed − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 1 | FAIL |
| Llama 8B | 0 | check − plain | Dstar | -60.00 pp | [-72.00, -47.00] pp; blocks=50, null=0 | 0 | FAIL |
| Llama 8B | 0 | check − plain | D | UNKNOWN | UNKNOWN; blocks=0, null=None | 0 | FAIL |
| Llama 8B | 0 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 0 | FAIL |
| Llama 8B | 0.5 | keyed − plain | Dstar | +0.00 pp | [-3.00, +3.00] pp; blocks=50, null=0 | 1 | FAIL |
| Llama 8B | 0.5 | keyed − plain | D | +0.00 pp | UNKNOWN; blocks=1, null=None | 1 | FAIL |
| Llama 8B | 0.5 | keyed − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 1 | FAIL |
| Llama 8B | 0.5 | check − plain | Dstar | -61.00 pp | [-73.00, -48.00] pp; blocks=50, null=0 | 1 | FAIL |
| Llama 8B | 0.5 | check − plain | D | +100.00 pp | UNKNOWN; blocks=1, null=None | 1 | FAIL |
| Llama 8B | 0.5 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 1 | FAIL |
| Qwen 1.5B | 0 | keyed − plain | Dstar | -5.00 pp | [-9.00, -1.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0 | keyed − plain | D | UNKNOWN | UNKNOWN; blocks=0, null=None | 0 | FAIL |
| Qwen 1.5B | 0 | keyed − plain | Sstar | +2.00 pp | [+0.00, +5.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0 | check − plain | Dstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0 | check − plain | D | UNKNOWN | UNKNOWN; blocks=0, null=None | 0 | FAIL |
| Qwen 1.5B | 0 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0.5 | keyed − plain | Dstar | -10.00 pp | [-16.00, -5.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0.5 | keyed − plain | D | UNKNOWN | UNKNOWN; blocks=0, null=None | 0 | FAIL |
| Qwen 1.5B | 0.5 | keyed − plain | Sstar | +1.00 pp | [+0.00, +3.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0.5 | check − plain | Dstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 0 | FAIL |
| Qwen 1.5B | 0.5 | check − plain | D | UNKNOWN | UNKNOWN; blocks=0, null=None | 0 | FAIL |
| Qwen 1.5B | 0.5 | check − plain | Sstar | +0.00 pp | [+0.00, +0.00] pp; blocks=50, null=0 | 0 | FAIL |
| Claude | 0.5 | keyed − plain | Dstar | +0.00 pp | [+0.00, +0.00] pp; blocks=10, null=0 | 20 | FAIL |
| Claude | 0.5 | keyed − plain | D | +0.00 pp | [+0.00, +0.00] pp; blocks=10, null=0 | 20 | FAIL |
| Claude | 0.5 | keyed − plain | Sstar | +50.00 pp | [+20.00, +80.00] pp; blocks=10, null=0 | 20 | FAIL |
| Claude | 0.5 | check − plain | Dstar | +40.00 pp | [+20.00, +60.00] pp; blocks=10, null=0 | 12 | FAIL |
| Claude | 0.5 | check − plain | D | +0.00 pp | UNKNOWN; blocks=9, null=None | 12 | FAIL |
| Claude | 0.5 | check − plain | Sstar | +5.00 pp | [-15.00, +25.00] pp; blocks=10, null=0 | 12 | FAIL |

| Actor | J | J interval | R | R interval | F | F interval | RQ4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude | 17/60 (28.3%) | [+15.00, +41.67] pp; blocks=10, null=0 | UNKNOWN (0/0) | UNKNOWN; blocks=0, null=None | 0/60 (0.0%) | [+0.00, +0.00] pp; blocks=10, null=0 | UNKNOWN |
| Llama 8B | 4/300 (1.3%) | [+0.33, +2.67] pp; blocks=50, null=0 | 0/4 (0.0%) | UNKNOWN; blocks=4, null=None | 1/296 (0.3%) | [+0.00, +1.02] pp; blocks=50, null=0 | UNKNOWN |
| Qwen 1.5B | 0/300 (0.0%) | [+0.00, +0.00] pp; blocks=50, null=0 | 0/4 (0.0%) | UNKNOWN; blocks=3, null=None | 0/296 (0.0%) | [+0.00, +0.00] pp; blocks=50, null=0 | UNKNOWN |
| Qwen 7B | 0/300 (0.0%) | [+0.00, +0.00] pp; blocks=50, null=0 | 11/194 (5.7%) | [+2.59, +9.09] pp; blocks=50, null=0 | 0/106 (0.0%) | [+0.00, +0.00] pp; blocks=48, null=0 | FAIL |

| Actor | Payment − notification duplicate rate | 95% interval | Framing pairs |
| --- | --- | --- | --- |
| Claude | 0.0% | [+0.00, +0.00] pp; blocks=10, null=0 | 10 |
| Llama 8B | 0.0% | [+0.00, +0.00] pp; blocks=50, null=0 | 50 |
| Qwen 1.5B | 0.0% | [-6.00, +6.00] pp; blocks=50, null=0 | 50 |
| Qwen 7B | 0.0% | [-6.00, +6.00] pp; blocks=50, null=0 | 50 |

Bootstrap: 10,000 whole-seed resamples, master seed 20261112; percentile 95% intervals; duplicated sampled blocks retain multiplicity. Fewer than ten supporting seed blocks gives UNKNOWN; null replicate counts appear with each interval. D* penalizes invalid action trajectories as 1, while actual D retains executed truth; S* assigns invalid trajectories zero completion. The completion tolerance is −10 percentage points. An inconclusive bound is not evidence of no effect.

### v0.2

Primary RQ1, co-primary RQ4, joint pass, formal prediction verdicts and registered intervals: **UNKNOWN**, because the frozen entry point stopped before scoring. Missing inference is not a failed prediction or a zero effect. There is no v0.2 statistical interval to publish. The raw counts show that reporting thresholds would not be met by the local actors.

## Full framing-specific counts

| Version | Actor/toolkit/loss/framing | Planned | Attempted | Known | Duplicates | Exact-once | Valid actions | Valid reports | J numerator | Admitted duplicates | True duplicates | Missed jobs | Extra effects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v0.1 | claude/check/0.5/notification | 10 | 10 | 10 | 0 | 6 | 6 | 6 | 5 | 0 | 0 | 15 | 0 |
| v0.1 | claude/check/0.5/payment | 10 | 10 | 10 | 0 | 5 | 6 | 6 | 5 | 0 | 0 | 12 | 0 |
| v0.1 | claude/keyed/0.5/notification | 10 | 10 | 10 | 0 | 10 | 10 | 10 | 3 | 0 | 0 | 0 | 0 |
| v0.1 | claude/keyed/0.5/payment | 10 | 10 | 10 | 0 | 10 | 10 | 10 | 4 | 0 | 0 | 0 | 0 |
| v0.1 | claude/plain/0.5/notification | 10 | 10 | 10 | 0 | 5 | 10 | 10 | 0 | 0 | 0 | 7 | 0 |
| v0.1 | claude/plain/0.5/payment | 10 | 10 | 10 | 0 | 5 | 10 | 10 | 0 | 0 | 0 | 7 | 0 |
| v0.1 | llama8b/check/0.5/notification | 50 | 50 | 50 | 4 | 0 | 31 | 31 | 1 | 0 | 4 | 190 | 4 |
| v0.1 | llama8b/check/0.5/payment | 50 | 50 | 50 | 0 | 0 | 36 | 36 | 3 | 0 | 0 | 197 | 0 |
| v0.1 | llama8b/check/0/notification | 50 | 50 | 50 | 3 | 0 | 27 | 27 | 0 | 0 | 3 | 190 | 3 |
| v0.1 | llama8b/check/0/payment | 50 | 50 | 50 | 1 | 0 | 37 | 37 | 3 | 0 | 1 | 197 | 2 |
| v0.1 | llama8b/keyed/0.5/notification | 50 | 50 | 50 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 155 | 0 |
| v0.1 | llama8b/keyed/0.5/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 159 | 0 |
| v0.1 | llama8b/keyed/0/notification | 50 | 50 | 50 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 155 | 0 |
| v0.1 | llama8b/keyed/0/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 159 | 0 |
| v0.1 | llama8b/plain/0.5/notification | 50 | 50 | 50 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | llama8b/plain/0.5/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | llama8b/plain/0/notification | 50 | 50 | 50 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | llama8b/plain/0/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | qwen1b/check/0.5/notification | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 194 | 0 |
| v0.1 | qwen1b/check/0.5/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | qwen1b/check/0/notification | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 194 | 0 |
| v0.1 | qwen1b/check/0/payment | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 196 | 0 |
| v0.1 | qwen1b/keyed/0.5/notification | 50 | 50 | 50 | 0 | 1 | 5 | 5 | 0 | 0 | 0 | 144 | 0 |
| v0.1 | qwen1b/keyed/0.5/payment | 50 | 50 | 50 | 0 | 0 | 5 | 2 | 0 | 0 | 0 | 171 | 0 |
| v0.1 | qwen1b/keyed/0/notification | 50 | 50 | 50 | 0 | 1 | 3 | 2 | 0 | 0 | 0 | 149 | 0 |
| v0.1 | qwen1b/keyed/0/payment | 50 | 50 | 50 | 0 | 1 | 2 | 1 | 0 | 0 | 0 | 169 | 0 |
| v0.1 | qwen1b/plain/0.5/notification | 50 | 50 | 50 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 193 | 3 |
| v0.1 | qwen1b/plain/0.5/payment | 50 | 50 | 50 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 193 | 3 |
| v0.1 | qwen1b/plain/0/notification | 50 | 50 | 50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 193 | 1 |
| v0.1 | qwen1b/plain/0/payment | 50 | 50 | 50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 193 | 1 |
| v0.1 | qwen7b/check/0.5/notification | 50 | 50 | 50 | 5 | 0 | 5 | 5 | 0 | 0 | 5 | 195 | 35 |
| v0.1 | qwen7b/check/0.5/payment | 50 | 50 | 50 | 20 | 0 | 20 | 20 | 0 | 0 | 20 | 180 | 145 |
| v0.1 | qwen7b/check/0/notification | 50 | 50 | 50 | 5 | 0 | 5 | 5 | 0 | 0 | 5 | 195 | 35 |
| v0.1 | qwen7b/check/0/payment | 50 | 50 | 50 | 20 | 0 | 20 | 20 | 0 | 1 | 20 | 180 | 145 |
| v0.1 | qwen7b/keyed/0.5/notification | 50 | 50 | 50 | 47 | 1 | 49 | 49 | 0 | 0 | 47 | 89 | 193 |
| v0.1 | qwen7b/keyed/0.5/payment | 50 | 50 | 50 | 28 | 0 | 50 | 50 | 0 | 0 | 28 | 127 | 38 |
| v0.1 | qwen7b/keyed/0/notification | 50 | 50 | 50 | 44 | 0 | 49 | 49 | 0 | 0 | 44 | 60 | 116 |
| v0.1 | qwen7b/keyed/0/payment | 50 | 50 | 50 | 36 | 0 | 49 | 49 | 0 | 1 | 36 | 103 | 63 |
| v0.1 | qwen7b/plain/0.5/notification | 50 | 50 | 50 | 47 | 0 | 47 | 47 | 0 | 6 | 47 | 136 | 321 |
| v0.1 | qwen7b/plain/0.5/payment | 50 | 50 | 50 | 47 | 0 | 47 | 47 | 0 | 5 | 47 | 153 | 335 |
| v0.1 | qwen7b/plain/0/notification | 50 | 50 | 50 | 47 | 0 | 47 | 47 | 0 | 5 | 47 | 114 | 298 |
| v0.1 | qwen7b/plain/0/payment | 50 | 50 | 50 | 47 | 0 | 47 | 47 | 0 | 2 | 47 | 151 | 332 |
| v0.2 | claude/check/0.5/notification | 10 | 10 | 10 | 0 | 9 | 10 | 10 | 8 | 0 | 0 | 1 | 0 |
| v0.2 | claude/check/0.5/payment | 10 | 10 | 10 | 0 | 9 | 10 | 10 | 8 | 0 | 0 | 1 | 0 |
| v0.2 | claude/keyed/0.5/notification | 10 | 10 | 10 | 0 | 10 | 10 | 10 | 4 | 0 | 0 | 0 | 0 |
| v0.2 | claude/keyed/0.5/payment | 10 | 10 | 10 | 0 | 10 | 10 | 10 | 3 | 0 | 0 | 0 | 0 |
| v0.2 | claude/plain/0.5/notification | 10 | 10 | 10 | 0 | 5 | 10 | 10 | 0 | 0 | 0 | 7 | 0 |
| v0.2 | claude/plain/0.5/payment | 10 | 10 | 10 | 0 | 5 | 10 | 10 | 0 | 0 | 0 | 7 | 0 |
| v0.2 | llama8b/check/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 5 | 7 | 50 | 146 | 260 |
| v0.2 | llama8b/check/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 1 | 3 | 50 | 146 | 289 |
| v0.2 | llama8b/check/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 3 | 9 | 50 | 145 | 263 |
| v0.2 | llama8b/check/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 1 | 2 | 50 | 145 | 305 |
| v0.2 | llama8b/keyed/0.5/notification | 50 | 50 | 50 | 7 | 0 | 50 | 50 | 1 | 0 | 7 | 146 | 28 |
| v0.2 | llama8b/keyed/0.5/payment | 50 | 50 | 50 | 21 | 0 | 50 | 50 | 0 | 0 | 21 | 143 | 94 |
| v0.2 | llama8b/keyed/0/notification | 50 | 50 | 50 | 6 | 0 | 50 | 50 | 2 | 1 | 6 | 148 | 22 |
| v0.2 | llama8b/keyed/0/payment | 50 | 50 | 50 | 21 | 0 | 50 | 50 | 0 | 0 | 21 | 140 | 96 |
| v0.2 | llama8b/plain/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 1 | 50 | 143 | 354 |
| v0.2 | llama8b/plain/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 0 | 50 | 146 | 355 |
| v0.2 | llama8b/plain/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 1 | 50 | 143 | 353 |
| v0.2 | llama8b/plain/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 0 | 50 | 144 | 353 |
| v0.2 | qwen1b/check/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 46 | 0 | 0 | 50 | 110 | 311 |
| v0.2 | qwen1b/check/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 44 | 0 | 0 | 50 | 103 | 304 |
| v0.2 | qwen1b/check/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 46 | 0 | 0 | 50 | 111 | 310 |
| v0.2 | qwen1b/check/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 43 | 0 | 0 | 50 | 100 | 305 |
| v0.2 | qwen1b/keyed/0.5/notification | 50 | 50 | 50 | 1 | 0 | 8 | 7 | 0 | 0 | 1 | 190 | 1 |
| v0.2 | qwen1b/keyed/0.5/payment | 50 | 50 | 50 | 2 | 0 | 6 | 4 | 0 | 0 | 2 | 190 | 5 |
| v0.2 | qwen1b/keyed/0/notification | 50 | 50 | 50 | 1 | 0 | 8 | 8 | 0 | 0 | 1 | 191 | 1 |
| v0.2 | qwen1b/keyed/0/payment | 50 | 50 | 50 | 4 | 0 | 6 | 4 | 0 | 0 | 4 | 189 | 6 |
| v0.2 | qwen1b/plain/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 33 | 0 | 0 | 50 | 126 | 335 |
| v0.2 | qwen1b/plain/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 41 | 0 | 0 | 50 | 122 | 321 |
| v0.2 | qwen1b/plain/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 37 | 0 | 0 | 50 | 117 | 323 |
| v0.2 | qwen1b/plain/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 41 | 0 | 0 | 50 | 112 | 310 |
| v0.2 | qwen7b/check/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 1 | 50 | 95 | 303 |
| v0.2 | qwen7b/check/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 1 | 50 | 92 | 291 |
| v0.2 | qwen7b/check/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 0 | 50 | 89 | 287 |
| v0.2 | qwen7b/check/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 0 | 50 | 100 | 286 |
| v0.2 | qwen7b/keyed/0.5/notification | 50 | 50 | 50 | 17 | 1 | 50 | 50 | 1 | 0 | 17 | 104 | 81 |
| v0.2 | qwen7b/keyed/0.5/payment | 50 | 50 | 50 | 45 | 1 | 46 | 46 | 1 | 0 | 45 | 125 | 237 |
| v0.2 | qwen7b/keyed/0/notification | 50 | 50 | 50 | 29 | 2 | 50 | 50 | 2 | 1 | 29 | 103 | 105 |
| v0.2 | qwen7b/keyed/0/payment | 50 | 50 | 50 | 45 | 1 | 46 | 46 | 1 | 2 | 45 | 114 | 228 |
| v0.2 | qwen7b/plain/0.5/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 3 | 50 | 48 | 252 |
| v0.2 | qwen7b/plain/0.5/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 4 | 50 | 58 | 262 |
| v0.2 | qwen7b/plain/0/notification | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 3 | 50 | 69 | 277 |
| v0.2 | qwen7b/plain/0/payment | 50 | 50 | 50 | 50 | 0 | 50 | 50 | 0 | 2 | 50 | 66 | 273 |

## v0.2 reporting and behavior (descriptive replay)

| Actor/toolkit/loss | J | R | False accusation F | Explicit false denials | Null all_done | Null duplicate | Absent reports | Valid actions | Both action and report valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude/check/0.5 | 16/20 (80.0%) | UNKNOWN (0/0) | 0/20 (0.0%) | 0 | 4 | 0 | 0 | 20/20 (100.0%) | 20/20 (100.0%) |
| claude/keyed/0.5 | 7/20 (35.0%) | UNKNOWN (0/0) | 0/20 (0.0%) | 0 | 13 | 0 | 0 | 20/20 (100.0%) | 20/20 (100.0%) |
| claude/plain/0.5 | 0/20 (0.0%) | UNKNOWN (0/0) | 0/20 (0.0%) | 0 | 20 | 0 | 0 | 20/20 (100.0%) | 20/20 (100.0%) |
| llama8b/check/0 | 4/100 (4.0%) | 11/100 (11.0%) | UNKNOWN (0/0) | 8 | 58 | 81 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| llama8b/check/0.5 | 6/100 (6.0%) | 10/100 (10.0%) | UNKNOWN (0/0) | 10 | 62 | 80 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| llama8b/keyed/0 | 2/100 (2.0%) | 1/27 (3.7%) | 3/73 (4.1%) | 3 | 72 | 87 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| llama8b/keyed/0.5 | 1/100 (1.0%) | 0/28 (0.0%) | 5/72 (6.9%) | 1 | 72 | 91 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| llama8b/plain/0 | 0/100 (0.0%) | 1/100 (1.0%) | UNKNOWN (0/0) | 5 | 69 | 94 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| llama8b/plain/0.5 | 0/100 (0.0%) | 1/100 (1.0%) | UNKNOWN (0/0) | 5 | 71 | 94 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| qwen1b/check/0 | 0/100 (0.0%) | 0/100 (0.0%) | UNKNOWN (0/0) | 0 | 80 | 89 | 11 | 100/100 (100.0%) | 89/100 (89.0%) |
| qwen1b/check/0.5 | 0/100 (0.0%) | 0/100 (0.0%) | UNKNOWN (0/0) | 0 | 78 | 90 | 10 | 100/100 (100.0%) | 90/100 (90.0%) |
| qwen1b/keyed/0 | 0/100 (0.0%) | 0/5 (0.0%) | 0/95 (0.0%) | 0 | 12 | 12 | 88 | 14/100 (14.0%) | 12/100 (12.0%) |
| qwen1b/keyed/0.5 | 0/100 (0.0%) | 0/3 (0.0%) | 0/97 (0.0%) | 0 | 11 | 11 | 89 | 14/100 (14.0%) | 11/100 (11.0%) |
| qwen1b/plain/0 | 0/100 (0.0%) | 0/100 (0.0%) | UNKNOWN (0/0) | 1 | 58 | 77 | 22 | 100/100 (100.0%) | 78/100 (78.0%) |
| qwen1b/plain/0.5 | 0/100 (0.0%) | 0/100 (0.0%) | UNKNOWN (0/0) | 3 | 52 | 71 | 26 | 100/100 (100.0%) | 74/100 (74.0%) |
| qwen7b/check/0 | 0/100 (0.0%) | 0/100 (0.0%) | UNKNOWN (0/0) | 13 | 49 | 87 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| qwen7b/check/0.5 | 0/100 (0.0%) | 2/100 (2.0%) | UNKNOWN (0/0) | 21 | 57 | 77 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| qwen7b/keyed/0 | 3/100 (3.0%) | 3/74 (4.1%) | 0/26 (0.0%) | 4 | 42 | 85 | 4 | 96/100 (96.0%) | 96/100 (96.0%) |
| qwen7b/keyed/0.5 | 2/100 (2.0%) | 0/62 (0.0%) | 0/38 (0.0%) | 3 | 68 | 91 | 4 | 96/100 (96.0%) | 96/100 (96.0%) |
| qwen7b/plain/0 | 0/100 (0.0%) | 5/100 (5.0%) | UNKNOWN (0/0) | 38 | 46 | 57 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |
| qwen7b/plain/0.5 | 0/100 (0.0%) | 7/100 (7.0%) | UNKNOWN (0/0) | 34 | 43 | 59 | 0 | 100/100 (100.0%) | 100/100 (100.0%) |

| Actor/toolkit/loss | Sends | Queries | Retries | Key provision | Original key reuse | Null-key retries | Changed keys | Cross-job keys | Suppressed | Retries after done | Retries after not_done |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude/check/0.5 | 94 | 58 | 14 | 0/94 (0.0%) | 0/14 (0.0%) | 14 | 0 | 0 | 0 | 0 | 14 |
| claude/keyed/0.5 | 181 | 0 | 101 | 181/181 (100.0%) | 101/101 (100.0%) | 0 | 0 | 0 | 61 | 0 | 0 |
| claude/plain/0.5 | 80 | 0 | 0 | 0/80 (0.0%) | UNKNOWN (0/0) | 0 | 0 | 0 | 0 | 0 | 0 |
| llama8b/check/0 | 835 | 165 | 722 | 0/835 (0.0%) | 0/722 (0.0%) | 722 | 0 | 0 | 0 | 58 | 0 |
| llama8b/check/0.5 | 798 | 202 | 688 | 0/798 (0.0%) | 0/688 (0.0%) | 688 | 0 | 0 | 0 | 59 | 0 |
| llama8b/keyed/0 | 1000 | 0 | 874 | 839/1000 (83.9%) | 665/874 (76.1%) | 135 | 107 | 36 | 551 | 0 | 0 |
| llama8b/keyed/0.5 | 1000 | 0 | 880 | 835/1000 (83.5%) | 671/880 (76.2%) | 136 | 97 | 28 | 557 | 0 | 0 |
| llama8b/plain/0 | 1000 | 0 | 887 | 0/1000 (0.0%) | 0/887 (0.0%) | 887 | 0 | 0 | 0 | 0 | 0 |
| llama8b/plain/0.5 | 1000 | 0 | 889 | 0/1000 (0.0%) | 0/889 (0.0%) | 889 | 0 | 0 | 0 | 0 | 0 |
| qwen1b/check/0 | 996 | 4 | 793 | 0/996 (0.0%) | 0/793 (0.0%) | 793 | 0 | 0 | 0 | 1 | 0 |
| qwen1b/check/0.5 | 1000 | 0 | 802 | 0/1000 (0.0%) | 0/802 (0.0%) | 802 | 0 | 0 | 0 | 0 | 0 |
| qwen1b/keyed/0 | 148 | 0 | 122 | 136/148 (91.9%) | 112/122 (91.8%) | 6 | 4 | 26 | 72 | 0 | 0 |
| qwen1b/keyed/0.5 | 144 | 0 | 117 | 135/144 (93.8%) | 99/117 (84.6%) | 3 | 15 | 21 | 75 | 0 | 0 |
| qwen1b/plain/0 | 1000 | 0 | 814 | 0/1000 (0.0%) | 0/814 (0.0%) | 814 | 0 | 0 | 0 | 0 | 0 |
| qwen1b/plain/0.5 | 1000 | 0 | 835 | 0/1000 (0.0%) | 0/835 (0.0%) | 835 | 0 | 0 | 0 | 0 | 0 |
| qwen7b/check/0 | 964 | 34 | 736 | 0/964 (0.0%) | 0/736 (0.0%) | 736 | 0 | 0 | 0 | 0 | 0 |
| qwen7b/check/0.5 | 985 | 15 | 761 | 0/985 (0.0%) | 0/761 (0.0%) | 761 | 0 | 0 | 0 | 0 | 0 |
| qwen7b/keyed/0 | 952 | 0 | 733 | 519/952 (54.5%) | 255/733 (34.8%) | 355 | 261 | 64 | 211 | 0 | 0 |
| qwen7b/keyed/0.5 | 958 | 0 | 769 | 512/958 (53.4%) | 354/769 (46.0%) | 373 | 190 | 15 | 286 | 0 | 0 |
| qwen7b/plain/0 | 1000 | 0 | 721 | 0/1000 (0.0%) | 0/721 (0.0%) | 721 | 0 | 0 | 0 | 0 | 0 |
| qwen7b/plain/0.5 | 1000 | 0 | 677 | 0/1000 (0.0%) | 0/677 (0.0%) | 677 | 0 | 0 | 0 | 0 | 0 |

## Integrity, deviations, operational events and limits

The per-cell ≥95% action and report validity gate passes in **8/42 v0.1 cells and 28/42 v0.2 cells**. Pooling can hide a failed framing cell: Qwen 7B keyed has 96/100 valid trajectories overall but 46/50 in the payment framing, at both receipt-loss levels. Thus complete technical acceptance is not met even where pooled action validity exceeds 95%.

All six v0.2 freezes verify through their sealed amendment chain; superseded bytes are checked against exact original witnesses. The native active r5 verifier passes. All 47,699 pre-v0.2 files matched the preserved baseline before this delivery. Frozen root RESULTS.md/PROJECT_STATE.md and root inventory remain intact; all reports, questions and helpers are under delivery/. Collection is complete: 1,860 scheduled active terminals; the two historical Claude DNS/schema terminals remain archived and are not additional model episodes. No collection, live inference, Git push, publication or v0.3 was performed in this task.

r1 operational usage-limit handling; r2 saved-envelope audit/generated-error handling; r3 definite zero-generation DNS non-start ruling and transport handling; r4 actual API-400 diagnosis; r5 provider-schema compatibility ruling are retained, with no historical evidence overwritten. The r5 Claude action schema is a provider-compatible superset only for cross-field combinations; the unchanged strict validator retains toolkit legality. Local constrained action schemas and unchanged JSON-mode reports were used. v0.1 results were seen before v0.2 P1–P7 re-registration. See [frozen deviations](../DEVIATIONS.md) and [protocol](../PROTOCOL.md).

| Operational event | ID | Cost | Model behavior? |
| --- | --- | --- | --- |
| dns non-start | claude-s00-notification-r50-check-0 | 0 | No |
| harness non-start | claude-s00-notification-r50-check-0-attempt1 | 0 | No |

There were zero saved usage-limit refusals in this collection, one DNS non-start and one schema harness non-start, each zero-cost; no active transport-failure terminal was found. These are operational events, not model errors, prediction outcomes, or duplicate failures. Historical STOP and clearance records remain.

| Actor / content failure | Episodes |
| --- | --- |
| qwen1b / key | 44 |
| qwen1b / report boolean/null required | 74 |
| qwen1b / truncated model output | 128 |
| qwen7b / key | 2 |
| qwen7b / truncated model output | 6 |

Guarded offline verification: **144/146 passed; two errors**, zero network/model/Git execution. Both failing tests copy the completed live ledger into a paused-resume fixture and fail with `r5 lacks zero settlement or is terminal in ledger`; they are retained, not silently fixed. The prior pre-collection suite reported 146/146. The frozen analysis failure is separate: a stale r3-only push allowlist rejects the authentic r5 receipt before any score is produced. No analysis code, prompts, thresholds, output repairs, extra model episodes or statistical rescue were introduced.

## Spend and resource bounds

| Version | Actor | Episodes | Accepted/terminal calls | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- |
| v0.1 | Qwen 7B | 600 | 4958 | 1875560 | 69350 |
| v0.2 | Qwen 7B | 600 | 6516 | 2470248 | 93281 |
| v0.1 | Llama 8B | 600 | 2482 | 865762 | 47208 |
| v0.2 | Llama 8B | 600 | 6600 | 2503628 | 106951 |
| v0.1 | Qwen 1.5B | 600 | 1535 | 527565 | 22356 |
| v0.2 | Qwen 1.5B | 600 | 4892 | 1775342 | 96526 |
| v0.1 | Claude | 60 | 474 | 832385 | 80044 |
| v0.2 | Claude | 60 | 526 | 899051 | 81482 |

Conservative API-equivalent spend: v0.1 USD5.660781; new v0.2 USD6.093738; cumulative settled **USD11.754519**. Retained v0.1 holds **USD0.293888**; project exposure USD12.048407; protected reserve USD1. Accounting RECONCILED; no new unknown-usage calls. Cash billing and local energy/hardware costs are UNKNOWN. Local model accounting and post hoc simulator baselines add USD0 model-call spend.

Saved active-time settlements total 5,796.106 seconds local and 1,713.664 seconds frontier. The 18,534 active-terminal calls are separate from two operational non-start attempts.

Frozen limits: 1,800 local/60 Claude episodes, ten action decisions plus a report; at most 19,800/660 generated calls; 12 local/2 frontier active hours; 180/420-second call timeouts; USD25 cumulative dispatch envelope, USD39 operational backstop, strict under-USD40 ceiling. No spending limit was reached. This benchmark assumes atomic permanent key bindings, four jobs, fixed draw generator and small fixed model samples; it does not test delayed delivery, expiry, real APIs, adversarial receivers or production impact. Across-version changes are descriptive: no paired causal decoding-effect test was registered, and Claude also has a disclosed schema compatibility amendment. Stop after v0.2. Scientific acceptance and Claude independent review remain unclaimed.

## Fresh-clone reproduction

See [README](README.md) for commands. The full v0.2 package is copied with only `__pycache__`, `.DS_Store`, `.git` and `*.lock` removed. The fresh-clone verifier permits only these absent files, reports their saved hashes, and still checks every present file. Historical pre-v0.2 inventory is an archive-preservation statement, not a dependency requiring a sibling checkout. Portable v0.1 results and provenance are under source-v01/. The package manifest covers every delivered nontransient file except its own recursive hash, and lists omitted transient hashes.

Rebuild evidence: `rebuild-verification.json`. Full sanitized copy: native r5 freeze PASS; original frozen-analysis failure reproduced. Descriptive replay and both post hoc baseline artifacts are byte-identical. Frozen numerical analysis identity is UNKNOWN because neither invocation produced a result.

