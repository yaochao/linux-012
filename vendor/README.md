# Vendor Assets

This directory stores project-owned historical assets so the repo can run without downloading Linux 0.12 artifacts at runtime.

## Files

- `src/linux-0.12.tar.gz`
  - Source: `https://www.kernel.org/pub/linux/kernel/Historic/old-versions/linux-0.12.tar.gz`
- `images/bootimage-0.12-hd`
  - Source package: `https://mirror.cs.msu.ru/oldlinux.org/Linux.old/bochs-images/linux-0.12-080324.zip`
  - Original path inside the package: `linux-0.12-080324/bootimage-0.12-hd`
- `images/hdc-0.12.img`
  - Source repository: `https://github.com/chenzhengchen200821109/linux-0.12`
  - Original path inside the repository: `src/hdc-0.12.img`

## Runtime Behavior

- `bootimage-0.12-hd` is stored in its original short form.
- `tools/qemu_driver.py` pads it to a full 1.44MB floppy image in `out/run/boot.img` or `out/verify/boot.img` before QEMU starts.
- `hdc-0.12.img` is mounted as `hda`.
- QEMU always runs with `-snapshot`, so the vendored disk image remains unchanged across runs.
