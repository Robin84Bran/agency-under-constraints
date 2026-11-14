# Claude–Codex orchestration rule

Approved by Robin on 10 November 2026. Applies to every Claude and Codex session working in RobinOS2 or Robin's repositories. Robin's instructions always come first.

## The one rule

**One writer per path at a time. Claim it with `claim.py` before you write; release it when you're done.**

## 1. Claim before writing

Claim with the tool, never by editing a file by hand:

```
python3 _shared/agents/claim.py claim <path> --agent claude --task "..." --hours 2
python3 _shared/agents/claim.py release <path> --agent claude --result "..."
python3 _shared/agents/claim.py list
```

- **Path** is the smallest folder that covers your work, for example `06_intelligence/AI_research/research/receipt-gap/`. A path outside RobinOS2, such as a repository clone, is claimed by its absolute path.
- **Agent** is `claude` or `codex`, plus the session name if there are several.
- **If the tool says BLOCKED, don't write there.** It refuses a path when another claim covers it, sits inside it, or was made at the same moment. Pick other work, or ask Robin.
- **Release when you're done**, even if the task failed, with one line on the result.
- A claim past its expected finish shows as **STALE**. Stale is not free: ask Robin before taking it over. The tool refuses to release another agent's claim.

**Why a tool and not a shared file:** two agents can read a file at the same moment, both see a path free, and both claim it. The tool claims by creating a lock folder, which the operating system grants to exactly one agent. It then re-checks for overlapping claims and withdraws the later one. It was tested with 20 simultaneous claims on one path (one winner) and 30 rounds of a folder and its subfolder claimed at the same instant (one winner every round). `locks/` is the source of truth; `CLAIMS.md` is the log the tool writes.

## 2. Reading and auditing are always allowed

- Either agent may read anything the other has written, at any time, including inside a claimed path.
- **A reviewer never edits the work under review, and never writes inside a path it hasn't claimed.** Reviews go in the review folder, which nobody claims:

  ```
  _shared/agents/reviews/<project>/REVIEW-<agent>-<YYYYMMDD>-<topic>.md
  ```

  Each review is a new file, so two reviewers can never collide. The claim holder reads it and fixes the findings.
- A review records what was checked, what reproduced, and each finding with a file and line, ordered by seriousness.

## 3. Delegating to the other agent

- Either agent may start a session for the other: Claude via `codex exec`, Codex via `claude -p`. **Claim the path for that session first**, under the delegate's name, and release it when the delegate is done.
- Give the delegate: this file, the task, the claimed path, the stop points, and the file to report back in (`HANDOFF.md` or `RESULTS.md` in the claimed folder).
- Delegated sessions run in their own folder or clone and stay inside the claimed path. One delegated writing session per path.
- The delegating agent reads the delegate's output and reports to Robin. Don't relay unverified claims: check them first.

## 4. Git and publishing

- **Never run git commands that change the RobinOS2 working tree itself** (checkout, stash, reset, commit, branch switch). Work in a separate clone or a release checkout under the project's `_releases/` or a temporary folder.
- One branch per task, named `claude/<task>` or `codex/<task>`. Never push to the other agent's branch.
- Websites and protected repositories change only by pull request, after the project's own checks pass.

## 5. Always ask Robin first

- Paid model calls beyond an approved cap, or with no approved cap.
- Merging to `main`, publishing, deploying, or changing who can see a repository.
- Deleting or overwriting data: trial files, ledgers, freezes, results.
- Anything involving money, brokers, trading bots, Telegram, credentials, or daemons and schedulers. **These stay off limits to delegated sessions entirely.**
- Editing `AGENTS.md` or any agent instruction file.

## 6. When in doubt

Stop, leave a note in `HANDOFF.md` or a review file, and ask Robin. A paused task is cheap; two agents overwriting each other isn't.
