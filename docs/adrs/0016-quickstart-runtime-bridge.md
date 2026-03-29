# ADR 0016: Quickstart Runtime Bridge

- Status: Accepted
- Date: 2026-03-29

## Context

The repository already pinned an upstream CN Quickstart LocalNet foundation at commit `fe56d460af650b71b8e20098b3e76693397a8bf9`, but that foundation reported a runtime line of `DAML_RUNTIME_VERSION=3.4.10`, `SPLICE_VERSION=0.5.3`, and `JAVA_VERSION=21-jdk` while the Control Plane repo itself remained pinned to Daml SDK `2.10.4` and Temurin JDK `17.0.18+8`.

That mismatch was the main blocker to real package deployment:

- the repo toolchain could build and test the Control Plane DAR locally, but not against the pinned Quickstart runtime line
- the Quickstart startup and onboarding flow expected a `3.4.10`-compatible DAR
- macOS Apple Silicon remained a first-class bootstrap platform for this repo, but Digital Asset did not publish a native macOS `arm64` SDK archive for Daml `3.4.10`

Probe builds against Daml `3.4.10` also exposed source-level compatibility gaps that had been hidden by the earlier IDE-ledger-only posture:

- the `ReturnRequest` replay guard relied on a contract key pattern that was not a stable bridge across the runtime lines
- generic Daml Script contract-query helpers no longer compiled cleanly on both lines without using explicit template-specific helpers

## Decision

Use a dual-runtime bridge instead of a repo-wide Daml upgrade or a Quickstart re-pin.

The bridge has four concrete parts:

1. Keep the repo-default host toolchain at Daml SDK `2.10.4` plus JDK `17` for the existing IDE-ledger workflow, demo, and portable verification surface.
2. Add a containerized Quickstart DAR build path that uses Ubuntu `24.04`, Java `21`, and Daml SDK `3.4.10` from checksum-pinned official Linux SDK archives.
3. Make the Control Plane Daml source compile on both runtime lines by removing the return replay dependency on a contract key and replacing it with an explicit `ReturnRequestRegistry`, while also switching Daml Script query helpers to template-specific implementations.
4. Add explicit command surfaces for building and deploying the Control Plane DAR into a running pinned Quickstart LocalNet:
   - `make localnet-build-dar`
   - `make localnet-deploy-dar`

`make localnet-deploy-dar` must treat the pinned Quickstart runtime as the authority for deployment status. It therefore:

- validates that the pinned upstream checkout exists
- verifies the runtime line through the existing Quickstart bootstrap and smoke commands
- rebuilds the Control Plane DAR through the containerized `3.4.10` path
- uploads that DAR to the running Quickstart participants through the upstream onboarding container and participant `/v2/packages` API

## Rejected Alternatives

### Alternative 1: Upgrade the whole repo to Daml `3.4.10`

Rejected because it was not the smallest credible bridge.

- the repo already had a working Daml `2.10.4` host-native bootstrap and IDE-ledger demo surface
- a full upgrade would have forced a broader revalidation of all Daml scripts, bootstrap assumptions, and Java tooling
- the lack of a native macOS `arm64` Daml `3.4.10` archive would still have left Apple Silicon contributors with a degraded or undocumented host path

### Alternative 2: Re-pin Quickstart to a `2.10.4`-compatible line

Rejected because it would weaken the already-pinned upstream LocalNet foundation.

- the repo had already chosen a real upstream Quickstart commit and image line
- moving Quickstart backward to match the repo would trade one bridge problem for a fork-or-drift problem
- the repo should stay close to the current upstream LocalNet direction unless an ADR proves that upstream cannot support the intended prototype path

### Alternative 3: Keep a separate Quickstart-only Daml source tree

Rejected because it would duplicate the workflow boundary and create two sources of truth.

- the Control Plane would have one package for IDE-ledger demos and another for Quickstart deployment
- replay, approval, and report semantics could drift between those packages
- future workflow-coupled integration work would become harder to reason about and test

## Operational Consequences

- `make daml-build`, `make daml-test`, `make demo-run`, `make demo-margin-call`, `make demo-return`, `make demo-substitution`, `make test-conformance`, and `make demo-all` remain on the repo-default Daml `2.10.4` host path.
- `make localnet-build-dar` and `make localnet-deploy-dar` now require Docker because the Quickstart-compatible DAR is built inside a Linux container.
- The Quickstart deployment path now depends on a running pinned Quickstart LocalNet, including the upstream OAuth2 and onboarding surfaces when the `lean` overlay profile is used.
- The Quickstart bridge closes package build and package deployment, but it does not yet seed a confidential collateral scenario, run a full Control Plane workflow on Quickstart, or add live asset adapters.
- Replay protection for return requests is now modeled explicitly through `ReturnRequestRegistry` rather than through a contract key on `ReturnRequest`.

## Rollback And Revisit Conditions

Revisit this ADR if any of the following become true:

- a native macOS `arm64` Daml SDK becomes available for the same Quickstart runtime line and a repo-wide toolchain unification becomes practical
- upstream Quickstart re-pins to a runtime line that can replace the current bridge with one host-native repo toolchain
- the Quickstart package-upload path, onboarding hooks, or auth model changes enough that the current deployment command is no longer the smallest reproducible install path
- future workflow execution on Quickstart requires additional runtime-specific package structure that cannot be maintained safely from one shared Daml source tree

If the bridge is retired later, the replacement must still preserve:

- one explicit ADR-backed runtime strategy
- checksum-pinned or commit-pinned dependency evidence
- reproducible build and deployment commands
- no fake Quickstart deployment claims in the evidence surface
