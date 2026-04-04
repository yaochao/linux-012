#!/bin/sh
set -eu

ROOT=/workspace
WORK_ROOT="$ROOT/rebuild/out/work"
SOURCE_ROOT="$WORK_ROOT/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
ROOTFS_DIR="$ROOT/rebuild/rootfs"
IMAGE_DIR="$ROOT/rebuild/out/images"
LOG_DIR="$ROOT/rebuild/out/logs"
BUILD_LOG="$LOG_DIR/build.log"
DISK_IMAGE="$IMAGE_DIR/hdc-0.12.img"
OVERLAY_TAR="$WORK_ROOT/overlay.tar"
export LIBGUESTFS_BACKEND=direct

rm -rf "$WORK_ROOT"
mkdir -p "$WORK_ROOT" "$IMAGE_DIR" "$LOG_DIR"
: >"$BUILD_LOG"

tar -xzf "$ROOT/vendor/src/linux-0.12.tar.gz" -C "$WORK_ROOT"

for patch in "$PATCH_DIR"/*.patch; do
    [ -s "$patch" ] || continue
    patch -p2 -d "$WORK_ROOT" < "$patch" >>"$BUILD_LOG" 2>&1
done

make -C "$SOURCE_ROOT" Image >>"$BUILD_LOG" 2>&1
cp "$SOURCE_ROOT/Image" "$IMAGE_DIR/bootimage-0.12-hd"

truncate -s 62447616 "$DISK_IMAGE"
sfdisk "$DISK_IMAGE" < "$ROOTFS_DIR/layout.sfdisk" >>"$BUILD_LOG" 2>&1
tar -C "$ROOTFS_DIR/overlay" -cpf "$OVERLAY_TAR" . >>"$BUILD_LOG" 2>&1

guestfish --format=raw -a "$DISK_IMAGE" >>"$BUILD_LOG" 2>&1 <<EOF
run
mkfs minix /dev/sda1
mount /dev/sda1 /
tar-in "$ROOTFS_DIR/base.tar" /
tar-in "$OVERLAY_TAR" /
umount /
EOF
