# `rebuild/rootfs/manifest/`

[中文 README](./README.md)

This directory stores root filesystem manifests. It describes which directories to create, which device nodes to create, and which initial files should be copied into the image.

## Current Files

- `directories.txt`
  list of directories to create
- `devices.tsv`
  device node definitions
- `etc/`
  files copied into guest `/etc`
- `usr/`
  files copied into guest `/usr`
