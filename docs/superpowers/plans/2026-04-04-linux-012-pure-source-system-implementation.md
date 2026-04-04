# Linux 0.12 Pure-Source System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete all imported runtime images and replace them with a pure-source pipeline that builds both QEMU runtime images from source and repo-owned manifests, then boots Linux 0.12 to a shell and executes `ls`.

**Architecture:** Keep `tools/qemu_driver.py` as the low-level QEMU automation layer, but move the repo's runtime contract to `rebuild/out/images/`. Replace the historical rootfs import flow with a containerized build that compiles the patched Linux 0.12 kernel, compiles a tiny Linux 0.12-compatible userland, packs those binaries into Linux 0.12 `ZMAGIC` executables, assembles a fresh Minix v1 root filesystem from manifests, and verifies the result with the existing screen-scrape automation.

**Tech Stack:** Python 3 standard library, Docker, POSIX shell, GNU patch, bin86, GCC multilib, GNU binutils, guestfish, Minix filesystem tools, QEMU, Linux 0.12 kernel source

---

## File Map

- **Host entrypoints**
  - Modify: `rebuild/driver.py`
  - Modify: `tools/qemu_driver.py`
  - Modify: `scripts/bootstrap-host.sh`
  - Modify: `scripts/run.sh`
  - Modify: `scripts/verify.sh`
  - Modify: `scripts/bootstrap-host.ps1`
  - Modify: `scripts/run.ps1`
  - Modify: `scripts/verify.ps1`
  - Modify: `scripts/bootstrap-host.cmd`
  - Modify: `scripts/run.cmd`
  - Modify: `scripts/verify.cmd`

- **Pure-source build inputs**
  - Create: `rebuild/tools/aout_pack.py`
  - Create: `rebuild/userland/include/linux012.h`
  - Create: `rebuild/userland/linker.ld`
  - Create: `rebuild/userland/src/crt0.S`
  - Create: `rebuild/userland/src/lib.c`
  - Create: `rebuild/userland/src/sh.c`
  - Create: `rebuild/userland/src/ls.c`
  - Create: `rebuild/rootfs/manifest/directories.txt`
  - Create: `rebuild/rootfs/manifest/devices.tsv`
  - Create: `rebuild/rootfs/manifest/etc/rc`
  - Create: `rebuild/rootfs/manifest/usr/root/README`

- **Container build pipeline**
  - Modify: `rebuild/Dockerfile`
  - Modify: `rebuild/container/build_images.sh`
  - Delete: `rebuild/container/capture_rootfs.sh`
  - Modify: `rebuild/rootfs/layout.sfdisk`

- **Boundary cleanup**
  - Delete: `vendor/images/bootimage-0.12-hd`
  - Delete: `vendor/images/hdc-0.12.img`
  - Delete: `rebuild/rootfs/base.tar`
  - Modify: `.gitignore`

- **Tests**
  - Modify: `tests/test_assets.py`
  - Modify: `tests/test_layout.py`
  - Modify: `tests/test_scripts.py`
  - Modify: `tests/test_qemu_driver.py`
  - Modify: `tests/test_rebuild_driver.py`
  - Delete: `tests/test_rebuild_promote.py`
  - Create: `tests/test_pure_source_boundary.py`
  - Create: `tests/test_aout_pack.py`

- **Docs**
  - Modify: `README.md`
  - Modify: `README.en.md`
  - Modify: `rebuild/README.md`
  - Modify: `vendor/README.md`

### Task 1: Encode The Pure-Source Boundary

**Files:**
- Modify: `.gitignore`
- Modify: `tests/test_assets.py`
- Modify: `tests/test_layout.py`
- Create: `tests/test_pure_source_boundary.py`
- Create: `rebuild/rootfs/manifest/directories.txt`
- Create: `rebuild/rootfs/manifest/devices.tsv`
- Create: `rebuild/rootfs/manifest/etc/rc`
- Create: `rebuild/rootfs/manifest/usr/root/README`
- Delete: `vendor/images/bootimage-0.12-hd`
- Delete: `vendor/images/hdc-0.12.img`
- Delete: `rebuild/rootfs/base.tar`
- Delete: `rebuild/container/capture_rootfs.sh`

- [ ] **Step 1: Write the failing boundary tests**

```python
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class BoundaryTest(unittest.TestCase):
    def test_imported_runtime_images_are_absent(self) -> None:
        forbidden = [
            ROOT / "vendor" / "images",
            ROOT / "rebuild" / "rootfs" / "base.tar",
            ROOT / "rebuild" / "container" / "capture_rootfs.sh",
        ]

        for path in forbidden:
            self.assertFalse(path.exists(), path)

    def test_build_pipeline_does_not_reference_imported_runtime_assets(self) -> None:
        build_script = (ROOT / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertNotIn("vendor/images", build_script)
        self.assertNotIn("base.tar", build_script)
        self.assertNotIn("capture_rootfs", build_script)
```

```python
class AssetTest(unittest.TestCase):
    def test_vendor_assets_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "vendor" / "src" / "linux-0.12.tar.gz",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)

    def test_rebuild_rootfs_inputs_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "rebuild" / "rootfs" / "layout.sfdisk",
            ROOT / "rebuild" / "rootfs" / "manifest" / "directories.txt",
            ROOT / "rebuild" / "rootfs" / "manifest" / "devices.tsv",
            ROOT / "rebuild" / "rootfs" / "manifest" / "etc" / "rc",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)
```

```python
class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "rebuild" / "tools" / "aout_pack.py",
            ROOT / "rebuild" / "userland" / "include" / "linux012.h",
            ROOT / "rebuild" / "userland" / "src" / "sh.c",
            ROOT / "rebuild" / "userland" / "src" / "ls.c",
            ROOT / "rebuild" / "rootfs" / "manifest",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)
```

- [ ] **Step 2: Run the boundary tests to verify they fail**

Run: `python3 -m unittest -v tests.test_assets tests.test_layout tests.test_pure_source_boundary`

Expected: FAIL because `vendor/images/` and `rebuild/rootfs/base.tar` still exist, and the new pure-source inputs do not exist yet.

- [ ] **Step 3: Delete imported runtime assets and add the new manifest scaffold**

```text
.gitignore
rebuild/rootfs/manifest/directories.txt
rebuild/rootfs/manifest/devices.tsv
rebuild/rootfs/manifest/etc/rc
rebuild/rootfs/manifest/usr/root/README
```

```gitignore
.DS_Store
.worktrees/
/out/
rebuild/out/*
!rebuild/out/
!rebuild/out/.gitkeep
__pycache__/
*.pyc
```

```text
# rebuild/rootfs/manifest/directories.txt
bin
dev
etc
tmp
usr
usr/root
```

```text
# rebuild/rootfs/manifest/devices.tsv
c 600 4 1 dev/tty1
c 666 5 0 dev/tty
c 666 1 3 dev/null
```

```sh
# rebuild/rootfs/manifest/etc/rc
cd /usr/root
```

```text
# rebuild/rootfs/manifest/usr/root/README
This root filesystem was built from source inside rebuild/.
Try: ls
```

- [ ] **Step 4: Re-run the boundary tests**

Run: `python3 -m unittest -v tests.test_assets tests.test_layout tests.test_pure_source_boundary`

Expected: still FAIL, but only because `aout_pack.py` and the userland source files do not exist yet. The deleted imported-image paths should now be green.

- [ ] **Step 5: Commit the boundary cleanup**

```bash
git add .gitignore tests/test_assets.py tests/test_layout.py tests/test_pure_source_boundary.py rebuild/rootfs/manifest
git rm -r vendor/images
git rm rebuild/rootfs/base.tar rebuild/container/capture_rootfs.sh
git commit -m "chore: remove imported runtime images"
```

### Task 2: Rewire The Runtime Contract To `rebuild/out/images`

**Files:**
- Modify: `rebuild/driver.py`
- Modify: `tools/qemu_driver.py`
- Modify: `scripts/bootstrap-host.sh`
- Modify: `scripts/run.sh`
- Modify: `scripts/verify.sh`
- Modify: `scripts/bootstrap-host.ps1`
- Modify: `scripts/run.ps1`
- Modify: `scripts/verify.ps1`
- Modify: `scripts/bootstrap-host.cmd`
- Modify: `scripts/run.cmd`
- Modify: `scripts/verify.cmd`
- Modify: `tests/test_rebuild_driver.py`
- Modify: `tests/test_qemu_driver.py`
- Modify: `tests/test_scripts.py`
- Delete: `tests/test_rebuild_promote.py`

- [ ] **Step 1: Write the failing driver and wrapper tests**

```python
def test_parse_args_supports_bootstrap_build_run_verify(self) -> None:
    from rebuild.driver import parse_args

    for command in ("bootstrap-host", "build", "run", "verify"):
        self.assertEqual(command, parse_args([command]).command)

def test_verify_environment_points_runtime_at_rebuild_outputs(self) -> None:
    root = pathlib.Path("/tmp/linux-012")
    paths = BuildPaths.from_root(root)

    env = verify_environment(paths)

    self.assertEqual(str(paths.boot_image), env["LINUX012_BOOT_SOURCE_IMAGE"])
    self.assertEqual(str(paths.hard_disk_image), env["LINUX012_HARD_DISK_IMAGE"])
```

```python
def test_driver_paths_use_rebuild_outputs_by_default(self) -> None:
    root = pathlib.Path("/tmp/linux-012")
    platform = resolve_host_platform("linux")

    with patch.dict("os.environ", {}, clear=True):
        paths = DriverPaths.from_root(root, platform=platform)

    self.assertEqual(root / "rebuild" / "out" / "images" / "bootimage-0.12-hd", paths.boot_source_image)
    self.assertEqual(root / "rebuild" / "out" / "images" / "hdc-0.12.img", paths.hard_disk_image)
```

```python
def test_verify_script_calls_rebuild_driver(self) -> None:
    text = (ROOT / "scripts" / "verify.sh").read_text()
    self.assertIn("rebuild/driver.py", text)
    self.assertIn("verify", text)
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m unittest -v tests.test_rebuild_driver tests.test_qemu_driver tests.test_scripts`

Expected: FAIL because `rebuild/driver.py` still exposes `capture-rootfs` and `promote`, `tools/qemu_driver.py` still defaults to `vendor/images/`, and the wrapper scripts still call `tools/qemu_driver.py` directly.

- [ ] **Step 3: Update the host-side runtime contract**

```python
@dataclass(frozen=True)
class BuildPaths:
    root: Path
    rebuild_dir: Path
    out_dir: Path
    images_dir: Path
    logs_dir: Path
    work_dir: Path
    boot_image: Path
    hard_disk_image: Path

    @classmethod
    def from_root(cls, root: Path) -> "BuildPaths":
        rebuild_dir = root / "rebuild"
        out_dir = rebuild_dir / "out"
        images_dir = out_dir / "images"
        return cls(
            root=root,
            rebuild_dir=rebuild_dir,
            out_dir=out_dir,
            images_dir=images_dir,
            logs_dir=out_dir / "logs",
            work_dir=out_dir / "work",
            boot_image=images_dir / "bootimage-0.12-hd",
            hard_disk_image=images_dir / "hdc-0.12.img",
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["bootstrap-host", "build", "run", "verify"])
    return parser.parse_args(argv)


def ensure_built(paths: BuildPaths) -> int:
    if paths.boot_image.exists() and paths.hard_disk_image.exists():
        return 0
    return run_build(paths)


def run_bootstrap_host(paths: BuildPaths) -> int:
    docker_status = run_command(["docker", "--version"], cwd=paths.root)
    if docker_status != 0:
        return docker_status
    return run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), "bootstrap-host"],
        cwd=paths.root,
    )


def run_runtime(paths: BuildPaths, mode: str) -> int:
    if ensure_built(paths) != 0:
        return 1
    return run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), mode],
        cwd=paths.root,
        env=verify_environment(paths),
    )
```

```python
def resolve_runtime_image(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if override:
        return Path(override).expanduser()
    return default


@classmethod
def from_root(
    cls,
    root: Path,
    session: str = "verify",
    platform: HostPlatform | None = None,
) -> "DriverPaths":
    host = platform or resolve_host_platform()
    out_dir = root / "out" / session
    if host.monitor_kind == "unix":
        monitor_socket = out_dir / "m.sock"
        monitor_host = None
        monitor_port = None
        monitor_address = f"unix:{monitor_socket},server=on,wait=off"
    else:
        monitor_socket = None
        monitor_host = "127.0.0.1"
        monitor_port = pick_tcp_port(monitor_host)
        monitor_address = f"tcp:{monitor_host}:{monitor_port},server=on,wait=off"
    return cls(
        root=root,
        platform=host,
        boot_source_image=resolve_runtime_image(
            "LINUX012_BOOT_SOURCE_IMAGE",
            root / "rebuild" / "out" / "images" / "bootimage-0.12-hd",
        ),
        hard_disk_image=resolve_runtime_image(
            "LINUX012_HARD_DISK_IMAGE",
            root / "rebuild" / "out" / "images" / "hdc-0.12.img",
        ),
        out_dir=out_dir,
        boot_floppy_image=out_dir / "boot.img",
        monitor_address=monitor_address,
        monitor_socket=monitor_socket,
        monitor_host=monitor_host,
        monitor_port=monitor_port,
        pidfile=out_dir / "q.pid",
        vga_dump=out_dir / "v.bin",
        qemu_log=out_dir / "q.log",
        monitor_log=out_dir / "m.log",
        screen_text=out_dir / "screen.txt",
    )


def prepare_runtime_assets(paths: DriverPaths) -> None:
    missing = [path for path in (paths.boot_source_image, paths.hard_disk_image) if not path.exists()]
    if missing:
        missing_text = "\n".join(f"  {path}" for path in missing)
        raise FileNotFoundError(
            "Missing source-built runtime images:\n"
            f"{missing_text}\n"
            "Run `python3 rebuild/driver.py build` first."
        )
    prepare_output_dir(paths)
    ensure_boot_floppy_image(source_image=paths.boot_source_image, target_image=paths.boot_floppy_image)
```

```sh
# scripts/verify.sh
#!/bin/sh
set -eu

exec python3 "$(dirname "$0")/../rebuild/driver.py" verify
```

```powershell
# scripts/verify.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
python (Join-Path $root "rebuild/driver.py") verify
```

- [ ] **Step 4: Re-run the targeted tests**

Run: `python3 -m unittest -v tests.test_rebuild_driver tests.test_qemu_driver tests.test_scripts`

Expected: PASS

- [ ] **Step 5: Commit the new runtime contract**

```bash
git add rebuild/driver.py tools/qemu_driver.py scripts tests/test_rebuild_driver.py tests/test_qemu_driver.py tests/test_scripts.py
git rm tests/test_rebuild_promote.py
git commit -m "feat: move runtime contract to source-built images"
```

### Task 3: Add A Minimal Linux 0.12 Userland And `ZMAGIC` Packer

**Files:**
- Create: `rebuild/tools/aout_pack.py`
- Create: `rebuild/userland/include/linux012.h`
- Create: `rebuild/userland/linker.ld`
- Create: `rebuild/userland/src/crt0.S`
- Create: `rebuild/userland/src/lib.c`
- Create: `rebuild/userland/src/sh.c`
- Create: `rebuild/userland/src/ls.c`
- Create: `tests/test_aout_pack.py`
- Modify: `tests/test_layout.py`

- [ ] **Step 1: Write the failing packer and source-layout tests**

```python
import pathlib
import struct
import tempfile
import unittest

from rebuild.tools.aout_pack import build_exec_header, write_zmagic_image


class AoutPackTest(unittest.TestCase):
    def test_build_exec_header_emits_linux_012_zmagic(self) -> None:
        header = build_exec_header(text_size=64, data_size=16, bss_size=8, entry=0)
        fields = struct.unpack("<8I", header)

        self.assertEqual(0o413, fields[0])
        self.assertEqual(64, fields[1])
        self.assertEqual(16, fields[2])
        self.assertEqual(8, fields[3])
        self.assertEqual(0, fields[5])

    def test_write_zmagic_image_places_text_at_offset_1024(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            output = pathlib.Path(tempdir) / "ls"
            write_zmagic_image(output, text=b"TEXT", data=b"DATA", bss_size=12, entry=0)
            blob = output.read_bytes()

        self.assertEqual(1024, blob.find(b"TEXT"))
        self.assertEqual(b"DATA", blob[1028:1032])
```

```python
class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "rebuild" / "tools" / "aout_pack.py",
            ROOT / "rebuild" / "userland" / "include" / "linux012.h",
            ROOT / "rebuild" / "userland" / "src" / "crt0.S",
            ROOT / "rebuild" / "userland" / "src" / "lib.c",
            ROOT / "rebuild" / "userland" / "src" / "sh.c",
            ROOT / "rebuild" / "userland" / "src" / "ls.c",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m unittest -v tests.test_aout_pack tests.test_layout`

Expected: FAIL because the packer module and userland source tree do not exist yet.

- [ ] **Step 3: Implement the minimal userland toolchain inputs**

```python
# rebuild/tools/aout_pack.py
from __future__ import annotations

import argparse
import pathlib
import struct
import subprocess
import tempfile


ZMAGIC = 0o413
TEXT_OFFSET = 1024


def build_exec_header(*, text_size: int, data_size: int, bss_size: int, entry: int) -> bytes:
    return struct.pack("<8I", ZMAGIC, text_size, data_size, bss_size, 0, entry, 0, 0)


def write_zmagic_image(output: pathlib.Path, *, text: bytes, data: bytes, bss_size: int, entry: int) -> None:
    header = build_exec_header(text_size=len(text), data_size=len(data), bss_size=bss_size, entry=entry)
    padding = b"\x00" * (TEXT_OFFSET - len(header))
    output.write_bytes(header + padding + text + data)


def parse_nm_output(lines: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in lines.splitlines():
        parts = line.split()
        if len(parts) == 3:
            result[parts[2]] = int(parts[0], 16)
    return result


def pack_elf_to_zmagic(elf_path: pathlib.Path, output: pathlib.Path) -> None:
    symbols = parse_nm_output(
        subprocess.run(["nm", "-n", str(elf_path)], check=True, text=True, capture_output=True).stdout
    )
    with tempfile.TemporaryDirectory() as tempdir:
        flat_path = pathlib.Path(tempdir) / "flat.bin"
        subprocess.run(["objcopy", "-O", "binary", str(elf_path), str(flat_path)], check=True)
        blob = flat_path.read_bytes()
    text_end = symbols["__data_start"]
    data_end = symbols["__bss_start"]
    bss_end = symbols["__bss_end"]
    write_zmagic_image(
        output,
        text=blob[:text_end],
        data=blob[text_end:data_end],
        bss_size=bss_end - data_end,
        entry=symbols["_start"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf_path", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args(argv)
    pack_elf_to_zmagic(args.elf_path, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```c
/* rebuild/userland/include/linux012.h */
#ifndef REBUILD_USERLAND_LINUX012_H
#define REBUILD_USERLAND_LINUX012_H

#define NULL ((void *)0)
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2

struct linux012_dirent {
    unsigned short inode;
    char name[14];
};

int open(const char *path, int flags, int mode);
int close(int fd);
int read(int fd, void *buffer, unsigned int count);
int write(int fd, const void *buffer, unsigned int count);
int fork(void);
int execve(const char *path, char **argv, char **envp);
int waitpid(int pid, int *status, int options);
int chdir(const char *path);
void _exit(int status);

int strcmp(const char *left, const char *right);
int strncmp(const char *left, const char *right, unsigned int count);
unsigned int strlen(const char *text);
char *strcpy(char *dest, const char *src);
void write_str(int fd, const char *text);
int read_line(int fd, char *buffer, unsigned int capacity);

#endif
```

```asm
; rebuild/userland/src/crt0.S
    .globl _start
_start:
    popl %eax
    movl %esp, %ebx
    leal 4(%esp,%eax,4), %ecx
    pushl %ecx
    pushl %ebx
    pushl %eax
    call main
    movl %eax, %ebx
    movl $1, %eax
    int $0x80
```

```c
/* rebuild/userland/src/lib.c */
#include "linux012.h"

static inline int syscall3(int number, int arg1, int arg2, int arg3) {
    int result;
    __asm__ volatile ("int $0x80" : "=a"(result) : "0"(number), "b"(arg1), "c"(arg2), "d"(arg3));
    return result;
}

int open(const char *path, int flags, int mode) { return syscall3(5, (int)path, flags, mode); }
int close(int fd) { return syscall3(6, fd, 0, 0); }
int read(int fd, void *buffer, unsigned int count) { return syscall3(3, fd, (int)buffer, count); }
int write(int fd, const void *buffer, unsigned int count) { return syscall3(4, fd, (int)buffer, count); }
int fork(void) { return syscall3(2, 0, 0, 0); }
int execve(const char *path, char **argv, char **envp) { return syscall3(11, (int)path, (int)argv, (int)envp); }
int waitpid(int pid, int *status, int options) { return syscall3(7, pid, (int)status, options); }
int chdir(const char *path) { return syscall3(12, (int)path, 0, 0); }
void _exit(int status) { syscall3(1, status, 0, 0); for (;;) {} }

unsigned int strlen(const char *text) { unsigned int size = 0; while (text[size]) { size++; } return size; }
int strcmp(const char *left, const char *right) { while (*left && *left == *right) { left++; right++; } return (unsigned char)*left - (unsigned char)*right; }
int strncmp(const char *left, const char *right, unsigned int count) { while (count && *left && *left == *right) { left++; right++; count--; } return count ? (unsigned char)*left - (unsigned char)*right : 0; }
char *strcpy(char *dest, const char *src) { char *out = dest; while ((*dest++ = *src++)) {} return out; }
void write_str(int fd, const char *text) { write(fd, text, strlen(text)); }
int read_line(int fd, char *buffer, unsigned int capacity) {
    unsigned int used = 0;
    char ch = 0;
    while (used + 1 < capacity) {
        int rc = read(fd, &ch, 1);
        if (rc <= 0) { break; }
        if (ch == '\r') { continue; }
        if (ch == '\n') { break; }
        buffer[used++] = ch;
    }
    buffer[used] = '\0';
    return (int)used;
}
```

```ld
/* rebuild/userland/linker.ld */
ENTRY(_start)

SECTIONS
{
    . = 0;
    .text : { *(.text*) *(.rodata*) }
    . = ALIGN(4);
    __data_start = .;
    .data : { *(.data*) }
    . = ALIGN(4);
    __bss_start = .;
    .bss : { *(.bss*) *(COMMON) }
    __bss_end = .;
}
```

```c
/* rebuild/userland/src/sh.c */
#include "linux012.h"

static char line[128];
static char cwd[64] = "/";

static void print_prompt(void) {
    write_str(1, "[");
    write_str(1, cwd);
    write_str(1, "]# ");
}

static int run_ls(char **envp) {
    int status = 0;
    char *argv[] = { "/bin/ls", NULL };
    int pid = fork();
    if (pid == 0) {
        execve("/bin/ls", argv, envp);
        _exit(127);
    }
    waitpid(pid, &status, 0);
    return status;
}

int main(int argc, char **argv, char **envp) {
    int interactive = argc > 0 && argv[0] && argv[0][0] == '-';
    if (chdir("/usr/root") == 0) {
        strcpy(cwd, "/usr/root");
    }
    while (1) {
        if (interactive) {
            print_prompt();
        }
        if (read_line(0, line, sizeof(line)) <= 0) {
            return 0;
        }
        if (strcmp(line, "ls") == 0) {
            run_ls(envp);
            continue;
        }
        if (strncmp(line, "cd ", 3) == 0) {
            if (chdir(line + 3) == 0) {
                strcpy(cwd, line + 3);
            } else {
                write_str(2, "cd: no such directory\n");
            }
            continue;
        }
        if (strcmp(line, "exit") == 0) {
            return 0;
        }
        write_str(2, "unsupported command\n");
    }
}
```

```c
/* rebuild/userland/src/ls.c */
#include "linux012.h"

static struct linux012_dirent entries[64];

int main(void) {
    int fd = open(".", O_RDONLY, 0);
    int size;
    int i;

    if (fd < 0) {
        write_str(2, "ls: cannot open .\n");
        return 1;
    }
    size = read(fd, entries, sizeof(entries));
    close(fd);
    if (size < 0) {
        write_str(2, "ls: cannot read .\n");
        return 1;
    }
    for (i = 0; i < size / sizeof(struct linux012_dirent); ++i) {
        if (!entries[i].inode || !entries[i].name[0]) {
            continue;
        }
        write_str(1, entries[i].name);
        write_str(1, "\n");
    }
    return 0;
}
```

- [ ] **Step 4: Re-run the targeted tests**

Run: `python3 -m unittest -v tests.test_aout_pack tests.test_layout`

Expected: PASS

- [ ] **Step 5: Commit the userland inputs**

```bash
git add rebuild/tools/aout_pack.py rebuild/userland tests/test_aout_pack.py tests/test_layout.py
git commit -m "feat: add minimal Linux 0.12 userland sources"
```

### Task 4: Build Kernel, Userland, And Root Filesystem From Scratch

**Files:**
- Modify: `rebuild/Dockerfile`
- Modify: `rebuild/container/build_images.sh`
- Modify: `rebuild/rootfs/layout.sfdisk`
- Modify: `tests/test_rebuild_driver.py`
- Modify: `tests/test_pure_source_boundary.py`

- [ ] **Step 1: Write the failing build-pipeline tests**

```python
def test_build_script_references_source_tarball_userland_and_manifest(self) -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    text = (root / "rebuild" / "container" / "build_images.sh").read_text()

    self.assertIn("vendor/src/linux-0.12.tar.gz", text)
    self.assertIn("rebuild/userland", text)
    self.assertIn("rebuild/tools/aout_pack.py", text)
    self.assertIn("rebuild/rootfs/manifest/directories.txt", text)
    self.assertIn("rebuild/rootfs/manifest/devices.tsv", text)
    self.assertNotIn("vendor/images", text)
    self.assertNotIn("base.tar", text)

def test_dockerfile_installs_multilib_userland_build_dependencies(self) -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    text = (root / "rebuild" / "Dockerfile").read_text()

    self.assertIn("gcc-multilib", text)
    self.assertIn("libc6-dev-i386", text)
    self.assertIn("libguestfs-tools", text)
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m unittest -v tests.test_rebuild_driver tests.test_pure_source_boundary`

Expected: FAIL because `build_images.sh` still restores a rootfs from `base.tar`, and the Docker image does not yet install the userland build dependencies.

- [ ] **Step 3: Replace the container build pipeline with source-only assembly**

```dockerfile
FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bc \
    bin86 \
    bison \
    build-essential \
    flex \
    gcc-multilib \
    libc6-dev-i386 \
    guestfish \
    libguestfs-tools \
    linux-image-kvm \
    make \
    patch \
    python3 \
    qemu-utils \
    util-linux \
    && rm -rf /var/lib/apt/lists/*
```

```sh
#!/bin/sh
set -eu

ROOT=/workspace
CONTAINER_WORK_ROOT=/tmp/linux-012-rebuild-work
SOURCE_ROOT="$CONTAINER_WORK_ROOT/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
USERLAND_ROOT="$ROOT/rebuild/userland"
MANIFEST_ROOT="$ROOT/rebuild/rootfs/manifest"
IMAGE_DIR="$ROOT/rebuild/out/images"
LOG_DIR="$ROOT/rebuild/out/logs"
WORK_DIR="$ROOT/rebuild/out/work"
STAGING_DIR="$WORK_DIR/rootfs"
USERLAND_BUILD="$WORK_DIR/userland"
DISK_IMAGE="$IMAGE_DIR/hdc-0.12.img"
ROOT_PARTITION_IMAGE="$WORK_DIR/rootfs.img"
ROOTFS_TAR="$WORK_DIR/rootfs.tar"

rm -rf "$CONTAINER_WORK_ROOT" "$STAGING_DIR" "$USERLAND_BUILD"
mkdir -p "$CONTAINER_WORK_ROOT" "$IMAGE_DIR" "$LOG_DIR" "$WORK_DIR" "$STAGING_DIR" "$USERLAND_BUILD"

tar -xzf "$ROOT/vendor/src/linux-0.12.tar.gz" -C "$CONTAINER_WORK_ROOT"
for patch in "$PATCH_DIR"/*.patch; do
    [ -s "$patch" ] || continue
    patch --batch -p1 -d "$CONTAINER_WORK_ROOT" < "$patch" >>"$LOG_DIR/build.log" 2>&1
done

chmod +x "$SOURCE_ROOT/tools/build.sh"
make -C "$SOURCE_ROOT" Image >>"$LOG_DIR/build.log" 2>&1
cp "$SOURCE_ROOT/Image" "$IMAGE_DIR/bootimage-0.12-hd"

while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    mkdir -p "$STAGING_DIR/$dir"
done < "$MANIFEST_ROOT/directories.txt"

gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/lib.c" -o "$USERLAND_BUILD/lib.o"
gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/sh.c" -o "$USERLAND_BUILD/sh.o"
gcc -m32 -ffreestanding -fno-pie -fno-pic -fno-stack-protector -nostdlib -nostartfiles -nodefaultlibs \
    -I"$USERLAND_ROOT/include" -c "$USERLAND_ROOT/src/ls.c" -o "$USERLAND_BUILD/ls.o"
gcc -m32 -c "$USERLAND_ROOT/src/crt0.S" -o "$USERLAND_BUILD/crt0.o"

ld -m elf_i386 -T "$USERLAND_ROOT/linker.ld" -o "$USERLAND_BUILD/sh.elf" \
    "$USERLAND_BUILD/crt0.o" "$USERLAND_BUILD/lib.o" "$USERLAND_BUILD/sh.o"
ld -m elf_i386 -T "$USERLAND_ROOT/linker.ld" -o "$USERLAND_BUILD/ls.elf" \
    "$USERLAND_BUILD/crt0.o" "$USERLAND_BUILD/lib.o" "$USERLAND_BUILD/ls.o"

python3 "$ROOT/rebuild/tools/aout_pack.py" "$USERLAND_BUILD/sh.elf" "$STAGING_DIR/bin/sh"
python3 "$ROOT/rebuild/tools/aout_pack.py" "$USERLAND_BUILD/ls.elf" "$STAGING_DIR/bin/ls"

cp "$MANIFEST_ROOT/etc/rc" "$STAGING_DIR/etc/rc"
cp "$MANIFEST_ROOT/usr/root/README" "$STAGING_DIR/usr/root/README"

while IFS=' ' read -r kind mode major minor relative_path; do
    [ -n "$relative_path" ] || continue
    mknod "$STAGING_DIR/$relative_path" "$kind" "$major" "$minor"
    chmod "$mode" "$STAGING_DIR/$relative_path"
done < "$MANIFEST_ROOT/devices.tsv"

tar -C "$STAGING_DIR" -cpf "$ROOTFS_TAR" .
truncate -s 62447616 "$DISK_IMAGE"
sfdisk "$DISK_IMAGE" < "$ROOT/rebuild/rootfs/layout.sfdisk" >>"$LOG_DIR/build.log" 2>&1
truncate -s "$((120959 * 512))" "$ROOT_PARTITION_IMAGE"
mkfs.minix -1 -n14 "$ROOT_PARTITION_IMAGE" >>"$LOG_DIR/build.log" 2>&1

guestfish --format=raw -a "$ROOT_PARTITION_IMAGE" <<EOF >>"$LOG_DIR/build.log" 2>&1
run
mount /dev/sda /
tar-in "$ROOTFS_TAR" /
umount /
EOF

dd if="$ROOT_PARTITION_IMAGE" of="$DISK_IMAGE" bs=512 seek=1 conv=notrunc >>"$LOG_DIR/build.log" 2>&1
```

- [ ] **Step 4: Re-run the targeted tests**

Run: `python3 -m unittest -v tests.test_rebuild_driver tests.test_pure_source_boundary`

Expected: PASS

- [ ] **Step 5: Commit the new source-only build pipeline**

```bash
git add rebuild/Dockerfile rebuild/container/build_images.sh rebuild/rootfs/layout.sfdisk tests/test_rebuild_driver.py tests/test_pure_source_boundary.py
git commit -m "feat: build Linux 0.12 runtime images from source"
```

### Task 5: Update Docs And Prove The End-To-End Flow

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `rebuild/README.md`
- Modify: `vendor/README.md`

- [ ] **Step 1: Update the docs to describe the source-only contract**

```text
## 从源码构建并验证

这个仓库不再提交任何运行时镜像。默认运行时镜像位于 `rebuild/out/images/`，由 `rebuild/driver.py` 在本地构建。

常用命令：

python3 rebuild/driver.py bootstrap-host
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
./scripts/run.sh

`python3 rebuild/driver.py verify` 会在镜像不存在时自动先执行构建，然后启动 QEMU，进入 shell，并自动执行 `ls`。
```

```text
## Vendor Assets

This directory only stores source archives now.

- `src/linux-0.12.tar.gz`
  - Source: kernel.org historical archive

No runtime disk images are committed to the repository.
```

- [ ] **Step 2: Run the full automated test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS

- [ ] **Step 3: Prove the source-only runtime works from a clean generated-output state**

Run:

```bash
rm -rf rebuild/out/images rebuild/out/logs rebuild/out/work out/run out/verify
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
./scripts/verify.sh
```

Expected:

- `python3 rebuild/driver.py build` exits `0`
- `python3 rebuild/driver.py verify` prints `Linux 0.12 boot verified and \`ls\` succeeded.`
- `./scripts/verify.sh` also passes using the same source-built images
- `out/verify/screen.txt` ends with the Linux 0.12 shell prompt and includes `ls` output

- [ ] **Step 4: Manually sanity-check interactive boot**

Run: `./scripts/run.sh`

Expected: QEMU boots into Linux 0.12, reaches `[/usr/root]#`, and accepts `ls`.

- [ ] **Step 5: Commit the docs and final verification**

```bash
git add README.md README.en.md rebuild/README.md vendor/README.md
git commit -m "docs: document pure-source Linux 0.12 workflow"
```
