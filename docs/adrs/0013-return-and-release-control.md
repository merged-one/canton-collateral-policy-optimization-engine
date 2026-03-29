# ADR 0013: Enforce Return And Release Control

- Status: Accepted
- Date: 2026-03-28

## Context

The Control Plane now proves end-to-end margin-call posting and atomic substitution, but its return path remains only a lifecycle skeleton. That is not sufficient for a confidential collateral release demo, because return and release handling are safety-critical in ways that overlap exposure coverage, secured-party control, custodian authority, replay safety, and report fidelity.

The current `CPL v0.1` contract can express eligibility, haircuts, concentration, and broad control requirements, but it does not yet carry a first-class return-rights clause that says exactly when collateral may be released back to the provider. The first return prototype therefore needs to prove real workflow control and report fidelity now without pretending that the broader language contract is already complete.

## Decision

The repository will implement the first return prototype as a retained-set-based, approval-gated, replay-safe release flow with a separate machine-readable `ReturnReport`.

Specific decisions:

1. The off-ledger orchestration layer will evaluate the currently encumbered inventory under policy, run the deterministic optimizer against the remaining required coverage amount, and derive the returned lots as `currentPostedLotIds - retainedLotIds`.
2. The Daml `ReturnRequest` contract will carry explicit return lot scope, requested return quantity, current secured amount, and remaining required coverage so the workflow can reject stale or mismatched release instructions directly on-ledger.
3. The `ReturnRequest` will use an active key on `returnRequestId` so a replayed return instruction cannot be recreated while the committed request remains active in a terminal state.
4. Return settlement intent must match the approved return lot scope and approved return quantity exactly; the workflow must reject altered settlement scope rather than silently accepting it.
5. The release path must remain blocked until all required secured-party and custodian approvals are present, and unauthorized settlement confirmation attempts must fail closed without changing encumbrance state.
6. The workflow must reject any return where `currentSecuredAmount - requestedReturnQuantity < remainingRequiredCoverage`, making obligation-state mismatch explicit rather than relying on operator discipline.
7. The operator command for this path is `make demo-return`, which will emit a separate `ReturnReport` plus Markdown summary and timeline artifacts backed by real policy, optimization, and Daml workflow execution.
8. Until a future CPL version adds first-class return-right clauses, the return prototype will treat release-approval requirements as workflow input derived from the scenario bundle and documented policy interpretation rather than as a hidden policy-engine side effect.

## Consequences

Positive:

- the repository gains a real return demo with explicit secured-party control and release-state evidence
- replay protection becomes concrete through an active workflow identifier instead of a prose-only aspiration
- return artifacts can now prove both committed and blocked paths in a machine-readable contract
- the retained-set recommendation stays deterministic because it reuses the existing optimizer rather than introducing a second hidden selection engine

Tradeoffs:

- the first return prototype uses quantity-based secured-amount checks in the Daml demo layer rather than a full on-ledger lendable-value model
- return approval requirements are still scenario-derived because `CPL v0.1` lacks dedicated return-rights fields
- the return workflow remains IDE-ledger-backed until the Quickstart deployment bridge is complete

These tradeoffs are accepted because the repository needs a trustworthy return and release control prototype now, but it should not pretend that policy-language support, Quickstart deployment, or production-grade reference-data coupling are already solved.
