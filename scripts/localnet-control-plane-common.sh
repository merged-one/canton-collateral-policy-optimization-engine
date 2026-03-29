need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "$2: missing required command '$1'" >&2
		exit 1
	}
}

require_bootstrapped_localnet() {
	test -d "$LOCALNET_WORKDIR/.git" || {
		echo "$1: missing Quickstart checkout; run make localnet-bootstrap first" >&2
		exit 1
	}

	current_commit=$(git -C "$LOCALNET_WORKDIR" rev-parse HEAD)
	test "$current_commit" = "$QS_COMMIT" || {
		echo "$1: expected pinned commit $QS_COMMIT but found $current_commit" >&2
		exit 1
	}

	test -f "$quickstart_dir/.env.local" || {
		echo "$1: missing $quickstart_dir/.env.local; run make localnet-bootstrap first" >&2
		exit 1
	}
}

load_quickstart_runtime_env() {
	set -a
	. "$quickstart_dir/.env"
	. "$quickstart_dir/.env.local"
	MODULES_DIR=${MODULES_DIR:-"$quickstart_dir/docker/modules"}
	IMAGE_TAG=${IMAGE_TAG:-"$SPLICE_VERSION"}
	LOCALNET_DIR=${LOCALNET_DIR:-"$quickstart_dir/docker/modules/localnet"}
	LOCALNET_ENV_DIR=${LOCALNET_ENV_DIR:-"$LOCALNET_DIR/env"}
	export MODULES_DIR IMAGE_TAG LOCALNET_DIR LOCALNET_ENV_DIR
	. "$LOCALNET_DIR/compose.env"
	. "$LOCALNET_ENV_DIR/common.env"
	set +a
}

quickstart_validators_ready() {
	load_quickstart_runtime_env
	for readyz_url in \
		"http://localhost:2${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz" \
		"http://localhost:3${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz" \
		"http://localhost:4${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz"
	do
		curl -fsS "$readyz_url" >/dev/null 2>&1 || return 1
	done
}

wait_for_quickstart_validators() {
	timeout_seconds=${1:-300}
	elapsed=0
	while [ "$elapsed" -lt "$timeout_seconds" ]; do
		quickstart_validators_ready && return 0
		sleep 5
		elapsed=$((elapsed + 5))
	done
	return 1
}

quickstart_control_plane_compose() {
	load_quickstart_runtime_env
	unset APP_PROVIDER_AUTH_ENV APP_USER_AUTH_ENV SV_AUTH_ENV
	docker compose \
		--project-name quickstart \
		--project-directory "$quickstart_dir" \
		-f "$quickstart_dir/docker/modules/localnet/compose.yaml" \
		-f "$quickstart_dir/docker/modules/keycloak/compose.yaml" \
		-f "$quickstart_dir/docker/modules/splice-onboarding/compose.yaml" \
		-f "$repo_root/infra/quickstart/overlay/control-plane-compose.yaml" \
		--env-file "$quickstart_dir/.env" \
		--env-file "$quickstart_dir/.env.local" \
		--env-file "$LOCALNET_DIR/compose.env" \
		--env-file "$LOCALNET_ENV_DIR/common.env" \
		--env-file "$quickstart_dir/docker/modules/keycloak/compose.env" \
		--profile app-provider \
		--profile app-user \
		--profile sv \
		--profile keycloak \
		"$@"
}

remove_legacy_quickstart_runtime_containers() {
	for container_name in \
		postgres \
		keycloak \
		nginx-keycloak \
		canton \
		splice \
		splice-onboarding \
		control-plane-postgres \
		control-plane-keycloak \
		control-plane-nginx-keycloak \
		control-plane-canton \
		control-plane-splice \
		control-plane-splice-onboarding
	do
		container_id=$(docker ps -aq --filter "name=^${container_name}$" | head -n 1)
		[ -n "$container_id" ] || continue

		project=$(docker inspect "$container_id" --format '{{ index .Config.Labels "com.docker.compose.project" }}' 2>/dev/null || true)
		working_dir=$(docker inspect "$container_id" --format '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}' 2>/dev/null || true)

		if [ "$project" = "quickstart" ] && [ "$working_dir" = "$quickstart_dir" ]; then
			docker rm -f "$container_id" >/dev/null
		fi
	done
}

ensure_running_control_plane_stack() {
	load_quickstart_runtime_env
	running_containers=$(docker ps --quiet --filter "network=${DOCKER_NETWORK:-quickstart}")
	test -n "$running_containers" || {
		echo "$1: the Quickstart stack is not running" >&2
		echo "$1: from $quickstart_dir run make build && make start, or use make localnet-start-control-plane" >&2
		exit 1
	}

	docker inspect "${LOCALNET_ONBOARDING_CONTAINER:-control-plane-splice-onboarding}" >/dev/null 2>&1 || {
		echo "$1: onboarding container '${LOCALNET_ONBOARDING_CONTAINER:-control-plane-splice-onboarding}' is not present in the running Quickstart stack" >&2
		exit 1
	}

	command -v curl >/dev/null 2>&1 || {
		echo "$1: missing required command 'curl'" >&2
		exit 1
	}

	quickstart_validators_ready || {
		echo "$1: the Quickstart stack is running but validator services are not ready" >&2
		echo "$1: run make localnet-start-control-plane to start or recover the full stack" >&2
		exit 1
	}
}

prepare_control_plane_dirs() {
	LOCALNET_CONTROL_PLANE_STATE_DIR=${LOCALNET_CONTROL_PLANE_STATE_DIR:-"$repo_root/.runtime/localnet/control-plane"}
	LOCALNET_CONTROL_PLANE_OUTPUT_DIR=${LOCALNET_CONTROL_PLANE_OUTPUT_DIR:-"$repo_root/reports/generated"}
	mkdir -p "$LOCALNET_CONTROL_PLANE_STATE_DIR" "$LOCALNET_CONTROL_PLANE_OUTPUT_DIR"
	AUTH_ENV_FILE="$LOCALNET_CONTROL_PLANE_STATE_DIR/auth.env"
	SEED_PARTICIPANT_CONFIG="$LOCALNET_CONTROL_PLANE_STATE_DIR/seed-participant-config.json"
	STATUS_PARTICIPANT_CONFIG="$LOCALNET_CONTROL_PLANE_STATE_DIR/status-participant-config.json"
	SEED_INPUT_FILE="$LOCALNET_CONTROL_PLANE_STATE_DIR/seed-input.json"
	STATUS_INPUT_FILE="$LOCALNET_CONTROL_PLANE_STATE_DIR/status-input.json"
	LOCALNET_DEPLOYMENT_RECEIPT="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR/localnet-control-plane-deployment-receipt.json"
	LOCALNET_SEED_RECEIPT="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR/localnet-control-plane-seed-receipt.json"
	LOCALNET_STATUS_JSON="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR/localnet-control-plane-status.json"
	LOCALNET_STATUS_MD="$LOCALNET_CONTROL_PLANE_OUTPUT_DIR/localnet-control-plane-status-summary.md"
}

write_control_plane_auth_env() {
	docker exec "${LOCALNET_ONBOARDING_CONTAINER:-control-plane-splice-onboarding}" \
		bash -lc '
set -euo pipefail
export DO_INIT=false
source /app/utils.sh
source /app/app-provider-auth.sh
source /app/app-user-auth.sh
APP_USER_WALLET_ADMIN_TOKEN=$(get_user_token "$AUTH_APP_USER_WALLET_ADMIN_USER_NAME" "$AUTH_APP_USER_WALLET_ADMIN_USER_PASSWORD" "$AUTH_APP_USER_AUTO_CONFIG_CLIENT_ID" "$AUTH_APP_USER_TOKEN_URL")
cat <<EOF
APP_PROVIDER_PARTICIPANT_ADMIN_TOKEN=$APP_PROVIDER_PARTICIPANT_ADMIN_TOKEN
APP_PROVIDER_PARTY=$APP_PROVIDER_PARTY
APP_PROVIDER_VALIDATOR_USER_ID=$AUTH_APP_PROVIDER_VALIDATOR_USER_ID
APP_PROVIDER_WALLET_ADMIN_USER_ID=$AUTH_APP_PROVIDER_WALLET_ADMIN_USER_ID
APP_USER_PARTICIPANT_ADMIN_TOKEN=$APP_USER_PARTICIPANT_ADMIN_TOKEN
APP_USER_PARTY=$APP_USER_PARTY
APP_USER_VALIDATOR_USER_ID=$AUTH_APP_USER_VALIDATOR_USER_ID
APP_USER_WALLET_ADMIN_TOKEN=$APP_USER_WALLET_ADMIN_TOKEN
APP_USER_WALLET_ADMIN_USER_ID=$AUTH_APP_USER_WALLET_ADMIN_USER_ID
EOF
' > "$AUTH_ENV_FILE"
	chmod 600 "$AUTH_ENV_FILE"
}

write_seed_participant_config() {
	load_quickstart_runtime_env
	set -a
	. "$AUTH_ENV_FILE"
	set +a
	APP_USER_LEDGER_PORT="2${PARTICIPANT_LEDGER_API_PORT_SUFFIX}" \
	APP_PROVIDER_LEDGER_PORT="3${PARTICIPANT_LEDGER_API_PORT_SUFFIX}" \
	PARTICIPANT_CONFIG_PATH="$SEED_PARTICIPANT_CONFIG" python3 - <<'PY'
import json
import os

path = os.environ["PARTICIPANT_CONFIG_PATH"]
config = {
    "default_participant": {
        "host": "host.docker.internal",
        "port": int(os.environ["APP_USER_LEDGER_PORT"]),
        "access_token": os.environ["APP_USER_PARTICIPANT_ADMIN_TOKEN"],
        "application_id": "localnet-control-plane-seed",
    },
    "participants": {
        "app-user-admin": {
            "host": "host.docker.internal",
            "port": int(os.environ["APP_USER_LEDGER_PORT"]),
            "access_token": os.environ["APP_USER_PARTICIPANT_ADMIN_TOKEN"],
            "application_id": "localnet-control-plane-seed",
        },
        "app-provider-admin": {
            "host": "host.docker.internal",
            "port": int(os.environ["APP_PROVIDER_LEDGER_PORT"]),
            "access_token": os.environ["APP_PROVIDER_PARTICIPANT_ADMIN_TOKEN"],
            "application_id": "localnet-control-plane-seed",
        },
    },
    "party_participants": {
        os.environ["APP_USER_PARTY"]: "app-user-admin",
        os.environ["APP_PROVIDER_PARTY"]: "app-provider-admin",
    },
}
with open(path, "w", encoding="ascii") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PY
}

write_status_participant_config() {
	load_quickstart_runtime_env
	set -a
	. "$AUTH_ENV_FILE"
	set +a
	APP_USER_LEDGER_PORT="2${PARTICIPANT_LEDGER_API_PORT_SUFFIX}" \
	SEED_RECEIPT_PATH="$LOCALNET_SEED_RECEIPT" \
	PARTICIPANT_CONFIG_PATH="$STATUS_PARTICIPANT_CONFIG" \
	python3 - <<'PY'
import json
import os

with open(os.environ["SEED_RECEIPT_PATH"], "r", encoding="utf-8") as f:
    receipt = json.load(f)

config = {
    "default_participant": {
        "host": "host.docker.internal",
        "port": int(os.environ["APP_USER_LEDGER_PORT"]),
        "access_token": os.environ["APP_USER_WALLET_ADMIN_TOKEN"],
        "application_id": "localnet-control-plane-status",
    },
    "participants": {
        "app-user-provider": {
            "host": "host.docker.internal",
            "port": int(os.environ["APP_USER_LEDGER_PORT"]),
            "access_token": os.environ["APP_USER_WALLET_ADMIN_TOKEN"],
            "application_id": "localnet-control-plane-status",
        }
    },
    "party_participants": {
        receipt["providerParty"]: "app-user-provider",
    },
}
with open(os.environ["PARTICIPANT_CONFIG_PATH"], "w", encoding="ascii") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PY
}

write_seed_input_from_manifest() {
	set -a
	. "$AUTH_ENV_FILE"
	set +a
	LOCALNET_SCENARIO_MANIFEST=${LOCALNET_SCENARIO_MANIFEST:-"$repo_root/infra/quickstart/scenarios/confidential-margin-scenario.json"}
	test -f "$LOCALNET_SCENARIO_MANIFEST" || {
		echo "$1: missing scenario manifest $LOCALNET_SCENARIO_MANIFEST" >&2
		exit 1
	}

	SCENARIO_PATH="$LOCALNET_SCENARIO_MANIFEST" SEED_INPUT_PATH="$SEED_INPUT_FILE" python3 - <<'PY'
import json
import os

with open(os.environ["SCENARIO_PATH"], "r", encoding="utf-8") as f:
    scenario = json.load(f)

seed_input = {
    "scenarioId": scenario["scenarioId"],
    "obligationId": scenario["obligationId"],
    "postingId": scenario["postingId"],
    "obligationCorrelationId": scenario["obligationCorrelationId"],
    "postingCorrelationId": scenario["postingCorrelationId"],
    "policyVersion": scenario["policyVersion"],
    "snapshotId": scenario["snapshotId"],
    "decisionReference": scenario["decisionReference"],
    "requiredCoverage": scenario["requiredCoverage"],
    "uncoveredAmount": scenario["uncoveredAmount"],
    "dueAt": scenario["dueAt"],
    "providerParty": os.environ["APP_USER_PARTY"],
    "providerUserId": os.environ["APP_USER_VALIDATOR_USER_ID"],
    "securedParty": os.environ["APP_PROVIDER_PARTY"],
    "securedPartyUserId": os.environ["APP_PROVIDER_VALIDATOR_USER_ID"],
    "operatorPartyHint": scenario["operator"]["partyHint"],
    "operatorDisplayName": scenario["operator"]["displayName"],
    "operatorUserId": scenario["operator"]["userId"],
    "custodianPartyHint": scenario["custodian"]["partyHint"],
    "custodianDisplayName": scenario["custodian"]["displayName"],
    "custodianUserId": scenario["custodian"]["userId"],
    "selectedLots": scenario["selectedLots"],
}

with open(os.environ["SEED_INPUT_PATH"], "w", encoding="ascii") as f:
    json.dump(seed_input, f, indent=2)
    f.write("\n")
PY
}

write_status_input_from_seed_receipt() {
	STATUS_RECEIPT_PATH="$LOCALNET_SEED_RECEIPT" STATUS_INPUT_PATH="$STATUS_INPUT_FILE" python3 - <<'PY'
import json
import os

with open(os.environ["STATUS_RECEIPT_PATH"], "r", encoding="utf-8") as f:
    receipt = json.load(f)

status_input = {
    "scenarioId": receipt["scenarioId"],
    "providerParty": receipt["providerParty"],
    "obligationId": receipt["obligationId"],
    "postingId": receipt["postingId"],
    "inventoryLotIds": [lot["lotId"] for lot in receipt["inventoryLots"]],
}

with open(os.environ["STATUS_INPUT_PATH"], "w", encoding="ascii") as f:
    json.dump(status_input, f, indent=2)
    f.write("\n")
PY
}
