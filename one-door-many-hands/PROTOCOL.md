# One Door, Many Hands · Protocol v0.1 r1

11 November 2026 (HKT). Builder: Codex. Reviewer and delegating agent: Claude. **AGREED · r1 offline build and pre-inference freeze.** Claude's [review](evidence/REVIEW-claude-20261111-r1.md) is AGREED with notes; Codex records AGREED here and in [REVISION.md](REVISION.md). Robin has not reviewed this project. This delegation permits build, tests and freeze only; no model calls, collection or push in this task. The supplied folder-only scope keeps Codex's agreement record here rather than writing into the shared review folder.

## 1. Question and claim boundary

**Primary:** does adding a deterministic delivery rehearsal to complete written rules improve a model's choice of capacity partition for a deadline, relative to the same rules alone?

**Co-primary:** does improvement survive treating abstention, invalid replies and missing choices as misses, while requiring a useful absolute optimal-choice rate?

Secondary: which door limits, damage probabilities and common versus independent failures change choices? How much does optimization of deadline attainment differ from expected work or survival? Do Llama, the smaller Qwen reference and a fixed Claude arm show the same pattern?

This is model-based **fleet selection**, not a team of model workers. It tests use of a concrete, mathematically redundant service observation. It does not claim more intelligence from more agents, embodied performance, actual tool resilience, equal total compute, production reliability or general understanding of queueing. It remains its own study and page. No external effects, messages, money or real carriers exist.

## 2. Environment, objective and intervention

An episode is one model decision before any failures. It chooses 1, 6 or 24 carriers, each design totaling capacity 24, with per-carrier payload respectively 24, 4 or 1. At dispatch, permanent damage removes carriers. Every survivor starts ready. The door admits at most **B bodies in total before the deadline**; each survivor crosses at most once. A work-conserving scheduler sends `min(K,B)` surviving bodies, where K is survivors. Delivery is `W=(24/n)*min(K,B)`. No return cycle, setup cost, carrier-size restriction, repairs or adaptive dispatch decisions occur. Each fleet has the same service limit, with no competition between counterfactual fleet designs.

The explicit objective is **maximize the probability W≥T**, where T is required work by the deadline. Do not optimize survivor count or expected W as substitutes. Any exactly optimal fleet is correct; no arbitrary preference breaks ties. Failure probability and common-mode mechanism are given, rather than inferred from a few rehearsal observations.

| Factor | Fixed values |
|---|---|
| Numeric block b | Integers 0–99 |
| Target T | `7 + (b mod 10)`, giving 7–16 units |
| Failure percent f | `20 + 6*floor(b/10)`, giving 20,26,…,74; p=f/100 |
| Door B | 1, 6, 24 bodies by deadline |
| Failure mechanism | independent; common |
| Evidence | rules; rules + rehearsal |

Thus 100 blocks form a full target × failure grid. Each block contains all twelve door × mechanism × evidence decisions. These are nearby numerical variants of one task, not 100 distinct domains. Both evidence arms and all models use identical rules, objective, numeric values and option order within a block/world.

- **Independent:** each carrier fails independently with probability p, irrespective of its payload.
- **Common:** one draw removes every carrier with probability p; otherwise every carrier survives. This is fully common failure, not an intermediate correlation coefficient.
- **Rules arm:** rehearsal is an empty array.
- **Rehearsal arm:** supply one failure-free synthetic rehearsal receipt for each fleet at the current B. Each receipt states carriers, crossings `min(n,B)` and delivered payload. They are deterministic worked observations, not samples of the future failure process, additional unknown-world information or optimal-choice labels. Rehearsal construction makes no model calls and is not charged as free model labor.

Rules-only can compute all rehearsal facts. The intervention adds length, salience and redundant computed information together; a positive result cannot isolate these mechanisms. It does not compare withholding a necessary fact with supplying it. A pass means models use worked examples better than complete written rules in this task; the eventual page must say that plainly.

Options appear in one of the six permutations of `[1,6,24]`: choose permutation number `b mod 6` from lexicographic order. Receipts follow the same order. Within a model, enumerate `(b,B,mechanism,evidence)` lexically, then shuffle once with Python `random.Random(20261111)` and freeze the explicit schedule later. Stateless requests; no preceding response or cross-arm history is visible. Local generation seed is b. Shared seeds do not guarantee deterministic responses. No prompt includes block ID, seed, evaluator probabilities, optimal set, provider, cost or pass thresholds.

## 3. Exact ground truth

Let `r(n,T)=ceil(T*n/24)`, implemented with integer arithmetic. For a legal fleet n, exact deadline success value is:

- If `r>min(n,B)`, `V(n)=0` in either mechanism.
- Otherwise, independent `V(n)=sum(comb(n,k)*(1-p)^k*p^(n-k), k=r..n)`.
- Otherwise, common `V(n)=1-p`.

Use rational arithmetic with p=f/100, no floating tolerance for ties. The oracle value `Vmax=max(V(1),V(6),V(24))`; the optimal set contains every fleet attaining it. n=1 always has V=1-p because T≤16<24 and B≥1, so the oracle is strictly positive in every cell. Publish the entire oracle table and optimal-set/tie frequencies. The rehearsal table never includes V or the optimal set.

Expected useful work is separately calculated by summing `(24/n)*min(k,B)` under the same binomial distribution, or `(1-p)*(24/n)*min(n,B)` for common damage. Complete-outage probability is p^n for independent failure and p for common failure. A carrier surviving is not automatically a delivered unit. These are exact environment values, not observed model performance or randomized future deliveries.

Later build must independently verify the rational scorer against a direct subset enumeration for n=1/6 and an independent distribution/dynamic-program calculation for n=24; include zero/total failure and door/target boundaries outside the study grid as fixtures. No Monte Carlo noise, favorable seed selection or model grading enters ground truth.

Draft arithmetic checks, performed without model replies or a saved harness: across the 100 independent-failure blocks, the unique optimal fleet is n=1 in all 100 B=1 cells; B=6 has 64 n=6 and 36 n=1 optima; B=24 has 59 n=24, nine n=6 and 32 n=1 optima. There are no independent-cell ties on this grid. Thus both service limits and failure severity matter; always choosing more bodies cannot solve the task. These are design diagnostics, not empirical model results or a hidden holdout.

## 4. Sample, model identities and output

| Cohort | Blocks × doors × mechanisms × evidence | Decisions/calls |
|---|---|---:|
| Qwen 2.5 7B, primary | 100 × 3 × 2 × 2 | 1,200 |
| Llama 3.1 8B, replication | Same | 1,200 |
| Qwen 2.5 1.5B, reference | Same | 1,200 |
| Claude, descriptive replication | 10 × 3 × 2 × 2 | 120 |

Primary Qwen independent-failure comparison: **300 pairs / 600 decisions**, grouped in 100 numeric blocks. Common-failure control adds another 300 pairs. No action, metric, counterfactual option or oracle evaluation counts as another model episode.

Frontier block indices are fixed as `b=10*j+((3*j) mod 10)`, j=0…9: **0,13,26,39,42,55,68,71,84,97**. This covers each target and each failure level once, with all twelve within-block conditions. It supplies 120 episodes in ten blocks; estimates are descriptive and cannot establish a family-wide ranking. No outcome-dependent expansion/shrinkage or substitution is permitted.

Run serially: Qwen 7B, Llama 8B, Qwen 1.5B, then Claude. Local source pins (from Bridge or Bus D2; live metadata still to be rechecked):

| Tag | Manifest SHA-256 | Template layer SHA-256 |
|---|---|---|
| `qwen2.5:7b` | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | `eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175` |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | `948af2743fc78a328dcb3b0f5a31b3d75f415840fdb699e8b1235978392ecf85` |
| `qwen2.5:1.5b` | `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b` | `eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175` |

Qwen's exact default system is `You are Qwen, created by Alibaba Cloud. You are a helpful assistant.`; system-layer SHA-256 `66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e`. Llama has no default system layer. Bind actual template/system bytes through their manifest layers, not just a nonempty-template test. The explicit study system below is separate; do not prepend the model default to it or reject Qwen for having that default metadata.

Later use the existing Ollama endpoint `http://127.0.0.1:11435/api/generate`, nonstreaming JSON mode, temperature 0.6, top_k 16, num_predict 192, num_ctx 8192, seed b. Capture model/runtime version, exact template/default system and effective context before inference; mismatch fails closed. Wait for shared hardware access without modifying a server, model store or other collection. No pulls, service startup/restart, tuning or sampling pilots.

Frontier is fixed `claude-opus-5-5`, requested medium effort, using Claude Code **2.1.312** at:

`<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude`

Use isolated print mode, `--json-schema` and `--output-format json`, no persisted session or external tools/MCP/browser access. Freeze installed binary/version, flags, environment controls and documented usage mapping later. No automatic provider/model change. Record returned model/effort: absent effort is UNKNOWN, conflicting effort/model is fatal. No credentials are copied or displayed.

The reply is exactly one object, e.g. `{"fleet":6}`. Fleet is integer 1, 6 or 24, or explicit null for abstention; booleans, strings, extra keys, duplicate keys, NaN, prose/fences, multiple objects or repairs are forbidden. Null is intentional abstention only when the strict object is otherwise valid. Missing/malformed is technical failure, never inferred abstention.

Frontier extraction uses exactly one **object-valued `structured_output`** in the strict outer JSON envelope; never parse `result`, prose, a substring or a stringified substitute. Preserve raw bytes to detect duplicate keys. Accept `num_turns` 1 or 2 only with a strict-valid `structured_output`; the known two-turn schema envelope has `stop_reason=tool_use`. Count `cache_creation_input_tokens` and `cache_read_input_tokens` as input alongside uncached input. The **first frozen scored call** is the compatibility check, included in the fixed sample. Verify success envelope, model, usage/cost and payload; failure saves evidence and durably stops further frontier dispatch. Repeat envelope/identity/accounting checks on every call. An invalid experimental answer inside an otherwise valid envelope is an episode failure; missing/wrong structured payload is an envelope failure. No extra preflight inference.

One submitted request per episode, no retries, repairs, replacements or re-query of ambiguous starts. Configure supported no-retry/turn controls from the installed transport and retain their evidence. Do not require an unprovable aggregate output-token bound as a launch gate. All reported internal usage is accounted; an unexpected turn/envelope or usage overrun stops further dispatch.

Local `done_reason=length`, output exactly equal to num_predict, or a recognized frontier output-length stop makes that episode a technical failure even if its object parses. No choice is scored from a length-stopped reply. Continue later episodes when integrity/accounting gates pass. **Input** truncation, identity/digest/template mismatch and accounting envelopes are collection-wide failures. For local replies, missing `done=true`, missing `eval_count`, and unreadable/incomplete transport are transport failures for that episode, with no resend; identity, context and known input loss remain collection-wide failures. Usage above a reserved token/cost allowance is an accounting overrun, even if caused by output length, and remains fatal. Unknown stop reasons are envelope errors. Do not claim byte sizing proves input completeness: capture prompt_eval_count and context metadata; reject known expected-token shortfall if an independent count is available, and stop on evidence of truncation or insufficient context. Exact input-token completeness remains UNKNOWN without such evidence.

## 5. Pre-registered endpoints and joint pass rule

For each planned decision define operational value `V*=V(chosen fleet)` for a valid, non-length-stopped legal choice; otherwise 0. Define regret `R*=Vmax-V*` and optimal-choice indicator `O*=1` iff a valid legal choice is in the exact optimal set; otherwise 0. Explicit null, malformed/missing replies, transport failure and unstarted jobs all have O*=0. Record factual chosen fleet as null/UNKNOWN with reason where no choice is known. An assigned penalty is not an observation that a particular failed fleet was chosen.

The primary estimands for **Qwen 7B, independent damage only**, equally weighting the 100 blocks and three doors, are:

1. `D_R = mean(R*_rules - R*_rehearsal)`; positive means lower expected deadline regret.
2. `D_O = mean(O*_rehearsal - O*_rules)`; positive means more exact optimal choices. This is the **abstention-as-miss co-primary**.

Use a paired block percentile bootstrap with 10,000 resamples, seed 20261112; each selected block retains all its doors/evidence decisions, with repeated-block multiplicity preserved. Two-sided 95% intervals use percentiles 2.5/97.5, linear interpolation. This measures sensitivity over the fixed synthetic numeric grid conditional on one saved reply per prompt. It is not a confidence statement about all tasks or full generation variance. Publish the full cell table and an exact paired choice-discordance table alongside intervals.

The joint scientific claim **delivery rehearsals improve useful fleet selection** passes only if all hold:

- D_R≥0.05 in absolute probability (five percentage points), with lower 95% bound strictly >0.
- D_O has lower 95% bound strictly >0, and rehearsal optimal-choice rate is ≥0.75 over all 300 assigned independent decisions.
- All 600 primary decisions were attempted; ≥95% in each independent door × evidence cell produce schema-valid completed objects (explicit null counts as schema-valid but never as an optimal choice).
- Rehearsal null / all assigned independent decisions ≤0.05. Always report null and technical failure separately.

These are intersection criteria, not independent replications. A schema or budget stop cannot be rescued by counting only completed favorable pairs. Report all planned denominators plus complete-valid-pair sensitivity, without replacing the primary. If the sample is incomplete the joint pass is unavailable, regardless of favorable point estimates.

Secondary reporting, with no additional confirmatory pass claim:

- R*, O*, V*, expected delivered work and predicted complete-outage probability for chosen fleets, by model × door × mechanism × evidence. For unavailable choices report factual values as null, alongside clearly labeled operational zero scores where applicable.
- Common-mode controls: all feasible fleets tie at 1-p, while any fleet unable to meet T is suboptimal. Publish feasible-optimal sets and refrain from claiming a preferred body count in a tie.
- Choice distribution, intentional abstention, parse/length/transport failures, exact n=1/6/24 oracle counts and tie prevalence.
- Actual prompt/input/output tokens, seconds and API-equivalent USD by arm/model; rehearsal does not have an equal-token claim. No cost-adjusted superiority test is added post hoc.
- Llama/Qwen 1.5B and the fixed ten-block frontier arm with the same estimands and paired intervals, explicitly descriptive. No pooling to rescue the Qwen primary, multiplicity fishing or optional sample additions.

## 6. Predictions before responses

| ID | Prediction | Registered decision |
|---|---|---|
| P1 | Rehearsals help Qwen 7B use the delivery objective | Joint primary rule in §5 passes |
| P2 | One-crossing cases are easier to recognize from delivered-work receipts | Qwen independent B=1 rehearsal optimal choices ≥0.90; report both arms and their difference |
| P3 | Models sometimes overvalue headcount despite infeasible delivery | Rules-only Qwen selects n=24 in ≥10% of independent B=6 decisions, where T≥7 makes that fleet impossible |
| P4 | Common-mode failure removes the survival argument for partitioning | Qwen common-mode rehearsal optimal choices ≥0.90; failure is reported as objective/feasibility error, not evidence of hidden redundancy |
| P5 | The receipt representation helps across families | Llama and Claude each have positive point estimates D_R and D_O; no significance or family-ranking claim |

Every prediction receives met/unmet/unavailable with denominators and reason. Toy results, scorer logic and sibling failures are already known; these are informed prospective predictions about previously unseen model replies. A ceiling in rules-only performance can falsify P1; no harder replacement task is introduced afterward.

## 7. Empirical budget and stops

Present-stage spend: USD0. Later local model-call USD is 0; electricity/hardware/opportunity costs and expected runtime are UNKNOWN, not zero. Maximum scheduled calls: 3,600 local and 120 frontier. Each episode is one call, so the whole-episode hold equals the call hold. No hidden pilot, judge, repair, rerun or second frontier family is included.

Let `pad(x)=64*ceil(1.10*x/64)`. For each exact rendered frontier request, reserve:

- Input `I=pad(P+S+K+826)`: measured visible UTF-8 prompt bytes P, explicit system bytes S, schema bytes K, plus the historical **826-token hidden-input maximum** from 995 archived calls. One input token per visible byte is an empirical conservative allowance, not exact tokenization. Measure outer request bytes separately; do not double-charge known schema/system input.
- Output `O=pad(512)=576`: empirical planning allowance of 512 accounted tokens, exceeding the sibling's measured historical 393-token maximum. Neither number is an enforced aggregate output bound.
- Planning call hold in integer microdollars is `4*I + 20*O`, using historical USD4/input-million and USD20/output-million. These are explicit API-equivalent subscription planning rates from sibling evidence, not a present cash price quote.

Appendix A gives exact draft request literals. Before freeze, measure every rendered job and retain prompt/system/schema/envelope bytes, hashes, historical evidence and reservation arithmetic in a portable sizing artifact. Current exact tokenizer counts, current cash billing and future actual costs are UNKNOWN. Changed final bytes/CLI need remeasurement before any response, not an assumed inherited input maximum. Higher supported overhead/rate evidence enlarges reservations before freeze.

**Frontier dispatch envelope ≤USD25, including USD1 protected reserve**; full-plan holds must total ≤USD24. Operational project stop USD39; absolute programme ceiling USD40 across all versions and failures. No planned extension is included. Admission is rolling: settled actual cost + all open/uncertain holds + proposed hold + protected reserve must fit the frontier envelope and remain below USD39. Reserve and flush a unique start before dispatch, locked and append-only. Stop at the first unfundable scheduled job; do not pack cheaper later jobs or shrink the registered sample.

Settle complete reported usage and actual `total_cost_usd`, preserving category breakdowns and API-equivalent versus cash distinctions. Release only known unused holds; never clip actual cost to a reservation. Missing usage/cost or an ambiguous timeout retains its full hold and stops dispatch pending reconciliation from saved evidence; never resend it. Any token or cost reservation overrun is settled in full where known and causes a durable stop. The first call tests transport compatibility within this same accounting. A short JSON reply, schema or CLI budget flag is not proof of a hard cost ceiling. **Empirical margins cannot guarantee that a single overrun never crosses a cap**; the protected reserve and stop limit exposure. Do not gate launch on proving an impossible aggregate output ceiling.

Stop collection for input loss, identity/digest/template/context mismatch, source/freeze drift, truth disagreement, leakage, envelope/accounting errors, cap or authority boundaries. Preserve all records. Low reward, an unexpected scientific result, null, ordinary bad JSON inside a valid envelope and a completed output-length stop fail their episodes, not the collection. No prompt/output-limit changes to improve outcomes.

Later operational limits: one inference request at a time; local request timeout 180 seconds, frontier 300 seconds; cumulative active collector wall time ≤8 hours local and ≤2 hours frontier, persisted across restarts. Shared hardware contention pauses dispatch without generating probes or altering services. A timeout with an uncertain start is not retried. Resource-stopped partial data remain reportable but do not meet completion acceptance. Extensions require a separately reviewed change, never silent reset of timers.

## 8. Later integrity and verification contract

After agreement, a separate build stage must implement pure world/scoring functions, strict parsing, schedule/payload preparation, an append-only collector and offline analysis. The r1 offline build implements this contract. Freeze protocol, all literal prompts/schemas, source subset/hashes, exact schedule, model/system/template pins, rates/empirical cost basis, sizing, tests, scoring and analysis before **any** call, including local calls and the first transport check.

Push from a separate research clone, never mutate the RobinOS2 Git tree. Follow Receipt Gap D1: obtain a full raw record from **GET `/repos/Robin84Bran/research/activity`**, with `activity_type=push`, server id, branch ref, `after` matching the commit and a timezone-aware server timestamp. Verify clone origin is `Robin84Bran/research`, clone HEAD/remote ref, and committed freeze/manifest blobs. Commit author dates are not push evidence. No request is made in this stage.

The later attestation interface must accept `--clone-root` for the separate clone and `--repo-path` for `one-door-many-hands` within it. The project collection root receives create-once **`collection/push.json`** and the raw server response/hash; no attestation writes go to the clone. Push must follow freeze and precede the first saved start. A later amendment needs its own preserved freeze/push chain; never rewrite earlier provenance.

Every call keeps unique model/block/door/mechanism/evidence ID, exact request/hash/settings, model identity, start/finish, raw stdout/stderr and envelope, extracted object/error, stop reason, tokens, seconds, holds/settlement and return status. No model response is overwritten or silently replaced. Resume only definitely unstarted jobs under the same verified freeze. Offline analysis imports no provider and needs no models, network, credentials or original absolute paths.

Meaningful later tests: rational threshold/tie boundaries; independent/common analytic identities; narrow-door impossibility and capacity conservation; independent scorer parity; identical paired rules/options; no oracle/seed leakage; rehearsal rows from the exact service rules; strict types/duplicate-key/null parsing; first-call structured_output gate with no result fallback; correct pinned Qwen/Llama systems; output exhaustion failing one episode and input truncation stopping the batch; wrong identity/envelope and missing cost stops; crash/no-resend and ledger races/overruns; all-null actor gives O*=V*=0 and cannot pass; fixed denominators and bootstrap repeated-block multiplicity; immutable starts/push evidence and separate roots; fresh-clone offline reproduction.

## 9. Acceptance criteria

**For this r1 build:** apply Claude’s two notes, implement and test the frozen offline package, and retain fake-transport evidence. No empirical acceptance is claimed.

**For a later empirical delivery, every criterion is required:**

1. Written Claude/Codex agreement and frozen artifacts precede genuine server push evidence and every call. Ground truth and rehearsal semantics pass independent offline verification.
2. All 1,200 assigned decisions for each of the three local models and all 120 frontier decisions have an attempted response or retained failure receipt; ≥95% schema-valid completed objects per local model × door × mechanism × evidence cell. For frontier, require ≥90% in each ten-decision cell and ≥95% overall, avoiding a hidden 100%-validity requirement from rounding. All raw replies, nulls, length failures, technical failures and unstarted jobs remain in registered denominators. A budget-stopped partial sample is incomplete.
3. Every primary/co-primary component, oracle table, tie/control results, resources and prediction is reported. **A positive result is not required for acceptance.** Negative or ceiling results cannot trigger a replacement series or altered thresholds.
4. Complete usage/cost/hold reconciliation; respected USD25 envelope, USD39 operational rule and programme USD40 ceiling. UNKNOWN charges are not zero; unresolved holds or actual cap breach block acceptance.
5. A fresh-clone rebuild regenerates tables and pass decisions offline from saved evidence; independent Claude review checks claims and every finding is fixed or answered. Both agents may record ACCEPTED only when the programme criteria are satisfied and more work would add little.
6. Later README, RESULTS and the plain-language page state the question, observed result, any twist and limits, including the one-wave simplification, representation intervention and distinction between model planning and actual multi-agent resilience. Publication follows the programme's applicable delivery gate; none is part of this task.

## Appendix A. Literal draft request contract

Explicit study system, one line:

```text
You are a careful planner. Return only the requested JSON object.
```

Common instruction, one line (identical in both evidence arms):

```text
Choose a fleet before damage to maximize the probability of delivering at least target work units by the deadline. Total payload capacity is 24. With n carriers each has payload 24/n; options are 1, 6, or 24. Damage happens before any crossing. In independent mode every carrier fails independently with failure_percent percent probability. In common mode all carriers fail together with that probability, or all survive. The door admits at most door_limit surviving bodies in total by the deadline. Each survivor crosses once at most, delivering its full payload immediately. The scheduler uses all available admissions. There are no returns, repairs, setup costs, or other constraints. Any fleet tied for the highest success probability is correct. Maximize deadline success probability, not survivor count or mean work. Optional rehearsal receipts show a failure-free dispatch with these same door rules; they do not predict future damage. Return exactly one object with fleet equal to 1, 6, 24, or null if you abstain. No explanation or other keys.
```

Prompt is that literal instruction + one LF + canonical payload JSON: ASCII, `ensure_ascii=True`, `sort_keys=True`, separators `(',',':')`, no trailing LF. Payload has exactly `target`, `failure_percent`, `mode`, `door_limit`, `options`, `rehearsal`. Mode is `independent` or `common`; options is the registered permutation. Rehearsal is `[]` or three objects in option order, each exactly `carriers`, `crossings`, `delivered`. Example for B=6 (sorted option order shown only as an example):

```json
{"door_limit":6,"failure_percent":20,"mode":"independent","options":[1,6,24],"rehearsal":[{"carriers":1,"crossings":1,"delivered":24},{"carriers":6,"crossings":6,"delivered":24},{"carriers":24,"crossings":6,"delivered":6}],"target":7}
```

Provider schema, canonical bytes:

```json
{"type":"object","properties":{"fleet":{"type":["integer","null"],"enum":[1,6,24,null]}},"required":["fleet"],"additionalProperties":false}
```

The provider schema supplements independent validation. Freeze final literal equality after review and save measured exact request sizes; illustrative whitespace and Markdown fences are never sent.

### Draft sizing, measured without inference

Inline standard-library byte counting of the literals above and all 120 scheduled frontier payloads measured **65 explicit system bytes, 1,052 instruction bytes and 139 schema bytes**. It enumerated only document payloads, not a collector or a model invocation. Applying §7's formula gives:

| Evidence | Calls | Prompt UTF-8 bytes | Input hold tokens/call | Output hold tokens/call | Total holds USD |
|---|---:|---:|---:|---:|---:|
| Rules | 60 | 1,151–1,158 | 2,432 | 576 | 1.274880 |
| Rehearsal | 60 | 1,281–1,291 | 2,560 | 576 | 1.305600 |
| Total | 120 | | | | **2.580480** |

Including USD1 protected reserve gives **USD3.580480 < USD25 < USD39 < USD40**. This is a measured-byte reservation scenario at historical accounting rates, not measured realized spend, exact tokenizer output or a bill guarantee. No separate model probe is budgeted. Largest frontier prompt SHA-256 by arm: rules `c510c9cfb35ffa5c9c4e37a63716f4e9cb7ed7a65b13ecdc1c515555552ab07a`; rehearsal `b714b99e12afbdce80e8e778a4fd8b7883299987eb2a7d44d48e19ade7a7537f`. Later preparation must reproduce these sizes from unchanged literals and record actual outer-envelope bytes; any reviewed literal/transport change requires new sizing before freeze.
