# Signal or Silence · project state

Updated 11 November 2026 (HKT), offline build complete.

- **Outcome:** protocol APPROVED under Claude and Codex agreement. Built stdlib-only portable archive import/validation, independent receipt-truth replay, opposite-history certificates, deterministic sample/request freezer, serial local/Claude collector, USD reservations, policy replay, statistics and immutable results renderer. `RUN.md` contains exact handoff commands.
- **Authority:** Robin authorized offline build, tests, reconciliation, portable evidence and freeze only. No inference, network, Git, server probes, credentials copied or publication. Every write stayed in this project. Source archives and sibling collection remained untouched.
- **Verification:** 99 offline tests pass, including fake HTTP local monitor and fake Claude subprocess. Reconciliation PASS for 1,440 source episodes, 4,320 main archived judgments and 90 calibration judgments; 407 source-freeze hashes and historical ledgers reconcile (USD 59.795598, sunk elsewhere). Portable reconstruction with original archive unavailable and sockets forbidden reproduces every dataset/certificate/design/request byte.
- **Design:** 240 primary episodes (60/source × truth stratum); 120 receipt pairs (40 HA, 80 Rebel). Both instructions use identical evidence. Exact F deduplication yields 1,868 dispatches/judge, 5,604 total. Scheduled scientific denominators remain unchanged.
- **Reuse:** fixed source selection and request bytes before cutoff 2026-11-11T04:38:54.811806+00:00. Snapshot includes 5,760 sibling originals and 48 replays. No byte-identical plain-F request; zero reuse. Every sibling receipt byte survives in the checksummed lossless 1.62 MiB `evidence/work-or-proof/receipts.tar.xz`. Original/replay descriptive accounting remains separate.
- **Resources:** frozen per-Claude measured-max reservations total USD 24.261584, plus USD 5 planning reserve, with zero sibling reuse assumed. USD 39 operational reserve stop, USD 40 absolute programme stop. Empirical maxima are estimates, not enforceable output/billing bounds. Unknown/failed chargeable attempts retain full reservations; overrun stops dispatch. Runtime/server/login/actual effort and current billing remain UNKNOWN. Source ClaudeCLI reads only its binary setting at run time from the existing `local.env`; credentials are never copied. Local cumulative active cap is 12 hours, including setup, metadata and persistence.
- **Freeze:** `freeze.json` created exclusively, verified; 5,203 frozen files. SHA-256 of exact freeze bytes: `09e07d27f622d4470fe8c4a6910e819cdbd892913c391c9297f4a72212c1a0a8`. Content manifest SHA-256: `13e0606432083a25aef6c6346c1e0d6c005b2e30822c508438e428ac5f588a67`. Freeze is never overwritten; code/prompts/settings/sample/evidence are fixed.
- **Analysis smoke:** renderer outputs under `build/renderer-smoke/` only, with 16 bootstrap smoke replicates; production remains 10,000. It correctly reports INCOMPLETE, 0/5,604 prospective calls, all predictions UNKNOWN pending new observations. Root prospective `RESULTS.md`, `README.md` and `collection/` are absent. New study calls and spend are zero.
- **Coordination:** read-only canonical claim list showed the existing Codex project build claim, no overlap. Three internal subagents wrote disjoint assigned files under that claim. No shared claim/log mutation or release was made because Robin explicitly confined writes to this project.
- **Next action, Claude:** start the existing project Ollama server at 127.0.0.1:11435; push the exact freeze from an isolated research clone; record GitHub server timestamp and commit using `python3 -B sos.py record-push ...`; then start collection with `python3 -B sos.py collect`. The runner verifies freeze/push/runtime pins before inference. Independent analysis/review and scientific acceptance remain pending. This handoff stops before inference.

## D1 update · 11 November 2026 (supersedes the historical collection status above)

- **Outcome/authority:** Codex (builder) and Claude (reviewer) agreed the
  cost-control-only D1 amendment after the frozen reservation stop under
  `evidence/agreements/semi_autonomous.md`, within Robin's standing pre-approval
  of up to USD40 per project. Robin's specific approval of D1 was not sought
  because it was not required. Preparation uses no inference, git or network and
  writes only inside this project. Existing Codex D1 claim remains untouched.
- **Current evidence:** both local judges finished 1,868 calls each; two Claude
  calls are saved and settled (USD0.013124 total). The second used 1,429 input
  tokens above the original 1,282 maximum, then stopped as required. Original
  freeze, saved calls, starts, ledger and scientific files remain unchanged.
- **D1:** per-job input = prompt UTF-8 bytes + 68 system bytes + historical hidden
  maximum 826, enlarged 10% and rounded up to 64. Plain maximum 2,496, explicit
  maximum 3,072; output 448. Exact token counts remain UNKNOWN. Full-plan USD
  33.092352 + unchanged USD5 = USD38.092352 below unchanged USD39 stop. Current
  settled spend plus remaining reservations and USD5 = USD38.067332.
- **Integrity:** new `freeze-d1.json` binds the original freeze hash and the D1
  manifest; original code backups and pre-D1 collection hashes are retained.
  Only the exact saved cost overrun is acknowledged; saved/uncertain jobs are
  skipped without retries. New overruns and unrelated integrity failures stop.
- **Verification:** offline tests and their exact counts are saved in new
  `build/postfreeze_test_report*.json`; `python3 -B sos.py verify` checks the
  original scientific inputs, D1 manifest and collection baseline.
- **Unresolved gate/next action, Claude:** D1 push status UNKNOWN. Push the full
  amendment and retained evidence from the isolated research clone, record real
  server evidence with `python3 -B sos.py record-push --deviation D1 ...`, creating
  `collection/push-d1.json`, then `python3 -B sos.py collect --models claude`.
  Until the D1 attestation exists, transport setup is blocked. Scientific analysis
  and acceptance remain pending completion; no further calls were made for D1.
