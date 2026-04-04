# Linux 0.12 QEMU Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained repository that boots Linux 0.12 under QEMU on macOS arm64, reaches a shell, and proves success by automatically running `ls`.

**Architecture:** Bundle the Linux 0.12 source archive plus boot/root floppy images under `vendor/`, use thin shell entrypoints under `scripts/`, and keep the runtime logic in a single Python driver under `tools/qemu_driver.py`. Verification reads the VGA text buffer through the QEMU monitor, waits for a stable prompt, injects keystrokes, and confirms the prompt returns after `ls`.

**Tech Stack:** POSIX shell, Python 3 standard library, Git, Homebrew QEMU, bundled historical Linux images

---

### Task 1: Scaffold The Repo And Asset Layout

**Files:**
- Create: `README.md`
- Create: `scripts/bootstrap-host.sh`
- Create: `scripts/run.sh`
- Create: `scripts/verify.sh`
- Create: `vendor/README.md`
- Create: `vendor/src/.gitkeep`
- Create: `vendor/images/.gitkeep`
- Create: `tests/test_layout.py`

- [ ] **Step 1: Write the failing layout test**

```python
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "README.md",
            ROOT / "scripts" / "bootstrap-host.sh",
            ROOT / "scripts" / "run.sh",
            ROOT / "scripts" / "verify.sh",
            ROOT / "vendor" / "README.md",
            ROOT / "vendor" / "src",
            ROOT / "vendor" / "images",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_layout`
Expected: FAIL because the files and directories do not exist yet

- [ ] **Step 3: Create the minimal scaffold**

```text
README.md
scripts/bootstrap-host.sh
scripts/run.sh
scripts/verify.sh
vendor/README.md
vendor/src/.gitkeep
vendor/images/.gitkeep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_layout`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md scripts vendor tests/test_layout.py
git commit -m "chore: scaffold Linux 0.12 QEMU repo"
```

### Task 2: Build And Test The QEMU Driver Core

**Files:**
- Create: `tools/qemu_driver.py`
- Test: `tests/test_qemu_driver.py`

- [ ] **Step 1: Write the failing driver tests**

```python
import pathlib
import unittest

from tools.qemu_driver import (
    DriverPaths,
    build_qemu_command,
    decode_vga_text_buffer,
    find_stable_prompt,
    verification_succeeded,
)


class QemuDriverTest(unittest.TestCase):
    def test_build_qemu_command_for_interactive_mode_uses_curses(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = DriverPaths.from_root(root)

        command = build_qemu_command(paths=paths, mode="interactive", qemu_bin="qemu-system-i386")

        self.assertIn("-display", command)
        self.assertIn("curses", command)
        self.assertIn("16M", command)
        self.assertIn(str(paths.boot_image), command)
        self.assertIn(str(paths.root_image), command)

    def test_decode_vga_text_buffer_returns_visible_text(self) -> None:
        data = bytearray(b" " * 4000)
        data[0] = ord("r")
        data[2] = ord("o")
        data[4] = ord("o")
        data[6] = ord("t")
        data[8] = ord("#")

        lines = decode_vga_text_buffer(bytes(data))

        self.assertEqual("root#", lines[0].rstrip())

    def test_find_stable_prompt_requires_three_identical_snapshots(self) -> None:
        history = [
            ["login: "],
            ["root# "],
            ["root# "],
            ["root# "],
        ]

        self.assertEqual("root#", find_stable_prompt(history))

    def test_verification_succeeded_requires_prompt_return(self) -> None:
        baseline = "root#"
        final_lines = [
            "Linux 0.12",
            "root# ls",
            "bin dev etc tmp usr",
            "root#",
        ]

        self.assertTrue(verification_succeeded(final_lines, baseline))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_qemu_driver`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors

- [ ] **Step 3: Write the minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DriverPaths:
    root: Path
    boot_image: Path
    root_image: Path
    out_dir: Path
    monitor_socket: Path
    pidfile: Path
    vga_dump: Path

    @classmethod
    def from_root(cls, root: Path) -> "DriverPaths":
        out_dir = root / "out" / "verify"
        return cls(
            root=root,
            boot_image=root / "vendor" / "images" / "bootimage-0.12",
            root_image=root / "vendor" / "images" / "rootimage-0.12",
            out_dir=out_dir,
            monitor_socket=out_dir / "monitor.sock",
            pidfile=out_dir / "qemu.pid",
            vga_dump=out_dir / "vga.bin",
        )


def build_qemu_command(paths: DriverPaths, mode: str, qemu_bin: str) -> list[str]:
    command = [
        qemu_bin,
        "-m",
        "16M",
        "-boot",
        "a",
        "-drive",
        f"file={paths.boot_image},format=raw,if=floppy,index=0",
        "-drive",
        f"file={paths.root_image},format=raw,if=floppy,index=1",
        "-k",
        "en-us",
    ]
    if mode == "interactive":
        command.extend(["-display", "curses"])
    else:
        command.extend(
            [
                "-display",
                "none",
                "-monitor",
                f"unix:{paths.monitor_socket},server=on,wait=off",
                "-pidfile",
                str(paths.pidfile),
            ]
        )
    return command


def decode_vga_text_buffer(data: bytes) -> list[str]:
    chars = []
    for index in range(0, min(len(data), 4000), 2):
        byte = data[index]
        chars.append(chr(byte) if 32 <= byte <= 126 else " ")
    rows = ["".join(chars[offset : offset + 80]).rstrip() for offset in range(0, 2000, 80)]
    return rows


def find_stable_prompt(history: list[list[str]]) -> str | None:
    if len(history) < 3:
        return None
    tail = history[-3:]
    if tail[0] != tail[1] or tail[1] != tail[2]:
        return None
    for line in reversed(tail[-1]):
        stripped = line.rstrip()
        if stripped.endswith("#") or stripped.endswith("$"):
            return stripped
    return None


def verification_succeeded(final_lines: list[str], baseline_prompt: str) -> bool:
    compact = [line.rstrip() for line in final_lines if line.strip()]
    try:
        command_index = compact.index(f"{baseline_prompt} ls")
    except ValueError:
        return False
    if compact[-1] != baseline_prompt:
        return False
    return any(line and line != f"{baseline_prompt} ls" for line in compact[command_index + 1 : -1])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_qemu_driver`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/qemu_driver.py tests/test_qemu_driver.py
git commit -m "feat: add QEMU driver core"
```

### Task 3: Add CLI Behavior And Script Entry Points

**Files:**
- Modify: `tools/qemu_driver.py`
- Modify: `scripts/bootstrap-host.sh`
- Modify: `scripts/run.sh`
- Modify: `scripts/verify.sh`
- Test: `tests/test_scripts.py`

- [ ] **Step 1: Write the failing script tests**

```python
import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ScriptTest(unittest.TestCase):
    def test_bootstrap_host_fails_with_clear_message_when_qemu_missing(self) -> None:
        env = {"PATH": ""}
        result = subprocess.run(
            ["sh", str(ROOT / "scripts" / "bootstrap-host.sh")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("brew install qemu", result.stderr)

    def test_verify_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify.sh").read_text()
        self.assertIn("tools/qemu_driver.py", text)
        self.assertIn("verify", text)

    def test_driver_supports_dry_run(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "qemu_driver.py"), "verify", "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("qemu-system-i386", result.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_scripts`
Expected: FAIL because the shell scripts and CLI behavior are incomplete

- [ ] **Step 3: Write the minimal implementation**

```sh
#!/bin/sh
set -eu

if ! command -v qemu-system-i386 >/dev/null 2>&1; then
  echo "qemu-system-i386 not found. Install it with: brew install qemu" >&2
  exit 1
fi

qemu-system-i386 --version
```

```sh
#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec python3 tools/qemu_driver.py run
```

```sh
#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec python3 tools/qemu_driver.py verify "$@"
```

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_scripts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts tools/qemu_driver.py tests/test_scripts.py
git commit -m "feat: add CLI entrypoints"
```

### Task 4: Bundle Historical Assets And Provenance Docs

**Files:**
- Modify: `README.md`
- Modify: `vendor/README.md`
- Create: `vendor/src/linux-0.12.tar.gz`
- Create: `vendor/images/bootimage-0.12`
- Create: `vendor/images/rootimage-0.12`
- Test: `tests/test_assets.py`

- [ ] **Step 1: Write the failing asset test**

```python
import hashlib
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AssetTest(unittest.TestCase):
    def test_vendor_assets_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "vendor" / "src" / "linux-0.12.tar.gz",
            ROOT / "vendor" / "images" / "bootimage-0.12",
            ROOT / "vendor" / "images" / "rootimage-0.12",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_assets`
Expected: FAIL because the historical assets are not bundled yet

- [ ] **Step 3: Download and document the assets**

```bash
curl -L https://www.kernel.org/pub/linux/kernel/Historic/old-versions/linux-0.12.tar.gz \
  -o vendor/src/linux-0.12.tar.gz

curl -L https://mirror.math.princeton.edu/pub/oldlinux/Linux.old/images/images-zip/bootimage-0.12-20040306 \
  -o vendor/images/bootimage-0.12

curl -L https://mirror.math.princeton.edu/pub/oldlinux/Linux.old/images/images-zip/rootimage-0.12-20040306 \
  -o vendor/images/rootimage-0.12
```

Update `vendor/README.md` to record the source URLs and why the repo ships raw images.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v tests.test_assets`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md vendor tests/test_assets.py
git commit -m "chore: bundle Linux 0.12 assets"
```

### Task 5: Implement End-To-End Verification And Prove It Works

**Files:**
- Modify: `tools/qemu_driver.py`
- Modify: `README.md`
- Test: `tests/test_qemu_driver.py`

- [ ] **Step 1: Write the failing integration-oriented test**

```python
import unittest

from tools.qemu_driver import verification_succeeded


class VerificationRulesTest(unittest.TestCase):
    def test_verification_rejects_missing_prompt_return(self) -> None:
        baseline = "root#"
        final_lines = [
            "root# ls",
            "bin dev etc tmp usr",
        ]

        self.assertFalse(verification_succeeded(final_lines, baseline))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -v tests.test_qemu_driver.VerificationRulesTest`
Expected: FAIL until the verification logic is fully wired

- [ ] **Step 3: Implement the runtime verification path**

```text
Add to tools/qemu_driver.py:
- argument parsing for `run` and `verify`
- out/verify directory creation
- local monitor socket polling
- `pmemsave 0xb8000 4000 <path>` monitor command
- prompt history collection
- `sendkey r`, `sendkey o`, `sendkey o`, `sendkey t`, `sendkey ret` for login
- `sendkey l`, `sendkey s`, `sendkey ret` for command execution
- timeout and artifact preservation
```

- [ ] **Step 4: Run the unit tests and host verification**

Run: `python3 -m unittest -v`
Expected: PASS

Run: `brew install qemu`
Expected: QEMU installed if not already present

Run: `./scripts/bootstrap-host.sh`
Expected: prints the QEMU version

Run: `./scripts/verify.sh`
Expected: exits `0` after booting Linux 0.12 and running `ls`

Run: `./scripts/run.sh`
Expected: boots interactively to the Linux 0.12 login or shell prompt

- [ ] **Step 5: Commit**

```bash
git add README.md tools/qemu_driver.py out/verify
git commit -m "feat: verify Linux 0.12 boot under QEMU"
```
