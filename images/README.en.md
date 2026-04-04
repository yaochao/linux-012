# `images/`

[中文 README](./README.md)

This directory stores the repo-managed runtime image snapshots. They are not third-party downloads. They are built by this repository's own `rebuild/` pipeline and then synced here.

## Current Files

- `bootimage-0.12-hd`
  Linux 0.12 boot image
- `hdc-0.12.img`
  Linux 0.12 minimal system hard disk image

## Usage

- `scripts/run.*` boots directly from the images here
- `scripts/run-window.*` boots directly from the images here and opens a visible window
- `scripts/build-and-run.*` and `scripts/build-and-run-window.*` rebuild first, then refresh the images here
