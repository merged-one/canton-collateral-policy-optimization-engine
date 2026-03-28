# Integration Surfaces

This document identifies the major system boundaries the prototype is expected to expose or depend on. All surfaces are planned; none are implemented in this prompt.

## Planned Surfaces

| Surface | Purpose | Notes |
| --- | --- | --- |
| Canton Quickstart LocalNet | Host confidential multi-party workflow execution. | Version and topology to be pinned in a future ADR. |
| Token-standard-style asset representation | Represent collateral assets and encumbrance state. | Must support deterministic eligibility and control semantics. |
| Policy input surface | Accept eligibility, haircut, concentration, and control rules. | Must be versioned and explainable. |
| Optimization boundary | Produce candidate allocations or substitutions under policy constraints. | Must remain separate from policy authoring and workflow settlement. |
| Workflow orchestration boundary | Execute margin call, substitution, and return flows atomically. | Must preserve confidentiality and replay safety. |
| Report generation surface | Emit machine-readable execution reports tied to committed state. | Must satisfy report-fidelity invariants. |
| External reference data inputs | Provide valuation, concentration, and static reference data. | Must be versioned and auditable. |

## Mapping To Established Practice

- Central-bank style collateral frameworks motivate the split between policy, valuation, control, and settlement.
- Tri-party workflows motivate explicit selection, substitution, and operational coordination boundaries.
- CCP-style control motivates concentration-sensitive policy evaluation and conservative haircut application.

## Near-Term Follow-Up

- pin the LocalNet distribution
- define asset and policy schemas
- define the first execution report contract
