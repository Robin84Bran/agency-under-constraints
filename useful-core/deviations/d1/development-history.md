# D1 development evidence

All failures below were offline test-fixture or historical-audit integration
issues; no study model was invoked and no collection evidence was changed.

- Initial 81-test run: one failure in the historical A1 exhaustive-audit test.
  D1 sources no longer have A1 source coordinates. The check now reconstructs
  the original and A1 source trees from immutable archives before rebuilding
  the unchanged historical audit; current scientific preservation remains checked.
- First D1 suite (93 tests): one assertion failure and one error. The report
  decision is always 7, even when actions end before decision 6; the test now
  checks only decisions actually called. A one-cell schedule could not satisfy
  the fixed statistical contrast. The analysis test now uses all 960 scheduled
  rows while inserting the single test episode at its matching design cell.
- First lineage suite (97 tests): one fixture-path error. `prepare` does not
  create config/prompts.json in the minimal fixture; the protected-input mutation
  test now uses the fixture's actual config/design.json. No production behavior
  was changed to make this test pass.

Subsequent 99-test run passed. The final source-bound report/log retain the
verification on the completed D1 inputs. Source archives and original A1 audit,
freeze, offline data and test evidence remain unchanged.

The first source-bound 99-test run after updating the runbook/README failed its
historical A1 README equality check. Its full failure is retained in test-log.txt
and test-report.json. That historical check now reads the exact archived A1
README; D1 manifest validation still pins every unchanged current input and the
allowed archive. Final evidence is test-log-final.txt/test-report-final.json.
