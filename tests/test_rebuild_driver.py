import hashlib
import json
import pathlib
import tempfile
import unittest

from rebuild.driver import (
    BuildPaths,
    check_repo_images,
    docker_build_command,
    docker_run_command,
    ensure_repo_runtime_images,
    fetch_release_images,
    parse_args,
    prepare_release_assets,
    sync_repo_images,
    verify_environment,
)


class RebuildDriverTest(unittest.TestCase):
    def test_build_paths_use_rebuild_directory(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        self.assertEqual(root / "rebuild", paths.rebuild_dir)
        self.assertEqual(root / "rebuild" / "out" / "images" / "bootimage-0.12-hd", paths.boot_image)
        self.assertEqual(root / "rebuild" / "out" / "images" / "hdc-0.12.img", paths.hard_disk_image)
        self.assertEqual(root / "images", paths.repo_images_dir)
        self.assertEqual(root / "images" / "bootimage-0.12-hd", paths.repo_boot_image)
        self.assertEqual(root / "images" / "hdc-0.12.img.xz", paths.repo_hard_disk_image_archive)
        self.assertEqual(root / "images" / "manifest.json", paths.repo_manifest)
        self.assertEqual(root / "out" / "repo-images" / "hdc-0.12.img", paths.repo_runtime_hard_disk_image)

    def test_docker_run_command_uses_linux_amd64_and_privileged_mode(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        command = docker_run_command(paths, script="rebuild/container/build_images.sh")

        self.assertIn("--platform", command)
        self.assertIn("linux/amd64", command)
        self.assertIn("--privileged", command)
        self.assertTrue(any(str(root) in item for item in command))

    def test_docker_build_command_points_at_rebuild_dockerfile(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        command = docker_build_command(paths)

        self.assertIn("-f", command)
        self.assertIn(str(paths.rebuild_dir / "Dockerfile"), command)
        self.assertEqual(str(root), command[-1])

    def test_parse_args_supports_bootstrap_build_run_verify(self) -> None:
        for command in (
            "bootstrap-host",
            "build",
            "run",
            "verify",
            "verify-userland",
            "check-repo-images",
            "fetch-release-images",
            "prepare-release-assets",
            "run-repo-images",
            "build-and-run-repo-images",
            "run-repo-images-window",
            "build-and-run-repo-images-window",
        ):
            self.assertEqual(command, parse_args([command]).command)

    def test_parse_args_supports_release_asset_metadata(self) -> None:
        args = parse_args(
            [
                "prepare-release-assets",
                "--release-tag",
                "v9.9.9",
                "--download-base-url",
                "https://example.invalid/releases/download/v9.9.9",
            ]
        )

        self.assertEqual("prepare-release-assets", args.command)
        self.assertEqual("v9.9.9", args.release_tag)
        self.assertEqual("https://example.invalid/releases/download/v9.9.9", args.download_base_url)

    def test_verify_environment_points_runtime_at_rebuild_outputs(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        env = verify_environment(paths)

        self.assertEqual(str(paths.boot_image), env["LINUX012_BOOT_SOURCE_IMAGE"])
        self.assertEqual(str(paths.hard_disk_image), env["LINUX012_HARD_DISK_IMAGE"])

    def test_repo_environment_points_runtime_at_repo_images(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        env = verify_environment(paths, source="repo")

        self.assertEqual(str(paths.repo_boot_image), env["LINUX012_BOOT_SOURCE_IMAGE"])
        self.assertEqual(str(paths.repo_runtime_hard_disk_image), env["LINUX012_HARD_DISK_IMAGE"])

    def test_sync_repo_images_compresses_repo_hard_disk_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            paths = BuildPaths.from_root(root)
            paths.images_dir.mkdir(parents=True)
            paths.repo_images_dir.mkdir(parents=True)
            paths.boot_image.write_bytes(b"boot")
            paths.hard_disk_image.write_bytes(b"disk" * 4096)

            status = sync_repo_images(paths)

            self.assertEqual(0, status)
            self.assertEqual(b"boot", paths.repo_boot_image.read_bytes())
            self.assertTrue(paths.repo_hard_disk_image_archive.exists())
            self.assertGreater(paths.repo_hard_disk_image_archive.stat().st_size, 0)
            self.assertTrue(paths.repo_manifest.exists())
            self.assertFalse((paths.repo_images_dir / "hdc-0.12.img").exists())

    def test_ensure_repo_runtime_images_extracts_repo_disk_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            paths = BuildPaths.from_root(root)
            paths.repo_images_dir.mkdir(parents=True)
            paths.repo_boot_image.write_bytes(b"boot")
            paths.repo_runtime_hard_disk_image.parent.mkdir(parents=True)
            paths.repo_runtime_hard_disk_image.write_bytes(b"stale")
            paths.repo_runtime_hard_disk_image.unlink()
            paths.boot_image.parent.mkdir(parents=True, exist_ok=True)
            paths.hard_disk_image.parent.mkdir(parents=True, exist_ok=True)
            paths.boot_image.write_bytes(b"boot")
            paths.hard_disk_image.write_bytes(b"disk" * 4096)
            self.assertEqual(0, sync_repo_images(paths))

            status = ensure_repo_runtime_images(paths)

            self.assertEqual(0, status)
            self.assertEqual(b"disk" * 4096, paths.repo_runtime_hard_disk_image.read_bytes())

    def test_check_repo_images_validates_repo_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            paths = BuildPaths.from_root(root)
            paths.repo_images_dir.mkdir(parents=True)
            boot = b"boot"
            disk = b"disk-image"
            paths.repo_boot_image.write_bytes(boot)
            paths.repo_hard_disk_image_archive.write_bytes(disk)
            paths.repo_manifest.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "release_tag": "v1.0.0",
                        "download_base_url": "https://example.invalid/releases/v1.0.0",
                        "assets": {
                            "bootimage-0.12-hd": {
                                "sha256": hashlib.sha256(boot).hexdigest(),
                                "size": len(boot),
                            },
                            "hdc-0.12.img.xz": {
                                "sha256": hashlib.sha256(disk).hexdigest(),
                                "size": len(disk),
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(0, check_repo_images(paths))

    def test_fetch_release_images_downloads_assets_declared_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            release_dir = root / "release"
            release_dir.mkdir()
            boot = b"boot"
            disk = b"disk-image"
            (release_dir / "bootimage-0.12-hd").write_bytes(boot)
            (release_dir / "hdc-0.12.img.xz").write_bytes(disk)
            paths = BuildPaths.from_root(root)
            paths.repo_images_dir.mkdir(parents=True)
            paths.repo_manifest.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "release_tag": "v1.0.0",
                        "download_base_url": release_dir.as_uri(),
                        "assets": {
                            "bootimage-0.12-hd": {
                                "sha256": hashlib.sha256(boot).hexdigest(),
                                "size": len(boot),
                            },
                            "hdc-0.12.img.xz": {
                                "sha256": hashlib.sha256(disk).hexdigest(),
                                "size": len(disk),
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(0, fetch_release_images(paths))
            self.assertEqual(boot, paths.repo_boot_image.read_bytes())
            self.assertEqual(disk, paths.repo_hard_disk_image_archive.read_bytes())

    def test_prepare_release_assets_writes_manifest_for_requested_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            paths = BuildPaths.from_root(root)
            paths.images_dir.mkdir(parents=True)
            paths.boot_image.write_bytes(b"boot")
            paths.hard_disk_image.write_bytes(b"disk" * 4096)

            status = prepare_release_assets(
                paths,
                release_tag="v9.9.9",
                download_base_url="https://example.invalid/releases/download/v9.9.9",
            )

            self.assertEqual(0, status)
            manifest = json.loads(paths.repo_manifest.read_text(encoding="utf-8"))
            self.assertEqual("v9.9.9", manifest["release_tag"])
            self.assertEqual(
                "https://example.invalid/releases/download/v9.9.9",
                manifest["download_base_url"],
            )
            self.assertTrue(paths.repo_boot_image.exists())
            self.assertTrue(paths.repo_hard_disk_image_archive.exists())

    def test_build_script_references_source_tarball_userland_and_manifest(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertIn("vendor/src/linux-0.12.tar.gz", text)
        self.assertIn("rebuild/patches/linux-0.12", text)
        self.assertIn("rebuild/userland", text)
        self.assertIn("rebuild/tools/aout_pack.py", text)
        self.assertIn("rebuild/rootfs/manifest/directories.txt", text)
        self.assertIn("rebuild/rootfs/manifest/devices.tsv", text)
        self.assertIn("bootimage-0.12-hd", text)
        self.assertIn("guestfish", text)
        self.assertIn("/tmp/linux-012-rebuild-work", text)
        self.assertNotIn("base.tar", text)
        self.assertNotIn("mount -t minix", text)

    def test_build_script_formats_minix_v1_with_14_character_names(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertIn("mkfs.minix -1 -n14", text)

    def test_build_script_stages_rootfs_inside_container_workdir_for_device_nodes(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertIn('STAGING_DIR="$CONTAINER_WORK_ROOT/rootfs"', text)
        self.assertIn('USERLAND_BUILD="$CONTAINER_WORK_ROOT/userland"', text)

    def test_dockerfile_installs_multilib_userland_build_dependencies(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "Dockerfile").read_text()

        self.assertIn("gcc-multilib", text)
        self.assertIn("libc6-dev-i386", text)
        self.assertIn("libguestfs-tools", text)
        self.assertIn("linux-image-kvm", text)

    def test_modern_gcc_patch_disables_pie_for_kernel_objects(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "patches" / "linux-0.12" / "0003-modern-inline-semantics.patch").read_text()

        self.assertIn("-fno-pie", text)
        self.assertIn("-fno-pic", text)


if __name__ == "__main__":
    unittest.main()
