import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AssetTest(unittest.TestCase):
    def test_vendor_assets_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "vendor" / "src" / "linux-0.12.tar.gz",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)

    def test_rebuild_rootfs_inputs_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "rebuild" / "rootfs" / "layout.sfdisk",
            ROOT / "rebuild" / "rootfs" / "manifest" / "directories.txt",
            ROOT / "rebuild" / "rootfs" / "manifest" / "devices.tsv",
            ROOT / "rebuild" / "rootfs" / "manifest" / "etc" / "rc",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)


if __name__ == "__main__":
    unittest.main()
