# Post-analysis questions — 12 November 2026 HKT

Appended by Codex for Claude’s delegated review. These questions arose after the frozen analysis; they are not pre-registered predictions and do not authorize further collection. v0.2 is the final cohort.

1. Why did shared memory outperform automatic routing in Qwen 7B, including among complete pairs? Is the pattern consistent with useful cross-console context, note construction, or another untested mechanism? Routing and context size changed together, so this study cannot isolate the cause.
2. How much usable memory survives a short output cap? The 215 completed output-length stops are operational limits, and local validity failed despite exact JSON Schema decoding. A future design would need a separately agreed cap/format contract before interpreting memory ability.
3. What does it mean for a notebook to be “productive” when Claude reaches 100% with both keyed and shared storage? Its tie falsifies P6’s advantage prediction while both memory arms beat discard; ten blocks cannot establish equivalence.
4. Why does Claude choose null without notes yet confidently use stale notes after remapping? The observed pattern is consistent with a distinction between missing evidence and obsolete evidence, but the mechanism was not tested.
5. Can a deterministic keyed ledger be a better operational memory system than model-written notes? Its stable 100% versus Qwen 7B’s 6.125% is a compelling engineering reference, not a causal comparison of equally expressive systems.
6. Does a tiny positive average gain matter when full-return success is zero? Llama’s ΔY is positive but ΔF ties at zero, and P3 passes despite very low absolute utility. The joint rule prevents that weak result from becoming the primary claim.
7. Why did identical mappings fail to reduce the routing advantage in Llama? The pre-registered family-wise conjunction fails even though Qwen’s direction held; no cross-family pooling can rescue it.
8. How should a portable, frozen regression suite preserve its historical collection checkpoint? One saved STOP test fails once later episodes exist, even though current freezes, receipt lineage, actual collection accounting and independent replay can be verified. Future harnesses should use immutable minimal fixtures rather than the evolving collection.
9. How should an operational failure affect evaluation denominators without becoming a behavioral claim? DNS, 429 and output caps stay operational here, while missing opportunities still count as misses under the frozen Y/F rule.
