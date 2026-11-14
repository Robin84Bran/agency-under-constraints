# Current r2 operational disposition

The saved collection contains one Claude attempt with a parseable DNS error,
zero generation tokens and zero cost. It is outside the programme's four supplied
classes; its disposition is UNKNOWN pending a ruling. It is excluded from model
metrics and the historical STOP remains effective. No empirical acceptance or
new model result is claimed. `revisions/r2/saved-rebuild.json` records replay and
reconciliation of all 1,860 rows: zero new settled cost, USD0.543744 project holds,
USD6.204525 exposure. r2 is an offline harness repair only. See DEVIATIONS.md.

The following is retained historical pre-collection r1 status.

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
