# Linux 0.12 On QEMU

This repository boots Linux 0.12 under `qemu-system-i386` and keeps all project artifacts inside the repo. The runtime is organized around one Python driver with thin host-specific wrappers for:

- macOS arm64
- Ubuntu 22.04
- Windows 10

The working boot path is:

- one historical Linux 0.12 boot floppy image
- one Linux 0.12 hard disk image mounted as `hda`
- one runtime step that pads the short boot image into a standard 1.44MB floppy before each launch

On Unix-like hosts, `./scripts/run.sh` lands at the Linux shell prompt `[/]#` inside a terminal curses UI.
On Windows 10, `scripts\run.cmd` or `.\scripts\run.ps1` opens the default QEMU window and drives the same boot flow.
The verification entrypoints boot the same VM, run `ls`, and exit non-zero if verification fails.

## Host Requirements

### macOS arm64

```sh
brew install qemu
```

### Ubuntu 22.04

```sh
sudo apt update
sudo apt install -y python3 qemu-system-x86
```

### Windows 10

- Install Python 3.
- Install QEMU for Windows.
- Ensure `qemu-system-i386.exe` is on `PATH`, or set `LINUX012_QEMU_BIN` to the full path of the QEMU binary.

Confirm the host dependency with the wrapper that matches the host:

```sh
./scripts/bootstrap-host.sh
```

```powershell
.\scripts\bootstrap-host.ps1
```

```bat
scripts\bootstrap-host.cmd
```

## Commands

### macOS and Ubuntu 22.04

Interactive boot:

```sh
./scripts/run.sh
```

Automated verification:

```sh
./scripts/verify.sh
```

### Windows 10 PowerShell

Interactive boot:

```powershell
.\scripts\run.ps1
```

Automated verification:

```powershell
.\scripts\verify.ps1
```

### Windows 10 Command Prompt

Interactive boot:

```bat
scripts\run.cmd
```

Automated verification:

```bat
scripts\verify.cmd
```

The verification command stores the latest artifacts under `out/verify/`, including:

- `screen.txt`: the final decoded VGA text screen
- `m.log`: monitor traffic
- `q.log`: QEMU output

The interactive launcher uses `out/run/` for the same kind of runtime artifacts.

## Repo Layout

- `scripts/bootstrap-host.sh`, `scripts/run.sh`, `scripts/verify.sh`: Unix wrappers for macOS and Ubuntu 22.04
- `scripts/bootstrap-host.ps1`, `scripts/run.ps1`, `scripts/verify.ps1`: PowerShell wrappers for Windows 10
- `scripts/bootstrap-host.cmd`, `scripts/run.cmd`, `scripts/verify.cmd`: Command Prompt wrappers that delegate to PowerShell
- `tools/qemu_driver.py`: runtime asset preparation, QEMU discovery, QEMU launch, VGA scraping, and key injection
- `vendor/src/linux-0.12.tar.gz`: Linux 0.12 source archive
- `vendor/images/bootimage-0.12-hd`: historical Linux 0.12 boot image for hard-disk-root boot
- `vendor/images/hdc-0.12.img`: Linux 0.12 hard disk image used as `hda`

## Notes

- The bundled boot image is shorter than 1.44MB. The driver pads it to a full floppy image in `out/run/boot.img` or `out/verify/boot.img` before launch.
- QEMU is started with `-snapshot`, so repeated runs do not mutate the vendored hard disk image.
- macOS and Ubuntu 22.04 use a local Unix socket for the QEMU monitor and `-display curses` for interactive sessions.
- Windows 10 uses a localhost TCP monitor endpoint because the Windows build does not offer Unix domain sockets. Interactive sessions rely on QEMU's default visible display.
- The guest prints `/root: ENOENT` before the shell prompt. This is expected for the bundled image and does not prevent the shell from working.

## Asset Provenance

- `vendor/src/linux-0.12.tar.gz` comes from the kernel.org historic archive.
- `vendor/images/bootimage-0.12-hd` comes from the OldLinux `linux-0.12-080324.zip` package.
- `vendor/images/hdc-0.12.img` comes from the `chenzhengchen200821109/linux-0.12` repository, which packages a Linux 0.12 hard disk image for QEMU.
