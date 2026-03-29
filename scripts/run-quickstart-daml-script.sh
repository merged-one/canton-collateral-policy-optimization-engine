#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$script_dir/toolchain.env"

usage() {
	cat <<'EOF'
Usage: run-quickstart-daml-script.sh --script-name MODULE:ENTITY --participant-config PATH --output-file PATH [--input-file PATH]

Runs a Daml Script against the pinned Quickstart runtime line using the repo-built
Quickstart-compatible Control Plane DAR.
EOF
}

need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "run-quickstart-daml-script: missing required command '$1'" >&2
		exit 1
	}
}

need_cmd docker

SCRIPT_NAME=
PARTICIPANT_CONFIG=
OUTPUT_FILE=
INPUT_FILE=

while [ "$#" -gt 0 ]; do
	case "$1" in
		--script-name)
			shift
			SCRIPT_NAME=${1:-}
			;;
		--participant-config)
			shift
			PARTICIPANT_CONFIG=${1:-}
			;;
		--output-file)
			shift
			OUTPUT_FILE=${1:-}
			;;
		--input-file)
			shift
			INPUT_FILE=${1:-}
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "run-quickstart-daml-script: unknown argument '$1'" >&2
			usage >&2
			exit 1
			;;
	esac
	shift
done

test -n "$SCRIPT_NAME" || {
	echo "run-quickstart-daml-script: --script-name is required" >&2
	exit 1
}

test -n "$PARTICIPANT_CONFIG" || {
	echo "run-quickstart-daml-script: --participant-config is required" >&2
	exit 1
}

test -n "$OUTPUT_FILE" || {
	echo "run-quickstart-daml-script: --output-file is required" >&2
	exit 1
}

test -f "$PARTICIPANT_CONFIG" || {
	echo "run-quickstart-daml-script: missing participant config $PARTICIPANT_CONFIG" >&2
	exit 1
}

if [ -n "$INPUT_FILE" ] && [ ! -f "$INPUT_FILE" ]; then
	echo "run-quickstart-daml-script: missing input file $INPUT_FILE" >&2
	exit 1
fi

"$script_dir/build-quickstart-dar.sh" >/dev/null

metadata_file="${LOCALNET_DAR_OUTPUT_DIR:-"$repo_root/.daml/dist-quickstart"}/quickstart-dar-metadata.env"
test -f "$metadata_file" || {
	echo "run-quickstart-daml-script: missing DAR metadata $metadata_file" >&2
	exit 1
}

. "$metadata_file"

test -f "$DAR_FILE" || {
	echo "run-quickstart-daml-script: missing Quickstart DAR $DAR_FILE" >&2
	exit 1
}

mkdir -p "$(dirname "$OUTPUT_FILE")"

container_dar="/workspace${DAR_FILE#"$repo_root"}"
container_participant_config="/workspace${PARTICIPANT_CONFIG#"$repo_root"}"
container_output_file="/workspace${OUTPUT_FILE#"$repo_root"}"

if [ -n "$INPUT_FILE" ]; then
	container_input_file="/workspace${INPUT_FILE#"$repo_root"}"
else
	container_input_file=
fi

docker run --rm -i \
	--add-host host.docker.internal:host-gateway \
	-v "$repo_root:/workspace" \
	-w /workspace \
	-e SCRIPT_NAME="$SCRIPT_NAME" \
	-e DAR_FILE="$container_dar" \
	-e PARTICIPANT_CONFIG="$container_participant_config" \
	-e OUTPUT_FILE="$container_output_file" \
	-e INPUT_FILE="$container_input_file" \
	-e QUICKSTART_DAML_SDK_VERSION="$QUICKSTART_DAML_SDK_VERSION" \
	-e QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE="$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE" \
	-e QUICKSTART_DAML_SDK_LINUX_AARCH64_URL="$QUICKSTART_DAML_SDK_LINUX_AARCH64_URL" \
	-e QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256="$QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256" \
	-e QUICKSTART_DAML_SDK_LINUX_X64_ARCHIVE="$QUICKSTART_DAML_SDK_LINUX_X64_ARCHIVE" \
	-e QUICKSTART_DAML_SDK_LINUX_X64_URL="$QUICKSTART_DAML_SDK_LINUX_X64_URL" \
	-e QUICKSTART_DAML_SDK_LINUX_X64_SHA256="$QUICKSTART_DAML_SDK_LINUX_X64_SHA256" \
	"$QUICKSTART_BUILD_CONTAINER_IMAGE" \
	/bin/sh <<'EOF'
set -eu

export DEBIAN_FRONTEND=noninteractive
apt-get update >/dev/null
apt-get install -y ca-certificates curl gzip openjdk-21-jdk-headless tar >/dev/null

container_arch=$(dpkg --print-architecture)
case "$container_arch" in
	arm64)
		daml_archive=$QUICKSTART_DAML_SDK_LINUX_AARCH64_ARCHIVE
		daml_url=$QUICKSTART_DAML_SDK_LINUX_AARCH64_URL
		daml_sha=$QUICKSTART_DAML_SDK_LINUX_AARCH64_SHA256
		;;
	amd64)
		daml_archive=$QUICKSTART_DAML_SDK_LINUX_X64_ARCHIVE
		daml_url=$QUICKSTART_DAML_SDK_LINUX_X64_URL
		daml_sha=$QUICKSTART_DAML_SDK_LINUX_X64_SHA256
		;;
	*)
		echo "run-quickstart-daml-script: unsupported container architecture $container_arch" >&2
		exit 1
		;;
esac

curl -fsSL "$daml_url" -o "/tmp/$daml_archive"
echo "$daml_sha  /tmp/$daml_archive" | sha256sum -c - >/dev/null
tar -xzf "/tmp/$daml_archive" -C /tmp

sdk_dir="/tmp/sdk-$QUICKSTART_DAML_SDK_VERSION"
export PATH="$sdk_dir/daml:$sdk_dir/daml-helper:$PATH"
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-$container_arch"
export DAML_HOME=/tmp/daml-home
export DAML_SDK_VERSION="$QUICKSTART_DAML_SDK_VERSION"

mkdir -p "$DAML_HOME/sdk"
ln -s "$sdk_dir" "$DAML_HOME/sdk/$QUICKSTART_DAML_SDK_VERSION"
cat > "$DAML_HOME/daml-config.yaml" <<CFG
update-check: never
auto-install: false
CFG

if [ -n "$INPUT_FILE" ]; then
	daml script \
		--dar "$DAR_FILE" \
		--script-name "$SCRIPT_NAME" \
		--participant-config "$PARTICIPANT_CONFIG" \
		--input-file "$INPUT_FILE" \
		--output-file "$OUTPUT_FILE"
else
	daml script \
		--dar "$DAR_FILE" \
		--script-name "$SCRIPT_NAME" \
		--participant-config "$PARTICIPANT_CONFIG" \
		--output-file "$OUTPUT_FILE"
fi
EOF

test -f "$OUTPUT_FILE" || {
	echo "run-quickstart-daml-script: expected output file $OUTPUT_FILE" >&2
	exit 1
}

echo "run-quickstart-daml-script: wrote $OUTPUT_FILE"
