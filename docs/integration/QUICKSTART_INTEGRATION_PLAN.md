# Quickstart Integration Plan

## Objective

Use an upstream Quickstart-based LocalNet as the prototype's Canton runtime while keeping Control-Plane-specific topology, packages, and services in overlays or adjacent services. Quickstart and LocalNet remain data-plane execution surfaces; the policy, optimization, workflow, and reporting subsystems remain part of the Control Plane. The goal is to maximize compatibility with the Quickstart ecosystem and minimize long-lived forks.

## Current Pinned Runtime Foundation

The repository now pins the first executable foundation around:

- Daml SDK `2.10.4`
- Canton open-source `2.10.4`
- Temurin JDK `17.0.18+8`
- pinned Quickstart runtime metadata `DAML_RUNTIME_VERSION=3.4.10`, `SPLICE_VERSION=0.5.3`, and `JAVA_VERSION=21-jdk`

These versions now operate through an explicit dual-runtime bridge:

- the repo-default host toolchain stays on Daml `2.10.4` plus JDK `17` for IDE-ledger workflows and portable verification
- Quickstart-compatible DAR builds run in Docker on Daml `3.4.10` plus Java `21`

## Current Foundation Status

The concrete Quickstart foundation now exists under `infra/quickstart/`:

- upstream CN Quickstart is pinned by commit SHA rather than by floating branch name
- `make localnet-bootstrap` stages the upstream checkout and writes `.env.local` from repo-owned overlay profiles
- `make localnet-smoke` reuses upstream Docker preflight checks and validates the composed stack without claiming full workflow deployment
- `make localnet-build-dar` builds a Quickstart-compatible Control Plane DAR from the shared repo Daml source tree
- `make localnet-deploy-dar` uploads that DAR into a running pinned Quickstart LocalNet through the upstream onboarding container
- `make localnet-start-control-plane` starts or reuses an isolated repo-owned overlay runtime with dedicated network, port-suffix, and container-name isolation
- `make localnet-seed-demo` allocates or reuses the scenario parties and users, then seeds one confidential margin-style obligation, provider inventory set, and posting intent on Quickstart
- `make localnet-status-control-plane` captures provider-visible ledger state as machine-readable and human-readable evidence

The runtime bridge is therefore no longer only a planning note or blocker, and seeded Quickstart state is no longer only a deferred plan. The remaining Quickstart work is full workflow execution, workflow-party disclosure shaping, and adapter integration on top of the seeded package and scenario surface.

## Integration Principles

- start from a pinned upstream Quickstart release
- express Control-Plane-specific participants, parties, package deployment, and service wiring through overlays first
- run policy, valuation, optimization, reporting, and integration services adjacent to Canton, not inside patched Quickstart internals
- fork upstream only when an extension point is missing and the gap is documented through an ADR
- keep the prototype topology reproducible from repo-controlled configuration

## Proposed LocalNet Shape

| Layer | Planned Content |
| --- | --- |
| upstream base | domain, sequencer, mediator, baseline participant setup, developer tooling |
| Control Plane overlay | participant and party additions for provider, secured-party, custodian, and operator roles; package deployment config; bootstrap data hooks; isolated compose overrides |
| adjacent services | policy registry, valuation service, optimization service, reporting service, integration gateway |
| scenario tools | reproducible commands for seed data, workflow execution, and report validation |

## Recommended Delivery Strategy

### Step 1: Pin the base

- select and pin the Quickstart release that will anchor LocalNet development
- use the already pinned Daml SDK and Canton `2.10.4` host foundation plus the Daml `3.4.10` containerized bridge as the compatibility floor
- record image or package versions in a dedicated dependency ADR before workflow code starts

### Step 2: Add overlays, not forks

- define overlay configuration for extra parties, participants, package deployment, service endpoints, and any needed container or network isolation
- keep base Quickstart files untouched where override or composition mechanisms exist
- isolate repo-specific topology under a Control-Plane-owned overlay directory once implementation begins

### Step 3: Deploy Control Plane Daml packages on top

- treat the Control Plane workflow package as an application deployed into the LocalNet, not as a modification to Quickstart core services
- keep obligation, encumbrance, settlement, and approval templates in the Control Plane package boundary
- preserve one shared Daml source tree and build the Quickstart-compatible DAR through the documented containerized bridge rather than a forked Quickstart-only package tree

### Step 4: Attach adjacent services

- policy registry serves versioned policy packages to the workflow orchestrator and reporter
- valuation service produces immutable snapshots consumed by policy evaluation and reports
- optimization service ranks feasible collateral without becoming the source of truth
- reporting service subscribes to committed workflow state and emits execution reports

### Step 5: Validate with conformance scenarios

- use scenario runners against the LocalNet deployment
- confirm that overlays do not change control semantics compared with the documented architecture
- capture deployment receipts, seed receipts, status snapshots, and later scenario execution reports as evidence

## When A Fork Is Acceptable

A Quickstart fork is acceptable only if all of the following are true:

1. the needed topology or integration point cannot be expressed with an overlay or adjacent service
2. the missing extension point blocks an implementation milestone
3. the fork scope is minimal and documented
4. an ADR records why the fork exists and how to retire it later

## Planned Boundaries For The Prototype

| Concern | Preferred Placement | Reason |
| --- | --- | --- |
| multi-party workflow execution | Quickstart LocalNet plus deployed Control Plane workflow package | keeps authoritative workflow state on Canton |
| policy versioning | adjacent policy registry | avoids coupling policy lifecycle to package deployment |
| optimization | adjacent service | keeps objective tuning out of workflow contracts |
| reporting | adjacent service | allows role-specific report profiles and re-generation from state |
| demo bootstrap | overlay scripts and config | keeps environment logic separate from business semantics |

## Simplifications In Early Prototype Phases

- LocalNet may run all services on one machine while still preserving logical role separation
- bootstrap data may use synthetic counterparties and assets, but only through documented seed inputs
- early settlement adapters may stop at instruction emission rather than real external asset movement
- observability may be local-only before shared demo infrastructure exists

## Exit Criteria For Moving Beyond Planning

- Quickstart version pinned
- Daml SDK and Canton baseline pinned for local compilation plus an explicit ADR-backed bridge for the pinned Quickstart runtime line
- overlay strategy documented in repo-controlled config
- Daml package boundary defined
- adjacent service contracts defined for policy, valuation, optimization, and reporting
- at least one reproducible LocalNet scenario planned end to end and seeded on Quickstart
