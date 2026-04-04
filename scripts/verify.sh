#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
exec python3 tools/qemu_driver.py verify "$@"
