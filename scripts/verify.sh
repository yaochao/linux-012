#!/bin/sh
set -eu

cd "${0%/*}/.."
exec /usr/bin/python3 rebuild/driver.py verify "$@"
