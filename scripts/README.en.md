# `scripts/`

[中文 README](./README.md)

This directory stores host-facing one-command entry scripts. Each platform has its own wrapper set, but they all delegate to `rebuild/driver.py`.

## Script Groups

- `bootstrap-host.*`
  check host dependencies such as Python, QEMU, and Docker
- `run.*`
  boot directly from the repo-managed snapshots and unpack the hard disk image automatically
- `run-window.*`
  boot directly from the repo-managed snapshots, unpack the hard disk image automatically, and open a visible QEMU window
- `build-and-run.*`
  rebuild first, then boot
- `build-and-run-window.*`
  rebuild first, then boot in a visible QEMU window
- `verify.*`
  boot automatically and verify `ls`
- `verify-userland.*`
  verify the current minimal shell built-ins automatically
