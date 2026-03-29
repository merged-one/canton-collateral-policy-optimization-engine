# Token Standard Alignment

## Objective

Describe how the Control Plane will represent collateral assets so that token-standard-style Canton projects and adjacent asset applications can integrate later without rewriting the control-plane model.

## Alignment Principles

- the Control Plane should reference tokenized assets through stable interfaces rather than embedding one specific token implementation
- asset ownership and transfer semantics belong to the asset application or adapter, not to the policy engine
- encumbrance and collateral-control semantics belong to the control plane and must be representable even when the underlying asset standard models ownership differently
- the prototype should simplify where necessary, but each simplification must be explicit

## Canonical Representation

| Concern | Control Plane Representation | Expected Token-Standard-Style Mapping |
| --- | --- | --- |
| asset identity | `CollateralAsset` with `asset_id`, issuer, class, currency, and adapter reference | token or instrument identifier exposed by the asset application |
| holding or position | `CollateralInventoryLot` with owner, custodian, account, quantity, and provenance; the current reference adapter uses `ReferenceTokenHolding` as the asset-side movement surface | token balance, position contract, or custody entitlement mapped into lot form |
| control or lock state | `EncumbranceState` and control metadata | token lock, escrow, custody control account, or adapter-managed hold |
| valuation inputs | `ValuationSnapshot` | off-ledger market data and static asset facts referenced by the asset application |
| movement intent | `SettlementInstruction` | transfer, control change, lock, unlock, or return call on the asset application |
| workflow evidence | `ExecutionReport` plus adapter-side receipts such as `ReferenceTokenAdapterReceipt` | external report keyed by workflow and asset identifiers rather than a token-side report |

## Required Integration Interfaces

| Interface | Minimum Fields |
| --- | --- |
| asset reference interface | `asset_id`, issuer, asset class, currency, denomination, jurisdiction, settlement system, transferability flags |
| holding interface | `lot_id`, owner party, custodian party, account reference, quantity, available quantity, effective time |
| control interface | control method, segregation or pledge account reference, release requirement flags |
| settlement adapter interface | instruction ID, source, destination, quantity, asset reference, deadline, status callback |
| valuation interface | snapshot ID, as-of time, price source, FX source, asset facts digest |

## Prototype Assumptions

- the asset application remains the source of truth for issuance and raw ownership
- the Control Plane consumes normalized asset and holding facts through an adapter layer
- one `CollateralAsset` may correspond to many lots with different custody accounts or provenance
- encumbrance is modeled as a control-plane overlay, not as a mutation of policy schedules
- asset transfers may initially be represented as instruction emission plus status callback rather than a live external settlement integration

## Current Reference Path

The current Quickstart-backed reference adapter proves one concrete token-standard-style mapping:

- the workflow package emits `SettlementInstruction` with `allocationsInScope`
- the adapter maps each allocation into `ReferenceTokenHolding`
- `MoveByCustodian` performs the token-style movement from provider account to secured account
- `ReferenceTokenAdapterReceipt` and `adapter-execution-report-v0.1` carry the adapter evidence back into the reporting surface

This path is intentionally reference-grade. It demonstrates the boundary shape without claiming a production custodian or issuer integration.

## Intentional Simplifications

| Area | Simplification | Why It Is Acceptable Now |
| --- | --- | --- |
| corporate actions | ignore coupon, dividend, and event-processing complexity in the first prototype | architecture and workflow boundaries can be specified without full servicing logic |
| legal agreement detail | model rights through policy schedules and approval rules rather than full legal-document parsing | keeps the control-plane contract clear while leaving room for richer legal integration later |
| settlement venues | treat settlement venue as a reference attribute rather than a full venue-specific workflow library | allows future adapters without locking the architecture now |
| partial fail management | treat failed movement as an exception path instead of modeling detailed partial settlement states in the first design pass | preserves safety without premature workflow complexity |
| multi-domain routing | assume a single LocalNet domain in the prototype | keeps topology compatible with Quickstart while leaving room for later expansion |

## Future Compatibility Targets

- token-standard-style Canton assets should map into the asset and holding interfaces without changing policy schedule semantics
- other Canton projects should be able to consume `ExecutionReport` and `SettlementInstruction` artifacts without needing direct access to internal templates
- Daml Finance-style or custom asset models should plug in through the same adapter boundaries where feasible
- future asset adapters should preserve lot-level provenance, custody location, and control status so concentration and eligibility rules remain portable

## Non-Goals

- defining a new universal asset token standard in this repository
- forcing every future integrator to adopt one Daml package layout
- modeling issuance, trading, or servicing logic that belongs in an asset platform rather than the collateral control plane
- treating the current reference token adapter as a generic external integration bus
