import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "README.md",
            ROOT / "rebuild" / "README.md",
            ROOT / "rebuild" / "Dockerfile",
            ROOT / "rebuild" / "driver.py",
            ROOT / "rebuild" / "container" / "build_images.sh",
            ROOT / "rebuild" / "tools" / "aout_pack.py",
            ROOT / "rebuild" / "patches" / "linux-0.12",
            ROOT / "rebuild" / "rootfs",
            ROOT / "rebuild" / "rootfs" / "manifest",
            ROOT / "rebuild" / "userland" / "include" / "linux012.h",
            ROOT / "rebuild" / "userland" / "src" / "crt0.S",
            ROOT / "rebuild" / "userland" / "src" / "lib.c",
            ROOT / "rebuild" / "userland" / "src" / "sh.c",
            ROOT / "rebuild" / "userland" / "src" / "ls.c",
            ROOT / "rebuild" / "out",
            ROOT / "scripts" / "bootstrap-host.sh",
            ROOT / "scripts" / "run.sh",
            ROOT / "scripts" / "verify.sh",
            ROOT / "scripts" / "bootstrap-host.ps1",
            ROOT / "scripts" / "run.ps1",
            ROOT / "scripts" / "verify.ps1",
            ROOT / "scripts" / "bootstrap-host.cmd",
            ROOT / "scripts" / "run.cmd",
            ROOT / "scripts" / "verify.cmd",
            ROOT / "vendor" / "README.md",
            ROOT / "vendor" / "src",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
