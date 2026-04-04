# `rebuild/patches/linux-0.12/`

[中文 README](./README.md)

This directory stores the Linux 0.12 patch series used to adapt the upstream source to modern toolchains, the current build flow, and the QEMU runtime environment.

## Current Patches

- `0001-modernize-toolchain.patch`
  handles modern toolchain compatibility
- `0002-qemu-root-device.patch`
  adjusts root device behavior for QEMU boot
- `0003-modern-inline-semantics.patch`
  fixes modern compiler differences around inline semantics and PIE/PIC
