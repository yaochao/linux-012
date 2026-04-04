# GitHub Actions CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions workflow that proves the repo still builds and boots Linux 0.12 from source on every push and pull request.

**Architecture:** Enforce workflow presence with a repository test, then add a single Ubuntu-based CI workflow under `.github/workflows/` that runs the existing host bootstrap, unit tests, source build, and QEMU `ls` verification. Keep the workflow aligned with current documented entrypoints instead of inventing a parallel CI-only path.

**Tech Stack:** GitHub Actions, Ubuntu runner, Docker, QEMU, Python `unittest`, repository shell scripts

---

### Task 1: Add The Failing Workflow Coverage Test

**Files:**
- Create: `tests/test_ci_workflow.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run the targeted test and confirm it fails because `.github/workflows/ci.yml` does not exist**
- [ ] **Step 3: Keep the test focused on the required workflow file and the key commands it must run**
- [ ] **Step 4: Re-run the targeted test after the workflow is added**

### Task 2: Add The GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Define a single CI workflow triggered on pushes and pull requests to `main`**
- [ ] **Step 2: Install QEMU and Docker support on `ubuntu-22.04`**
- [ ] **Step 3: Run `python3 -m unittest discover -s tests -v`**
- [ ] **Step 4: Run `./scripts/bootstrap-host.sh`, `python3 rebuild/driver.py build`, and `./scripts/verify.sh`**
- [ ] **Step 5: Upload verification artifacts so CI failures are debuggable**

### Task 3: Document And Verify The New CI Path

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `tests/test_layout.py`

- [ ] **Step 1: Add `.github/workflows/ci.yml` to the expected repository layout**
- [ ] **Step 2: Add a short CI section to both README files**
- [ ] **Step 3: Run `python3 -m unittest discover -s tests -v`**
- [ ] **Step 4: Run `git diff --check`**
- [ ] **Step 5: Inspect `git status --short` and summarize the new CI files**
