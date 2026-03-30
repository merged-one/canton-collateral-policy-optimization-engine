# Conformance Suite Summary

- Suite ID: `csr-d7e4b4c29646d5d4`
- Command: `make test-conformance`
- Overall status: `PASS`
- Runtime modes: `QUICKSTART`
- Scenario coverage: `10` total / `3` positive / `7` negative
- Quickstart deployment receipt: `reports/generated/localnet-control-plane-deployment-receipt.json`
- Reference adapter execution report: `reports/generated/localnet-reference-token-adapter-execution-report.json`

## Checks

| Check | Status | Invariants | Evidence | Detail |
| --- | --- | --- | --- | --- |
| AUTHORIZATION_AND_ROLE_CONTROL | PASS | `AUTH-001`, `CTRL-001`, `WF-001` | `reports/generated/negative-unauthorized-return-quickstart-workflow-result.json`, `reports/generated/negative-unauthorized-return-quickstart/localnet-return-status.json`, `reports/generated/positive-substitution-quickstart-workflow-result.json`, `reports/generated/positive-substitution-quickstart/localnet-control-plane-seed-receipt.json` | Quickstart proved approval gates stayed on Canton before substitution settlement intent could be exposed, and an unauthorized return release attempt stayed blocked without any adapter-side movement. |
| ELIGIBILITY_DETERMINISM | PASS | `ELIG-001`, `PDR-001` | `reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json` | Running the same policy and inventory inputs twice produced byte-equivalent deterministic policy evaluation output. |
| HAIRCUT_CORRECTNESS | PASS | `HAIR-001` | `reports/generated/conformance-haircut-policy-evaluation-report.json` | The conformance haircut vector preserved the expected valuation basis, haircut schedule, and lendable-value arithmetic without hidden adjustments. |
| NO_DOUBLE_ENCUMBRANCE | PASS | `ENC-001`, `CTRL-001` | `reports/generated/negative-partial-substitution-quickstart-workflow-result.json`, `reports/generated/negative-partial-substitution-quickstart/localnet-substitution-status.json`, `reports/generated/negative-unauthorized-return-quickstart-workflow-result.json`, `reports/generated/negative-unauthorized-return-quickstart/localnet-return-status.json`, `reports/generated/positive-margin-call-quickstart-workflow-result.json`, `reports/generated/positive-margin-call-quickstart/localnet-reference-token-adapter-execution-report.json`, `reports/generated/positive-margin-call-quickstart/localnet-reference-token-adapter-status.json`, `reports/generated/positive-return-quickstart-workflow-result.json`, `reports/generated/positive-return-quickstart/localnet-return-adapter-execution-report.json`, `reports/generated/positive-return-quickstart/localnet-return-status.json`, `reports/generated/positive-substitution-quickstart-workflow-result.json`, `reports/generated/positive-substitution-quickstart/localnet-substitution-adapter-execution-report.json`, `reports/generated/positive-substitution-quickstart/localnet-substitution-status.json` | Across the Quickstart posting, substitution, and return paths, final encumbrance and release evidence remained disjoint, blocked paths preserved incumbent scope, and adapter receipts stayed absent where workflow gates failed. |
| ATOMIC_SUBSTITUTION_WHEN_REQUIRED | PASS | `ATOM-001`, `CTRL-001` | `reports/generated/negative-partial-substitution-quickstart-workflow-result.json`, `reports/generated/negative-partial-substitution-quickstart/localnet-substitution-status.json`, `reports/generated/positive-substitution-quickstart-workflow-result.json`, `reports/generated/positive-substitution-quickstart/localnet-substitution-adapter-execution-report.json`, `reports/generated/positive-substitution-quickstart/localnet-substitution-status.json` | The Quickstart substitution path either committed the full incumbent-release and replacement set atomically or preserved the incumbent encumbrances with zero adapter side effects. |
| REPLAY_SAFETY | PASS | `REPL-001` | `reports/generated/negative-replayed-return-instruction-quickstart-workflow-result.json`, `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-adapter-execution-report.json`, `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-status.json` | The Quickstart return path settled the original release once, preserved the request identifier, and blocked the duplicate instruction without creating a second adapter receipt. |
| REPORT_FIDELITY | PASS | `REPT-001`, `PDR-001` | `reports/generated/localnet-control-plane-deployment-receipt.json`, `reports/generated/localnet-reference-token-adapter-execution-report.json`, `reports/generated/localnet-reference-token-adapter-status.json`, `reports/generated/margin-call-quickstart-execution-report.json`, `reports/generated/margin-call-quickstart-summary.md`, `reports/generated/margin-call-quickstart-timeline.md`, `reports/generated/return-quickstart-report.json`, `reports/generated/return-quickstart-summary.md`, `reports/generated/return-quickstart-timeline.md`, `reports/generated/substitution-quickstart-report.json`, `reports/generated/substitution-quickstart-summary.md`, `reports/generated/substitution-quickstart-timeline.md` | Every demo report references real generated artifacts, preserves scenario and workflow counts, and keeps machine-readable summaries aligned with the committed evidence files. |
| AUDIT_TRAIL_COMPLETENESS | PASS | `AUD-001` | `reports/generated/margin-call-quickstart-execution-report.json`, `reports/generated/margin-call-quickstart-summary.md`, `reports/generated/margin-call-quickstart-timeline.md`, `reports/generated/return-quickstart-report.json`, `reports/generated/return-quickstart-summary.md`, `reports/generated/return-quickstart-timeline.md`, `reports/generated/substitution-quickstart-report.json`, `reports/generated/substitution-quickstart-summary.md`, `reports/generated/substitution-quickstart-timeline.md` | Each positive flow records step-level workflow history, execution-report events, and top-level timeline entries that can be audited without hidden reconstruction. |

## Runtime Evidence

| Surface | Command | Artifact |
| --- | --- | --- |
| Quickstart deployment | `make localnet-start-control-plane` | `reports/generated/localnet-control-plane-deployment-receipt.json` |
| Reference adapter path | `make localnet-run-token-adapter` | `reports/generated/localnet-reference-token-adapter-execution-report.json` |
| Reference adapter status | `make localnet-adapter-status` | `reports/generated/localnet-reference-token-adapter-status.json` |

## Demo Reports

| Demo | Report Type | Runtime | Positive | Negative | Report |
| --- | --- | --- | --- | --- | --- |
| CONFIDENTIAL_MARGIN_CALL | ExecutionReport | QUICKSTART | positive-margin-call-quickstart | negative-ineligible-asset-quickstart, negative-workflow-rejected-quickstart | `reports/generated/margin-call-quickstart-execution-report.json` |
| CONFIDENTIAL_COLLATERAL_SUBSTITUTION | SubstitutionReport | QUICKSTART | positive-substitution-quickstart | negative-replacement-becomes-ineligible-quickstart, negative-partial-substitution-quickstart | `reports/generated/substitution-quickstart-report.json` |
| CONFIDENTIAL_MARGIN_RETURN | ReturnReport | QUICKSTART | positive-return-quickstart | negative-unauthorized-return-quickstart, negative-replayed-return-instruction-quickstart, negative-obligation-state-mismatch-quickstart | `reports/generated/return-quickstart-report.json` |
