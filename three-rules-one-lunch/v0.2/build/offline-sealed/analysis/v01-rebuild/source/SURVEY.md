# Three Rules, One Lunch · Survey

11 November 2026 (HKT). Codex, Wave 2, stages 1–2. Proposed study: [PROTOCOL.md](PROTOCOL.md), **v0.1 draft, awaiting Claude review**. No model inference, implementation, freeze, Git mutation or publication occurred. Only this folder is writable for this task. The supplied Codex claim was confirmed with read-only `claim.py list`; the shared claim/log was not changed, including release, because Robin explicitly restricted writes to this folder.

## What the playable experiment establishes

The toy's actual slug is **`three-rule-swarm`**, not this research folder's name. The website root's `public/` and `src/` do not contain it. The inspected release is:

`<WORKSPACE>/00_identity_output/website/_releases/research-rebel-20261110/public/three-rule-swarm/`

Read `README.md`, `model.mjs`, `batch.mjs` and `results.json`. There is no `EXPERIMENT.md` in that public allowlist. The corresponding page is `../research-home-20261110/src/pages/intelligence/three-rule-swarm.astro` relative to the release directory. Source model SHA-256 is `b687e43d52ed57165684662bef48c982b3cedcdac69fec333d6268ac6200a5ad`, matching the saved result's `modelSha256`. Saved batch counts and means were inspected; the simulator/tests were not executed or fully reproduced during this survey.

Three scripted policies search a 24×16 toroidal grid with two smooth, deterministic, non-depleting food patches. The default has 32 queries per round for 160 rounds, exploration 0.15 and sharing 0.35. Food moves halfway through. All arms receive the same observation allowance, but independent policy random streams.

- The local swarm moves one cell per query. Walkers continue successful headings, sometimes follow adjacent sampled traces, and explore after three disappointments or an exploration draw. Shared rewards decay by 3% each round.
- The central learner can query **any** cell. It explores uniformly or reuses its best decaying remembered cell. Its mobility differs from the walkers'.
- Uniform random search has no useful memory. Observations are equalized; internal work, communication, movement, FLOPs, latency and money are not.

Saved means, reward per observation, over all 32 seeds in each setting:

| Setting | Swarm | Central learner | Random |
|---|---:|---:|---:|
| Default | 0.505865 | 0.814851 | 0.163736 |
| No sharing | 0.225781 | 0.814851 | 0.163736 |
| No relocation | 0.582506 | 0.837554 | 0.165011 |
| High exploration | 0.355415 | 0.570323 | 0.163736 |
| Eight walkers/queries | 0.371356 | 0.735435 | 0.162971 |
| Sixty-four walkers/queries | 0.540680 | 0.843935 | 0.164663 |

There are 192 saved seed/setting runs, each containing three policy summaries; these are not 576 independent worlds. Changing walker count changes every arm's observation allowance across settings. The central policy wins these settings, and the no-sharing ablation greatly reduces swarm reward. This does not establish superiority of centralized AI planning, identify intelligence separately from mobility, or show that communication pays its real cost.

## Research question and deliberate narrowing

`ANTresidency/experiment_to_research.md` §7 recommends **merging this direction into Minimum Intelligence**, retaining Three Rules as a teaching game. That recommendation is a scope warning, not evidence that a separate empirical study already exists. Robin now explicitly requests this project's draft. The proposal therefore isolates a small question that can also serve as a Minimum Intelligence module:

**With equal legal query access and observation allowance, do faithful shared observation receipts improve a team of model workers over private receipts? How does one central planner compare?**

The primary intervention changes only the receipt visibility of three otherwise identical workers. A secondary central planner chooses the same three simultaneous queries in one call. All arms may jump anywhere, removing the toy's mobility asymmetry. We deliberately change grid size and horizon to make local-first collection practical. This is a new bounded environment inspired by the toy, not a replication of its reported numbers. The experiment does not test learned free-text notes, deception, agent personalities, emergent intelligence or the best architecture at equal total compute. No monitor or self-report judge is added.

## Reusable structure and observed lessons

| Source inspected | Reuse in a later authorized build | Limit |
|---|---|---|
| `../work-or-proof/{SURVEY.md,PROTOCOL.md,README.md}` and `wop_stats.py` | Source/exposure inventory, fixed primary model, paired blocks, conservative all-scheduled denominators, fresh-clone offline rebuild | Archived monitoring outcomes are not observations for this search task |
| `../signal-or-silence/{SURVEY.md,PROTOCOL.md,QUESTIONS.md,sos_collect.py}` and `sos_stats.py` | Pinned Ollama identities, isolated ClaudeCLI transport, strict validation, append-only attempts, paired bootstrap and separate coverage | Old verdict parser/output assumptions must not be copied into a new action schema |
| `../signal-or-silence/{DEVIATIONS.md,sos_d1.py,config/cost_basis.json}` | Measure actual prompt bytes at every depth; include system/schema and hidden CLI input; reserve before dispatch; retain uncertain holds and stop on overruns | Historical overhead/output maxima and API-equivalent rates are empirical planning inputs, not hard/current billing bounds |
| `../receipt-gap/PROTOCOL.md` and Claude's `REVIEW-claude-20261111-r1.md` | Strict payload contract, no extraction/repair, whole-episode holds, informative frontier sample | Review rejects a 24-episode frontier arm: use at least 60; verify schema transport before collector implementation |

SoS D1 records that the original 1,282-input-token historical maximum was exceeded by a different explicit prompt. D1 used exact visible bytes plus the historical 826-token hidden-input maximum, with 10% margin rounded to 64 tokens. It preserved the overrun and revised cost controls without changing scientific inputs. This draft measures its own bounded prompts instead of inheriting that maximum.

Offline inspection of the runtime-selected binary, without sourcing its environment or exposing credentials, found **Claude Code 2.1.312**. `--help` advertises `--json-schema` for print mode and `--output-format json`. Read-only inspection of bundled binary strings/code found an optional `structured_output` result field and a terminal structured-output handler. Binary SHA-256: `6b5ec691195e551b02c41df9f7d723f4ea61eaa03c2df90acefe3736f1aeb620`. This establishes installed offline schema support, not successful live transport. Plain `claude` is absent from this shell's PATH; use the established runtime binary resolver later. Do not substitute another executable silently.

The help also advertises `--max-budget-usd`; that alone does not prove a hard per-request output/cost ceiling. Effective output-limit enforcement, hidden overhead under structured output, and automatic retry behavior remain **UNKNOWN**. They must be resolved offline before frontier dispatch; no exploratory model call was made to resolve them.

Receipt Gap's concurrently available r2 transport appendix and `evidence/cli-contract.json` identify candidate controls in this same binary: `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, hidden `--max-turns`, and structured-output/provider retry settings. Those are useful implementation evidence, not a completed verification of this draft's 1,024-token/medium-effort contract. In particular, all startup and internal requests must be covered by accounting and limits, not merely the visible action response.

## Draft feasibility and handoff

The fixed proposal has 900 local episodes and 60 frontier episodes, with 100 local/20 frontier seed blocks. Each arm receives twelve query opportunities. The primary local comparison contains 200 model episodes. Exact draft prompt sizing gives at most **USD18.083840** frontier reservations at historical API-equivalent rates and the conditional output allowance; including USD1 protected reserve gives **USD19.083840**, below the **USD25 dispatch envelope**. This is conditional feasibility, not clearance to run. Current-stage spend is USD0; actual cash billing and future elapsed time are unavailable.

Sources already exposed: toy outcomes above, programme design recommendations, sibling results/methods and Receipt Gap review. No prospective search-model replies are known. Next work is Claude's stage-3 review of the protocol and questions. This task stops after the documents: no agreement asserted, build, freeze, model calls, sibling edits or shared-board updates.

Document verification re-read the draft's literal blocks and independently checked every prompt-depth byte maximum, schema/system lengths, reservation arithmetic, local document links and the three-file write scope. These were offline document checks, not harness tests or inference.
