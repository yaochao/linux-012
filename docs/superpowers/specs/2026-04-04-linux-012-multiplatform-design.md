# Linux 0.12 Multiplatform Design

**Date:** 2026-04-04

## Goal

Extend the existing self-contained Linux 0.12 QEMU repository so the same checkout can be used on:

- macOS arm64
- Ubuntu 22.04
- Windows 10

The project must continue to boot Linux 0.12, reach the shell prompt, and run an automated `ls` verification flow.

## Chosen Approach

Keep `tools/qemu_driver.py` as the single source of truth and move all host-specific behavior into a small platform layer inside that driver. Add thin wrapper scripts for each host shell instead of duplicating boot logic.

This keeps the repo operationally simple:

- one runtime implementation
- one verification implementation
- per-platform entrypoint wrappers only where required

## Alternatives Considered

### 1. Separate shell scripts per operating system

This would minimize Python changes, but the boot logic would diverge quickly and verification behavior would become difficult to keep consistent across platforms.

### 2. Portable Python driver plus thin wrappers

This is the selected design. QEMU invocation, runtime asset preparation, VGA scraping, and input injection stay in Python. Shell, PowerShell, and batch wrappers only dispatch into the driver.

### 3. Introduce an external task runner

This would unify command entrypoints but would add a new dependency to a repo whose main value is portability and self-containment.

## Platform Strategy

### Common Behavior

All platforms continue to use:

- the vendored Linux 0.12 boot image
- the vendored Linux 0.12 hard disk image
- a runtime-generated padded floppy image in `out/<session>/boot.img`
- `-snapshot` so vendored images remain unchanged

### macOS and Ubuntu 22.04

- Interactive mode uses `-display curses`
- Verification uses `-display none`
- QEMU monitor transport uses a UNIX domain socket
- Host bootstrap checks for `qemu-system-i386` on `PATH`

### Windows 10

- Interactive mode uses the default QEMU windowed display by omitting `-display curses`
- Verification uses `-display none`
- QEMU monitor transport uses loopback TCP instead of a UNIX socket
- Host bootstrap checks for `qemu-system-i386.exe` and also searches common install locations if it is not already on `PATH`
- Windows wrappers are provided for both PowerShell and `cmd`

## Driver Changes

`tools/qemu_driver.py` will gain:

- host platform detection
- per-platform QEMU discovery and install guidance
- monitor endpoint abstraction
- Windows-safe monitor connection logic
- platform-aware display selection
- a Python-hosted bootstrap command so every wrapper delegates to the same implementation

The driver remains responsible for:

- preparing `out/run` and `out/verify`
- padding the boot image
- launching QEMU
- driving the boot prompt
- detecting the Linux shell prompt
- sending `ls` in verification mode

## Wrapper Scripts

The repo will expose:

- existing POSIX wrappers for macOS and Ubuntu
- new `*.ps1` wrappers for Windows PowerShell
- new `*.cmd` wrappers for Windows Command Prompt

All wrappers will be thin shims into `tools/qemu_driver.py`.

## Documentation

`README.md` will be updated to describe:

- supported host platforms
- host-specific installation instructions at a high level
- which script to run on Unix vs Windows
- Windows-specific notes such as PowerShell and `cmd` entrypoints

## Testing

This workspace can only execute macOS behavior directly, so the implementation will be verified in two layers:

1. Real local execution on macOS for the end-to-end boot and `ls` verification flow
2. Unit tests for Ubuntu and Windows command construction, monitor selection, QEMU discovery, and wrapper coverage

The test suite must prove:

- macOS/Linux interactive mode still uses curses
- Windows interactive mode uses a visible QEMU window
- Windows verification mode uses loopback TCP monitor
- bootstrap guidance changes by platform
- Windows wrapper files exist and point into the Python driver

## Constraints

- No runtime downloads
- No new non-standard Python dependency
- All project-owned assets stay inside the repository
- Existing macOS behavior must not regress
