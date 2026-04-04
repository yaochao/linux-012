from __future__ import annotations

import argparse
import os
import shlex
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROMPT_TOKEN = "(qemu)"
BOOT_PROMPT = "Press <RETURN> to see SVGA-modes available or any other key to continue."
VGA_ADDRESS = "0xb8000"
VGA_BYTES = 4000
FLOPPY_BYTES = 1474560
VERIFY_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 1.0


@dataclass(frozen=True)
class DriverPaths:
    root: Path
    boot_source_image: Path
    hard_disk_image: Path
    out_dir: Path
    boot_floppy_image: Path
    monitor_socket: Path
    pidfile: Path
    vga_dump: Path
    qemu_log: Path
    monitor_log: Path
    screen_text: Path

    @classmethod
    def from_root(cls, root: Path, session: str = "verify") -> "DriverPaths":
        out_dir = root / "out" / session
        return cls(
            root=root,
            boot_source_image=root / "vendor" / "images" / "bootimage-0.12-hd",
            hard_disk_image=root / "vendor" / "images" / "hdc-0.12.img",
            out_dir=out_dir,
            boot_floppy_image=out_dir / "boot.img",
            monitor_socket=out_dir / "m.sock",
            pidfile=out_dir / "q.pid",
            vga_dump=out_dir / "v.bin",
            qemu_log=out_dir / "q.log",
            monitor_log=out_dir / "m.log",
            screen_text=out_dir / "screen.txt",
        )


def build_qemu_command(paths: DriverPaths, mode: str, qemu_bin: str) -> list[str]:
    command = [
        qemu_bin,
        "-m",
        "16M",
        "-boot",
        "a",
        "-no-reboot",
        "-snapshot",
        "-drive",
        f"file={paths.boot_floppy_image},format=raw,if=floppy,index=0",
        "-drive",
        f"file={paths.hard_disk_image},format=raw,if=ide,index=0",
        "-k",
        "en-us",
        "-monitor",
        f"unix:{paths.monitor_socket},server=on,wait=off",
        "-pidfile",
        str(paths.pidfile),
    ]
    if mode == "interactive":
        command.extend(["-display", "curses"])
    else:
        command.extend(["-display", "none"])
    return command


def screen_contains(lines: list[str], needle: str) -> bool:
    lowered = needle.lower()
    return any(lowered in line.lower() for line in lines)


def decode_vga_text_buffer(data: bytes) -> list[str]:
    chars = []
    for index in range(0, min(len(data), VGA_BYTES), 2):
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


def ensure_boot_floppy_image(source_image: Path, target_image: Path) -> None:
    data = source_image.read_bytes()
    if len(data) > FLOPPY_BYTES:
        raise ValueError(f"Boot image is too large for a 1.44MB floppy: {source_image}")
    target_image.write_bytes(data + (b"\x00" * (FLOPPY_BYTES - len(data))))


def decide_next_keys(
    lines: list[str],
    baseline_prompt: str | None,
    ls_sent: bool,
    boot_prompt_confirmed: bool = False,
    send_ls: bool = True,
) -> list[str]:
    if not boot_prompt_confirmed and screen_contains(lines, BOOT_PROMPT):
        return ["spc"]
    if send_ls and baseline_prompt and not ls_sent and any(line.rstrip() == baseline_prompt for line in lines):
        return ["l", "s", "ret"]
    return []


def verification_succeeded(final_lines: list[str], baseline_prompt: str) -> bool:
    compact = [line.rstrip() for line in final_lines if line.strip()]
    try:
        command_index = compact.index(f"{baseline_prompt} ls")
    except ValueError:
        return False
    if compact[-1] != baseline_prompt:
        return False
    return any(line and line != f"{baseline_prompt} ls" for line in compact[command_index + 1 : -1])


class HMPClient:
    def __init__(self, socket_path: Path, log_path: Path) -> None:
        self.socket_path = socket_path
        self.log_path = log_path
        self.sock: socket.socket | None = None

    def connect(self, timeout: float) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.socket_path.exists():
                time.sleep(0.2)
                continue
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect(str(self.socket_path))
            except OSError:
                time.sleep(0.2)
                continue
            self.sock = sock
            output = self._read_until_prompt(timeout=2.0)
            if PROMPT_TOKEN not in output:
                self._send_raw("\n")
                self._read_until_prompt(timeout=2.0)
            return
        raise TimeoutError(f"Timed out waiting for monitor socket: {self.socket_path}")

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def command(self, text: str, timeout: float = 5.0) -> str:
        self._send_raw(f"{text}\n")
        return self._read_until_prompt(timeout=timeout)

    def _send_raw(self, text: str) -> None:
        if self.sock is None:
            raise RuntimeError("Monitor socket is not connected")
        payload = text.encode("utf-8")
        self.sock.sendall(payload)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f">>> {text}")

    def _read_until_prompt(self, timeout: float) -> str:
        if self.sock is None:
            raise RuntimeError("Monitor socket is not connected")
        deadline = time.time() + timeout
        chunks: list[bytes] = []
        while time.time() < deadline:
            try:
                data = self.sock.recv(4096)
            except socket.timeout:
                if PROMPT_TOKEN in b"".join(chunks).decode("utf-8", errors="replace"):
                    break
                continue
            if not data:
                break
            chunks.append(data)
            text = b"".join(chunks).decode("utf-8", errors="replace")
            if PROMPT_TOKEN in text:
                break
        output = b"".join(chunks).decode("utf-8", errors="replace")
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(output)
        return output


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def prepare_output_dir(paths: DriverPaths) -> None:
    paths.out_dir.mkdir(parents=True, exist_ok=True)
    for artifact in (
        paths.boot_floppy_image,
        paths.monitor_socket,
        paths.pidfile,
        paths.vga_dump,
        paths.qemu_log,
        paths.monitor_log,
        paths.screen_text,
    ):
        if artifact.exists():
            artifact.unlink()


def prepare_runtime_assets(paths: DriverPaths) -> None:
    prepare_output_dir(paths)
    ensure_boot_floppy_image(source_image=paths.boot_source_image, target_image=paths.boot_floppy_image)


def monitor_file_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def send_keys(client: HMPClient, keys: list[str], delay: float = 0.15) -> None:
    for key in keys:
        client.command(f"sendkey {key}")
        time.sleep(delay)


def snapshot_screen(client: HMPClient, paths: DriverPaths) -> list[str]:
    dump_path = monitor_file_path(paths.vga_dump, paths.root)
    client.command(f"pmemsave {VGA_ADDRESS} {VGA_BYTES} {dump_path}")
    data = paths.vga_dump.read_bytes()
    lines = decode_vga_text_buffer(data)
    paths.screen_text.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def launch_qemu(paths: DriverPaths, qemu_bin: str, mode: str) -> subprocess.Popen[bytes]:
    command = build_qemu_command(paths=paths, mode=mode, qemu_bin=qemu_bin)
    if mode == "interactive":
        return subprocess.Popen(command, cwd=paths.root)
    log_handle = paths.qemu_log.open("wb")
    return subprocess.Popen(
        command,
        cwd=paths.root,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )


def drive_to_shell(paths: DriverPaths, qemu_bin: str, mode: str, send_ls: bool) -> tuple[int, str | None]:
    prepare_runtime_assets(paths)
    process = launch_qemu(paths=paths, qemu_bin=qemu_bin, mode=mode)
    client = HMPClient(paths.monitor_socket, paths.monitor_log)
    history: list[list[str]] = []
    baseline_prompt: str | None = None
    boot_prompt_confirmed = False
    ls_sent = False
    last_lines: list[str] = []
    try:
        client.connect(timeout=30.0)
        deadline = time.time() + VERIFY_TIMEOUT_SECONDS
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"QEMU exited early with status {process.returncode}")
            lines = snapshot_screen(client, paths)
            last_lines = lines
            visible = [line.rstrip() for line in lines if line.strip()]
            if visible:
                history.append(visible)
                history = history[-6:]
            if baseline_prompt is None:
                baseline_prompt = find_stable_prompt(history)
            keys = decide_next_keys(
                lines,
                baseline_prompt=baseline_prompt,
                ls_sent=ls_sent,
                boot_prompt_confirmed=boot_prompt_confirmed,
                send_ls=send_ls,
            )
            if keys:
                if keys == ["spc"]:
                    boot_prompt_confirmed = True
                elif keys == ["l", "s", "ret"]:
                    ls_sent = True
                send_keys(client, keys)
                time.sleep(1.0)
                continue
            if baseline_prompt and not send_ls:
                return 0, baseline_prompt
            if baseline_prompt and ls_sent and verification_succeeded(lines, baseline_prompt):
                return 0, baseline_prompt
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError("Timed out waiting for Linux 0.12 to boot")
    except Exception as exc:
        if last_lines:
            paths.screen_text.write_text("\n".join(last_lines) + "\n", encoding="utf-8")
        print(f"Verification failed: {exc}", file=sys.stderr)
        print(f"Artifacts: {paths.out_dir}", file=sys.stderr)
        return 1, baseline_prompt
    finally:
        client.close()
        if mode != "interactive" and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)


def automate_verification(paths: DriverPaths, qemu_bin: str) -> int:
    status, baseline_prompt = drive_to_shell(paths=paths, qemu_bin=qemu_bin, mode="verify", send_ls=True)
    if status != 0:
        return status
    print("Linux 0.12 boot verified and `ls` succeeded.")
    if baseline_prompt:
        print(f"Prompt: {baseline_prompt}")
    print(f"Screen capture: {paths.screen_text}")
    return 0


def run_interactive(paths: DriverPaths, qemu_bin: str) -> int:
    status, _ = drive_to_shell(paths=paths, qemu_bin=qemu_bin, mode="interactive", send_ls=False)
    if status != 0:
        return status
    pid = int(paths.pidfile.read_text(encoding="utf-8").strip())
    try:
        _, wait_status = os.waitpid(pid, 0)
    except ChildProcessError:
        return 0
    return os.waitstatus_to_exitcode(wait_status)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["run", "verify"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--qemu-bin", default="qemu-system-i386")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    session = "run" if args.mode == "run" else "verify"
    mode = "interactive" if args.mode == "run" else "verify"
    paths = DriverPaths.from_root(repo_root(), session=session)
    command = build_qemu_command(paths=paths, mode=mode, qemu_bin=args.qemu_bin)
    if args.dry_run:
        print(f"boot source: {paths.boot_source_image}")
        print(" ".join(shlex.quote(part) for part in command))
        return 0
    if args.mode == "run":
        return run_interactive(paths=paths, qemu_bin=args.qemu_bin)
    return automate_verification(paths=paths, qemu_bin=args.qemu_bin)


if __name__ == "__main__":
    raise SystemExit(main())
