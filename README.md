# Linux 0.12 On QEMU

This repository boots historical Linux 0.12 under QEMU on macOS and keeps the project assets inside the repo.

## Host Requirement

Install QEMU on the host:

```sh
brew install qemu
```

## Repo Layout

- `scripts/bootstrap-host.sh`: checks for `qemu-system-i386`
- `scripts/run.sh`: interactive boot
- `scripts/verify.sh`: automated boot and `ls` verification
- `tools/qemu_driver.py`: QEMU runtime and verification logic
- `vendor/src/linux-0.12.tar.gz`: Linux 0.12 source archive
- `vendor/images/bootimage-0.12`: boot floppy image
- `vendor/images/rootimage-0.12`: root floppy image

## Planned Commands

```sh
./scripts/bootstrap-host.sh
./scripts/verify.sh
./scripts/run.sh
```

## Asset Provenance

- `vendor/src/linux-0.12.tar.gz` comes from the kernel.org historic archive.
- `vendor/images/bootimage-0.12` and `vendor/images/rootimage-0.12` are raw images decompressed from the Princeton oldlinux mirror's `.Z` files for Linux 0.12.
