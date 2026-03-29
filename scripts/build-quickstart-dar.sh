#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

. "$script_dir/toolchain.env"
. "$repo_root/infra/quickstart/overlay/upstream-pin.env"

need_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "localnet-build-dar: missing required command '$1'" >&2
		exit 1
	}
}

need_cmd docker

output_dir=${LOCALNET_DAR_OUTPUT_DIR:-"$repo_root/.daml/dist-quickstart"}
metadata_file="$output_dir/quickstart-dar-metadata.env"
container_output_dir="/workspace${output_dir#"$repo_root"}"
container_metadata_file="$container_output_dir/quickstart-dar-metadata.env"

mkdir -p "$output_dir"
rm -f "$output_dir"/*.dar "$metadata_file"

docker run --rm -i \
	-v "$repo_root:/workspace" \
	-w /workspace \
	-e OUTPUT_DIR="$container_output_dir" \
	-e METADATA_FILE="$container_metadata_file" \
	-e LEGACY_DAML_SDK_VERSION="$DAML_SDK_VERSION" \
	-e QUICKSTART_BUILD_CONTAINER_IMAGE="$QUICKSTART_BUILD_CONTAINER_IMAGE" \
	-e QUICKSTART_DAML_SDK_VERSION="$QUICKSTART_DAML_SDK_VERSION" \
	-e QUICKSTART_JAVA_VERSION="$QUICKSTART_JAVA_VERSION" \
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
		echo "localnet-build-dar: unsupported container architecture $container_arch" >&2
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

mkdir -p "$DAML_HOME/sdk"
ln -s "$sdk_dir" "$DAML_HOME/sdk/$QUICKSTART_DAML_SDK_VERSION"
cat > "$DAML_HOME/daml-config.yaml" <<CFG
update-check: never
auto-install: false
CFG

probe_dir=$(mktemp -d)
trap 'rm -rf "$probe_dir"' EXIT HUP INT TERM

cp /workspace/daml.yaml "$probe_dir/daml.yaml"
cp -R /workspace/daml "$probe_dir/daml"
sed -i "s/^sdk-version: .*/sdk-version: $QUICKSTART_DAML_SDK_VERSION/" "$probe_dir/daml.yaml"

cd "$probe_dir"
daml build --package-root "$probe_dir" >/dev/null

dar_file=$(find "$probe_dir/.daml/dist" -maxdepth 1 -name '*.dar' | head -n 1)
test -n "$dar_file" || {
	echo "localnet-build-dar: no DAR produced by the Quickstart bridge build" >&2
	exit 1
}

cp "$dar_file" "$OUTPUT_DIR/"
output_dar="$OUTPUT_DIR/$(basename "$dar_file")"

inspect_output=$(daml damlc inspect-dar "$output_dar")
package_id=$(printf '%s\n' "$inspect_output" | awk '
	/^DAR archive contains the following packages:$/ {capture = 1; next}
	capture && $1 ~ /^canton-collateral-control-plane-/ {
		gsub(/"/, "", $2)
		print $2
		exit
	}
')
test -n "$package_id" || {
	echo "localnet-build-dar: unable to determine the Control Plane package id from $output_dar" >&2
	exit 1
}

cat > "$METADATA_FILE" <<CFG
DAR_FILE=$output_dar
PACKAGE_ID=$package_id
DAML_SDK_VERSION=$QUICKSTART_DAML_SDK_VERSION
JAVA_VERSION=$QUICKSTART_JAVA_VERSION
BUILD_CONTAINER_IMAGE=$QUICKSTART_BUILD_CONTAINER_IMAGE
CFG
EOF

test -f "$metadata_file" || {
	echo "localnet-build-dar: missing build metadata file $metadata_file" >&2
	exit 1
}

. "$metadata_file"

DAR_FILE="$output_dir/$(basename "$DAR_FILE")"

cat > "$metadata_file" <<CFG
DAR_FILE=$DAR_FILE
PACKAGE_ID=$PACKAGE_ID
DAML_SDK_VERSION=$DAML_SDK_VERSION
JAVA_VERSION=$JAVA_VERSION
BUILD_CONTAINER_IMAGE=$BUILD_CONTAINER_IMAGE
CFG

echo "localnet-build-dar: built $DAR_FILE"
echo "localnet-build-dar: main package id $PACKAGE_ID"
echo "localnet-build-dar: runtime line Daml SDK $DAML_SDK_VERSION via $BUILD_CONTAINER_IMAGE"
