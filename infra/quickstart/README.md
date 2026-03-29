# Quickstart LocalNet Foundation

## Purpose

This directory holds the repo-owned foundation for a Quickstart-based LocalNet while keeping the Canton Collateral Control Plane close to upstream CN Quickstart workflows.

The implemented layer now covers:

- pin one upstream CN Quickstart commit
- bootstrap a detached upstream checkout under `.runtime/localnet/`
- write a repo-owned `.env.local` overlay from a documented profile
- validate the composed LocalNet configuration with upstream `make check-docker` plus `docker compose ... config`
- build a Quickstart-compatible Control Plane DAR from the shared repo Daml source tree
- start an isolated repo-owned Quickstart overlay with dedicated network, container names, and non-conflicting port suffixes
- deploy the Control Plane DAR into the running Quickstart participants
- allocate or reuse the parties and users needed for one confidential collateral scenario
- seed one real margin-style obligation, provider inventory set, and posting intent on Quickstart
- emit machine-readable and human-readable deployment, seed, and status evidence derived from the running LocalNet

It does not yet:

- execute a full Quickstart-backed posting, substitution, or return workflow beyond the seeded state
- integrate a live token-standard-style asset application, custodian adapter, venue, or financing app
- add settlement-window enforcement, workflow-coupled optimizer reservation, or production-grade collateral business logic

## Upstream Pin

`infra/quickstart/overlay/upstream-pin.env` records the current LocalNet pin:

- CN Quickstart repo: `https://github.com/digital-asset/cn-quickstart.git`
- pinned on: `2026-03-28`
- pinned commit: `fe56d460af650b71b8e20098b3e76693397a8bf9`
- upstream Quickstart subdirectory: `quickstart/`
- upstream Quickstart `.env` values observed at that commit: `DAML_RUNTIME_VERSION=3.4.10`, `SPLICE_VERSION=0.5.3`, `JAVA_VERSION=21-jdk`

This pin is separate from the repository's current Daml SDK `2.10.4` workflow package. ADR 0016 closes that mismatch through a containerized Daml `3.4.10` plus Java `21` bridge for Quickstart-compatible DAR builds while preserving the repo-default host toolchain for the existing IDE-ledger workflow surface. ADR 0017 then adds the seeded Quickstart scenario through repo-owned overlays and Daml Script rather than an upstream fork.

## Overlay Assets

- `overlay/profiles/lean.env.local`: lighter LocalNet profile with OAuth2 preserved
- `overlay/profiles/faithful.env.local`: upstream-style profile with observability preserved
- `overlay/control-plane-compose.yaml`: repo-owned compose override with isolated `control-plane-*` container names
- `scenarios/confidential-margin-scenario.json`: default seed manifest for the confidential margin-style scenario

Both overlay profiles now place the stack on the dedicated Docker network `quickstart-control-plane` and move the validator or participant port suffixes away from the upstream defaults so this repo can coexist with other Quickstart workspaces on the same host.

## Reproducible Commands

From the repository root:

```sh
make localnet-bootstrap
make localnet-smoke
make localnet-build-dar
make localnet-deploy-dar
make localnet-start-control-plane
make localnet-seed-demo
make localnet-status-control-plane
```

Command summary:

- `make localnet-bootstrap`: stage the pinned upstream checkout and write `quickstart/.env.local`
- `make localnet-smoke`: reuse the upstream `make check-docker` target, validate the fully composed Docker configuration, and probe validator readiness if the stack is already running
- `make localnet-build-dar`: emit `.daml/dist-quickstart/canton-collateral-control-plane-0.1.1.dar` plus package metadata for the pinned Quickstart runtime line
- `make localnet-deploy-dar`: rebuild that DAR and upload it into the running app-provider and app-user participants
- `make localnet-start-control-plane`: start or reuse the isolated overlay runtime, deploy the DAR, and write `reports/generated/localnet-control-plane-deployment-receipt.json` plus `reports/generated/localnet-control-plane-deployment-summary.md`
- `make localnet-seed-demo`: allocate the required scenario users or parties, seed the default confidential collateral scenario, and write `reports/generated/localnet-control-plane-seed-receipt.json`
- `make localnet-status-control-plane`: query the provider-visible Quickstart view and write `reports/generated/localnet-control-plane-status.json` plus `reports/generated/localnet-control-plane-status-summary.md`

Optional overrides:

```sh
make localnet-bootstrap LOCALNET_PROFILE=faithful LOCALNET_PARTY_HINT=canton-demo-1
make localnet-start-control-plane LOCALNET_WORKDIR=/absolute/path/to/cn-quickstart
make localnet-seed-demo LOCALNET_SCENARIO_MANIFEST=infra/quickstart/scenarios/confidential-margin-scenario.json
```

## Seeded Default Scenario

The default seed manifest provisions one confidential margin-style scenario:

- existing Quickstart `app-user` party acts as the collateral provider
- existing Quickstart `app-provider` party acts as the secured party
- repo-allocated `controlplane-custodian-1` party acts as the custodian
- repo-allocated `controlplane-operator-1` party acts as the optional operator
- one obligation `quickstart-margin-obligation-001`
- one posting intent `quickstart-margin-posting-001`
- two provider inventory lots: `quickstart-us-tbill-lot-001` and `quickstart-us-tbill-lot-002`

The seed and status commands write ledger-returned contract identifiers so the evidence surface proves the scenario lives on Quickstart rather than only in local manifests.

## Evidence Surface

The primary generated artifacts are:

- `reports/generated/localnet-control-plane-deployment-receipt.json`
- `reports/generated/localnet-control-plane-deployment-summary.md`
- `reports/generated/localnet-control-plane-seed-receipt.json`
- `reports/generated/localnet-control-plane-status.json`
- `reports/generated/localnet-control-plane-status-summary.md`

See [docs/runbooks/LOCALNET_CONTROL_PLANE_RUNBOOK.md](../../docs/runbooks/LOCALNET_CONTROL_PLANE_RUNBOOK.md) for the operator procedure and [docs/evidence/prompt-14-execution-report.md](../../docs/evidence/prompt-14-execution-report.md) for the Prompt 14 execution evidence.

## Assumptions, Mocked Surfaces, And Deferred Work

| Area | Current State | Why |
| --- | --- | --- |
| Quickstart source | real pinned upstream checkout | avoid repo forks and keep delta reviewable |
| `.env.local` overlay | real and generated by repo script | smallest practical extension point supported by upstream workflow |
| compose override | real repo-owned overlay file | isolate the Control Plane LocalNet from other host Quickstart stacks without patching upstream files |
| LocalNet container startup | real repo-owned wrapper over the upstream compose stack | keeps runtime ownership explicit while still giving the repository a reproducible start command |
| Control Plane DAR deployment | real | the repo installs a Quickstart-compatible DAR through the documented containerized bridge and onboarding path |
| confidential seed scenario | real | obligation, posting intent, inventory, role registrations, and status are now seeded from the shared Daml package on Quickstart |
| token-standard-style asset integration | deferred | adapter contract and settlement callback shapes still need to be pinned |
| workflow execution after seeding | deferred | Prompt 14 stops at seeded state and status evidence rather than a full Quickstart-backed workflow execution report |

See [docs/integration/LOCALNET_DEMO_PLAN.md](../../docs/integration/LOCALNET_DEMO_PLAN.md) and [docs/integration/ASSET_ADAPTER_PLAN.md](../../docs/integration/ASSET_ADAPTER_PLAN.md) for the staged path from this foundation to a real confidential collateral demo.
