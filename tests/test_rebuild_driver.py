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
        self.assertTrue(any(str(root) in item for item in command))

    def test_docker_build_command_points_at_rebuild_dockerfile(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        command = docker_build_command(paths)

        self.assertIn("-f", command)
        self.assertIn(str(paths.rebuild_dir / "Dockerfile"), command)
        self.assertEqual(str(root), command[-1])

    def test_build_script_references_source_tarball_and_patch_directory(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertIn("vendor/src/linux-0.12.tar.gz", text)
        self.assertIn("rebuild/patches/linux-0.12", text)
        self.assertIn("bootimage-0.12-hd", text)
        self.assertIn("guestfish", text)
        self.assertIn("/tmp/linux-012-rebuild-work", text)
        self.assertNotIn("mount -t minix", text)

    def test_build_script_formats_minix_v1_with_14_character_names(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "build_images.sh").read_text()

        self.assertIn("mkfs.minix -1 -n14", text)

    def test_capture_script_uses_guestfish_for_minix_export(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "container" / "capture_rootfs.sh").read_text()

        self.assertIn("guestfish", text)
        self.assertIn("tar-out", text)
        self.assertNotIn("mount -t minix", text)

    def test_dockerfile_installs_libguestfs_tools(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "Dockerfile").read_text()

        self.assertIn("libguestfs-tools", text)
        self.assertIn("linux-image-kvm", text)

    def test_modern_gcc_patch_disables_pie_for_kernel_objects(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "rebuild" / "patches" / "linux-0.12" / "0003-modern-inline-semantics.patch").read_text()

        self.assertIn("-fno-pie", text)
        self.assertIn("-fno-pic", text)


if __name__ == "__main__":
    unittest.main()
