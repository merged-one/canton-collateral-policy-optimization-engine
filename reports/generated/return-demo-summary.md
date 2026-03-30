# Return Demo Summary

- Report ID: `rrr-5acf1d3fa870d789`
- Runtime mode: `IDE_LEDGER`
- Command: `make demo-return`
- Manifest: `examples/demo-scenarios/return/demo-config.json`
- Report artifact: `reports/generated/return-demo-report.json`

## Scenario Outcomes

| Scenario | Mode | Result | Blocked Phase | Adapter Outcome | Request | Replay | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| positive-return | POSITIVE | SUCCESS | - | NOT_REQUESTED | ret-request-positive | NOT_REQUESTED | The optimizer retained ret-current-fannie, ret-current-kfw and the Daml workflow closed the return for ret-current-ust. |
| negative-unauthorized-return | NEGATIVE | EXPECTED_FAILURE | WORKFLOW | NOT_REQUESTED | ret-request-unauthorized | NOT_REQUESTED | The workflow ended in state PendingSettlement with control checks APPROVAL_GATE_BLOCKED, UNAUTHORIZED_RETURN_BLOCKED. |
| negative-replayed-return-instruction | NEGATIVE | EXPECTED_FAILURE | WORKFLOW | NOT_REQUESTED | ret-request-replay | BLOCKED_DUPLICATE_RETURN_REQUEST | The workflow ended in state Closed with control checks APPROVAL_GATE_BLOCKED, REPLAY_RETURN_BLOCKED. |
| negative-obligation-state-mismatch | NEGATIVE | EXPECTED_FAILURE | WORKFLOW | NOT_REQUESTED | ret-request-mismatch | NOT_REQUESTED | The workflow ended in state UnderEvaluation with control checks OBLIGATION_STATE_MISMATCH_BLOCKED. |

## Invariant Checks

| Invariant | Status | Evidence | Note |
| --- | --- | --- | --- |
| PDR-001 | PASS | `reports/generated/positive-return-policy-evaluation-report.json` | The positive return path used a generated policy-evaluation report derived from declared inputs. |
| ALLOC-001 | PASS | `reports/generated/positive-return-optimization-report.json` | The optimizer selected the retained encumbered set deterministically and the returned lots were derived from that recommendation. |
| CTRL-001 | PASS | `reports/generated/negative-unauthorized-return-workflow-result.json`, `reports/generated/negative-replayed-return-instruction-workflow-result.json`, `reports/generated/negative-obligation-state-mismatch-workflow-result.json` | The return workflow blocked unauthorized release, replay, and obligation-state mismatch paths with explicit control checks instead of silently mutating encumbrance state. |
| ATOM-001 | PASS | `reports/generated/positive-return-workflow-result.json`, `reports/generated/negative-unauthorized-return-workflow-result.json`, `reports/generated/negative-replayed-return-instruction-workflow-result.json`, `reports/generated/negative-obligation-state-mismatch-workflow-result.json` | The positive path released only the selected encumbrances, while blocked return paths preserved the incumbent encumbrance set. |
| REPL-001 | PASS | `reports/generated/negative-replayed-return-instruction-workflow-result.json` | The replayed return instruction was rejected because the active return request identifier remained reserved after the committed release. |
| REPT-001 | PASS | `reports/generated/positive-return-workflow-result.json`, `reports/generated/positive-return-policy-evaluation-report.json`, `reports/generated/positive-return-optimization-report.json` | The return report references real workflow, policy, and optimization artifacts rather than operator-authored placeholders. |
| EXCP-001 | PASS | `reports/generated/negative-unauthorized-return-policy-evaluation-report.json`, `reports/generated/negative-unauthorized-return-optimization-report.json`, `reports/generated/negative-unauthorized-return-workflow-result.json`, `reports/generated/negative-replayed-return-instruction-policy-evaluation-report.json`, `reports/generated/negative-replayed-return-instruction-optimization-report.json`, `reports/generated/negative-replayed-return-instruction-workflow-result.json`, `reports/generated/negative-obligation-state-mismatch-policy-evaluation-report.json`, `reports/generated/negative-obligation-state-mismatch-optimization-report.json`, `reports/generated/negative-obligation-state-mismatch-workflow-result.json` | The negative return scenarios failed deterministically for unauthorized release, replayed return instruction, and obligation-state mismatch conditions. |
