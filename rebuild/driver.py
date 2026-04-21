from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


CONTAINER_IMAGE = "linux-012-rebuild"
REPO_IMAGE_ASSET_NAMES = ("bootimage-0.12-hd", "hdc-0.12.img.xz")


@dataclass(frozen=True)
class BuildPaths:
    root: Path
    repo_images_dir: Path
    rebuild_dir: Path
    out_dir: Path
    images_dir: Path
    logs_dir: Path
    work_dir: Path
    boot_image: Path
    hard_disk_image: Path
    repo_boot_image: Path
    repo_hard_disk_image_archive: Path
    repo_manifest: Path
    repo_runtime_dir: Path
    repo_runtime_hard_disk_image: Path

    @classmethod
    def from_root(cls, root: Path) -> "BuildPaths":
        rebuild_dir = root / "rebuild"
        out_dir = rebuild_dir / "out"
        images_dir = out_dir / "images"
        repo_images_dir = root / "images"
        repo_runtime_dir = root / "out" / "repo-images"
        return cls(
            root=root,
            repo_images_dir=repo_images_dir,
            rebuild_dir=rebuild_dir,
            out_dir=out_dir,
            images_dir=images_dir,
            logs_dir=out_dir / "logs",
            work_dir=out_dir / "work",
            boot_image=images_dir / "bootimage-0.12-hd",
            hard_disk_image=images_dir / "hdc-0.12.img",
            repo_boot_image=repo_images_dir / "bootimage-0.12-hd",
            repo_hard_disk_image_archive=repo_images_dir / "hdc-0.12.img.xz",
            repo_manifest=repo_images_dir / "manifest.json",
            repo_runtime_dir=repo_runtime_dir,
            repo_runtime_hard_disk_image=repo_runtime_dir / "hdc-0.12.img",
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


def verify_environment(paths: BuildPaths, source: str = "rebuild") -> dict[str, str]:
    env = os.environ.copy()
    if source == "rebuild":
        env["LINUX012_BOOT_SOURCE_IMAGE"] = str(paths.boot_image)
        env["LINUX012_HARD_DISK_IMAGE"] = str(paths.hard_disk_image)
        return env
    if source == "repo":
        env["LINUX012_BOOT_SOURCE_IMAGE"] = str(paths.repo_boot_image)
        env["LINUX012_HARD_DISK_IMAGE"] = str(paths.repo_runtime_hard_disk_image)
        return env
    raise ValueError(f"Unsupported runtime image source: {source}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "bootstrap-host",
            "build",
            "run",
            "verify",
            "verify-userland",
            "verify-repo-images",
            "check-repo-images",
            "check-reproducible-build",
            "fetch-release-images",
            "verify-release-readback",
            "prepare-release-assets",
            "run-repo-images",
            "run-repo-images-window",
            "build-and-run-repo-images",
            "build-and-run-repo-images-window",
        ],
    )
    parser.add_argument("--release-tag")
    parser.add_argument("--download-base-url")
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


def repo_image_paths(paths: BuildPaths) -> dict[str, Path]:
    return {
        "bootimage-0.12-hd": paths.repo_boot_image,
        "hdc-0.12.img.xz": paths.repo_hard_disk_image_archive,
    }


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def snapshot_record(path: Path) -> dict[str, object]:
    return {
        "sha256": hash_file(path),
        "size": int(path.stat().st_size),
    }


def parse_github_remote(remote: str) -> str | None:
    text = remote.strip()
    if not text:
        return None
    if text.startswith("git@github.com:"):
        slug = text.removeprefix("git@github.com:")
    elif text.startswith("https://github.com/"):
        slug = text.removeprefix("https://github.com/")
    elif text.startswith("http://github.com/"):
        slug = text.removeprefix("http://github.com/")
    else:
        return None
    if slug.endswith(".git"):
        slug = slug[:-4]
    parts = [part for part in slug.split("/") if part]
    if len(parts) != 2:
        return None
    return "/".join(parts)


def exact_git_tag(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "describe", "--tags", "--exact-match"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    tag = completed.stdout.strip()
    return tag or None


def default_release_base_url(root: Path, tag: str | None) -> str | None:
    if not tag:
        return None
    completed = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    slug = parse_github_remote(completed.stdout)
    if not slug:
        return None
    return f"https://github.com/{slug}/releases/download/{tag}"


def load_repo_manifest(paths: BuildPaths) -> dict:
    if not paths.repo_manifest.exists():
        raise FileNotFoundError(paths.repo_manifest)
    return json.loads(paths.repo_manifest.read_text(encoding="utf-8"))


def repo_manifest_assets(manifest: dict) -> dict[str, dict[str, object]]:
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        raise ValueError("Repo image manifest is missing the `assets` object.")
    return assets


def current_repo_asset_records(paths: BuildPaths) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for name, path in repo_image_paths(paths).items():
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
        records[name] = snapshot_record(path)
    return records


def preserve_release_metadata(paths: BuildPaths, assets: dict[str, dict[str, object]]) -> tuple[str | None, str | None]:
    try:
        existing = load_repo_manifest(paths)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        existing = None
    if existing is not None:
        try:
            existing_assets = repo_manifest_assets(existing)
        except ValueError:
            existing_assets = {}
        if all(existing_assets.get(name) == record for name, record in assets.items()):
            tag = existing.get("release_tag")
            base_url = existing.get("download_base_url")
            if isinstance(tag, str) and tag and isinstance(base_url, str) and base_url:
                return tag, base_url
    tag = exact_git_tag(paths.root)
    return tag, default_release_base_url(paths.root, tag)


def write_repo_manifest(
    paths: BuildPaths,
    *,
    release_tag: str | None = None,
    download_base_url: str | None = None,
) -> None:
    assets = current_repo_asset_records(paths)
    if release_tag is None and download_base_url is None:
        release_tag, download_base_url = preserve_release_metadata(paths, assets)
    elif download_base_url is None:
        download_base_url = default_release_base_url(paths.root, release_tag)
    manifest = {
        "version": 1,
        "release_tag": release_tag,
        "download_base_url": download_base_url,
        "assets": assets,
    }
    paths.repo_images_dir.mkdir(parents=True, exist_ok=True)
    temporary = paths.repo_manifest.with_name(f"{paths.repo_manifest.name}.tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(paths.repo_manifest)


def require_repo_images(paths: BuildPaths) -> bool:
    required = [paths.repo_boot_image, paths.repo_hard_disk_image_archive, paths.repo_manifest]
    missing = [path for path in required if not path.exists() or path.stat().st_size == 0]
    if not missing:
        return True
    print("Missing repo-managed runtime images:", file=sys.stderr)
    for path in missing:
        print(f"  {path}", file=sys.stderr)
    print(
        "Run `python3 rebuild/driver.py fetch-release-images` or "
        "`python3 rebuild/driver.py build-and-run-repo-images` first.",
        file=sys.stderr,
    )
    return False


def compress_image_snapshot(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp")
    with source.open("rb") as source_handle, lzma.open(temporary, "wb", preset=9 | lzma.PRESET_EXTREME) as target_handle:
        shutil.copyfileobj(source_handle, target_handle)
    temporary.replace(target)


def extract_image_snapshot(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp")
    with lzma.open(source, "rb") as source_handle, temporary.open("wb") as target_handle:
        shutil.copyfileobj(source_handle, target_handle)
    temporary.replace(target)
    os.utime(target, ns=(source.stat().st_mtime_ns, source.stat().st_mtime_ns))


def check_repo_images(paths: BuildPaths) -> int:
    if not require_repo_images(paths):
        return 1
    try:
        manifest = load_repo_manifest(paths)
        assets = repo_manifest_assets(manifest)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid repo image manifest: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    for name in REPO_IMAGE_ASSET_NAMES:
        record = assets.get(name)
        if not isinstance(record, dict):
            errors.append(f"Missing manifest entry for `{name}`.")
            continue
        path = repo_image_paths(paths)[name]
        if not path.exists():
            errors.append(f"Missing repo image file `{path}`.")
            continue
        expected_size = record.get("size")
        actual_size = int(path.stat().st_size)
        if expected_size != actual_size:
            errors.append(f"Size mismatch for `{name}`: expected {expected_size}, got {actual_size}.")
            continue
        expected_hash = record.get("sha256")
        actual_hash = hash_file(path)
        if expected_hash != actual_hash:
            errors.append(f"SHA-256 mismatch for `{name}`: expected {expected_hash}, got {actual_hash}.")
    if errors:
        print("Repo image snapshot verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("Repo image snapshots verified.")
    return 0


def download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp")
    with urllib.request.urlopen(url) as response, temporary.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    temporary.replace(target)


def fetch_release_images(paths: BuildPaths) -> int:
    try:
        manifest = load_repo_manifest(paths)
        assets = repo_manifest_assets(manifest)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Cannot fetch release images without a valid repo image manifest: {exc}", file=sys.stderr)
        return 1
    base_url = manifest.get("download_base_url")
    if not isinstance(base_url, str) or not base_url:
        print("This checkout is not tied to a published GitHub Release asset set.", file=sys.stderr)
        return 1
    paths.repo_images_dir.mkdir(parents=True, exist_ok=True)
    try:
        for name in REPO_IMAGE_ASSET_NAMES:
            if name not in assets:
                raise ValueError(f"Manifest is missing asset `{name}`.")
            download_file(f"{base_url.rstrip('/')}/{name}", repo_image_paths(paths)[name])
    except (OSError, urllib.error.URLError, ValueError) as exc:
        print(f"Failed to download release images: {exc}", file=sys.stderr)
        return 1
    legacy_image = paths.repo_images_dir / "hdc-0.12.img"
    if legacy_image.exists():
        legacy_image.unlink()
    return check_repo_images(paths)


def sync_repo_images(
    paths: BuildPaths,
    *,
    release_tag: str | None = None,
    download_base_url: str | None = None,
) -> int:
    if not require_rebuilt_images(paths):
        return 1
    paths.repo_images_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.boot_image, paths.repo_boot_image)
    compress_image_snapshot(paths.hard_disk_image, paths.repo_hard_disk_image_archive)
    write_repo_manifest(paths, release_tag=release_tag, download_base_url=download_base_url)
    legacy_image = paths.repo_images_dir / "hdc-0.12.img"
    if legacy_image.exists():
        legacy_image.unlink()
    return 0


def prepare_release_assets(
    paths: BuildPaths,
    *,
    release_tag: str | None,
    download_base_url: str | None = None,
) -> int:
    tag = release_tag or exact_git_tag(paths.root)
    if not tag:
        print(
            "Release asset preparation needs `--release-tag` or an exact git tag checkout.",
            file=sys.stderr,
        )
        return 1
    status = sync_repo_images(paths, release_tag=tag, download_base_url=download_base_url)
    if status != 0:
        return status
    return check_repo_images(paths)


def ensure_repo_runtime_images(paths: BuildPaths) -> int:
    if check_repo_images(paths) != 0:
        return 1
    archive = paths.repo_hard_disk_image_archive
    runtime_image = paths.repo_runtime_hard_disk_image
    if runtime_image.exists() and runtime_image.stat().st_size > 0:
        if runtime_image.stat().st_mtime_ns >= archive.stat().st_mtime_ns:
            return 0
    extract_image_snapshot(archive, runtime_image)
    return 0


def run_bootstrap_host(paths: BuildPaths) -> int:
    qemu_status = run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), "bootstrap-host"],
        cwd=paths.root,
    )
    if qemu_status != 0:
        return qemu_status
    return run_command(["docker", "info", "--format", "{{.ServerVersion}}"], cwd=paths.root)


def run_runtime(paths: BuildPaths, mode: str) -> int:
    if ensure_rebuilt_images(paths) != 0:
        return 1
    return run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), mode],
        cwd=paths.root,
        env=verify_environment(paths),
    )


def run_repo_runtime(paths: BuildPaths, mode: str = "run") -> int:
    if ensure_repo_runtime_images(paths) != 0:
        return 1
    return run_command(
        [sys.executable, str(paths.root / "tools" / "qemu_driver.py"), mode],
        cwd=paths.root,
        env=verify_environment(paths, source="repo"),
    )


def verify_repo_runtime(paths: BuildPaths) -> int:
    return run_repo_runtime(paths, mode="verify")


def check_reproducible_build(paths: BuildPaths) -> int:
    paths.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="repro-", dir=paths.out_dir) as tmp:
        snapshot_root = Path(tmp)
        runs: list[dict[str, dict[str, object]]] = []
        for index in (1, 2):
            status = run_build(paths)
            if status != 0:
                return status
            run_dir = snapshot_root / f"run-{index}"
            run_dir.mkdir(parents=True, exist_ok=True)
            boot_snapshot = run_dir / paths.boot_image.name
            disk_snapshot = run_dir / paths.hard_disk_image.name
            archive_snapshot = run_dir / paths.repo_hard_disk_image_archive.name
            shutil.copy2(paths.boot_image, boot_snapshot)
            shutil.copy2(paths.hard_disk_image, disk_snapshot)
            compress_image_snapshot(disk_snapshot, archive_snapshot)
            runs.append(
                {
                    "bootimage-0.12-hd": snapshot_record(boot_snapshot),
                    "hdc-0.12.img": snapshot_record(disk_snapshot),
                    "hdc-0.12.img.xz": snapshot_record(archive_snapshot),
                }
            )
    mismatches: list[str] = []
    first, second = runs
    for name in ("bootimage-0.12-hd", "hdc-0.12.img", "hdc-0.12.img.xz"):
        if first[name] != second[name]:
            mismatches.append(f"{name}: first={first[name]} second={second[name]}")
    if mismatches:
        print("Reproducible build check failed.", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  {mismatch}", file=sys.stderr)
        return 1
    print("Reproducible build check passed.")
    return 0


def backup_file(path: Path, backup_root: Path) -> Path | None:
    if not path.exists():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    target = backup_root / path.name
    shutil.copy2(path, target)
    return target


def restore_file(path: Path, backup: Path | None) -> None:
    if backup is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, path)


def verify_release_readback(paths: BuildPaths) -> int:
    try:
        repo_manifest_assets(load_repo_manifest(paths))
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Cannot verify release readback without a valid repo image manifest: {exc}", file=sys.stderr)
        return 1
    paths.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-readback-", dir=paths.out_dir) as tmp:
        backup_root = Path(tmp)
        repo_boot_backup = backup_file(paths.repo_boot_image, backup_root)
        repo_disk_backup = backup_file(paths.repo_hard_disk_image_archive, backup_root)
        repo_manifest_backup = backup_file(paths.repo_manifest, backup_root)
        status = 1
        try:
            if paths.repo_runtime_hard_disk_image.exists():
                paths.repo_runtime_hard_disk_image.unlink()
            status = fetch_release_images(paths)
            if status != 0:
                return status
            if paths.repo_runtime_hard_disk_image.exists():
                paths.repo_runtime_hard_disk_image.unlink()
            status = verify_repo_runtime(paths)
            if status == 0:
                print("Release readback verification passed.")
            return status
        finally:
            restore_file(paths.repo_boot_image, repo_boot_backup)
            restore_file(paths.repo_hard_disk_image_archive, repo_disk_backup)
            restore_file(paths.repo_manifest, repo_manifest_backup)
            if paths.repo_runtime_hard_disk_image.exists():
                paths.repo_runtime_hard_disk_image.unlink()


def build_and_run_repo_images(paths: BuildPaths, mode: str = "run") -> int:
    if run_build(paths) != 0:
        return 1
    if sync_repo_images(paths) != 0:
        return 1
    return run_repo_runtime(paths, mode=mode)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    paths = BuildPaths.from_root(repo_root())
    if args.command == "bootstrap-host":
        return run_bootstrap_host(paths)
    if args.command == "build":
        return run_build(paths)
    if args.command == "verify-repo-images":
        return verify_repo_runtime(paths)
    if args.command == "check-repo-images":
        return check_repo_images(paths)
    if args.command == "check-reproducible-build":
        return check_reproducible_build(paths)
    if args.command == "fetch-release-images":
        return fetch_release_images(paths)
    if args.command == "verify-release-readback":
        return verify_release_readback(paths)
    if args.command == "prepare-release-assets":
        return prepare_release_assets(
            paths,
            release_tag=args.release_tag,
            download_base_url=args.download_base_url,
        )
    if args.command == "run":
        return run_runtime(paths, mode="run")
    if args.command == "verify":
        return run_runtime(paths, mode="verify")
    if args.command == "run-repo-images":
        return run_repo_runtime(paths)
    if args.command == "run-repo-images-window":
        return run_repo_runtime(paths, mode="run-window")
    if args.command == "build-and-run-repo-images":
        return build_and_run_repo_images(paths)
    if args.command == "build-and-run-repo-images-window":
        return build_and_run_repo_images(paths, mode="run-window")
    return run_runtime(paths, mode="verify-userland")


if __name__ == "__main__":
    raise SystemExit(main())
