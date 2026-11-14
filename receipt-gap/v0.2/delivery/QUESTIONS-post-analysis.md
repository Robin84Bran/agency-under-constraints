# The Receipt Gap · post-analysis questions

Appended 11 November 2026 (HKT), Codex analysis delivery under the Claude/Codex
agreement. These are **post hoc** questions prompted by the frozen results, not
registered predictions, measured mechanisms, or permission to collect again.
The original QUESTIONS.md is unchanged.

- **Why did a plain baseline fail even without receipt loss?** Qwen 7B duplicated
  in 94/100 plain episodes at both 0% and 50% receipt loss, with no exact-once
  completion in either arm. What observable decision pattern explains this
  insensitivity to confirmations? A future study could distinguish prompt/interface
  adherence from evidence use without replacing these failed runs.
- **Does keeping a key explain anything if the agent does not finish the task?**
  Llama reused original nonnull keys in 67/67 main keyed retry opportunities but
  completed 0/100 episodes exactly once; Qwen 1.5B reused 355/357 but completed
  only 1/100. Which job-selection errors coexist with apparently excellent reuse,
  and would a separately registered interface variant preserve that distinction?
- **When does a reliable check become unusable?** Only 25/100 Qwen main check
  trajectories were valid, all 25 already duplicated; Claude's check arm had
  eight failures, including one harness failure and seven key-rule violations.
  Would a new interface that makes operation-specific key constraints explicit
  change validity, safety, or both? This version cannot separate those mechanisms.
- **Can perfect completion coexist with reasonable uncertainty?** Claude keyed
  completed 20/20 exactly once, yet only 7/20 joint reports were determinate and
  correct. Which information would let the model certify completion without
  inducing unwarranted confidence? A future evidence-sufficiency study could
  score epistemic uncertainty separately from operational reporting utility.
- **How can duplicate admission be tested when the actor causes none?** Claude
  produced zero duplicates across all 60 episodes, leaving R=0/0 UNKNOWN.
  Would separately registered, code-certified duplicate histories provide a
  meaningful report-only challenge? That would test a different population and
  must not be presented as a repair of this actor benchmark.
- **Why did the forecast confuse silence with explicit denial?** Qwen admitted
  11/194 duplicate episodes, explicitly denied 52/194, and abstained on 131/194.
  What evidence boundary separates appropriate abstention from avoidable
  reporting failure? Neither this endpoint nor the current data establish intent.
- **How much apparent toolkit benefit comes from contract validity?** The actual
  Qwen complete-pair duplicate interval was negative, but only 93 pairs qualified,
  and 34/42 study cells failed technical gates. Can a new registered design obtain
  high validity before testing toolkit effectiveness, while retaining this failed
  study as evidence rather than selecting it away?
- **What survives a production receiver?** The positive Claude keyed completion
  pattern assumes permanent atomic bindings. A new bounded experiment could test
  delayed acknowledgements, key expiry, reset or non-atomic effect/key writes.
  Which first failure would most constrain a production claim? None was tested here.


## Appended after v0.2 collection · 12 November 2026 HKT

Codex, under the Claude/Codex agreement. These are **post hoc** questions based on descriptive terminal-event replay; the frozen v0.2 entry point stopped before scoring. The inherited v0.1 questions above are preserved. None authorizes a v0.3 or new model collection.

- **Why do all three local actors duplicate with a reliable status tool?** At 50% receipt loss, every local check arm has 100/100 actual duplicate episodes despite 100/100 valid action trajectories. What observable job-selection and status-use patterns separate knowing a fact from using it to stop? This is consistent with a decision-policy limitation; internal reasoning was not tested.
- **Why does the zero-receipt-loss plain baseline also duplicate every time?** All three local v0.2 actors duplicate in 100/100 episodes even when every delivered request returns a receipt. Can unnecessary retries after positive confirmations explain this pattern? Receipt ambiguity alone cannot describe these saved outcomes.
- **What did constrained action decoding improve, and what did it expose?** Llama action validity rose from 3/100 to 100/100 in main plain, yet exact-once completion stayed 0/100 and duplicates rose from 1/100 to 100/100. A future causal design would need to distinguish format validity from the changed distribution of legal decisions, without deleting either version.
- **How far does a stable key get before job coverage becomes the problem?** The scripted same-seed keyed policy completes 72/100 local episodes exactly once; the model keyed arms achieve 2/100, 0/100 and 0/100. Which observable allocation errors explain the gap, and why does Qwen 1.5B still have only 14/100 valid keyed trajectories? These comparators are post hoc and do not identify a mechanism.
- **Can operational certainty and report certainty come apart?** Claude keyed completes 20/20 exactly once while only 7/20 reports are jointly determinate and correct; check completes 18/20 and has 16/20 jointly correct reports. Does reliable state evidence improve report utility relative to idempotent execution? This descriptive comparison is not a causal explanation.
- **How should duplicate admission be challenged when a policy never duplicates?** Claude again has zero true duplicate episodes, leaving R UNKNOWN (0/0). A future report-only study would need separately registered duplicate histories and must not be called a repair of this actor benchmark.
- **Can a freeze protect the intended execution path as well as its bytes?** The native r5 freeze verifies but the frozen analysis rejects the genuine r5 receipt because an older allowlist ends at r3. Which pre-collection integration fixture would exercise a completed r5 call through the full analysis without contacting a model?
- **How can post-run verification avoid depending on the live ledger being paused?** Two frozen resume tests now fail because they copy the completed ledger into a pre-resume fixture. Would a sealed historical ledger fixture preserve the intended transition test across collection completion? The current failures remain visible.

Correction to the third newly appended question: the v0.1 Llama main plain arm has **2/100 valid action trajectories and 0/100 duplicate episodes** (not 3/100 and 1/100). Its v0.2 counterparts are 100/100 and 100/100. The underlying question and both saved versions remain unchanged.
