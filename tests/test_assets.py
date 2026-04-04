import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AssetTest(unittest.TestCase):
    def test_vendor_assets_exist_and_are_non_empty(self) -> None:
        assets = [
            ROOT / "vendor" / "src" / "linux-0.12.tar.gz",
            ROOT / "vendor" / "images" / "bootimage-0.12-hd",
            ROOT / "vendor" / "images" / "hdc-0.12.img",
        ]

        for asset in assets:
            self.assertTrue(asset.exists(), asset)
            self.assertGreater(asset.stat().st_size, 0, asset)


if __name__ == "__main__":
    unittest.main()
