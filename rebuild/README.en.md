# `rebuild/`

[中文 README](./README.md)

`rebuild/` is the source-to-image build center of this repository. It turns the Linux 0.12 kernel source, minimal userland source, rootfs manifests, and patch set into runtime images that QEMU can boot.

## Responsibilities

- build `rebuild/out/images/bootimage-0.12-hd`
- build `rebuild/out/images/hdc-0.12.img`
- use `driver.py` to orchestrate Docker and QEMU for build, boot, and verification
- sync the built boot image and compressed hard disk snapshot into the repo-level `images/` directory when requested

## Main Contents

- `driver.py`
  host-side entrypoint for `build`, `run`, `verify`, and related commands
- `Dockerfile`
  container definition for the Linux 0.12-compatible toolchain
- `container/`
  in-container scripts that assemble the runtime images
- `patches/`
  patch series applied to Linux 0.12 source
- `rootfs/`
  root filesystem layout, directory manifests, device nodes, and boot files
- `tools/`
  helper scripts used during the build
- `userland/`
  repo-owned minimal Linux 0.12 userland source

## Common Commands

```sh
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
python3 rebuild/driver.py run-repo-images
python3 rebuild/driver.py run-repo-images-window
```

## Boundary

- this directory owns source build and image assembly
- runtime output under `rebuild/out/` is generated content
- repo-managed image snapshots live in the top-level `images/` directory, with the hard disk stored in compressed form
