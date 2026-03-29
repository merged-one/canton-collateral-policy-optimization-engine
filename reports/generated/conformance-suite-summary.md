# Conformance Suite Summary

- Suite ID: `csr-76c28d948047e880`
- Command: `make test-conformance`
- Overall status: `PASS`
- Scenario coverage: `13` total / `3` positive / `10` negative

## Checks

| Check | Status | Invariants | Evidence | Detail |
| --- | --- | --- | --- | --- |
| AUTHORIZATION_AND_ROLE_CONTROL | PASS | `AUTH-001`, `CTRL-001`, `WF-001` | `reports/generated/negative-unauthorized-release-workflow-result.json`, `reports/generated/negative-unauthorized-return-workflow-result.json` | Unauthorized substitution release and return release attempts were blocked by approval and role controls without changing the incumbent encumbrance set. |
| ELIGIBILITY_DETERMINISM | PASS | `ELIG-001`, `PDR-001` | `reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json` | Running the same policy and inventory inputs twice produced byte-equivalent deterministic policy evaluation output. |
| HAIRCUT_CORRECTNESS | PASS | `HAIR-001` | `reports/generated/conformance-haircut-policy-evaluation-report.json` | The conformance haircut vector preserved the expected valuation basis, haircut schedule, and lendable-value arithmetic without hidden adjustments. |
| NO_DOUBLE_ENCUMBRANCE | PASS | `ENC-001`, `CTRL-001` | `reports/generated/positive-margin-call-workflow-result.json`, `reports/generated/positive-substitution-workflow-result.json`, `reports/generated/negative-unauthorized-release-workflow-result.json`, `reports/generated/positive-return-workflow-result.json`, `reports/generated/negative-unauthorized-return-workflow-result.json` | Across posting, substitution, and return flows the suite preserved disjoint encumbrance sets and blocked state changes that would overlap or duplicate collateral commitments. |
| ATOMIC_SUBSTITUTION_WHEN_REQUIRED | PASS | `ATOM-001`, `CTRL-001` | `reports/generated/positive-substitution-workflow-result.json`, `reports/generated/negative-partial-substitution-workflow-result.json`, `reports/generated/negative-unauthorized-release-workflow-result.json` | When full replacement is required, substitution either commits the new set atomically or leaves the incumbent encumbrances untouched. |
| REPLAY_SAFETY | PASS | `REPL-001` | `reports/generated/negative-replayed-return-instruction-workflow-result.json` | The return workflow committed the original release once and then blocked a replayed instruction using the same request identifier. |
| REPORT_FIDELITY | PASS | `REPT-001`, `PDR-001` | `reports/generated/margin-call-demo-execution-report.json`, `reports/generated/margin-call-demo-summary.md`, `reports/generated/margin-call-demo-timeline.md`, `reports/generated/return-demo-report.json`, `reports/generated/return-demo-summary.md`, `reports/generated/return-demo-timeline.md`, `reports/generated/substitution-demo-report.json`, `reports/generated/substitution-demo-summary.md`, `reports/generated/substitution-demo-timeline.md` | Every demo report references real generated artifacts, preserves scenario and workflow counts, and keeps machine-readable summaries aligned with the committed evidence files. |
| AUDIT_TRAIL_COMPLETENESS | PASS | `AUD-001` | `reports/generated/margin-call-demo-execution-report.json`, `reports/generated/margin-call-demo-summary.md`, `reports/generated/margin-call-demo-timeline.md`, `reports/generated/return-demo-report.json`, `reports/generated/return-demo-summary.md`, `reports/generated/return-demo-timeline.md`, `reports/generated/substitution-demo-report.json`, `reports/generated/substitution-demo-summary.md`, `reports/generated/substitution-demo-timeline.md` | Each positive flow records step-level workflow history, execution-report events, and top-level timeline entries that can be audited without hidden reconstruction. |

## Demo Reports

| Demo | Report Type | Positive | Negative | Report |
| --- | --- | --- | --- | --- |
| CONFIDENTIAL_MARGIN_CALL | ExecutionReport | positive-margin-call | negative-ineligible-asset, negative-insufficient-lendable-value, negative-expired-policy-window | `reports/generated/margin-call-demo-execution-report.json` |
| CONFIDENTIAL_COLLATERAL_SUBSTITUTION | SubstitutionReport | positive-substitution | negative-replacement-becomes-ineligible, negative-concentration-breach, negative-unauthorized-release, negative-partial-substitution | `reports/generated/substitution-demo-report.json` |
| CONFIDENTIAL_MARGIN_RETURN | ReturnReport | positive-return | negative-unauthorized-return, negative-replayed-return-instruction, negative-obligation-state-mismatch | `reports/generated/return-demo-report.json` |
