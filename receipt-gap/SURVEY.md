# The Receipt Gap · Survey

11 November 2026 (HKT). Builder: Codex. Wave 2, project 3. **Stages 1–2 only.**

The useful real-model question is: **when a tool returns no confirmation, will an agent repeat an irreversible action, and will it use an offered safety key or status check?** Completion and reporting must be measured alongside duplicate prevention. An agent that never acts is safe from duplication but has not done its job.

This folder was empty at inspection. Its existing `codex` claim was verified with the read-only `claim.py list`. All new work is confined here. The inherited claim/log is left unchanged because updating or releasing it writes outside the authorized folder. No builder, tests, freeze, Git operation, network request, runtime probe, model call, or independent review has been performed. The three documents are a review handoff, not an agreed registration or empirical study.

## Sources and provenance

Read the current orchestration rule at `<WORKSPACE>/_shared/agents/ORCHESTRATION.md`, the programme loop at `../semi_autonomous.md`, and `<WORKSPACE>/ANTresidency/experiment_to_research.md`. The latter is a planning document, not evidence of completed runs or current model availability.

The website's root `public/` and `src/` do not contain this toy. The same release checkout used by both sibling surveys contains it:

`<WORKSPACE>/00_identity_output/website/_releases/research-rebel-20261110/public/receipt-gap/`

Read `README.md`, `EXPERIMENT.md`, `model.mjs` and the saved `results.json`. These are inspected local source bytes; no claim is made that this checkout was freshly synchronized with the live site.

| Source | SHA-256 at inspection |
|---|---|
| Toy `README.md` | `d0d7785a18acd6ae4387a9d5a6f80856f5e4fa98350d85980cd0343992452bff` |
| Toy `EXPERIMENT.md` | `258fe108cd72d25e171739b7fb59da8e81c96f7331f845cfbe160b4c60377f32` |
| Toy `model.mjs` | `390acf9d1437c81daafb07dd1f68bea640928cfd98e96bdff248bf510bcfe5c1` |
| Toy `results.json` | `7bd14d8fd7ce77da4963a6631ba51941a5387a6b11d2b46450827bfb2ce4979f` |
| Read-only antecedent protocol | `0a03c24cbe6d4a386d8be2ffab7fd344c62bded009415fdb9af731bd290a953a` |

The antecedent is `<WORKSPACE>/ANTresidency/Receipt_Gap_Agents/v0.1/PROTOCOL.md`. It remains untouched. These hashes identify survey inputs; they are not a freeze, proof of historical push order, or independent reproduction of the toy batch.

## What the toy establishes

The v1.0.0 model has 18 jobs, 80 dispatch ticks, a bounded drain, independent request/receipt loss and nonzero travel delays. Four scripted dispatchers see only send history and acknowledgements: send once, retry oldest, random eligible retry, and retry oldest with a receiver-side key. The evaluator alone sees effects. Keys atomically accompany effects, can expire or be reset, and cost twice as many credits per attempt. Receipt loss also applies to suppressed repeats.

`results.json` identifies 640 worlds / 2,560 policy outcomes over ten settings and seeds 1–64; its recorded model hash matches the inspected model. Its README reports these default means:

| Scripted policy | Jobs delivered / 18 | Extra effects | Confirmed jobs | Credits |
|---|---:|---:|---:|---:|
| Send once | 14.016 | 0 | 8.375 | 18 |
| Retry oldest | 18 | 13.844 | 17.844 | 40.469 |
| Random retry | 18 | 14.172 | 17.844 | 40.906 |
| Retry + key | 17.328 | 0 | 13.797 | 59.969 |

Eight-tick retention permits a mean 5.281 extra keyed effects; a 24-credit ceiling reduces keyed delivery to 9.5 jobs versus 15.984 for oldest retry. A clean channel still duplicates under an impatient timeout because messages can be slow. These are conditional simulator results with programmed policies. They establish neither LLM behavior nor production exactly-once safety. No model has demonstrated an understanding of ambiguity here.

## Carry forward, simplify, and correct

The antecedent's four jobs, ten decisions, payment/notification framings, 20% request loss, 0%/50% receipt loss and three toolkits are a good small environment. Keep these, with all effects strictly simulated. Remove delays, expiry and resets for this first real-agent study. Charge every send or status query one decision, including a suppressed repeat. Thus this version tests tool availability and agent behavior under equal decision opportunities; it does not test the toy's price/retention tradeoff. Keyed safety remains an assumption about the receiver.

Correct four issues in the old draft:

1. Ten seeds give only 20 paired main-condition scenarios/model. Use 50 seeds × two framings: 100 pairs and 200 compared episodes/model for keyed versus plain.
2. Zero receipt loss still leaves 20% request loss. Retrying can be necessary in this control; it is not a no-failure world.
3. A required key would partly force the behavior being measured. Offer an optional key and leave null legal, so omission and exact reuse are observable. Never insert a key on the agent's behalf.
4. Duplicate reduction alone rewards inaction. Require completion non-inferiority and failure-sensitive scoring. Reports may explicitly abstain, but abstention must count as a miss in the co-primary reporting test.

The old under-USD10 frontier estimate used short archived judgments rather than growing interactive transcripts. It cannot be inherited as a measured budget. Omit a new GPT arm, use a small fixed Claude replication, and measure the actual prompt envelope before any dispatch.

## Reusable structure and tooling

Read the siblings' surveys, protocols, question logs and relevant implementation excerpts. Reuse methods later by copying narrowly into this project, never importing a collector for survey work or changing sibling evidence.

| Reuse source | What it contributes | Required adaptation |
|---|---|---|
| `../work-or-proof/PROTOCOL.md`, survey and questions | Exposure statement, paired units, failure denominators, honest negative-result acceptance, fresh-clone rebuild | New trajectories and actor decisions rather than replay of saved judgments |
| `../signal-or-silence/sos_collect.py` | Serial collection, append-only starts/receipts, reservation ledger, uncertain-start handling, identity and push gates | Interactive bounded transcript, per-episode reservation, strict actor/report schemas |
| `../signal-or-silence/sos_d1.py`, `DEVIATIONS.md` | Exact UTF-8 measurement; system + hidden CLI allowance; margins; reserve before dispatch; stop on overrun | Bound every reachable transcript, not merely the initial task or an unrelated historical maximum |
| `../signal-or-silence/sos_stats.py` | Paired seed-block bootstrap with sampled-block multiplicity | Resample 50 world seeds, retaining both framings and all toolkits |
| `../signal-or-silence/evidence/Honest_Agent/v0.3.1/providers_api.py` | Ollama request semantics and isolated, tools-disabled `ClaudeCLI` transport | Do not instantiate at import; validate schema support and usage limits before future paid calls |

SoS D1 records a stop after 1,429 accounted input tokens exceeded a 1,282-token reservation. Its historical hidden CLI input maximum was 826 tokens; D1 added system bytes and per-request visible bytes with a 10% rounded margin. This is empirical overhead, not a guaranteed bound for a new CLI version. SoS's post-analysis state also records Claude technical parsing failures and unmet validity acceptance. Finishing collection did not make those replies valid. This draft therefore requires structured frontier output and strict independent validation, rather than accepting prose around a recoverable JSON substring.

The known local endpoint is `http://127.0.0.1:11435`. Model tags/digests and generation settings come from the inspected sibling evidence. Present runtime readiness, available capacity, current Claude schema/output-limit support and current prices are **UNKNOWN**; no endpoint, CLI or authentication was probed. Do not start or reconfigure a server, pull models, read credentials, or treat historical metadata as current readiness.

## Proposed study and handoff

[PROTOCOL.md](PROTOCOL.md) proposes 1,800 local episodes across three pinned models (at most 19,800 generation requests), then 24 fixed descriptive frontier episodes (at most 264 requests). Qwen 7B is the preselected primary actor; Llama 8B replicates and Qwen 1.5B is a reference. A tiny frontier arm cannot establish a family superiority claim.

Planning target: local model-call USD0; frontier roughly USD3–8 as a forecast, bounded by a project-local USD12 dispatch envelope including a USD1 planning reserve. Protocol Appendix A measures 132 draft prompt envelopes, producing USD6.322176 in conditional reservations / USD7.322176 including reserve at historical rates. The programme's operational USD39 and absolute USD40 limits remain backstops on cumulative spend. Remeasure the final reviewed prompts and verify enforceable transport limits before a later freeze; no current paid-dispatch feasibility is certified. Energy, hardware costs and runtime are unavailable, not zero.

The draft is ready for Claude's stage-3 review. Important review questions are completion tolerance, optional-key semantics, conservative failure scoring, strict frontier schema feasibility, and measured worst-transcript cost. This handoff neither claims `AGREED` nor starts that review. Open research questions are in [QUESTIONS.md](QUESTIONS.md).
