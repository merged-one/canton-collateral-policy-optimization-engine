# Return Report Specification

## Status

- Report version: `0.1.0`
- Canonical schema: [reports/schemas/return-report.schema.json](../../reports/schemas/return-report.schema.json)
- Primary commands: `make demo-return` and `make demo-return-quickstart`

## Purpose

`ReturnReport` is the first machine-readable operator-facing contract for end-to-end collateral return and release control in the Control Plane. It ties together:

- the policy-evaluation artifact for each return scenario
- the optimization artifact that selects the retained encumbered set and therefore the released lots
- the committed or blocked return workflow result for each scenario
- Quickstart seed, adapter-execution, and provider-visible status artifacts when the real runtime path is used
- invariant-linked negative-path evidence for unauthorized release, replayed return instruction, and obligation-state mismatch failures

The contract exists so operators and proposal reviewers can verify that the repository now proves real return and release behavior without guessing how policy, retained-set selection, approvals, replay protection, and workflow outcomes relate.

## Inputs

The current return-report path consumes one manifest under `examples/demo-scenarios/return/` and resolves:

1. one `CPL v0.1` policy file per scenario
2. one normalized inventory snapshot containing the currently encumbered collateral set
3. one normalized obligation input per scenario carrying the current posted lot set and the remaining required coverage amount used by the retained-set optimizer
4. one parameterized Daml Script request for every scenario

The manifest additionally defines:

- which scenarios run optimization and workflow execution
- whether a scenario uses the IDE-ledger workflow path or the Quickstart-backed workflow-plus-adapter path
- expected policy, optimization, workflow, and reason-code outcomes
- workflow metadata such as the return request ID, correlation ID, workflow gate, custody account, settlement accounts, and simulated replay flags
- optional workflow-side overrides such as a higher remaining required coverage amount to prove stale obligation-state mismatch handling

## Deterministic Rules

The report depends on these rules:

1. Every scenario runs policy evaluation first.
2. Every scenario then runs the deterministic optimizer against the currently encumbered inventory and the declared remaining required coverage amount.
3. The returned lots are derived as `currentPostedLotIds - retainedLotIds`; the Daml workflow does not re-select release scope independently.
4. The Daml workflow input carries both the full currently encumbered set and the selected return lot set, plus explicit `currentSecuredAmount` and `remainingRequiredCoverage` values.
5. The Daml return path must reject the release when `currentSecuredAmount - requestedReturnQuantity < remainingRequiredCoverage`.
6. The Daml return path must reject altered settlement scope and unauthorized settlement confirmation attempts.
7. A replayed return instruction must be blocked by preserving an active `returnRequestId` after the committed return closes.
8. On the Quickstart path, the adapter may execute only from a real pending-settlement `SettlementInstruction` emitted by the workflow result.
9. On blocked Quickstart paths, provider-visible adapter receipt count must remain `0`.
10. The top-level `returnReportId` is a stable hash of the manifest content plus the scenario results used to build the report.

## Top-Level Structure

| Field | Meaning |
| --- | --- |
| `reportType` | Fixed to `ReturnReport`. |
| `reportVersion` | Fixed to `0.1.0`. |
| `returnReportId` | Deterministic hash-based identifier for one return demo run. |
| `generatedAt` | UTC timestamp when the orchestration wrote the report. |
| `overallStatus` | `PASS` or `FAIL` for the full demo run. |
| `demo` | Runtime mode, command, manifest path, output directory, primary optimization artifact, and scenario counts. |
| `artifacts` | Paths to the JSON return report, Markdown summary, and Markdown timeline. |
| `scenarios` | Per-scenario results including policy, optimization, workflow, and reason-code outcomes. |
| `timeline` | Ordered execution-phase entries across the demo run. |
| `invariantChecks` | Pass/fail entries mapping the demo outputs back to repository invariants. |

## Scenario Semantics

Each scenario object records:

- whether the scenario is `POSITIVE` or `NEGATIVE`
- the operator-readable description and summary
- observed versus expected reason codes
- references to the generated policy-evaluation, optimization, workflow-input, workflow-result, Quickstart seed, adapter-execution, and provider-visible status artifacts
- the policy decision and optimization status
- the current posted lot set, retained lot set, return lot set, requested return quantity, and remaining required coverage
- the blocked phase and adapter outcome when a Quickstart scenario fails before or during release handling
- the explicit request identifier, approval state, release action, final post-return state, and replay handling result
- the Daml workflow result

The current positive IDE-ledger scenario emits:

- one policy-evaluation report
- one optimization report
- one workflow-input JSON artifact
- one Daml workflow-result JSON artifact
- one closed return path with selected encumbrances moved to released state and retained encumbrances left pledged

The current Quickstart-backed positive scenario additionally emits:

- one Quickstart seed receipt
- one Quickstart workflow-result artifact with request identifier, approval state, release condition, and pending-settlement handoff evidence
- one Quickstart adapter execution report showing release action, receipt status, and final workflow confirmation
- one provider-visible Quickstart status artifact showing final post-return encumbrances, holdings, and adapter receipt count

The current negative scenarios emit:

- one policy-evaluation report, one optimization report, one workflow-input, and one workflow-result artifact each
- one blocked unauthorized release path with provider-visible Quickstart status proving no adapter side effects
- one replay-protection path that closes the original return, emits one adapter receipt, and then blocks the duplicate instruction
- one obligation-state mismatch path that fails before approval or settlement can progress and leaves provider-visible adapter receipt count at `0`

## Workflow Result Semantics

When present, `workflow` records:

- `returnRequestId`
- `correlationId` and optional `workflowGate`
- `returnState`
- `securedPartyApproval` and `custodianApproval`
- `settlementInstructionId` and `settlementInstructionState`
- `currentEncumberedLotIds`, `returnedLotIds`, and `remainingEncumberedLotIds`
- `requestedReturnQuantity`, `currentSecuredAmount`, and `remainingRequiredCoverage`
- `releaseConditionSatisfied`
- `atomicityOutcome`
- `executionReports` and `executionReportCount`
- `controlChecks`
- ordered workflow `steps`

These fields exist so a consumer can distinguish:

- a committed return that released only the selected encumbrances
- an unauthorized release attempt that left the request in `PendingSettlement`
- a replayed instruction that was rejected after the original return committed
- a stale obligation-state mismatch that left the request in `UnderEvaluation`

The scenario-level Quickstart evidence fields then make those outcomes explicit in one place:

- `requestIdentifier` shows the runtime request ID carried through the flow
- `approvalState` shows the secured-party and custodian approval surface plus release-condition outcome
- `releaseAction` shows the real settlement instruction, release action, and adapter receipt state when present
- `finalPostReturnState` shows the final return state plus provider-visible encumbrance, holding, and receipt-count evidence
- `replayHandlingResult` shows whether replay was attempted and how it was blocked

## Timeline Semantics

`timeline` records real execution phases in order:

- `POLICY_EVALUATION`
- `OPTIMIZATION`
- `QUICKSTART_SEED` when runtime mode is `QUICKSTART`
- `WORKFLOW`
- `ADAPTER` when runtime mode is `QUICKSTART`

The Markdown timeline derived from the report keeps the same order and points at the generated JSON artifacts for each phase.

## Current Scope And Limits

The current `ReturnReport` contract covers:

- the first end-to-end return demo path
- the first Quickstart-backed end-to-end return demo path
- one real positive return path
- three real negative return paths
- replay-safe request identifiers on the Daml boundary
- approval-gated release evidence on the real runtime path
- provider-visible blocked-path status evidence showing no unintended adapter release
- invariant-linked evidence references
- operator-facing Markdown summary and timeline artifacts

The current contract does not yet cover:

- role-scoped disclosure profiles
- conformance aggregation or final demo-pack inclusion of the Quickstart-backed return path
- first-class return-right clauses in `CPL v0.1`
- on-ledger lendable-value or valuation reconciliation

Those remain future work for CPL evolution, workflow disclosure profiles, conformance packaging, and broader runtime coverage.
