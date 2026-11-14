D3 verification method (Claude delegation; no model calls or Git)

Retained unsuccessful test logs: build 3 exposed a test fixture colliding with
an already saved second usage-resume directory; the synthetic later-fatal
terminal now uses an unstarted schedule id. Build 5 exhausted temporary storage
while overlapping full-collection copies ran. Those task-owned sessions were
stopped. Destructive-copy tests now copy only actual saved Claude attempts and
prefix checkpoints; the complete original collection is independently verified
and replayed in place after sealing. No original evidence was edited.

A profiling attempt showed repeated prefix hashing. Log verification now updates
one SHA-256 state per appended raw line and compares every retained prefix
checkpoint, preserving identical evidence and rejection behavior. The full
94-test build 6 passed in 8.719 seconds, including the real saved frontier
clearance and attestation. The final run adds D3 nonstart-resume regression.

The baseline records all pre-D3 collection evidence, plus exact ledger lengths
and prefix hashes. Parent scope/science and archived source hashes are checked.
Final checks cover freeze creation/verification, recorded clearance, local
attestation, full raw replay, all baseline bytes, unchanged ledger prefixes,
remaining exposure, and the dispatch gate. Collection is never invoked by the
builder. Final results are written to collection/d3-verification.json so that
the sealed source inventory remains immutable.
