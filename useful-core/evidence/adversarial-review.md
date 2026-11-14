# Build failure-path review · 2026-11-11

Applied the adversarial-review skill within the folder-local implementation delegation. No independent reviewer or sub-agent is implied.

Material findings fixed:

1. Interrupted starts originally lacked an offline audit path without a terminal record. Reproduction: reserve, save request/start, interrupt before parsed/terminal write. Current audit retains unknown truth and holds, and reconciles a saved full settlement if present. `test_crash_after_paid_start_retains_unknown_hold_in_analysis` and `test_crash_after_settlement_reconciles_cost_without_terminal` pass.
2. Saved failure flags needed independent verification. Reproduction: mark a valid raw reply as failed. `classify_reply` now derives failure classes from raw bytes/envelopes; `test_independent_audit_rejects_forged_failure` passes. All realized local settings and Claude argv/environment are checked against frozen inputs, including failed calls.
3. First-call compatibility must survive resume. Missing/changed retained first-call contracts stop frontier admission. `test_frontier_contract_retained_and_revalidated` passes. No result-prose fallback exists.
4. Invalid outer JSON types must save terminal failure evidence. Both adapters and offline audit now handle array envelopes without losing raw bytes; `test_nonobject_envelope_fails_closed_with_evidence` passes. Partial local transport bytes are retained as an episode transport failure, never retried.

Other tested boundaries: exact manifest/template/system pin chain; Qwen default-system override; local done/eval_count and length distinctions; known overrun charged fully even above stop; unknown usage retained; concurrent lock rejection; append-only prefixes/truncation; server-activity id/after/ref/timestamp and every committed blob; local-before-frontier and three-failure pause; complete-block/all-scheduled co-primary gates.

Residual limitations: current provider compatibility, runtime/capacity, exact prompt tokenization and cash billing are UNKNOWN. Empirical overhead/output reservations are not guaranteed billing caps. The first frozen scored frontier call resolves compatibility and may stop the arm. Live collection and empirical study acceptance are outside this build.
