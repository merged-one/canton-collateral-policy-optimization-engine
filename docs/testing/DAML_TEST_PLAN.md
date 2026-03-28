# Daml Test Plan

## Purpose

This plan defines the first executable checks for the Daml package boundary under `daml/CantonCollateral/`.

## Reproducible Commands

```sh
make daml-build
make daml-test
make demo-run
```

## Script Coverage

| Script | Scope | Invariants touched |
| --- | --- | --- |
| `CantonCollateral.Test:marginCallLifecycleTest` | margin call creation, approval gating, execution-report emission | `AUTH-001`, `WF-001`, `REPT-001`, `AUD-001` |
| `CantonCollateral.Test:postingAndSubstitutionLifecycleTest` | posting intent, approval routing, settlement, substitution approval, substitution rejection, encumbrance replacement | `CTRL-001`, `ENC-001`, `ATOM-001`, `WF-001`, `REPT-001` |
| `CantonCollateral.Test:returnLifecycleTest` | return request approval and settlement-confirmed release path | `CTRL-001`, `ATOM-001`, `WF-001`, `REPT-001` |
| `Bootstrap:workflowSmokeTest` | aggregate smoke run over the three lifecycle scripts | command-surface validation and operator reproducibility |

## Positive Paths

- margin call creation reaches `Closed` only after issuance or explicit approval
- posting creates an explicit `SettlementInstruction` before encumbrances are committed
- substitution archives released encumbrances and creates replacement encumbrances only when settlement is confirmed
- return workflow releases encumbrances only after return settlement confirmation

## Negative Paths

- posting can be rejected by secured party or custodian before settlement
- substitution can be rejected without mutating the currently pledged encumbrance set
- settlement exception choices keep the workflow in `ExceptionOpen` rather than fabricating success

## Current Limits

- the scripts use pinned policy references, not a live policy engine
- privacy is checked structurally through stakeholder choices and query scope, not yet through a full disclosure-profile suite
- replay, expiry, temporal, and concentration-limit scenarios remain future work
