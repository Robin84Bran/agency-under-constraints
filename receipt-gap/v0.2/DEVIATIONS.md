# r5 provider-only schema deviation · 2026-11-12 HKT

Per Claude's reviewer ruling, the exact zero-usage/cost API 400 top-level-schema
rejection is HARNESS NON-START. Claude's per-toolkit provider schema is a superset
of the local one only in cross-field combinations; these remain enforced by the
unchanged strict validator. This removes provider cross-field constrained decoding
and is disclosed as a provider compatibility deviation. Local schemas/data,
prompts, report schema, schedule, scientific functions and reservations remain
unchanged. The same prompt resumes with a corrected schema; no generated outcome
is replaced. All old evidence/STOPs remain. Five parents bind the r5 correction;
clearance-r5 records eligibility, without dispatch. No builder model calls, pushes,
Git commands or real attestations. See revisions/r5/README.md.

Earlier entries are historical.

# v0.2 deviations

Pre-push r1 was the first harness revision. It replaces fatal handling only for
proven pre-generation subscription usage-limit refusals. This implements Claude's
programme-wide decision relayed to this builder, recorded in `REVISIONS.md`.
It makes no scientific change and does not relax handling for ambiguous starts.

Original freeze bytes and evidence are retained. The active freeze is
`freeze-r1.json`; reviewer attest and collect commands in `RUN.md` select it
explicitly. Fresh push and attestation remain prerequisites for all real calls.
No v0.2 refusal had previously been scored, and no STOP needed clearing.


## r2: saved-envelope disposition audit (2026-11-12 HKT)

Claude requested saved-byte diagnosis and harness repair. r2 preserves both parent
freezes and records the reply's classification as UNKNOWN: parseable ENOTFOUND,
zero tokens and cost, no exact 429. The programme's four classes do not cover it.
STOP clearance is recorded as false; no historical terminal, STOP or ledger is
rewritten. The revised analysis excludes this unresolved operational episode from
model metrics. A programme ruling is required before clearance or any resend.

The separate proven harness bug is fatal exit-code handling of generated error
replies. Collector and independent replay now handle generated max-token errors,
refusals and structured-output failures as episode failures; missing modelUsage on
errors is not an identity mismatch. Safety/accounting boundaries remain enforced.
`freeze-r2.json` is the active amendment; see `revisions/r2/README.md`, its
saved-byte diagnosis/rebuild, original witnesses and three ledger prefix snapshots.
Fresh r2 attestation preserves old receipts and each call's original provenance.


## r3: definite DNS non-start ruling (2026-11-12 HKT)

Claude supplied the programme ruling missing in r2. The current ENOTFOUND case
is a definite non-start with zero API duration, usage and cost, and empty
modelUsage. `freeze-r3.json` binds all three sealed parents. STOP clearance is
recorded separately with the original request preserved for identical resend;
no old STOP, terminal, parsed evidence, attestation or ledger entry is changed.
Transport errors that may have reached the server end only their episode with
no resend, and three consecutive transport failures pause collection durably.
This is an operational amendment; registered science and r2 generated-error
handling stay unchanged. See revisions/r3/README.md and RUN.md.


## r4: actual saved r3 STOP is schema rejection

The delegating reviewer's prompt describes the old DNS envelope, but the actual
r3 dispatch 1 returns API 400 for unsupported top-level oneOf/allOf/anyOf. The old
DNS wrapper is unchanged and matches r3 correctly, including returncode 1, empty
stderr, nested zero usage, fallback_credit null and empty modelUsage. The collector
checks nonstart before decode. The 400 falls through and decode's exit gate masks
it as transport failure. r4 gives it an explicit API 400 diagnostic and UNKNOWN
programme disposition; it does not invent a DNS match or authorize a schema
change. STOP-r3 and all journal prefixes remain intact; clearance-r4 is false.
The exact 400 wrapper and real useful-core saved 429 bytes are portable fixtures.
The latter verifies reset gating, identical resume and accounting through the
collector. freeze-r4 binds all four parents with changed-file byte witnesses.
No model call, push, Git command or actual attestation is performed by the builder.
