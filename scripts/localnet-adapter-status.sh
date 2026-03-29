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

need_cmd git localnet-adapter-status
need_cmd docker localnet-adapter-status
need_cmd python3 localnet-adapter-status
need_cmd curl localnet-adapter-status

prepare_control_plane_dirs
require_bootstrapped_localnet localnet-adapter-status
ensure_running_control_plane_stack localnet-adapter-status

test -f "$LOCALNET_SEED_RECEIPT" || {
	echo "localnet-adapter-status: missing $LOCALNET_SEED_RECEIPT; run make localnet-seed-demo first" >&2
	exit 1
}

write_control_plane_auth_env
write_adapter_participant_config
write_adapter_status_input_from_seed_receipt

"$script_dir/run-quickstart-daml-script.sh" \
	--script-name CantonCollateral.QuickstartAdapter:referenceTokenAdapterStatus \
	--participant-config "$ADAPTER_PARTICIPANT_CONFIG" \
	--input-file "$ADAPTER_STATUS_INPUT_FILE" \
	--output-file "$LOCALNET_ADAPTER_STATUS_JSON"

ADAPTER_STATUS_PATH="$LOCALNET_ADAPTER_STATUS_JSON" ADAPTER_STATUS_MD_PATH="$LOCALNET_ADAPTER_STATUS_MD" python3 - <<'PY'
import json
import os
from pathlib import Path

with open(os.environ["ADAPTER_STATUS_PATH"], "r", encoding="utf-8") as f:
    status = json.load(f)

lines = [
    "# Reference Token Adapter Status",
    "",
    f"- Scenario id: `{status['scenarioId']}`",
    f"- Posting state: `{status['postingState']}`",
    f"- Settlement instruction state: `{status['settlementInstructionState']}`",
    f"- Provider-visible execution reports: `{status['providerVisibleExecutionReportCount']}`",
    f"- Provider-visible encumbrances: `{status['providerVisibleEncumbranceCount']}`",
    f"- Provider-visible reference token holdings: `{len(status['providerVisibleReferenceTokenHoldings'])}`",
    f"- Provider-visible adapter receipts: `{len(status['providerVisibleAdapterReceipts'])}`",
    "",
    "## Holdings",
    "",
]

for holding in status["providerVisibleReferenceTokenHoldings"]:
    lines.append(
        f"- Holding `{holding['holdingId']}` lot `{holding['lotId']}` owner `{holding['beneficialOwner']}` "
        f"account `{holding['accountId']}` quantity `{holding['quantity']}` state `{holding['controlState']}`"
    )

lines.extend(["", "## Receipts", ""])

for receipt in status["providerVisibleAdapterReceipts"]:
    lines.append(
        f"- Receipt `{receipt['receiptId']}` instruction `{receipt['instructionId']}` "
        f"action `{receipt['settlementAction']}` status `{receipt['status']}` "
        f"external transaction `{receipt['externalTransactionId']}`"
    )

Path(os.environ["ADAPTER_STATUS_MD_PATH"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

echo "localnet-adapter-status: wrote $LOCALNET_ADAPTER_STATUS_JSON"
echo "localnet-adapter-status: wrote $LOCALNET_ADAPTER_STATUS_MD"
