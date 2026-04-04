#!/bin/sh
set -eu

ROOT=/workspace
ROOTFS_DIR="$ROOT/rebuild/rootfs"
LOG_DIR="$ROOT/rebuild/out/logs"
SOURCE_IMAGE="$ROOT/vendor/images/hdc-0.12.img"
LOG_FILE="$LOG_DIR/capture-rootfs.log"
export LIBGUESTFS_BACKEND=direct

mkdir -p "$ROOTFS_DIR" "$LOG_DIR"
: >"$LOG_FILE"
rm -f "$ROOTFS_DIR/base.tar"

guestfish --ro --format=raw -a "$SOURCE_IMAGE" >>"$LOG_FILE" 2>&1 <<EOF
run
mount-ro /dev/sda1 /
tar-out / "$ROOTFS_DIR/base.tar"
EOF
