# Third-Party Provenance And Licensing Notes

[中文版本](./THIRD_PARTY.md)

This repository now contains two kinds of material:

- repo-authored scripts, patches, minimal userland sources, tests, and documentation
- third-party source inputs kept in the repository so Linux 0.12 can be rebuilt

The root [LICENSE](./LICENSE) applies only to repo-authored material. It does not replace the upstream terms or obligations attached to third-party source code.

## Third-Party Source Distributed In This Repository

### `vendor/src/linux-0.12.tar.gz`

- Type: upstream historical source archive
- Purpose: input to the `rebuild/` pipeline that produces the Linux 0.12 boot and runtime images
- Origin: the Linux 0.12 source archive from the kernel.org historic release archive
- Repo status: the archive is kept as-is under `vendor/src/`
- Local modification strategy: compatibility and QEMU-related changes live separately under `rebuild/patches/linux-0.12/`

## Licensing Boundary For Generated Images

- `images/bootimage-0.12-hd`
  contains the boot chain built from upstream Linux 0.12 kernel sources
- `images/hdc-0.12.img.xz`
  is a generated runtime snapshot assembled from upstream Linux 0.12 kernel sources, repo-owned minimal userland sources, and repo-owned filesystem manifests

These images are generated artifacts. They should not be treated as files covered only by the root MIT license. Redistribution and reuse still need to account for the upstream Linux 0.12 code embedded in those outputs.

## Main Repo-Authored Areas

The following areas are generally repo-authored and covered by the root [LICENSE](./LICENSE):

- `rebuild/driver.py`
- `rebuild/container/`
- `rebuild/tools/`
- `rebuild/rootfs/`
- `rebuild/userland/`
- `rebuild/patches/linux-0.12/`
- `tools/`
- `scripts/`
- `tests/`
- repository documentation and GitHub Actions workflows

## External Dependencies Not Redistributed Here

The following are required to build or run the project, but they are not bundled in this repository:

- QEMU
- Docker / Docker Desktop
- Python 3
- official GitHub Actions used by CI and release workflows

Each of those dependencies carries its own upstream license terms.
