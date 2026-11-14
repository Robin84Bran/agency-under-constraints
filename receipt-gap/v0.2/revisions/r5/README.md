# r5 Claude schema compatibility and non-start clearance

Claude is the delegating reviewer; Codex is the builder. The r5 ruling is:
“an API 400 rejecting the --json-schema (top-level oneOf unsupported) with zero
usage/cost is a HARNESS NON-START: nothing was generated; resend the identical
prompt with a corrected schema on resume.” No model call, push, Git command or
real attestation is part of this builder task.

`rg_claude_schema.py` emits one closed object per toolkit, all three fields
required. It has toolkit-specific op enums, job integer 1–4 or null, key null
for plain/check and a bounded ASCII key string or null for keyed. Nullable
properties use type arrays, with no top-level oneOf/anyOf/allOf. Reports retain
their original schema. Provider compilation remains UNKNOWN until a future
scored call; no live pilot was run.

The Claude provider action schema is a superset of the local schema only in
cross-field combinations: send/status with a null job, finish with a non-null
job, and keyed finish with a non-null key. The unchanged strict validator rejects
these as model-output failures under the original episode-only rule; they are
never repaired or retried. Every local legal action remains provider-legal.
The test enumerates all job values 1–4 plus null, invalid boundary/type values,
all operations plus invalid operations, and representative valid/invalid keys.
A structural branch-domain check proves inclusion for all valid key strings,
beyond the samples. Local schemas, local data, prompts, report schema, schedule,
world, scoring, strict validator and reservations are unchanged. The smaller
provider schema fits the original conservative bounds for every toolkit,
framing, phase and history depth; old sizing bytes are retained as historical
reservation evidence. provider-schemas.json records the current provider objects.

The exact saved 400 wrapper is recognized before decode with strict zero-token,
zero-cost, empty-modelUsage and no-output/activity checks. Unrelated 400s, positive
usage/cost, missing metadata and mixed replies do not qualify. The historical
r4 classification and clearance remain UNKNOWN in their original records;
current classification is HARNESS NON-START. Pending non-starts are operational
events excluded from model metrics.

After freeze-r5.json is sealed, collection/clearance-r5.json records PASS and
cleared true, binds STOP.json, STOP-r3.json, the saved raw/start and both original
and corrected requests. The new resumes/r5 overlay copies both original dispatches
and preserves the rejected request; only the request schema changes. Pauses bind
the rejected request, and verification permits precisely that schema-only
transition. Original r3 files, terminal, stops, clearances and all parent freezes
are retained. The existing zero settlement receives one append-only
recognize-nonstart event with no monetary change. Reservation restoration happens
only when dispatch resumes, retaining accounting and time holds. A fresh r5 push
and attestation remain required for future collection. The new STOP-r5 gate
cannot clear an unrelated STOP-r2 or a new failure.

preservation.json hashes all 90,078 pre-r5 collection files and snapshots all
three journal prefixes; originals/ retains every changed parent input. Five
sealed parents are bound in freeze-r5.json. The saved tests exercise the actual
DNS and 400 history, idempotent clearance, an identical-prompt mocked resend,
reconciliation, new STOPs, provider gates and mocked parent attestation.
check-1.json preserves three initial integration errors (two historical r3 tests
needed their original schema projection mocked; the r5 parent list accidentally
included its own uncreated manifest). check-2.json records the corrected 145-test
pass. check-3.json passes all 146 guarded tests, adding full r5 admission and parent-push checks.

Read-only sibling inspection found top-level anyOf passed to --json-schema in
bridge-or-bus/v0.2 for both action and report. useful-core, one-door-many-hands,
portable-self/v0.2 and three-rules-one-lunch do not pass a top-level union.
Exact source references are in sibling-schema-audit.json. No sibling was changed.
Reviewer commands are at the end of RUN.md.
