# Return Demo Runbook

## Purpose

Run the end-to-end return and release prototype and verify that the repository generates real return artifacts from policy, optimization, workflow execution, and, in Quickstart mode, the reference token adapter path.

## Preconditions

- run from the repository root
- local bootstrap completed with `make bootstrap`
- the repo-local Daml toolchain is available under `.runtime/`
- no local policy or demo input edits are pending unless intentionally under test

## Primary Commands

```sh
make demo-return
make demo-return-quickstart
```

`make demo-return`:

1. compiles the Daml package through `make daml-build`
2. evaluates the positive and negative return bundles under `examples/demo-scenarios/return/`
3. runs deterministic retained-set optimization against the currently encumbered collateral set for every scenario
4. invokes the Daml return workflow path for the positive path and the three workflow-control negative paths
5. validates the generated `ReturnReport` against `reports/schemas/return-report.schema.json`
6. writes JSON and Markdown artifacts under `reports/generated/`

`make demo-return-quickstart`:

1. starts or reuses the pinned Quickstart overlay through `make localnet-start-control-plane`
2. evaluates the Quickstart-backed positive and negative return bundles under `examples/demo-scenarios/return/`
3. reseeds scenario-scoped Quickstart state for each workflow-bearing scenario
4. advances the real Quickstart return workflow to either a pending-settlement adapter handoff or a deterministic blocked outcome
5. invokes the reference token adapter only for the positive and replay scenarios
6. refreshes provider-visible Quickstart status for both committed and blocked paths
7. validates the generated `ReturnReport` against `reports/schemas/return-report.schema.json`
8. writes JSON and Markdown artifacts under `reports/generated/`

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

After a successful Quickstart run, confirm that these files also exist:

- `reports/generated/return-quickstart-report.json`
- `reports/generated/return-quickstart-summary.md`
- `reports/generated/return-quickstart-timeline.md`
- `reports/generated/positive-return-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/positive-return-quickstart/localnet-return-adapter-execution-report.json`
- `reports/generated/positive-return-quickstart/localnet-return-status.json`
- `reports/generated/negative-unauthorized-return-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-unauthorized-return-quickstart/localnet-return-status.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-adapter-execution-report.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-status.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart/localnet-return-status.json`

## Operator Checks

Check the return report:

```sh
jq '{returnReportId, overallStatus, demo, scenarios: [.scenarios[] | {scenarioId, mode, result, policyDecision, optimizationStatus, returnLotIds, retainedLotIds, observedReasonCodes}]}' reports/generated/return-demo-report.json
jq '{returnReportId, overallStatus, demo, scenarios: [.scenarios[] | {scenarioId, mode, result, blockedPhase, adapterOutcome, requestIdentifier, replayHandlingResult, finalPostReturnState}]}' reports/generated/return-quickstart-report.json
```

Check the positive workflow result:

```sh
jq '{returnState, currentEncumberedLotIds, returnedLotIds, remainingEncumberedLotIds, requestedReturnQuantity, remainingRequiredCoverage, releaseConditionSatisfied, atomicityOutcome, executionReportCount}' reports/generated/positive-return-workflow-result.json
jq '{returnState, workflowGate, settlementInstructionId, settlementInstructionState, currentEncumberedLotIds, returnedLotIds, remainingEncumberedLotIds, releaseConditionSatisfied, atomicityOutcome, controlChecks}' reports/generated/positive-return-quickstart-workflow-result.json
```

Check the positive Quickstart adapter and replay evidence:

```sh
jq '{settlementInstruction, adapterReceipt, workflowConfirmation, replayHandling}' reports/generated/positive-return-quickstart/localnet-return-adapter-execution-report.json
jq '{scenarioId, returnState, settlementInstructionState, providerVisibleEncumbrances, providerVisibleCurrentLotHoldings, providerVisibleAdapterReceipts}' reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-status.json
```

Check the Markdown summary:

```sh
sed -n '1,220p' reports/generated/return-demo-summary.md
sed -n '1,220p' reports/generated/return-quickstart-summary.md
```

## Failure Handling

If either return command fails:

1. inspect the reported scenario name and failure reason
2. open the generated scenario artifact under `reports/generated/` if one was written before the failure
3. run the component commands directly if needed:

```sh
make policy-eval POLICY=examples/demo-scenarios/return/return-policy.json INVENTORY=examples/demo-scenarios/return/positive-inventory.json
make optimize POLICY=examples/demo-scenarios/return/return-policy.json INVENTORY=examples/demo-scenarios/return/positive-inventory.json OBLIGATION=examples/demo-scenarios/return/positive-obligation.json
```

4. if the failure comes from the Quickstart-backed path, inspect the scenario-specific artifacts and rerun the lower-level commands directly:

```sh
LOCALNET_SCENARIO_MANIFEST=infra/quickstart/scenarios/confidential-return-demo-positive-scenario.json scripts/localnet-seed-return-demo.sh
scripts/localnet-run-return-workflow.sh --input-file reports/generated/positive-return-quickstart-workflow-input.json --output-file reports/generated/positive-return-quickstart-workflow-result.json
scripts/localnet-run-return-token-adapter.sh --input-file .runtime/localnet/control-plane/positive-return-quickstart/return-adapter-input.json --output-file reports/generated/positive-return-quickstart/localnet-return-adapter-execution-report.json
scripts/localnet-return-status.sh --output-file reports/generated/positive-return-quickstart/localnet-return-status.json
```

5. if the failure comes from Daml workflow execution, confirm the package still builds and the lifecycle tests still pass:

```sh
make daml-build
make daml-test
```

6. if schema validation fails, inspect the relevant generated JSON file and compare it against:

- `reports/schemas/policy-evaluation-report.schema.json`
- `reports/schemas/optimization-report.schema.json`
- `reports/schemas/return-report.schema.json`

## Recovery Notes

- The run is idempotent with respect to generated artifacts under `reports/generated/`; re-running the command replaces the prior return outputs.
- The IDE-ledger and Quickstart variants intentionally share the same policy and retained-set logic so report drift between runtimes stays visible.
- The Quickstart-backed command now proves approval-gated release, real adapter execution, replay-safe request handling, and blocked unauthorized or stale-coverage paths with provider-visible status evidence.
- The aggregate proposal package now consumes the Quickstart return report through `make test-conformance` and `make demo-all`; role-scoped report disclosure and production-grade custodian integrations remain future work.
