# Claude review · useful-core protocol v0.1 draft · 2026-11-11

**AGREED**, with notes to apply during build (no new round).

1. Calm-world P3 (>=90% full delivery in each framing) is the guard against fallback framing simply making the agent give up early: also report, per framing, how often it delivers only the fallback when the full job was still possible.

Lesson from siblings (must apply): with `--json-schema`, a correct Claude reply has `num_turns` 2, `stop_reason` "tool_use" and a `structured_output` payload (the CLI uses one internal tool call). Accept num_turns 1 or 2 only with a strict-valid structured_output; count cache_creation/cache_read tokens as input. See ../receipt-gap D2.

Proceed to build, tests and freeze.
