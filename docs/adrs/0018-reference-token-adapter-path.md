# ADR 0018: Implement The First Quickstart-Backed Reference Token Adapter Path

- Status: Accepted
- Date: 2026-03-29

## Context

ADR 0017 established a real confidential Quickstart scenario with seeded obligations, inventory lots, role registrations, and posting intent state. That left one explicit gap between the Control Plane and something another Canton project could actually integrate with: there was still no concrete asset-side adapter path consuming real workflow outputs and producing execution evidence.

Prompt 15 requires the first such path to be narrow and explicit:

- the Control Plane must keep ownership of policy, optimization, workflow authority, and report generation
- the adapter must own only the asset or network side action surface
- the first implementation must be reference-grade rather than a generic external integration bus or a production custodian abstraction
- the adapter must emit evidence that can be carried into execution reporting

## Decision

Implement the first concrete adapter path as a Quickstart-backed reference token adapter that consumes Control Plane settlement and control artifacts and performs a token-style movement inside the same LocalNet.

The concrete boundary is:

1. The Control Plane remains authoritative for workflow state:
   - `CollateralPostingIntent`
   - `SettlementInstruction`
   - `EncumbranceState`
   - `ExecutionReportRecord`
2. The adapter consumes, but does not reinterpret:
   - the posted `SettlementInstruction`
   - the lot-level `allocationsInScope`
   - the obligation, correlation, asset, and account references carried by the workflow state
3. The adapter executes a minimal asset-side action through a reference token model:
   - `ReferenceTokenHolding` represents the token-style holding surface
   - `MoveByCustodian` performs the minimal movement or control-state transition
4. The adapter emits its own machine-readable evidence:
   - `ReferenceTokenAdapterReceipt` on-ledger
   - `adapter-execution-report-v0.1` JSON off-ledger through `make localnet-run-token-adapter`
5. Workflow authority stays with the Control Plane:
   - the adapter never approves or rewrites policy
   - the adapter never creates encumbrances directly
   - the workflow still closes only when the Daml posting flow calls `ConfirmPostingSettlement`

The implementation shape is mixed, but narrow:

- Daml templates define the asset-side reference token holding and adapter receipt boundary
- a Daml Script layer under `CantonCollateral.QuickstartAdapter` bridges seeded Quickstart workflow outputs to the reference token movement
- shell commands wrap that script into reproducible operator surfaces

## Rejected Alternatives

### Alternative 1: Build a generic external integration bus first

Rejected because the repository needs one real path before it generalizes anything.

- a bus-first design would create a broad interface without proving one concrete settlement action
- it would encourage undocumented extension points before one stable receipt shape exists
- Prompt 15 calls for a narrow reference implementation, not a generic integration fabric

### Alternative 2: Push token movement logic into the workflow templates

Rejected because it would collapse data-plane execution into workflow authority.

- the workflow package should emit settlement intent and confirm settlement
- the adapter should own only the asset-side move
- collapsing those concerns would weaken the control-plane versus data-plane split

### Alternative 3: Emit only an off-ledger mock receipt

Rejected because the repository already has a real Quickstart ledger and Prompt 15 requires actual execution evidence.

- a mock receipt would not prove token-style movement on the running LocalNet
- it would weaken the report-fidelity posture the repository has enforced throughout the demo surface

## Consequences

Positive:

- the repository now has one real, documented adapter path another project can inspect and reuse as a boundary reference
- Quickstart-backed workflow execution now extends beyond seeding into a real settlement-consumption and asset-movement path
- the adapter result is auditable through both on-ledger and generated machine-readable artifacts

Tradeoffs:

- the first path is intentionally posting-focused and reference-grade rather than a full substitution, return, or release adapter family
- the Quickstart reference token path still relies on a simplified in-repo token holding model, not a real external custodian or token issuer
- production retry semantics, settlement-window enforcement, and broader callback handling remain future work

These tradeoffs are accepted because the repository needed one concrete data-plane adapter boundary more than it needed a broad but unproven abstraction.
