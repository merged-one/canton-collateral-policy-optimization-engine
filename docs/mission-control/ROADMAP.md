# Roadmap

## Phase 0: Mission Control Spine

Objective:
Establish repository governance, control documents, and traceability before adding business logic.

Exit criteria:

- core documentation spine exists
- ADR baseline exists
- invariant, risk, and evidence registries exist
- lightweight verification commands succeed

## Phase 1: Pinned Foundations

Objective:
Choose and pin the LocalNet, asset-model, and reporting dependencies needed for implementation.

Expected outputs:

- dependency ADRs
- interface boundary documents
- pinned setup commands

## Phase 2: Asset And Policy Contracts

Objective:
Define data contracts for collateral assets, policy rules, valuation inputs, and control states.

Expected outputs:

- asset and control schemas
- policy data model
- invariant-to-schema traceability

## Phase 3: Selection And Workflow Specification

Objective:
Specify deterministic eligibility evaluation, haircuting, optimization, and Canton workflow boundaries.

Expected outputs:

- policy evaluation rules
- optimization constraints
- margin call, substitution, and return workflow specs

## Phase 4: Implementation Baseline

Objective:
Introduce the first business logic with pinned dependencies and reproducible demos.

Expected outputs:

- LocalNet bootstrap
- executable workflow slices
- test harnesses mapped to invariants

## Phase 5: Reporting, Operations, And Release Evidence

Objective:
Produce machine-readable execution reports, runbooks, and release-grade verification evidence.

Expected outputs:

- execution report schema and validators
- operator runbooks
- release checklist evidence
