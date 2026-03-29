# Prompt 14 Execution Report

## Scope

Move the Control Plane from "Quickstart deployment path exists" to "the pinned Quickstart LocalNet actually hosts a seeded confidential collateral scenario" by adding an overlay-first start, deploy, seed, and status command surface plus real machine-readable evidence.

## Quickstart Overlay Surface

ADR 0017 chooses a repo-owned overlay strategy:

- preserve the pinned upstream Quickstart checkout at commit `fe56d460af650b71b8e20098b3e76693397a8bf9`
- add an isolated compose override, dedicated Docker network, and non-conflicting port suffixes rather than forking upstream Quickstart
- deploy the shared Control Plane DAR through the existing Quickstart runtime bridge
- allocate or reuse the required parties and users through participant-management APIs
- seed the default scenario and query provider-visible state through Daml Script so receipts come from the real Quickstart ledger

## Commands

```sh
make localnet-start-control-plane
make localnet-seed-demo
make localnet-status-control-plane
make docs-lint
git diff --check
```

Additional command-level checks executed during implementation:

```sh
sh -n scripts/localnet-control-plane-common.sh
sh -n scripts/run-quickstart-daml-script.sh
sh -n scripts/localnet-start-control-plane.sh
sh -n scripts/localnet-seed-demo.sh
sh -n scripts/localnet-status-control-plane.sh
sh -n scripts/localnet-deploy-dar.sh
sh -n scripts/run-localnet-smoke.sh
make daml-build
make localnet-build-dar
```

## Results

- `make localnet-start-control-plane` passed and started the repo-owned Quickstart overlay on Docker network `quickstart-control-plane` with isolated `control-plane-*` container names.
- the same command deployed `.daml/dist-quickstart/canton-collateral-control-plane-0.1.1.dar` into the pinned Quickstart participants and wrote `reports/generated/localnet-control-plane-deployment-receipt.json` plus `reports/generated/localnet-control-plane-deployment-summary.md`.
- the deployment receipt proves package id `829c57ff1186dd09d4e3e232f2ac08c447de2bfe7c7f3b0cc3bf433fb3190f63` was uploaded through onboarding container `control-plane-splice-onboarding` into participants `app-provider` and `app-user`.
- `make localnet-seed-demo` passed and seeded the default confidential scenario `quickstart-confidential-margin-001` on Quickstart rather than on the IDE ledger.
- the seed receipt proves the following seeded Quickstart state:
  - provider party `app_user_canton-collateral-1::122029d17b90ca982c572b237f30895dd12b8db8582d623e473ed8059ce3e4185d0a`
  - secured party `app_provider_canton-collateral-1::12208903631325bcb3f6a87594729003aa53482189f278200572cb23b01e795a5afc`
  - custodian party `controlplane-custodian-1::12208903631325bcb3f6a87594729003aa53482189f278200572cb23b01e795a5afc`
  - operator party `controlplane-operator-1::12208903631325bcb3f6a87594729003aa53482189f278200572cb23b01e795a5afc`
  - obligation `quickstart-margin-obligation-001` with contract id `001cc057d2d710d0481f3958fb4a9a6ea24b0d6afe793c4daa1ffdf269ac04dfa5ca1212206f27aee27d9010d88f4304dae08c8151f1ba7979e4e56b0dba6f2ec3e84e00d4`
  - posting intent `quickstart-margin-posting-001` with contract id `00c3efadc11126a9b2c292ab1b877fb172de301b0ce9c59f7d27a0fc5c6ac1d94fca121220317035a2be0a176d559ce4b8f7552c4bd16c8c50d98a63c07a967bc3c382bcfd`
  - inventory lots `quickstart-us-tbill-lot-001` and `quickstart-us-tbill-lot-002`
- `make localnet-status-control-plane` passed and wrote `reports/generated/localnet-control-plane-status.json` plus `reports/generated/localnet-control-plane-status-summary.md`.
- the provider-visible status snapshot proves Quickstart now contains `1` visible obligation, `2` visible inventory lots, and `1` visible posting intent for the seeded scenario, with `0` execution reports and `0` encumbrances because full workflow execution has not started yet.
- `make docs-lint` passed after the tracker, runbook, ADR, invariant, and evidence surfaces were updated for the seeded Quickstart posture.
- `git diff --check` passed with no whitespace or patch-format issues.
- the seeded scenario is therefore real Quickstart ledger state with ledger-returned contract identifiers, not only a local manifest or IDE-ledger demo input.

## Remaining Blockers

- the seeded Quickstart scenario still stops at obligation, inventory, role-registration, and posting-intent state; there is not yet a Quickstart-backed execution report or settlement trace
- live asset adapters remain absent, so no real token, custodian, or venue movement executes beyond the seeded ledger state
- settlement-window enforcement and workflow-coupled optimizer reservation remain intentionally absent
- role-scoped disclosure profiles for execution, return, and substitution reports remain future work
