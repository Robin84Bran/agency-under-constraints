# Offline verification history

All activity used fake transports or metadata-only CLI inspection. No model generation, push or collection occurred.

- First 36-test pass attempt: two test assertions failed. The leak test incorrectly rejected the public instruction word “artifact”; it now checks forbidden hidden fields/values. The interrupted-time test expected exactly 430 seconds despite deliberately charged between-call overhead; it now requires at least the full timeout. Both were fixture/assertion errors, not observed world leakage or under-accounting.
- 43 tests then passed, including provenance using mocked Git, missing paid usage, full overrun settlement, strict output, identity and no-resend paths.
- Failure-path review found a real analysis gap for interrupted paid calls without terminal records. Analysis now retains unknown factual utility and the original hold, reconciles known saved settlements, and does not import providers. Raw-envelope classification also rejects invented failure flags. Added crash and raw-byte checks.
- Expanded 52-test attempt: one bootstrap assertion used exact binary float equality for 1/3, and one synthetic crash fixture put its copied start before its newly created reservation. The assertion now uses a tight tolerance; the simulated start now follows its reservation. The production prior-reservation check correctly rejected the bad fixture.
- Malformed nonobject-envelope testing found a real list `.get()` assumption in offline audit metadata extraction. The runner saves the invalid raw bytes and fails closed; analysis now handles the same invalid envelope and retains unknown usage.
- Final suite: 57 tests pass. Scope includes transport/identity/first-call failures, no-resend recovery, three-failure cohort pause, full-output/input failure distinctions, calm fallback-only reporting, joint-pass/coverage gates, seed-block multiplicity, reservation prefixes/concurrency, server activity provenance and portable independent analysis.

The final test log/report and source digests are frozen under `evidence/`. The first dry-run outputs remain intact; `offline/analysis-final.json` is the current independent rebuild. Failed fixtures were corrected before freeze, with no model-response exposure.
