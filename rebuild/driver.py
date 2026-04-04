from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CONTAINER_IMAGE = "linux-012-rebuild"


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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def docker_build_command(paths: BuildPaths) -> list[str]:
    return [
        "docker",
        "build",
        "--platform",
        "linux/amd64",
        "-t",
        CONTAINER_IMAGE,
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
        CONTAINER_IMAGE,
        "bash",
        script,
    ]


def verify_environment(paths: BuildPaths) -> dict[str, str]:
    env = os.environ.copy()
    env["LINUX012_BOOT_SOURCE_IMAGE"] = str(paths.boot_image)
    env["LINUX012_HARD_DISK_IMAGE"] = str(paths.hard_disk_image)
    return env


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["bootstrap-host", "build", "run", "verify"])
    return parser.parse_args(argv)


def run_command(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=False).returncode
    except FileNotFoundError as exc:
        print(f"Missing host dependency: {exc.filename}", file=sys.stderr)
        return 1


def run_container_script(paths: BuildPaths, script: str) -> int:
    build_status = run_command(docker_build_command(paths), cwd=paths.root)
    if build_status != 0:
        return build_status
    return run_command(docker_run_command(paths, script=script), cwd=paths.root)


def require_rebuilt_images(paths: BuildPaths) -> bool:
    required = [paths.boot_image, paths.hard_disk_image]
    missing = [path for path in required if not path.exists() or path.stat().st_size == 0]
    if not missing:
        return True
    print("Missing rebuilt images:", file=sys.stderr)
    for path in missing:
        print(f"  {path}", file=sys.stderr)
    print("Run `python3 rebuild/driver.py build` first.", file=sys.stderr)
    return False


def run_build(paths: BuildPaths) -> int:
    return run_container_script(paths, script="rebuild/container/build_images.sh")


def ensure_rebuilt_images(paths: BuildPaths) -> int:
    if require_rebuilt_images(paths):
        return 0
    return run_build(paths)


def run_bootstrap_host(paths: BuildPaths) -> int:
    qemu_status = run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), "bootstrap-host"],
        cwd=paths.root,
    )
    if qemu_status != 0:
        return qemu_status
    return run_command(["docker", "--version"], cwd=paths.root)


def run_runtime(paths: BuildPaths, mode: str) -> int:
    if ensure_rebuilt_images(paths) != 0:
        return 1
    return run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), mode],
        cwd=paths.root,
        env=verify_environment(paths),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    paths = BuildPaths.from_root(repo_root())
    if args.command == "bootstrap-host":
        return run_bootstrap_host(paths)
    if args.command == "build":
        return run_build(paths)
    if args.command == "run":
        return run_runtime(paths, mode="run")
    return run_runtime(paths, mode="verify")


if __name__ == "__main__":
    raise SystemExit(main())
