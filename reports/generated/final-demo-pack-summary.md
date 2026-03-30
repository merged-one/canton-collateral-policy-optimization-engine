# Final Demo Pack Summary

- Demo pack ID: `fdp-ad4246d5144c77eb`
- Command: `make demo-all`
- Overall status: `PASS`
- Conformance report: `reports/generated/conformance-suite-report.json`
- Quickstart deployment receipt: `reports/generated/localnet-control-plane-deployment-receipt.json`
- Reference adapter execution report: `reports/generated/localnet-reference-token-adapter-execution-report.json`

## Runtime Evidence

| Surface | Command | Artifact |
| --- | --- | --- |
| Quickstart deployment | `make localnet-start-control-plane` | `reports/generated/localnet-control-plane-deployment-receipt.json` |
| Reference adapter path | `make localnet-run-token-adapter` | `reports/generated/localnet-reference-token-adapter-execution-report.json` |
| Reference adapter status | `make localnet-adapter-status` | `reports/generated/localnet-reference-token-adapter-status.json` |

## Demo Flows

| Demo | Report Type | Command | Runtime | Positive | Negative | Report |
| --- | --- | --- | --- | --- | --- | --- |
| CONFIDENTIAL_MARGIN_CALL | ExecutionReport | `make demo-margin-call-quickstart` | QUICKSTART | positive-margin-call-quickstart | negative-ineligible-asset-quickstart, negative-workflow-rejected-quickstart | `reports/generated/margin-call-quickstart-execution-report.json` |
| CONFIDENTIAL_COLLATERAL_SUBSTITUTION | SubstitutionReport | `make demo-substitution-quickstart` | QUICKSTART | positive-substitution-quickstart | negative-replacement-becomes-ineligible-quickstart, negative-partial-substitution-quickstart | `reports/generated/substitution-quickstart-report.json` |
| CONFIDENTIAL_MARGIN_RETURN | ReturnReport | `make demo-return-quickstart` | QUICKSTART | positive-return-quickstart | negative-unauthorized-return-quickstart, negative-replayed-return-instruction-quickstart, negative-obligation-state-mismatch-quickstart | `reports/generated/return-quickstart-report.json` |

## Real Vs Staged

### Real On Quickstart

- Pinned Quickstart deployment and DAR installation into app-provider and app-user participants.
- One concrete reference token adapter posting path with machine-readable execution and status evidence.
- Quickstart-backed confidential margin call, substitution, and return demo flows with real workflow-to-adapter handoff evidence.
- Aggregate invariant evidence across those runtime-backed demo paths through make test-conformance and make demo-all.

### Prototype Scope Still Staged

- Production-grade custodian or issuer adapters beyond the narrow reference token path.
- Role-scoped disclosure profiles beyond the current workflow-party and provider-visible baseline.
- Workflow-coupled optimizer reservation and consent interfaces.
- Settlement-window enforcement and broader collateral business logic hardening.

## Invariant Output

| Check | Status | Detail |
| --- | --- | --- |
| AUTHORIZATION_AND_ROLE_CONTROL | PASS | Quickstart proved approval gates stayed on Canton before substitution settlement intent could be exposed, and an unauthorized return release attempt stayed blocked without any adapter-side movement. |
| ELIGIBILITY_DETERMINISM | PASS | Running the same policy and inventory inputs twice produced byte-equivalent deterministic policy evaluation output. |
| HAIRCUT_CORRECTNESS | PASS | The conformance haircut vector preserved the expected valuation basis, haircut schedule, and lendable-value arithmetic without hidden adjustments. |
| NO_DOUBLE_ENCUMBRANCE | PASS | Across the Quickstart posting, substitution, and return paths, final encumbrance and release evidence remained disjoint, blocked paths preserved incumbent scope, and adapter receipts stayed absent where workflow gates failed. |
| ATOMIC_SUBSTITUTION_WHEN_REQUIRED | PASS | The Quickstart substitution path either committed the full incumbent-release and replacement set atomically or preserved the incumbent encumbrances with zero adapter side effects. |
| REPLAY_SAFETY | PASS | The Quickstart return path settled the original release once, preserved the request identifier, and blocked the duplicate instruction without creating a second adapter receipt. |
| REPORT_FIDELITY | PASS | Every demo report references real generated artifacts, preserves scenario and workflow counts, and keeps machine-readable summaries aligned with the committed evidence files. |
| AUDIT_TRAIL_COMPLETENESS | PASS | Each positive flow records step-level workflow history, execution-report events, and top-level timeline entries that can be audited without hidden reconstruction. |

## Command Surface

- Primary Quickstart commands: `make localnet-start-control-plane, make localnet-run-token-adapter, make localnet-adapter-status, make demo-margin-call-quickstart, make demo-substitution-quickstart, make demo-return-quickstart, make test-conformance, make demo-all`
- Comparison-only commands: `make demo-margin-call, make demo-substitution, make demo-return, make verify-portable`
- Full verification commands: `make verify`

## Integration Surfaces

| Participant | Purpose | Outputs |
| --- | --- | --- |
| VENUE | Submit secured-finance obligations and consume machine-readable execution outcomes. | OptimizationReport, ExecutionReport, SubstitutionReport, ReturnReport |
| FINANCING_APP | Call policy evaluation, optimization, and workflow orchestration from a Canton-native lending or derivatives application. | PolicyEvaluationReport, OptimizationReport, workflow input payloads, execution evidence |
| TOKEN_ISSUER | Replace the reference adapter later by consuming workflow-declared settlement intent without taking over policy or workflow authority. | settlement intent references, execution reports, audit trail evidence |
| CUSTODIAN | Approve or reject control changes and confirm settlement-driven encumbrance updates. | approval-gated workflow states, execution-report event ids, audit-ready workflow steps |

## Artifact Counts

- Machine-readable artifacts: `64`
- Human-readable artifacts: `14`
- Artifact index: `docs/evidence/DEMO_ARTIFACT_INDEX.md`

