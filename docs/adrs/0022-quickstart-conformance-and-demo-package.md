# ADR 0022: Center Conformance And Final Demo Packaging On Quickstart Runtime Evidence

- Status: Accepted
- Date: 2026-03-30

## Context

ADR 0014 introduced an aggregate conformance suite and a final demo pack while the workflow demos still centered the Daml IDE ledger. Prompts 16 through 18 then moved the confidential margin-call, substitution, and return demos onto the pinned Quickstart runtime and the narrow reference token adapter path.

That left one proposal-readiness gap:

- `make test-conformance` still centered the older IDE-ledger report chain
- `make demo-all` still indexed the package as though Quickstart deployment and adapter proof were sidecar evidence rather than the primary runtime story
- the final package did not clearly separate what is now real on Quickstart from what remains staged prototype scope
- third-party reviewers could still mistake the reference adapter path for a broader production integration claim

Prompt 19 requires the repository to close that packaging gap without weakening the existing control-plane versus data-plane boundary.

## Decision

The aggregate conformance suite and final demo pack will now treat the pinned Quickstart deployment, one concrete reference token adapter path, and the three Quickstart-backed confidential workflow demos as the primary proof surface for proposal review.

The concrete shape is:

1. `make test-conformance` becomes Quickstart-first:
   - it refreshes the Quickstart deployment surface
   - it validates one concrete reference token adapter proof path
   - it executes the Quickstart-backed margin-call, substitution, and return demo manifests
   - it validates aggregate invariants against runtime-backed workflow, adapter, and provider-visible status artifacts
2. `make demo-all` becomes proposal-package-first:
   - it indexes Quickstart deployment evidence
   - it indexes concrete reference token adapter execution and status artifacts
   - it indexes the three Quickstart-backed demo reports as the primary demo flows
   - it records explicit real-versus-staged readiness notes in the machine-readable final pack
3. The IDE-ledger demo commands remain available only as comparison or portable-verification surfaces:
   - they are no longer the package's primary runtime story
   - they should not be used to imply that broader external integrations are already runtime-proven
4. Third-party integration guidance must stay boundary-disciplined:
   - the Control Plane remains authoritative for policy, optimization, workflow, conformance, and reporting
   - the reference token adapter remains a narrow consumer of workflow-declared settlement intent
   - replacement adapters must preserve that authority split rather than collapsing it

## Rejected Alternatives

### Alternative 1: Keep the aggregate package centered on the IDE-ledger reports and list Quickstart evidence only as supplemental artifacts

Rejected because it would preserve the exact readiness gap Prompt 19 is intended to close.

- reviewers would still have to infer which runtime path is actually real
- the final package would keep underselling the Quickstart-backed execution surface
- the repo would still read like an IDE-ledger prototype with optional runtime appendices

### Alternative 2: Remove the IDE-ledger commands entirely once the Quickstart package becomes primary

Rejected because the portable comparison path still has value.

- the host-only commands remain useful when Docker-backed Quickstart runtime is unavailable
- keeping the comparison path visible helps reviewers see the technical delta between the earlier prototype and the current runtime-backed one
- the key change is packaging priority, not forced deletion of comparison surfaces

## Consequences

Positive:

- the proposal package now tells one consistent story about what is real on Quickstart
- deployment, adapter, workflow, and aggregate invariant proof now sit in one reproducible package
- external adopters get a clearer integration picture with less risk of mistaking prototype scope for production scope

Tradeoffs:

- `make test-conformance` now depends on the Quickstart runtime and the concrete reference-adapter proof surface
- the final package now carries more explicit readiness language about what remains staged
- the package still proves only one narrow adapter path rather than a broad production asset-integration set

These tradeoffs are accepted because the repository now needs a credible proposal-ready proof surface more than it needs to preserve the earlier IDE-ledger-centric packaging story.
