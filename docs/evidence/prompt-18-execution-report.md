# Prompt 18 Execution Report

## Summary

Prompt 18 wires the confidential return demo through Quickstart and the reference token adapter so the Control Plane can prove:

- approval-gated release on the real runtime path
- replay-safe duplicate return handling after the original release settles
- blocked unauthorized release with no adapter side effects
- blocked stale-coverage handling with no adapter side effects

## Commands

The Prompt 18 implementation work uses these reproducible commands:

```sh
make demo-return
make demo-return-quickstart
make docs-lint
sh -n scripts/build-quickstart-dar.sh
python3 -m py_compile app/orchestration/return_demo.py app/orchestration/return_cli.py
git diff --check
```

## Outcomes

- `make demo-return` passed and regenerated `reports/generated/return-demo-report.json` on the IDE-ledger comparison path.
- `make demo-return-quickstart` passed and validated:
  - `reports/generated/return-quickstart-report.json`
  - `reports/generated/return-quickstart-summary.md`
  - `reports/generated/return-quickstart-timeline.md`
- `make docs-lint` passed after the Quickstart return docs, ADR, tracker, evidence, and command-surface updates landed.
- `sh -n scripts/build-quickstart-dar.sh`, `python3 -m py_compile ...`, and `git diff --check` all passed.

## Quickstart Run Evidence

The final accepted Quickstart return scenario ids are the fresh `831` positive path, `841` unauthorized-release path, `851` replay path, and `861` stale-coverage mismatch path. Those ids replaced the original debug range so the acceptance run would execute against clean scenario-scoped state on the existing LocalNet.

Positive Quickstart artifacts:

- `reports/generated/positive-return-quickstart-policy-evaluation-report.json`
- `reports/generated/positive-return-quickstart-optimization-report.json`
- `reports/generated/positive-return-quickstart-workflow-input.json`
- `reports/generated/positive-return-quickstart-workflow-result.json`
- `reports/generated/positive-return-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/positive-return-quickstart/localnet-return-adapter-execution-report.json`
- `reports/generated/positive-return-quickstart/localnet-return-status.json`

The positive Quickstart path proves:

- request identifier `quickstart-return-request-831`
- approval state `ApprovalGranted` for both secured-party and custodian approvals with `workflowGate = PREPARE_FOR_ADAPTER`
- release action `ReturnCollateral` against settlement instruction `quickstart-return-correlation-831-instruction`
- one adapter movement for lot `quickstart-ret-current-ust-831`
- final post-return state `Closed` with settlement instruction state `Settled`
- one provider-visible adapter receipt
- returned lot and holding `quickstart-ret-current-ust-831`
- remaining encumbered and secured lots `quickstart-ret-current-fannie-831` and `quickstart-ret-current-kfw-831`

Unauthorized-release negative artifacts:

- `reports/generated/negative-unauthorized-return-quickstart-policy-evaluation-report.json`
- `reports/generated/negative-unauthorized-return-quickstart-optimization-report.json`
- `reports/generated/negative-unauthorized-return-quickstart-workflow-input.json`
- `reports/generated/negative-unauthorized-return-quickstart-workflow-result.json`
- `reports/generated/negative-unauthorized-return-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-unauthorized-return-quickstart/localnet-return-status.json`

The unauthorized path proves:

- request identifier `quickstart-return-request-841`
- control checks `APPROVAL_GATE_BLOCKED` and `UNAUTHORIZED_RETURN_BLOCKED`
- workflow state remained `PendingSettlement`
- no adapter execution artifact was produced
- provider-visible adapter receipt count remained `0`
- all incumbent encumbrances and holdings stayed pledged or settled to the secured account

Replay-safe negative artifacts:

- `reports/generated/negative-replayed-return-instruction-quickstart-policy-evaluation-report.json`
- `reports/generated/negative-replayed-return-instruction-quickstart-optimization-report.json`
- `reports/generated/negative-replayed-return-instruction-quickstart-workflow-input.json`
- `reports/generated/negative-replayed-return-instruction-quickstart-workflow-result.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-adapter-execution-report.json`
- `reports/generated/negative-replayed-return-instruction-quickstart/localnet-return-status.json`

Replay safety is evidenced by:

- original request identifier `quickstart-return-request-851`
- adapter replay handling result `BLOCKED_DUPLICATE_RETURN_REQUEST`
- replay control check id `REPLAY_RETURN_BLOCKED`
- replay detail: the workflow preserved the active request identifier after the original Quickstart release settled
- only one provider-visible adapter receipt remained visible after the replay attempt
- only the original approved lot `quickstart-ret-current-ust-851` was returned
- remaining encumbered lots `quickstart-ret-current-fannie-851` and `quickstart-ret-current-kfw-851` stayed pledged

Stale-coverage mismatch negative artifacts:

- `reports/generated/negative-obligation-state-mismatch-quickstart-policy-evaluation-report.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart-optimization-report.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart-workflow-input.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart-workflow-result.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart/localnet-control-plane-seed-receipt.json`
- `reports/generated/negative-obligation-state-mismatch-quickstart/localnet-return-status.json`

The stale-coverage path proves:

- request identifier `quickstart-return-request-861`
- control check `OBLIGATION_STATE_MISMATCH_BLOCKED`
- workflow state remained `UnderEvaluation`
- no settlement instruction was created
- provider-visible adapter receipt count remained `0`
- all incumbent encumbrances and holdings stayed pledged or settled to the secured account

## Evidence Added

- ADR: [docs/adrs/0021-quickstart-return-demo-orchestration.md](../adrs/0021-quickstart-return-demo-orchestration.md)
- Quickstart Daml Script layer: [daml/CantonCollateral/QuickstartReturn.daml](../../daml/CantonCollateral/QuickstartReturn.daml)
- Quickstart return commands:
  - [scripts/localnet-seed-return-demo.sh](../../scripts/localnet-seed-return-demo.sh)
  - [scripts/localnet-run-return-workflow.sh](../../scripts/localnet-run-return-workflow.sh)
  - [scripts/localnet-run-return-token-adapter.sh](../../scripts/localnet-run-return-token-adapter.sh)
  - [scripts/localnet-return-status.sh](../../scripts/localnet-return-status.sh)
- Quickstart scenario manifests:
  - [examples/demo-scenarios/return/quickstart-demo-config.json](../../examples/demo-scenarios/return/quickstart-demo-config.json)
  - [infra/quickstart/scenarios/confidential-return-demo-positive-scenario.json](../../infra/quickstart/scenarios/confidential-return-demo-positive-scenario.json)
- Expanded report contract:
  - [app/orchestration/return_demo.py](../../app/orchestration/return_demo.py)
  - [reports/schemas/return-report.schema.json](../../reports/schemas/return-report.schema.json)
- Quickstart DAR cache guard:
  - [scripts/build-quickstart-dar.sh](../../scripts/build-quickstart-dar.sh)

## Runtime Notes

- The shared Daml package version was bumped from `0.1.8` to `0.1.10` while the Quickstart return path was being stabilized so the updated DAR could be redeployed without package-version drift.
- `scripts/build-quickstart-dar.sh` now reuses a current Quickstart DAR when the runtime metadata and Daml sources have not changed, which keeps the repeated Quickstart return script invocations practical without weakening determinism.
- Final packaging remains future work: `make demo-all` and the aggregate conformance suite still need to absorb the Quickstart-backed return artifact set and its packaging narrative.
