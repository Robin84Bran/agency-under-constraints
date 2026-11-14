# Method provenance

Read-only reuse, 2026-11-11. No sibling project was edited or imported at runtime.

- `../signal-or-silence/sos_d1.py`: exact UTF-8 bytes plus historical 826 hidden-input tokens; 10% margin rounded up to 64; preserve overruns rather than clipping. This project adds schema bytes, a conditional output allowance and full episode holds.
- `../signal-or-silence/{sos_collect.py,RUN.md,config/cost_basis.json}`: synchronous durable starts, immutable receipts, stop/resume accounting and separation of historical API-equivalent accounting from cash charges.
- `../work-or-proof/wop_stats.py`: seed-block bootstrap, repeated-block multiplicity, linear percentile intervals and conservative denominators. Search endpoints and joint coverage rule are implemented independently here.
- `../receipt-gap/{rg_core.py,rg_collect.py,rg_freeze.py,evidence/cli-contract.json}`: strict duplicate-key JSON rejection, structured_output-only envelope contract, schema/JSON flags, source-level CLI control discovery, whole-episode reservations and commit-bound push evidence. Candidate controls are not promoted into verified aggregate enforcement by analogy.
- `evidence/toy-model.mjs`: exact snapshot of the teaching toy, SHA-256 `b687e43d52ed57165684662bef48c982b3cedcdac69fec333d6268ac6200a5ad`. JS fixtures import only its RNG; the independent JS field formula implements this study's deliberate 8×6/scale-3/horizon-4 departure. All 100 fields are compared to Python. Baseline policies, relocation metrics and scoring are study-specific.

Prior toy/sibling exposure is recorded in the original SURVEY.md. None of those outcomes is model evidence for this prospective study.
