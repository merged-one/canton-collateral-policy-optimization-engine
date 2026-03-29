# ADR 0014: Package Conformance And Final Demo Evidence

- Status: Accepted
- Date: 2026-03-28

## Context

The repository already exposes separate end-to-end confidential margin-call, substitution, and return demos. Each flow emits real JSON and Markdown artifacts, but proposal reviewers still need one reproducible command that proves:

- authorization and role control
- deterministic eligibility and haircut behavior
- no double-encumbrance and atomic substitution
- replay safety
- report fidelity
- audit trail completeness
- a stable integration surface for future Canton projects

Without an aggregate conformance layer, the repository would still look like a set of disconnected feature demos rather than a coherent Control Plane prototype with a defensible safety case.

## Decision

The repository will publish a first aggregate conformance suite and final demo pack on top of the existing demo runners.

Specific decisions:

1. `make test-conformance` will execute the three existing demo flows, run explicit invariant-oriented checks across their generated artifacts, and emit a machine-readable conformance report plus a Markdown summary.
2. `make demo-all` will depend on the conformance suite and emit a separate final demo-pack index that gathers the three confidential workflow demos, invariant pass/fail output, and documented third-party integration surfaces.
3. The conformance suite will check at least authorization and role control, eligibility determinism, haircut correctness, no double-encumbrance, atomic substitution when required, replay safety, report fidelity, and audit trail completeness.
4. The final demo package will remain evidence-driven: it may only reference real generated artifacts and documented interfaces, never placeholder success narratives.
5. Third-party integration guidance will stay documentation-first and stable at the boundary level, while live adapters, Quickstart deployment, and role-scoped disclosure profiles remain separate follow-on tasks.

## Consequences

Positive:

- the repository now has a single reproducible proof surface for technical, economic, and operational readiness
- invariant checks become explicit operator-facing outputs instead of implied properties buried in separate demos
- Development Fund reviewers and future Canton projects can inspect one integration guide and one artifact index instead of reconstructing the package manually

Tradeoffs:

- `make test-conformance` now runs the full demo set rather than a narrow unit-only check
- the final package increases the amount of committed generated evidence that must remain reproducible
- the package still depends on the Daml IDE ledger for workflow execution until the Quickstart deployment bridge is solved

These tradeoffs are accepted because the prototype's next milestone is credibility and integration clarity, not just more isolated workflow features.
