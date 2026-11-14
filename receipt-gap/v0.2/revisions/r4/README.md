# r4 saved-envelope audit

Claude is the delegating reviewer; Codex is the builder. The claimed DNS matcher
miss did not occur in the saved bytes. Dispatch 0 is the historical DNS wrapper
(SHA 358c59daddca28a2cc0f759538a7c718a464eae311f4399ca3c50ad3971f4c85),
correctly recognized and resent by r3. The actual new dispatch 1 has SHA
32e37928e96f691d6345cdf4469aa10771ce8f062d7737b362b503f677fb2330 and reports
API 400: top-level oneOf/allOf/anyOf is unsupported. STOP-r3 was created for that
response. Its empty stderr, returncode 1, nested zero usage, empty modelUsage and
zero API duration/cost do not turn its 400 result into ENOTFOUND. See diagnosis.json.

The collector already checks nonstart before decode. Both the DNS and actual
saved 429 pass this admission check with returncode 1. The 400 does not; decode
formerly mislabeled its nonzero exit as uncertain transport. r4 fixes that message
and records UNKNOWN rather than inventing a new non-start ruling. No resend is
prepared; the unchanged action schema would still contain the rejected oneOf.
A separate 400 disposition and equivalent-schema decision were requested from
the delegating reviewer. No reply had been supplied when this package was sealed.

All collection files and three journal prefixes are hashed in preservation.json.
All four parent manifests remain byte-exact; changed r3 inputs have original
witnesses. No config, prompt, schema, schedule, scoring or scientific function is
changed. clearance-r4.json is written after sealing and binds the final hash,
STOP-r3, current raw reply and original request, with UNKNOWN and cleared false.
No ledger or timer event is appended. New r4 collection is blocked before provider
construction. The original r3 clearance remains historical; it cannot clear STOP-r3.

A real saved 429 is copied read-only from useful-core's paused dispatch. Its source
raw metadata, stdout/stderr bytes, start and pause are retained unchanged. The
fixture adapts only the wrapper storage format, with source hashes and method in
real-429-provenance.json. Offline tests prove the actual refusal matches, pauses
at zero cost, blocks before the saved reset, resumes the identical request after
reset and reconciles accounting. It is foreign operational evidence, not Receipt
Gap study data. Tests also prove exact 400 preservation, DNS admission before
decode, four-parent sealing, mocked r4 attestation, UNKNOWN clearance idempotence
and no-call blocking. Full verification blocks real Git/model processes and network.
check-1.json retains the initial stale failure-audit line inventory failure;
the r4 failure-site inventory and test reference correct it. No model calls,
pushes, actual Git commands or real attestations were made by the builder.

Exact reviewer commands are in RUN.md. The r4 collect invocation intentionally
refuses admission pending the different programme ruling.
