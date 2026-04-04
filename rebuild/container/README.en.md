# `rebuild/container/`

[中文 README](./README.md)

This directory stores the scripts executed inside the build container. They run in the environment created by `rebuild/Dockerfile` and produce the Linux 0.12 runtime images.

## Current File

- `build_images.sh`
  builds the boot image, minimal userland, Minix root filesystem, and hard disk image
