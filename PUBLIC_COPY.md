# About this public copy

This repository is a redacted public copy of the private working repository for the research programme at https://iamrobin.ai/research/. It was produced on 14 November 2026 from private commit `fff877960c7183212370ad99ed1db1be26e6be0b`. The private repository remains the frozen record.

## What was changed, and why

The studies saved every model call, including the exact command lines and file paths used on the machine that ran them. Those details identify a personal computer, not the science, so they were replaced with neutral placeholders:

| Placeholder | Replaces | Replacements |
|---|---|---|
| `<WORKSPACE>` | the workspace root path on the collection machine | 56,475 |
| `<HOME>` | the home directory path | 14,799 |
| `<user>` | the machine login name | 14,909 |
| `<external-tooling>` | the path and name of an unrelated folder that held the Claude command-line install | 16,763 |
| `00000000-0000-0000-0000-000000000000` | Claude session and message identifiers in saved replies | 27,994 |
| `<TMPDIR>` | the operating-system temporary directory | 3,357 |
| `<SCRATCH>` | an agent scratch directory | 82 |

- **30,400 of 796,225 files** were changed. Nothing else in them was altered: prompts, model replies, token counts, costs, timestamps and scores are as collected.
- **25 compressed archives were withheld**, because they contain the same details and rewriting an archive would produce a new, unverifiable artefact. They are copies of 7 distinct archives (offline dry runs and bundled copies of earlier evidence).
- Experiment-generated identifiers such as `run_id` and `cohort_run_id` were left as they are.
- Git history was not carried over, because the original commits contain the unredacted files. This copy starts from a single commit.

## The record

- [`public-copy/redactions.jsonl`](public-copy/redactions.jsonl): one line per changed or withheld file, with the SHA-256 of the original bytes, the SHA-256 of the public bytes, and the number of replacements by rule.
- [`public-copy/summary.json`](public-copy/summary.json): the totals above.
- [`public-copy/redact_public_copy.py`](public-copy/redact_public_copy.py): the script that made the changes. Its rule file names the removed strings, so only a template is published: [`public-copy/rules.template.json`](public-copy/rules.template.json).
- [`public-copy/scan_public_copy.py`](public-copy/scan_public_copy.py): the independent scan run afterwards over every file. It found no home-directory paths, no private email addresses, no credentials, no account fields and no chat links.

## What this means for verification

Each study's freeze files and manifests list SHA-256 hashes of the **original** bytes. For the 30,400 redacted files and the 25 withheld archives those hashes will not match this copy, so integrity checks and "rebuild from a fresh clone" commands that verify hashes can fail here even though the scientific content is unchanged. The statement on the website that every study rebuilds byte for byte from a fresh clone refers to the private original. `redactions.jsonl` links each public file to the hash of its original, so a changed file can be told apart from a tampered one.

Paths in the run instructions (for example `<WORKSPACE>/06_intelligence/AI_research/research/<study>`) are placeholders: substitute the folder where you cloned this repository.

## Related

- The Honest Agent and The Obedient Rebel: https://github.com/Robin84Bran/honest-agent
- Programme pages: https://iamrobin.ai/research/
