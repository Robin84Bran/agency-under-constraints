# The Useful Core

Synthetic bulletin experiment with a Claude-reviewer-delegated D2 harness fix.
The saved boundary contains 900 local and 12 Claude terminal episodes. The latest
Claude STOP was a harness identity rejection of a parseable zero-usage ECONNRESET
API-error envelope with empty modelUsage. D2 preserves the original evidence,
records an episode transport disposition and exact STOP clearance, and advances
without retrying that episode. No model calls, network requests, pushes or Git
operations are part of this repair.

[RUN.md](RUN.md) gives exact clearance, local attestation and resume commands.
`freeze-d2.json` binds unchanged `freeze.json`, `freeze-a1.json`, `freeze-d1.json`,
archived D1 sources, all retained collection files and journal prefixes, and a
frozen disposition plan. [D2 record](deviations/d2/README.md) explains the evidence
and interpretation. Original STOP, replies, terminals and journals remain intact.
Generated errors, truncation, refusals and schema failures are episode failures;
exact zero-usage 429 limits pause for identical-request resume. Integrity and
accounting guards remain active. Frozen prompts, schemas, schedule, science and
statistics stay unchanged. Collection is incomplete; no publication claim is made.
