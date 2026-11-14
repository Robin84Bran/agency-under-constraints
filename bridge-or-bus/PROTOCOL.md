# Bridge or Bus? · Protocol v0.2 offline build

11 November 2026 (HKT). Builder: Codex **AGREED**. Reviewer: Claude **AGREED with notes**, r1. Robin authorized revision, offline implementation, tests and freeze on 11 November. **OFFLINE BUILD ONLY · no model calls, push or collection.**

This document registers prospective work under [the programme loop](../semi_autonomous.md). The current task ends with an offline build and freeze. [SURVEY.md](SURVEY.md) records sources and prior exposure: toy outcomes and sibling methods/failures are known; no response exists for this study. This remains prospective: no study response has been collected. The original draft is retained in `evidence/agreements/PROTOCOL-v0.1-draft.md`.

### Revision record · v0.2 · 11 November 2026

Claude r1 is AGREED with three notes; no new scientific agreement round was requested. Codex agrees and applies all three below. The question remains access to current tool descriptions after drift, chosen as a cheaper information-access test; this is not a direct-adapter versus translation-bus result. Carry this boundary into SURVEY, RESULTS and the local page template.

1. Unit-world successful submissions are counted per arm for compatibility with direct lookup reuse and with mg/1000. These counts overlap: the output contract cannot distinguish the two numerically identical paths. Exclusive direct/derived counts are `null`, provenance `UNKNOWN`, never inferred arithmetic. This resolves the note without adding an unreviewed reasoning field.
2. Report per arm/world the count of registry episodes exhausting six decisions after at least one describe, without an accepted submit; an explicit finish on decision six is separately a voluntary stop. Oracle registry trajectories pay two describes and complete in five decisions in every world.
3. Robin's present instruction supersedes the draft's documents-only stop and permits an offline collector scaffold/freeze while transport readiness is unresolved. It does not waive any live transport/accounting gate. The Claude adapter uses only object `structured_output` from strict outer JSON; candidate flags/environment controls are frozen and tested with fake transports. Complete disabled-tool compatibility, retry semantics, charged-output enforcement and current rates remain `UNKNOWN`; `frontier_gate` refuses dispatch before any paid start. No empirical bound or CLI flag alone clears these gates. A reviewed evidence amendment/new freeze and genuine push must precede future frontier dispatch.

No seeds, endpoints, sample size, thresholds, provider, output schema, prices or decision allowance change. `evidence/agreements/RESPONSE-codex-20261111-r1.md` records agreement and limits. Frozen literals are enumerated in `bob_core.py`; provider schemas/prompts are in `config/`. All observations are independently replayed.

## 1. Questions and claim boundary

- **RQ1, primary:** does optional access to current tool descriptions increase correct completion after interface drift, compared with initial descriptions alone, under the same six-decision allowance?
- **RQ2, co-primary:** does the advantage survive requiring a correct, determinate completion report, with abstention, malformed/missing reports and failures counted as misses?
- **RQ3, secondary:** how does the effect vary across renamed fields, changed units, new required arguments, unchanged controls and model families? What decisions and resources buy recovery?

The registry is informational; it never repairs, translates or executes a model action. This design compares information access, not direct adapters against a translation bus. It cannot establish production reliability, architecture costs, hub resilience or deliberate dishonesty. There are no external tools, messages, accounts or financial effects. Only harness code changes a synthetic ledger.

## 2. Environment and matched interventions

Each independent episode has one item and a hidden exact mass, six action decisions, and a separate final-report call. Item for seed s is `item-` plus six zero-padded decimal digits. Mass in grams is `1000 + ((7919*s + 104729) mod 998000)`, an integer in 1000–998999. Models see the item, never seed, formula, intervention label, hidden truth or future events. `lookup` returns the mass in grams. A successful `convert` is required before `submit`; models must decide every action and argument themselves.

Both arms receive the same v0 descriptions once. Both are warned that interfaces may change, that units matter, and that the job is complete only after a correct accepted submission. Drift occurs exactly once **immediately after the first successful lookup**, before the next decision. Repeated lookups do not trigger more drift. No unsolicited drift announcement or refresh occurs. A description query before lookup returns v0. No lookup means no realized drift; such episodes remain in their assigned intention-to-treat cell and cannot be silently excluded.

| Assigned world | Interface after lookup | Information available to both arms |
|---|---|---|
| stable | v0 unchanged | Normal observations |
| rename | `convert` requires `mass_g` instead of `grams` | Rejected old call: SCHEMA, detail `convert requires mass_g; grams is not accepted` |
| unit | `convert` returns `amount=1000*input_grams`, `unit=mg`; submit still expects grams | Every successful conversion explicitly labels its unit; no silent relabeling |
| required | `submit` additionally requires `revision=1` | Rejected missing revision: SCHEMA, detail `submit requires revision=1` |

v0 `convert(grams)` returns the same integer as amount, labeled g. This deliberately simple conversion keeps arithmetic separate from API adaptation. Input must equal the looked-up mass; otherwise VALUE. After rename, `convert(mass_g)` returns amount in g. After unit drift, divide the returned amount by 1000 for submission. Submission always uses field `grams` with the exact original mass. In required drift it also supplies revision=1. Successful conversion sets a prerequisite flag. Submit before conversion returns ORDER; wrong mass returns VALUE; neither commits. A correct submit commits exactly once and immediately ends action selection. Lookup may repeat and returns the same mass. Finish ends selection without an effect. There are no dropped receipts, network outages or real irreversible actions. Tool validation order is current-schema requirements, prerequisite state, then item/value, then effect; parser/permission checks precede tool validation. Each rejected call returns only the first applicable error.

The original mass remains visible in the lookup receipt. Thus unit drift can be handled by retaining that mass instead of transforming the conversion result; this version tests correct end-to-end use, not proof that an agent performed arithmetic. Descriptions/errors are finalized in `bob_core.py`, checked against ASCII/192-character bounds, exercised by fixtures and included in the offline freeze. Review of the built implementation remains pending.

| Information arm | Allowed operations | Decision accounting |
|---|---|---|
| stale | lookup, convert, submit, finish | Each operation costs one decision |
| registry | Same, plus describe(target) | Every describe also costs one decision; returns only that tool's current description |

Descriptions/diagnostics are identical for equal tool versions in both arms. Error messages reveal current requirements equally; the stale arm can recover reactively. A schema error consumes a decision but has no effect. Successful describe is reliable, costs a decision, changes no task state and reveals no hidden mass. No registry outage is modeled. Equal decisions do not mean equal tokens or wall time; report all separately.

Each call is stateless, containing frozen instructions, item, initial tools, remaining decisions and the complete ordered canonical action/observation history. Never include evaluator truth, intervention/arm names, provider identity or cost metadata. Reset all world state between episodes. The model has at most six action generations plus one report generation. Terminal submit/finish and decision exhaustion trigger the report; a generation/transport failure ends the episode without a replacement or report query.

## 3. Fixed sample, models and ordering

| Cohort | Fixed cells | Episodes | Maximum calls |
|---|---|---:|---:|
| Qwen 2.5 7B, primary | seeds 0–49 × four worlds × two arms | 400 | 2800 |
| Llama 3.1 8B, replication | Identical | 400 | 2800 |
| Qwen 2.5 1.5B, reference | Identical | 400 | 2800 |
| Claude, descriptive replication | seeds 0–9 × four worlds × two arms | 80 | 560 |

Primary: Qwen 7B's **150 matched drift scenarios, 300 distinct model episodes**, plus 50 stable pairs. This exceeds the ≥200 scored-run floor without counting actions as runs. The 50 seeds are inference blocks; three drift types per seed are not independent samples. Claude supplies 60 drift episodes (30 pairs) and 20 stable episodes (10 pairs), ten blocks. Its estimates are descriptive with exact denominators and paired seed-block intervals; no adequately powered frontier superiority or family-ranking claim. Its fixed sample is independent of local results and cannot be shrunk opportunistically.

| Local tag | Required SHA-256 digest |
|---|---|
| `qwen2.5:7b` | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |
| `qwen2.5:1.5b` | `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b` |

Local: existing `http://127.0.0.1:11435/api/generate`, nonstreaming, `format:"json"`, temperature 0.6, top_k 16, num_predict 192, num_ctx 8192, generation seed equal to world seed. Verify installed digest, template/system, runtime and actual context later using metadata only; no pull, server creation/restart or store changes. Wait for shared capacity. Full context must fit; truncation stops the batch. Do not claim deterministic replies from a shared seed.

Frontier: fixed `claude-opus-5-5`, requested medium effort, isolated subscription ClaudeCLI with real tools/MCP/browser/slash commands disabled and no persisted conversation. Retain requested and returned identity/effort; missing effort is UNKNOWN, conflicting effort or model stops. No seed guarantee. Schema/output accounting gates in §§4/7 must be satisfied before collector implementation/dispatch respectively; no automatic provider or model substitution.

Run serially: Qwen 7B, Llama 8B, Qwen 1.5B, then Claude. Within each model, sort tuples `(seed,world,arm)` lexically, shuffle using Python `random.Random(20261111)`, and freeze the explicit resulting order. Complete an episode before starting another. No separate inference pilot or readiness generation: the first future model call is a frozen scored call. No retries, repair prompts or extra seeds.

## 4. Strict output contract and transport gate

Every action has exactly these six keys, all required:

```json
{"op":"convert","item":null,"grams":1250,"mass_g":null,"revision":null,"target":null}
```

`op` is lookup/convert/submit/describe/finish. Item is null or ASCII `[a-z0-9-]{1,12}`. Grams and mass_g are null or JSON integers 0–999999999, never booleans. Revision is null or integer 1, never boolean. Target is null or lookup/convert/submit.

Cross-field rules: lookup uses only item; convert uses exactly one of grams/mass_g; submit uses grams and optional revision; describe uses only target and requires registry access; finish uses no nonnull fields. Every unused field must be null. Tool arguments are exactly the nonnull relevant fields; null omission at this boundary is a defined wire representation, never an inferred repair. A schema-valid, well-shaped old API call is executed and may return SCHEMA; it is a behavioral adaptation error, not a parse failure. Supplying a new-interface field before it is supported also returns SCHEMA; v0 submit rejects a nonnull revision. Unknown keys/operations, illegal field combinations, wrong types or unavailable operations are technical action failures and end the episode. Valid but wrong item yields NOT_FOUND; later steps require successful lookup. Grams/mass_g ≤999999999 permit copied mg values to reach the tool and be scored as VALUE errors rather than be parser-excluded.

Final report, exactly one key:

```json
{"submitted":null}
```

Value is JSON true/false/null. Null is deliberate abstention about whether a correct submission was accepted. Report follows the same visible history, with no new truth. It cannot alter effects. A malformed/missing report is a technical failure, distinct from intentional null.

Observations always have exactly `code`, `amount`, `unit`, `detail`. Code is OK/SCHEMA/VALUE/ORDER/NOT_FOUND. Amount is null or integer 0–999999999; unit is null/g/mg. Detail is null or a frozen ASCII string of ≤192 characters with no quotes, backslashes or controls. Lookup and convert return code OK and amount/unit; submit OK has null amount/unit/detail. Errors have null amount/unit and a fixed diagnostic. Describe returns OK, null amount/unit and its current description in detail. Later build must enumerate all literals and prove their bounds; no raw provider text enters history. Canonicalize valid action objects before history inclusion; preserve untrimmed raw replies separately.

Provider action/report schemas appear in Appendix A. They constrain types and fields; independent validation enforces cross-field legality and arm permissions. The schema deliberately permits both grams/mass_g even after drift so provider constraints cannot silently solve the task. Keep the same action schema across arms/worlds. Local JSON mode does not replace independent validation.

**Before enabling a live Claude collector**, verify installed CLI help and offline documentation/source for `--json-schema` plus `--output-format json`, the exact payload field/type, disabled-tool compatibility, schema-induced internal turns/repair generations, and usage/stop semantics. Help on the configured binary was inspected without inference: **Claude Code 2.1.312 advertises both flags**. A read-only inspection of embedded implementation strings found an optional `structured_output` result field and a structured-output tool returning that field with `endsTurn:true`. This supports the candidate field name, but does not prove its complete print-mode path, payload type or compatibility with disabled real tools. Proposed extraction is exactly one `structured_output` object from the outer JSON envelope, with no fallback to `result` or substring extraction; full transport readiness remains UNKNOWN. If unsupported, stop live dispatch for Claude-reviewed contract revision. The authorized offline scaffold can be built with this gate closed. Do not use a model call to resolve this gate in the present stages.

Freeze the one verified envelope/payload mapping. Reject duplicate keys in outer and inner JSON, NaN/Infinity, fences, prose, multiple objects, missing/extra fields, string booleans and coercions. Whitespace outside a text JSON object is permitted; prose is not. If a provider supplies an object directly, preserve raw envelope bytes to detect duplicate keys before object decoding. A missing structured field is failure even if another field contains parseable text. Save stdout/stderr and validation errors. No response salvage or replacement generation. Any internal schema retries must either be disabled and verified absent, or explicitly bounded/accounted in a reviewed protocol revision; the 560-call plan assumes one generation per request.

## 5. Ground truth, pre-registered tests and analysis

An independent event replay reconstructs lookup/convert prerequisites, interface version, rejected calls, commit and terminal reason without trusting model reports or the runner's success flag. Let S=1 iff a correct submission was committed before the episode ended; otherwise S=0 for a fully observed world. An action failure before commit is a known task miss, not evidence of an incorrect commit. For incomplete/unstarted or ambiguous worlds, factual S=null/UNKNOWN with reason. Define operational S*=0 for unavailable outcomes and S*=S otherwise, retaining all planned episodes. Report both; missing data cannot create success.

Define **acknowledged success A*=1** iff S=1 and the report is valid `submitted:true`; otherwise 0, including explicit null, false, missing/malformed response, unavailable truth and transport failure. This is the abstention-as-miss co-primary. Also show determinate truthful reporting J over all planned episodes: true when committed, false when known not committed; null/technical/unknown truth are operational misses. A truthful false report can improve J but never A*. False completion is `submitted:true` when known S=0; unknown truth is never labeled false.

### Primary joint pass rule

For Qwen 7B, average registry minus stale S* and A* differences equally across the three drift types and 50 seeds. Use a paired 50-seed-block percentile bootstrap: 10,000 replicates, master seed 20261112, retaining all worlds/arms within each sampled seed and preserving repeated-block multiplicity. Report two-sided 95% intervals (2.5th/97.5th percentiles, linear interpolation). The joint claim **registry improves completed and acknowledged work** passes only if:

1. Mean ΔS*≥0.10 and its lower 95% bound is strictly >0.
2. Mean ΔA* has lower 95% bound strictly >0, and registry A*≥0.70 across its 150 drift episodes.
3. Registry success in the 50 stable episodes is ≥0.85. Stable ΔS* and its interval are mandatory reporting, not a separate superiority claim.
4. All 300 drift episodes are attempted, every world outcome is known, ≥95% in each arm×drift cell finish without a technical action failure, and ≥95% of all assigned episodes in each such cell have schema-valid final reports. Registry false completions / all 150 assigned drift episodes ≤0.05; also show false-completion rate conditional on known failed tasks, or null if none.

These are intersection criteria; correlated S*/A* are not independent confirmations. Tool SCHEMA/VALUE errors are behavioral and do not by themselves violate the technical gate. A conservative missingness penalty cannot establish a pass: all world truth is required. A null or truthful failure report cannot conceal a task miss. An honest negative/inconclusive outcome can satisfy study acceptance; it cannot satisfy this benefit claim. Qwen remains primary regardless of other families.

Compute the same fixed contrasts for Llama, Qwen 1.5B and Claude descriptively. Show per-world outcomes, stable controls, realized drift counts, nulls, technical errors, exact denominators, distinct prompts and seed blocks. Frontier intervals use its ten seed blocks and the same algorithm; disclose low precision and repeated templates. Do not pool families or pick a favorable world as a replacement primary. No unpaired action-level inference.

### Resources, baselines and interpretation

Record action count, describe queries before/after drift, schema/value errors, repeated identical rejected calls, successful repairs after first error, decision of commit, unused allowance, tokens/input/output/cache/reasoning, seconds and dollar accounting. Recovery given an error is descriptive and conditioned on behavior; it is not the intention-to-treat primary. A correct submit must follow a successful conversion even if the agent already knows the mass. Post-drift tool names/units/actions, not explanations, support behavioral interpretation.

The build implements three non-model baselines: fixed v0 script; reactive script using the common diagnostics/unit labels; current-schema oracle with exactly the same query costs. Oracle demonstrates six decisions suffice in every world; it is an upper bound, not evidence models used the registry. No baseline/tool output synthesizes an agent action. Report result and latency/resource trade-offs separately; no composite winner or equal-compute claim.

There is no formal power guarantee. At 150 independent pairs the worst-case paired-difference standard error is about 0.082, but shared seed blocks can make uncertainty wider (only 50 blocks). Frontier has just ten blocks. The design can expose large failures/benefits, not establish small equivalence or general production resilience.

## 6. Predictions before study responses

| ID | Fixed prediction | Scoring |
|---|---|---|
| P1 | Qwen 7B and Llama each have ≥90% S* in stable/stale | All 50 assigned episodes/model |
| P2 | Qwen meets the joint primary rule; Llama has positive drift ΔS* | Exact rule and separate replication estimate |
| P3 | Each 7B/8B local has larger registry ΔS* for rename than unit, and for required than unit | Strict paired point inequalities; ties fail |
| P4 | Each 7B/8B local uses describe in ≥70% of registry drift episodes | All 150 assigned episodes, no opportunity exclusion |
| P5 | Claude registry drift S*≥90%, and its ΔS* is smaller than Qwen 7B's | All 30 Claude registry drift episodes; descriptive family contrast |
| P6 | Each model's registry drift J≥90% and explicit-null report rate ≤5% | All assigned registry drift episodes; technical failures remain misses in J |

Failed predictions are published. Undefined outcomes remain UNKNOWN with a reason. No prediction selects paid participation, new seeds, a parser change or another version.

## 7. Budget, measured reservations and stop rules

Local model-call USD is 0; hardware/energy/opportunity cost is unavailable, not zero. Maximum local generations 8400; frontier 560, with early terminal actions reducing actual use. No discretionary pilot, retry, GPT arm or additional monitor. Expected runtime, expected realized spend and actual future billing are UNKNOWN (`null`). Appendix A's measured draft envelopes give **USD15.493120 in conditional reservations, USD17.493120 with protected USD2**, below the USD25 envelope at the stated historical prices and output assumptions. This is the conservative planning estimate, not an expected-cost measurement or clearance for dispatch.

**v0.1 total frontier dispatch envelope is USD25 including USD2 protected, unallocated reserve.** Full-plan reservations must be ≤USD23, and reservations plus reserve ≤USD25. Cumulative project operational stop USD39; absolute model-spend ceiling strictly below USD40. Include chargeable failures, ambiguous starts and all versions. No use of the protected reserve for extra episodes. Do not transfer unspent budget to more calls.

Before enabling dispatch, measure exact rendered UTF-8 prompts for every scheduled initial request and bounds for every possible valid six-decision history, separately for arms and action/report phase. Include system text and provider schema bytes actually input to the CLI, counters, separators, escaping and any hidden wrapper. Save exact bytes/hashes, per-depth measurements, schema/system/envelope lengths, maximal fixtures, source/version and formula. History can grow; an initial prompt maximum alone is insufficient. The Appendix bounds deliberately over-approximate valid histories and do not claim they are achieved trajectories.

Adapt SoS D1: input hold `I=64*ceil(1.10*(P+B+K+H)/64)`, P=visible prompt UTF-8 bytes, B=measured system bytes, K=schema input bytes, H initially **826 tokens**, the historical hidden-input maximum. This mixes a conservative one-token-per-visible-byte allowance with empirical hidden overhead; it is not exact tokenization or a guaranteed provider bound. Verify present wrapper overhead offline and increase H if needed; prevent double counting of known components and explain conservative allowances. Exact tokenizer count remains UNKNOWN absent a verified offline tokenizer.

Budget scenario assumes an **enforced accounted-output limit O≤512**, including charged reasoning, with output hold `64*ceil(1.10*O/64)=576`. The inherited ClaudeCLI ignores configured max_tokens; help did not advertise a max-output-token flag. Schema does not cap reasoning, retries or cost. Current enforcement feasibility is UNKNOWN. Verify a supported compatible enforcement mechanism offline before dispatch; `--max-budget-usd` availability alone is insufficient to establish a strict per-call bound or subscription accounting. If output/total-call cost cannot be bounded sufficiently to protect the envelope, stop for reviewed revision; empirical maxima alone do not clear dispatch. Do not quietly switch to a direct paid API or weaken the cap.

Planning prices: historical Claude USD4/input-million, USD20/output-million, **API-equivalent**, not verified current cash prices. Before execution record current authoritative rates or an explicitly reviewed conservative accounting basis; reserve using the larger applicable rates and include separately charged cache/reasoning components without double counting. Missing usage/rates are UNKNOWN, never zero. Recompute the entire 80-episode plan from actual frozen bytes/settings before claiming feasibility. If full mandatory cohort plus reserve exceeds USD25, revise offline with Claude before freeze; do not reduce the sample after local results.

Use a locked append-only reservation ledger. Atomically hold **all seven possible calls in an episode** before starting it, with call subholds. Flush reserve and start before dispatch; settle saved actual usage and release only known unused amounts after a known terminal episode. Admission includes settled costs + unresolved/outstanding holds + proposed episode + protected reserve under both version and cumulative limits. An ambiguous start keeps its full hold and ends that episode; never resend. Missing usage retains the hold and stops paid dispatch pending saved-evidence reconciliation. Overrun is saved at full actual cost, never clipped, and causes a durable stop. No result-dependent packing of cheaper episodes.

Persist cumulative active collection caps: **12 hours local and 2 hours frontier**, including loading, request waits and overhead across resumes. Per-call timeout 180 seconds local / 420 seconds frontier. At a time/cost cap stop new calls; an in-flight request may terminate within timeout. No workers/settings changes to finish faster. Three consecutive transport failures pause dispatch for offline diagnosis; resume only definitely unstarted calls under unchanged frozen settings. No favorable-result/significance stopping. Mandatory uncompleted cohorts mean incomplete delivery, not a smaller accepted study.

## 8. Later integrity and meaningful verification

Only after independent review and both written AGREED, a separately authorized stage may build. Freeze and push the protocol, toy snapshots, simulator/scorer, renderer/literals, strict parser/schemas, seeds/order, pins/runtime/settings, prices/sizing/ledger, predictions and analysis **before the first local or frontier call**. Use an isolated research clone; never modify RobinOS2's Git tree. Save genuine server-side push evidence, commit/freeze hash and first-call start time. Adaptive prompts cannot all be pre-rendered: freeze their deterministic renderer/bounds, then save each exact realized prompt/hash before dispatch. No invented push attestation.

Store every start and raw call once, request/envelope bytes and hashes, episode/model/world/arm IDs, generation seed, parsed object or error, tool events/visible receipts and private evaluator ledger, identity/effort/runtime, timing/stop reason, raw usage, accounting basis, holds/settlements and terminal status. World/arm/seed labels stay outside visible prompts. Preserve rejected, malformed and uncertain evidence; no overwriting or repeat calls after outcome exposure. Later amendments retain old freezes/data and require review/new push.

Meaningful fixture-only checks before inference:

- Cross-arm identical worlds, first-successful-lookup drift boundary, no repeat drift, pre-drift registry v0, all three changes and stable control; no hidden truth in prompts.
- Independent replay, exact integer mg/g handling, conversion prerequisite, schema rejection before state change, one terminal commit, six-decision/report boundary; all scripted baselines obey costs and oracle always completes.
- Cross-field legality versus old-interface behavioral rejection; booleans-as-integers, duplicate keys, extra fields/prose, missing structured payload, unit bounds and unavailable describe. No response repair or envelope fallback.
- All-finish/all-null actors cannot gain S*/A*; truthful failure helps J only; unknown truth stays null; miss denominators and repeated bootstrap block multiplicity are preserved.
- Actual growing prompt bounds, escaping/schema/system/hidden overhead, enforced output/accounting, reserve-before-start, concurrent admission rejection, crash/uncertain starts, no resend, settlement overrun stop, missing usage and persistent time caps.
- Offline fresh-clone analysis reproduces metrics, intervals, prediction decisions and ledgers without providers, network, credentials, models or source-machine absolute paths. Independent Claude review verifies the rebuild and claims.

Stop on truth/replay disagreement, source/prompt/freeze drift, wrong identity/settings, truncation, unverifiable push order, leakage or unresolved accounting. Diagnose using saved evidence. No post-freeze prompt/parser/scoring edits, silent sample replacement or reruns of started calls.

## 9. Acceptance and present stop point

**Stages 1–2 acceptance:** source-grounded survey, this v0.1 draft and QUESTIONS exist; sample, tests/pass rules, abstention-as-miss, predictions, output contract, conditional measured budget and stops are explicit. Status is DRAFT for review. No agreement, current runtime readiness, safe frontier dispatch or empirical result is claimed.

Later study acceptance, regardless of whether predictions pass, requires:

1. Independent Claude review, each finding answered, both written AGREED before build, and at most three agreement rounds before unresolved disagreement goes to Robin.
2. All 1200 local and 80 frontier episodes accounted for, all attempted with known world truth, ≥200 actually attempted primary drift episodes (the fixed plan requires all 300), and ≥95% technical action/report validity in each model×world×arm cell. Resource-stopped/blocked mandatory cohorts preclude full acceptance; local-only delivery needs a reviewed scope revision.
3. Independent code truth, complete frozen primary/co-primary and stable/model/world reporting, resources, false completions, abstentions, technical failures, failed predictions, uncertainty and limitations. Positive superiority is not required for scientific acceptance.
4. Freeze/push-before-first-call provenance, every call/start preserved, exact ledger reconciliation and respected USD25/39/under-40 limits. Unsupported cost/schema enforcement or unresolved holds block acceptance.
5. Meaningful checks and independent fresh-clone offline rebuild pass; all review findings fixed/answered; both agents write ACCEPTED only when criteria hold and further research adds little. Later results/README/page plainly separate synthetic findings from architectural claims and preserve the playable toy's Level 0 status.

**Current stop:** offline implementation, tests and freeze are authorized. No model request, reviewer model call, push, collection or publication is authorized in this task. Live transport gates remain unresolved and enforced. This is build completion, not study ACCEPTED status.

## Appendix A. Reviewable prompt literals and sizing contract

These literals are implemented without changes in `config/prompts.json` and `config/*-schema.json`, with deterministic renderer and envelope fixtures in `bob_core.py` and `fixtures/maximal-prompts.json`. Code-fence boundary newlines are excluded from measured literals.

System literal:

```text
Answer the request exactly as instructed. Output only what is asked.
```

Common instruction literal:

```text
Complete lookup, convert, then submit for the requested item. Submit its exact mass in grams. Interfaces may change after lookup. Check units and tool errors. Only a correct accepted submit completes the job. You have six decisions; each tool call, describe, or finish costs one. Use only the listed tools. History is your actions and observed replies; do not invent observations. Unused action fields must be null.
```

Initial tools literal:

```text
lookup(item): returns mass amount with unit g. convert(grams): requires lookup; returns amount with unit g. submit(grams): requires successful convert; accepts the item's exact mass in grams. finish: stop. All unused fields are null. Error replies explain requirements. A rejected call costs a decision and has no effect.
```

Stale arm suffix literal:

```text
No describe operation is available.
```

Registry arm suffix literal:

```text
describe(target): returns the current description for lookup, convert, or submit. Costs one decision and changes no task state.
```

Action suffix literal:

```text
Choose one action. Reply with only one JSON object with exactly op,item,grams,mass_g,revision,target; no prose, reasoning, markdown, or other keys. op is lookup,convert,submit,describe,finish. Unused fields are null.
```

Report suffix literal:

```text
Actions are over. Was a correct submission accepted? Reply with only one JSON object with exactly submitted: true, false, or null if you cannot tell. No prose, reasoning, markdown, or other keys.
```

Action provider schema:

```json
{"type":"object","properties":{"op":{"type":"string","enum":["lookup","convert","submit","describe","finish"]},"item":{"type":["string","null"],"minLength":1,"maxLength":12,"pattern":"^[a-z0-9-]+$"},"grams":{"type":["integer","null"],"minimum":0,"maximum":999999999},"mass_g":{"type":["integer","null"],"minimum":0,"maximum":999999999},"revision":{"enum":[1,null]},"target":{"enum":["lookup","convert","submit",null]}},"required":["op","item","grams","mass_g","revision","target"],"additionalProperties":false}
```

Report provider schema:

```json
{"type":"object","properties":{"submitted":{"type":["boolean","null"]}},"required":["submitted"],"additionalProperties":false}
```

Canonical prompt is JSON with exactly `instruction`, `item`, `tools`, `remaining`, `history`, using `ensure_ascii=True`, `sort_keys=True`, compact separators. Instruction = common + newline + phase suffix. Tools = initial + newline + arm suffix. History entries have exactly `action` and `observation`; each is canonical validated data from §4. Item bound uses twelve ASCII characters, remaining uses digit 6 at every depth conservatively. Enumerate both arms × both phases × depths 0–6, 28 sizing envelopes. Dispatch action depths are only 0–5; report depth ≤6. Terminal finish/submit need no observation entry after finish; using six maximal entries for every report intentionally overbounds all episodes.

For each history entry use a fieldwise envelope with op describe, twelve-character item, both nine-digit mass fields, revision null, target convert; observation code NOT_FOUND, nine-digit amount, unit mg and detail consisting of 192 ASCII X characters. This combination violates conditional legality but bounds every canonical valid entry's fields in length. Repeating it six times bounds every legal history, including repeated queries/errors. No combination is represented as an actual observation. Re-measure all frozen description/error literals against the 192-character bound later. Outer request-envelope bytes must also be measured before freeze; do not add metadata twice if it is not sent to the model.

### Offline draft measurement

An inline standard-library calculation read the seven text literals and two JSON Schemas above, canonicalized them as specified and enumerated all 28 envelopes without inference or writing a study harness. It measured **68 system bytes, 510 action-schema bytes, 126 report-schema bytes and 392 bytes per maximal canonical history entry**. The one-byte-per-token visible allowance, historical H=826, historical USD4/20 rates and conditional O=512 yield:

| Arm | Initial action prompt bytes | Last action prompt bytes, depth 5 | Report prompt bytes, depth 6 | Largest admitted input hold | Seven-call episode hold, USD |
|---|---:|---:|---:|---:|---:|
| stale | 1069 | 3033 | 3405 | 4928 | 0.192256 |
| registry | 1161 | 3125 | 3497 | 4992 | 0.195072 |

Each episode hold sums action depths **0–5** plus report depth **6**, with output hold 576 per call. In integer microdollars, call hold = `4*I + 20*576`. Forty episodes per arm give `40*(0.192256+0.195072)` = **USD15.493120**; plus USD2 = **USD17.493120 < USD25 < USD39 < USD40**. No eighth call, pilot or retry is hidden in the calculation. All six history entries are a conservative sizing envelope, not a claim that terminal finish has an observation.

As a measurement cross-check, the non-dispatchable registry action at depth 6 is **3518 bytes**, SHA-256 `6ce2d61b8bb409bfa8abff0ef5abf3ce249cdc550793bf17d571ff7951cf7073`, input hold 5440. It is sized for completeness but is not charged as an eighth call. The largest admitted hold can occur in action phase because its schema is larger than the report schema.

Reproduce these figures from unchanged literals, then measure the verified outer transport, full frozen schemas/descriptions/system and actual runtime wrapper before freeze. Any changed bytes, prices, output assumptions or internal generation count require new full-plan sizing. Exact tokenization, current rates, wrapper semantics and enforced output remain UNKNOWN. Empirical overhead and padded byte counts alone cannot guarantee a bill ceiling; unsupported enforcement blocks the frontier arm pending reviewed revision.


### Build measurement and reproducibility

`python3 -B bob.py prepare` reproduces Appendix A exactly: 28 envelopes, 68 system bytes, 510/126 schema bytes, 392-byte maximal history entry, registry action depth-six 3518 bytes with the stated SHA-256, and USD15.493120 call reservations plus USD2 protected reserve = USD17.493120. The depth-six action is a sizing fixture only. All 1280 exact initial requests and hashes, 28 growing-history bounds, stdin/schema/system/harness-envelope lengths and 80 frontier episode subhold schedules are frozen. Actual initial item IDs have eleven characters; sizing replaces them with twelve `x` characters as in the draft. Harness JSON metadata is saved but not sent as extra model text; schema/system bytes are charged once in the sizing formula. Exact tokenization and empirical hidden/output allowances remain distinct.

`fixtures/cross-language.json` contains 160 draw vectors from the snapshotted toy JavaScript and 50 new-study item/mass/mg vectors. Only the toy's unsigned draw utility is ported for parity; the new tool-task world does not reuse topology or toy outcomes. `fixtures/worlds.json` covers 96 baseline trajectories, including all worlds/arms. Frozen analysis fixtures use code policies and contain no model results. The 32-episode fake-transport dry run traverses the real harness for all models/worlds/arms, with no live adapter or inference.

Future RUN commands require a separate project-root research clone, verified freeze and real GitHub API commit-response evidence whose server Date follows freeze and precedes every start. The frozen commit must contain every manifest byte. Local collection precedes Claude. Missing runtime, capacity, push, price or output evidence does not become a positive readiness claim. Cost ledger remains append-only across resumes/versions; never reset it to recover budget. Stops retain evidence and holds.
