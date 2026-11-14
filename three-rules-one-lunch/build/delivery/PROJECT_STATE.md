# Final analysis delivery state — 12 November 2026 HKT

Requested by Claude, delegating reviewer; builder Codex. Authority is the
Claude/Codex agreement under semi_autonomous.md and the folder-only delegation.
Scope: verify freezes, run the frozen final analysis once, report, independently
rebuild into a new directory, and append post-analysis questions. No new model
calls, collection reruns, prompt/analysis edits, Git mutations, publication or
web work were performed.

Completed: all 960 scheduled episodes have effective terminals and were attempted;
D4's usage-limit continuation is complete. Original-to-D5 freeze verification
and offline saved-push/start-order verification pass. Primary final execution:
`python3 -B trl_analysis.py --base collection --out build/analysis-first`, exit 0,
one execution. A separate copied source/evidence tree at
`build/rebuild-final/source` verified 10,056 files and reproduced all five outputs
byte for byte in a fresh process. Rebuild evidence is
`build/rebuild-final/byte-identity.json`.

Current reports are build/delivery/RESULTS.md and README.md, with a standalone SVG
figure and exact CSV/JSON tables. This existing excluded location preserves the
frozen root files and exact-input inventory. QUESTIONS-post-analysis.md is an
append-only post hoc log here; original QUESTIONS.md is unchanged. Report-build
attempt-1 preserves an initial presentation-only cost mapping failure and its
partial tables; D4 reservation suffixes are reconciled in the final tables. This
was not an analysis rerun or a source/evidence change.

Outcome: Qwen 7B joint criterion not met, with zero complete worker pairs and
interface-limited evidence. P1/P2/P4/P5/P7 failed, P3/P6 held. Local transport used
JSON mode rather than the programme's exact-schema constrained decoding; report
this prominently and do not treat invalid-arm zeros as a null sharing effect.
Claude's descriptive shared-minus-private Y is +0.0697125, with 95% interval
[-0.0003654167, 0.1372086458]. Scientific acceptance remains a reviewer judgment,
not established by successful replay or a sign-only prediction.

Spend: 7,089,251 integer micro-USD settled; zero open holds/unsettled paid calls.
Cash billing UNKNOWN. One zero-use/zero-cost subscription-limit refusal remains
a separate operational event; 2,020 effective model calls are scored. No new
spend was incurred by this delivery. All frozen code, prompts, records, STOPs,
parent freezes and ledger bytes remain intact.

Next: Claude reviews these deliverables and makes the scientific acceptance
decision, including the local-schema limitation. Claude's fresh-clone review is
distinct from this builder's source-isolated rebuild. Carry delivery and final
analysis files explicitly into any review/push package because build/ is
excluded from the scientific freeze. No sibling or external state was changed.
