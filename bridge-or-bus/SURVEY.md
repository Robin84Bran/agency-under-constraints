# Bridge or Bus? · Survey

11 November 2026 (HKT). Stage 1; proposed stage 2 in [PROTOCOL.md](PROTOCOL.md). **Claude r1 AGREED with notes; offline build authorized. No inference or publication.**

## What was inspected

The main website checkout has no `public/bridge-or-bus/`. The inspected saved release is [`website/_releases/research-rebel-20261110/public/bridge-or-bus/`](../../../../00_identity_output/website/_releases/research-rebel-20261110/public/bridge-or-bus/): `README.md`, `EXPERIMENT.md`, `model.mjs`, and `results.json`. It is a source snapshot, not independently verified live-site content. Also read the programme's [loop](../semi_autonomous.md), [research conversion brief](../../../../ANTresidency/experiment_to_research.md), orchestration rule, Work or Proof's survey/protocol, Signal or Silence's survey/protocol, D1 amendment/code and v0.2 format follow-up, and Receipt Gap's protocol and [Claude r1 review](../../../../_shared/agents/reviews/receipt-gap/REVIEW-claude-20261111-r1.md).

The existing shared claim lists this folder under Codex for this survey/protocol task. Robin supplied that claim. Shared claim files are outside the authorized write boundary and were left untouched, including release; no other project was edited.

## What the toy actually shows

The toy models 160 ticks, eight services, three-service job routes, two arrivals per tick, three delivery attempts and one repair opportunity. A direct route requires current adapters for its adjacent service pairs. A shared route requires current adapters for each service plus an available hub. Schema drift invalidates affected adapters; jobs wait at most 24 ticks in a queue of 64. All four scripted policies see the same realized arrivals, versions and hub state, but no future events.

The saved batch has ten settings × 64 seeds × four policies: **640 matched worlds, 2,560 policy outcomes**. This survey recomputed delivered-job means from all saved outcome rows and checked their counts; it did not execute the simulator or its tests.

| Setting | Direct | Shared | Static | Random |
|---|---:|---:|---:|---:|
| Default | 127.234375 | 319.343750 | 15.718750 | 70.921875 |
| Stable schemas | 320 | 319.343750 | 320 | 320 |
| Rapid drift | 53.828125 | 317.437500 | 7.046875 | 20.359375 |
| Fragile hub | 127.234375 | 284.859375 | 15.718750 | 70.921875 |
| Two repairs | 308.359375 | 319.343750 | 15.718750 | 199.859375 |
| Two repeated routes | 319.687500 | 319.328125 | 20.718750 | 319.546875 |

Shared adapters reduce the repair fan-out encoded by the simulator. Stable interfaces or a small repeated route set can reverse the ordering. Shared routing also creates a common failure domain. Equal action opportunities do not establish equal engineering effort, latency or compute. There are no model decisions, real schemas, error interpretation, units or payload transformations here; these outcomes cannot establish real-agent robustness or recommend a service architecture.

Source SHA-256 snapshots:

| File | SHA-256 |
|---|---|
| `README.md` | `e5b7b89e76907be8bcf0c69f424cd9700621ee413f97b7d2354742dec7c883cd` |
| `EXPERIMENT.md` | `36ad109e1b6b75db1a2c0f1e01a6a23109deb62c048c2ed8b0ac917867b64033` |
| `model.mjs` | `0807f2ccb04d9894fca4397c4a599238f8d6f67057c42fca7bc32f650c14ebc4` |
| `results.json` | `9a9c0bdb516be796bcd56105a7cc87e92e9850f36bbb0e34c64fcb13b32c572b` |

The model hash matches the saved results' `modelSha256`. Hashes identify inspected bytes, not historical push provenance.

## The real-model question

What we tested instead, and why: this study tests access to current tool descriptions after drift as a cheaper information-access question; it does not test direct adapters against a translation bus.

**When a tool changes during a three-step job, does an optional current registry improve correct completion over descriptions supplied once, after charging registry queries against the same decision allowance?**

Use synthetic lookup → convert → submit jobs. After the first successful lookup, change a conversion argument name, the conversion result's unit, or a required submission argument; include unchanged controls. Agents receive the same initial descriptions and the same error diagnostics. Only the registry arm may request current descriptions. The harness never translates an agent's old call into a new one. Ground truth is an exact submission recorded by code, independently replayed.

This tests access to current interface information and its use under a limited action budget. It does **not** reproduce direct-versus-bus topology, adapter fan-out or hub resilience. Better registry outcomes could reflect access to useful information; they do not identify an architectural advantage or an internal reasoning mechanism. The initial descriptions explicitly warn that interfaces may change, in both arms. Error messages reveal actionable requirements in both arms, making recovery possible without the registry.

## Reuse and lessons

- **Work or Proof:** portable evidence, independent truth reconstruction, seed-block paired inference, strict separation of a failed prediction from a failed study, fresh-clone offline rebuild. Its archived judgments answer different questions and cannot substitute for new agent trajectories.
- **Signal or Silence D1:** size the actual visible prompt, system and growing history; include schema and hidden transport overhead. Its original historical input maximum failed on a longer instruction. Reuse reservation/settlement and uncertain-start handling, not an unrelated maximum as a guarantee.
- **Signal or Silence v0.2:** its protocol records 274/1,868 Claude replies with one legal object plus prose in v0.1. Outer transport JSON did not guarantee strict verdict text. Here every prompt explicitly requests only JSON, provider schemas constrain generation where supported, and an independent strict validator remains mandatory. No parser relaxation or replacement call after results.
- **Receipt Gap review:** include an informative fixed frontier cohort: **80 episodes, including 60 drift episodes**, rather than a handful of examples; keep its total dispatch envelope ≤USD25. Verify `--json-schema` before collector work.

An offline inspection of the configured Claude binary returned **Claude Code 2.1.312**, exit 0 for `--version` and `--help`. Help advertises `--json-schema <schema>` for print mode and `--output-format json` as a single JSON result. It also advertises `--max-budget-usd` for API calls. Read-only embedded implementation inspection found an optional `structured_output` result field and a structured-output tool returning that field with `endsTurn:true`. This verifies option availability and supports the candidate field name, not the complete transport path. Payload type, compatibility with tool-disabled invocation, internal schema-repair generations, and protection against output/cost overrun remain **UNKNOWN**. No CLI print request or model call was made. The inherited ClaudeCLI does not enforce its configured `max_tokens`; neither schema nor a budget flag is assumed to fix that.

Local models come first at `127.0.0.1:11435`, with inherited full digests. No local metadata endpoint or generation endpoint was contacted; present availability is UNKNOWN. The draft proposes 1,200 local episodes and 80 frontier episodes, with a finite call/time cap and no inference retries. Actual model behavior and expected runtime remain unknown. Conditional budget sizing and unresolved transport gates are explicit in the protocol; resolving them belongs to later review/build authority.

## Present handoff

The deliverables are this survey, v0.1 draft protocol, and [QUESTIONS.md](QUESTIONS.md). All real-agent predictions remain untested. Stop after stages 1–2: Claude review/agreement, implementation, freeze/push, inference and delivery have not been performed or authorized by this task.


2026-11-11 build update: the historical survey handoff above is preserved as context. Claude r1 AGREED; Robin subsequently authorized offline implementation/tests/freeze. Transport and cost-enforcement readiness remain UNKNOWN, and no model was called. See protocol v0.2 and RUN.md.
