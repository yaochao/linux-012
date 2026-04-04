# Linux 0.12 Rebuild Pipeline

`rebuild/` owns the source-to-image workflow for this repository.

## What It Produces

- `rebuild/out/images/bootimage-0.12-hd`
  - built from patched Linux 0.12 kernel source in `vendor/src/linux-0.12.tar.gz`
- `rebuild/out/images/hdc-0.12.img`
  - built from repo-owned minimal userland sources plus rootfs manifests
- `images/bootimage-0.12-hd`
  - repo-managed snapshot copied from `rebuild/out/images/bootimage-0.12-hd`
- `images/hdc-0.12.img`
  - repo-managed snapshot copied from `rebuild/out/images/hdc-0.12.img`

The repository no longer depends on imported runtime images or a rootfs captured from a third-party disk image.

## Requirements

- Python 3
- Docker
- `qemu-system-i386` on `PATH` if you want to run any QEMU boot command, including `run`, `run-repo-images`, `run-repo-images-window`, `build-and-run-repo-images`, `build-and-run-repo-images-window`, `verify`, or `verify-userland`

## Commands

Build the containerized toolchain and regenerate both runtime images:

```sh
python3 rebuild/driver.py build
```

Boot QEMU with the rebuilt images:

```sh
python3 rebuild/driver.py run
```

Boot QEMU from the committed repo images in `images/`:

```sh
python3 rebuild/driver.py run-repo-images
```

Boot QEMU from the committed repo images in a visible window:

```sh
python3 rebuild/driver.py run-repo-images-window
```

Force a rebuild, sync the new images into `images/`, and then boot QEMU:

```sh
python3 rebuild/driver.py build-and-run-repo-images
```

Force a rebuild, sync the new images into `images/`, and then boot QEMU in a visible window:

```sh
python3 rebuild/driver.py build-and-run-repo-images-window
```

Boot QEMU with the rebuilt images, wait for the shell prompt, and run `ls`:

```sh
python3 rebuild/driver.py verify
```

Boot QEMU with the rebuilt images and verify the current shell built-ins:

```sh
python3 rebuild/driver.py verify-userland
```

Check host dependencies:

```sh
python3 rebuild/driver.py bootstrap-host
```

`run`, `verify`, and `verify-userland` automatically call `build` if the runtime images are missing. `run-repo-images` and `run-repo-images-window` use only the committed images in `images/`.

## Typical Workflow

```sh
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
```

## Directory Layout

- `driver.py`: host-side CLI for bootstrap, build, run, run-repo-images, run-repo-images-window, build-and-run-repo-images, build-and-run-repo-images-window, verify, and verify-userland
- `../images/`: repo-managed snapshots of the self-built runtime images
- `Dockerfile`: container image for the Linux 0.12-compatible build toolchain
- `container/build_images.sh`: container-side script that builds both runtime images
- `patches/linux-0.12/`: patch series applied to Linux 0.12 source
- `userland/`: minimal Linux 0.12-compatible `/bin/sh` and `/bin/ls` sources
- `tools/aout_pack.py`: packs generated ELF binaries into Linux 0.12 `ZMAGIC` executables
- `rootfs/layout.sfdisk`: hard disk partition layout
- `rootfs/manifest/`: directory tree, device node, and boot-file manifests
- `out/images/`: locally generated runtime images
- `out/logs/`: build logs

## Build Boundary

This pipeline rebuilds the runtime from:

- upstream Linux 0.12 source
- repo-owned patch series
- repo-owned minimal userland source
- repo-owned rootfs manifests

It does not attempt to recreate a full historical Linux 0.12 user-space distribution.
