# Return Demo Runbook

## Purpose

Run the first end-to-end return and release prototype and verify that the repository generates real return artifacts from policy, optimization, and Daml workflow execution.

## Preconditions

- run from the repository root
- local bootstrap completed with `make bootstrap`
- the repo-local Daml toolchain is available under `.runtime/`
- no local policy or demo input edits are pending unless intentionally under test

## Primary Command

```sh
make demo-return
```

This command:

1. compiles the Daml package through `make daml-build`
2. evaluates the positive and negative return bundles under `examples/demo-scenarios/return/`
3. runs deterministic retained-set optimization against the currently encumbered collateral set for every scenario
4. invokes the Daml return workflow path for the positive path and the three workflow-control negative paths
5. validates the generated `ReturnReport` against `reports/schemas/return-report.schema.json`
6. writes JSON and Markdown artifacts under `reports/generated/`

## Expected Artifacts

After a successful run, confirm that these files exist:

- `reports/generated/return-demo-report.json`
- `reports/generated/return-demo-summary.md`
- `reports/generated/return-demo-timeline.md`
- `reports/generated/positive-return-policy-evaluation-report.json`
- `reports/generated/positive-return-optimization-report.json`
- `reports/generated/positive-return-workflow-input.json`
- `reports/generated/positive-return-workflow-result.json`

The same run also refreshes the negative-path artifacts:

- `reports/generated/negative-unauthorized-return-policy-evaluation-report.json`
- `reports/generated/negative-unauthorized-return-optimization-report.json`
- `reports/generated/negative-unauthorized-return-workflow-input.json`
- `reports/generated/negative-unauthorized-return-workflow-result.json`
- `reports/generated/negative-replayed-return-instruction-policy-evaluation-report.json`
- `reports/generated/negative-replayed-return-instruction-optimization-report.json`
- `reports/generated/negative-replayed-return-instruction-workflow-input.json`
- `reports/generated/negative-replayed-return-instruction-workflow-result.json`
- `reports/generated/negative-obligation-state-mismatch-policy-evaluation-report.json`
- `reports/generated/negative-obligation-state-mismatch-optimization-report.json`
- `reports/generated/negative-obligation-state-mismatch-workflow-input.json`
- `reports/generated/negative-obligation-state-mismatch-workflow-result.json`

## Operator Checks

Check the return report:

```sh
jq '{returnReportId, overallStatus, demo, scenarios: [.scenarios[] | {scenarioId, mode, result, policyDecision, optimizationStatus, returnLotIds, retainedLotIds, observedReasonCodes}]}' reports/generated/return-demo-report.json
```

Check the positive workflow result:

```sh
jq '{returnState, currentEncumberedLotIds, returnedLotIds, remainingEncumberedLotIds, requestedReturnQuantity, remainingRequiredCoverage, releaseConditionSatisfied, atomicityOutcome, executionReportCount}' reports/generated/positive-return-workflow-result.json
```

Check the Markdown summary:

```sh
sed -n '1,220p' reports/generated/return-demo-summary.md
```

## Failure Handling

If `make demo-return` fails:

1. inspect the reported scenario name and failure reason
2. open the generated scenario artifact under `reports/generated/` if one was written before the failure
3. run the component commands directly if needed:

```sh
make policy-eval POLICY=examples/demo-scenarios/return/return-policy.json INVENTORY=examples/demo-scenarios/return/positive-inventory.json
make optimize POLICY=examples/demo-scenarios/return/return-policy.json INVENTORY=examples/demo-scenarios/return/positive-inventory.json OBLIGATION=examples/demo-scenarios/return/positive-obligation.json
```

4. if the failure comes from Daml workflow execution, confirm the package still builds and the lifecycle tests still pass:

```sh
make daml-build
make daml-test
```

5. if schema validation fails, inspect the relevant generated JSON file and compare it against:

- `reports/schemas/policy-evaluation-report.schema.json`
- `reports/schemas/optimization-report.schema.json`
- `reports/schemas/return-report.schema.json`

## Recovery Notes

- The run is idempotent with respect to generated artifacts under `reports/generated/`; re-running the command replaces the prior return outputs.
- The demo currently uses the Daml IDE ledger, not the pinned Quickstart LocalNet.
- The positive workflow path proves release-condition validation, approval gating, replay-safe request identifiers, and encumbrance-state updates only. It does not yet prove Quickstart deployment, asset-adapter execution, or role-scoped report disclosure.
