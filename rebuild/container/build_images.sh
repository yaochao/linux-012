#!/bin/sh
set -eu

ROOT=/workspace
CONTAINER_WORK_ROOT=/tmp/linux-012-rebuild-work
SOURCE_ROOT="$CONTAINER_WORK_ROOT/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
ROOTFS_DIR="$ROOT/rebuild/rootfs"
MANIFEST_DIR="$ROOT/rebuild/rootfs/manifest"
DIRECTORIES_FILE="$ROOT/rebuild/rootfs/manifest/directories.txt"
DEVICES_FILE="$ROOT/rebuild/rootfs/manifest/devices.tsv"
USERLAND_ROOT="$ROOT/rebuild/userland"
AOUT_PACKER="$ROOT/rebuild/tools/aout_pack.py"
IMAGE_DIR="$ROOT/rebuild/out/images"
LOG_DIR="$ROOT/rebuild/out/logs"
WORK_DIR="$ROOT/rebuild/out/work"
BUILD_LOG="$LOG_DIR/build.log"
DISK_IMAGE="$IMAGE_DIR/hdc-0.12.img"
ROOTFS_TAR="$CONTAINER_WORK_ROOT/rootfs.tar"
STAGING_DIR="$CONTAINER_WORK_ROOT/rootfs"
USERLAND_BUILD="$CONTAINER_WORK_ROOT/userland"
ROOT_PARTITION_IMAGE="$CONTAINER_WORK_ROOT/rootfs.img"
export LIBGUESTFS_BACKEND=direct

cleanup() {
    rm -rf "$CONTAINER_WORK_ROOT"
}

trap cleanup EXIT

rm -rf "$CONTAINER_WORK_ROOT"
rm -rf "$WORK_DIR"
mkdir -p "$CONTAINER_WORK_ROOT" "$IMAGE_DIR" "$LOG_DIR" "$WORK_DIR" "$STAGING_DIR" "$USERLAND_BUILD"
: >"$BUILD_LOG"

tar -xzf "$ROOT/vendor/src/linux-0.12.tar.gz" -C "$CONTAINER_WORK_ROOT"

for patch in "$PATCH_DIR"/*.patch; do
    [ -s "$patch" ] || continue
    patch --batch -p1 -d "$CONTAINER_WORK_ROOT" < "$patch" >>"$BUILD_LOG" 2>&1
done

chmod +x "$SOURCE_ROOT/tools/build.sh"
make -C "$SOURCE_ROOT" Image >>"$BUILD_LOG" 2>&1
cp "$SOURCE_ROOT/Image" "$IMAGE_DIR/bootimage-0.12-hd"

while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    mkdir -p "$STAGING_DIR/$dir"
done < "$DIRECTORIES_FILE"

gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/lib.c" -o "$USERLAND_BUILD/lib.o" >>"$BUILD_LOG" 2>&1
gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/sh.c" -o "$USERLAND_BUILD/sh.o" >>"$BUILD_LOG" 2>&1
gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/ls.c" -o "$USERLAND_BUILD/ls.o" >>"$BUILD_LOG" 2>&1
gcc -m32 -fno-pie -fno-pic -c "$USERLAND_ROOT/src/crt0.S" -o "$USERLAND_BUILD/crt0.o" >>"$BUILD_LOG" 2>&1

ld -m elf_i386 -T "$USERLAND_ROOT/linker.ld" -o "$USERLAND_BUILD/sh.elf" \
    "$USERLAND_BUILD/crt0.o" "$USERLAND_BUILD/lib.o" "$USERLAND_BUILD/sh.o" >>"$BUILD_LOG" 2>&1
ld -m elf_i386 -T "$USERLAND_ROOT/linker.ld" -o "$USERLAND_BUILD/ls.elf" \
    "$USERLAND_BUILD/crt0.o" "$USERLAND_BUILD/lib.o" "$USERLAND_BUILD/ls.o" >>"$BUILD_LOG" 2>&1

python3 "$AOUT_PACKER" "$USERLAND_BUILD/sh.elf" "$STAGING_DIR/bin/sh" >>"$BUILD_LOG" 2>&1
python3 "$AOUT_PACKER" "$USERLAND_BUILD/ls.elf" "$STAGING_DIR/bin/ls" >>"$BUILD_LOG" 2>&1
chmod 755 "$STAGING_DIR/bin/sh" "$STAGING_DIR/bin/ls"

truncate -s 62447616 "$DISK_IMAGE"
sfdisk "$DISK_IMAGE" < "$ROOTFS_DIR/layout.sfdisk" >>"$BUILD_LOG" 2>&1
ROOT_PARTITION_SECTORS=$(awk -F'[=, ]+' '/size=/{for (i = 1; i <= NF; i++) if ($i == "size") {print $(i + 1); exit}}' "$ROOTFS_DIR/layout.sfdisk")
[ -n "$ROOT_PARTITION_SECTORS" ]
truncate -s "$((ROOT_PARTITION_SECTORS * 512))" "$ROOT_PARTITION_IMAGE"
mkfs.minix -1 -n14 "$ROOT_PARTITION_IMAGE" >>"$BUILD_LOG" 2>&1
cp "$MANIFEST_DIR/etc/rc" "$STAGING_DIR/etc/rc"
cp "$MANIFEST_DIR/usr/root/README" "$STAGING_DIR/usr/root/README"

while IFS=' ' read -r kind mode major minor relative_path; do
    [ -n "$kind" ] || continue
    mknod "$STAGING_DIR/$relative_path" "$kind" "$major" "$minor"
    chmod "$mode" "$STAGING_DIR/$relative_path"
done < "$DEVICES_FILE"

tar -C "$STAGING_DIR" -cpf "$ROOTFS_TAR" . >>"$BUILD_LOG" 2>&1

guestfish --format=raw -a "$ROOT_PARTITION_IMAGE" >>"$BUILD_LOG" 2>&1 <<EOF
run
mount /dev/sda /
tar-in "$ROOTFS_TAR" /
umount /
EOF

dd if="$ROOT_PARTITION_IMAGE" of="$DISK_IMAGE" bs=512 seek=1 conv=notrunc >>"$BUILD_LOG" 2>&1
