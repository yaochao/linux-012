# Directory README Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Chinese-first `README.md` and English `README.en.md` files to every tracked project directory except generated output directories.

**Architecture:** Use one layout test to enforce README coverage across all tracked directories, then add focused bilingual README pairs to each directory. Keep top-level READMEs and existing directory descriptions aligned with the current source-built QEMU workflow.

**Tech Stack:** Python `unittest`, Markdown documentation, git-tracked repository layout

---

### Task 1: Enforce README Coverage In Tests

**Files:**
- Modify: `tests/test_layout.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run the targeted layout test and confirm missing README failures**
- [ ] **Step 3: Keep the expected directory list limited to tracked source directories and exclude generated output trees**
- [ ] **Step 4: Re-run the targeted layout test after documentation files are added**

### Task 2: Add Bilingual README Files To Source Directories

**Files:**
- Modify: `rebuild/README.md`
- Modify: `vendor/README.md`
- Create: `rebuild/README.en.md`
- Create: `vendor/README.en.md`
- Create: `docs/README.md`
- Create: `docs/README.en.md`
- Create: `docs/superpowers/README.md`
- Create: `docs/superpowers/README.en.md`
- Create: `docs/superpowers/plans/README.md`
- Create: `docs/superpowers/plans/README.en.md`
- Create: `docs/superpowers/specs/README.md`
- Create: `docs/superpowers/specs/README.en.md`
- Create: `images/README.md`
- Create: `images/README.en.md`
- Create: `rebuild/container/README.md`
- Create: `rebuild/container/README.en.md`
- Create: `rebuild/patches/README.md`
- Create: `rebuild/patches/README.en.md`
- Create: `rebuild/patches/linux-0.12/README.md`
- Create: `rebuild/patches/linux-0.12/README.en.md`
- Create: `rebuild/rootfs/README.md`
- Create: `rebuild/rootfs/README.en.md`
- Create: `rebuild/rootfs/manifest/README.md`
- Create: `rebuild/rootfs/manifest/README.en.md`
- Create: `rebuild/rootfs/manifest/etc/README.md`
- Create: `rebuild/rootfs/manifest/etc/README.en.md`
- Create: `rebuild/rootfs/manifest/usr/README.md`
- Create: `rebuild/rootfs/manifest/usr/README.en.md`
- Create: `rebuild/rootfs/manifest/usr/root/README.en.md`
- Create: `rebuild/rootfs/overlay/README.md`
- Create: `rebuild/rootfs/overlay/README.en.md`
- Create: `rebuild/tools/README.md`
- Create: `rebuild/tools/README.en.md`
- Create: `rebuild/userland/README.md`
- Create: `rebuild/userland/README.en.md`
- Create: `rebuild/userland/include/README.md`
- Create: `rebuild/userland/include/README.en.md`
- Create: `rebuild/userland/src/README.md`
- Create: `rebuild/userland/src/README.en.md`
- Create: `scripts/README.md`
- Create: `scripts/README.en.md`
- Create: `tests/README.md`
- Create: `tests/README.en.md`
- Create: `tools/README.md`
- Create: `tools/README.en.md`
- Create: `vendor/src/README.md`
- Create: `vendor/src/README.en.md`

- [ ] **Step 1: Convert existing single-language directory READMEs to Chinese-first README.md files**
- [ ] **Step 2: Add README.en.md peers to directories that already had only Chinese or only English docs**
- [ ] **Step 3: Add concise Chinese-first README pairs to the remaining tracked directories**
- [ ] **Step 4: Keep each README scoped to its directory responsibility and main files**

### Task 3: Verify Documentation Coverage And Formatting

**Files:**
- Modify: `tests/test_layout.py`
- Verify: repository-wide documentation files

- [ ] **Step 1: Run `python3 -m unittest -v tests.test_layout.LayoutTest.test_expected_paths_exist`**
- [ ] **Step 2: Run `python3 -m unittest discover -s tests -v`**
- [ ] **Step 3: Run `git diff --check`**
- [ ] **Step 4: Inspect `git status --short` and report the new README set**
