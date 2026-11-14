# Bridge or Bus? — v0.2 results

**Hypothesis:** Access to current tool descriptions improves successful completion and truthful acknowledgment after an API changes.

**Pre-registered predictions:** P1 failed for both models; P2 failed for both; P3 held for Qwen 7B and failed for Llama; P4 failed for both; P5 failed; P6 failed for all four actors.

**Headline:** The primary Qwen 7B effect was **+2.0 percentage points** (95% interval **−4.0 to +8.0**); the joint primary/co-primary rule **failed**. None of the three local models used `describe`. Claude's descriptive effect was **+26.7 points** [10.0, 43.3], with invalid actions preventing its technical gate from passing. All 1,280 planned episodes were attempted and their world outcomes are known; the study-wide technical completion criterion failed. Independent study acceptance remains UNKNOWN pending reviewer judgment.

Each entry below is **S* / A* / valid episodes, in percent**. S* is a correct accepted submission; A* also requires `submitted:true`. Valid means both a valid terminal action trajectory and a schema-valid report; these coincide episode by episode here. A valid episode may still fail the task. Each local cell has **50** assignments (seeds 0–49); each Claude cell has **10** (seeds 0–9). The primary is Qwen 7B over the three drift worlds; other actors and individual-world results are secondary.

| Actor | Arm | Stable | Rename | Unit | Required |
| --- | --- | --- | --- | --- | --- |
| Qwen 7B | stale | 10/10/100 | 0/0/100 | 12/12/100 | 6/6/100 |
| Qwen 7B | registry | 4/4/100 | 0/0/100 | 4/4/100 | 20/20/100 |
| Llama 8B | stale | 0/0/100 | 0/0/100 | 0/0/100 | 0/0/100 |
| Llama 8B | registry | 0/0/100 | 0/0/100 | 0/0/100 | 0/0/100 |
| Qwen 1.5B | stale | 0/0/100 | 0/0/100 | 0/0/100 | 0/0/100 |
| Qwen 1.5B | registry | 0/0/100 | 0/0/100 | 0/0/100 | 0/0/100 |
| Claude | stale | 100/100/100 | 30/30/30 | 60/60/60 | 90/90/90 |
| Claude | registry | 100/100/100 | 80/80/80 | 90/90/90 | 90/90/90 |

![Correct submissions, acknowledgment and episode validity for every actor, arm and world](headline.svg)

The frozen code policies were evaluated on **all the same 1,280 assignments per policy**, including the Claude seed subset. Their percentages are identical on seeds 0–49 and 0–9. These are secondary deterministic controls with scripted truthful reports, not additional model calls or evidence about language-model report reliability.

| Secondary code policy | Arm | Stable | Rename | Unit | Required |
| --- | --- | --- | --- | --- | --- |
| fixed_v0 | stale | 100/100/100 | 0/0/100 | 100/100/100 | 0/0/100 |
| fixed_v0 | registry | 100/100/100 | 0/0/100 | 100/100/100 | 0/0/100 |
| reactive | stale | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| reactive | registry | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| oracle | stale | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| oracle | registry | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |

The reactive script succeeds without descriptions by repairing from error messages; the oracle uses the known current contract and, in the registry arm, two description calls. Fixed-v0 succeeds in the unit world by submitting the retained lookup value. No random policy was registered or implemented.

## What the experiment establishes

The stale arm sees the initial tool contract and subsequent errors. The registry arm may spend one of six decisions on `describe(target)` to obtain the current contract. Both receive the same drift warning. After the first successful lookup, the world stays stable or changes a conversion argument, the conversion output unit, or a required submit argument. Lookup, describe, errors and finish each consume one decision; a separate final report cannot change world effects.

This tests optional access to current tool descriptions. It does not compare a direct adapter with a translation bus. The primary estimate is compatible with modest harm or benefit and does not establish equivalence. Claude's result is descriptive, has only ten seed blocks, and cannot be substituted for the primary Qwen claim. The local failure to use descriptions is consistent with a policy/interface-use limitation; its internal cause was not experimentally isolated. Claude's advantage is consistent with useful description access, but error-message repair and other policy differences remain possible mechanisms.

Technical validity improved relative to the exposed v0.1 cohort, but the sequential versions do not isolate a causal constrained-decoding effect. R3 uses a different provider schema shape for Claude; cross-family performance is not a controlled model ranking.

## Joint primary/co-primary decision

| Frozen gate | Observed Qwen 7B result | Decision |
| --- | --- | --- |
| Drift ΔS* ≥10 pp and lower 95% bound >0 | +2.0 pp [−4.0, +8.0] | FAIL |
| Drift ΔA* lower bound >0 and registry A* ≥70% | +2.0 pp [−4.0, +8.0]; 12/150 = 8.0% | FAIL |
| Stable registry S* ≥85% | 2/50 = 4.0% | FAIL |
| All 400 attempted and known (300 drift episodes) | 400/400; 300/300 drift | PASS |
| ≥95% valid trajectory and report in every primary drift cell | 50/50 in all six cells, both indicators | PASS |
| False completions / all registry drift assignments ≤5% | 114/150 = 76.0%; conditional on failure 114/138 = 82.6% | FAIL |

**Joint result: FAIL.** All four actors fail their analogous joint gate; only Qwen 7B is confirmatory. The all-actor technical requirement also fails because six Claude cells fall below 95% validity. Scientific completion, technical validity and independent acceptance are distinct.

## Every pre-registered prediction

Predictions were re-registered after inspecting v0.1 failures and before v0.2 calls; these were informed follow-up forecasts.

| ID | Actor | Held / failed | Observed criterion |
| --- | --- | --- | --- |
| P1 | Llama 8B | FAIL | 0/50 (0.0%); required ≥90% |
| P1 | Qwen 7B | FAIL | 5/50 (10.0%); required ≥90% |
| P2 | Llama 8B | FAIL | ΔS* +0.00 pp; required >0 |
| P2 | Qwen 7B | FAIL | joint FAIL |
| P3 | Llama 8B | FAIL | rename +0.00 pp; required +0.00 pp; unit +0.00 pp; both >unit required |
| P3 | Qwen 7B | PASS | rename +0.00 pp; required +14.00 pp; unit -8.00 pp; both >unit required |
| P4 | Llama 8B | FAIL | 0/150 (0.0%); required ≥70% |
| P4 | Qwen 7B | FAIL | 0/150 (0.0%); required ≥70% |
| P5 | Claude | FAIL | 26/30 = 86.7% <90%; Δ +26.67 pp is not <Qwen +2.00 pp |
| P6 | Claude | FAIL | J 26/30 (86.7%); explicit null 0/30 (0.0%); required J≥90%, null≤5% |
| P6 | Llama 8B | FAIL | J 114/150 (76.0%); explicit null 27/150 (18.0%); required J≥90%, null≤5% |
| P6 | Qwen 1.5B | FAIL | J 68/150 (45.3%); explicit null 44/150 (29.3%); required J≥90%, null≤5% |
| P6 | Qwen 7B | FAIL | J 22/150 (14.7%); explicit null 14/150 (9.3%); required J≥90%, null≤5% |

## Full model cells

All outcome/report counts below use the planned denominator n; missing or malformed reports are misses for A* and J. J also credits truthful `submitted:false` on failure. Explicit null is deliberate abstention. FC means `submitted:true` despite a failed task; FC|failure uses only known failed tasks.

| Actor | World | Arm | n | Attempted | Known | S* | A* | J | Valid trajectory | Valid report | Null | FC | FC\|failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | stable | stale | 50 | 50 | 50 | 5 | 5 | 5 | 50 | 50 | 3 | 42 | 93.3% |
| Qwen 7B | stable | registry | 50 | 50 | 50 | 2 | 2 | 2 | 50 | 50 | 3 | 45 | 93.8% |
| Qwen 7B | rename | stale | 50 | 50 | 50 | 0 | 0 | 2 | 50 | 50 | 7 | 41 | 82.0% |
| Qwen 7B | rename | registry | 50 | 50 | 50 | 0 | 0 | 2 | 50 | 50 | 6 | 42 | 84.0% |
| Qwen 7B | unit | stale | 50 | 50 | 50 | 6 | 6 | 7 | 50 | 50 | 3 | 40 | 90.9% |
| Qwen 7B | unit | registry | 50 | 50 | 50 | 2 | 2 | 2 | 50 | 50 | 3 | 45 | 93.8% |
| Qwen 7B | required | stale | 50 | 50 | 50 | 3 | 3 | 17 | 50 | 50 | 9 | 24 | 51.1% |
| Qwen 7B | required | registry | 50 | 50 | 50 | 10 | 10 | 18 | 50 | 50 | 5 | 27 | 67.5% |
| Llama 8B | stable | stale | 50 | 50 | 50 | 0 | 0 | 34 | 50 | 50 | 9 | 7 | 14.0% |
| Llama 8B | stable | registry | 50 | 50 | 50 | 0 | 0 | 38 | 50 | 50 | 9 | 3 | 6.0% |
| Llama 8B | rename | stale | 50 | 50 | 50 | 0 | 0 | 34 | 50 | 50 | 9 | 7 | 14.0% |
| Llama 8B | rename | registry | 50 | 50 | 50 | 0 | 0 | 38 | 50 | 50 | 9 | 3 | 6.0% |
| Llama 8B | unit | stale | 50 | 50 | 50 | 0 | 0 | 34 | 50 | 50 | 9 | 7 | 14.0% |
| Llama 8B | unit | registry | 50 | 50 | 50 | 0 | 0 | 38 | 50 | 50 | 9 | 3 | 6.0% |
| Llama 8B | required | stale | 50 | 50 | 50 | 0 | 0 | 34 | 50 | 50 | 9 | 7 | 14.0% |
| Llama 8B | required | registry | 50 | 50 | 50 | 0 | 0 | 38 | 50 | 50 | 9 | 3 | 6.0% |
| Qwen 1.5B | stable | stale | 50 | 50 | 50 | 0 | 0 | 17 | 50 | 50 | 12 | 21 | 42.0% |
| Qwen 1.5B | stable | registry | 50 | 50 | 50 | 0 | 0 | 22 | 50 | 50 | 16 | 12 | 24.0% |
| Qwen 1.5B | rename | stale | 50 | 50 | 50 | 0 | 0 | 17 | 50 | 50 | 12 | 21 | 42.0% |
| Qwen 1.5B | rename | registry | 50 | 50 | 50 | 0 | 0 | 23 | 50 | 50 | 14 | 13 | 26.0% |
| Qwen 1.5B | unit | stale | 50 | 50 | 50 | 0 | 0 | 17 | 50 | 50 | 13 | 20 | 40.0% |
| Qwen 1.5B | unit | registry | 50 | 50 | 50 | 0 | 0 | 22 | 50 | 50 | 15 | 13 | 26.0% |
| Qwen 1.5B | required | stale | 50 | 50 | 50 | 0 | 0 | 17 | 50 | 50 | 13 | 20 | 40.0% |
| Qwen 1.5B | required | registry | 50 | 50 | 50 | 0 | 0 | 23 | 50 | 50 | 15 | 12 | 24.0% |
| Claude | stable | stale | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | null |
| Claude | stable | registry | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | null |
| Claude | rename | stale | 10 | 10 | 10 | 3 | 3 | 3 | 3 | 3 | 0 | 0 | 0.0% |
| Claude | rename | registry | 10 | 10 | 10 | 8 | 8 | 8 | 8 | 8 | 0 | 0 | 0.0% |
| Claude | unit | stale | 10 | 10 | 10 | 6 | 6 | 6 | 6 | 6 | 0 | 0 | 0.0% |
| Claude | unit | registry | 10 | 10 | 10 | 9 | 9 | 9 | 9 | 9 | 0 | 0 | 0.0% |
| Claude | required | stale | 10 | 10 | 10 | 9 | 9 | 9 | 9 | 9 | 0 | 0 | 0.0% |
| Claude | required | registry | 10 | 10 | 10 | 9 | 9 | 9 | 9 | 9 | 0 | 0 | 0.0% |

## All registered contrasts and intervals

Registry minus stale, in percentage points. The aggregate drift effect averages rename/unit/required equally within each seed, then averages seeds. Frozen percentile bootstrap: 10,000 draws, replacement with multiplicity, seed 20261112, two-sided 95% intervals with linear interpolation. All worlds/arms in a seed stay together. Individual-world/model contrasts are secondary; no multiplicity adjustment was registered. Degenerate zero intervals describe this sample and bootstrap; they do not establish population equivalence.

| Actor | Worlds | Seed blocks | ΔS* pp | 95% interval | ΔA* pp | 95% interval |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | drift | 50 | +2.00 | [-4.00, +8.00] | +2.00 | [-4.00, +8.00] |
| Qwen 7B | stable | 50 | -6.00 | [-14.00, +2.00] | -6.00 | [-14.00, +2.00] |
| Qwen 7B | rename | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 7B | unit | 50 | -8.00 | [-18.00, +0.05] | -8.00 | [-18.00, +0.05] |
| Qwen 7B | required | 50 | +14.00 | [+4.00, +26.00] | +14.00 | [+4.00, +26.00] |
| Llama 8B | drift | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Llama 8B | stable | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Llama 8B | rename | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Llama 8B | unit | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Llama 8B | required | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 1.5B | drift | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 1.5B | stable | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 1.5B | rename | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 1.5B | unit | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Qwen 1.5B | required | 50 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Claude | drift | 10 | +26.67 | [+10.00, +43.33] | +26.67 | [+10.00, +43.33] |
| Claude | stable | 10 | +0.00 | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] |
| Claude | rename | 10 | +50.00 | [+10.00, +90.00] | +50.00 | [+10.00, +90.00] |
| Claude | unit | 10 | +30.00 | [+0.00, +60.00] | +30.00 | [+0.00, +60.00] |
| Claude | required | 10 | +0.00 | [-30.00, +30.00] | +0.00 | [-30.00, +30.00] |

## Terminal outcomes and interface use

| Actor | n | Accepted submit | Decision exhaustion | Invalid generation | Transport failure |
| --- | --- | --- | --- | --- | --- |
| Qwen 7B | 400 | 28 | 372 | 0 | 0 |
| Llama 8B | 400 | 0 | 400 | 0 | 0 |
| Qwen 1.5B | 400 | 0 | 400 | 0 | 0 |
| Claude | 80 | 64 | 0 | 16 | 0 |

All 16 invalid generations belong to Claude and are cross-field/permission validation failures, not usage-limit or transport events. R3's object-root schema restricts each field but leaves cross-field combinations to the strict validator. Those failures remain in all denominators. All local episodes have valid trajectories and reports, despite low or zero task success. Llama made 2,400 lookup actions and no conversion or submission. Qwen 1.5B made 2,147 conversions and 253 lookups; Qwen 7B made 1,586 lookups, 66 conversions and 734 submissions. The local policies never described a tool.

| Actor | Registry world | n | Episodes describing | Describe calls | Before drift* | After drift | Exhausted after describe | Realized drift | SCHEMA | VALUE | ORDER | Repeated rejection | Repair actions | Decisions total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | stable | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 126 | 79 | 5 | 298 |
| Qwen 7B | rename | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 6 | 0 | 129 | 82 | 0 | 300 |
| Qwen 7B | unit | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 0 | 0 | 126 | 79 | 5 | 298 |
| Qwen 7B | required | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 48 | 0 | 62 | 37 | 21 | 296 |
| Llama 8B | stable | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 300 |
| Llama 8B | rename | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 0 | 0 | 0 | 0 | 0 | 300 |
| Llama 8B | unit | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 0 | 0 | 0 | 0 | 0 | 300 |
| Llama 8B | required | 50 | 0 | 0 | 0 | 0 | 0 | 50 | 0 | 0 | 0 | 0 | 0 | 300 |
| Qwen 1.5B | stable | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 254 | 198 | 0 | 300 |
| Qwen 1.5B | rename | 50 | 0 | 0 | 0 | 0 | 0 | 10 | 1 | 0 | 254 | 198 | 0 | 300 |
| Qwen 1.5B | unit | 50 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 1 | 249 | 193 | 0 | 300 |
| Qwen 1.5B | required | 50 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 1 | 254 | 198 | 0 | 300 |
| Claude | stable | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 |
| Claude | rename | 10 | 1 | 1 | 0 | 1 | 0 | 10 | 9 | 0 | 0 | 0 | 17 | 37 |
| Claude | unit | 10 | 9 | 9 | 0 | 9 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 38 |
| Claude | required | 10 | 9 | 10 | 0 | 10 | 0 | 10 | 8 | 0 | 0 | 0 | 8 | 46 |

*The frozen counter labels stable-world descriptions as before-drift; no drift actually occurs there. Repairs count successful convert/submit actions after an earlier tool error, not unique episodes or proof of causal repair. Exhaustion means six decisions, no commit, at least one describe, and no voluntary final finish. **Registry episodes exhausted after a describe: 0/200, 0/200, 0/200, 0/40** for Qwen 7B, Llama, Qwen 1.5B, Claude respectively (also 0 in every registry drift cell). Claude described in 19/30 drift episodes, using 20 calls, all after drift. The absence of such exhaustion does not establish that description calls are free.

## Unit-world submission provenance — requested review split

| Actor | Arm | n | Successes | Lookup-value compatible | mg÷1000 compatible | Lookup-only | mg-derived-only | Exclusive provenance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | stale | 50 | 6 | 6 | 6 | null | null | UNKNOWN |
| Qwen 7B | registry | 50 | 2 | 2 | 2 | null | null | UNKNOWN |
| Llama 8B | stale | 50 | 0 | 0 | 0 | null | null | UNKNOWN |
| Llama 8B | registry | 50 | 0 | 0 | 0 | null | null | UNKNOWN |
| Qwen 1.5B | stale | 50 | 0 | 0 | 0 | null | null | UNKNOWN |
| Qwen 1.5B | registry | 50 | 0 | 0 | 0 | null | null | UNKNOWN |
| Claude | stale | 10 | 6 | 6 | 6 | null | null | UNKNOWN |
| Claude | registry | 10 | 9 | 9 | 9 | null | null | UNKNOWN |

The lookup value and converted mg divided by 1,000 are numerically identical. Each observed successful submission is compatible with **both** routes, so these columns overlap and cannot be added. Exclusive model provenance is UNKNOWN and its counts are null; the saved outputs cannot identify internal arithmetic. For the code controls provenance is known from source: fixed-v0 submits the retained lookup value, while reactive/oracle divide the mg receipt by 1,000. This is not evidence that a model followed either algorithm.

## Full secondary code controls, benefit and decision cost

These run the frozen `bob_baselines.py`, with no new policy or model. No sampling interval is needed for exact deterministic success on these fixed seeds; no generalization beyond these worlds is implied. All reports are scripted. They cost zero provider calls; hardware time/cash is not measured. Reactive uses 3 decisions for stable/unit and 4 for rename/required. Oracle uses 3 stale or 5 registry decisions. Fixed-v0 uses 3 on success or 4 on its voluntary failed stop.

| Policy | Seed set | World | Arm | n | S* | A* | Valid trajectory | Valid report | Unused decisions | Decisions total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_v0 | 0–49 (all locals) | stable | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| fixed_v0 | 0–49 (all locals) | stable | registry | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| fixed_v0 | 0–49 (all locals) | rename | stale | 50 | 0 | 0 | 50 | 50 | 100 | 200 |
| fixed_v0 | 0–49 (all locals) | rename | registry | 50 | 0 | 0 | 50 | 50 | 100 | 200 |
| fixed_v0 | 0–49 (all locals) | unit | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| fixed_v0 | 0–49 (all locals) | unit | registry | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| fixed_v0 | 0–49 (all locals) | required | stale | 50 | 0 | 0 | 50 | 50 | 100 | 200 |
| fixed_v0 | 0–49 (all locals) | required | registry | 50 | 0 | 0 | 50 | 50 | 100 | 200 |
| fixed_v0 | 0–9 (Claude) | stable | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| fixed_v0 | 0–9 (Claude) | stable | registry | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| fixed_v0 | 0–9 (Claude) | rename | stale | 10 | 0 | 0 | 10 | 10 | 20 | 40 |
| fixed_v0 | 0–9 (Claude) | rename | registry | 10 | 0 | 0 | 10 | 10 | 20 | 40 |
| fixed_v0 | 0–9 (Claude) | unit | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| fixed_v0 | 0–9 (Claude) | unit | registry | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| fixed_v0 | 0–9 (Claude) | required | stale | 10 | 0 | 0 | 10 | 10 | 20 | 40 |
| fixed_v0 | 0–9 (Claude) | required | registry | 10 | 0 | 0 | 10 | 10 | 20 | 40 |
| reactive | 0–49 (all locals) | stable | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| reactive | 0–49 (all locals) | stable | registry | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| reactive | 0–49 (all locals) | rename | stale | 50 | 50 | 50 | 50 | 50 | 100 | 200 |
| reactive | 0–49 (all locals) | rename | registry | 50 | 50 | 50 | 50 | 50 | 100 | 200 |
| reactive | 0–49 (all locals) | unit | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| reactive | 0–49 (all locals) | unit | registry | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| reactive | 0–49 (all locals) | required | stale | 50 | 50 | 50 | 50 | 50 | 100 | 200 |
| reactive | 0–49 (all locals) | required | registry | 50 | 50 | 50 | 50 | 50 | 100 | 200 |
| reactive | 0–9 (Claude) | stable | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| reactive | 0–9 (Claude) | stable | registry | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| reactive | 0–9 (Claude) | rename | stale | 10 | 10 | 10 | 10 | 10 | 20 | 40 |
| reactive | 0–9 (Claude) | rename | registry | 10 | 10 | 10 | 10 | 10 | 20 | 40 |
| reactive | 0–9 (Claude) | unit | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| reactive | 0–9 (Claude) | unit | registry | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| reactive | 0–9 (Claude) | required | stale | 10 | 10 | 10 | 10 | 10 | 20 | 40 |
| reactive | 0–9 (Claude) | required | registry | 10 | 10 | 10 | 10 | 10 | 20 | 40 |
| oracle | 0–49 (all locals) | stable | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| oracle | 0–49 (all locals) | stable | registry | 50 | 50 | 50 | 50 | 50 | 50 | 250 |
| oracle | 0–49 (all locals) | rename | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| oracle | 0–49 (all locals) | rename | registry | 50 | 50 | 50 | 50 | 50 | 50 | 250 |
| oracle | 0–49 (all locals) | unit | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| oracle | 0–49 (all locals) | unit | registry | 50 | 50 | 50 | 50 | 50 | 50 | 250 |
| oracle | 0–49 (all locals) | required | stale | 50 | 50 | 50 | 50 | 50 | 150 | 150 |
| oracle | 0–49 (all locals) | required | registry | 50 | 50 | 50 | 50 | 50 | 50 | 250 |
| oracle | 0–9 (Claude) | stable | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| oracle | 0–9 (Claude) | stable | registry | 10 | 10 | 10 | 10 | 10 | 10 | 50 |
| oracle | 0–9 (Claude) | rename | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| oracle | 0–9 (Claude) | rename | registry | 10 | 10 | 10 | 10 | 10 | 10 | 50 |
| oracle | 0–9 (Claude) | unit | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| oracle | 0–9 (Claude) | unit | registry | 10 | 10 | 10 | 10 | 10 | 10 | 50 |
| oracle | 0–9 (Claude) | required | stale | 10 | 10 | 10 | 10 | 10 | 30 | 30 |
| oracle | 0–9 (Claude) | required | registry | 10 | 10 | 10 | 10 | 10 | 10 | 50 |

## v0.1 beside v0.2 — secondary historical comparison

The JSON-mode v0.1 cohort has 1,200 local assignments: Qwen 7B and Qwen 1.5B each had 400 generation failures; Llama had 154 generation failures and 246 decision exhaustions. No correct accepted submissions occurred. Only 246/1,200 reports and trajectories were valid; every local cell failed its ≥95% technical gate. Claude v0.1 was held, with 0/80 starts; its outcomes are UNKNOWN, not zero. Independent replay found **0/953 falsely rejected legal actions**, including the disputed mass_g cases. One preflight has no reply and cannot be classified as an illegal reply.

| Actor | World | Arm | n/version | v0.1 S* | v0.1 A* | v0.1 valid traj | v0.1 valid report | v0.2 S* | v0.2 A* | v0.2 valid traj | v0.2 valid report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | stable | stale | 50 | 0 | 0 | 0 | 0 | 5 | 5 | 50 | 50 |
| Qwen 7B | stable | registry | 50 | 0 | 0 | 0 | 0 | 2 | 2 | 50 | 50 |
| Qwen 7B | rename | stale | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 7B | rename | registry | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 7B | unit | stale | 50 | 0 | 0 | 0 | 0 | 6 | 6 | 50 | 50 |
| Qwen 7B | unit | registry | 50 | 0 | 0 | 0 | 0 | 2 | 2 | 50 | 50 |
| Qwen 7B | required | stale | 50 | 0 | 0 | 0 | 0 | 3 | 3 | 50 | 50 |
| Qwen 7B | required | registry | 50 | 0 | 0 | 0 | 0 | 10 | 10 | 50 | 50 |
| Llama 8B | stable | stale | 50 | 0 | 0 | 33 | 33 | 0 | 0 | 50 | 50 |
| Llama 8B | stable | registry | 50 | 0 | 0 | 29 | 29 | 0 | 0 | 50 | 50 |
| Llama 8B | rename | stale | 50 | 0 | 0 | 33 | 33 | 0 | 0 | 50 | 50 |
| Llama 8B | rename | registry | 50 | 0 | 0 | 29 | 29 | 0 | 0 | 50 | 50 |
| Llama 8B | unit | stale | 50 | 0 | 0 | 32 | 32 | 0 | 0 | 50 | 50 |
| Llama 8B | unit | registry | 50 | 0 | 0 | 28 | 28 | 0 | 0 | 50 | 50 |
| Llama 8B | required | stale | 50 | 0 | 0 | 33 | 33 | 0 | 0 | 50 | 50 |
| Llama 8B | required | registry | 50 | 0 | 0 | 29 | 29 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | stable | stale | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | stable | registry | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | rename | stale | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | rename | registry | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | unit | stale | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | unit | registry | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | required | stale | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |
| Qwen 1.5B | required | registry | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 50 |

v0.1 was exposed before the informed follow-up predictions. Versions remain separate and are never pooled. v0.2 does not retrospectively validate v0.1. **v0.2-r1 is a different category: all 1,200 local episodes (400 per model), zero Claude starts, are VOID-HARNESS.** They ended at zero decisions because decoder branches admitted incomplete action objects. They contribute incident counts and resource charges only; they are excluded from every behavioral table, contrast and prediction here. Archived r1 analyses are also VOID-HARNESS.

## Resources, spend, operational events and limits

| Actor | Episodes | Saved calls | Ordinary input | Cache create | Cache read | Output | Reasoning | Generation seconds | Accounted USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 7B | 400 | 2786 | 1211292 | null | null | 83461 | null | 1433.794 | 0.000000 |
| Llama 8B | 400 | 2800 | 1154600 | null | null | 85575 | null | 2192.327 | 0.000000 |
| Qwen 1.5B | 400 | 2800 | 1159223 | null | null | 88137 | null | 2404.013 | 0.000000 |
| Claude | 80 | 356 | 712 | 375473 | 270769 | 62811 | null | 1512.224 | 4.667178 |

**Programme accounted spend: USD 4.667178; outstanding holds USD0.** Prior v0.1 and VOID-r1 accounted spend is USD0. Claude's aggregate provider-reported amounts total USD4.317075; the conservative USD4/input-million and USD20/output-million basis totals USD3.844036. Settlement takes the larger amount **per call**, so the ledger total can exceed both aggregate columns. Local accounting is USD0; energy, hardware cost, incremental subscription cash billing and actual invoice charges remain UNKNOWN. Unknown reasoning-token counts stay null; output already includes reasoning and is not added twice. Returned effort is absent in all 356 Claude envelopes: requested medium, realized effort UNKNOWN.

There are **8,742 saved scored-call receipts** (8,386 local, 356 Claude) and one additional Claude refusal attempt. The refusal at `claude-03-unit-stale-action-2` had integer 429 status, zero usage and cost, and exact subscription-limit refusal text. It is saved separately as a definite non-start, settled at zero, paused until 2026-11-11 23:30 UTC, then cleared at 23:32:34 UTC. The identical pending request resumed; earlier calls were not resent. There are zero paused episodes at analysis. This event is operational, not a model decision, technical-content failure, or an extra scored episode. No saved DNS or other rate-limit event appears in this v0.2 evidence; unsaved external events are UNKNOWN and must not be inferred from model behavior.

Persistent local active charge is **16064.305s / 43,200s** (including 4843.353s prior v0.1+VOID-r1 exposure); frontier charge is **2069.863s / 7,200s**. Both have zero unsettled time holds. Timer charges include operational overhead and differ from summed generation seconds. Offline usage-limit waiting is excluded. No time or money cap was reached. Frozen limits remain: six decisions plus one report per episode, 180s local / 420s Claude request timeout, USD25 frontier envelope including USD2 protected reserve, USD39 operational programme stop and strictly under USD40 absolute ceiling. Reservations are empirical safeguards, not proof of provider billing/output bounds.

## Freeze integrity, deviations and reproduction

Prepared by Codex for Claude, the delegating reviewer, under the Claude/Codex semi-autonomous agreement. The original frozen root RESULTS.md and PROJECT_STATE.md are historical build inputs. **This delivery is in v0.2/delivery/** so those files, the protocol, prompts, analysis source, freezes and collection bytes remain unchanged.

All four manifest content digests and the parent chain passed; the latest 107-file source inventory and its exact source-bound 213-test report passed. All 9,611 r1-preservation files, the r3-preserved local evidence and ledger prefix, and all 20,954 v0.1-preservation files matched on the canonical machine. Saved GitHub push evidence precedes each admitted cohort; the offline push gate and raw-call audit passed. Historical inventories are superseded by their bound revisions, not re-applied to later source bytes. The frozen empirical analysis ran **once** in the original folder with `python3 -B bob.py analyze`, after verification. Its full result is [../build/results.json](../build/results.json).

| Manifest | SHA-256 |
| --- | --- |
| freeze-r1.json | `0381913a685bb837d2c227fb6bb7b75bc8b1944bd69c9280bfa086d3159ceeee` |
| freeze-r2.json | `31dfdb3b8bcacd361e6c85fd90520d46bc9cb18fb237b65bdebc37901064d272` |
| freeze-r3.json | `41998f58e147abccc8dad7edd472f5ebabdc9c0d21364ad95f34f9e41e823a51` |
| freeze.json | `c1c108d06741d3e9c00751915b4e33933ad620e819cb5905d505fc481e2272e4` |

Applied deviations: inherited v0.1 D1 provenance/empirical reservation release, D2 pinned-local-identity correction and operational preflight disposition, D3 strict provider/usage/failure-boundary audit, and A1 audit seal remain disclosed in the parent study and frozen evidence. The v0.2 informed constrained-decoding follow-up retains world/scientific endpoints. R1 added zero-usage subscription-limit pause/resume handling. R2 closed decoder branches and replaced the VOID-HARNESS collection without pooling or outcome selection, retaining resource exposure and recalculating schema-size holds. R3 changed only Claude provider-schema compatibility before Claude starts, retaining r2 local bytes and the independent cross-field validator. No new scientific deviation, prompt repair, collection rerun, cohort selection or v0.3 was introduced in this delivery.

Post hoc presentation work is explicitly secondary: the headline comparisons and figure, frozen scripted-policy evaluation on all scheduled seeds, requested unit-provenance compatibility breakdown, registry exhaustion breakdown, and operational/accounting summaries. Registered endpoints, predictions and intervals are read directly from the single frozen analysis output.

The published package retains **every file except paths containing __pycache__, .DS_Store, .git, or a *.lock component**. The fresh-clone adapter [reproduce.py](reproduce.py) changes only verification presentation in memory: delivery/ is an explicit post-freeze output namespace; absent documented transient files are permitted and listed with saved hashes. A present transient must still match. Every other frozen/preserved/package file and ledger prefix is verified. No frozen source is edited, lock recreated, hash replaced or schema relaxed. The four omitted preservation locks and their hashes are listed in [transient-files.json](transient-files.json). Plain frozen `bob.py verify` predates delivery/ and cannot accept newly added deliverables; use the documented adapter.

An independent rebuild in a separate filtered COPY verifies all saved package hashes, runs the unchanged empirical loader and the registered synthetic fixture rebuild, and compares canonical output bytes with the original. The saved proof is [rebuild-proof.json](rebuild-proof.json). The empirical output must be byte-identical: SHA-256 `daec3a018eac0db5bd7d031274da07dd91c62221f647e69e5901bfd12c5ff9f5`. The original frozen suite passed 213/213; four additive verifier-boundary checks passed. The filtered copy simulates the specified GitHub publication exclusions; this task does not claim a network clone, GitHub push, website deployment or completed independent reviewer acceptance.

Follow the exact commands in [README.md](README.md). No installed models, Ollama service, provider CLI, credentials, parent study directory or network are required to rebuild saved empirical results. Python 3.9+ suffices; Node is required only for the optional frozen cross-language test suite. The empirical rebuild, presentation generation and four adapter tests use the Python standard library.

**Stop:** v0.2 is final for this task. Failed forecasts and the technical completion failure remain visible. Interesting questions are appended in [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md); none authorizes new collection.
