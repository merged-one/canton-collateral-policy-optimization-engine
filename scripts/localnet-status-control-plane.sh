#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$script_dir/toolchain.env"
. "$repo_root/infra/quickstart/overlay/upstream-pin.env"

LOCALNET_WORKDIR=${LOCALNET_WORKDIR:-"$repo_root/.runtime/localnet/cn-quickstart"}
quickstart_dir="$LOCALNET_WORKDIR/$QS_QUICKSTART_SUBDIR"
LOCALNET_ONBOARDING_CONTAINER=${LOCALNET_ONBOARDING_CONTAINER:-control-plane-splice-onboarding}

. "$script_dir/localnet-control-plane-common.sh"

need_cmd git localnet-status-control-plane
need_cmd docker localnet-status-control-plane
need_cmd python3 localnet-status-control-plane
need_cmd curl localnet-status-control-plane

prepare_control_plane_dirs
require_bootstrapped_localnet localnet-status-control-plane
ensure_running_control_plane_stack localnet-status-control-plane

test -f "$LOCALNET_SEED_RECEIPT" || {
	echo "localnet-status-control-plane: missing $LOCALNET_SEED_RECEIPT; run make localnet-seed-demo first" >&2
	exit 1
}

write_control_plane_auth_env
write_status_participant_config
write_status_input_from_seed_receipt

"$script_dir/run-quickstart-daml-script.sh" \
	--script-name CantonCollateral.QuickstartSeed:statusForProviderView \
	--participant-config "$STATUS_PARTICIPANT_CONFIG" \
	--input-file "$STATUS_INPUT_FILE" \
	--output-file "$LOCALNET_STATUS_JSON"

STATUS_JSON_PATH="$LOCALNET_STATUS_JSON" \
SEED_RECEIPT_PATH="$LOCALNET_SEED_RECEIPT" \
DEPLOYMENT_RECEIPT_PATH="$LOCALNET_DEPLOYMENT_RECEIPT" \
STATUS_MD_PATH="$LOCALNET_STATUS_MD" \
python3 - <<'PY'
import json
import os
from pathlib import Path

with open(os.environ["STATUS_JSON_PATH"], "r", encoding="utf-8") as f:
    status = json.load(f)
with open(os.environ["SEED_RECEIPT_PATH"], "r", encoding="utf-8") as f:
    receipt = json.load(f)

deployment = {}
deployment_path = Path(os.environ["DEPLOYMENT_RECEIPT_PATH"])
if deployment_path.exists():
    with deployment_path.open("r", encoding="utf-8") as f:
        deployment = json.load(f)

lines = [
    "# LocalNet Control Plane Status",
    "",
    f"- Scenario id: `{status['scenarioId']}`",
    f"- Quickstart seeded: `{status['seeded']}`",
    f"- Provider party: `{receipt['providerParty']}`",
    f"- Secured party: `{receipt['securedParty']}`",
    f"- Custodian party: `{receipt['custodianParty']}`",
    f"- Operator party: `{receipt['operatorParty']}`",
]

if deployment:
    lines.append(f"- Package id: `{deployment['packageId']}`")
    lines.append(f"- Quickstart commit: `{deployment['quickstartCommit']}`")

lines.extend(
    [
        "",
        "## Provider View",
        "",
        f"- Role registrations visible: `{len(status['providerRoleRegistrations'])}`",
        f"- Obligations visible: `{len(status['providerVisibleObligations'])}`",
        f"- Inventory lots visible: `{len(status['providerVisibleInventoryLots'])}`",
        f"- Posting intents visible: `{len(status['providerVisiblePostingIntents'])}`",
        f"- Execution reports visible: `{status['providerVisibleExecutionReportCount']}`",
        f"- Encumbrances visible: `{status['providerVisibleEncumbranceCount']}`",
        "",
        "## Seeded Contracts",
        "",
        f"- Call obligation cid: `{receipt['obligationContractId']}`",
        f"- Posting intent cid: `{receipt['postingIntentContractId']}`",
    ]
)

for lot in receipt["inventoryLots"]:
    lines.append(f"- Inventory lot `{lot['lotId']}` cid: `{lot['contractId']}`")

Path(os.environ["STATUS_MD_PATH"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

echo "localnet-status-control-plane: wrote $LOCALNET_STATUS_JSON"
echo "localnet-status-control-plane: wrote $LOCALNET_STATUS_MD"
