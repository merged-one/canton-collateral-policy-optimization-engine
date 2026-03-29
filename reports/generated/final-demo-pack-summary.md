# Final Demo Pack Summary

- Demo pack ID: `fdp-3ef235fefb11f2eb`
- Command: `make demo-all`
- Overall status: `PASS`
- Conformance report: `reports/generated/conformance-suite-report.json`

## Demo Flows

| Demo | Report Type | Command | Positive | Negative | Report |
| --- | --- | --- | --- | --- | --- |
| CONFIDENTIAL_MARGIN_CALL | ExecutionReport | `make demo-margin-call` | positive-margin-call | negative-ineligible-asset, negative-insufficient-lendable-value, negative-expired-policy-window | `reports/generated/margin-call-demo-execution-report.json` |
| CONFIDENTIAL_COLLATERAL_SUBSTITUTION | SubstitutionReport | `make demo-substitution` | positive-substitution | negative-replacement-becomes-ineligible, negative-concentration-breach, negative-unauthorized-release, negative-partial-substitution | `reports/generated/substitution-demo-report.json` |
| CONFIDENTIAL_MARGIN_RETURN | ReturnReport | `make demo-return` | positive-return | negative-unauthorized-return, negative-replayed-return-instruction, negative-obligation-state-mismatch | `reports/generated/return-demo-report.json` |

## Invariant Output

| Check | Status | Detail |
| --- | --- | --- |
| AUTHORIZATION_AND_ROLE_CONTROL | PASS | Unauthorized substitution release and return release attempts were blocked by approval and role controls without changing the incumbent encumbrance set. |
| ELIGIBILITY_DETERMINISM | PASS | Running the same policy and inventory inputs twice produced byte-equivalent deterministic policy evaluation output. |
| HAIRCUT_CORRECTNESS | PASS | The conformance haircut vector preserved the expected valuation basis, haircut schedule, and lendable-value arithmetic without hidden adjustments. |
| NO_DOUBLE_ENCUMBRANCE | PASS | Across posting, substitution, and return flows the suite preserved disjoint encumbrance sets and blocked state changes that would overlap or duplicate collateral commitments. |
| ATOMIC_SUBSTITUTION_WHEN_REQUIRED | PASS | When full replacement is required, substitution either commits the new set atomically or leaves the incumbent encumbrances untouched. |
| REPLAY_SAFETY | PASS | The return workflow committed the original release once and then blocked a replayed instruction using the same request identifier. |
| REPORT_FIDELITY | PASS | Every demo report references real generated artifacts, preserves scenario and workflow counts, and keeps machine-readable summaries aligned with the committed evidence files. |
| AUDIT_TRAIL_COMPLETENESS | PASS | Each positive flow records step-level workflow history, execution-report events, and top-level timeline entries that can be audited without hidden reconstruction. |

## Integration Surfaces

| Participant | Purpose | Outputs |
| --- | --- | --- |
| VENUE | Submit secured-finance obligations and consume machine-readable execution outcomes. | OptimizationReport, ExecutionReport, SubstitutionReport, ReturnReport |
| FINANCING_APP | Call policy evaluation, optimization, and workflow orchestration from a Canton-native lending or derivatives application. | PolicyEvaluationReport, OptimizationReport, workflow input payloads, execution evidence |
| TOKEN_ISSUER | Honor settlement and encumbrance state changes without taking over policy or workflow authority. | settlement intent references, execution reports, audit trail evidence |
| CUSTODIAN | Approve or reject control changes and confirm settlement-driven encumbrance updates. | approval-gated workflow states, execution-report event ids, audit-ready workflow steps |

## Artifact Counts

- Machine-readable artifacts: `46`
- Human-readable artifacts: `11`
- Artifact index: `docs/evidence/DEMO_ARTIFACT_INDEX.md`

