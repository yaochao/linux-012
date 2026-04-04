# Linux 0.12 Source Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repo-owned `rebuild/` pipeline that ports Linux 0.12 source to the current QEMU workflow, regenerates `bootimage-0.12-hd` and `hdc-0.12.img`, and proves the rebuilt images can replace the downloaded runtime images.

**Architecture:** Keep the current runtime path centered on `tools/qemu_driver.py`, but add image override support so rebuilt artifacts can be verified before promotion. Put all source-build responsibilities under `rebuild/`: a host-side Python driver, a Docker-based Linux amd64 build environment, a Linux 0.12 patch series, a canonical rootfs source tarball, and container-side scripts for image generation.

**Tech Stack:** Python 3 standard library, Docker, POSIX shell, GNU patch, bin86, GNU binutils, GCC, Linux filesystem and partition tools, existing QEMU runtime driver

---

### Task 1: Scaffold The Rebuild Workspace

**Files:**
- Modify: `.gitignore`
- Modify: `tests/test_layout.py`
- Create: `rebuild/README.md`
- Create: `rebuild/Dockerfile`
- Create: `rebuild/driver.py`
- Create: `rebuild/container/build_images.sh`
- Create: `rebuild/container/capture_rootfs.sh`
- Create: `rebuild/patches/linux-0.12/.gitkeep`
- Create: `rebuild/rootfs/.gitkeep`
- Create: `rebuild/out/.gitkeep`

- [ ] **Step 1: Write the failing layout test**

```python
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "rebuild" / "README.md",
            ROOT / "rebuild" / "Dockerfile",
            ROOT / "rebuild" / "driver.py",
            ROOT / "rebuild" / "container" / "build_images.sh",
            ROOT / "rebuild" / "container" / "capture_rootfs.sh",
            ROOT / "rebuild" / "patches" / "linux-0.12",
            ROOT / "rebuild" / "rootfs",
            ROOT / "rebuild" / "out",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_layout`
Expected: FAIL because the `rebuild/` files and directories do not exist yet

- [ ] **Step 3: Create the minimal scaffold and ignore generated output**

```text
.gitignore                    # add rebuild/out/* and !rebuild/out/.gitkeep
rebuild/README.md
rebuild/Dockerfile
rebuild/driver.py
rebuild/container/build_images.sh
rebuild/container/capture_rootfs.sh
rebuild/patches/linux-0.12/.gitkeep
rebuild/rootfs/.gitkeep
rebuild/out/.gitkeep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_layout`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .gitignore tests/test_layout.py rebuild
git commit -m "chore: scaffold Linux 0.12 rebuild workspace"
```

### Task 2: Add Runtime Image Override Support

**Files:**
- Modify: `tools/qemu_driver.py`
- Modify: `tests/test_qemu_driver.py`

- [ ] **Step 1: Write the failing driver tests for image overrides**

```python
def test_driver_paths_use_override_images_from_environment(self) -> None:
    root = pathlib.Path("/tmp/linux-012")
    platform = resolve_host_platform("linux")
    env = {
        "LINUX012_BOOT_SOURCE_IMAGE": "/tmp/custom/bootimage-0.12-hd",
        "LINUX012_HARD_DISK_IMAGE": "/tmp/custom/hdc-0.12.img",
    }

    with patch.dict("os.environ", env, clear=False):
        paths = DriverPaths.from_root(root, platform=platform)

    self.assertEqual(pathlib.Path(env["LINUX012_BOOT_SOURCE_IMAGE"]), paths.boot_source_image)
    self.assertEqual(pathlib.Path(env["LINUX012_HARD_DISK_IMAGE"]), paths.hard_disk_image)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_qemu_driver`
Expected: FAIL because `DriverPaths.from_root()` still hardcodes the vendored images

- [ ] **Step 3: Implement the minimal override resolution**

```python
def resolve_runtime_image(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


@classmethod
def from_root(cls, root: Path, session: str = "verify", platform: HostPlatform | None = None) -> "DriverPaths":
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
    boot_source_image = resolve_runtime_image(
        "LINUX012_BOOT_SOURCE_IMAGE",
        root / "vendor" / "images" / "bootimage-0.12-hd",
    )
    hard_disk_image = resolve_runtime_image(
        "LINUX012_HARD_DISK_IMAGE",
        root / "vendor" / "images" / "hdc-0.12.img",
    )
    return cls(
        root=root,
        platform=host,
        boot_source_image=boot_source_image,
        hard_disk_image=hard_disk_image,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_qemu_driver`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/qemu_driver.py tests/test_qemu_driver.py
git commit -m "feat: add runtime image overrides"
```

### Task 3: Build The Host-Side Rebuild Driver

**Files:**
- Create: `tests/test_rebuild_driver.py`
- Modify: `rebuild/driver.py`

- [ ] **Step 1: Write the failing rebuild driver tests**

```python
import pathlib
import unittest

from rebuild.driver import BuildPaths, docker_build_command, docker_run_command


class RebuildDriverTest(unittest.TestCase):
    def test_build_paths_use_rebuild_directory(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        self.assertEqual(root / "rebuild", paths.rebuild_dir)
        self.assertEqual(root / "rebuild" / "out" / "images" / "bootimage-0.12-hd", paths.boot_image)
        self.assertEqual(root / "rebuild" / "out" / "images" / "hdc-0.12.img", paths.hard_disk_image)

    def test_docker_run_command_uses_linux_amd64_and_privileged_mode(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        command = docker_run_command(paths, script="rebuild/container/build_images.sh")

        self.assertIn("--platform", command)
        self.assertIn("linux/amd64", command)
        self.assertIn("--privileged", command)
        self.assertIn(str(root), command)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_rebuild_driver`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors

- [ ] **Step 3: Implement the minimal host-side driver structure**

```python
from dataclasses import dataclass
from pathlib import Path


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


def docker_build_command(paths: BuildPaths) -> list[str]:
    return [
        "docker",
        "build",
        "--platform",
        "linux/amd64",
        "-t",
        "linux-012-rebuild",
        "-f",
        str(paths.rebuild_dir / "Dockerfile"),
        str(paths.root),
    ]


def docker_run_command(paths: BuildPaths, script: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--privileged",
        "-v",
        f"{paths.root}:/workspace",
        "-w",
        "/workspace",
        "linux-012-rebuild",
        "bash",
        script,
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_rebuild_driver`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add rebuild/driver.py tests/test_rebuild_driver.py
git commit -m "feat: add rebuild host driver"
```

### Task 4: Add The Container Contract And Kernel Source Patch Flow

**Files:**
- Modify: `rebuild/Dockerfile`
- Modify: `rebuild/container/build_images.sh`
- Create: `rebuild/patches/linux-0.12/0001-modernize-toolchain.patch`
- Create: `rebuild/patches/linux-0.12/0002-qemu-root-device.patch`
- Modify: `rebuild/README.md`
- Modify: `tests/test_rebuild_driver.py`

- [ ] **Step 1: Write the failing dry-run test for container-side build inputs**

```python
def test_build_script_references_source_tarball_and_patch_directory(self) -> None:
    text = (ROOT / "rebuild" / "container" / "build_images.sh").read_text()

    self.assertIn("vendor/src/linux-0.12.tar.gz", text)
    self.assertIn("rebuild/patches/linux-0.12", text)
    self.assertIn("bootimage-0.12-hd", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_rebuild_driver`
Expected: FAIL because the build script is still empty or placeholder-only

- [ ] **Step 3: Add the Docker toolchain and patch application flow**

```dockerfile
FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bin86 \
    build-essential \
    bsdmainutils \
    dosfstools \
    fdisk \
    file \
    gcc-multilib \
    make \
    minix \
    patch \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
```

```sh
#!/bin/sh
set -eu

ROOT=/workspace
WORK="$ROOT/rebuild/out/work/linux-0.12"
PATCH_DIR="$ROOT/rebuild/patches/linux-0.12"
IMAGE_DIR="$ROOT/rebuild/out/images"

rm -rf "$WORK"
mkdir -p "$WORK" "$IMAGE_DIR" "$ROOT/rebuild/out/logs"
tar -xzf "$ROOT/vendor/src/linux-0.12.tar.gz" -C "$ROOT/rebuild/out/work"

for patch in "$PATCH_DIR"/*.patch; do
    [ -f "$patch" ] || continue
    patch -d "$WORK" -p1 < "$patch"
done

make -C "$WORK" ROOT_DEV=/dev/hd1 Image
cp "$WORK/Image" "$IMAGE_DIR/bootimage-0.12-hd"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_rebuild_driver`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add rebuild/Dockerfile rebuild/container/build_images.sh rebuild/patches rebuild/README.md tests/test_rebuild_driver.py
git commit -m "feat: add Linux 0.12 source build container"
```

### Task 5: Capture A Canonical Rootfs And Rebuild The Hard Disk Image

**Files:**
- Modify: `rebuild/container/capture_rootfs.sh`
- Modify: `rebuild/container/build_images.sh`
- Create: `rebuild/rootfs/layout.sfdisk`
- Create: `rebuild/rootfs/base.tar`
- Create: `rebuild/rootfs/overlay/.gitkeep`
- Modify: `tests/test_assets.py`

- [ ] **Step 1: Write the failing asset test for the canonical rootfs input**

```python
def test_rebuild_rootfs_assets_exist_and_are_non_empty(self) -> None:
    expected = [
        ROOT / "rebuild" / "rootfs" / "base.tar",
        ROOT / "rebuild" / "rootfs" / "layout.sfdisk",
    ]

    for path in expected:
        self.assertTrue(path.exists(), path)
        self.assertGreater(path.stat().st_size, 0, path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_assets`
Expected: FAIL because the rootfs source inputs do not exist yet

- [ ] **Step 3: Implement capture and disk assembly**

```sh
#!/bin/sh
set -eu

ROOT=/workspace
TMP="$ROOT/rebuild/out/work/rootfs-capture"
IMG="$ROOT/vendor/images/hdc-0.12.img"
PART="$TMP/root-partition.img"

rm -rf "$TMP"
mkdir -p "$TMP"
dd if="$IMG" of="$PART" bs=512 skip=1 count=120959 status=none
mkdir -p "$TMP/mnt"
mount -t minix -o loop "$PART" "$TMP/mnt"
tar -C "$TMP/mnt" -cpf "$ROOT/rebuild/rootfs/base.tar" .
umount "$TMP/mnt"
```

```sh
cat > "$ROOT/rebuild/rootfs/layout.sfdisk" <<'EOF'
label: dos
unit: sectors

start=1, size=120959, type=81, bootable
EOF

truncate -s 62447616 "$IMAGE_DIR/hdc-0.12.img"
sfdisk "$IMAGE_DIR/hdc-0.12.img" < "$ROOT/rebuild/rootfs/layout.sfdisk"
dd if=/dev/zero of="$ROOT/rebuild/out/work/root-partition.img" bs=512 count=120959 status=none
mkfs.minix "$ROOT/rebuild/out/work/root-partition.img"
mkdir -p "$ROOT/rebuild/out/work/mnt"
mount -t minix -o loop "$ROOT/rebuild/out/work/root-partition.img" "$ROOT/rebuild/out/work/mnt"
tar -C "$ROOT/rebuild/out/work/mnt" -xpf "$ROOT/rebuild/rootfs/base.tar"
cp -a "$ROOT/rebuild/rootfs/overlay/." "$ROOT/rebuild/out/work/mnt/" 2>/dev/null || true
umount "$ROOT/rebuild/out/work/mnt"
dd if="$ROOT/rebuild/out/work/root-partition.img" of="$IMAGE_DIR/hdc-0.12.img" bs=512 seek=1 conv=notrunc status=none
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_assets`
Expected: PASS after `rebuild/rootfs/base.tar` and `rebuild/rootfs/layout.sfdisk` exist

- [ ] **Step 5: Commit**

```bash
git add rebuild/rootfs rebuild/container tests/test_assets.py
git commit -m "feat: add rebuild rootfs source and disk image assembly"
```

### Task 6: Verify Rebuilt Images And Promote Them Into The Runtime

**Files:**
- Modify: `rebuild/driver.py`
- Modify: `rebuild/README.md`
- Create: `tests/test_rebuild_promote.py`

- [ ] **Step 1: Write the failing verification and promote tests**

```python
import pathlib
import unittest

from rebuild.driver import BuildPaths, verify_environment, promotion_pairs


class RebuildPromoteTest(unittest.TestCase):
    def test_verify_environment_points_runtime_at_rebuild_outputs(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        env = verify_environment(paths)

        self.assertEqual(str(paths.boot_image), env["LINUX012_BOOT_SOURCE_IMAGE"])
        self.assertEqual(str(paths.hard_disk_image), env["LINUX012_HARD_DISK_IMAGE"])

    def test_promotion_pairs_copy_rebuilt_images_into_vendor_images(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        pairs = promotion_pairs(paths)

        self.assertEqual(paths.boot_image, pairs[0][0])
        self.assertEqual(root / "vendor" / "images" / "bootimage-0.12-hd", pairs[0][1])
        self.assertEqual(paths.hard_disk_image, pairs[1][0])
        self.assertEqual(root / "vendor" / "images" / "hdc-0.12.img", pairs[1][1])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_rebuild_promote`
Expected: FAIL because the rebuild driver does not yet implement verification and promotion helpers

- [ ] **Step 3: Implement `verify` and `promote` commands**

```python
def verify_environment(paths: BuildPaths) -> dict[str, str]:
    env = os.environ.copy()
    env["LINUX012_BOOT_SOURCE_IMAGE"] = str(paths.boot_image)
    env["LINUX012_HARD_DISK_IMAGE"] = str(paths.hard_disk_image)
    return env


def promotion_pairs(paths: BuildPaths) -> list[tuple[Path, Path]]:
    return [
        (paths.boot_image, paths.root / "vendor" / "images" / "bootimage-0.12-hd"),
        (paths.hard_disk_image, paths.root / "vendor" / "images" / "hdc-0.12.img"),
    ]


def run_verify(paths: BuildPaths) -> int:
    return subprocess.run(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), "verify"],
        cwd=paths.root,
        env=verify_environment(paths),
        check=False,
    ).returncode


def run_promote(paths: BuildPaths) -> int:
    if run_verify(paths) != 0:
        return 1
    for source, target in promotion_pairs(paths):
        shutil.copy2(source, target)
    return subprocess.run([str(paths.root / "scripts" / "verify.sh")], cwd=paths.root, check=False).returncode
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_rebuild_promote`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add rebuild/driver.py rebuild/README.md tests/test_rebuild_promote.py
git commit -m "feat: add rebuild verification and promotion flow"
```

### Task 7: Run End-To-End Verification And Update User Docs

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `vendor/README.md`
- Modify: `rebuild/README.md`

- [ ] **Step 1: Document the rebuild workflow**

```markdown
## Rebuild Runtime Images

1. `python3 rebuild/driver.py capture-rootfs`
2. `python3 rebuild/driver.py build`
3. `python3 rebuild/driver.py verify`
4. `python3 rebuild/driver.py promote`
```

- [ ] **Step 2: Run the full automated test suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS with all rebuild and runtime tests green

- [ ] **Step 3: Run the rebuild flow for real**

Run:

```bash
python3 rebuild/driver.py capture-rootfs
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
python3 rebuild/driver.py promote
```

Expected:

- `rebuild/rootfs/base.tar` exists and is non-empty
- `rebuild/out/images/bootimage-0.12-hd` exists and is non-empty
- `rebuild/out/images/hdc-0.12.img` exists and is non-empty
- `python3 rebuild/driver.py verify` exits `0`
- `./scripts/verify.sh` exits `0` after promotion

- [ ] **Step 4: Commit the implementation**

```bash
git add README.md README.en.md vendor/README.md rebuild tests tools
git commit -m "feat: rebuild Linux 0.12 runtime images from source"
```
