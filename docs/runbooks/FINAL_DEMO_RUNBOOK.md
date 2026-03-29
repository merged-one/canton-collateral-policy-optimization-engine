# Final Demo Runbook

## Purpose

Run the final prototype package for the Canton Collateral Control Plane and verify that one reproducible command produces:

- confidential margin-call evidence
- confidential collateral-substitution evidence
- confidential margin-return evidence
- invariant pass or fail output
- machine-readable artifact indexing
- documented third-party integration surfaces

## Preconditions

- run from the repository root
- local bootstrap completed with `make bootstrap`
- the repo-local Daml toolchain is available under `.runtime/`
- no local scenario, policy, or report-schema edits are pending unless intentionally under test

## Primary Command

```sh
make demo-all
```

This command:

1. runs `make test-conformance`
2. re-executes the confidential margin-call, substitution, and return demos as part of the conformance suite
3. generates aggregate invariant pass or fail output
4. writes `reports/generated/final-demo-pack.json`
5. writes `reports/generated/final-demo-pack-summary.md`

## Expected Artifacts

After a successful run, confirm that these files exist:

- `reports/generated/final-demo-pack.json`
- `reports/generated/final-demo-pack-summary.md`
- `reports/generated/conformance-suite-report.json`
- `reports/generated/conformance-suite-summary.md`
- `reports/generated/margin-call-demo-execution-report.json`
- `reports/generated/substitution-demo-report.json`
- `reports/generated/return-demo-report.json`

The operator package also depends on these repository documents:

- `docs/evidence/DEMO_ARTIFACT_INDEX.md`
- `docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md`
- `docs/testing/CONFORMANCE_SUITE.md`

## Operator Checks

Check the final pack:

```sh
jq '{demoPackId, overallStatus, commandSurface, demoFlows: [.demoFlows[] | {demoType, reportType, reportPath}], invariantOutput: {passedCheckCount, failedCheckCount}}' reports/generated/final-demo-pack.json
```

Check the conformance output:

```sh
jq '{suiteId, overallStatus, checks: [.checks[] | {checkId, status}]}' reports/generated/conformance-suite-report.json
```

Check the human-readable summary:

```sh
sed -n '1,260p' reports/generated/final-demo-pack-summary.md
```

Check the integration guide:

```sh
sed -n '1,260p' docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md
```

## Failure Handling

If `make demo-all` fails:

1. inspect `reports/generated/conformance-suite-summary.md` if it exists
2. identify whether the failure came from:
   - one of the three confidential workflow demos
   - the aggregate conformance checks
   - the final demo-pack indexing step
3. re-run the lower-level command that failed:

```sh
make demo-margin-call
make demo-substitution
make demo-return
make test-conformance
```

4. if the failure is in the final pack only, inspect the referenced artifact paths in:

```sh
sed -n '1,260p' reports/generated/conformance-suite-report.json
```

5. if the failure is workflow-related, confirm the Daml package and lifecycle tests still pass:

```sh
make daml-build
make daml-test
```

## Recovery Notes

- `make demo-all` is idempotent with respect to the generated files under `reports/generated/`
- the package still executes on the Daml IDE ledger rather than the pinned Quickstart runtime
- the final demo pack is the operator-facing proposal artifact bundle; `make verify` remains the full repository validation loop
