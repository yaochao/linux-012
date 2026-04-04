#!/bin/sh
set -eu

if ! command -v qemu-system-i386 >/dev/null 2>&1; then
  echo "qemu-system-i386 not found. Install it with: brew install qemu" >&2
  exit 1
fi

qemu-system-i386 --version
