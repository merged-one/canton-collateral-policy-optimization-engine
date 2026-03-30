# Conformance Suite

## Purpose

The conformance suite turns the three confidential Quickstart-backed workflow demos plus one concrete reference token adapter proof path into one explicit invariant-verification surface for the Canton Collateral Control Plane.

It does not replace the underlying runtime commands. It refreshes them, aggregates their evidence, and emits one machine-readable pass or fail report that a reviewer can inspect without guessing which real runtime path proved which property.

## Primary Command

```sh
make test-conformance
```

This command:

1. starts or reuses the pinned Quickstart Control Plane deployment through `make localnet-start-control-plane`
2. validates the current reference token adapter proof artifacts
3. validates the Quickstart-backed confidential margin-call, substitution, and return demo reports and their referenced artifact chains
4. generates supporting policy-evaluation evidence for determinism and haircut checks
5. emits `reports/generated/conformance-suite-report.json`
6. emits `reports/generated/conformance-suite-summary.md`
7. runs `test/conformance/test_conformance.py` against the generated suite report
8. runs `test/conformance/test_conformance_checks.py` so key helper checks can fail independently of the aggregate runtime rerun

## Required Coverage

The current suite covers the minimum runtime-backed prototype control set required by the proposal:

| Check ID | Invariants | What It Proves | Primary Evidence |
| --- | --- | --- | --- |
| `AUTHORIZATION_AND_ROLE_CONTROL` | `AUTH-001`, `CTRL-001`, `WF-001` | approval gates remain authoritative on Canton before substitution settlement can be exposed, and an unauthorized Quickstart return release attempt stays blocked without adapter movement | positive substitution Quickstart workflow result, unauthorized return Quickstart workflow result plus status artifact |
| `ELIGIBILITY_DETERMINISM` | `ELIG-001`, `PDR-001` | repeating the same policy evaluation with identical inputs produces the same machine-readable result | `reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json` |
| `HAIRCUT_CORRECTNESS` | `HAIR-001` | valuation basis, haircut basis points, and lendable value arithmetic remain explicit and reproducible | `reports/generated/conformance-haircut-policy-evaluation-report.json` |
| `NO_DOUBLE_ENCUMBRANCE` | `ENC-001`, `CTRL-001` | the Quickstart posting, substitution, and return chains preserve disjoint committed or released lot sets, and blocked paths preserve incumbent scope | positive margin-call adapter execution and status, substitution atomicity evidence, return final-state evidence |
| `ATOMIC_SUBSTITUTION_WHEN_REQUIRED` | `ATOM-001`, `CTRL-001` | full replacement either commits atomically or leaves the incumbent set untouched on Quickstart | positive substitution adapter execution and status plus blocked partial-substitution status evidence |
| `REPLAY_SAFETY` | `REPL-001` | a replayed Quickstart return instruction is rejected without duplicating adapter-side release behavior | replay return adapter execution and status evidence |
| `REPORT_FIDELITY` | `REPT-001`, `PDR-001` | Quickstart deployment, adapter, demo, and report artifacts all point to real generated files and preserve scenario, workflow, and adapter counts | deployment receipt, reference adapter proof, top-level demo reports, and referenced scenario artifacts |
| `AUDIT_TRAIL_COMPLETENESS` | `AUD-001` | positive Quickstart workflow paths expose workflow steps, timelines, and final runtime-backed effect evidence without hidden reconstruction | top-level demo reports, workflow results, timelines, and adapter-backed final-state artifacts |

## Generated Outputs

After a successful run, the conformance suite refreshes or validates at least these artifacts:

- `reports/generated/conformance-suite-report.json`
- `reports/generated/conformance-suite-summary.md`
- `reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json`
- `reports/generated/conformance-haircut-policy-evaluation-report.json`
- `reports/generated/localnet-control-plane-deployment-receipt.json`
- `reports/generated/localnet-control-plane-deployment-summary.md`
- `reports/generated/localnet-reference-token-adapter-execution-report.json`
- `reports/generated/localnet-reference-token-adapter-status.json`
- `reports/generated/margin-call-quickstart-execution-report.json`
- `reports/generated/substitution-quickstart-report.json`
- `reports/generated/return-quickstart-report.json`

## Operator Checks

Check the suite outcome:

```sh
jq '{suiteId, overallStatus, runtimeEvidence: {deploymentReceiptPath: .runtimeEvidence.deploymentReceiptPath, referenceAdapterExecutionReportPath: .runtimeEvidence.referenceAdapterExecutionReportPath}, coverage, checks: [.checks[] | {checkId, status, invariantIds}]}' reports/generated/conformance-suite-report.json
```

Check the Quickstart runtime evidence:

```sh
jq '{quickstartCommit, packageId, participants}' reports/generated/localnet-control-plane-deployment-receipt.json
jq '{adapterName, settlementAction: .settlementInstruction.settlementAction, receiptStatus: .adapterReceipt.status, movementLotIds: [.adapterReceipt.movements[].lotId]}' reports/generated/localnet-reference-token-adapter-execution-report.json
```

Check the Markdown summary:

```sh
sed -n '1,260p' reports/generated/conformance-suite-summary.md
```

Check the supporting haircut vector:

```sh
jq '{overallDecision, assetResults: [.assetResults[] | {lotId, valuationBasisValue, baseHaircutBps, totalHaircutBps, lendableValue}]}' reports/generated/conformance-haircut-policy-evaluation-report.json
```

## Failure Handling

If `make test-conformance` fails:

1. inspect `reports/generated/conformance-suite-summary.md` if it was written
2. identify the failing `checkId` and its referenced artifacts
3. confirm the Quickstart deployment and concrete adapter proof path still pass:

```sh
make localnet-start-control-plane
make localnet-run-token-adapter
make localnet-adapter-status
```

4. re-run the affected Quickstart demo if needed:

```sh
make demo-margin-call-quickstart
make demo-substitution-quickstart
make demo-return-quickstart
```

5. if the failure is in determinism or haircut evidence, compare the supporting policy-evaluation artifacts directly:

```sh
sed -n '1,220p' reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json
sed -n '1,220p' reports/generated/conformance-haircut-policy-evaluation-report.json
```

6. if the failure points at runtime evidence, inspect:

```sh
sed -n '1,220p' reports/generated/localnet-control-plane-deployment-receipt.json
sed -n '1,220p' reports/generated/localnet-reference-token-adapter-execution-report.json
sed -n '1,220p' reports/generated/localnet-reference-token-adapter-status.json
```

## Notes

- `make test-conformance` is now the prototype's runtime-backed invariant gate, not a replacement for `make test-policy-engine`, `make test-optimizer`, or the IDE-ledger comparison commands
- the conformance package now validates Quickstart deployment evidence, one concrete reference token adapter proof path, and the three Quickstart-backed confidential workflow demo surfaces in one machine-readable package
- `make demo-margin-call`, `make demo-substitution`, and `make demo-return` remain comparison paths only; they are no longer the primary conformance story
