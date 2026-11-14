# Useful Core · D1 handoff · 2026-11-11

Outcome: implemented Claude's reviewer-delegated, folder-local post-push D1 before
any Claude study call. Exact zero-usage 429 usage-limit refusals are durable
operational non-starts, settle cost at zero, exit cleanly paused and resume at the
same saved request after reset. Mid-episode prior history remains unchanged.
Other errors, nonzero usage and ambiguous starts retain the frozen handling.

Authority: Claude is the delegating reviewer agent. This implementation includes
local code/tests/docs/evidence/freeze only. No model calls, network requests,
pushes, Git operations, production D1 attestation or collection by this builder.

Observed boundary: saved A1 push at 2026-11-11T10:58:10Z, commit
6f40319a81f475d314dc7992891c9e28cfa56844. All 900 local episodes have retained
terminal records. No Claude starts, usage-limit refusals or STOP files existed;
no clearance or historical re-disposition was needed. The pre-D1 inventory pins
37,473 existing collection files; journal pins allow verified append-only growth.

Lineage: original freeze.json SHA-256
fc497643b1e72f1e928ab8a36dc74d72bc2b82d6a70239c1e18868924a854d51;
freeze-a1.json SHA-256
746b525bab8dc67fdb695958a3df071c005f72bef14950274b637925817eba82.
New freeze-d1.json binds both, exact archived A1 inputs and the collection baseline.
Scientific inputs, scoring and statistics stay fixed. A1 audit rebuild tests now
use retained A1 sources; original A1 audit/test evidence remains unchanged.

Verification: see deviations/d1/test-report-final.json and test-log-final.txt for source-bound
offline results, including supplied real-envelope metadata, exact refusal,
first/mid/report resume, repeat refusal, crash recovery, journal growth/tampering,
lineage/order, and unchanged failure accounting. Evidence checks and local replay
are retained under deviations/d1; fake results remain explicitly labelled.

Next: reviewer runs `python3 -B uc_freeze.py attest-d1`, then the exact Claude
collect command in RUN.md. No new GitHub push is required for this local deviation.
Subsequent resumes use collect alone. Unknown reset remains paused. First scheduled
Claude contract, live runtime, cash billing and empirical outcomes remain UNKNOWN.
