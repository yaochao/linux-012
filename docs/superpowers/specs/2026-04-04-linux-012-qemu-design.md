# Linux 0.12 QEMU Self-Contained Repo Design

Date: 2026-04-04
Status: Design approved in chat, pending written-spec review

## 1. Summary

Build a self-contained project in this directory that can boot Linux 0.12 under QEMU on this machine, reach a command-line prompt, and prove success by automatically running `ls`.

The repository must keep all project artifacts under the current directory. Installing QEMU on the host via Homebrew is allowed, but the repo itself should contain the scripts, vendor assets, documentation, and generated runtime output needed for repeatable use and future GitHub publication.

The v1 implementation will optimize for repeatable execution and transparent provenance, not for reconstructing a 1992-native build toolchain on macOS arm64.

## 2. Context And Constraints

- Host OS: macOS on Apple Silicon (`arm64`)
- Current working directory is empty and will be treated as the project root
- Homebrew installation of `qemu` is allowed on the host
- All project files must remain under this repository root
- The desired result is a repeatable one-command workflow
- The repository should be suitable for later upload to GitHub
- The repo should be self-contained from a project-assets perspective

Interpretation of "self-contained" for this project:

- Allowed outside-repo dependency: host-installed `qemu-system-i386` from Homebrew
- Disallowed outside-repo dependency for normal project use: downloading Linux 0.12 source or boot/root images at runtime
- Required in-repo assets: Linux 0.12 source snapshot, bootable runtime images, launch scripts, verification tooling, docs

## 3. Goals

- Provide a single command that boots Linux 0.12 interactively
- Provide a single command that verifies the boot non-interactively and proves `ls` executed successfully
- Keep runtime assets, scripts, and logs organized entirely under this repository
- Preserve the provenance of bundled historical assets clearly enough for GitHub publication and later maintenance
- Make the verification flow deterministic enough to be rerun by other users on similar hosts

## 4. Non-Goals

- Rebuilding Linux 0.12 from source on macOS arm64 in v1
- Reconstructing a period-correct 1992 build environment in v1
- Supporting every host OS in v1
- Exposing guest services over network in v1
- Creating a generalized Linux-0.x emulator framework in v1

## 5. Considered Approaches

### Approach A: Full Source Rebuild

Bundle Linux 0.12 source and rebuild the bootable system from source on the host.

Pros:

- Highest transparency
- Strong educational value
- Minimal reliance on prebuilt historical images

Cons:

- Highest implementation risk on macOS arm64
- Requires solving an old x86 toolchain problem before solving the user problem
- Much more fragile than necessary for "boot, reach shell, run `ls`"

Decision: rejected for v1.

### Approach B: Pure Prebuilt Runtime Images

Bundle only the images required to run Linux 0.12 plus a small launch script.

Pros:

- Fastest path to a working result
- Lowest operational risk

Cons:

- Weak transparency
- Poor traceability for future maintainers

Decision: rejected as too opaque.

### Approach C: Hybrid Self-Contained Repo

Bundle Linux 0.12 source snapshot for provenance plus bootable images for execution. Use QEMU scripts for launching and Python tooling for deterministic verification.

Pros:

- Best fit for the requested "self-contained GitHub-friendly" result
- Practical to implement on macOS arm64
- Clear separation between runtime assets and historical source provenance

Cons:

- Slightly larger repository
- Does not rebuild the system from source in v1

Decision: accepted.

## 6. High-Level Design

### 6.1 Repo Layout

The repository will use this layout:

```text
.
├── README.md
├── .gitignore
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-04-linux-012-qemu-design.md
├── scripts/
│   ├── bootstrap-host.sh
│   ├── run.sh
│   └── verify.sh
├── tools/
│   └── qemu_driver.py
├── vendor/
│   ├── src/
│   │   └── linux-0.12.tar.gz
│   └── images/
│       ├── bootimage-0.12
│       └── rootimage-0.12
└── out/
    └── verify/
```

Notes:

- `vendor/src/` stores the Linux 0.12 source archive for provenance and future extension.
- `vendor/images/` stores the runtime boot media used by QEMU.
- `scripts/` contains user-facing entry points.
- `tools/` contains implementation details for automation.
- `out/` stores runtime logs and verification artifacts and should not be committed.

### 6.2 Runtime Strategy

The runtime flow will use `qemu-system-i386` on the host. The guest will boot from bundled Linux 0.12 boot/root images.

The repo will not depend on runtime downloads. If the repo is cloned with full contents and the host has `qemu-system-i386`, both interactive boot and automated verification should work immediately.

### 6.3 Why Images First

The user request is to boot Linux 0.12, reach a command line, and run `ls` repeatably. Prevalidated runtime images are the shortest path to that result. Bundling the source archive in parallel preserves traceability without turning v1 into a legacy compiler project.

## 7. Host Dependency Design

### 7.1 Allowed Host Dependency

The only required host dependency in v1 is QEMU installed through Homebrew:

```sh
brew install qemu
```

No project script will install Homebrew or QEMU automatically. The project will fail fast with a clear message if `qemu-system-i386` is missing.

### 7.2 Host Bootstrap Script

`scripts/bootstrap-host.sh` will:

- verify `qemu-system-i386` exists
- print the discovered QEMU path and version
- exit non-zero with an explicit Homebrew installation instruction if QEMU is missing

This script is intentionally narrow. It validates prerequisites; it does not mutate the project state.

## 8. Boot Design

### 8.1 Interactive Boot Path

`scripts/run.sh` will start Linux 0.12 in an interactive text UI using QEMU's curses display mode.

Planned characteristics:

- target binary: `qemu-system-i386`
- display mode: curses text UI
- guest boot device: floppy image
- guest assets: bundled boot/root images under `vendor/images/`
- keyboard layout: `en-us`
- no networking required
- runtime output kept inside `out/`

Why curses:

- Linux 0.12 is a text-console workload
- curses mode avoids dependence on a separate GUI window manager flow
- it is more compatible with terminal-based operation and easier to document

### 8.2 Conservative Guest Defaults

The boot wrapper will choose conservative guest defaults appropriate for a very old x86 guest. The default guest memory size for v1 is fixed at `16M` instead of relying on modern QEMU defaults. This value is chosen as a compatibility-first default, not a performance setting.

### 8.3 Asset Selection Rule

Implementation must verify that the bundled images actually boot to a shell and permit `ls`. If the first candidate historical image set does not satisfy that behavior, the repo may substitute another Linux 0.12-compatible image set, but the provenance and reason must be documented in `README.md`.

## 9. Verification Design

### 9.1 Verification Goal

`scripts/verify.sh` must automatically prove all of the following:

1. QEMU started successfully.
2. Linux 0.12 reached a usable command-line prompt.
3. The guest received the command `ls`.
4. The screen state after execution satisfies the success rules defined in section 9.5.

The script must return exit code `0` only if all four conditions are satisfied.

### 9.2 Verification Architecture

`scripts/verify.sh` will delegate to `tools/qemu_driver.py`.

`tools/qemu_driver.py` will:

- start QEMU in a non-interactive mode without showing a display window
- expose the QEMU monitor only on a local UNIX domain socket under `out/verify/`
- capture QEMU process metadata and logs under `out/verify/`
- poll the guest VGA text buffer through the monitor
- wait until a shell prompt pattern is recognized
- inject keystrokes to run `ls`
- capture the resulting screen state
- decide pass/fail using deterministic string matching rules

### 9.3 How Command Injection Works

Automation will not rely on copy-paste into a GUI window.

Instead, the verifier will use the QEMU monitor to send keys into the guest. This keeps the automation local, scriptable, and compatible with headless verification.

The default input sequence is:

1. Wait for prompt
2. Send `l`
3. Send `s`
4. Send `ret`
5. Wait for command echo and output stabilization

### 9.4 How Prompt Detection Works

The verifier will inspect the guest 80x25 VGA text buffer and consider the system "at prompt" only when all of the following are true:

- the bottom-most non-empty visible line ends with `#` or `$`
- that same line content remains unchanged for three consecutive polls
- the screen did not change in the immediately preceding poll window except for cursor-position effects that do not alter characters

The exact prompt line captured at this moment becomes the baseline prompt string for the rest of the verification run.

### 9.5 How Success Is Determined

Verification succeeds only if the final captured screen state includes:

- the command text `ls`
- at least one non-empty line between the echoed `ls` line and the reappeared prompt line
- the exact baseline prompt string reappearing after command execution

If output tokens differ from expectations, the verifier must fail and preserve artifacts instead of guessing success.

## 10. Failure Handling

### 10.1 Failure Categories

The implementation must distinguish at least these failure modes:

- missing host dependency (`qemu-system-i386` not found)
- QEMU launch failure
- boot timeout
- prompt not detected
- key injection failure
- `ls` output not recognized

### 10.2 Failure Artifacts

On every verification failure, the project must preserve:

- QEMU PID file if available
- monitor socket path
- monitor session log
- QEMU stderr/stdout log
- final text-screen dump
- a concise failure summary printed to the terminal

### 10.3 No Silent Fallbacks

The implementation must not silently switch to runtime downloads, alternate images outside the repo, or different host tools. Any such behavior would violate the project's self-contained constraint.

## 11. Documentation Design

### 11.1 README Requirements

`README.md` must include:

- project purpose
- host requirements
- `brew install qemu`
- repo layout overview
- interactive boot command
- verification command
- expected success output
- known limitations
- provenance note for bundled Linux 0.12 source archive and runtime images

### 11.2 Provenance Note

The repo must document where the bundled historical assets came from and whether they were modified. Provenance matters here because the runtime images are historical artifacts, not newly built binaries.

## 12. Testing Strategy

### 12.1 Required Validation Before Completion

Implementation is not complete until all of the following are demonstrated on this host:

- `scripts/bootstrap-host.sh` succeeds after QEMU is installed
- `scripts/run.sh` boots to a shell interactively
- `scripts/verify.sh` exits successfully
- the verification artifacts show the `ls` command and its result clearly enough for inspection

### 12.2 Repeatability Expectation

The verify command must be rerunnable without manual cleanup. If output directories already exist, the script should either clean only its own generated files or overwrite them safely.

## 13. Scope Boundary: V1 vs V2

### 13.1 V1

V1 includes:

- self-contained repo structure
- bundled Linux 0.12 source archive
- bundled bootable runtime images
- host bootstrap check
- interactive launch script
- automated verification that proves `ls`
- logs and README

### 13.2 V2

V2 may include:

- rebuilding bootable images from source
- adding image-integrity checksums
- CI automation on a suitable runner
- alternative display backends
- richer guest command automation

## 14. Implementation Decisions Locked By This Spec

- The repo is self-contained for project assets but not for QEMU binaries.
- Homebrew-provided QEMU is allowed and expected.
- All repo-owned files live under the current directory.
- V1 uses a hybrid model: source archive for provenance, prebuilt images for execution.
- Interactive mode uses a text-oriented QEMU display flow.
- Automated verification uses a local monitor socket and scripted key injection.
- V1 does not rebuild Linux 0.12 from source.

## 15. Reference Sources

- Linux 0.12 source archive provenance: https://www.kernel.org/pub/linux/kernel/Historic/old-versions/
- Historical Linux image source candidate: https://oldlinux.org/
- QEMU manual reference for display, keyboard, chardev, and process options: https://www.qemu.org/docs/master/system/qemu-manpage.html
- QEMU monitor reference for `sendkey` and guest memory inspection: https://www.qemu.org/docs/master/system/monitor.html
- QEMU security guidance for monitor exposure: https://www.qemu.org/docs/master/system/security.html

## 16. Open Questions

None. The current scope is sufficiently defined for implementation planning.
