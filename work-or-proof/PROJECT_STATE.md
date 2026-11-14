# Work or Proof? · Project state

Updated 11 November 2026 (HKT), offline build.

- Authorized outcome: implement, test, import/reconcile and freeze offline; stop before inference. No network or git authorized or performed. Writes confined to this project.
- Agreement: PROTOCOL.md status APPROVED by Claude and Codex under semi_autonomous.md; only its status line changed. Both agreement records are copied and checksummed under evidence/agreements/.
- Built: standard-library portable importer, independent ordered receipt truth checks, immutable serial Ollama collector, exact replay sampler, resource-reserving policies, fixed statistics/bootstrap, deterministic offline renderer and CLI. RUN.md gives the exact staged commands and outputs.
- Verification: 74 offline tests pass, including an injected fake monitor, crash/timeout/resume/digest checks, routing failures, duplicate bootstrap instances, portable-source rebuild and a synthetic renderer. config/offline_test_report.json retains the complete test log. No real capped-policy evaluation occurred.
- Reconciliation: PASS; 1,440 primary items, 737 breaches / 703 compliant; 2,880 Claude judgments and 720 each GPT monitor/referee. All four historical ledgers reconcile to USD 59.795598. 407 source-freeze hashes checked. Main evidence manifest covers 5,143 files; agreement copies are separately checksummed. imported/ contains data, validation counts and the report.
- Retained diagnosis: the initial importer attempted tasks['calibration'] instead of the source-configured payment family; that implementation KeyError was corrected before successful reconciliation. imported/reconciliation-failures.jsonl preserves it. No source truth contradiction was found.
- Freeze: created and verified; SHA-256 75e19187ace057a67afb72b45505d8b4cf419b25a3abf0302dbaab629ae07bf7. Verify with python3 -B wop.py verify. The freeze binds protocol, RUN, prior-exposure records, code, config, tests, evidence and imported outputs. This operational state file is mutable and excluded to avoid circular hashes.
- Runtime limitation: no endpoint was contacted. Actual server metadata/defaults/context remain UNKNOWN. Installed Ollama 0.33.3 binary and archived model metadata were inspected offline; collection verifies expected version/pins and binds observed metadata before dispatch and across resumes.
- Next action: Claude pushes the unchanged freeze and underlying evidence from an isolated clone, records the server-sourced push time, starts project Ollama at 127.0.0.1:11435, and supplies collection/push.json using RUN.md. Only then may collection begin. No inference has started; actual collection/ is absent.
- Ownership: the existing tool-created Codex build claim was verified. Its lifecycle remains with the owning orchestration session because the claim registry is outside this task's explicit write scope.
- Scientific acceptance and final delivery remain pending collection, frozen analysis, independent fresh-clone review and both ACCEPTED records; Robin retains the first-project delivery gate.


## 2026-11-11 (HKT) · Offline analysis and local delivery completed

This current snapshot supersedes the pre-collection next action above; the earlier build record is retained.

- Authority: Robin requested frozen verification/analysis, RESULTS/README, offline with no Git or model calls and writes inside this project. The post-analysis questions came from Claude’s analysis brief. No publication, new inference or acceptance decision was performed.
- Freeze passed for all 5,187 files before analysis and again after completion. Exact command: `python3 -B wop.py analyze --output results/main`; exit 0, primary `passes`, 700 table rows. All 8 generated artifact hashes match `results/main/manifest.json`. All 74 tests and portable import/reconciliation passed.
- Primary at 822,482 frontier tokens: Qwen LT mean TP 499.98828125/737 (67.8410%) versus X 368.39453125/737 (49.9857%); recall difference +17.8553 pp, 95% interval +16.1784 to +19.7736 pp. Both co-primary lower bounds, source FPR guardrails and audit floors passed. Full Qwen LT census still loses 66 catches relative to C while saving 32.9855% frontier tokens.
- Collection: 5,808 completed, 0 failed/uncertain/malformed, 0 new frontier calls, 0 USD. Both models replayed 24/24 raw replies and verdicts exactly; LP5 for Llama failed. Push attestation 2026-11-11T04:11:53Z / 63dd761; first local start 2026-11-11T04:12:28.652785Z.
- Deliverables: root RESULTS.md includes every registered policy/grid/cohort, primary guardrails, resources, source/actor breakdowns, predictions and limits. README.md provides offline fresh-clone rebuilding and the file map. Two post hoc questions were appended without changing the registered history prefix.
- Question-log exception: QUESTIONS.md was itself frozen. Its exact registered bytes are retained as delivery/QUESTIONS.registered.md and match the original freeze. Only this authorized append differs in the current root. Root `verify` will report that mismatch. delivery/prepare_rebuild.py stages the original registered package for unchanged frozen verification/analysis; no verifier/code/freeze patch was made. The local staged package passed hashes and portable import, then its verified disposable input copy was removed; delivery/staged_validation.json records that check.
- Remaining: independent Claude finished-study review and fresh-clone numerical rebuild, findings answered and both ACCEPTED records; scientific acceptance remains UNKNOWN. Publication/first-project delivery gates are outside this offline task.
- Ownership: reused the existing tool-created Codex claim matching this task. Its lifecycle remains with the owning orchestration session; the registry is outside this task's write scope.

## 2026-11-11 (HKT) · Results review r1 addressed; page prepared

This entry supersedes the earlier question-log exception and pending-review status.

- Authority: Robin requested Claude’s Fix 1 and Fix 2, direct tests/verification, a local response and the website research page. Durable deliverables are in the study/release task paths; no Git commands, publication or inference were performed. Existing Codex claims were verified; the external registry remains with the owning orchestration session.
- Restored `QUESTIONS.md` to its original registered bytes. Preserved both post-analysis questions separately in unfrozen `QUESTIONS-post-analysis.md`; their request came from Claude’s analysis brief. README no longer requires staging registered bytes. Historical delivery checks remain labelled superseded.
- Added exactly 150 words for a general reader at the top of RESULTS.md. Updated the unfrozen renderer to reproduce the final report byte for byte.
- Evidence: all 74 tests passed (`delivery/results-r1-tests.log`); direct `python3 -B wop.py verify` returned `PASS: 5187 frozen files`. All eight frozen result artifact hashes match. `delivery/results-r1-verification.json` records current checks. No frozen outputs or analysis code changed.
- Acceptance: Claude’s results review accepted conditional on these fixes. Both are addressed; Codex’s `RESPONSE-results-r1.md` ends ACCEPTED. Scientific study complete; first-project delivery approval remains Robin’s gate. Historical frozen acceptance UNKNOWN is preserved.
- Website: wrote `src/pages/research/work-or-proof/index.astro` in `<WORKSPACE>/00_identity_output/website/_releases/research-work-or-proof-20261111`, added the empirical study without removing its playable seed, and registered the SEO/sitemap route and route count.
- Release check BLOCKED: exact requested `npx --yes pnpm@11.19.0 run release:check` exited 1 before running checks because DNS resolution of `registry.npmjs.org` failed (`ENOTFOUND`). Release checkout `release-check-work-or-proof.log` retains the error. Per Robin’s instruction, stopped after edits without a workaround. Website build/render validity remains UNKNOWN; it has not been published.
- Next action: run the exact release check in a network-enabled environment, resolve any reported issues, then obtain Claude’s page review and Robin’s first-project delivery approval before publication.
