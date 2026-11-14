# v0.2 r1 operational status

No production v0.2 calls have been made. Model outcomes and empirical acceptance
remain UNKNOWN. The pre-push revision changes only usage-limit handling.

Production usage-limit refusals observed here: **0**. No earlier v0.2 refusal
was scored as a technical failure, and none needed re-disposition. Sibling
programme refusals supplied context; they are not counted as this study's data.
The zero-call inspection and ledger prefix evidence are in
`revisions/r1/clearance.json`.

After collection, `rg_analysis.py` reports `operational_events.usage_limit_refusals`
and individual zero-cost, no-output events. They never enter model behavior or
technical-failure counts. Pending interrupted episodes remain UNKNOWN and are
excluded from model metrics until resumed; their registrations are listed in
`pending_usage_limit_episodes`. No acceptance decision is made while paused.

113 guarded offline tests passed, with no network, actual Git command or real
model call. Deterministic Node parity was the only executed subprocess. The
real valid envelope and synthetic zero-usage 429 both pass their intended checks.
`revisions/r1/verification.json` contains the complete test report; intermediate
failed verification reports are retained under `validation-attempts/`.
