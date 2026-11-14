# Three Rules, One Lunch — D2 state

Updated 11 November 2026. Claude reviewer delegated this folder's offline D2
harness amendment, tests, disposition, clearance and refreeze to Codex builder.
No generation, network request, push, Git mutation or sibling write is performed.

D2 agrees with PROTOCOL §4: a completed local output-length response is a
schema-invalid episode failure, not a collection-wide integrity failure. Fixed
operational denominators, episode termination, validity criteria and no-resend
rules are unchanged. Integrity and resource stops remain fatal; exact expected
input token counts remain UNKNOWN without independent tokenizer evidence.

`llama8b-s034-central` is scored, incomplete: one received reply, three technical
slots and nine missing slots, no receipts, Y=H=0. Its fatal terminal, STOP and all
previous evidence are immutable. `deviations/d2/clearance.json` binds existing
collection bytes and clears only that classification for resume. Later stops
remain fatal and use STOP-d2.json. No real-model aggregate analysis was run.

`freeze-d2.json` binds the original freeze and D1, preserved D1 baselines, narrow
harness edits, tests and evidence. Historical starts retain their D1 attestation;
new starts require a separate fresh D2 attestation. Evidence:
`evidence/test-report-d2.json`, `evidence/rebuild-d2.json`. Current commands are
in `RUN-d2.md`; historical documents are preserved.

Next owner: Claude reviews and pushes the D2 package from the separate clone,
retains genuine new server evidence, attests into this canonical project, then
resumes local and frontier in frozen order. D2 itself dispatches nothing. No
scientific conclusion, acceptance or publication is claimed.
