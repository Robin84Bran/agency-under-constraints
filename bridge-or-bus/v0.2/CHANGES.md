# R2 current change: complete decoder branches and isolated replacement

All 1,200 r1 local episodes are VOID-HARNESS (400 per local model), retained
byte-for-byte and excluded from model-behaviour analysis. R2 fixes the action
branch omission defect and explicitly closes report branches, updates only
schema-derived inputs, isolates all new evidence under collection-r2/, and
binds both parent manifests in freeze-r2.json. Historical time remains charged;
usage-limit handling and scientific semantics are unchanged. See REVISIONS.md,
DEVIATIONS.md and RUN-r2.md. The earlier change log below is historical.

# Build changes and sibling lessons

Prepared for Claude's delegated review. No original project file was edited.

The original core, world arithmetic/semantics, prompts, analysis, seed-block
bootstrap, baselines and cross-language toy fixtures are reused unchanged.
`bob_validation.py`, `bob_collect.py` and `bob_audit.py` retain D3's distinction
between model-content errors, local transport failures and fatal integrity or
accounting failures. The isolated package replaces historical D1/D2/D3 migration
and freeze machinery with a v0.2 source-bound freeze/attestation implementation;
it does not apply an old version's resume exception to the new study.

Scientific change: `config/action-schema.json` adds operation-specific shapes;
all actors receive it as constrained decoding. Ollama `format` is the actual
phase schema object, never its serialized JSON string or `"json"`. Reports use
the frozen report schema. All world-dependent argument choices and describe
availability remain with the harness, as specified in PROTOCOL.md. Identical
schema bytes across arms prevent an oracle contract refresh.

Retained/applied engineering lessons from Bridge D1/D2/D3, The Receipt Gap v0.2,
Portable Self v0.2 and Signal or Silence v0.2:

- Bind real template/system metadata to pinned manifests and content-addressed
  layers, allowing absent system only when the pinned system is empty. Require
  Ollama runtime version 0.33.3; include schema bytes in context allowance (maximum 7,674 / 8,192),
  save actual context and full generation bytes on
  a subsequent runtime failure. No server/store changes or model substitution.
- Treat malformed/illegal model payloads as episode-local failures; save raw
  evidence, make no repair/report retry, continue the next frozen episode.
  Incomplete/unreadable local metadata is transport failure; restart reconstructs
  the three-failure pause. Unknown identity/context, accounting and harness
  failures remain fatal. A pause has no automatic override.
- Accept the supplied real CLI metadata: two integer envelope turns only with
  tool_use, correct object structured_output, all-zero nested subagent telemetry.
  Any positive nested tool/subagent counter, queued work, permission denial or
  safety stop is fatal. Reject its sibling payload under this study's contract.
  Preserve usage when only payload content has duplicates/nonfinite data.
- Count ordinary/cache-creation/cache-read input once; output includes thinking.
  Settle the greater of aggregate CLI dollars and conservative API-equivalent
  basis. Missing accounting retains the full unresolved hold. Full measured
  overrun is retained and stops admission. Empirical output bounds stay labeled.
- Carry frozen prior spent and unresolved exposure into the append-only ledger,
  including the verified zero in this project; never reset the programme budget.
  Reserve all possible episode calls before start; no resend of uncertain starts.
  Carry the original local active-time charge as well as persistent crash
  holds and resource stops across versions/resumes.
- Freeze source/fixtures/tests before inference, bind the new freeze and exact
  pushed bytes using genuine repository activity-API push evidence, and reject
  historical receipts. Attestation implementation contains future read-only Git
  checks; **none was executed in this task**. Offline tests mock live providers.
- Disclose v0.1 exposure, retain its failed technical outcome beside v0.2, keep
  abstention-as-miss denominators, and stop after this one follow-up version.

Schema size changes the byte-based reservations. Fixture regeneration and bound
checks update only v0.2 artifacts. No original source, collection, ledger, freeze,
protocol or project state was rewritten. No bug-fix deviation was opened because
independent replay found zero legal rejections. HARNESS_CHECK.md explains scoring
from saved bytes if future evidence ever establishes a genuine false rejection.

Pre-push revision r1 (Claude reviewer delegation): pure Claude usage-limit
refusals with proven zero usage/cost now pause as definite non-starts and resume
only that request after reset. Prior calls/history, scientific fixtures and
original freeze bytes are retained. See REVISIONS.md, DEVIATIONS.md and the
prefix-verified no-op clearance; no empirical evidence required re-disposition.


## R3

Claude now uses separate object-root action/report schemas; local schemas, strict
validators and all r2 local data stay unchanged. Cross-field legality remains in
the strict validator. R3 binds all parents and preserves the r2 collection while
requiring its own post-freeze push receipt for Claude-only collection. See
RUN-r3.md, tests/test_schema_r3.py and evidence/r3/ for compatibility proof,
preservation, offline checks and the read-only sibling audit.
