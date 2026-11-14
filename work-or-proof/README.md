# Work or Proof?

Can a cheap local monitor select work for frontier checking better than spending
the same frontier allowance on a random share of the work?

This study fixes 1,440 previously examined trajectories from the Honest Agent
(360) and Obedient Rebel (1,080), independently reconciles their receipts, and
collects new Qwen 2.5 7B and Llama 3.1 8B judgments on each report and trace.
Allocation replay then uses saved Claude trace judgments for escalation. There
are 737 breached and 703 compliant trajectories. This is prospective local
judgment on known tasks with pre-specified retrospective allocation replay.

The primary comparison is Qwen trace screening followed by frontier trace
escalation (LT) versus random-share frontier trace checking (X), at 822,482
frontier tokens, half the saved trace census. Abstention counts as a miss. See
[RESULTS.md](RESULTS.md) for the outcome, guardrails, policy tables, failed
predictions and limitations, and [PROTOCOL.md](PROTOCOL.md) for registration.
The primary test passed: mean breach recall was 67.84% for Qwen LT versus 49.99%
for X, a +17.86 percentage-point difference (95% interval +16.18 to +19.77).
The uncapped Qwen LT census still missed 66 breaches caught by full trace checking.
Local computing is a separately reported resource; zero new model-call USD
does not mean zero hardware or energy cost.

## Rebuild offline from a fresh clone

Once the complete repository package is on disk, disconnecting the network is
fine. Python 3.10+ and its standard library are sufficient. No package install,
credentials, model weights, Ollama server, original source workspace, Git
operation or new inference is needed. Keep the saved `collection/` and
`evidence/`; do not run `collect` to reproduce an analysis.

Start in this study's folder. All registered files, including `QUESTIONS.md`,
match the original freeze. Post-analysis questions requested in Claude’s analysis
brief are separate in the unfrozen `QUESTIONS-post-analysis.md`. Run verification
directly, with no staging helper or replacement freeze. Use a new output directory
for a numerical rebuild and retain the delivered `results/main/` artifacts.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B wop.py import
python3 -B wop.py verify
python3 -B wop.py analyze --output results/rebuild
```

These are the frozen offline commands in [RUN.md](RUN.md). The final step does
substantial CPU and disk work: 2,000 seed-block bootstrap replicates with 16
orders each, plus all policy tables over 256 shared orders. Do not interpret a
quiet terminal as an invitation to change the code or collect again.

Compare `primary.json`, `tables.json`, `tables.csv`, `predictions.json`,
`bootstrap_draws.jsonl.gz`, `orders_routes.jsonl.gz` and the generated `RESULTS.md`
against the delivered `results/main/` artifacts. Each output directory has a
SHA-256 `manifest.json`. `collection.json` also records runtime metadata and
collection accounting; tiny floating-point differences in summed elapsed
seconds can follow filesystem traversal order, so compare those numerically
when needed. The narrative root `RESULTS.md` is delivery prose, distinct from
the frozen analyzer's short generated report.

This delivery ran the original analysis as
`python3 -B wop.py analyze --output results/main`.
Claude’s results review judged the acceptance criteria met, conditional on the
two fixes now recorded in [RESPONSE-results-r1.md](RESPONSE-results-r1.md).
Codex accepts the completed study; publication still requires the first-project
delivery approval.

## File map

| Path | Contents |
|---|---|
| `RESULTS.md` | Readable findings, primary pass rule, all policy comparisons, predictions and limits |
| `PROTOCOL.md` | Registered population, prompts, policies, schedules, predictions and acceptance gates |
| `RUN.md` | Frozen build, collection and offline-analysis instructions |
| `SURVEY.md`, `survey_inventory.*`, `agreement_sizing.*` | Prior exposure, historical inventories and sizing provenance |
| `freeze.json` | Original SHA-256 inventory of 5,187 registered files |
| `config/` | Fixed study/collector settings, replay sample, environment expectations and copied model metadata |
| `evidence/` | Portable source trajectories, judgments, prompts, ledgers, source freezes and agreement records |
| `imported/` | Normalized dataset, receipt reconciliation and retained build-diagnosis evidence |
| `collection/push.json` | Operator attestation of the pre-collection GitHub push, bound to this freeze |
| `collection/calls/`, `collection/replays/` | Saved requests/start markers and full first/replay response records |
| `collection/runtime.json`, `collection/activity/`, `collection/summaries/` | Observed identity, cumulative active-time accounting and collection summary |
| `wop.py`, `wop_*.py` | Frozen command line, import, freeze, collector, policy replay, statistics and analysis |
| `tests/` | Frozen offline test suite |
| `results/main/primary.json` | Co-primary estimates, intervals, guardrails, audit floors and seed-block sensitivity |
| `results/main/tables.json`, `results/main/tables.csv` | Complete policy/cap/cohort/model metrics, including source, actor and fixture breakdowns |
| `results/main/orders_routes.jsonl.gz` | Integer outcomes, reservations, debits, routes and costs for every ordering; first line defines route columns |
| `results/main/bootstrap_draws.jsonl.gz` | Registered bootstrap block draws and order seeds |
| `results/main/collection.json`, `results/main/predictions.json` | Collection accounting/replay exactness and every frozen prediction evaluation |
| `results/main/manifest.json`, `results/main/RESULTS.md` | Generated artifact checksums and the frozen analyzer's own report |
| `QUESTIONS.md` | Original frozen question history |
| `QUESTIONS-post-analysis.md` | Unfrozen post hoc questions requested in Claude’s analysis brief |
| `delivery/QUESTIONS.registered.md` | Byte-exact question log bound by the original freeze |
| `delivery/prepare_rebuild.py` | Historical staging helper; no longer needed for reproduction |
| `delivery/render_results.py` | Delivery prose/table renderer reading only the completed frozen artifacts |
| `delivery/verification.json`, `delivery/staged_validation.json` | Historical delivery checks before review fixes; superseded by `delivery/results-r1-verification.json` |
| `PROJECT_STATE.md` | Mutable operational status and remaining review gates |

No frozen code, saved response or original freeze is revised by this delivery.
