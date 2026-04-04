# Linux 0.12 On QEMU

This repository boots Linux 0.12 under `qemu-system-i386` on macOS arm64 and keeps all project artifacts inside the repo.

The working boot path is:

- one historical Linux 0.12 boot floppy image
- one Linux 0.12 hard disk image mounted as `hda`
- one runtime step that pads the short boot image into a standard 1.44MB floppy before each launch

`./scripts/run.sh` lands at the Linux shell prompt `[/]#`.
`./scripts/verify.sh` boots the same VM, runs `ls`, and exits non-zero if verification fails.

## Host Requirement

Install QEMU on the host:

```sh
brew install qemu
```

Confirm the host dependency:

```sh
./scripts/bootstrap-host.sh
```

## Commands

Interactive boot:

```sh
./scripts/run.sh
```

Automated verification:

```sh
./scripts/verify.sh
```

The verification command stores the latest artifacts under `out/verify/`, including:

- `screen.txt`: the final decoded VGA text screen
- `m.log`: monitor traffic
- `q.log`: QEMU output

The interactive launcher uses `out/run/` for the same kind of runtime artifacts.

## Repo Layout

- `scripts/bootstrap-host.sh`: checks for `qemu-system-i386`
- `scripts/run.sh`: boots to an interactive Linux 0.12 shell in QEMU curses mode
- `scripts/verify.sh`: boots the same VM, executes `ls`, and validates the returned prompt
- `tools/qemu_driver.py`: runtime asset preparation, QEMU launch, VGA scraping, and key injection
- `vendor/src/linux-0.12.tar.gz`: Linux 0.12 source archive
- `vendor/images/bootimage-0.12-hd`: historical Linux 0.12 boot image for hard-disk-root boot
- `vendor/images/hdc-0.12.img`: Linux 0.12 hard disk image used as `hda`

## Notes

- The bundled boot image is shorter than 1.44MB. The driver pads it to a full floppy image in `out/run/boot.img` or `out/verify/boot.img` before launch.
- QEMU is started with `-snapshot`, so repeated runs do not mutate the vendored hard disk image.
- The guest prints `/root: ENOENT` before the shell prompt. This is expected for the bundled image and does not prevent the shell from working.

## Asset Provenance

- `vendor/src/linux-0.12.tar.gz` comes from the kernel.org historic archive.
- `vendor/images/bootimage-0.12-hd` comes from the OldLinux `linux-0.12-080324.zip` package.
- `vendor/images/hdc-0.12.img` comes from the `chenzhengchen200821109/linux-0.12` repository, which packages a Linux 0.12 hard disk image for QEMU.
