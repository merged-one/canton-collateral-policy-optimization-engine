# LocalNet Demo Plan

## Objective

Turn the current repository into a real confidential-collateral demo on top of an upstream CN Quickstart LocalNet without collapsing policy, optimization, workflow authority, or reporting boundaries.

## Current Implemented Layer

This prompt implements Stage 0 only:

- pinned upstream CN Quickstart checkout at commit `fe56d460af650b71b8e20098b3e76693397a8bf9`
- repo-owned `.env.local` overlay profiles under `infra/quickstart/overlay/`
- reproducible bootstrap through `make localnet-bootstrap`
- reproducible compose-preflight smoke through `make localnet-smoke`
- documented operator path that stays with upstream `make check-docker`, `make build`, `make start`, and `make status`

This prompt does not yet:

- deploy the Control Plane DAR into Quickstart
- seed confidential collateral data or live parties
- move assets through a token-standard-style application
- emit a Quickstart-backed `ExecutionReport`

## Staged Delivery

### Stage 0: Pinned Foundation

Status: implemented in this prompt

- pin one upstream Quickstart commit and record the observed upstream runtime versions
- keep the upstream tree detached and unmodified
- express repo intent through `.env.local` overlays and adjacent scripts
- validate the composed stack before claiming a runnable confidential demo

### Stage 1: Upstream LocalNet Bring-Up

Status: documented, not automated here

- run `make check-docker`, `make build`, `make start`, and `make status` inside the staged upstream `quickstart/` directory
- verify the LocalNet validators and supporting services are healthy
- preserve upstream logs, Daml Shell, and observability workflows so later debugging stays aligned with the Quickstart ecosystem

### Stage 2: Control Plane Package Bridge

Status: deferred

- reconcile the current repo Daml SDK `2.10.4` package with the pinned Quickstart runtime line (`DAML_RUNTIME_VERSION=3.4.10`)
- decide whether the bridge is achieved through a repo upgrade, a separately built compatible DAR, or a version-pinned sidecar package boundary
- only after that bridge exists, upload the Control Plane DAR and allocate or onboard the demo parties

### Stage 3: Confidential Collateral Seed Scenario

Status: deferred

- seed a minimal but real scenario covering pledgor, secured party, custodian or controller, and one token issuer
- load obligations, normalized inventory provenance, and policy references without bypassing workflow authority
- produce a real `ExecutionReport` and settlement-intent trace from committed Canton state

### Stage 4: Cross-App Demo Extensions

Status: deferred

- attach one token-standard-style issuer or wallet path
- attach one custodian or control adapter path
- optionally expose venue or financing-app callbacks once settlement instruction contracts are pinned

## Assumptions, Mocked Surfaces, And Deferrals

| Area | Assumed Or Mocked | Why |
| --- | --- | --- |
| Quickstart topology | upstream CN Quickstart modular Docker Compose stack | stay close to supported workflows and reduce repo-owned runtime code |
| Auth path | OAuth2 remains the default overlay choice | keeps the future confidential demo close to the upstream security posture |
| Observability | optional in `lean`, enabled in `faithful` | preserve a lightweight preflight while keeping a higher-fidelity path available |
| LocalNet start | documented but not auto-executed by repo Make targets | avoids claiming end-to-end success before the Daml version bridge is pinned |
| Control Plane package load | deferred | repo Daml artifacts are not yet aligned with the pinned Quickstart runtime line |
| Asset movement | mocked as future adapter work | avoids fake settlement or fake token movement in the main execution path |

## Integration Hooks For Other Canton Projects

| Integrator | Future Hook |
| --- | --- |
| venues | consume approved `SettlementInstruction` artifacts and return venue-specific execution status callbacks |
| financing apps | call policy evaluation, optimization, and workflow proposal boundaries without owning settlement authority |
| token issuers | expose token, balance, control, and transfer surfaces through the planned asset-adapter contract |
| custodians | map custody-account control, hold, and release semantics into `EncumbranceState` and settlement callback updates |
| margining applications | drive obligation issuance and workflow consent while reusing the shared policy and optimization layers |

## Reproducible Commands

From the repository root:

```sh
make localnet-bootstrap
make localnet-smoke
```

From the staged upstream checkout after bootstrap:

```sh
cd .runtime/localnet/cn-quickstart/quickstart
make check-docker
make build
make start
make status
```

## Exit Criteria For A Real Confidential Demo

- the upstream Quickstart stack starts reproducibly from the pinned checkout
- the Control Plane DAR is deployed through a documented version-bridge path
- at least one token-standard-style asset path can be loaded through a real adapter
- at least one collateral posting or substitution scenario emits a real machine-readable `ExecutionReport`
- all assumptions, mocks, and deferred surfaces remain explicit in operator documentation
