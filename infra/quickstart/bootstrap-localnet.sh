#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/../.." && pwd)
overlay_dir="$script_dir/overlay"

. "$overlay_dir/upstream-pin.env"

usage() {
	cat <<'EOF'
Usage: bootstrap-localnet.sh [--profile lean|faithful] [--workdir PATH] [--party-hint ORG-ROLE-N]

Bootstraps a pinned upstream CN Quickstart checkout under the requested workdir
and writes quickstart/.env.local from the selected overlay profile.
EOF
}

need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "localnet-bootstrap: missing required command '$1'" >&2
		exit 1
	}
}

validate_party_hint() {
	echo "$1" | grep -Eq '^[A-Za-z]+-[A-Za-z]+-[0-9]+$' || {
		echo "localnet-bootstrap: party hint must match ORG-ROLE-N using letters and digits only" >&2
		exit 1
	}
}

LOCALNET_PROFILE=${LOCALNET_PROFILE:-lean}
LOCALNET_WORKDIR=${LOCALNET_WORKDIR:-"$repo_root/.runtime/localnet/cn-quickstart"}
LOCALNET_PARTY_HINT=${LOCALNET_PARTY_HINT:-canton-collateral-1}

while [ "$#" -gt 0 ]; do
	case "$1" in
		--profile)
			shift
			LOCALNET_PROFILE=${1:-}
			;;
		--workdir)
			shift
			LOCALNET_WORKDIR=${1:-}
			;;
		--party-hint)
			shift
			LOCALNET_PARTY_HINT=${1:-}
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "localnet-bootstrap: unknown argument '$1'" >&2
			usage >&2
			exit 1
			;;
	esac
	shift
done

profile_template="$overlay_dir/profiles/$LOCALNET_PROFILE.env.local"
test -f "$profile_template" || {
	echo "localnet-bootstrap: unknown profile '$LOCALNET_PROFILE'" >&2
	exit 1
}

validate_party_hint "$LOCALNET_PARTY_HINT"

need_cmd git
need_cmd sed

workspace_parent=$(dirname "$LOCALNET_WORKDIR")
mkdir -p "$workspace_parent"

if [ -e "$LOCALNET_WORKDIR" ] && [ ! -d "$LOCALNET_WORKDIR/.git" ]; then
	echo "localnet-bootstrap: existing workdir is not a git checkout: $LOCALNET_WORKDIR" >&2
	exit 1
fi

if [ ! -d "$LOCALNET_WORKDIR/.git" ]; then
	mkdir -p "$LOCALNET_WORKDIR"
	git -C "$LOCALNET_WORKDIR" init >/dev/null
	git -C "$LOCALNET_WORKDIR" remote add origin "$QS_REPO_URL"
fi

remote_url=$(git -C "$LOCALNET_WORKDIR" remote get-url origin 2>/dev/null || true)
test "$remote_url" = "$QS_REPO_URL" || {
	echo "localnet-bootstrap: unexpected origin '$remote_url' in $LOCALNET_WORKDIR" >&2
	exit 1
}

git -C "$LOCALNET_WORKDIR" fetch --depth 1 origin "$QS_COMMIT" >/dev/null
git -C "$LOCALNET_WORKDIR" checkout --detach "$QS_COMMIT" >/dev/null 2>&1

quickstart_dir="$LOCALNET_WORKDIR/$QS_QUICKSTART_SUBDIR"
test -f "$quickstart_dir/Makefile" || {
	echo "localnet-bootstrap: expected Quickstart Makefile under $quickstart_dir" >&2
	exit 1
}
test -f "$quickstart_dir/.env" || {
	echo "localnet-bootstrap: expected Quickstart .env under $quickstart_dir" >&2
	exit 1
}
test -f "$quickstart_dir/compose.yaml" || {
	echo "localnet-bootstrap: expected Quickstart compose.yaml under $quickstart_dir" >&2
	exit 1
}

sed "s/__PARTY_HINT__/$LOCALNET_PARTY_HINT/g" "$profile_template" > "$quickstart_dir/.env.local"

current_commit=$(git -C "$LOCALNET_WORKDIR" rev-parse HEAD)
test "$current_commit" = "$QS_COMMIT" || {
	echo "localnet-bootstrap: expected commit $QS_COMMIT but found $current_commit" >&2
	exit 1
}

echo "localnet-bootstrap: staged CN Quickstart commit $QS_COMMIT in $LOCALNET_WORKDIR"
echo "localnet-bootstrap: wrote $quickstart_dir/.env.local from profile '$LOCALNET_PROFILE' with PARTY_HINT=$LOCALNET_PARTY_HINT"
echo "localnet-bootstrap: next upstream commands:"
echo "  cd $quickstart_dir"
echo "  make check-docker"
echo "  make build"
echo "  make start"
echo "  make status"
