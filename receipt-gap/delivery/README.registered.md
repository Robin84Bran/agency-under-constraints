# The Receipt Gap

An agreed, pre-inference study of how agents retry simulated irreversible actions when confirmations disappear. Does an optional idempotency key reduce duplicates while preserving exactly-once completion? Can the same agent correctly report what happened?

Protocol r2 schedules 1,800 local and 60 descriptive Claude episodes. Qwen 7B is the fixed primary; Llama is a fixed replication and Qwen 1.5B a reference. No real payments, messages or external effects occur. No real-agent results exist at this handoff.

- [PROTOCOL.md](PROTOCOL.md): scientific rules, predictions, strict JSON contract and limits.
- [RUN.md](RUN.md): offline checks, push attestation, local-first collection, recovery and fresh-clone rebuild.
- `rg_core.py`: toy-compatible draws, receiver and public prompts.
- `rg_collect.py`: isolated adapters, append-only episode/call evidence, holds and time controls.
- `rg_analysis.py`: independent replay, all planned denominators, seed-block intervals and cost reconciliation.
- `config/`: explicit frozen order, literals, schemas and measured reservation envelopes.
- `fixtures/`, `tests/`, `offline/`: offline verification only; fake replies are never empirical results.
- `freeze.json`: source/data SHA-256 manifest, created once before inference.

Codex built and tested offline. Claude owns push and later collection. Runtime readiness and real transport success remain UNKNOWN until the frozen checks run. The first real call is scored, saved and never replaced. Model-call spend to date is zero; future frontier reservations total USD15.805440 plus USD1 protected reserve, under the USD25 envelope and USD39 operational stop.
