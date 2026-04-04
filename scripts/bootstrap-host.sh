#!/bin/sh
set -eu

cd "${0%/*}/.."
exec /usr/bin/python3 tools/qemu_driver.py bootstrap-host "$@"
