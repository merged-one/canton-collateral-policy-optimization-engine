#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$script_dir/toolchain.env"
. "$repo_root/infra/quickstart/overlay/upstream-pin.env"

need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "localnet-deploy-dar: missing required command '$1'" >&2
		exit 1
	}
}

need_cmd docker
need_cmd git

LOCALNET_WORKDIR=${LOCALNET_WORKDIR:-"$repo_root/.runtime/localnet/cn-quickstart"}
quickstart_dir="$LOCALNET_WORKDIR/$QS_QUICKSTART_SUBDIR"
metadata_file="${LOCALNET_DAR_OUTPUT_DIR:-"$repo_root/.daml/dist-quickstart"}/quickstart-dar-metadata.env"
onboarding_container=${LOCALNET_ONBOARDING_CONTAINER:-splice-onboarding}

test -d "$LOCALNET_WORKDIR/.git" || {
	echo "localnet-deploy-dar: missing Quickstart checkout; run make localnet-bootstrap first" >&2
	exit 1
}

current_commit=$(git -C "$LOCALNET_WORKDIR" rev-parse HEAD)
test "$current_commit" = "$QS_COMMIT" || {
	echo "localnet-deploy-dar: expected pinned commit $QS_COMMIT but found $current_commit" >&2
	exit 1
}

test -f "$quickstart_dir/.env.local" || {
	echo "localnet-deploy-dar: missing $quickstart_dir/.env.local; run make localnet-bootstrap first" >&2
	exit 1
}

LOCALNET_WORKDIR="$LOCALNET_WORKDIR" "$script_dir/run-localnet-smoke.sh"
"$script_dir/build-quickstart-dar.sh"

test -f "$metadata_file" || {
	echo "localnet-deploy-dar: missing build metadata; expected $metadata_file" >&2
	exit 1
}

. "$metadata_file"
dar_basename=$(basename "$DAR_FILE")

set -a
. "$quickstart_dir/.env"
. "$quickstart_dir/.env.local"
. "$quickstart_dir/docker/modules/localnet/compose.env"
. "$quickstart_dir/docker/modules/localnet/env/common.env"
set +a

running_containers=$(docker ps --quiet --filter "network=${DOCKER_NETWORK:-quickstart}")
test -n "$running_containers" || {
	echo "localnet-deploy-dar: built $DAR_FILE but the Quickstart stack is not running" >&2
	echo "localnet-deploy-dar: from $quickstart_dir run make build && make start, then retry" >&2
	exit 1
}

docker inspect "$onboarding_container" >/dev/null 2>&1 || {
	echo "localnet-deploy-dar: missing onboarding container '$onboarding_container' in the running Quickstart stack" >&2
	exit 1
}

docker exec "$onboarding_container" mkdir -p /canton/dars
docker cp "$DAR_FILE" "$onboarding_container:/canton/dars/$dar_basename"

docker exec \
	-e CONTROL_PLANE_DAR_BASENAME="$dar_basename" \
	-e CONTROL_PLANE_PACKAGE_ID="$PACKAGE_ID" \
	"$onboarding_container" \
	bash -lc '
set -euo pipefail
export DO_INIT=false
source /app/utils.sh

deploy_to_participant() {
	local participant_label=$1
	local participant_host=$2
	local token=$3
	local packages

	packages=$(curl_check "http://$participant_host/v2/packages" "$token" "application/json")
	if printf "%s\n" "$packages" | grep -q "$CONTROL_PLANE_PACKAGE_ID"; then
		echo "localnet-deploy-dar: package $CONTROL_PLANE_PACKAGE_ID already present on the $participant_label participant"
		return
	fi

	curl_check "http://$participant_host/v2/packages" "$token" "application/octet-stream" \
		--data-binary "@/canton/dars/$CONTROL_PLANE_DAR_BASENAME" >/dev/null

	packages=$(curl_check "http://$participant_host/v2/packages" "$token" "application/json")
	printf "%s\n" "$packages" | grep -q "$CONTROL_PLANE_PACKAGE_ID" || {
		echo "localnet-deploy-dar: package $CONTROL_PLANE_PACKAGE_ID missing on the $participant_label participant after upload" >&2
		exit 1
	}

	echo "localnet-deploy-dar: uploaded $CONTROL_PLANE_DAR_BASENAME to the $participant_label participant"
}

if [ "${APP_PROVIDER_PROFILE:-off}" = "on" ]; then
	source /app/app-provider-auth.sh
	deploy_to_participant "app-provider" "canton:3${PARTICIPANT_JSON_API_PORT_SUFFIX}" "$APP_PROVIDER_PARTICIPANT_ADMIN_TOKEN"
fi

if [ "${APP_USER_PROFILE:-off}" = "on" ]; then
	source /app/app-user-auth.sh
	deploy_to_participant "app-user" "canton:2${PARTICIPANT_JSON_API_PORT_SUFFIX}" "$APP_USER_PARTICIPANT_ADMIN_TOKEN"
fi
'

echo "localnet-deploy-dar: Control Plane DAR $dar_basename is present on the targeted Quickstart participants"
echo "localnet-deploy-dar: main package id $PACKAGE_ID"
