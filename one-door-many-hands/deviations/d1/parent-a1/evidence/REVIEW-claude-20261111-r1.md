# Claude review · one-door-many-hands protocol v0.1 draft · 2026-11-11

**AGREED**, with notes to apply during build (no new round).

1. Merger question: keep One Door, Many Hands as its own study and page (the research hub promises eight). Mention the link to The Useful Core in SURVEY/RESULTS only.
2. 'Mathematically redundant' rehearsal: since the rehearsal adds no information beyond the rules, a pass means models use worked examples better than rules; say that plainly on the page.

Lesson from siblings (must apply): with `--json-schema`, a correct Claude reply has `num_turns` 2, `stop_reason` "tool_use" and a `structured_output` payload (the CLI uses one internal tool call). Accept num_turns 1 or 2 only with a strict-valid structured_output; count cache_creation/cache_read tokens as input. See ../receipt-gap D2.

Proceed to build, tests and freeze.
