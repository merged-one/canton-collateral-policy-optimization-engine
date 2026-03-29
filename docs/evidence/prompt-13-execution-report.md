# Prompt 13 Execution Report

## Scope

Close the runtime or version bridge between the repo-default Daml toolchain and the pinned upstream Quickstart runtime line so the Canton Collateral Control Plane DAR can be built and installed into the pinned Quickstart LocalNet through a real reproducible command surface.

## Runtime Decision

ADR 0016 chooses a dual-runtime bridge:

- keep the repo-default host toolchain on Daml SDK `2.10.4` plus JDK `17` for the existing IDE-ledger workflow surface
- build Quickstart-compatible DARs in Docker on Daml SDK `3.4.10` plus Java `21`
- keep one shared Control Plane Daml source tree and fix source compatibility rather than forking a Quickstart-only package

## Commands

```sh
make localnet-bootstrap
make daml-build
make daml-test
make localnet-build-dar
make check-docker
. /Users/charlesdusek/Code/canton-collateral-control-plane/.runtime/env.sh && make build
. ./scripts/toolchain.env && docker run --rm -i -v "$PWD/.runtime/localnet/cn-quickstart/quickstart:/workspace" -w /workspace/daml/licensing -e QUICKSTART_DAML_SDK_VERSION="$QUICKSTART_DAML_SDK_VERSION" -e QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE="$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE" -e QUICKSTART_DAML_SDK_LINUX_AARCH64_URL="$QUICKSTART_DAML_SDK_LINUX_AARCH64_URL" -e QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256="$QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256" ubuntu:24.04 /bin/sh <<'EOF'
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update >/dev/null
apt-get install -y ca-certificates curl gzip openjdk-21-jdk-headless tar >/dev/null
curl -fsSL "$QUICKSTART_DAML_SDK_LINUX_AARCH64_URL" -o "/tmp/$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE"
echo "$QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256  /tmp/$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE" | sha256sum -c - >/dev/null
tar -xzf "/tmp/$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE" -C /tmp
sdk_dir="/tmp/sdk-$QUICKSTART_DAML_SDK_VERSION"
export PATH="$sdk_dir/daml:$sdk_dir/daml-helper:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64
export DAML_HOME=/tmp/daml-home
mkdir -p "$DAML_HOME/sdk" "$DAML_HOME/bin"
ln -s "$sdk_dir" "$DAML_HOME/sdk/$QUICKSTART_DAML_SDK_VERSION"
ln -s "$sdk_dir/daml/daml" "$DAML_HOME/bin/daml"
cat > "$DAML_HOME/daml-config.yaml" <<CFG
update-check: never
auto-install: false
CFG
daml build --project-root /workspace/daml/licensing
EOF
export MODULES_DIR="$PWD/docker/modules" LOCALNET_DIR="$PWD/docker/modules/localnet" LOCALNET_ENV_DIR="$PWD/docker/modules/localnet/env" IMAGE_TAG="$(sed -n 's/^SPLICE_VERSION=//p' .env)" && docker compose --profile app-provider --profile app-user --profile sv --profile swagger-ui --profile pqs-app-provider --profile keycloak -f compose.yaml -f "$LOCALNET_DIR/compose.yaml" -f "$MODULES_DIR/keycloak/compose.yaml" -f "$MODULES_DIR/splice-onboarding/compose.yaml" -f "$MODULES_DIR/pqs/compose.yaml" --env-file .env --env-file .env.local --env-file "$LOCALNET_DIR/compose.env" --env-file "$LOCALNET_ENV_DIR/common.env" --env-file "$MODULES_DIR/keycloak/compose.env" --env-file "$MODULES_DIR/pqs/compose.env" up -d --build keycloak nginx-keycloak canton splice splice-onboarding
make localnet-deploy-dar
make docs-lint
make verify-portable
make verify
git diff --check
git status --short --branch
```

## Results

- `make localnet-bootstrap` passed and staged the pinned upstream CN Quickstart checkout at commit `fe56d460af650b71b8e20098b3e76693397a8bf9`.
- `make daml-build` and `make daml-test` passed after the Daml source was updated to compile on both runtime lines, including the keyless `ReturnRequestRegistry` replay guard and template-specific contract query helpers.
- `make localnet-build-dar` passed and produced `.daml/dist-quickstart/canton-collateral-control-plane-0.1.0.dar` with main package id `fc0d45f0d0ee032245807bdeba0be201d3c5c9518fa150cf804985440b05efe8`.
- `make check-docker` passed inside the pinned Quickstart checkout.
- `. /Users/charlesdusek/Code/canton-collateral-control-plane/.runtime/env.sh && make build` in the upstream Quickstart checkout failed at `:daml:verifyDamlSdkVersion` because the host path intentionally remained on Daml `2.10.4`; that failure confirmed the repo should not pretend the full upstream host build is the bridge.
- the direct Dockerized `daml build --project-root /workspace/daml/licensing` command passed and produced the upstream Quickstart licensing DAR needed by the onboarding container.
- the direct Docker Compose startup command passed after the keycloak overlay was included and brought up the minimal pinned Quickstart runtime slice needed for package upload: `postgres`, `keycloak`, `nginx-keycloak`, `canton`, `splice`, and `splice-onboarding`.
- intermediate `make localnet-deploy-dar` attempts failed for repo-owned reasons before the final success:
  - the first attempt exposed a missing `-i` flag in the bridge container invocation, so the embedded shell payload never ran
  - the next attempt exposed missing `compose.env` defaults in `scripts/localnet-deploy-dar.sh`
  - the next attempt exposed container-path metadata (`/workspace/...`) leaking into the host-side DAR metadata file
  - the next attempt reached the participant package API but failed with `401` until the Quickstart keycloak module was included in the running stack
- the final `make localnet-deploy-dar` run passed and uploaded `canton-collateral-control-plane-0.1.0.dar` to both the app-provider and app-user participants on the pinned Quickstart LocalNet.
- `make docs-lint` passed after ADR 0016, the Prompt 13 execution report, and the tracker or dependency updates were added to the required documentation surface.
- `make verify-portable` passed and re-ran docs linting, CPL validation, policy-engine tests, optimizer tests, Daml build, Daml lifecycle tests, the aggregate conformance suite, and the final demo pack.
- `make verify` passed and re-ran the full `make verify-portable` surface plus the pinned Quickstart smoke path against the running LocalNet.
- `git diff --check` passed with no whitespace or patch-format issues.
- `git status --short --branch` before commit showed only the expected Prompt 13 code, documentation, tracker, ADR, generated-artifact, and evidence changes.
- the Control Plane DAR was successfully built against the chosen bridge strategy.
- deployment into the pinned Quickstart LocalNet succeeded.

## Residual Risks

- the bridge is still dual-runtime, so future Daml source changes must continue to be checked against both the host-native `2.10.4` path and the containerized Quickstart `3.4.10` path
- the current proof installs the DAR into Quickstart participants but does not yet run a full seeded Control Plane workflow there
- the Quickstart stack startup remains upstream-owned rather than wrapped in a repo Make target, so runtime bring-up still depends on documented operator steps or equivalent compose commands
