# `tools/`

[中文 README](./README.md)

This directory stores host-side helper tools used during runtime. The main file here is the QEMU driver script.

## Current Files

- `qemu_driver.py`
  prepares boot media, launches QEMU, captures VGA text, injects keys through the monitor, and completes automated verification
- `__init__.py`
  allows the directory to be imported as a Python module
