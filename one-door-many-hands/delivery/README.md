# One Door, Many Hands

Adding worked delivery examples worsened Qwen 7B's registered planning outcomes: optimal choices fell from 34.3% to 21.3%, and expected regret increased by 0.10990. The joint primary test failed. P3 held; P1, P2, P4 and P5 failed. All four actors completed their assigned episodes and passed the technical-validity gates. Settled API-equivalent spend: USD1.925098; cash billing: UNKNOWN.

The rehearsal adds no information beyond the complete written rules. A pass would mean models use worked examples better than rules in this task. This is a one-shot fleet-planning experiment, not a test of executing real multi-agent teams.

Read [RESULTS.md](RESULTS.md) for the hypothesis, every prediction, intuitive headline comparisons, the figure, full cells, paired intervals, code baselines, deviations, operational events, resources and limits. [headline.svg](headline.svg) is a standalone vector figure. All final deliverables are under **delivery/** because root Markdown files are frozen historical inputs. In particular, the old root RESULTS.md and PROJECT_STATE.md describe earlier operational stages; the final report here supersedes their status claims without rewriting them.

## Offline reproduction from a fresh GitHub clone

Python 3.9+ and its standard library suffice. No model server, credentials, network, packages or original absolute location are needed. The published package must include the complete study folder, including `collection/`, `offline/`, `evidence/`, all archives, deviations, prefixes, freezes and this delivery folder. Exclude **only** directories named `__pycache__` or `.git`, files named `.DS_Store`, and files matching `*.lock`. Do not apply the historical A1 packaging exclusions in root RUN.md: this final package includes all saved collection and development evidence. Frozen archives remain intact, including their internal members.

From the cloned `one-door-many-hands/` directory, choose an unused output path **outside** that folder:

```sh
python3 -B delivery/reproduce.py --output /private/tmp/one-door-rebuild-UNIQUE
```

The runner resolves absolute paths, runs the unchanged frozen verifier, resolves all six historical freeze inventories against current or archived exact bytes, checks all three collection baselines and ledger prefixes, executes the frozen analysis once into the new output directory, then regenerates the presentation artifacts from that rebuilt JSON. It compares the analysis and all nine generated report artifacts byte for byte with the saved originals and fails on any mismatch. Output includes `analysis.json`, `rendered/`, and `verification.json`. Existing outputs are never overwritten. The runner does not import or invoke live model transport. Run it once per intended independent verification; it is not a collection command.

The historical runbook's relative `--data collection` invocation exposes a D3 path mismatch before statistics. The supported direct command uses absolute paths:

```sh
python3 -B od_analysis.py --root "$PWD" --data "$PWD/collection" --output /private/tmp/one-door-analysis-UNIQUE.json
```

Use either the runner or the direct command, not both for the same rebuild. Never run collection, preparation or freeze creation to reproduce results. Never edit prompts, analysis, saved replies, ledgers, freezes or attestations.

To verify freezes and baselines without recomputing statistics:

```sh
python3 -B delivery/reproduce.py --verify-only --output /private/tmp/one-door-verify-UNIQUE
```

No fresh-clone exception mode is required: no excluded transient path is bound by any frozen input or collection baseline. The normal verifier passes with those files absent. The excluded paths and saved hashes are recorded in [package-snapshot.json](package-snapshot.json). The optional `delivery/check_copy.py` script creates a fresh filtered copy and runs the same independent verification; it is a delivery QA tool, not part of the scientific analysis. It creates a package snapshot once and preserves all original files.

## What was checked

[freeze-verification.json](freeze-verification.json) resolves every historical frozen entry. [rebuild-verification.json](rebuild-verification.json) records the independent copy, the exact transient omissions, file-hash comparisons, the saved/rebuilt analysis hash and generated artifact identities. The copy contains every source file except the specified transient paths; the source folder is preserved. No GitHub network clone or new push was performed in this bounded delivery task: this is a fresh-clone-equivalent local copy, tested after the identical publication exclusions. Independent reviewer verification from GitHub remains a separate delivery gate.

The completed canonical analysis is [collection/analysis-final-d3.json](../collection/analysis-final-d3.json), rebuilt directly from raw responses. [analysis-invocation.json](analysis-invocation.json) preserves the failed relative-path invocation and successful absolute-path correction. There was one completed canonical scientific analysis, with no collection rerun. The later independent rebuild checks deterministic reproducibility.

CSV exports are [headline](headline.csv), [model cells](model-cells.csv), [code baselines](baseline-cells.csv), [paired contrasts](contrasts.csv), [exact paired choices](paired-choices.csv), and [resources](resources.csv). Operational nonstarts are also exported as [JSON](operational-events.json). Uniform-random expectations and presentation aggregations are post hoc; the primary endpoints, bootstrap and decisions are unchanged.

The original preregistration is [PROTOCOL.md](../PROTOCOL.md), agreement is [REVISION.md](../REVISION.md), all applied amendments are in [DEVIATIONS.md](../DEVIATIONS.md), and active integrity is pinned by [freeze-d3.json](../freeze-d3.json). The original A1 GitHub push receipt, later local attestations, historical stops, nonstarts, requests, raw envelopes and append-only budget/time records remain in `collection/`.

Post-analysis questions are appended in [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md). [presentation-qa.json](presentation-qa.json) checks all 48 model cells, 256 baseline rows, 1,860 exact pairs, token/spend reconciliation and the SVG.

## Frozen regression-suite qualification

The unchanged full suite ran in the filtered copy: **94 tests passed and one errored**. `test_d3.D3.test_real_clearance_attestation_and_prefixes` copies the current collection into a fixture intended for the pre-D3, 43-generated-call stop. After completion it copies later D3 starts without their attestation and stops on the missing fixture attestation. Its fixed forecast/spend assertions also refer to that earlier baseline. This is a historical fixture assumption, not a failed saved-evidence rebuild. The full error is retained in [frozen-tests.txt](frozen-tests.txt); it is not presented as a passing current full suite.

The same frozen recovery test **passed** when run against an independent reconstruction of the exact D3 baseline files, saved ledger byte prefixes and original checkpoints. No frozen test or analysis code was changed, and the live collection was preserved. [historical-test.json](historical-test.json) and [historical-test.txt](historical-test.txt) retain the result. To repeat only that diagnostic, use a new external output directory:

```sh
python3 -B delivery/check_historical_test.py --output /private/tmp/one-door-historical-UNIQUE
```

The primary fresh-clone reproduction command above does not depend on this historically staged recovery fixture. It passes the normal verifier and reproduces final raw-evidence analysis and all generated reports exactly with the completed collection.

This delivery was delegated by Claude under the Claude/Codex research agreement. Scientific joint pass: FAIL. Technical gates: PASS for all four actors. Independent Claude acceptance, publication and any later web page are not claimed by this local report.
