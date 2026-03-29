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

need_cmd git localnet-seed-demo
need_cmd docker localnet-seed-demo
need_cmd python3 localnet-seed-demo
need_cmd curl localnet-seed-demo

prepare_control_plane_dirs
require_bootstrapped_localnet localnet-seed-demo
ensure_running_control_plane_stack localnet-seed-demo

test -f "${LOCALNET_DAR_OUTPUT_DIR:-"$repo_root/.daml/dist-quickstart"}/quickstart-dar-metadata.env" || {
	echo "localnet-seed-demo: missing Quickstart DAR metadata; run make localnet-start-control-plane or make localnet-deploy-dar first" >&2
	exit 1
}

if [ -f "$LOCALNET_SEED_RECEIPT" ]; then
	if CURRENT_SEED_RECEIPT="$LOCALNET_SEED_RECEIPT" CURRENT_SCENARIO_MANIFEST="${LOCALNET_SCENARIO_MANIFEST:-"$repo_root/infra/quickstart/scenarios/confidential-margin-scenario.json"}" python3 - <<'PY'
import json
import os
import sys

with open(os.environ["CURRENT_SEED_RECEIPT"], "r", encoding="utf-8") as f:
    receipt = json.load(f)
with open(os.environ["CURRENT_SCENARIO_MANIFEST"], "r", encoding="utf-8") as f:
    scenario = json.load(f)

if receipt.get("scenarioId") == scenario.get("scenarioId"):
    sys.exit(0)
sys.exit(1)
PY
	then
		LOCALNET_WORKDIR="$LOCALNET_WORKDIR" \
		LOCALNET_CONTROL_PLANE_STATE_DIR="$LOCALNET_CONTROL_PLANE_STATE_DIR" \
		LOCALNET_CONTROL_PLANE_OUTPUT_DIR="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR" \
			"$script_dir/localnet-status-control-plane.sh" >/dev/null
		if SEED_STATUS_PATH="$LOCALNET_STATUS_JSON" python3 - <<'PY'
import json
import os
import sys

with open(os.environ["SEED_STATUS_PATH"], "r", encoding="utf-8") as f:
    status = json.load(f)

if status.get("seeded"):
    sys.exit(0)
sys.exit(1)
PY
		then
		echo "localnet-seed-demo: scenario already active on Quickstart; refreshed status artifacts instead of reseeding"
		exit 0
		fi
	fi
fi

write_control_plane_auth_env
write_seed_participant_config
write_seed_input_from_manifest localnet-seed-demo

"$script_dir/run-quickstart-daml-script.sh" \
	--script-name CantonCollateral.QuickstartSeed:seedScenario \
	--participant-config "$SEED_PARTICIPANT_CONFIG" \
	--input-file "$SEED_INPUT_FILE" \
	--output-file "$LOCALNET_SEED_RECEIPT"

SEED_RECEIPT_PATH="$LOCALNET_SEED_RECEIPT" SEED_INPUT_PATH="$SEED_INPUT_FILE" python3 - <<'PY'
import json
import os
from pathlib import Path

receipt_path = Path(os.environ["SEED_RECEIPT_PATH"])
with receipt_path.open("r", encoding="utf-8") as f:
    receipt = json.load(f)
with open(os.environ["SEED_INPUT_PATH"], "r", encoding="utf-8") as f:
    seed_input = json.load(f)

receipt["obligationId"] = seed_input["obligationId"]
receipt["postingId"] = seed_input["postingId"]

with receipt_path.open("w", encoding="utf-8") as f:
    json.dump(receipt, f, indent=2)
    f.write("\n")
PY

LOCALNET_WORKDIR="$LOCALNET_WORKDIR" \
LOCALNET_CONTROL_PLANE_STATE_DIR="$LOCALNET_CONTROL_PLANE_STATE_DIR" \
LOCALNET_CONTROL_PLANE_OUTPUT_DIR="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR" \
	"$script_dir/localnet-status-control-plane.sh" >/dev/null

echo "localnet-seed-demo: wrote $LOCALNET_SEED_RECEIPT"
echo "localnet-seed-demo: refreshed $LOCALNET_STATUS_JSON and $LOCALNET_STATUS_MD"
