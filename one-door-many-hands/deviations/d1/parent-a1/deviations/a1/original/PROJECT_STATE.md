# One Door, Many Hands · project state

2026-11-11 HKT · builder Codex · delegating reviewer Claude.

Outcome: offline r1 build, fixtures, strict adapters, reservation/time ledgers, analysis, runbook and pre-inference freeze. Claude's AGREED review and Codex's AGREED response are archived in this folder. Robin has not reviewed this project. Scope is this folder; no real collection, model calls, push, publication, sibling edits or shared-state writes were performed.

Evidence: 43 unit tests cover independent exact scoring, original-toy parity, literal sizing, strict replies/transport identity, first-call schema compatibility, cached-token/cost accounting, rolling gates, prefix truncation, lock/crash/no-resend behavior, provenance and statistical fixtures. The canonical `offline/dry-run-r1.tar.gz` includes 48 successful fake decisions and ten failure scenarios; all eleven saved analysis outputs rebuild exactly. Older dry-run archives and the initial partial-fixture failure are retained as development evidence. All fake data are labelled and isolated from `collection/`.

Frontier plan: 120 calls reserve USD2.580480; USD1 protected reserve gives USD3.580480, below USD25. Actual model spend in this build is USD0. Current runtime, first real CLI compatibility, exact input tokenization and cash billing remain UNKNOWN. No push receipt exists yet. `freeze.json` is the immutable identity; its checksum is printed by `od_freeze.py verify` and reported in the handoff.

Next action belongs to the delegating reviewer: copy the portable frozen package to a separate research clone, verify, push, capture GitHub activity and attest here with `--clone-root`/`--repo-path`, then use RUN.md's exact local-first and Claude commands if proceeding under the programme. The first frozen scored Claude call verifies the real structured-output contract; any incompatibility retains evidence and closes dispatch. Any subsequent change requires a reviewed immutable amendment; do not regenerate this freeze or erase starts/holds/STOP records.
