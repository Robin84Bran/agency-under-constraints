# Work or Proof? frozen build and later execution

All commands run from this folder. Python 3.10+; standard library only. No install,
credentials, source workspace, or model server is needed for validation/rebuild.
The historical `survey_inventory.py` and `agreement_sizing.py` remain provenance;
the portable pipeline below uses only copied evidence.

## Offline checks

```sh
python3 -B -m unittest discover -s tests -v
python3 -B wop.py import
python3 -B wop.py verify
```

`import` verifies `evidence/manifest.json`, independently reconciles receipts,
preserved prompts and historical ledgers, and checks the immutable outputs in
`imported/`. A mismatch stops the pipeline. It never contacts a server. The
initial archive-copy invocation is build-only; fresh clones need no source path.
`verify` checks the write-once `freeze.json` against protocol, code, configuration,
tests, copied evidence and normalized inputs. Never overwrite a freeze or calls.

## Claude must do first

1. Push this complete frozen package, including underlying `evidence/` and
   `freeze.json`, from an isolated research clone to the private
   `Robin84Bran/research` repository. Confirm the pushed bytes and retain the
   GitHub server timestamp and commit. Do not edit frozen files in preparation.
2. Start the project-owned Ollama server in a separate foreground terminal on
   the execution machine. Use the existing model store; never pull or change it:

```sh
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=<WORKSPACE>/ANTresidency/Honest_Agent/models/ollama /opt/homebrew/bin/ollama serve
```

3. Record the verified push evidence in the execution checkout. Replace the
   sample timestamp, commit and source with actual GitHub evidence:

```sh
python3 -B wop.py record-push --pushed-at '<GitHub UTC ISO timestamp>' --commit '<40-character pushed commit SHA>' --timestamp-source '<GitHub push event URL or saved server evidence>'
```

This creates `collection/push.json` exclusively and binds the attestation to the
SHA-256 of `freeze.json`. It is an operator attestation, not a fabricated online
verification. The collector requires it to precede the first local call.

## Collection: later-stage inference, not part of this build

```sh
python3 -B wop.py collect
```

Use the same command to resume. It checks the freeze and push attestation before
contacting only `127.0.0.1:11435`. It verifies actual Ollama 0.33.3 and both model
digests, records actual metadata/defaults, and stops on identity drift. Offline
build metadata explicitly marks live defaults/context UNKNOWN. Source model
manifests, templates and parameters are copied under `config/model_metadata/`.

The runner sends at most 5,760 original requests then 48 predetermined replays,
serially with the protocol's decoding settings and 180-second timeout. Expected
outputs are append-only request/start and full response records under
`collection/calls/` and `collection/replays/`, metadata and cumulative active-time
records under `collection/`, and `collection/push.json`. Prompts, seeds,
configured/observed model identity, raw replies, usage and timing are retained.
No response or ambiguous started request is resent. A crash may conservatively
consume reserved active time; the cumulative 12-hour cap never resets. Transport
failures and unknown usage remain visible and block complete-study acceptance.

## Frozen offline analysis and independent rebuild

After collection finishes, choose a new output directory:

```sh
python3 -B wop.py analyze --output results/main
```

The analysis reads first responses, never substitutes replays, and never imports
the collector or contacts models. Outputs are `primary.json`, `tables.json`,
`tables.csv`, `collection.json`, `predictions.json`, `bootstrap_draws.jsonl.gz`,
`orders_routes.jsonl.gz`, `RESULTS.md` and their `manifest.json`. The route archive
starts with its array-column schema. C is always the full trace census reference;
at insufficient caps it is labelled infeasible, rather than converted to a prefix.
The fixed 2,000 × 16 bootstrap is substantial
CPU work. Negative results remain results; incomplete data are labelled.

Claude's fresh-clone offline rebuild uses the same saved collection:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B wop.py import
python3 -B wop.py verify
python3 -B wop.py analyze --output results/rebuild
```

Compare the deterministic numerical artifacts in the two output directories.
Neither reanalysis nor a replay mismatch authorizes another original response.
Independent review and both agents' ACCEPTED remain outstanding after the build.
