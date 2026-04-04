# `images/`

[中文 README](./README.md)

This directory stores the repo-managed runtime image snapshots. They are not third-party downloads. They are built by this repository's own `rebuild/` pipeline and then synced here. To keep the repository smaller, the hard disk image is stored as a compressed snapshot.

## Current Files

- `bootimage-0.12-hd`
  Linux 0.12 boot image
- `hdc-0.12.img.xz`
  compressed snapshot of the Linux 0.12 minimal system hard disk image

## Usage

- `scripts/run.*` boots from the snapshots here and unpacks the hard disk image into `out/repo-images/`
- `scripts/run-window.*` boots from the snapshots here, unpacks the hard disk image into `out/repo-images/`, and opens a visible window
- `scripts/build-and-run.*` and `scripts/build-and-run-window.*` rebuild first, then refresh the snapshots here
