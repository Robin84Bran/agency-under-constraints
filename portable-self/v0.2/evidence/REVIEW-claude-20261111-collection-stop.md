# Claude · Portable Self · local collection stopped by reviewer · 2026-11-11

**What I saw.** After 287 local episodes, 280 had ended with `invalid control` and 6 with `invalid action keys/length`. Re-reading saved raw replies: models answer the *commands* (e.g. `{"controls":["south","east","north","west"]}`) or the string `"null"` where the contract asks for control integers 1–4 or JSON null. `format:"json"` cannot prevent this. The pre-registered technical gate (≥95% whole-episode validity per arm) is unreachable, so continuing only spends the sample.

**Action.** Claude stopped the local collector (process kill between/within episodes; any partial episode stays as saved evidence, never rerun). v0.1 is reported as stopped early by the reviewer for this stated reason — an outcome-informed operational stop, disclosed as such; no v0.1 result is discarded.

**Next (v0.2).** One change, same as The Receipt Gap v0.2: exact JSON Schema as constrained decoding for every actor (Ollama `format:<schema>` with controls = array of 4 items, each integer enum 1–4 or null; Claude `--json-schema` with the same schema). Prompts, worlds, seeds, scoring, thresholds and analysis unchanged; v0.1 data reported beside v0.2. Predictions re-registered before calls, disclosing v0.1 exposure.
