#!/bin/sh
set -eu

ROOT=/workspace
CONTAINER_WORK_ROOT=/tmp/linux-012-rebuild-work
SOURCE_ROOT="$CONTAINER_WORK_ROOT/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
ROOTFS_DIR="$ROOT/rebuild/rootfs"
IMAGE_DIR="$ROOT/rebuild/out/images"
LOG_DIR="$ROOT/rebuild/out/logs"
BUILD_LOG="$LOG_DIR/build.log"
DISK_IMAGE="$IMAGE_DIR/hdc-0.12.img"
OVERLAY_TAR="$CONTAINER_WORK_ROOT/overlay.tar"
ROOT_PARTITION_IMAGE="$CONTAINER_WORK_ROOT/rootfs.img"
export LIBGUESTFS_BACKEND=direct

cleanup() {
    rm -rf "$CONTAINER_WORK_ROOT"
}

trap cleanup EXIT

rm -rf "$CONTAINER_WORK_ROOT"
mkdir -p "$CONTAINER_WORK_ROOT" "$IMAGE_DIR" "$LOG_DIR"
: >"$BUILD_LOG"

tar -xzf "$ROOT/vendor/src/linux-0.12.tar.gz" -C "$CONTAINER_WORK_ROOT"

for patch in "$PATCH_DIR"/*.patch; do
    [ -s "$patch" ] || continue
    patch --batch -p1 -d "$CONTAINER_WORK_ROOT" < "$patch" >>"$BUILD_LOG" 2>&1
done

chmod +x "$SOURCE_ROOT/tools/build.sh"
make -C "$SOURCE_ROOT" Image >>"$BUILD_LOG" 2>&1
cp "$SOURCE_ROOT/Image" "$IMAGE_DIR/bootimage-0.12-hd"

truncate -s 62447616 "$DISK_IMAGE"
sfdisk "$DISK_IMAGE" < "$ROOTFS_DIR/layout.sfdisk" >>"$BUILD_LOG" 2>&1
ROOT_PARTITION_SECTORS=$(awk -F'[=, ]+' '/size=/{for (i = 1; i <= NF; i++) if ($i == "size") {print $(i + 1); exit}}' "$ROOTFS_DIR/layout.sfdisk")
[ -n "$ROOT_PARTITION_SECTORS" ]
truncate -s "$((ROOT_PARTITION_SECTORS * 512))" "$ROOT_PARTITION_IMAGE"
mkfs.minix -1 -n14 "$ROOT_PARTITION_IMAGE" >>"$BUILD_LOG" 2>&1
tar -C "$ROOTFS_DIR/overlay" --exclude=.gitkeep -cpf "$OVERLAY_TAR" . >>"$BUILD_LOG" 2>&1

guestfish --format=raw -a "$ROOT_PARTITION_IMAGE" >>"$BUILD_LOG" 2>&1 <<EOF
run
mount /dev/sda /
tar-in "$ROOTFS_DIR/base.tar" /
tar-in "$OVERLAY_TAR" /
umount /
EOF

dd if="$ROOT_PARTITION_IMAGE" of="$DISK_IMAGE" bs=512 seek=1 conv=notrunc >>"$BUILD_LOG" 2>&1
