# Daml Mapping

## Purpose

This document maps the published collateral domain model and lifecycle vocabulary onto the first Daml package under `daml/CantonCollateral/`.

## Domain-To-Module Map

| Domain concept | Daml module | Daml form | Notes |
| --- | --- | --- | --- |
| parties and roles | `CantonCollateral.Roles` | `PartyRoleRegistration` template plus `PartyRole` enum | keeps role attribution explicit without granting hidden business authority |
| collateral asset abstraction | `CantonCollateral.Asset` | `CollateralAsset` data record | reusable reference record carried by lots and workflow inputs |
| collateral inventory lot | `CantonCollateral.Inventory` | `CollateralInventoryLot` template | provider-owned operational lot with custody and availability metadata |
| encumbrance state | `CantonCollateral.Encumbrance` | `EncumbranceState` template | tracks pledged, pending-release, and released overlays separate from policy |
| call obligation | `CantonCollateral.Obligation` | `CallObligation` template | models margin call creation and issuance state without embedding valuation logic |
| collateral posting intent | `CantonCollateral.Posting` | `CollateralPostingIntent` template | captures provider nomination, approval routing, settlement intent, and final encumbrance creation |
| substitution request | `CantonCollateral.Substitution` | `SubstitutionRequest` template | references encumbrances to release and lot allocations to pledge atomically |
| return request | `CantonCollateral.Return` | `ReturnRequest` template | captures release approval and return settlement intent separately from encumbrance state |
| settlement instruction | `CantonCollateral.Settlement` | `SettlementInstruction` template | explicit control or movement intent created by workflow choices |
| execution report | `CantonCollateral.Report` | `ExecutionReportRecord` template plus `ExecutionEvent` record | emitted from workflow transitions as state-derived evidence |
| shared state vocabulary | `CantonCollateral.Types` | shared records and enums | keeps lifecycle states, approval semantics, and policy references consistent across modules |

## Lifecycle Mapping

| Documented workflow | Daml template and choices | Current skeleton boundary |
| --- | --- | --- |
| margin call creation | `CallObligation.StartEvaluation`, `ConfirmShortfall`, `RouteForApproval`, `IssueCallWithoutApproval`, `ApproveCallIssuance` | closes on obligation issuance and emits an execution report |
| collateral posting intent | `CollateralPostingIntent.SubmitPostingIntent`, `StartPostingEvaluation`, `RecordFeasiblePosting`, approval choices, `ConfirmPostingSettlement` | creates separate settlement instruction and encumbrance contracts |
| substitution request | `SubstitutionRequest.SubmitSubstitutionRequest`, `StartSubstitutionEvaluation`, `RecordFeasibleSubstitution`, approval choices, `SubmitSubstitutionSettlementIntent`, `ConfirmSubstitutionSettlement` | archives released encumbrances and creates replacement encumbrances only on confirmed settlement |
| substitution rejection | `RejectSubstitutionBySecuredParty`, `RejectSubstitutionByCustodian` | emits rejection report without mutating encumbrance state |
| margin return request | `ReturnRequest.SubmitReturnRequest`, `StartReturnEvaluation`, `RecordFeasibleReturn`, approval choices, `SubmitReturnSettlementIntent`, `ConfirmReturnSettlement` | archives encumbrances only after return settlement confirmation |
| release or return settlement intent | `mkSettlementInstruction` plus workflow-owned settlement-confirmation and exception choices | keeps settlement intent visible as a separate artifact rather than a hidden field |

## Privacy And Stakeholder Intent

- Inventory lots are provider-signed contracts with explicit observer lists so unrelated inventory does not become visible to counterparties by default.
- Workflow requests carry explicit observer lists rather than relying on one global role visibility policy.
- Settlement instructions are separate contracts so custodians can receive the movement intent they need without becoming the authority over obligation creation.
- Execution reports are created from workflow choices and shared only with the workflow parties in scope for that path.

## Policy And Optimization Separation

- `PolicyContext` pins `policyVersion`, `snapshotId`, and `decisionReference` on-ledger.
- No Daml template in this package embeds eligibility schedules, haircut formulas, concentration rules, or optimization objectives.
- Off-ledger policy and optimization components remain advisory inputs; only Canton workflow choices mutate obligation, encumbrance, settlement, or report state.
