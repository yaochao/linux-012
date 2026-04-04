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


if __name__ == "__main__":
    unittest.main()
