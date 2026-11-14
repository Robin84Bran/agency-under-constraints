# Signal or Silence · current post-analysis state

Updated 11 November 2026 (HKT). This companion records the requested state update
without editing PROJECT_STATE.md, whose exact bytes are bound by freeze-d1.json.
The task also explicitly forbids changes to frozen files. Both freezes remain
authoritative; no replacement freeze or verification exception is introduced.

- **Outcome:** original frozen analysis completed once with 10,000 bootstrap
  replicates (seed 20261112). Collection COMPLETE: 5,604 saved responses and starts,
  1,868 per judge, zero missing/uncertain/unstarted/reused calls and zero transport
  failures. Every plain and explicit joint test failed under both weightings.
- **Headline evidence:** plain T abstention Qwen 10.42%, Llama 37.50%, Claude
  97.50%; T−F contrasts −2.92 / +24.58 / +97.50 percentage points. Claude F/R plain
  recall is 85.83%/92.50% by trajectory, with 47/40 primary technical failures.
  Explicit instructions did not produce a joint pass. Receipt-arm Claude W
  abstention was 0% plain and 88.33% explicit.
- **Forecasts:** P1 plain passed for all; P1 explicit failed overall. P2, P3 and
  P4 failed as complete forecasts in both instructions; their individual successes
  and failures are tabulated in RESULTS.md. P5 failed for all judges in both
  weightings. P6 is retrospective only, not a prospective success or failure.
- **Authority:** this task authorizes offline verification, frozen analysis,
  one separately directed rebuild, reports, post hoc questions and project-local
  state. Protocol and D1 choices came from Claude/Codex agreement under
  semi_autonomous.md. No new collection, prompt/code changes, network, Git,
  publication, credentials or outside-project writes are part of this delivery.
- **Integrity:** both original and D1 freezes passed before the first analysis.
  Original numerical artifact SHA-256:
  `0ac4d9486e96ac10c661b2bc951126bbb5bef356ace85caf4986543c646f6861`.
  Original generated Markdown is retained in delivery/frozen-analysis/; root
  RESULTS.md and README.md are expanded delivery prose derived from the saved
  JSON. QUESTIONS.md and all frozen inputs are preserved.
- **D1 and spend:** USD11.053392 fully settled in collection/cost.jsonl, with
  zero outstanding reservation. Local accounted model-call USD is zero;
  actual hardware/energy/opportunity costs are unavailable. D1 increased only
  reservation allowances after the second Claude call stopped at an input overrun;
  both saved calls were retained. The original flagged overrun is conservatively
  included among 275 unique Claude technical failures by the frozen analysis.
- **Rebuild:** separately requested command
  `python3 -B sos.py analyze --output analysis-rebuild-1` completed. All three
  generated artifacts are byte-identical to the original numerical JSON and
  preserved generated Markdown. Both freezes passed final verification.
  Comparisons, checksums and offline provenance checks are recorded in
  delivery/verification.json. This was one original production execution and
  one expressly requested independent rebuild; no additional analysis run.
- **Acceptance and limits:** scientific acceptance UNKNOWN. Claude primary F/R
  semantic validity is below 95%, so that acceptance condition is unmet. The
  independent fresh-clone Claude review and documented findings/dispositions
  remain pending. This same-workspace rebuild cannot substitute for them. Repeated
  synthetic evidence and previously examined tasks limit generalization; internal
  mechanisms are untested. No agent is marked ACCEPTED.
- **Next action:** make these completed local deliverables available for
  independent fresh-clone Claude review and disposition of acceptance gaps.
  No further model call or scientific extension is authorized by this state note.
