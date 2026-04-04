# Linux 0.12 on QEMU

[中文 README](./README.md)

This repository does one specific thing: on a modern host, it builds the two runtime images required to boot Linux 0.12 under QEMU from source and repo-owned manifests, enters the shell, and verifies the result by running `ls`.

The repository no longer stores third-party runtime images. The images used at runtime are built locally by the `rebuild/` workflow:

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`

## What This Project Delivers

The build and runtime flow is:

- unpack Linux 0.12 from `vendor/src/linux-0.12.tar.gz`
- apply repo-owned compatibility patches
- compile the kernel boot image
- compile the repo-owned minimal userland programs `/bin/sh` and `/bin/ls`
- build a Minix v1 root filesystem from repo manifests
- boot QEMU
- reach `[/usr/root]#`
- run `ls`

This is not a “download a historical image and boot it” repo. It is a “rebuild the runtime images locally and boot them” repo.

## Supported Hosts

- macOS arm64
- Ubuntu 22.04
- Windows 10

## Quick Start

### 1. Install Dependencies

All hosts need:

- Python 3
- Docker
- QEMU

macOS arm64:

```sh
brew install qemu
```

Ubuntu 22.04:

```sh
sudo apt update
sudo apt install -y python3 qemu-system-x86 docker.io
```

Windows 10:

- Install Python 3
- Install Docker Desktop
- Install QEMU for Windows
- Ensure `qemu-system-i386.exe` is on `PATH`, or set `LINUX012_QEMU_BIN` to the full path

Notes:

- On Ubuntu, the current user must be able to run `docker`
- The first build can take a while because the Docker build environment must be prepared

### 2. Check Host Dependencies

macOS / Ubuntu:

```sh
./scripts/bootstrap-host.sh
```

Windows PowerShell:

```powershell
.\scripts\bootstrap-host.ps1
```

Windows CMD:

```bat
scripts\bootstrap-host.cmd
```

### 3. Verify End-to-End

The recommended entrypoint is the verification script. If the runtime images are missing, it automatically triggers the source build first.

macOS / Ubuntu:

```sh
./scripts/verify.sh
```

Windows PowerShell:

```powershell
.\scripts\verify.ps1
```

Windows CMD:

```bat
scripts\verify.cmd
```

On success, the guest ends in a state like:

```text
[/usr/root]# ls
README
[/usr/root]#
```

### 4. Start an Interactive Session

macOS / Ubuntu:

```sh
./scripts/run.sh
```

Windows PowerShell:

```powershell
.\scripts\run.ps1
```

Windows CMD:

```bat
scripts\run.cmd
```

## Common Commands

Build the images explicitly:

```sh
python3 rebuild/driver.py build
```

Run source-build verification directly:

```sh
python3 rebuild/driver.py verify
```

Start an interactive session with source-built images:

```sh
python3 rebuild/driver.py run
```

Important generated artifacts:

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`
- `out/verify/screen.txt`
- `out/run/boot.img`

## What The Build Pipeline Does

The `rebuild/` directory owns the full source-to-image pipeline:

1. unpack `vendor/src/linux-0.12.tar.gz`
2. apply patches from `rebuild/patches/linux-0.12/`
3. compile the Linux 0.12 boot image
4. compile the minimal userland sources in `rebuild/userland/`
5. pack generated ELF binaries into Linux 0.12 `ZMAGIC` a.out executables
6. create directories, device nodes, and boot files from `rebuild/rootfs/manifest/`
7. build a Minix v1 root filesystem that Linux 0.12 can mount
8. assemble `hdc-0.12.img`
9. boot QEMU, scrape VGA text, and inject keys to complete verification

This pipeline intentionally builds only the smallest system required by the repo. It does not try to recreate a full historical Linux 0.12 distribution.

## Repository Layout

- `scripts/`
  host-specific entry scripts
- `rebuild/driver.py`
  source build, runtime, and verification entrypoint
- `rebuild/container/build_images.sh`
  container-side image build script
- `rebuild/patches/linux-0.12/`
  Linux 0.12 patches for QEMU and modern toolchains
- `rebuild/userland/`
  minimal Linux 0.12 userland sources
- `rebuild/rootfs/manifest/`
  root filesystem manifests for directories, device nodes, and boot files
- `rebuild/tools/aout_pack.py`
  packs ELF output into Linux 0.12 `ZMAGIC` executables
- `tools/qemu_driver.py`
  QEMU launch, VGA scraping, and automated key injection
- `tests/`
  tests for the build pipeline and runtime entrypoints
- `vendor/src/linux-0.12.tar.gz`
  upstream Linux 0.12 source archive

## Runtime Notes

- The boot image is shorter than 1.44MB, so the driver pads it into a full floppy image before launch
- QEMU always starts with `-snapshot`, so repeated runs do not mutate `rebuild/out/images/hdc-0.12.img`
- Interactive mode on macOS and Ubuntu 22.04 uses `-display curses`
- Interactive mode on Windows 10 uses QEMU's default GUI window
- macOS / Ubuntu use a local Unix socket for the QEMU monitor
- Windows 10 uses a localhost TCP monitor

## Scope Boundary

This project does:

- build runtime images from source
- boot Linux 0.12 to a shell
- run `ls` automatically

This project does not try to:

- recreate a full historical Linux 0.12 distribution
- ship a broad historical userland
- preserve or depend on third-party runtime images

## Provenance

- `vendor/src/linux-0.12.tar.gz` comes from the kernel.org historic Linux 0.12 source archive
- Runtime images are not downloaded from third parties; they are built locally from repo-owned sources, patches, and manifests
