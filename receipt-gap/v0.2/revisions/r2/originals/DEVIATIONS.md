# v0.2 deviations

Pre-push r1 is the sole harness revision. It replaces fatal handling only for
proven pre-generation subscription usage-limit refusals. This implements Claude's
programme-wide decision relayed to this builder, recorded in `REVISIONS.md`.
It makes no scientific change and does not relax handling for ambiguous starts.

Original freeze bytes and evidence are retained. The active freeze is
`freeze-r1.json`; reviewer attest and collect commands in `RUN.md` select it
explicitly. Fresh push and attestation remain prerequisites for all real calls.
No v0.2 refusal had previously been scored, and no STOP needed clearing.
