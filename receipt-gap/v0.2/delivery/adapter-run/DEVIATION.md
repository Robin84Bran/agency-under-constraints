# Disclosed analysis-adapter deviation · 12 November 2026 HKT

Claude, the delegating reviewer, permitted the prepared version/scope adapter subject to unchanged calculations, v0.1 byte identity, a single canonical v0.2 analysis and a fresh-clone-style rebuild. This records Claude’s ruling; it is not a statement of Robin approval. No new scientific registration, collection, model call, push or Git operation is involved.

The original frozen entry point ran once and failed before scoring because its saved-push allowlist stops at r3. Its original logs remain at delivery/frozen-analysis.*. The adapted canonical invocation ran once after the v0.1 test passed; see execution.json.

The adapter selects the package root, imports its native frozen loader, and calls its unchanged main function. For v0.2 it requires freeze-r5.json and checks its bindings to analysis, statistics, core and schedule bytes. Only the r5 receipt provenance allowlist is adapted, with the same repository, event, hash, commit, branch and time checks; earlier receipts retain the original checker. The native r5 loader selects the local cohort and the completed Claude cohort under r1–r5, preserving archived non-starts. No rows, endpoints, bootstrap settings, pass rules or predictions are changed. Frozen code and evidence remain intact.

Adapter SHA-256: `d00d80c1afacf5c4fdc93e6c5ff366ea7a3f6fed42aea414d4b811b0cd2188c1`.
Frozen rg_analysis.py SHA-256: `e001f0925c0ef2d11b811de0643c2f9cabe7342771d27838349485ea6ff92d69`.
Frozen rg_stats.py SHA-256: `c63177d21e32245f8ae0b4e48efddd142cfbdda30d19cdc60e0f2c87522eb9a5`.
Analysis output SHA-256: `e459557d277f177d8b5300713026055e8c11a77fe1925deb0d9ace470a94f53f`.

The regression selects the v0.1 frozen loader and reproduces its saved 78,795-byte result exactly (SHA-256 622a8bd6b887a59755c5164c9d0231e1072377d67294cdc28d1142a82343a3e9). The seven calculation functions and all eight statistics functions match v0.1 source-for-source; their hashes and eight rejected tampered receipt fields are in v01-regression/verification.json. This test uses the existing v0.1 inputs read-only, writes only under delivery/, and does not rerun collection.

Headline D/S/R/action-validity counts and denominators are byte-identical to the earlier descriptive headline.csv. Formal inference resolves RQ1 PASS, Qwen RQ4 FAIL, joint safer-and-reliably-reported false and technical acceptance false. Predictions are 6 MET, 10 FAILED, 0 UNKNOWN. Rebuild evidence is in rebuild-verification.json. Prior delivery documents and manifest are preserved under originals/; prior UNKNOWN analysis statements remain historical evidence.
