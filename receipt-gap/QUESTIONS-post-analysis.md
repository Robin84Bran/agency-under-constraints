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
