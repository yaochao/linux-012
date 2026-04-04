.DEFAULT_GOAL := help

.PHONY: help bootstrap-host build run run-window verify verify-userland check-images fetch-release-images repro-check release-readback

help:
	@printf '%s\n' \
		'Available targets:' \
		'  bootstrap-host      Check Python, QEMU, and Docker on the current host' \
		'  build               Build Linux 0.12 runtime images from source' \
		'  run                 Boot QEMU from the committed repo snapshots' \
		'  run-window          Boot QEMU from the committed repo snapshots in a visible window' \
		'  verify              Boot Linux 0.12 and verify that ls succeeds' \
		'  verify-userland     Verify minimal shell built-ins and helper commands' \
		'  check-images        Verify committed repo snapshots against images/manifest.json' \
		'  fetch-release-images Restore committed repo snapshots from the tagged GitHub Release' \
		'  repro-check         Build twice and verify that image outputs are reproducible' \
		'  release-readback    Re-download release assets and verify they still boot'

bootstrap-host:
	./scripts/bootstrap-host.sh

build:
	/usr/bin/python3 rebuild/driver.py build

run:
	./scripts/run.sh

run-window:
	./scripts/run-window.sh

verify:
	./scripts/verify.sh

verify-userland:
	./scripts/verify-userland.sh

check-images:
	./scripts/check-images.sh

fetch-release-images:
	./scripts/fetch-release-images.sh

repro-check:
	./scripts/check-reproducible-build.sh

release-readback:
	./scripts/verify-release-readback.sh
