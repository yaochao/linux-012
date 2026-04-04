# Linux 0.12 Rebuild

This directory owns the source-to-image pipeline for rebuilding the Linux 0.12 runtime images used by this repository.

Planned entrypoints:

- `python3 rebuild/driver.py capture-rootfs`
- `python3 rebuild/driver.py build`
- `python3 rebuild/driver.py verify`
- `python3 rebuild/driver.py promote`
