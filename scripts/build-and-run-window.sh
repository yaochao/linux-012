#!/bin/sh
set -eu

cd "${0%/*}/.."
exec /usr/bin/python3 rebuild/driver.py build-and-run-repo-images-window "$@"
