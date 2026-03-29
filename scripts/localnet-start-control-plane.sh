#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$script_dir/toolchain.env"
. "$repo_root/infra/quickstart/overlay/upstream-pin.env"

runtime_env="$repo_root/.runtime/env.sh"
LOCALNET_WORKDIR=${LOCALNET_WORKDIR:-"$repo_root/.runtime/localnet/cn-quickstart"}
quickstart_dir="$LOCALNET_WORKDIR/$QS_QUICKSTART_SUBDIR"
LOCALNET_ONBOARDING_CONTAINER=${LOCALNET_ONBOARDING_CONTAINER:-control-plane-splice-onboarding}

. "$script_dir/localnet-control-plane-common.sh"

need_cmd git localnet-start-control-plane
need_cmd docker localnet-start-control-plane
need_cmd make localnet-start-control-plane
need_cmd python3 localnet-start-control-plane
need_cmd curl localnet-start-control-plane

test -f "$runtime_env" || {
	echo "localnet-start-control-plane: missing $runtime_env; run make bootstrap first" >&2
	exit 1
}

. "$runtime_env"
export PATH JAVA_HOME DAML_HOME DAML_SDK_ROOT

prepare_control_plane_dirs
require_bootstrapped_localnet localnet-start-control-plane

cd "$quickstart_dir"
make --no-print-directory check-docker >/dev/null

if quickstart_validators_ready && docker inspect "$LOCALNET_ONBOARDING_CONTAINER" >/dev/null 2>&1; then
	quickstart_control_plane_compose ps >/dev/null
else
	remove_legacy_quickstart_runtime_containers
	quickstart_control_plane_compose up -d --no-recreate \
		postgres \
		keycloak \
		nginx-keycloak \
		canton \
		splice \
		splice-onboarding >/dev/null

	wait_for_quickstart_validators 300 || {
		echo "localnet-start-control-plane: Quickstart validators did not become ready within 300 seconds" >&2
		quickstart_control_plane_compose ps >&2 || true
		exit 1
	}
fi

LOCALNET_DEPLOY_RECEIPT="$LOCALNET_DEPLOYMENT_RECEIPT" \
LOCALNET_WORKDIR="$LOCALNET_WORKDIR" \
LOCALNET_PROFILE="${LOCALNET_PROFILE:-lean}" \
LOCALNET_PARTY_HINT="${LOCALNET_PARTY_HINT:-canton-collateral-1}" \
	"$script_dir/localnet-deploy-dar.sh"

LOCALNET_DEPLOYMENT_RECEIPT="$LOCALNET_DEPLOYMENT_RECEIPT" python3 - <<'PY'
import json
import os
from pathlib import Path

receipt_path = Path(os.environ["LOCALNET_DEPLOYMENT_RECEIPT"])
with receipt_path.open("r", encoding="utf-8") as f:
    receipt = json.load(f)

markdown = [
    "# LocalNet Control Plane Deployment Summary",
    "",
    f"- Quickstart commit: `{receipt['quickstartCommit']}`",
    f"- DAR file: `{receipt['darFile']}`",
    f"- Package id: `{receipt['packageId']}`",
    f"- Target participants: `{', '.join(receipt['participants'])}`",
    f"- Onboarding container: `{receipt['onboardingContainer']}`",
]

summary_path = receipt_path.with_name("localnet-control-plane-deployment-summary.md")
summary_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")
PY

echo "localnet-start-control-plane: wrote $LOCALNET_DEPLOYMENT_RECEIPT"
echo "localnet-start-control-plane: wrote ${LOCALNET_DEPLOYMENT_RECEIPT%/*}/localnet-control-plane-deployment-summary.md"
