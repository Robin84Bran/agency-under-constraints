# R3 offline evidence

preservation.json binds all pre-r3 collection-r2 files, unchanged local inputs
and the three parent freezes. cost.jsonl is bound as a prefix because Claude
must append to the same accounting ledger. All other listed files stay exact.
parent-build/ retains the original r2 build outputs before r3 verification.

sibling-schema-audit.json records read-only active source paths and hashes for
the five requested projects. No other sibling uses a top-level union in its
active Claude schema. Property/item unions are not root unions. No model call
was used to inspect schemas; live Claude acceptance remains UNKNOWN.

tests/test_schema_r3.py proves universal inclusion by exact scalar-domain
projection, then checks 67,200 finite action combinations, both arm permissions,
report equality, required keys, extras, types, actual schema argv and conservative
size allowances. tests/test_revision_r3.py covers all parent bindings, local
preservation, ledger prefixes, pre-Claude freeze requirements, all four pushed
manifests, new attestation placement and fake Claude collector/audit handoff.
All simulated Git and model transports in tests are mocks; they execute neither.

fixture-transport-policy-failure.txt retains the first fake-collector handoff
failure: the minimal synthetic parent omitted the existing transport-policy
field, and the unchanged frontier gate stopped it. The fixture now explicitly
supplies D3_ACCOUNT_ACTUAL_NO_REPAIR; no production gate was relaxed.
fixture-runtime-failure.txt retains the next fixture setup failure: no runtime
config had been provided. The fake collector now supplies a fake binary name;
its adapter remains mocked and executes no process.

The active build/test-report.json is source-bound by freeze-r3.json after final
passing checks. The freeze is create-once and does not overwrite any parent.
