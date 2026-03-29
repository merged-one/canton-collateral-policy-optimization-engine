# Return Demo Timeline

## Execution Phases

| Seq | Scenario | Phase | Status | Artifact | Detail |
| --- | --- | --- | --- | --- | --- |
| 1 | positive-return | POLICY_EVALUATION | COMPLETED | `reports/generated/positive-return-policy-evaluation-report.json` | Evaluated currently encumbered collateral for positive scenario with overall decision ACCEPT. |
| 2 | positive-return | OPTIMIZATION | COMPLETED | `reports/generated/positive-return-optimization-report.json` | Optimized the retained encumbered set for scenario positive-return with optimizer action SUBSTITUTE. |
| 3 | positive-return | WORKFLOW | COMPLETED | `reports/generated/positive-return-workflow-result.json` | Recorded the Daml return workflow for scenario positive-return and confirmed settlement-driven encumbrance release. |
| 4 | negative-unauthorized-return | POLICY_EVALUATION | COMPLETED | `reports/generated/negative-unauthorized-return-policy-evaluation-report.json` | Evaluated currently encumbered collateral for negative scenario with overall decision ACCEPT. |
| 5 | negative-unauthorized-return | OPTIMIZATION | COMPLETED | `reports/generated/negative-unauthorized-return-optimization-report.json` | Optimized the retained encumbered set for scenario negative-unauthorized-return with optimizer action SUBSTITUTE. |
| 6 | negative-unauthorized-return | WORKFLOW | COMPLETED | `reports/generated/negative-unauthorized-return-workflow-result.json` | Recorded the Daml return control failure for scenario negative-unauthorized-return with workflow state PendingSettlement. |
| 7 | negative-replayed-return-instruction | POLICY_EVALUATION | COMPLETED | `reports/generated/negative-replayed-return-instruction-policy-evaluation-report.json` | Evaluated currently encumbered collateral for negative scenario with overall decision ACCEPT. |
| 8 | negative-replayed-return-instruction | OPTIMIZATION | COMPLETED | `reports/generated/negative-replayed-return-instruction-optimization-report.json` | Optimized the retained encumbered set for scenario negative-replayed-return-instruction with optimizer action SUBSTITUTE. |
| 9 | negative-replayed-return-instruction | WORKFLOW | COMPLETED | `reports/generated/negative-replayed-return-instruction-workflow-result.json` | Recorded the Daml return workflow for scenario negative-replayed-return-instruction, settled the original return, and blocked a replayed instruction. |
| 10 | negative-obligation-state-mismatch | POLICY_EVALUATION | COMPLETED | `reports/generated/negative-obligation-state-mismatch-policy-evaluation-report.json` | Evaluated currently encumbered collateral for negative scenario with overall decision ACCEPT. |
| 11 | negative-obligation-state-mismatch | OPTIMIZATION | COMPLETED | `reports/generated/negative-obligation-state-mismatch-optimization-report.json` | Optimized the retained encumbered set for scenario negative-obligation-state-mismatch with optimizer action SUBSTITUTE. |
| 12 | negative-obligation-state-mismatch | WORKFLOW | COMPLETED | `reports/generated/negative-obligation-state-mismatch-workflow-result.json` | Recorded the Daml return control failure for scenario negative-obligation-state-mismatch with workflow state UnderEvaluation. |

## Positive Workflow Steps

| Step | Phase | Actor | State | Detail |
| --- | --- | --- | --- | --- |
| 1 | BASELINE | provider | Encumbered | provider started from an already pledged collateral set |
| 2 | RETURN | provider | Draft | provider created the draft return request |
| 3 | RETURN | provider | Submitted | provider submitted the return request |
| 4 | RETURN | provider | UnderEvaluation | provider moved the return request into evaluation |
| 5 | RETURN | provider | PendingApproval | provider recorded a feasible return after confirming the release condition against the selected retained set |
| 6 | CONTROL | provider | Blocked | provider could not create the settlement intent before the required approvals were recorded |
| 7 | RETURN | secured-party | PendingApproval | secured party approved the return request |
| 8 | RETURN | custodian | Approved | custodian approved the return request |
| 9 | SETTLEMENT | provider | PendingSettlement | provider submitted the approved return settlement intent for the selected release lots |
| 10 | SETTLEMENT | custodian | Closed | custodian confirmed settlement and the selected encumbrances moved to released state |
