#!/bin/sh
set -eu

ROOT=/workspace
WORK_ROOT="$ROOT/rebuild/out/work"
SOURCE_ROOT="$WORK_ROOT/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
IMAGE_DIR="$ROOT/rebuild/out/images"
LOG_DIR="$ROOT/rebuild/out/logs"
BUILD_LOG="$LOG_DIR/build.log"

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
