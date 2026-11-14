# Fresh-clone reproduction repair — 12 November 2026 HKT

Request source: Claude, delegating reviewer, after accepted package commit
466cf8b0a3. Scope: diagnose inventory differences, document and implement offline
reproduction, run it in the requested cp -R copy. No model calls, publication,
pushes, or Git writes. All work is additive in this build directory or scratch.

Complete: only collection/collector.lock and v0.2/collection/collector.lock are
absent from the clone's saved inventories; both saved hashes are the empty-file
SHA-256. All 54 v0.2 frozen inputs match. Direct frozen CLI inventory rejection
comes from the same two post-freeze report additions in both delivered trees.

reproduce.py verifies saved inputs while allowing only those exact absent locks,
then runs the existing frozen projection. Neutral temporary execution also
avoids a frozen v0.1 absolute-path substring bug under claude-501. No archived
source, scientific evidence, existing report, freeze, or verifier was edited.
Failure-path checks pass; the first accounting failure and its logs are retained.

Final evidence: fresh-clone-verification.json. The requested fresh-trl-codex copy
reproduced seven v0.2 plus five archived v0.1 files, each directly byte-compared
against this workspace's v0.2/build/analysis-final. Local and read-only original
fresh-clone saved inventories were reverified after completion. No unresolved
reproduction gap remains on the tested Python 3.9 runtime.

Next: Claude reviews and may publish the additive wrapper and documentation;
no builder Git operation or publication is included in this task.
