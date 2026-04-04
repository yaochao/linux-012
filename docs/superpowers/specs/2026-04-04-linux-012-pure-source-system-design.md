# Linux 0.12 Pure-Source System Design

## Goal

Replace all third-party runtime images with a pure source build pipeline that:

- starts from source archives and repo-owned build scripts only
- produces the boot image and system image required by QEMU
- boots Linux 0.12 successfully under the current QEMU workflow
- reaches a shell prompt
- executes `ls` successfully

This phase explicitly removes all dependence on downloaded boot or disk images. Third-party source code is allowed. Third-party prebuilt images are not allowed.

## Scope Boundary

The existing repository already compiles a QEMU-compatible Linux 0.12 boot image from source, but the hard disk image is still rebuilt from a root filesystem extracted from a historical disk image. That is not sufficient for the new requirement.

This phase must therefore build a complete minimal runnable system from source, not just a kernel image. The system only needs to satisfy the current acceptance target:

- boot under QEMU
- enter a shell
- run `ls`

It does not need to reproduce a full historical Linux 0.12 distribution.

## Approaches

### 1. Full Historical Distribution Rebuild

Import historical userland source packages, recreate an old Linux 0.12 user-space toolchain, and rebuild a large root filesystem close to the original era.

Pros:

- most historically faithful
- lowest conceptual gap between source and runtime system

Cons:

- the largest scope by far
- hardest toolchain and package-compatibility problem
- far beyond the minimum needed to satisfy `sh` + `ls`

### 2. Minimal Pure-Source System

Keep Linux 0.12 as the kernel target, but add a repo-owned minimal userland source tree that provides only the binaries and filesystem layout needed to boot, enter a shell, and run `ls`. Build both kernel and userland from source inside the container, then assemble a fresh Minix root filesystem image.

Pros:

- satisfies the acceptance target without image imports
- keeps the scope focused
- makes every runtime artifact traceable to source and scripts in the repo

Cons:

- requires introducing a Linux 0.12-compatible userland build chain
- yields a minimal system, not a broad historical environment

### 3. Modern Binary Format Adaptation

Patch Linux 0.12 heavily so it can load a more modern executable format and run a newer statically linked userland.

Pros:

- might reduce dependence on historical userland tools in theory

Cons:

- the most invasive kernel change
- still does not solve syscall and ABI mismatches cleanly
- high risk with little advantage for this project

## Recommendation

Use **Approach 2: Minimal Pure-Source System**.

It is the smallest coherent system that actually meets the requirement after all imported images are deleted. It keeps QEMU changes limited, avoids pretending that kernel source alone can produce a full root filesystem, and makes the hard part explicit: source-building a Linux 0.12-compatible minimal userland.

## Target Architecture

The repository will move from a `source kernel + imported runtime image` model to a `source kernel + source userland + source-built rootfs image` model.

The runtime path will still center on `tools/qemu_driver.py`, but its default images will come from the repo's own source-build pipeline instead of from imported historical images.

The repository will contain:

- Linux 0.12 kernel source
- patch series required for modern toolchains and QEMU
- minimal userland source required for `init`, shell, and `ls`
- root filesystem layout metadata
- containerized build environment for kernel and userland
- image assembly scripts
- automated boot-and-`ls` verification

## Required Repository Changes

### 1. Remove Third-Party Runtime Images

Delete:

- `vendor/images/bootimage-0.12-hd`
- `vendor/images/hdc-0.12.img`
- `rebuild/rootfs/base.tar`

The repository may keep third-party source archives, but must no longer keep or depend on imported runtime images.

### 2. Replace Rootfs Capture With Rootfs Construction

The current `capture-rootfs` path extracts a canonical filesystem from a historical disk image. That flow must be removed or repurposed because it violates the new source-only boundary.

Instead, the root filesystem must be assembled from:

- repo-owned directory layout metadata
- repo-owned device-node manifest
- repo-owned config files
- source-built user binaries

### 3. Add A Minimal Userland Source Tree

Introduce a new source area under `rebuild/` or `vendor/src/` that contains the minimum user-space components required to satisfy the acceptance target.

The minimal system should include:

- `init`
- `/bin/sh`
- `/bin/ls`
- any tiny support binaries or helpers required by the shell startup path

This userland does not need to be feature-rich. It only needs to boot and support the tested command path.

### 4. Add A Linux 0.12-Compatible Userland Toolchain Path

This is the key technical gap. Linux 0.12 user programs must match the executable format and syscall expectations that the kernel can actually run.

The build container must therefore grow from:

- kernel build tools

to:

- kernel build tools
- userland compiler/linker path that emits Linux 0.12-compatible binaries

The design assumes a containerized historical or compatibility toolchain will be used so the host machine does not need to manage this complexity directly.

### 5. Assemble The Root Filesystem From Scratch

The rootfs build must:

- create the target directory tree
- create required device nodes
- install source-built binaries into the correct paths
- write minimal boot-time config files
- format a Minix filesystem with Linux 0.12-compatible options
- inject that filesystem into the hard disk image layout used by QEMU

The key output is a fresh `hdc-0.12.img` produced without extracting any content from an imported image.

## Proposed Directory Changes

### New Or Repurposed Paths

- `vendor/src/linux-0.12.tar.gz`
  - retained
- `vendor/src/`
  - may gain userland source archives if external source imports are needed
- `rebuild/userland/`
  - repo-owned minimal userland source tree
- `rebuild/rootfs/manifest/`
  - directory layout, file placement, device-node definitions, and boot config inputs
- `rebuild/container/`
  - expanded to build kernel and userland from source

### Paths To Remove From The Runtime Contract

- `vendor/images/`
- `rebuild/rootfs/base.tar`

## Build Flow

The new end-to-end build flow will be:

1. Build the container image.
2. Extract Linux 0.12 kernel source.
3. Apply kernel portability and QEMU patches.
4. Compile the Linux 0.12 boot image from source.
5. Build the minimal userland binaries from source with the compatible toolchain.
6. Construct the root filesystem tree from manifests and built binaries.
7. Format a Linux 0.12-compatible Minix filesystem.
8. Assemble the hard disk image.
9. Run QEMU verification with only the newly built images.

No step may read files from `vendor/images/` or a rootfs tar captured from an imported image.

## Verification Rules

The new acceptance criteria are:

- the repository contains no third-party runtime images
- `rebuild/driver.py build` succeeds from source inputs only
- `rebuild/driver.py verify` boots the newly built images
- the guest reaches a shell prompt
- `ls` executes successfully

The test suite must also enforce the boundary:

- no rebuild script may reference `vendor/images/`
- no rebuild script may reference `rebuild/rootfs/base.tar`
- no capture-from-image workflow may remain on the critical path

## Error Handling

The build driver should fail early and clearly for:

- missing source archives
- missing Docker
- missing compatible userland toolchain inside the container
- unsupported executable format for built user binaries
- invalid Minix filesystem parameters
- boot failures during QEMU verification

Verification artifacts should continue to land in `out/verify/` so failures remain debuggable.

## Testing Strategy

Testing should expand in three layers:

### Static Tests

- repository layout tests for the new source-only structure
- script-content tests proving the build path does not reference imported runtime images
- tests that default verification environment points to source-built images

### Build Tests

- container build succeeds
- kernel image is produced
- userland binaries are produced
- hard disk image is produced

### Runtime Tests

- QEMU boot reaches a shell
- `ls` succeeds
- promoted default runtime path still passes `./scripts/verify.sh`

## Non-Goals

This phase does not aim to:

- recreate a full historical Linux distribution
- preserve compatibility with previously imported disk images
- provide a large Unix userland beyond what is needed for shell boot and `ls`

## Success Condition

This phase is complete when the repository can delete every imported runtime image, rebuild both required QEMU images from source and repo-owned manifests, boot Linux 0.12 successfully, enter the shell, and execute `ls` successfully.
