# Asset Adapter Plan

## Objective

Define the staged path from the current normalized-inventory and workflow skeletons to a real token-standard-style asset integration that can support a confidential collateral demo without collapsing workflow authority into adapter code.

## Current Baseline

The repository already has:

- normalized inventory inputs for deterministic policy evaluation and optimization
- Daml workflow contracts for obligations, posting, substitution, return, encumbrance, settlement intent, and execution reporting
- a real Quickstart package deployment, seeded-scenario, and status-query path
- a first Quickstart-backed reference token adapter path that consumes settlement instructions, performs token-style movement, and emits adapter evidence
- architecture guidance that keeps asset issuance and raw ownership outside the Control Plane

The repository does not yet have:

- a live asset issuer integration
- a live custodian or control adapter
- a settlement callback contract implementation
- a production-grade adapter surface that spans posting, substitution, return, release, retries, and external custody APIs

## Adapter Principles

- asset applications remain authoritative for issuance, raw balances, and transfer mechanics
- the Control Plane remains authoritative for policy, optimization advice, workflow consent, and encumbrance intent
- adapters may normalize, submit, or acknowledge facts; they may not mutate authoritative workflow state off-ledger
- every adapter boundary must preserve lot provenance, custody location, control method, and valuation lineage

## Staged Adapter Delivery

### Stage 0: Plan And Pin

Status: implemented in this prompt

- document the LocalNet and adapter foundation
- keep sample inventory inputs explicit about what is normalized or synthetic
- defer live adapter code until the LocalNet package bridge is pinned

### Stage 1: Read-Only Inventory Adapter

Status: deferred

- ingest issuer or custodian facts and normalize them into `CollateralAsset` and `CollateralInventoryLot`
- preserve immutable source identifiers and as-of timestamps
- prove deterministic eligibility and concentration evaluation against that normalized feed

### Stage 2: Control-State Adapter

Status: deferred

- map custody holds, pledged accounts, escrow locks, or token freezes into `EncumbranceState`
- expose whether release requires issuer, custodian, or secured-party confirmation
- keep partial or exceptional states explicit rather than inferred

### Stage 3: Settlement-Intent Adapter

Status: partially implemented

- Prompt 15 now implements the first concrete reference path:
  - consume `SettlementInstruction` emitted by the posting workflow on Quickstart
  - map each allocation to a `ReferenceTokenHolding`
  - execute a token-style `MoveByCustodian`
  - emit `ReferenceTokenAdapterReceipt` plus `adapter-execution-report-v0.1`
- the current implementation is intentionally narrow:
  - posting-focused rather than substitution or return-complete
  - Quickstart-backed reference token movement rather than a production custodian API
  - evidence-bearing rather than a generic external integration bus

### Stage 4: Demo-Grade Multi-App Integration

Status: deferred

- connect one token issuer path, one custodian path, and one financing or margining application path to the same demo scenario
- preserve confidentiality boundaries across parties and applications on Canton
- generate real execution evidence without relying on fake operational shortcuts

## Minimum Adapter Contract Shape

| Surface | Minimum Fields |
| --- | --- |
| asset reference | `asset_id`, issuer, asset class, currency, denomination, settlement system, jurisdiction |
| holding facts | `lot_id`, owner party, custodian party, account reference, quantity, available quantity, effective time |
| control facts | control method, lock or hold identifier, segregated account reference, release requirement flags |
| valuation lineage | snapshot ID, source, as-of time, currency, asset facts digest |
| settlement callback | instruction ID, external transaction or hold ID, status, status time, failure reason if any |

## Integration Hooks For Canton Ecosystem Participants

| Participant Type | Expected Role In The Adapter Plan |
| --- | --- |
| venues | receive or originate venue-specific settlement and return acknowledgments |
| financing apps | request policy evaluation, optimization, and workflow initiation while leaving settlement authority outside the app |
| token issuers | provide token metadata, balances, freezes or lock states, and transfer or unlock actions |
| custodians | provide account provenance, control acknowledgments, and release confirmations |
| margining applications | provide obligation issuance, consent context, and report consumers for exposure workflows |

## Assumptions, Mocked Surfaces, And Deferrals

| Area | Current Position |
| --- | --- |
| normalized inventory JSON | assumed as the read-only adapter output for now |
| settlement callbacks | deferred until `SettlementInstruction` consumption is pinned |
| cross-app identity mapping | deferred until the Quickstart package bridge and party model are pinned |
| Daml Finance-style compatibility | still a target, but not the first reference path in this prompt |
| production-grade retries and replay hardening | deferred until the first live adapter exists |

## Exit Criteria For The First Live Adapter

- one real upstream source can populate normalized inventory lots without hand edits
- one control-state signal can be mapped into `EncumbranceState`
- one settlement action can be acknowledged back into workflow state through explicit callbacks
- the adapter boundary is documented well enough that venues, financing apps, token issuers, custodians, and margining applications can see where their responsibilities start and stop

Prompt 15 satisfies the third criterion for a narrow reference path by proving one real settlement action on Quickstart with explicit adapter evidence.
