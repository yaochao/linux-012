import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class LayoutTest(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected = [
            ROOT / "README.md",
            ROOT / ".github",
            ROOT / ".github" / "README.md",
            ROOT / ".github" / "README.en.md",
            ROOT / ".github" / "workflows",
            ROOT / ".github" / "workflows" / "README.md",
            ROOT / ".github" / "workflows" / "README.en.md",
            ROOT / ".github" / "workflows" / "ci.yml",
            ROOT / ".github" / "workflows" / "release.yml",
            ROOT / "images",
            ROOT / "images" / "bootimage-0.12-hd",
            ROOT / "images" / "hdc-0.12.img.xz",
            ROOT / "images" / "manifest.json",
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
            ROOT / "scripts" / "build-and-run.sh",
            ROOT / "scripts" / "build-and-run-window.sh",
            ROOT / "scripts" / "check-images.sh",
            ROOT / "scripts" / "fetch-release-images.sh",
            ROOT / "scripts" / "run.sh",
            ROOT / "scripts" / "run-window.sh",
            ROOT / "scripts" / "verify.sh",
            ROOT / "scripts" / "verify-userland.sh",
            ROOT / "scripts" / "bootstrap-host.ps1",
            ROOT / "scripts" / "build-and-run.ps1",
            ROOT / "scripts" / "build-and-run-window.ps1",
            ROOT / "scripts" / "check-images.ps1",
            ROOT / "scripts" / "fetch-release-images.ps1",
            ROOT / "scripts" / "run.ps1",
            ROOT / "scripts" / "run-window.ps1",
            ROOT / "scripts" / "verify.ps1",
            ROOT / "scripts" / "verify-userland.ps1",
            ROOT / "scripts" / "bootstrap-host.cmd",
            ROOT / "scripts" / "build-and-run.cmd",
            ROOT / "scripts" / "build-and-run-window.cmd",
            ROOT / "scripts" / "check-images.cmd",
            ROOT / "scripts" / "fetch-release-images.cmd",
            ROOT / "scripts" / "run.cmd",
            ROOT / "scripts" / "run-window.cmd",
            ROOT / "scripts" / "verify.cmd",
            ROOT / "scripts" / "verify-userland.cmd",
            ROOT / "vendor" / "README.md",
            ROOT / "vendor" / "src",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
        self.assertEqual([], missing)

    def test_tracked_directories_have_bilingual_readmes(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-tree", "-dr", "--name-only", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        excluded = {
            "rebuild/out",
        }
        directories = [ROOT]
        directories.extend(ROOT / entry for entry in tracked if entry and entry not in excluded)

        missing: list[str] = []
        for directory in directories:
            for name in ("README.md", "README.en.md"):
                path = directory / name
                if not path.exists():
                    missing.append(str(path.relative_to(ROOT)))

        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
