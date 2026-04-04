# `rebuild/rootfs/`

[中文 README](./README.md)

This directory stores the assembly inputs for the root filesystem. It defines the disk layout, directory tree, device node sources, and the initial files placed in the guest.

## Main Contents

- `layout.sfdisk`
  hard disk partition layout
- `manifest/`
  manifests for directories, device nodes, and initial files in the root filesystem
- `overlay/`
  reserved overlay directory, currently empty
