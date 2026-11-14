# Semi-autonomous research: how Claude and Codex run the programme

Robin's brief, 11 November 2026. Applies to every project in this folder. [`_shared/agents/ORCHESTRATION.md`](../../../_shared/agents/ORCHESTRATION.md) (claims, reviews, git, stop points) still applies; this file adds the research loop.

## Goal

Turn the eight playable experiments listed on https://iamrobin.ai/research/ into real studies, to the standard of the Honest Agent, with as little human intervention as possible. Target: all done by **Sunday 15 November 2026**.

**Order:**
- **Wave 1:** Work or Proof?, then Signal or Silence.
- **Wave 2:** The Receipt Gap, Bridge or Bus?, Three Rules, One Lunch.
- **Wave 3:** The Useful Core, The Portable Self, One Door, Many Hands.

Each project gets its own folder here: `work-or-proof/`, `signal-or-silence/`, and so on.

## Roles

| Who | Role | Does |
|---|---|---|
| **Robin** | Sovereign | Sets direction. Approves the **first project's final delivery** only; after that, the loop runs on its own. Asked about anything over 100 USD, deletions, repository visibility, money or credentials |
| **Codex** (`gpt-6.1-sol`, effort high) | Builder | Reviews the playable experiment, drafts the protocol and acceptance criteria, writes code and tests, runs the study, writes results, builds the web page. May use its own sub-agents (scribe, tester, builder) |
| **Claude** | Reviewer and judge | Reviews each protocol and each finished study, proposes extra scope, agrees acceptance criteria with Codex, checks claims before reporting, keeps the question log. Spends its own effort on judgement, not on building |

## The loop, per project

1. **Survey (Codex).** Read the playable experiment (`robin-web/public/<slug>/`: README, EXPERIMENT.md, model and results) and `ANTresidency/experiment_to_research.md`. Write `<project>/SURVEY.md`: what the toy shows, and which real-model question it can carry.
2. **Protocol (Codex).** Draft `PROTOCOL.md` from the Honest Agent template. It includes **acceptance criteria**, predictions, a budget estimate and a stop rule. Ground truth is scored by code; local models come first and frontier models second.
3. **Agreement (Claude ⇄ Codex).** Claude writes its review in `_shared/agents/reviews/<project>/`. Codex answers in a `RESPONSE-*.md` file in the same folder, and revises. **They proceed once both write "AGREED"** in that folder. There are at most three rounds; then the disagreement goes to Robin, with both positions in one page.
4. **Build and run (Codex).** Tests, freeze, push to GitHub before any model call, record the push time and the first call's start time, run, then run the frozen analysis.
5. **Review (Claude).** Read the results from a fresh clone, check that the numbers rebuild, look for overclaims, and propose deeper scope if worthwhile.
6. **Iterate or stop.** Codex digs deeper as a new version (`v0.2`, …) with its own protocol and freeze. Repeat steps 3–5. **Stop when the first of these happens:**
   - the project's spend reaches **40 USD**; or
   - Claude and Codex both write "ACCEPTED", meaning the agreed acceptance criteria are met and more work would add little.
7. **Deliver (Codex builds, Claude checks).**
   - Write `RESULTS.md` and `README.md`.
   - Push the deliverables to GitHub.
   - Build the web page at `https://iamrobin.ai/research/<slug>/` as a `robin-web` pull request, after `pnpm run release:check` passes.
   - Claude reviews the page against the results.
   - Merge once `verify` passes: automatic after Robin clears project 1; project 1 waits for Robin.
   - Confirm the page is live, and update the project's card on `/research/` from "Playable seed" to "Empirical study".

## Default acceptance criteria (each protocol may tighten them)

- **Real models make the decisions:** local models (Qwen 2.5 7B, Llama 3.1 8B; Qwen 2.5 1.5B as reference), plus at least one frontier family where it adds information.
- **At least one pre-registered primary test** with a pass rule. Pre-register abstention-as-miss as co-primary wherever monitors may abstain.
- **Enough data to say something:** at least 200 scored runs or judgments for the primary test, unless the protocol argues otherwise.
- **Integrity, as in the Honest Agent:** push before the first call, a freeze, every call saved, a spend ledger, an offline rebuild from a fresh clone, and failed predictions stated.
- **An independent review by Claude**, with every finding fixed or answered.
- **A clear story:** a plain-language page with a question, a result, the twist (if any) and the limits.

## Budget

- **Per project:** up to **40 USD** of model calls is approved automatically. That is also the stop line.
- Going past 40 USD needs Claude and Codex to agree in writing, with the reason. **Over 100 USD: ask Robin.**
- Each project keeps its own ledger. `BUDGET.md` in this folder totals them.
- Codex's own building time runs on Robin's subscription and isn't counted in the project budget.

## Where things live

| What | Where |
|---|---|
| Working folders | `06_intelligence/AI_research/research/<project>/` |
| Reviews and agreement | `_shared/agents/reviews/<project>/` |
| GitHub | private repository `Robin84Bran/research`, one folder per project. Pushed from a clone in the scratch area, never from RobinOS2 itself |
| Web pages | `robin-web`, via a release checkout under `00_identity_output/website/_releases/` and a pull request |
| Question log | `interesting_questions.md` in this folder. Anyone may append; never rewrite past entries |
| Status board | `STATUS.md` in this folder, one line per project, updated by Claude |

## House rules (unchanged from the Honest Agent)

- Never overwrite saved runs, freezes or ledgers.
- Never change prompts or analysis after freeze.
- Never rerun a series after seeing its results.
- Label post hoc work.
- Say "consistent with" for untested mechanisms.
- Report bad results plainly.
- **No daemons, schedulers, brokers, trading, Telegram or credentials** in any delegated session.
- **Computer control** is permitted for this programme (Robin, 11 November 2026). Use it only when a command-line route doesn't exist.

## Final delivery to Robin, per project

1. The live page `https://iamrobin.ai/research/<slug>/`.
2. The GitHub folder with the protocol, code, data, results and checksums.
3. Local deliverables in the project folder.
4. A three-line résumé entry: the question, the result, the link.
