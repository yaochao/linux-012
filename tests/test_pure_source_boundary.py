import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class BoundaryTest(unittest.TestCase):
    def test_imported_runtime_images_are_absent(self) -> None:
        forbidden = [
            ROOT / "vendor" / "images",
            ROOT / "rebuild" / "rootfs" / "base.tar",
            ROOT / "rebuild" / "container" / "capture_rootfs.sh",
        ]

        for path in forbidden:
            self.assertFalse(path.exists(), path)

    def test_build_pipeline_does_not_reference_imported_runtime_assets(self) -> None:
        build_script = (ROOT / "rebuild" / "container" / "build_images.sh").read_text(encoding="utf-8")

        self.assertNotIn("vendor/images", build_script)
        self.assertNotIn("base.tar", build_script)
        self.assertNotIn("capture_rootfs", build_script)


if __name__ == "__main__":
    unittest.main()
