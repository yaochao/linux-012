import pathlib
import unittest

from rebuild.driver import BuildPaths, promotion_pairs, verify_environment


class RebuildPromoteTest(unittest.TestCase):
    def test_verify_environment_points_runtime_at_rebuild_outputs(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        env = verify_environment(paths)

        self.assertEqual(str(paths.boot_image), env["LINUX012_BOOT_SOURCE_IMAGE"])
        self.assertEqual(str(paths.hard_disk_image), env["LINUX012_HARD_DISK_IMAGE"])

    def test_promotion_pairs_copy_rebuilt_images_into_vendor_images(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = BuildPaths.from_root(root)

        pairs = promotion_pairs(paths)

        self.assertEqual(paths.boot_image, pairs[0][0])
        self.assertEqual(root / "vendor" / "images" / "bootimage-0.12-hd", pairs[0][1])
        self.assertEqual(paths.hard_disk_image, pairs[1][0])
        self.assertEqual(root / "vendor" / "images" / "hdc-0.12.img", pairs[1][1])


if __name__ == "__main__":
    unittest.main()
