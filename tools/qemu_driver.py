from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DriverPaths:
    root: Path
    boot_image: Path
    root_image: Path
    out_dir: Path
    monitor_socket: Path
    pidfile: Path
    vga_dump: Path

    @classmethod
    def from_root(cls, root: Path) -> "DriverPaths":
        out_dir = root / "out" / "verify"
        return cls(
            root=root,
            boot_image=root / "vendor" / "images" / "bootimage-0.12",
            root_image=root / "vendor" / "images" / "rootimage-0.12",
            out_dir=out_dir,
            monitor_socket=out_dir / "monitor.sock",
            pidfile=out_dir / "qemu.pid",
            vga_dump=out_dir / "vga.bin",
        )


def build_qemu_command(paths: DriverPaths, mode: str, qemu_bin: str) -> list[str]:
    command = [
        qemu_bin,
        "-m",
        "16M",
        "-boot",
        "a",
        "-drive",
        f"file={paths.boot_image},format=raw,if=floppy,index=0",
        "-drive",
        f"file={paths.root_image},format=raw,if=floppy,index=1",
        "-k",
        "en-us",
    ]
    if mode == "interactive":
        command.extend(["-display", "curses"])
    else:
        command.extend(
            [
                "-display",
                "none",
                "-monitor",
                f"unix:{paths.monitor_socket},server=on,wait=off",
                "-pidfile",
                str(paths.pidfile),
            ]
        )
    return command


def decode_vga_text_buffer(data: bytes) -> list[str]:
    chars = []
    for index in range(0, min(len(data), 4000), 2):
        byte = data[index]
        chars.append(chr(byte) if 32 <= byte <= 126 else " ")
    return ["".join(chars[offset : offset + 80]).rstrip() for offset in range(0, 2000, 80)]


def find_stable_prompt(history: list[list[str]]) -> str | None:
    if len(history) < 3:
        return None
    tail = history[-3:]
    if tail[0] != tail[1] or tail[1] != tail[2]:
        return None
    for line in reversed(tail[-1]):
        stripped = line.rstrip()
        if stripped.endswith("#") or stripped.endswith("$"):
            return stripped
    return None


def verification_succeeded(final_lines: list[str], baseline_prompt: str) -> bool:
    compact = [line.rstrip() for line in final_lines if line.strip()]
    try:
        command_index = compact.index(f"{baseline_prompt} ls")
    except ValueError:
        return False
    if compact[-1] != baseline_prompt:
        return False
    return any(line and line != f"{baseline_prompt} ls" for line in compact[command_index + 1 : -1])
