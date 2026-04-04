# Vendor Assets

`vendor/` now stores third-party source inputs only. Runtime images are built locally and written to `rebuild/out/images/`.

## Files

- `src/linux-0.12.tar.gz`
  - Source: `https://www.kernel.org/pub/linux/kernel/Historic/old-versions/linux-0.12.tar.gz`

## Runtime Contract

- `rebuild/driver.py build` generates the runtime images under `rebuild/out/images/`
- `rebuild/driver.py verify` boots those images in QEMU and runs `ls`
- `tools/qemu_driver.py` pads the short boot image into `out/run/boot.img` or `out/verify/boot.img` before QEMU starts
- QEMU always runs with `-snapshot`, so repeated runs do not mutate the generated hard disk image

## Provenance Boundary

- Third-party source archive: allowed in `vendor/src/`
- Third-party runtime images: not stored and not used
- Runtime images: produced locally from repo-owned source, patches, and manifests
