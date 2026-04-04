# Changelog

[中文变更日志](./CHANGELOG.md)

## v1.0.0

Release date: 2026-04-04

This is the first formal release of the repository. At this point the project has moved from “proved on this machine” to “versioned, verifiable, and repeatable.”

### Major Capabilities

- build the Linux 0.12 boot image and system image from `vendor/src/linux-0.12.tar.gz`, repo-owned patches, manifests, and minimal userland source
- boot Linux 0.12 under QEMU, enter the shell, and run `ls` automatically
- provide the minimal userland binaries `/bin/sh` and `/bin/ls`
- provide shell built-ins for `cd`, `pwd`, `echo`, `cat`, `uname`, and `exit`
- support macOS arm64, Ubuntu 22.04, and Windows 10 as host platforms
- provide one-command terminal and visible-window launch scripts
- provide one-command rebuild-and-run launch scripts
- provide `verify` and `verify-userland` automated verification entrypoints

### Engineering Outcome

- the repository does not depend on third-party runtime images
- committed runtime snapshots are self-built, and the hard disk image is stored in compressed form as `images/hdc-0.12.img.xz`
- runtime launch automatically unpacks that snapshot into `out/repo-images/hdc-0.12.img`
- GitHub Actions automatically runs unit tests, source builds, and QEMU boot verification on `ubuntu-22.04`
- the CI workflow has been upgraded to official action versions compatible with Node 24

### Release Assets

- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`

### Known Boundaries

- the current goal is a minimal runnable Linux 0.12 system, not a full historical distribution
- real host validation has been completed primarily on the current macOS host and on the GitHub Ubuntu runner
- Ubuntu 22.04 and Windows 10 host entrypoints are implemented, but more real-machine regression coverage is still recommended
