# The Portable Self · Survey

11 November 2026 (HKT). Stage 1. Builder: Codex; delegating reviewer: Claude. Decisions follow Claude/Codex agreement under [semi_autonomous.md](../semi_autonomous.md). This project has not been reviewed by Robin. Stage 2 is a **v0.1 draft**, not an agreement, freeze or executed study.

## Sources inspected

The website root does not contain `public/portable-self/` or `src/data/research-programme.json`. The following release snapshots supply the inputs; their presence is not verification of the current live deployment.

- Toy: [README](../../../../00_identity_output/website/_releases/research-home-20261110/public/portable-self/README.md), [EXPERIMENT](../../../../00_identity_output/website/_releases/research-home-20261110/public/portable-self/EXPERIMENT.md), [model](../../../../00_identity_output/website/_releases/research-home-20261110/public/portable-self/model.mjs), saved `results.json`, and `src/pages/intelligence/portable-self.astro` in that same release.
- Programme: [research-programme.json](../../../../00_identity_output/website/_releases/intelligence-research-preview-20261111/src/data/research-programme.json). Entry `portable-self`: week `2026-W42`, title “The Portable Self”, question “Which habits should travel with an agent into a different body?”, direction `memory`, maturity `Playable seed`. The playable URL is `https://iamrobin.ai/intelligence/portable-self/`; `/research/` is the programme hub.
- Research intent: [experiment_to_research.md](../../../../ANTresidency/experiment_to_research.md), especially §8; orchestration and the current semi-autonomous programme supersede its older individual-approval workflow for this delegated draft.
- Read-only methods: `../work-or-proof/{SURVEY,PROTOCOL,QUESTIONS}.md`, `../signal-or-silence/PROTOCOL.md`, `../receipt-gap/{PROTOCOL,RUN,PROJECT_STATE}.md` and `rg_freeze.py`, `../bridge-or-bus/{PROTOCOL,QUESTIONS,PROJECT_STATE-d2}.md` and D2 identity evidence/code, `../three-rules-one-lunch/{PROTOCOL,QUESTIONS,PROJECT_STATE-d2}.md` and D2/budget code. Their results are antecedents, never portable-self observations.

Source SHA-256 values checked by reading bytes:

| Snapshot file | SHA-256 |
|---|---|
| Toy README | `7443759141c707e2ec58a5a7fad61d628f5514d5e5a34a157d3f904606196326` |
| Toy EXPERIMENT | `f39e12027c485cf05a6a769f53584a0c65fd7abf4502bf8dc17450cbed0f2e52` |
| Toy model.mjs | `a6b2ac449690fd155468bbd5ff5ee4ef7a027a296b70cb79dbfd3a68de62122c` |
| Toy results.json | `48b918ab4328fc822032a8161f580e3b48a93e427fce3e4b329079ef3846090d` |
| Programme JSON | `39c616af61947d39b7932326032558b4933fad8a85b06afa8ffd4b20c33447e3` |

## What the toy establishes

A body is a hidden bijection between four physical controls and north/east/south/west. Every policy gets one action per tick, the current target, body label, advertised fingerprint and after-action feedback. Correct actions advance a recipe; four make an assembly. The adaptive policies share the same hand-written learning and bijection inference. Only retention differs: one global map, erase at handoff, or maps selected by fingerprint. Frozen-manual and seeded-random policies do not learn.

Default: 96 ticks, four recurring bodies, handoff every eight ticks, permuted controls and no drift. The archive registers ten settings × seeds 1–64 × five policies: **640 matched worlds / 3,200 policy outcomes**. Reading saved rows reproduced these means, in correct commands out of 96:

| Setting | Carry all | Blank | Keyed portable | Frozen | Random |
|---|---:|---:|---:|---:|---:|
| Default | 72.797 | 72.938 | 87.938 | 2.281 | 24.484 |
| Same mapping | 94.156 | 73.141 | 88.344 | 96.000 | 23.578 |
| Rapid handoff | 49.922 | 50.984 | 88.094 | 3.047 | 24.156 |
| One-use bodies | 72.875 | 72.406 | 72.406 | 3.813 | 24.078 |
| Fresh labels after drift | 72.875 | 72.969 | 80.125 | 3.359 | 23.938 |
| Stale labels after drift | 72.875 | 72.969 | 80.406 | 3.359 | 23.938 |

The saved `modelSha256` matches the model bytes. This survey did not execute the simulator or its tests; saved-row checks are not a full reproduction.

The important boundary is visible in the unfavorable settings. Per-body state helps when different bodies recur; identical mappings reward shared habits, and no return removes the reuse opportunity. Stale labels cause recalled errors, yet slightly higher throughput than fresh labels here because full recalibration also costs actions. Wrong actions have equal, reversible cost. These are properties of scripted controllers, not empirical LLM memory, robot safety, consciousness or personal identity.

## Real-model question and proposed translation

**Does automatic routing of model-written notes by an environment label improve correct actions when that environment returns, relative to letting the model manage a shared notebook with the same total capacity?**

Four synthetic consoles have opaque labels and four permuted controls. Each is demonstrated once with all four controls. The model writes one short note after each demonstration. After all four, each console returns and the model chooses controls for four target commands. Each invocation is stateless; only the arm's designated notes survive. Code supplies observations and moves raw text, but never writes, repairs or interprets the model's mapping notes.

Three arms: four automatically keyed note slots; four shared slots managed by the model; and notes discarded. Both persistent arms have four 96-character slots, four writes and the same complete calibration evidence. Shared memory may itself record labels and implement keyed organization. It is a capable comparator, not an instruction to overwrite one generic map. Keyed routing exposes only the matching slot, while shared routing exposes all four; report input tokens and call latency rather than claiming equal compute.

The primary world uses distinct stable mappings. Local boundary controls use identical mappings and obsolete labels after remapping. The frontier contrast includes stable and stale worlds, ten seed blocks and sixty episodes. The protocol makes complete calibration exogenous to isolate note retention/routing and keep the frontier arm feasible. Consequently it does not test active exploration, online feedback repair, firmware detection, long-term forgetting or a fresh-versus-stale versioning policy. A ceiling tie is an informative possible outcome: automatic routing may add little when a shared notebook is small and labels are explicit.

## Lessons incorporated before building

- **Study acceptance differs from a positive prediction.** Fix a primary/co-primary joint rule, all planned denominators, validity guards and complete-pair sensitivity. Preserve nulls, failures and unfavorable results.
- **Frontier structured output:** plan Claude CLI 2.1.312 with `--json-schema` and `--output-format json`; accept only object-valued `structured_output`. The first frozen scored call verifies the live contract and fails closed on mismatch. No pilot call.
- **Budget:** size this study's actual prompt/system/schema bytes, add a historical hidden-input allowance and 10% margin, reserve output empirically, settle actual usage and stop on overruns. USD25 frontier envelope, USD39 project admission stop, USD40 outer programme line. An unprovable aggregate output ceiling must not block or supposedly guarantee collection.
- **Push:** use the private repository's `/repos/Robin84Bran/research/activity` push record, not an expectation that `/events` contains PushEvents. Later attestation must distinguish the clone root/repository path from this folder, which owns `collection/push.json`.
- **Identity:** bind exact pinned manifests and template/system layers. Qwen's default system is Alibaba's text; Llama's is empty. A universal empty-system check is wrong.
- **Failure classification:** a completed `done_reason:length` reply fails its episode without stopping all collection; input truncation, identity/digest mismatch and provider-envelope/accounting integrity failures remain fatal.

The existing Codex claim was verified read-only. Only the three requested Markdown documents are created. No build, freeze, runtime probe, model call, Git change or external publication occurred. The shared claim registry is outside the project-only write boundary; Claude must release the inherited claim after handoff.
