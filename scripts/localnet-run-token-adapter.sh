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

need_cmd git localnet-run-token-adapter
need_cmd docker localnet-run-token-adapter
need_cmd python3 localnet-run-token-adapter
need_cmd curl localnet-run-token-adapter

prepare_control_plane_dirs
require_bootstrapped_localnet localnet-run-token-adapter
ensure_running_control_plane_stack localnet-run-token-adapter

test -f "$LOCALNET_SEED_RECEIPT" || {
	echo "localnet-run-token-adapter: missing $LOCALNET_SEED_RECEIPT; run make localnet-seed-demo first" >&2
	exit 1
}

write_control_plane_auth_env
write_adapter_participant_config
write_adapter_input_from_seed_receipt

"$script_dir/run-quickstart-daml-script.sh" \
	--script-name CantonCollateral.QuickstartAdapter:referenceTokenAdapterReport \
	--participant-config "$ADAPTER_PARTICIPANT_CONFIG" \
	--input-file "$ADAPTER_INPUT_FILE" \
	--output-file "$LOCALNET_ADAPTER_EXECUTION_REPORT"

ADAPTER_REPORT_PATH="$LOCALNET_ADAPTER_EXECUTION_REPORT" ADAPTER_SUMMARY_PATH="$LOCALNET_ADAPTER_SUMMARY_MD" python3 - <<'PY'
import json
import os
from pathlib import Path

with open(os.environ["ADAPTER_REPORT_PATH"], "r", encoding="utf-8") as f:
    report = json.load(f)

summary = [
    "# Reference Token Adapter Summary",
    "",
    f"- Scenario id: `{report['scenarioId']}`",
    f"- Adapter: `{report['adapterName']}` `{report['adapterVersion']}`",
    f"- Workflow type: `{report['settlementInstruction']['workflowType']}`",
    f"- Settlement action: `{report['settlementInstruction']['settlementAction']}`",
    f"- Posting state before adapter preparation: `{report['workflowConfirmation']['postingStateBefore']}`",
    f"- Posting state after preparation: `{report['workflowConfirmation']['postingStateAfterPreparation']}`",
    f"- Posting state after confirmation: `{report['workflowConfirmation']['postingStateAfterConfirmation']}`",
    f"- Settled instruction state: `{report['workflowConfirmation']['settledInstructionState']}`",
    f"- Adapter receipt id: `{report['adapterReceipt']['receiptId']}`",
    f"- Adapter external transaction id: `{report['adapterReceipt']['externalTransactionId']}`",
    f"- Provider-visible encumbrances after confirmation: `{report['workflowConfirmation']['providerVisibleEncumbranceCount']}`",
    f"- Provider-visible execution reports after confirmation: `{report['workflowConfirmation']['providerVisibleExecutionReportCount']}`",
    "",
    "## Movements",
    "",
]

for movement in report["adapterReceipt"]["movements"]:
    summary.append(
        f"- Lot `{movement['lotId']}` moved `{movement['quantity']}` of `{movement['assetId']}` "
        f"from `{movement['sourceAccount']}` to `{movement['destinationAccount']}` with control state "
        f"`{movement['resultingControlState']}`"
    )

Path(os.environ["ADAPTER_SUMMARY_PATH"]).write_text("\n".join(summary) + "\n", encoding="utf-8")
PY

LOCALNET_WORKDIR="$LOCALNET_WORKDIR" \
LOCALNET_CONTROL_PLANE_STATE_DIR="$LOCALNET_CONTROL_PLANE_STATE_DIR" \
LOCALNET_CONTROL_PLANE_OUTPUT_DIR="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR" \
	"$script_dir/localnet-adapter-status.sh" >/dev/null

echo "localnet-run-token-adapter: wrote $LOCALNET_ADAPTER_EXECUTION_REPORT"
echo "localnet-run-token-adapter: wrote $LOCALNET_ADAPTER_SUMMARY_MD"
echo "localnet-run-token-adapter: refreshed $LOCALNET_ADAPTER_STATUS_JSON and $LOCALNET_ADAPTER_STATUS_MD"
