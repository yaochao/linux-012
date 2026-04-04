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

    def test_run_script_calls_python_driver_with_repo_images(self) -> None:
        text = (ROOT / "scripts" / "run.sh").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("run-repo-images", text)

    def test_run_window_script_calls_python_driver_with_repo_window_mode(self) -> None:
        text = (ROOT / "scripts" / "run-window.sh").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("run-repo-images-window", text)

    def test_windows_verify_powershell_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("verify", text)

    def test_windows_run_powershell_script_calls_python_driver_with_repo_images(self) -> None:
        text = (ROOT / "scripts" / "run.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("run-repo-images", text)

    def test_windows_run_window_powershell_script_calls_python_driver_with_repo_window_mode(self) -> None:
        text = (ROOT / "scripts" / "run-window.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("run-repo-images-window", text)

    def test_verify_userland_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify-userland.sh").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("verify-userland", text)

    def test_windows_verify_userland_powershell_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "verify-userland.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("verify-userland", text)

    def test_windows_run_batch_script_delegates_to_powershell(self) -> None:
        text = (ROOT / "scripts" / "run.cmd").read_text()

        self.assertIn("powershell", text.lower())
        self.assertIn("run.ps1", text)

    def test_windows_run_window_batch_script_delegates_to_powershell(self) -> None:
        text = (ROOT / "scripts" / "run-window.cmd").read_text()

        self.assertIn("powershell", text.lower())
        self.assertIn("run-window.ps1", text)

    def test_build_and_run_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "build-and-run.sh").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("build-and-run-repo-images", text)

    def test_build_and_run_window_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "build-and-run-window.sh").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("build-and-run-repo-images-window", text)

    def test_windows_build_and_run_powershell_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "build-and-run.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("build-and-run-repo-images", text)

    def test_windows_build_and_run_window_powershell_script_calls_python_driver(self) -> None:
        text = (ROOT / "scripts" / "build-and-run-window.ps1").read_text()

        self.assertIn("rebuild/driver.py", text)
        self.assertIn("build-and-run-repo-images-window", text)

    def test_windows_build_and_run_batch_script_delegates_to_powershell(self) -> None:
        text = (ROOT / "scripts" / "build-and-run.cmd").read_text()

        self.assertIn("powershell", text.lower())
        self.assertIn("build-and-run.ps1", text)

    def test_windows_build_and_run_window_batch_script_delegates_to_powershell(self) -> None:
        text = (ROOT / "scripts" / "build-and-run-window.cmd").read_text()

        self.assertIn("powershell", text.lower())
        self.assertIn("build-and-run-window.ps1", text)

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

    def test_driver_supports_verify_userland_dry_run(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "qemu_driver.py"), "verify-userland", "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("qemu-system-i386", result.stdout)
        self.assertIn("bootimage-0.12-hd", result.stdout)
        self.assertIn("hdc-0.12.img", result.stdout)


if __name__ == "__main__":
    unittest.main()
