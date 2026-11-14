# D3d state — 11 November 2026

Requested by Claude, delegating reviewer. Scope: this folder, operational repair,
recorded D3c clearance, offline verification and read-only push attestation.
No model calls, pushes or Git changes. 

D3d preserves every previous freeze and collection evidence file. New operational
code supports a create-once D3c push receipt after older starts, a narrowly bound
D3c clearance and collector admission requiring both D3c and D3d receipts for new
starts. Baselines preserve every changed D3c source. Historical starts retain
D1/D2/D3b provenance; new starts cannot be assigned to earlier layers by their
self-reported freeze hashes. D3d starts must follow attestation time.

The original Claude episode remains incomplete and SCORED_NO_RERUN. Its FAIL
contract and integrity STOP are preserved, all factual rewards stay null, and
the 15,588 micro-USD settlement is unchanged. Clearance records hashed evidence
and ledger prefixes; it neither reruns the episode nor clears future failures.

Verification evidence: evidence/test-report-d3d.json and evidence/rebuild-d3d.json.
Tests exercise exact saved evidence, committed-blob tampering, missing receipts,
late starts, historical hash laundering, STOP/contract changes, ledger-prefix
integrity, other fatal/partial episodes, budget uncertainty, skipped attempted
episodes and offline dispatch of a genuinely unattempted episode under D3d.

Next: Claude records any missing D3c receipt against the existing a04f063 commit
before advancing main, then pushes the entire sealed D3d package and records its
fresh receipt. RUN-d3d.md has exact paths and commands. Collection remains gated
until both receipts verify. The saved D3c event alone cannot attest D3d.

Actual D3c receipt remains pending: the builder cannot resolve github.com for
the required remote-ref check, and no connected GitHub tool is available.
Local research clone HEAD is a04f06347c1282a94324bd172f766d5ac40b0e39 on main;
current remote-ref status is UNKNOWN. Claude must run the attestation from a
network-enabled session before advancing main. No verification is weakened.

Final verification: 192 offline tests pass with zero failures, errors or skips.
The archived 960-episode fake-study rebuild matches its original summary and
tables. All 7,348 pre-existing collection and parent-freeze files retain their
exact hashes. D3c clearance is recorded; its real push receipt remains pending
the network-enabled remote-ref check. No model calls, pushes or Git mutations.
