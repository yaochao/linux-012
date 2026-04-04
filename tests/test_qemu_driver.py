import pathlib
import unittest

from tools.qemu_driver import (
    DriverPaths,
    build_qemu_command,
    decode_vga_text_buffer,
    find_stable_prompt,
    verification_succeeded,
)


class QemuDriverTest(unittest.TestCase):
    def test_build_qemu_command_for_interactive_mode_uses_curses(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = DriverPaths.from_root(root)

        command = build_qemu_command(paths=paths, mode="interactive", qemu_bin="qemu-system-i386")

        self.assertIn("-display", command)
        self.assertIn("curses", command)
        self.assertIn("16M", command)
        self.assertTrue(any(str(paths.boot_image) in item for item in command))
        self.assertTrue(any(str(paths.root_image) in item for item in command))

    def test_decode_vga_text_buffer_returns_visible_text(self) -> None:
        data = bytearray(b" " * 4000)
        data[0] = ord("r")
        data[2] = ord("o")
        data[4] = ord("o")
        data[6] = ord("t")
        data[8] = ord("#")

        lines = decode_vga_text_buffer(bytes(data))

        self.assertEqual("root#", lines[0].rstrip())

    def test_find_stable_prompt_requires_three_identical_snapshots(self) -> None:
        history = [
            ["login: "],
            ["root# "],
            ["root# "],
            ["root# "],
        ]

        self.assertEqual("root#", find_stable_prompt(history))

    def test_verification_succeeded_requires_prompt_return(self) -> None:
        baseline = "root#"
        final_lines = [
            "Linux 0.12",
            "root# ls",
            "bin dev etc tmp usr",
            "root#",
        ]

        self.assertTrue(verification_succeeded(final_lines, baseline))


if __name__ == "__main__":
    unittest.main()
