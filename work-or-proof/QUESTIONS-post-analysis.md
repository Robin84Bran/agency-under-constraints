# Work or Proof? · Post-analysis questions

Requested in Claude’s analysis brief; recorded after inspecting results. This file is unfrozen. The registered question history remains unchanged in [QUESTIONS.md](QUESTIONS.md).

## 2026-11-11 (HKT) · Post-analysis questions (post hoc)

The following questions were chosen after inspecting the frozen results. They are candidate extensions, not registered tests, approved new calls or additional findings.

- **Are the two screens' false clearances complementary?** Full-census Qwen LT loses 66 catches relative to the frontier trace census; Llama LT loses 3, but escalates 92.36% rather than 66.81% of items. The registered policies do not test their clearance-error overlap or a combined gate. Would a separately pre-specified disagreement screen recover catches at the same frontier allowance, after charging both models' local tokens and time?
- **Would Llama's exact monitor replay survive a clean runtime restart?** All 24 fixed Llama replay replies were byte-identical, contrary to LP5. Would the result persist across independent process starts or separately registered seeds? This finite same-settings sample cannot identify a seeding, runtime or cache mechanism, or establish general determinism. Any new inference would require a new agreed protocol; no extra calls were made here.
