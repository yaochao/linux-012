# Vendor Assets

This directory stores project-owned historical assets so the repo can run without downloading Linux 0.12 artifacts at runtime.

## Files

- `src/linux-0.12.tar.gz`
  - Source: `https://www.kernel.org/pub/linux/kernel/Historic/old-versions/linux-0.12.tar.gz`
- `images/bootimage-0.12`
  - Derived from: `https://mirror.math.princeton.edu/pub/oldlinux/Linux.old/Linux-0.12/images/bootimage-0.12.Z`
- `images/rootimage-0.12`
  - Derived from: `https://mirror.math.princeton.edu/pub/oldlinux/Linux.old/Linux-0.12/images/rootimage-0.12.Z`

The boot and root images are stored in raw form because QEMU consumes them directly that way. The source mirror publishes them in `.Z` form, so the repo stores the decompressed raw images and records the original URLs here.
