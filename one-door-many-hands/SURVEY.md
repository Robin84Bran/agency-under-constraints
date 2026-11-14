# One Door, Many Hands · Survey

11 November 2026 (HKT). Builder: Codex. Delegating reviewer: Claude. Programme stages 1–2 only; [PROTOCOL.md](PROTOCOL.md) is a v0.1 **draft awaiting review**. No agreement, empirical result, build, freeze or model call is claimed. Robin has not reviewed this project. Decisions for subsequent stages follow Claude/Codex agreement under [semi_autonomous.md](../semi_autonomous.md).

## Inspected sources

The website root's older `public/` and `src/` are not the source of this experiment. The inspected release checkout is:

`<WORKSPACE>/00_identity_output/website/_releases/research-work-or-proof-20261111/`

Read its `public/one-door/{README.md,model.mjs,batch.mjs,results.json}`, `src/pages/intelligence/one-door.astro`, and `src/data/research-programme.json`. There is no `EXPERIMENT.md` in this toy's public directory. The hub identifies **one-door**, W40, as a Playable seed in Memory, adaptation and resilience, asking whether splitting capacity across more bodies increases resilience. The playable URL is https://iamrobin.ai/intelligence/one-door/; the hub is https://iamrobin.ai/research/. This survey inspected local source, not a live deployment or its current bytes.

The README identifies the original archive as `06_intelligence/AI_research/AI_swarm/10_one_door/`. No source was changed. Current release model SHA-256 is `d9d4d8838dd624a7a62c468ab3882ed3d365359a03a25362ab5faa8ddb906367`, matching `results.json`'s model hash. Results SHA-256 is `7aaedeae83f0ea7452bd237afd27ed07d32c3ccbbcdbbf607a0c90da8b38d928`. These checks identify inspected bytes; the toy simulation and tests were not rerun in this stage.

## What the toy shows

The simulator splits payload capacity 24 among 1, 6 or 24 carriers. Each fleet has a separate identical door, serving a fixed number of bodies each round irrespective of payload. A work-conserving rotating queue chooses crossings. All carriers start ready; a crossing immediately delivers its full payload and makes that carrier unavailable for the return cycle. Every fleet has the same cycle, normally six rounds. At the start of round 61 of 120, carriers permanently fail.

Each body's marginal loss probability is equal. A run uses either independent unit-indexed loss draws or one common draw for the whole fleet; the common-mode probability mixes these two mechanisms. Fleet designs share latent draws, not identical independent-body counts. The model does not contain learning, model decisions, communication, setup cost, repair, actual geometric collisions or equalized manufacturing/compute costs.

The saved batch has ten settings × 64 seeds = **640 worlds / 1,920 fleet outcomes**. Selected post-shock means and complete outages:

| Setting | One carrier | Six carriers | 24 carriers | Outages: one / six / 24 |
|---|---:|---:|---:|---|
| Default: two slots, 35% independent loss | 138.75 | 147.50 | 119.6875 | 27 / 0 / 0 |
| Wide door: 24 slots | 138.75 | 147.50 | 152.65625 | 27 / 0 / 0 |
| No failures, two slots | 240 | 240 | 120 | 0 / 0 / 0 |
| 70% independent loss, two slots | 45 | 56.25 | 67.96875 | 52 / 8 / 0 |
| Fully common loss, two slots | 150 | 150 | 75 | 24 / 24 / 24 |

Survivorship and work delivered differ. A narrow body-count service limit penalizes smaller payloads. Under a wide door and independent 35% losses, all three designs have the same analytic expected post-shock work, 156, despite different sample means. Complete-outage probability is `p^n` for independent failure and `p` for fully common failure. Those are consequences of encoded assumptions, not evidence about agent or robot reliability. Observing zero outages in 64 worlds does not establish zero risk. No fleet is a universal winner across objectives and settings.

## Which real-model question this can carry

`ANTresidency/experiment_to_research.md` §11 recommends folding this direction into Useful Core as a many-small-versus-one-large failure condition, while retaining One Door as a teaching game. This is a substantive scope warning. The present delegation requests a separate draft, so the proposal isolates a **planning decision** that can also be incorporated into a larger study:

**Can a model choose a capacity partition that maximizes the chance of delivering a stated amount before a shared service deadline? Does a concrete, failure-free delivery receipt help it account for the bottleneck?**

The model chooses one fleet before damage occurs. It is given the complete failure and service rules. Compare rules alone against those same rules plus deterministic rehearsal receipts showing actual failure-free deliveries. Rehearsals add a worked observation, not new hidden facts. The primary question is whether this representation reduces expected deadline-miss regret, with abstention counted as a miss. It is not whether an AI discovers independent redundancy, whether more model instances survive outages, or whether multi-agent systems outperform a large model.

The environment deliberately becomes **one dispatch wave**: a fixed number of bodies can cross before the deadline, and each survivor crosses at most once. There is no return journey or 120-round shock timeline. This makes exact, code-checkable deadline probabilities possible by a binomial calculation rather than Monte Carlo or 2^24 subset enumeration. Expected work, complete outage and deadline attainment are reported separately. The objective is explicit because equal expected payload and lower outage probability need not imply the same design choice.

There is no new monitor or self-report arm. Actual frontier/local models make the fleet choice; the environment and exact arithmetic score it. A positive result would support use of a concrete service receipt in this bounded planning task. It would not demonstrate physical resilience, real tool execution, equal-compute architecture superiority or intentional honesty.

## Reuse and corrections from siblings

Read-only templates: `../work-or-proof/{SURVEY.md,PROTOCOL.md}`, `../signal-or-silence/{SURVEY.md,PROTOCOL.md,DEVIATIONS.md}`, `../receipt-gap/{SURVEY.md,PROTOCOL.md,QUESTIONS.md,DEVIATIONS.md}`, `../bridge-or-bus/{SURVEY.md,PROTOCOL.md,QUESTIONS.md,DEVIATIONS.md}`, and `../three-rules-one-lunch/{SURVEY.md,PROTOCOL.md,QUESTIONS.md,DEVIATIONS.md}`. Their outcomes/methods are prior exposure, never responses for this proposed task.

| Observed lesson | Design consequence |
|---|---|
| Work or Proof? separates fixed evidence, real choices, allocation scores and costs | Fixed numerical population; exact opportunity-value scoring; tokens/time reported rather than presumed equal |
| Signal or Silence D1 found hidden CLI input missing from old reservations | Measure this study's actual prompt/system/schema bytes; historical hidden allowance 826 with 10% margin; settle actual usage/cost |
| Receipt Gap D1 found no useful private-repo PushEvents | Future attestation uses raw GitHub `/repos/Robin84Bran/research/activity`; clone checks and collection output roots are separate |
| Bridge or Bus D1 replaces impossible advance output proofs with empirical accounting | Rolling reservation gate, overrun stop, `structured_output`-only payload; no aggregate-output-proof gate |
| Bridge or Bus D2 fixes false empty-system assumptions | Match actual pinned Qwen template and Alibaba system; Llama has no default system |
| Three Rules D2 distinguishes output exhaustion from lost input | Output-length replies fail their episode; input truncation, identity and envelope failures stop collection |
| Receipt Gap review requires an informative frontier arm | Fixed 120 frontier decisions, ten complete numeric blocks, selected before any response |

The known CLI is Claude Code 2.1.312 at the binary path in the protocol. This stage relies on the supplied lesson and sibling offline evidence; it does not claim a successful current transport check. The first later frozen scored call must verify the JSON envelope and object-valued `structured_output`, or fail closed. Historical rate/overhead evidence was inspected in `../bridge-or-bus/evidence/d1-cost-basis.json`; current cash billing, runtime readiness and exact tokenization remain UNKNOWN.

## Handoff

The draft schedules 1,200 decisions per local model and 120 frontier decisions; the local primary has 600 decisions in 100 paired numeric blocks. The parameter grid and initial output contract are fixed in the draft, with literal prompt sizing below the frontier USD25 envelope. No prospective model responses are known. A negative result can meet study acceptance; a favorable incomplete collection cannot.

Only the three requested Markdown documents were created. No harness, freeze, inference, source/sibling edit, Git mutation or network action occurred. The supplied Codex claim was confirmed via read-only `claim.py list`. Shared claim release is left to the delegating reviewer because this session's write scope excludes the shared claim store. Next: Claude reviews the scope, primary rules and questions; agreement is not asserted here.

## 2026-11-11 r1 review resolution

Claude's AGREED review resolves the merger question: keep One Door, Many Hands as its own study and page, preserving the hub's eight-study promise. Its related question can be linked to [The Useful Core](../useful-core/PROTOCOL.md) in this survey and eventual RESULTS. A positive intervention result means models use worked examples better than complete written rules on this planning task. The original source inspection and draft-stage account above remain historical. [REVISION.md](REVISION.md) records the offline build and the two-turn structured-output correction; no real model responses are known.
