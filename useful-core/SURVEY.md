# The Useful Core · Survey

11 November 2026 (HKT). Stages 1–2 only. Builder: Codex; delegating reviewer: Claude. This is a draft for the Claude/Codex agreement process in [semi_autonomous.md](../semi_autonomous.md). Robin has not reviewed this project. No study model calls, implementation, freeze, push or publication have occurred in this task.

## Sources and what was checked

The research hub's local programme data identifies **The Useful Core**, W44, as a **Playable seed** in “Memory, adaptation and resilience,” asking “What stays useful when parts of a system break?” The playable page is [/intelligence/useful-core/](https://iamrobin.ai/intelligence/useful-core/), linked from [/research/](https://iamrobin.ai/research/).

The website's top-level `src/` and `public/` did not contain this title. The inspected source snapshot is `00_identity_output/website/_releases/intelligence-research-preview-20261111/`, relative to the RobinOS2 root. Read its `src/data/research-programme.json`, `src/pages/intelligence/useful-core.astro`, and `public/useful-core/{README.md,EXPERIMENT.md,model.mjs,results.json}`. These are local source observations; the live site was not fetched, so deployment parity is UNKNOWN.

Also read `ANTresidency/experiment_to_research.md`, the orchestration rules, the programme's semi-autonomous loop, and the five requested sibling projects' relevant surveys/protocols. Read the later Receipt Gap D1, Bridge or Bus D1/D2 and Three Rules D1/D2 amendments rather than carrying forward their superseded transport gates or incorrect attribution. Siblings were read only. Their methods and disclosed failures informed this draft; their model responses were not used as outcomes for this title.

Source hashes (SHA-256):

| Source within the website snapshot | SHA-256 |
|---|---|
| `public/useful-core/model.mjs` | `3088195827042dd696ec26e1bb052427b8bf5d20ca0f260c49a515fe1a38abf1` |
| `public/useful-core/results.json` | `46294eac5bb1e88e209bd6e84fa5807c849a74163867b4fbf26eb196dafdfee6` |
| `src/data/research-programme.json` | `39c616af61947d39b7932326032558b4933fad8a85b06afa8ffd4b20c33447e3` |

## What the toy actually shows

Eight modules comprise three actuators, two sensors, one link and two power cells. Full work requires all eight and is worth 12 units. Reduced work requires two actuators, one sensor and one power cell for 6. Core work requires an actuator and a power cell for 2. Every policy receives the same current health trace and one decision per tick; none sees future failures. After tick zero, repairs precede correlated shocks, then independent failures. Choices cannot affect those draws.

The full-job policy always attempts full work. The graceful policy deterministically selects the highest feasible tier, but earns only 10/5/2 units and pays a switching charge. Core-only always attempts core; random chooses a tier from separate seeded draws. There is no model deciding, learning, reporting completion or concealing failure.

The archive has ten settings × 64 seeds × four policies: **640 matched worlds and 2,560 policy outcomes**. A read-only standard-library calculation checked all seed/policy cells and recomputed useful-work, productive-tick, failed-attempt and switching means from saved outcome rows. The model hash matches the archive. The simulator and its test suite were not executed; this is not a full reproduction.

| Setting | Full job | Graceful shed | Core only | Random |
|---|---:|---:|---:|---:|
| Calm | 1440.000 | 1200.000 | 240.000 | 812.125 |
| Default | 128.438 | 454.906 | 203.438 | 254.875 |
| Harsh | 24.000 | 127.797 | 86.031 | 64.500 |
| No repair | 49.125 | 119.453 | 53.281 | 66.281 |
| Fast repair | 408.938 | 693.094 | 233.031 | 432.625 |

In default worlds the full-job policy produces on 10.703 of 120 ticks; graceful and core-only both produce on 101.719. Graceful earns more because it uses larger feasible tiers. Free switching raises its default work from 454.906 to 470; switch cost three lowers it to 430.484. The calm-world reversal comes from an explicitly assigned architecture penalty, not an observed engineering cost.

These results establish a teaching mechanism: preserve useful partial capability under the encoded dependencies, while retaining its cost. They establish no real-agent robustness, honesty, production reliability or intrinsic advantage of modular architecture.

## The real-model question

**When a tool fails after work has begun, does explicitly prioritizing a useful fallback improve the value an agent actually delivers, and does that advantage survive counting inaccurate or abstained completion reports as misses?**

[PROTOCOL.md](PROTOCOL.md) proposes a small synthetic bulletin task with four dependent tools and three deliverable tiers. The model must obtain real simulator receipts and explicitly commit a deliverable. A label alone earns no work. A separate report is checked against the committed ledger. The intervention changes the goal framing, with identical tools, fallback permissions, tier values and action allowance in both arms. Early and late outages have known, different feasible ceilings; a calm control shows whether fallback framing sacrifices full completion unnecessarily.

This is an instruction-framing and tool-orchestration experiment, not a direct replication of the toy's architecture comparison. There is no architecture tax, switching-cost model, adaptive learner, open-ended bulletin-quality judge or population of agents. No real tool, account, publication or service is affected. Real-model decisions replace the toy's perfect feasibility selector; code remains the ground-truth scorer.

The research brief suggested folding One Door into Useful Core. The newer programme loop and this delegation commission separate Wave 3 projects. This v0.1 keeps the useful-partial-completion question here; carrier capacity, queues and multi-agent resilience remain outside scope. Any future merger needs an explicit editorial/design decision, not duplicate evidence presented as two independent studies.

## Proposed scope and readiness

Three pinned local models each receive 50 seeds × three worlds × two framings: **900 local episodes** in total, at most 6,300 model requests. Qwen 7B's primary outage contrast contains **100 matched scenario pairs / 200 episodes**, clustered in 50 seed blocks. Llama replicates; Qwen 1.5B is a reference. Then a fixed frontier arm supplies **60 episodes across ten seed blocks**, at most 420 requests. No frontier outcome can replace the local primary.

Planning: local model-call USD0; frontier approximately USD10–18 API-equivalent. Protocol Appendix B's read-only draft-byte sizing gives **USD10.083840 empirical reservations**, or **USD12.083840 including USD2 reserve**, using historical allowances/rates. Final reviewed inputs must be remeasured later. Frontier admission stays within USD25 including that protected reserve, with a cumulative project USD39 stop and USD40 programme ceiling. Historical token allowances are estimates, not hard provider limits. Actual usage/cost settles each call; missing accounting or a reservation overrun stops further dispatch. Runtime, current endpoint capacity, live CLI compatibility and current cash billing remain UNKNOWN.

The next step is Claude's stage-3 protocol review. No scientific AGREED or ACCEPTED decision is claimed. [QUESTIONS.md](QUESTIONS.md) separates review decisions from follow-up hypotheses. This task stops at the three draft documents.
