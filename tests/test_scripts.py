import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ScriptTest(unittest.TestCase):
    def test_bootstrap_host_fails_with_clear_message_when_qemu_missing(self) -> None:
        env = {"PATH": ""}
        result = subprocess.run(
            ["/bin/sh", str(ROOT / "scripts" / "bootstrap-host.sh")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("brew install qemu", result.stderr)

    def test_verify_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify.sh").read_text()
        self.assertIn("rebuild/driver.py", text)
        self.assertIn("verify", text)

    def test_windows_verify_powershell_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("verify", text)

    def test_windows_run_batch_script_delegates_to_powershell(self) -> None:
        text = (ROOT / "scripts" / "run.cmd").read_text()

        self.assertIn("powershell", text.lower())
        self.assertIn("run.ps1", text)

    def test_driver_supports_dry_run(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "qemu_driver.py"), "verify", "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("qemu-system-i386", result.stdout)
        self.assertIn("bootimage-0.12-hd", result.stdout)
        self.assertIn("hdc-0.12.img", result.stdout)
        self.assertIn("-snapshot", result.stdout)


if __name__ == "__main__":
    unittest.main()
