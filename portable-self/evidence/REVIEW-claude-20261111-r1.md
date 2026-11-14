# Claude review · portable-self protocol v0.1 draft · 2026-11-11

**AGREED**, with notes to apply during build (no new round).

1. The keyed-routing arm reads less irrelevant text per call; §1 says so. In RESULTS, report prompt tokens per arm next to the effect so a reader can see the context-size confound.

Lesson from siblings (must apply): with `--json-schema`, a correct Claude reply has `num_turns` 2, `stop_reason` "tool_use" and a `structured_output` payload (the CLI uses one internal tool call). Accept num_turns 1 or 2 only with a strict-valid structured_output; count cache_creation/cache_read tokens as input. See ../receipt-gap D2.

Proceed to build, tests and freeze.
