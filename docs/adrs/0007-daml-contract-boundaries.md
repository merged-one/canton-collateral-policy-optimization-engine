# ADR 0007: Split The First Daml Workflow Package Along Contract Boundaries

- Status: Accepted
- Date: 2026-03-28

## Context

The repository now has a pinned Daml toolchain and a documented collateral lifecycle model, but the runtime package still needs its first real contract boundary. This boundary must prove that confidential collateral control can be modeled on Canton without collapsing policy, workflow, settlement, and reporting into one opaque template set.

The first Daml package needs to:

- encode the documented roles, assets, lots, encumbrance states, obligations, substitution requests, return requests, settlement instructions, and execution reports
- preserve role separation and confidentiality intent through explicit stakeholder sets
- keep policy evaluation and optimization off-ledger and non-authoritative while still pinning policy and snapshot references on-ledger
- support real lifecycle tests without hardcoding implicit success paths

## Decision

The initial Daml package will be split into small modules under `daml/CantonCollateral/` and will keep workflow, settlement, and reporting as separate contract surfaces.

Specific decisions:

1. Shared workflow vocabulary, approval state, encumbrance state, settlement action, and execution-event records live in `CantonCollateral.Types`.
2. Party-role registration, asset abstraction, and inventory lots are separate modules from workflow requests so reference facts remain composable.
3. `CallObligation`, `CollateralPostingIntent`, `SubstitutionRequest`, and `ReturnRequest` are distinct workflow templates with explicit lifecycle-state fields and explicit approval choices.
4. `SettlementInstruction` is a separate template rather than an embedded field-only status so settlement intent remains visible as its own contract boundary.
5. `ExecutionReportRecord` is a separate template created only from workflow choices, so reports remain state-derived artifacts instead of operator-authored summaries.
6. Workflow contracts carry a `PolicyContext` reference that pins `policyVersion`, `snapshotId`, and `decisionReference`, but they do not embed policy rules or optimization logic.
7. Daml scripts under `CantonCollateral.Test` are the first executable conformance layer for issuance, posting, substitution, rejection, and return skeletons.

## Consequences

Positive:

- the first Daml implementation now matches the documented domain partitions instead of hiding them behind one large template
- privacy intent is visible in contract stakeholder choices and observer lists
- settlement and reporting stay downstream of workflow state, which reinforces report fidelity and workflow authority invariants
- future Quickstart overlays and asset adapters can bind to explicit obligation, encumbrance, settlement, and report contracts

Tradeoffs:

- the first package contains more modules and cross-template references than the earlier smoke package
- atomic workflow behavior is still skeletal because policy decisions, valuation feeds, and asset-adapter integrations remain out of scope
- role-scoped report profiles are still future work even though the report boundary now exists

These tradeoffs are accepted because the repository now needs real contract surfaces and executable lifecycle checks, not just a compile-only runtime stub.
