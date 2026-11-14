# D1 operational status

The saved collection contains all 3,600 local terminals and no Claude attempt at
the D1 baseline. Claude results are UNKNOWN. No model calls were made for D1.

Usage-limit refusals in this project's saved baseline: **0**. No saved refusal
was previously scored as a transport/technical failure, so no real
re-disposition or STOP clearance was needed. Synthetic tests cover both.

Future analysis reports refusals separately under
`ledger.operational_events.usage_limit_refusals` with saved evidence and reset
times. A refusal is an operational event and a definite non-start; it contributes
no model technical failure or model behaviour observation. Its assigned episode
remains pending until a generated reply exists. The fixed denominator and all
scientific scoring rules are unchanged. The supplied real envelope is a sibling
fixture, not an observation from this project.
