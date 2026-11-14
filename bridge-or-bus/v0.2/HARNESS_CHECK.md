# R2 harness incident disclosure

**The v0.2-r1 collection is VOID-HARNESS, separate from the v0.1 check below.**
All 1,200 r1 local episodes (400 per model) ended before any accepted action
because incomplete decoder branches allowed partial objects. This invalidates
r1 scientific interpretation without weakening strict validation. Every byte is
retained; see evidence/r2/void-r1.json and preservation.json. R2 fixes and tests
all schema branches and writes only collection-r2/. The saved-byte v0.1 findings
below remain historical evidence and do not validate the broken r1 grammar.

# Saved-byte harness check · 11 November 2026

Independent replay of all 1,200 local v0.1 terminal episodes found **zero legal
replies falsely rejected**, among **953 rejected action replies**. No validator
fix, scoring deviation or replacement inference is justified by this check.

| Actor / recorded rejection | Rejected | Actually legal |
|---|---:|---:|
| Qwen 7B `mass_g` | 88 | 0 |
| Qwen 7B cross-field legality / unavailable operation | 311 | 0 |
| Qwen 1.5B missing/extra keys | 380 | 0 |
| Qwen 1.5B `grams` | 12 | 0 |
| Qwen 1.5B duplicate `op` | 4 | 0 |
| Qwen 1.5B cross-field legality | 4 | 0 |
| Llama missing/extra keys | 150 | 0 |
| Llama `target` | 4 | 0 |
| Total | 953 | 0 |

A separate Qwen 7B preflight failure has **no saved model reply**. It remains the
original retained technical failure, never a legal/illegal action judgment.
There are 3,066 saved replies: 2,820 action replies (1,867 accepted, 953 rejected)
and 246 valid final reports. All recorded accepted actions and receipts match
independent replay. Every local episode has zero correct accepted submissions.

All 88 `mass_g` rejections have a non-integer value, e.g. `123.45`. Each assigned
world has 22; only eight occur after a successful lookup, and two of those are
rename episodes. The field name is legal for conversion after rename; its value
must still be a JSON integer, and unused lookup fields must be null. The 311
cross-field rejections contain illegal combinations, e.g. lookup with a nonnull
`mass_g` or `revision`. Of these, 128 occur after successful lookup. World state
cannot make such combinations conform to the frozen six-field contract.

`audit_v01.py` has its own strict JSON parser, action validator and transition
reducer. It imports neither the production validator nor World. It reads each
original raw reply, checks its saved SHA-256 and envelope, reconstructs the
ordered world state, verifies the exact prior history/remaining allowance in
the saved request, and compares every receipt/terminal state. Literal description
strings are read as data from the original source. `evidence/v01-replay.json`
records counts, every rejected call, state, hashes, and per-cell v0.1 outcomes.
`fixtures/v01-rejected-replies.json` preserves all 953 raw rejected envelopes and
their preceding events for portable regression tests.

The original v0.1 saved-byte scores stand. The preflight failure is retained
under its existing disposition; no episode already started is rerun. Any later
verified false rejection would require a named deviation and independent replay
of saved bytes only: accept the legal saved action, apply its effect, score only
subsequent replies actually present, leave any missing continuation/report
missing, and never invent or generate a counterfactual continuation.
