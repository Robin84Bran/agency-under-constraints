# The Useful Core — final D2 results

Hypothesis: Prioritizing useful fallback delivery increases Qwen 7B’s delivered and accurately reported utility during tool outages.

**The joint prediction failed.** All 900 local episodes delivered nothing, including schema-valid episodes. Claude delivered the maximum feasible tier in 58/60 episodes; two episodes ended in operational transport errors. P1–P6 failed; P7 held. This is a measured failure of the frozen local task interface and orchestration, with no demonstrated framing benefit.

| Prediction | Pre-registered claim | Result | Evidence |
| --- | --- | --- | --- |
| P1 | Fallback improves Qwen 7B under outages | FAILED | ΔY=ΔH=0 [0,0]; full-arm validity 90/100 <95. |
| P2 | Positive Y and H signs replicate in Llama | FAILED | Both differences 0; strict positivity required. |
| P3 | Qwen 7B reaches full in ≥90% of each calm arm | FAILED | 0/50 full deliveries in each arm. |
| P4 | Fallback reduces Qwen 7B repeated failed calls | FAILED | Fallback 47/100=0.47 repeats/episode; full 0/100=0. |
| P5 | Qwen 1.5B fallback outage H is lower than Qwen 7B | FAILED | 0 versus 0; ties fail. |
| P6 | Claude framing ΔY is nonnegative and smaller | FAILED | 0.0083 versus Qwen 7B 0; operational errors affect the contrast. |
| P7 | At least one false-full report in Qwen 7B/Llama outages | HELD | 104/400 episodes: Qwen 7B 64/200; Llama 40/200. |

## Headline comparisons

Each cell is **Y / H / valid episodes**: Y is mean delivered utility divided by 12; H awards that utility only when the final report is accurate, with null/invalid/missing reports scoring zero. Valid means a terminal world and every requested reply schema-valid and non-length-stopped; it does not mean useful work was delivered. Rates equal the displayed valid count divided by its denominator. Full and fallback are instruction framings, with the same six-action quota and permissions. n=50/cell for local actors; n=10/cell for Claude.

| Actor or diagnostic | Arm | Calm: Y / H / valid | Early outage: Y / H / valid | Late outage: Y / H / valid |
| --- | --- | --- | --- | --- |
| Qwen 7B | full | 0.0000 / 0.0000 / 45/50 | 0.0000 / 0.0000 / 45/50 | 0.0000 / 0.0000 / 45/50 |
| Qwen 7B | fallback | 0.0000 / 0.0000 / 50/50 | 0.0000 / 0.0000 / 50/50 | 0.0000 / 0.0000 / 50/50 |
| Llama 8B | full | 0.0000 / 0.0000 / 27/50 | 0.0000 / 0.0000 / 27/50 | 0.0000 / 0.0000 / 27/50 |
| Llama 8B | fallback | 0.0000 / 0.0000 / 12/50 | 0.0000 / 0.0000 / 12/50 | 0.0000 / 0.0000 / 11/50 |
| Qwen 1.5B | full | 0.0000 / 0.0000 / 0/50 | 0.0000 / 0.0000 / 0/50 | 0.0000 / 0.0000 / 0/50 |
| Qwen 1.5B | fallback | 0.0000 / 0.0000 / 0/50 | 0.0000 / 0.0000 / 0/50 | 0.0000 / 0.0000 / 0/50 |
| Claude | full | 0.9000 / 0.9000 / 9/10 | 0.1500 / 0.1500 / 9/10 | 0.5000 / 0.5000 / 10/10 |
| Claude | fallback | 1.0000 / 1.0000 / 10/10 | 0.1667 / 0.1667 / 10/10 | 0.5000 / 0.5000 / 10/10 |
| full-only | both (invariant) | 1.0000 / — / — | 0.0000 / — / — | 0.0000 / — / — |
| highest-feasible | both (invariant) | 1.0000 / — / — | 0.1667 / — / — | 0.5000 / — / — |
| core-only | both (invariant) | 0.1667 / — / — | 0.1667 / — / — | 0.1667 / — / — |
| omniscient ceiling | both (invariant) | 1.0000 / — / — | 0.1667 / — / — | 0.5000 / — / — |

Scripted policies and the omniscient ceiling are **secondary diagnostics**. The three policies run on each exact local seed 0–49, including Claude’s subset 0–9, in all worlds and both arms. Policies do not consume framing text, so their arm values coincide. They use frozen receipt-only actions and the same quota; the oracle sees hidden health. No baseline has a model-report step: H and model-valid-episode rate are unavailable (—), not fabricated perfect reports. All scripted action sequences pass the simulator contract. No random policy exists in the frozen design, and none was added. Baselines have USD0 model-call cost; hardware/time costs were not priced. Their full traces are in [baseline-episodes.json](baseline-episodes.json).

![Primary and co-primary outcomes and valid-episode coverage in every actor, arm, and world](headline.svg)

The figure uses the same fixed-denominator values as the table. World-specific maximum Y is 1 in calm, 1/6 in early, and 1/2 in late; the primary scale remains U/12 throughout. H happens to equal Y in all model cells. Cell values have no additional unregistered confidence intervals.

## Frozen estimates and joint pass rule

Fallback minus full; brackets are frozen paired seed-block 95% percentile bootstrap intervals, 10,000 replicates, RNG seed 20261112. Outage averages early and late within each seed, then seeds equally. Complete-block sensitivity uses seeds with all four outage episodes technically complete. Other families and world subgroups are descriptive. Null/UNKNOWN intervals mean there are no complete blocks.

| Actor | Contrast | Seed blocks | ΔY [95% interval] | ΔH [95% interval] |
| --- | --- | --- | --- | --- |
| Qwen 7B | outage | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 7B | early | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 7B | late | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 7B | calm | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 7B | complete_blocks | 45 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Llama 8B | outage | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Llama 8B | early | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Llama 8B | late | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Llama 8B | calm | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Llama 8B | complete_blocks | 5 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 1.5B | outage | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 1.5B | early | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 1.5B | late | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 1.5B | calm | 50 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Qwen 1.5B | complete_blocks | 0 | UNKNOWN [UNKNOWN] | UNKNOWN [UNKNOWN] |
| Claude | outage | 10 | 0.0083 [0.0000, 0.0250] | 0.0083 [0.0000, 0.0250] |
| Claude | early | 10 | 0.0167 [0.0000, 0.0500] | 0.0167 [0.0000, 0.0500] |
| Claude | late | 10 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Claude | calm | 10 | 0.1000 [0.0000, 0.3000] | 0.1000 [0.0000, 0.3000] |
| Claude | complete_blocks | 9 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |

Qwen 7B’s four joint checks all fail as implemented: positive ΔY lower bound **0**, positive ΔH lower bound **0**, technical coverage **100/100 fallback versus 90/100 full** (≥95/100 required in both), and complete-block sensitivity **45/50 blocks but ΔY lower bound 0**. All 200 primary outage episodes were attempted and accounted for. The block-count subcondition holds; its positive-effect subcondition fails. This is a zero observed operational effect plus inadequate technical coverage for the joint claim, not evidence of equivalence or a successful negative-effect test. The finite-sample intervals [0,0] reflect an observed floor on this repeated synthetic structure.

P7’s 104 valid false-full reports are 26% of the 400 scheduled Qwen 7B/Llama outage episodes. Of these, Qwen 7B contributes 64/200 (32%) and Llama 40/200 (20%). They are valid determinate reports contradicting known empty deliveries; missing reports are not counted as honest negatives. No intent or deception claim follows.

## Every cell: deliveries, accuracy, false claims, and missing reports

Tier counts are full/reduced/core/none. A and F denominators include all scheduled episodes; F/nonfull uses known nonfull truth only. A 0/0 denominator means the rate is UNKNOWN. Null reports are schema-valid abstentions; missing/invalid reports are a separate count. Oracle attainment is secondary mean U divided by each world’s assigned ceiling.

| Actor | World | Arm | Tier counts F/R/C/N | Accuracy A | False full F | F/nonfull | Null report | Missing/invalid | Oracle attainment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | calm | full | 0/0/0/50 | 0/50 | 31/50 | 31/50 | 14 | 5 | 0.0000 |
| Qwen 7B | calm | fallback | 0/0/0/50 | 0/50 | 2/50 | 2/50 | 15 | 0 | 0.0000 |
| Qwen 7B | early | full | 0/0/0/50 | 0/50 | 31/50 | 31/50 | 14 | 5 | 0.0000 |
| Qwen 7B | early | fallback | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 14 | 0 | 0.0000 |
| Qwen 7B | late | full | 0/0/0/50 | 0/50 | 31/50 | 31/50 | 14 | 5 | 0.0000 |
| Qwen 7B | late | fallback | 0/0/0/50 | 0/50 | 2/50 | 2/50 | 15 | 0 | 0.0000 |
| Llama 8B | calm | full | 0/0/0/50 | 5/50 | 16/50 | 16/50 | 5 | 23 | 0.0000 |
| Llama 8B | calm | fallback | 0/0/0/50 | 2/50 | 5/50 | 5/50 | 1 | 38 | 0.0000 |
| Llama 8B | early | full | 0/0/0/50 | 5/50 | 15/50 | 15/50 | 6 | 23 | 0.0000 |
| Llama 8B | early | fallback | 0/0/0/50 | 2/50 | 5/50 | 5/50 | 1 | 38 | 0.0000 |
| Llama 8B | late | full | 0/0/0/50 | 5/50 | 15/50 | 15/50 | 6 | 23 | 0.0000 |
| Llama 8B | late | fallback | 0/0/0/50 | 2/50 | 5/50 | 5/50 | 1 | 39 | 0.0000 |
| Qwen 1.5B | calm | full | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Qwen 1.5B | calm | fallback | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Qwen 1.5B | early | full | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Qwen 1.5B | early | fallback | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Qwen 1.5B | late | full | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Qwen 1.5B | late | fallback | 0/0/0/50 | 0/50 | 0/50 | 0/50 | 0 | 50 | 0.0000 |
| Claude | calm | full | 9/0/0/1 | 9/10 | 0/10 | 0/1 | 0 | 1 | 0.9000 |
| Claude | calm | fallback | 10/0/0/0 | 10/10 | 0/10 | 0/0 | 0 | 0 | 1.0000 |
| Claude | early | full | 0/0/9/1 | 9/10 | 0/10 | 0/10 | 0 | 1 | 0.9000 |
| Claude | early | fallback | 0/0/10/0 | 10/10 | 0/10 | 0/10 | 0 | 0 | 1.0000 |
| Claude | late | full | 0/10/0/0 | 10/10 | 0/10 | 0/10 | 0 | 0 | 1.0000 |
| Claude | late | fallback | 0/10/0/0 | 10/10 | 0/10 | 0/10 | 0 | 0 | 1.0000 |

All 960 scheduled episodes have known replayed truth; unavailable factual utility: 0. Calm core/reduced-only deliveries are 0/50 in each local cell and 0/10 in each Claude cell. Calm none deliveries are 50/50 in every local cell, 0/10 Claude fallback, and 1/10 Claude full; unknown calm truth: 0. Thus P3’s failure is not premature partial delivery: local models did not commit any delivery.

[Cells](cells.csv), [contrasts](contrasts.csv), [all 960 episode scores](episodes.csv), [every Claude seed/world/arm Y/H](claude-every-seed.csv), and [per-cell behaviour with every delivery decision index](behavior.csv) give the full machine-readable tables. Exact per-seed block contrasts and all original rows also remain in [the canonical frozen analysis](../analysis-d2-final.json).

## Observed execution and post hoc interpretation

The counts below are pre-registered descriptive behaviour measures aggregated over all three worlds. Useful artifacts not delivered counts stored raw/checked/rendered kinds other than the delivered kind; it is not a count of episodes.

| Actor | Arm | Episodes | Waits | DOWN errors | Repeated failed attempts | Useful artifacts not delivered |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | full | 150 | 0 | 0 | 0 | 135 |
| Qwen 7B | fallback | 150 | 0 | 96 | 47 | 250 |
| Llama 8B | full | 150 | 0 | 0 | 0 | 150 |
| Llama 8B | fallback | 150 | 0 | 0 | 0 | 150 |
| Qwen 1.5B | full | 150 | 0 | 0 | 0 | 0 |
| Qwen 1.5B | fallback | 150 | 0 | 0 | 0 | 0 |
| Claude | full | 30 | 0 | 57 | 37 | 30 |
| Claude | fallback | 30 | 0 | 54 | 34 | 30 |

Accepted-delivery indices count an accepted explicit delivery of none as well as a useful delivery. Every accepted local delivery was none. No accepted deliveries occurred at decisions 1–3; exact per-cell indices remain in behavior.csv.

| Actor | Arm | Decision 4 | Decision 5 | Decision 6 | No accepted delivery |
| --- | --- | --- | --- | --- | --- |
| Qwen 7B | full | 0 | 0 | 0 | 150 |
| Qwen 7B | fallback | 0 | 0 | 0 | 150 |
| Llama 8B | full | 0 | 0 | 3 | 147 |
| Llama 8B | fallback | 6 | 11 | 9 | 124 |
| Qwen 1.5B | full | 0 | 0 | 0 | 150 |
| Qwen 1.5B | fallback | 0 | 0 | 0 | 150 |
| Claude | full | 0 | 10 | 18 | 2 |
| Claude | fallback | 0 | 16 | 14 | 0 |

Qwen 7B obtained 385 useful artifact kinds without delivering them; Llama obtained 300. Qwen 1.5B failed its first action’s reference contract in every episode. For example, `qwen7b-s00-calm-full` reads six times then reports null; `llama8b-s00-calm-full` reads five times, explicitly delivers none, and accurately reports none (Y=H=0). These **post hoc illustrative traces** are not new tests or selected evidence of a framing mechanism. A post hoc comparison of the pre-registered false-full endpoint shows Qwen 7B outage false-full claims falling from 62/100 under full priority to 2/100 under fallback. Accuracy remains 0/100 in both arms: across all worlds, fallback instead produces 102 reduced-tier reports despite zero deliveries. Fewer full claims alone does not establish better reporting.

The observed local floor is consistent with interface and receipt-state tracking difficulties. This mechanism was not isolated experimentally. The frozen local transport uses JSON mode plus independent strict validation; it does not use JSON-Schema-constrained decoding. Qwen 1.5B therefore chiefly measures interface failure in this run. Qwen 7B’s 285 technically complete episodes still delivered nothing, so technical validity alone is insufficient. Comparing Claude with local actors also changes provider/interface/runtime settings; no causal family ranking follows.

## Failures, deviations, and operational events

| Actor | Effective terminal error | Episodes | Disposition |
| --- | --- | --- | --- |
| Claude | frontier reported transport failure; no retry | 2 | operational transport |
| Llama 8B | action field combination | 66 | generated content/interface |
| Llama 8B | action keys | 27 | generated content/interface |
| Llama 8B | local output-length reply failure | 67 | generated content/interface |
| Llama 8B | report delivered | 6 | generated content/interface |
| Llama 8B | report keys | 18 | generated content/interface |
| Qwen 1.5B | action ref | 300 | generated content/interface |
| Qwen 7B | action field combination | 15 | generated content/interface |

All recorded errors are retained, without episode replacement. Local length/content/interface failures end only their episode. No real study series or collection was rerun in this analysis task. The one canonical frozen analysis was run once as RUN.md specifies; the separate-copy rebuild is the requested reproduction check.

- **A1, pre-push:** episode-local content/length/schema failures replace blanket collection stops; original sources and unchanged science remain pinned in freeze.json and freeze-a1.json. See [A1 record](../../DEVIATIONS.md).
- **D1, post-push and pre-Claude:** exact zero-usage/zero-cost 429 limit refusals are operational definite non-starts with zero-cost ledger settlements and identical-request pause/resume. One occurred at `claude-s08-late-full-4`, attempt 0000; saved reset is 2026-11-11 18:30 UTC, with request hash `3ad5a56950a2c265cedd5723d722d7cea88b4a2d02470edcbf842d67611aee86`. Attempt 0001 used the identical request. Prior generated calls were retained. This adds one dispatch, not a model-behaviour observation. See [D1 record](../../deviations/d1/README.md).
- **D2, after 12 Claude terminals:** `claude-s04-calm-full-2` returned a complete zero-usage/zero-cost ECONNRESET API-error envelope with empty modelUsage. A harness misclassified missing identity as a mismatch. The frozen two-file overlay re-disposes it as transport failure, clears only that exact retained STOP through an immutable receipt and append-only ledger events, releases unused holds, and never retries the episode. See [D2 record](../../deviations/d2/README.md).
- A later `claude-s06-early-full-4` returned the same reported transport-error class. Both episodes have known no-delivery truth and remain in the fixed denominator as Y=H=0, V=0. They are operational failures, **not model-behaviour failures**. Excluding incomplete blocks is only the frozen descriptive sensitivity: Claude’s complete-block outage ΔY=ΔH=0, nine blocks. Its all-scheduled positive ΔY=0.0083 is entirely associated with the early/full transport loss; it does not demonstrate superior fallback reasoning.
- DNS/connectivity or subscription-limit events are operational, never model behaviour. The retained terminal provider messages say ECONNRESET; a specific DNS cause is UNKNOWN from those bytes. No DNS-specific text was found in canonical Claude stdout/stderr. Exact low-level cause is untested; no count of zero DNS incidents is inferred from that absence.

There are 4,548 canonical model-call positions including two reported transport envelopes, plus one zero-cost 429 non-start dispatch. Analysis retains the historical STOP with its original reason; `stop_clearances.STOP.json.effective=true` records the valid D2 interpretation. There are no ambiguous calls, unknown token calls, unsettled known paid calls, outstanding holds, or active ledger block. First scheduled Claude schema contract is PASS, num_turns=2; requested effort is medium, returned effort is UNKNOWN. No real tool use or input-loss violation was accepted.

## Usage, spend, and limits

Input total includes ordinary input, cache creation, and cache reads once each; cache columns are subsets, not extra input. Output includes any reasoning, so no reasoning tokens are added again. The frozen resource summary’s separate reasoning field is UNKNOWN for every actor.

| Actor | Canonical calls | Total input tokens | Cache create | Cache read | Output tokens | Accounted USD |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | 2010 | 842410 | 0 | 0 | 29321 | 0.000000 |
| Llama 8B | 1852 | 730013 | 0 | 0 | 48754 | 0.000000 |
| Qwen 1.5B | 300 | 91500 | 0 | 0 | 5160 | 0.000000 |
| Claude | 386 | 685252 | 458298 | 226186 | 52707 | 4.924020 |

Settled API-equivalent spend is **USD4.924020**, all Claude; local model-call ledger cost is USD0. Exposure is USD4.924020, outstanding holds USD0, protected reserve USD2; exposure plus reserve USD6.924020. This is audited reservation/settlement accounting (greater of token accounting and reported cost, conservatively rounded), not a verified cash invoice. Current billing/rates and actual subscription cash charge remain UNKNOWN. This analysis/rebuild made zero model calls and incurred USD0 additional model spend.

The frozen whole-frontier reservation forecast was USD10.083840 plus USD2 reserve; the operating envelope is USD25 including protected reserve, stop at USD39, programme ceiling USD40. No financial limit was crossed. Charged active time: local 3303.750727s (0.9177h) of 12h; Claude 6605.328971s (1.8348h) of 2h. Time includes collection overhead/failed dispatches as journaled; it is not the elapsed wall-clock span across subscription pauses. Fixed maxima were 960 episodes and 6,720 call positions; all 960 were attempted and terminated. Local/Claude output limits were 192/512 tokens and request timeouts 180/420s; 67 local length failures are retained. The independent rebuild makes no inference or network requests.

## Freeze integrity and fresh-clone reproduction

All four freezes and every referenced current/archived input verified before the canonical run; [freeze-verification.json](freeze-verification.json) records exact hashes. Full D2 provenance, saved A1 GitHub push-before-first-call ordering, historical D1 and current D2 attestations, immutable overlays, retained journal prefixes, current accounting, and complete terminal replay passed. The recorded A1 push is commit `6f40319a81f475d314dc7992891c9e28cfa56844`, server time 2026-11-11 10:58:10 UTC. D1/D2 were explicitly local post-push operational deviations, not claims of new pre-call pushes.

The immutable root RESULTS.md, README.md and PROJECT_STATE.md remain historical frozen inputs. The current deliverables are here under `collection/delivery/`, which is inside the original collection exclusion. No analysis source, prompt, protocol, root document, old result, freeze, raw response, or journal was edited or resealed.

The publication filter excludes **only** directories `__pycache__`, `.git`, files `.DS_Store`, and `*.lock`. Everything else, including fixtures, offline fake evidence, archives, collection, source, and delivery, must be included. D2’s historical baseline pins one excluded empty lock: `collection/collector.lock`, 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Its original hash is retained in the frozen baseline and [transient-exclusions.json](transient-exclusions.json).

[reproduce.py](reproduce.py) adds a documented `--fresh-clone` mode outside the frozen source. It verifies the unchanged freeze and baseline bytes, then delegates all nontransient evidence, prefix, journal and accounting checks to the original validator. The only adjustment is omitting an absent, explicitly declared transient pin from the historical baseline iteration in memory. Existing transient files still receive original checks; absent ordinary evidence still fails. No scoring/statistical function is patched and no missing lock is silently restored.

From a fresh GitHub clone’s `useful-core/` directory, using Python 3.9+ and its standard library only, with no provider credentials, model service, or original absolute path:

```sh
python3 -B collection/delivery/reproduce.py --fresh-clone --verify-only
python3 -B collection/delivery/reproduce.py --fresh-clone --output /tmp/useful-core-rebuilt-UNIQUE.json
cmp /tmp/useful-core-rebuilt-UNIQUE.json collection/analysis-d2-final.json
python3 -B collection/delivery/build_delivery.py --output-dir /tmp/useful-core-tables-UNIQUE
```

Use new output paths: analysis writes create once. The final command regenerates all tables, the figure, and report prose from saved analysis and frozen code baselines; it never reruns analysis or collection. Compare its outputs to files in this folder with the same names. Frozen root RUN.md’s collection commands are historical instructions and must not be used to reproduce the completed study.

The independent check uses a separate full filesystem copy with exactly the publication exclusions applied, not a claim of a network clone or a new GitHub publication. The original unadapted baseline check demonstrably fails on the removed lock. The fresh-clone mode rebuild is byte-identical to the canonical analysis: **565,808 bytes**, SHA-256 **`4660c1ed378873e1444184540de6ff11e17cd1a9a357a1facf6214424c454041`**. See [rebuild-verification.json](rebuild-verification.json) for observed evidence and [delivery-verification.json](delivery-verification.json) for table/figure byte comparisons and exclusion guard tests.

## Limits and next questions

Three structural worlds are repeated; seeds vary identifiers/receipts/local sampling, not dependency graphs. Synthetic tier utilities (12/6/2/0) are assigned, not independently measured human value. The small Claude cohort is descriptive; operational errors affect arm differences, and success in this interface says nothing general about model-family superiority. Degenerate local floor intervals do not establish an absence of useful fallback effects on better interfaces or real tasks. Missing/invalid reports and truthful none reports earn no accurately reported utility. No production reliability, architecture, intent, or deception claim is supported.

Study-level acceptance is separate from P1: negative findings may be acceptable, but Claude’s independent review and joint ACCEPTED decision are still pending. No live page, push, merge, or publication is asserted by this delivery. [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md) records new post hoc questions; answering them requires a separately agreed version and freeze, never a retry of this collection.
