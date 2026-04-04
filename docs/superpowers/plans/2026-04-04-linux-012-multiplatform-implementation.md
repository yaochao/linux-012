# Linux 0.12 Multiplatform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing Linux 0.12 QEMU repo usable on macOS arm64, Ubuntu 22.04, and Windows 10 without changing the vendored boot assets.

**Architecture:** Keep `tools/qemu_driver.py` as the single runtime implementation and add a host-platform abstraction inside it. Use thin shell, PowerShell, and batch wrappers so the repo exposes native entrypoints on Unix and Windows while preserving a single verification flow.

**Tech Stack:** Python 3 standard library, POSIX shell, PowerShell, Windows batch scripts, QEMU

---

### Task 1: Add Failing Cross-Platform Tests

**Files:**
- Modify: `tests/test_layout.py`
- Modify: `tests/test_qemu_driver.py`
- Modify: `tests/test_scripts.py`

- [ ] **Step 1: Add layout expectations for Windows entrypoints**

Add expectations for:

- `scripts/bootstrap-host.ps1`
- `scripts/run.ps1`
- `scripts/verify.ps1`
- `scripts/bootstrap-host.cmd`
- `scripts/run.cmd`
- `scripts/verify.cmd`

- [ ] **Step 2: Add failing driver tests for platform-aware behavior**

Cover:

- macOS/Linux interactive mode uses `-display curses`
- Windows interactive mode omits curses display
- Windows verification mode uses TCP monitor
- platform-specific bootstrap hints
- environment-variable or common-path QEMU resolution

- [ ] **Step 3: Add failing script tests for Windows wrapper coverage**

Check that Windows wrappers dispatch into `tools/qemu_driver.py`.

- [ ] **Step 4: Run the targeted tests and confirm they fail**

Run:

```bash
python3 -m unittest -v tests.test_layout tests.test_qemu_driver tests.test_scripts
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_layout.py tests/test_qemu_driver.py tests/test_scripts.py
git commit -m "test: cover Linux 0.12 multiplatform support"
```

### Task 2: Make The Python Driver Platform-Aware

**Files:**
- Modify: `tools/qemu_driver.py`
- Test: `tests/test_qemu_driver.py`

- [ ] **Step 1: Add platform abstraction and monitor endpoint modeling**

Introduce small focused helpers for:

- host platform detection
- monitor endpoint creation
- QEMU binary discovery
- install guidance

- [ ] **Step 2: Update QEMU command construction**

Implement:

- curses display for macOS/Linux interactive mode
- default windowed display for Windows interactive mode
- TCP monitor for Windows verification
- UNIX socket monitor for macOS/Linux verification

- [ ] **Step 3: Add bootstrap mode to the driver**

Expose a driver mode that:

- resolves the QEMU binary
- prints version when found
- prints a platform-appropriate install hint when not found

- [ ] **Step 4: Run targeted tests and make them pass**

Run:

```bash
python3 -m unittest -v tests.test_qemu_driver
python3 -m unittest -v tests.test_scripts
```

- [ ] **Step 5: Commit**

```bash
git add tools/qemu_driver.py tests/test_qemu_driver.py tests/test_scripts.py
git commit -m "feat: add multiplatform QEMU driver support"
```

### Task 3: Add Native Windows Entry Points

**Files:**
- Create: `scripts/bootstrap-host.ps1`
- Create: `scripts/run.ps1`
- Create: `scripts/verify.ps1`
- Create: `scripts/bootstrap-host.cmd`
- Create: `scripts/run.cmd`
- Create: `scripts/verify.cmd`
- Test: `tests/test_layout.py`
- Test: `tests/test_scripts.py`

- [ ] **Step 1: Add PowerShell wrappers**

Each PowerShell wrapper should:

- move to the repo root
- resolve `py -3` or `python`
- execute the Python driver with the correct mode

- [ ] **Step 2: Add batch wrappers**

Each batch wrapper should delegate to the matching PowerShell script with execution policy bypass.

- [ ] **Step 3: Run targeted tests and make them pass**

Run:

```bash
python3 -m unittest -v tests.test_layout tests.test_scripts
```

- [ ] **Step 4: Commit**

```bash
git add scripts tests/test_layout.py tests/test_scripts.py
git commit -m "feat: add Windows entrypoint wrappers"
```

### Task 4: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `vendor/README.md`

- [ ] **Step 1: Document host support matrix**

Describe:

- macOS arm64
- Ubuntu 22.04
- Windows 10

- [ ] **Step 2: Document host entrypoints**

Show:

- Unix commands via `*.sh`
- Windows commands via `*.ps1` and `*.cmd`

- [ ] **Step 3: Document platform-specific operational notes**

Explain:

- Windows interactive mode uses a QEMU window
- Unix interactive mode uses curses
- Windows verification uses loopback TCP monitor

- [ ] **Step 4: Commit**

```bash
git add README.md vendor/README.md
git commit -m "docs: document multiplatform host support"
```

### Task 5: Run Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

- [ ] **Step 2: Run Unix host bootstrap**

Run:

```bash
./scripts/bootstrap-host.sh
```

- [ ] **Step 3: Run automated verification**

Run:

```bash
./scripts/verify.sh
```

- [ ] **Step 4: Run interactive boot sanity check**

Run:

```bash
./scripts/run.sh
```

Confirm `out/run/screen.txt` reaches `[/]#`, then stop the QEMU process.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: verify multiplatform Linux 0.12 support"
```
