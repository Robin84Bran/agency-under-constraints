# v0.2 pre-push revision r1

2026-11-11 HKT. Claude is the delegating reviewer. This is a harness-only
programme decision relayed by Claude; no approval from Robin is asserted.
The original v0.2 has not been pushed or called. Its `freeze.json` is preserved
at SHA-256 `eda67ccd5bbb5ce828e109b7ff1262ca73f16ebad68e74a2db8785ddb4825440`.

The subscription's usage-limit refusal occurs before generation. Exactly verified
429 refusals with zero input/output/cache tokens, zero cost and `is_error: true`
are definite non-starts. Save the raw envelope, settle zero, pause durably and
exit cleanly. The next collect after the stated reset resends the same request
at the same position, preserving all prior history without resending prior calls.
Every other failure retains the frozen handling. No scientific method, prompt,
schema, sample, effect, scoring rule or acceptance threshold changes.

Implementation: `rg_usage_limit.py` checks strict refusal evidence and reset time;
`rg_collect.py` adds create-once dispatch records, zero settlements, validated
reservation restores and deterministic prior-history replay. `rg_analysis.py`
validates dispatch/refusal provenance and reports refusals as operational events.
Pending paused episodes remain UNKNOWN and are withheld from model metrics until
completed. `rg_freeze.py` and `rg.py` accept `--freeze freeze-r1.json`; push
attestation checks the new manifest, parent freeze and all original witnesses.
The revision inventory binds every input and enumerates every changed parent
file. `revisions/r1/originals/` preserves their exact pre-revision bytes.

Evidence: offline fixtures include a strict zero-usage 429 and the existing
portable real valid Claude envelope. The latter exactly matches the supplied
`<SCRATCH>/orchestra/real-claude-envelope.json`
(SHA-256 `a4e9f03ce0cd4cbde843924c06880082baaee6e58597fcad0f970022a9c6eb2c`).
Tests cover first-call/mid-episode/report/repeated pauses, identical resends,
no earlier resends, reset blocking, ambiguous errors, interrupted dispatches,
tampering, independent accounting and revised push provenance. The supplied real
envelope remains accepted by collector and independent analysis.

`revisions/r1/clearance.json` records the before-dispatch inspection: no STOP,
no calls and no previously scored refusal in v0.2. Both ledgers match their
preserved byte prefixes. No clearance action or re-disposition was necessary;
no evidence or ledger was rewritten. All v0.1 artifacts and holds are unchanged.
No model calls, pushes, Git commands or actual attestations were made.
