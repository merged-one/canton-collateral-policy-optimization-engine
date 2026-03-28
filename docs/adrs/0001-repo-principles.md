# ADR 0001: Repository Principles For A Safety-Critical Prototype

- Status: Accepted
- Date: 2026-03-28

## Context

The repository is intended to grow into a mission-critical collateral system prototype. The problem space spans confidential policy handling, valuation-derived lendable value, margin call and substitution workflows, release handling, and machine-readable reporting. The architecture is justified by established collateral practice:

- central-bank collateral frameworks separate eligibility, haircuting, control, and settlement responsibilities
- tri-party collateral utilities operationalize selection, valuation, and substitution
- CCP-style risk controls rely on conservative haircut and concentration schedules
- Canton is attractive because it can support privacy-preserving, atomic workflows across parties and applications

Starting implementation without a control spine would create avoidable ambiguity around requirements, evidence, and safety properties.

## Decision

The repository will adopt the following principles:

1. Documentation-first before business logic.
2. Mandatory traceability from requirements to invariants, evidence, and tests.
3. ADR-backed design for significant architecture or operating changes.
4. Explicit separation of policy, optimization, workflow execution, and reporting.
5. Deterministic, reproducible tooling and demos with pinned dependencies where possible.
6. No fake demo outputs, placeholder reports, or ambiguous success artifacts in the main execution path.
7. Safety-critical handling of collateral policy, control, substitution, and release.

## Consequences

Positive:

- clearer implementation boundaries
- earlier visibility into security, operational, and evidence gaps
- lower risk of building a prototype that cannot be defended or reproduced

Tradeoffs:

- slower initial progress on executable code
- more document maintenance overhead per feature
- early discipline around ADRs, invariants, and evidence

These tradeoffs are accepted because the domain is operationally sensitive and correctness is more important than rapid but opaque prototyping.
