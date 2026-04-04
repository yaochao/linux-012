# Linux 0.12 Source Build Design

## Goal

Add a new repo-owned build area that ports the bundled Linux 0.12 source to the current QEMU workflow and regenerates the two runtime images this repository depends on:

- `bootimage-0.12-hd`
- `hdc-0.12.img`

Success means the existing QEMU boot-and-verify flow can stop reading the downloaded runtime images, boot the rebuilt images instead, reach the shell prompt, run `ls`, and return to the prompt.

## Current State

The repository currently boots Linux 0.12 with:

- `vendor/src/linux-0.12.tar.gz` as a historical source archive
- `vendor/images/bootimage-0.12-hd` as a historical prebuilt boot image
- `vendor/images/hdc-0.12.img` as a downloaded hard disk image
- `tools/qemu_driver.py` as the runtime and verification driver

The Linux 0.12 source archive includes the kernel build system and boot pipeline, but it does not include a complete userspace root filesystem. It can produce the bootable kernel image, but it cannot, by itself, produce the shell and userland that back `ls`.

The user explicitly allows source modifications where needed to make Linux 0.12 build and boot cleanly under the current QEMU-based workflow.

## Non-Goals

This phase does not attempt to recreate a historically pure 1992 build environment or compile the entire userspace from original source archives.

This phase does not remove the original downloaded images from history. It replaces them as the active runtime images after the rebuilt images have passed verification.

This phase does not redesign the current QEMU runtime interface. The existing `scripts/` and `tools/qemu_driver.py` flow remains the runtime source of truth.

## Approach Options

### Option 1: Rebuild Only The Boot Image

Build a new `bootimage-0.12-hd` from source and keep using the downloaded hard disk image.

This is the smallest change, but it does not satisfy the requirement to replace both runtime images.

### Option 2: Rebuild The Boot Image And Reassemble The System Image From Repo-Owned Rootfs Inputs

Create a new `rebuild/` directory that:

- applies a patch series to Linux 0.12 for modern toolchain and QEMU compatibility
- builds a repo-owned `bootimage-0.12-hd`
- stores a canonical repo-owned rootfs source input
- assembles a fresh `hdc-0.12.img` from that rootfs and a fixed disk layout
- verifies the rebuilt images through the existing QEMU driver before promoting them

This is the recommended scope for this phase. It produces reproducible runtime images without pretending the Linux 0.12 kernel archive alone contains a full userspace.

### Option 3: Rebuild Kernel And Full Userspace From Historical Source Archives

Add a second historical-source recovery project for shell, core utilities, init, and filesystem layout.

This is the most complete approach, but it is larger than the current phase and should be treated as its own project after the repo can already regenerate working runtime images.

## Recommended Design

Use Option 2.

The repository will gain a dedicated `rebuild/` directory that owns the source-to-image pipeline. The top-level runtime remains unchanged except for one extension: `tools/qemu_driver.py` will be able to read alternate image paths so the verifier can boot rebuilt artifacts before they replace the vendored images.

The build pipeline will be split into three layers:

1. Host-side orchestration in Python under `rebuild/driver.py`
2. A containerized Linux build environment under `rebuild/Dockerfile`
3. Container-side scripts and data under `rebuild/container/`, `rebuild/patches/`, and `rebuild/rootfs/`

This keeps host differences small while isolating the fragile x86-era build tooling inside a fixed Linux amd64 container.

## Why Containerization

The Linux 0.12 `Makefile` expects `as86`, `ld86`, `gcc`, `gas`, and `gld` in an x86-oriented environment. That is not a stable assumption on modern macOS arm64, Ubuntu 22.04 arm64, or Windows 10 hosts.

The build pipeline will therefore standardize on a Docker-based Linux amd64 container for image generation. The host only needs:

- Docker or Docker Desktop
- Python 3
- the repo checkout
- the already-supported host QEMU install for runtime verification

The container will own:

- the 16-bit boot toolchain (`as86`, `ld86`)
- the modern GNU toolchain wrappers needed for 32-bit kernel objects
- disk layout tools
- filesystem tools used to construct the rebuilt hard disk image

## Source Modification Policy

`vendor/src/linux-0.12.tar.gz` remains untouched as the historical source-of-record.

All changes needed to build and boot under the current QEMU workflow will live as patch files under:

`rebuild/patches/linux-0.12/`

These patches may cover:

- toolchain modernization for current GNU `gcc`, `as`, and `ld`
- explicit 32-bit build flags
- root-device defaults that match the rebuilt disk layout
- small QEMU-compatibility fixes where the original source assumes older emulator or BIOS behavior

The build flow always starts from the historical tarball, then applies the patch series.

## System Image Strategy

The system image in this phase is a rebuilt artifact, not a historically complete userspace source build.

To make the hard disk image reproducible and repo-owned, `rebuild/` will contain a canonical rootfs source input. The simplest stable representation is a tar archive that preserves the shell, utilities, metadata, and layout needed by the working Linux 0.12 system:

- `rebuild/rootfs/base.tar`

This tarball becomes the authoritative rootfs input for the system image build. A fresh `hdc-0.12.img` is then assembled from:

- a fixed raw disk size
- a fixed single-partition MBR layout
- a fixed filesystem creation step
- the contents of `rebuild/rootfs/base.tar`
- any small repo-owned overlay adjustments needed for verification

This is the smallest honest way to replace the downloaded system image with a repo-owned rebuilt system image while keeping the phase focused.

## Transitional Bootstrap

There is one unavoidable bootstrapping step in this phase: the canonical rootfs source input has to come from somewhere because the Linux 0.12 kernel archive does not contain userspace.

The design therefore includes a one-time capture flow that extracts the currently working filesystem contents from `vendor/images/hdc-0.12.img` and writes the canonical repo-owned rootfs archive under `rebuild/rootfs/base.tar`.

After that capture has been committed, the rebuild flow no longer needs the downloaded hard disk image to regenerate `hdc-0.12.img`.

The acceptance criterion for this phase is not “never touched the old image during development”; it is “the runtime images used by the project can now be regenerated by the repo-owned pipeline and replace the downloaded runtime images successfully.”

## Directory Layout

The new directory will be:

```text
rebuild/
├── README.md
├── Dockerfile
├── driver.py
├── container/
│   ├── build_images.sh
│   └── capture_rootfs.sh
├── patches/
│   └── linux-0.12/
│       ├── 0001-modernize-toolchain.patch
│       └── 0002-qemu-root-device.patch
├── rootfs/
│   ├── base.tar
│   ├── layout.sfdisk
│   └── overlay/
└── out/
    ├── images/
    ├── logs/
    └── work/
```

Responsibilities:

- `rebuild/driver.py`: host entrypoint for `capture-rootfs`, `build`, `verify`, and `promote`
- `rebuild/Dockerfile`: fixed Linux amd64 build environment
- `rebuild/container/build_images.sh`: container-side rebuild flow
- `rebuild/container/capture_rootfs.sh`: one-time extraction of the canonical rootfs tarball
- `rebuild/patches/linux-0.12/`: patch series applied to the historical source archive
- `rebuild/rootfs/layout.sfdisk`: disk partition layout for the rebuilt `hdc-0.12.img`
- `rebuild/rootfs/base.tar`: canonical filesystem content input
- `rebuild/rootfs/overlay/`: small repo-owned updates applied on top of `base.tar`
- `rebuild/out/`: generated artifacts and logs, ignored by git

## Build Flow

### 1. Rootfs Capture

`python3 rebuild/driver.py capture-rootfs`

This command:

- builds the rebuild container if needed
- runs a privileged container-side extraction step against `vendor/images/hdc-0.12.img`
- extracts the active Linux partition
- captures it as `rebuild/rootfs/base.tar`

This command is only needed when the canonical rootfs input is missing or intentionally refreshed.

### 2. Image Build

`python3 rebuild/driver.py build`

This command:

- unpacks `vendor/src/linux-0.12.tar.gz` into `rebuild/out/work/`
- applies `rebuild/patches/linux-0.12/*.patch`
- compiles a new Linux 0.12 image suitable for the current QEMU flow
- writes `rebuild/out/images/bootimage-0.12-hd`
- creates a fresh raw hard disk image with the fixed layout from `rebuild/rootfs/layout.sfdisk`
- populates the filesystem from `rebuild/rootfs/base.tar` plus `rebuild/rootfs/overlay/`
- writes `rebuild/out/images/hdc-0.12.img`

### 3. Verification

`python3 rebuild/driver.py verify`

This command:

- points `tools/qemu_driver.py` at `rebuild/out/images/bootimage-0.12-hd`
- points `tools/qemu_driver.py` at `rebuild/out/images/hdc-0.12.img`
- reuses the existing boot-to-shell and `ls` automation
- stores proof under `rebuild/out/logs/` and the normal `out/verify/`

### 4. Promotion

`python3 rebuild/driver.py promote`

This command:

- requires a successful `verify`
- copies the rebuilt images over the active vendored runtime images
- reruns `./scripts/verify.sh` against the promoted images

This final step is the explicit acceptance gate for replacing the downloaded runtime images.

## Runtime Integration

`tools/qemu_driver.py` will gain image override support through environment variables:

- `LINUX012_BOOT_SOURCE_IMAGE`
- `LINUX012_HARD_DISK_IMAGE`

If unset, the driver continues to use the current defaults under `vendor/images/`.

This preserves all existing scripts and tests while allowing `rebuild/driver.py verify` to point the runtime at rebuilt artifacts without mutating the active vendored images too early.

## Failure Handling

The rebuild flow must fail early and loudly in these cases:

- Docker is missing
- the rebuild container cannot start with the required privileges
- `rebuild/rootfs/base.tar` is missing when `build` runs
- the Linux 0.12 patch series does not apply cleanly
- the kernel build does not produce a boot image
- the rebuilt hard disk image is missing or empty
- QEMU verification fails to reach a prompt or fails to run `ls`

Each failure path must write logs into `rebuild/out/logs/` and print the exact failing stage.

## Testing Strategy

Three layers of verification are required.

### 1. Unit Tests

Add tests for:

- `rebuild/` layout presence
- host-side path resolution in `rebuild/driver.py`
- Docker command construction in `rebuild/driver.py`
- image override behavior in `tools/qemu_driver.py`

### 2. Build Artifact Checks

The build flow must verify:

- `rebuild/out/images/bootimage-0.12-hd` exists and is non-empty
- `rebuild/out/images/hdc-0.12.img` exists and is non-empty
- the hard disk image has the expected single active Linux partition layout

### 3. End-To-End Runtime Verification

The rebuilt images must:

- boot under the existing runtime
- reach `[/]#`
- execute `ls`
- return to `[/]#`

## Acceptance Criteria

This phase is complete only when all of the following are true:

1. The repo contains a new `rebuild/` directory with the rebuild pipeline, patch series, rootfs source input, and docs.
2. `python3 rebuild/driver.py build` generates both required runtime images under `rebuild/out/images/`.
3. `python3 rebuild/driver.py verify` proves the rebuilt images boot and execute `ls`.
4. `python3 rebuild/driver.py promote` replaces the active runtime images in `vendor/images/`.
5. After promotion, the standard runtime command `./scripts/verify.sh` still succeeds without any image override variables.

## Out Of Scope For This Phase

- historical userspace source recovery
- reproducing the exact original compiler environment from 1992
- adding a second emulator target besides QEMU
- redesigning the existing runtime verification mechanism
