#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$repo_root/infra/quickstart/overlay/upstream-pin.env"

need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "localnet-smoke: missing required command '$1'" >&2
		exit 1
	}
}

LOCALNET_WORKDIR=${LOCALNET_WORKDIR:-"$repo_root/.runtime/localnet/cn-quickstart"}
quickstart_dir="$LOCALNET_WORKDIR/$QS_QUICKSTART_SUBDIR"

test -d "$LOCALNET_WORKDIR/.git" || {
	echo "localnet-smoke: missing Quickstart checkout; run make localnet-bootstrap first" >&2
	exit 1
}

test -f "$quickstart_dir/.env.local" || {
	echo "localnet-smoke: missing $quickstart_dir/.env.local; run make localnet-bootstrap first" >&2
	exit 1
}

need_cmd git
need_cmd docker
need_cmd make
need_cmd curl

current_commit=$(git -C "$LOCALNET_WORKDIR" rev-parse HEAD)
test "$current_commit" = "$QS_COMMIT" || {
	echo "localnet-smoke: expected pinned commit $QS_COMMIT but found $current_commit" >&2
	exit 1
}

for key in OBSERVABILITY_ENABLED AUTH_MODE PARTY_HINT TEST_MODE; do
	grep -q "^$key=" "$quickstart_dir/.env.local" || {
		echo "localnet-smoke: missing $key in $quickstart_dir/.env.local" >&2
		exit 1
	}
done

cd "$quickstart_dir"
make --no-print-directory check-docker >/dev/null
make --no-print-directory compose-config >/dev/null

set -a
. ./.env
. ./.env.local
set +a

running_containers=$(docker ps --quiet --filter "network=${DOCKER_NETWORK:-quickstart}")

if [ -n "$running_containers" ]; then
	make --no-print-directory status >/dev/null
	for readyz_url in \
		"http://localhost:2${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz" \
		"http://localhost:3${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz" \
		"http://localhost:4${VALIDATOR_ADMIN_API_PORT_SUFFIX}/api/validator/readyz"
	do
		curl -fsS "$readyz_url" >/dev/null
	done
	echo "localnet-smoke: compose configuration validated and running validator readyz checks passed"
else
	echo "localnet-smoke: compose configuration validated for pinned commit $QS_COMMIT"
	echo "localnet-smoke: runtime readyz probes skipped because the Quickstart stack is not running"
fi
