import pathlib
import tempfile
import unittest

from tools.qemu_driver import (
    DriverPaths,
    build_qemu_command,
    decide_next_keys,
    decode_vga_text_buffer,
    ensure_boot_floppy_image,
    find_stable_prompt,
    monitor_file_path,
    verification_succeeded,
)


class QemuDriverTest(unittest.TestCase):
    def test_build_qemu_command_for_interactive_mode_uses_curses_and_snapshot(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = DriverPaths.from_root(root)

        command = build_qemu_command(paths=paths, mode="interactive", qemu_bin="qemu-system-i386")

        self.assertIn("-display", command)
        self.assertIn("curses", command)
        self.assertIn("-snapshot", command)
        self.assertIn("16M", command)
        self.assertTrue(any(str(paths.boot_floppy_image) in item for item in command))
        self.assertTrue(any(str(paths.hard_disk_image) in item for item in command))

    def test_driver_paths_use_runtime_boot_image_and_short_monitor_names(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = DriverPaths.from_root(root)

        self.assertEqual(root / "vendor" / "images" / "bootimage-0.12-hd", paths.boot_source_image)
        self.assertEqual(root / "vendor" / "images" / "hdc-0.12.img", paths.hard_disk_image)
        self.assertEqual(root / "out" / "verify" / "boot.img", paths.boot_floppy_image)
        self.assertEqual(root / "out" / "verify" / "m.sock", paths.monitor_socket)

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
        baseline = "[/]#"
        final_lines = [
            "Linux 0.12",
            "[/]# ls",
            "bin dev etc tmp usr",
            "[/]#",
        ]

        self.assertTrue(verification_succeeded(final_lines, baseline))

    def test_decide_next_keys_handles_svga_prompt(self) -> None:
        lines = ["Press <RETURN> to see SVGA-modes available or any other key to continue."]

        self.assertEqual(["spc"], decide_next_keys(lines, baseline_prompt=None, ls_sent=False))

    def test_decide_next_keys_handles_shell_prompt(self) -> None:
        lines = ["[/]#"]

        self.assertEqual(["l", "s", "ret"], decide_next_keys(lines, baseline_prompt="[/]#", ls_sent=False))

    def test_decide_next_keys_skips_ls_when_verification_is_disabled(self) -> None:
        lines = ["[/]#"]

        self.assertEqual([], decide_next_keys(lines, baseline_prompt="[/]#", ls_sent=False, send_ls=False))

    def test_monitor_file_path_uses_repo_relative_path(self) -> None:
        root = pathlib.Path("/tmp/linux-012")
        paths = DriverPaths.from_root(root)

        self.assertEqual("out/verify/v.bin", monitor_file_path(paths.vga_dump, root))

    def test_ensure_boot_floppy_image_pads_boot_sector_image_to_full_floppy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "bootimage-0.12-hd"
            target = root / "boot.img"
            source.write_bytes(b"linux012")

            ensure_boot_floppy_image(source_image=source, target_image=target)

            self.assertEqual(1474560, target.stat().st_size)
            self.assertEqual(b"linux012", target.read_bytes()[:8])


if __name__ == "__main__":
    unittest.main()
