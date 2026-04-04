# Linux 0.12 on QEMU

[中文 README](./README.md)
[Changelog](./CHANGELOG.en.md)

This repository does one specific thing: on a modern host, it builds the two runtime images required to boot Linux 0.12 under QEMU from source and repo-owned manifests, enters the shell, and verifies the result by running `ls`.

The repository no longer stores third-party runtime images. The repository now includes self-built runtime image snapshots under version control:

- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`

The same source-build workflow also produces local working images:

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`

## What This Project Delivers

The build and runtime flow is:

- unpack Linux 0.12 from `vendor/src/linux-0.12.tar.gz`
- apply repo-owned compatibility patches
- compile the kernel boot image
- compile the repo-owned minimal userland programs `/bin/sh` and `/bin/ls`
- build a Minix v1 root filesystem from repo manifests
- generate the repo-bundled images `images/bootimage-0.12-hd` and `images/hdc-0.12.img.xz`
- boot QEMU
- reach `[/usr/root]#`
- run `ls`

This is not a “download a historical image and boot it” repo. It is a “rebuild the runtime images locally and boot them” repo.

Current formal release: `v1.0.0`

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

### 3. Start QEMU From The Bundled Images

If you just want to boot Linux 0.12 immediately, run:

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

This entrypoint uses the committed snapshots in `images/` directly and does not rebuild first. The hard disk image is automatically unpacked to `out/repo-images/hdc-0.12.img` before launch. On macOS / Ubuntu it keeps the current terminal-based interactive flow; on Windows it already uses a visible GUI window.

### 4. Open A Visible QEMU Window And Interact Manually

If you want a visible QEMU window that you can click into and operate yourself, run:

macOS / Ubuntu:

```sh
./scripts/run-window.sh
```

Windows PowerShell:

```powershell
.\scripts\run-window.ps1
```

Windows CMD:

```bat
scripts\run-window.cmd
```

On this macOS host, this entrypoint explicitly uses QEMU's `cocoa` display backend.

### 5. Rebuild From Source, Then Start QEMU

If you want the flow to start from compilation every time, run:

macOS / Ubuntu:

```sh
./scripts/build-and-run.sh
```

Windows PowerShell:

```powershell
.\scripts\build-and-run.ps1
```

Windows CMD:

```bat
scripts\build-and-run.cmd
```

This entrypoint forces a rebuild, syncs the new images into `images/`, stores the hard disk image as the compressed snapshot `images/hdc-0.12.img.xz`, and then starts QEMU.

If you want the flow to start from compilation and still end in a visible interactive QEMU window, run:

macOS / Ubuntu:

```sh
./scripts/build-and-run-window.sh
```

Windows PowerShell:

```powershell
.\scripts\build-and-run-window.ps1
```

Windows CMD:

```bat
scripts\build-and-run-window.cmd
```

### 6. Verify End-to-End

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

If you also want a guest-side check of the current minimal shell built-ins, run:

macOS / Ubuntu:

```sh
./scripts/verify-userland.sh
```

Windows PowerShell:

```powershell
.\scripts\verify-userland.ps1
```

Windows CMD:

```bat
scripts\verify-userland.cmd
```

## Common Commands

Start QEMU from the committed repo images:

```sh
python3 rebuild/driver.py run-repo-images
```

Start QEMU from the committed repo images with a visible window:

```sh
python3 rebuild/driver.py run-repo-images-window
```

Force a fresh rebuild, sync `images/`, and then start QEMU:

```sh
python3 rebuild/driver.py build-and-run-repo-images
```

Force a fresh rebuild, sync `images/`, and then start QEMU in a visible window:

```sh
python3 rebuild/driver.py build-and-run-repo-images-window
```

## Continuous Integration

The repository now includes the GitHub Actions workflow [ci.yml](/Users/infoxmed-01/ai/workspace/linux-012/.github/workflows/ci.yml). On pushes to `main` and pull requests targeting `main`, it runs the following on `ubuntu-22.04`:

- `python3 -m unittest discover -s tests -v`
- `./scripts/bootstrap-host.sh`
- `python3 rebuild/driver.py build`
- `./scripts/verify.sh`

On failure it uploads `out/verify` and `rebuild/out/logs` as debugging artifacts.

Build the images explicitly:

```sh
python3 rebuild/driver.py build
```

Run source-build verification directly:

```sh
python3 rebuild/driver.py verify
```

Verify the current shell built-ins `pwd`, `echo`, `cat`, `uname`, and `cd`:

```sh
python3 rebuild/driver.py verify-userland
```

Start an interactive session with source-built images:

```sh
python3 rebuild/driver.py run
```

Important generated artifacts:

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`
- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`
- `out/repo-images/hdc-0.12.img`
- `out/verify/screen.txt`
- `out/verify-userland/screen.txt`
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
9. sync the new boot image and compressed hard disk snapshot into the repo-managed `images/` directory when requested
10. boot QEMU, scrape VGA text, and inject keys to complete verification

This pipeline intentionally builds only the smallest system required by the repo. It does not try to recreate a full historical Linux 0.12 distribution.

The current shell provides these built-in commands:

- `cd`
- `pwd`
- `echo`
- `cat`
- `uname`
- `exit`

The current standalone userland binaries are:

- `/bin/sh`
- `/bin/ls`

## Repository Layout

- `scripts/`
  host-specific entry scripts
- `images/`
  committed snapshots of the self-built runtime images, with the hard disk stored in compressed form
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
- `scripts/run.*` uses the committed snapshots in `images/` by default and unpacks the hard disk image into `out/repo-images/`
- `scripts/run-window.*` uses the committed snapshots in `images/`, unpacks the hard disk image into `out/repo-images/`, and opens a visible QEMU window
- `scripts/build-and-run.*` rebuilds from source and refreshes `images/`
- `scripts/build-and-run-window.*` rebuilds from source, refreshes `images/`, and opens a visible QEMU window
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
- verify the current minimal shell built-ins automatically

This project does not try to:

- recreate a full historical Linux 0.12 distribution
- ship a broad historical userland
- preserve or depend on third-party runtime images

## Provenance

- `vendor/src/linux-0.12.tar.gz` comes from the kernel.org historic Linux 0.12 source archive
- Runtime images are not downloaded from third parties; they are built locally from repo-owned sources, patches, and manifests
