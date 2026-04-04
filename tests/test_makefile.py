import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MakefileTest(unittest.TestCase):
    def test_makefile_declares_shortcuts_for_common_repo_tasks(self) -> None:
        makefile = ROOT / "Makefile"

        self.assertTrue(makefile.exists(), makefile)
        text = makefile.read_text(encoding="utf-8")
        for target in (
            "help:",
            "bootstrap-host:",
            "build:",
            "run:",
            "run-window:",
            "verify:",
            "verify-userland:",
            "check-images:",
            "fetch-release-images:",
            "repro-check:",
            "release-readback:",
        ):
            self.assertIn(target, text)


if __name__ == "__main__":
    unittest.main()
