# LocalNet Control Plane Runbook

## Purpose

Bootstrap the pinned Quickstart checkout, start the repo-owned isolated overlay, deploy the Canton Collateral Control Plane DAR, seed the default confidential collateral scenario, inspect the resulting Quickstart state, and tear the environment down cleanly.

This runbook covers the Prompt 14 Quickstart surface only. The existing IDE-ledger demos remain documented in the margin-call, return, substitution, and final-demo runbooks.

## Prerequisites

- run from the repository root
- Docker Desktop or an equivalent Docker runtime is running
- `make bootstrap` has completed successfully
- the host can reach `host.docker.internal`

Optional overrides:

- `LOCALNET_PROFILE=faithful` to keep the upstream observability path enabled
- `LOCALNET_PARTY_HINT=canton-demo-1` to change the staged Quickstart overlay hint
- `LOCALNET_SCENARIO_MANIFEST=infra/quickstart/scenarios/confidential-margin-scenario.json` to point at a different seed manifest

## Bootstrap

Stage the pinned upstream Quickstart checkout and write the repo-owned `.env.local` overlay:

```sh
make localnet-bootstrap
```

Expected outcome:

- `.runtime/localnet/cn-quickstart/quickstart/` exists
- `.runtime/localnet/cn-quickstart/quickstart/.env.local` reflects the selected overlay profile
- the pinned Quickstart commit remains `fe56d460af650b71b8e20098b3e76693397a8bf9`

## Start And Deploy

Start or reuse the isolated overlay runtime and deploy the Control Plane DAR:

```sh
make localnet-start-control-plane
```

What this command does:

- validates the staged Quickstart checkout and Docker prerequisites
- starts the repo-owned overlay runtime on Docker network `quickstart-control-plane`
- uses the repo-owned compose override so the runtime container names remain `control-plane-*`
- builds the Quickstart-compatible DAR if needed
- uploads the DAR into the Quickstart `app-provider` and `app-user` participants
- writes:
  - `reports/generated/localnet-control-plane-deployment-receipt.json`
  - `reports/generated/localnet-control-plane-deployment-summary.md`

The current default successful deployment proof shows:

- DAR file: `.daml/dist-quickstart/canton-collateral-control-plane-0.1.1.dar`
- package id: `829c57ff1186dd09d4e3e232f2ac08c447de2bfe7c7f3b0cc3bf433fb3190f63`
- onboarding container: `control-plane-splice-onboarding`

## Seed

Seed the default confidential margin-style scenario:

```sh
make localnet-seed-demo
```

What this command seeds:

- provider role anchored on the existing Quickstart `app-user` party
- secured-party role anchored on the existing Quickstart `app-provider` party
- repo-allocated custodian party `controlplane-custodian-1`
- repo-allocated operator party `controlplane-operator-1`
- obligation `quickstart-margin-obligation-001`
- posting intent `quickstart-margin-posting-001`
- inventory lots `quickstart-us-tbill-lot-001` and `quickstart-us-tbill-lot-002`

Generated artifacts:

- `reports/generated/localnet-control-plane-seed-receipt.json`
- refreshed `reports/generated/localnet-control-plane-status.json`
- refreshed `reports/generated/localnet-control-plane-status-summary.md`

Current default seed result:

- scenario id: `quickstart-confidential-margin-001`
- obligation state: `Submitted`
- posting intent state: `Submitted`
- provider-visible inventory-lot count: `2`
- provider-visible execution-report count: `0`

`make localnet-seed-demo` is idempotent for the default manifest. If the scenario is already present, the command keeps the existing seed receipt and refreshes status instead of creating duplicate state.

## Inspect

Refresh the provider-visible Quickstart status summary:

```sh
make localnet-status-control-plane
```

Inspect the generated Markdown summary:

```sh
sed -n '1,220p' reports/generated/localnet-control-plane-status-summary.md
```

Inspect the machine-readable status snapshot:

```sh
cat reports/generated/localnet-control-plane-status.json
```

Inspect the running overlay containers:

```sh
docker ps --format 'table {{.Names}}\t{{.Status}}' --filter network=quickstart-control-plane
```

The default status snapshot currently proves:

- the scenario id is `quickstart-confidential-margin-001`
- the seeded flag is `true`
- the provider-visible view sees `1` obligation, `2` inventory lots, and `1` posting intent
- no execution reports or encumbrances exist yet because Prompt 14 stops at seeded state rather than full workflow execution

## Teardown

To stop and remove the repo-owned overlay runtime, run:

```sh
cd .runtime/localnet/cn-quickstart/quickstart
MODULES_DIR="$PWD/docker/modules"
LOCALNET_DIR="$MODULES_DIR/localnet"
LOCALNET_ENV_DIR="$LOCALNET_DIR/env"
unset APP_PROVIDER_AUTH_ENV APP_USER_AUTH_ENV SV_AUTH_ENV
docker compose \
  --project-name quickstart \
  --project-directory "$PWD" \
  -f compose.yaml \
  -f "$LOCALNET_DIR/compose.yaml" \
  -f "$MODULES_DIR/keycloak/compose.yaml" \
  -f "$MODULES_DIR/splice-onboarding/compose.yaml" \
  -f "/Users/charlesdusek/Code/canton-collateral-control-plane/infra/quickstart/overlay/control-plane-compose.yaml" \
  --env-file .env \
  --env-file .env.local \
  --env-file "$LOCALNET_DIR/compose.env" \
  --env-file "$LOCALNET_ENV_DIR/common.env" \
  --env-file "$MODULES_DIR/keycloak/compose.env" \
  --profile app-provider \
  --profile app-user \
  --profile sv \
  --profile keycloak \
  down -v
```

If you only need to re-query status or reseed the existing scenario, do not tear the stack down.

## Common Failure Modes

- `bootstrap-localnet.sh: missing pinned checkout` or similar bootstrap errors
  Run `make localnet-bootstrap` first and confirm `.runtime/localnet/cn-quickstart/quickstart/` exists.
- Docker or compose prerequisites missing
  Start Docker and rerun `make localnet-smoke` or `make localnet-start-control-plane`.
- validator readiness timeout
  Inspect `docker ps` on `quickstart-control-plane` and retry `make localnet-start-control-plane` after the runtime stabilizes.
- onboarding auth export fails
  Confirm `control-plane-splice-onboarding` is running and the OAuth2 Keycloak sidecars are healthy.
- seed command fails before writing a receipt
  Re-run `make localnet-status-control-plane` only after `make localnet-seed-demo` succeeds; the status command depends on `reports/generated/localnet-control-plane-seed-receipt.json`.
- status shows no seeded scenario
  Rerun `make localnet-seed-demo`; if it still fails, inspect `reports/generated/localnet-control-plane-seed-receipt.json` and the onboarding or canton container logs.

## Remaining Boundary

This runbook proves that the Control Plane package can be deployed and that one confidential scenario can be seeded and queried on Quickstart. It does not yet prove live asset movement, settlement-window enforcement, workflow-coupled optimizer reservation, or a Quickstart-backed execution report.
