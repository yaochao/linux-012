from __future__ import annotations

import argparse
import os
import shlex
import shutil
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
class HostPlatform:
    name: str
    interactive_display: str | None
    monitor_kind: str
    install_hint: str
    qemu_names: tuple[str, ...]


@dataclass(frozen=True)
class DriverPaths:
    root: Path
    platform: HostPlatform
    boot_source_image: Path
    hard_disk_image: Path
    out_dir: Path
    boot_floppy_image: Path
    monitor_address: str
    monitor_socket: Path | None
    monitor_host: str | None
    monitor_port: int | None
    pidfile: Path
    vga_dump: Path
    qemu_log: Path
    monitor_log: Path
    screen_text: Path

    @classmethod
    def from_root(
        cls,
        root: Path,
        session: str = "verify",
        platform: HostPlatform | None = None,
    ) -> "DriverPaths":
        host = platform or resolve_host_platform()
        out_dir = root / "out" / session
        monitor_socket: Path | None
        monitor_host: str | None
        monitor_port: int | None
        if host.monitor_kind == "unix":
            monitor_socket = out_dir / "m.sock"
            monitor_host = None
            monitor_port = None
            monitor_address = f"unix:{monitor_socket},server=on,wait=off"
        else:
            monitor_socket = None
            monitor_host = "127.0.0.1"
            monitor_port = pick_tcp_port(monitor_host)
            monitor_address = f"tcp:{monitor_host}:{monitor_port},server=on,wait=off"
        return cls(
            root=root,
            platform=host,
            boot_source_image=resolve_runtime_image(
                "LINUX012_BOOT_SOURCE_IMAGE",
                root / "vendor" / "images" / "bootimage-0.12-hd",
            ),
            hard_disk_image=resolve_runtime_image(
                "LINUX012_HARD_DISK_IMAGE",
                root / "vendor" / "images" / "hdc-0.12.img",
            ),
            out_dir=out_dir,
            boot_floppy_image=out_dir / "boot.img",
            monitor_address=monitor_address,
            monitor_socket=monitor_socket,
            monitor_host=monitor_host,
            monitor_port=monitor_port,
            pidfile=out_dir / "q.pid",
            vga_dump=out_dir / "v.bin",
            qemu_log=out_dir / "q.log",
            monitor_log=out_dir / "m.log",
            screen_text=out_dir / "screen.txt",
        )


def resolve_runtime_image(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser()


def resolve_host_platform(platform_name: str | None = None) -> HostPlatform:
    current = platform_name or sys.platform
    if current.startswith("darwin"):
        return HostPlatform(
            name="macos",
            interactive_display="curses",
            monitor_kind="unix",
            install_hint="brew install qemu",
            qemu_names=("qemu-system-i386",),
        )
    if current.startswith("linux"):
        return HostPlatform(
            name="linux",
            interactive_display="curses",
            monitor_kind="unix",
            install_hint="sudo apt update && sudo apt install -y qemu-system-x86",
            qemu_names=("qemu-system-i386",),
        )
    if current.startswith("win"):
        return HostPlatform(
            name="windows",
            interactive_display=None,
            monitor_kind="tcp",
            install_hint="Install QEMU for Windows, ensure qemu-system-i386.exe is on PATH, or set LINUX012_QEMU_BIN to its full path.",
            qemu_names=("qemu-system-i386.exe", "qemu-system-i386"),
        )
    raise RuntimeError(f"Unsupported host platform: {current}")


def pick_tcp_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.bind((host, 0))
        return int(candidate.getsockname()[1])


def windows_qemu_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("QEMU_HOME", "ProgramFiles", "ProgramFiles(x86)"):
        raw = os.environ.get(env_name)
        if not raw:
            continue
        base = Path(raw)
        if env_name == "QEMU_HOME":
            candidates.append(base / "qemu-system-i386.exe")
        else:
            candidates.append(base / "qemu" / "qemu-system-i386.exe")
    return candidates


def resolve_qemu_binary(explicit: str | None, platform: HostPlatform) -> str:
    override = explicit or os.environ.get("LINUX012_QEMU_BIN")
    if override:
        return override
    for name in platform.qemu_names:
        discovered = shutil.which(name)
        if discovered:
            return discovered
    if platform.name == "windows":
        for candidate in windows_qemu_candidates():
            if candidate.exists():
                return str(candidate)
    return platform.qemu_names[0]


def qemu_binary_exists(qemu_bin: str) -> bool:
    has_separator = os.sep in qemu_bin or (os.altsep is not None and os.altsep in qemu_bin)
    if has_separator:
        return Path(qemu_bin).exists()
    return shutil.which(qemu_bin) is not None


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
        paths.monitor_address,
        "-pidfile",
        str(paths.pidfile),
    ]
    if mode == "interactive":
        if paths.platform.interactive_display:
            command.extend(["-display", paths.platform.interactive_display])
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
    def __init__(self, paths: DriverPaths) -> None:
        self.paths = paths
        self.log_path = paths.monitor_log
        self.sock: socket.socket | None = None

    def connect(self, timeout: float) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                sock = self._open_socket()
            except OSError:
                time.sleep(0.2)
                continue
            self.sock = sock
            output = self._read_until_prompt(timeout=2.0)
            if PROMPT_TOKEN not in output:
                self._send_raw("\n")
                self._read_until_prompt(timeout=2.0)
            return
        raise TimeoutError(f"Timed out waiting for monitor endpoint: {self.paths.monitor_address}")

    def _open_socket(self) -> socket.socket:
        if self.paths.platform.monitor_kind == "unix":
            if self.paths.monitor_socket is None or not self.paths.monitor_socket.exists():
                raise OSError("Monitor socket not ready")
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(str(self.paths.monitor_socket))
            return sock
        if self.paths.monitor_host is None or self.paths.monitor_port is None:
            raise OSError("TCP monitor endpoint is incomplete")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect((self.paths.monitor_host, self.paths.monitor_port))
        return sock

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
    artifacts = [
        paths.boot_floppy_image,
        paths.pidfile,
        paths.vga_dump,
        paths.qemu_log,
        paths.monitor_log,
        paths.screen_text,
    ]
    if paths.monitor_socket is not None:
        artifacts.append(paths.monitor_socket)
    for artifact in artifacts:
        if artifact.exists():
            artifact.unlink()


def prepare_runtime_assets(paths: DriverPaths) -> None:
    prepare_output_dir(paths)
    ensure_boot_floppy_image(source_image=paths.boot_source_image, target_image=paths.boot_floppy_image)


def monitor_file_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


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


def drive_to_shell(
    paths: DriverPaths,
    qemu_bin: str,
    mode: str,
    send_ls: bool,
) -> tuple[int, str | None, subprocess.Popen[bytes] | None]:
    prepare_runtime_assets(paths)
    process = launch_qemu(paths=paths, qemu_bin=qemu_bin, mode=mode)
    client = HMPClient(paths)
    history: list[list[str]] = []
    baseline_prompt: str | None = None
    boot_prompt_confirmed = False
    ls_sent = False
    last_lines: list[str] = []
    keep_running = False
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
                keep_running = True
                return 0, baseline_prompt, process
            if baseline_prompt and ls_sent and verification_succeeded(lines, baseline_prompt):
                return 0, baseline_prompt, process
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError("Timed out waiting for Linux 0.12 to boot")
    except Exception as exc:
        if last_lines:
            paths.screen_text.write_text("\n".join(last_lines) + "\n", encoding="utf-8")
        print(f"Verification failed: {exc}", file=sys.stderr)
        print(f"Artifacts: {paths.out_dir}", file=sys.stderr)
        return 1, baseline_prompt, None
    finally:
        client.close()
        if not keep_running and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)


def automate_verification(paths: DriverPaths, qemu_bin: str) -> int:
    status, baseline_prompt, _ = drive_to_shell(paths=paths, qemu_bin=qemu_bin, mode="verify", send_ls=True)
    if status != 0:
        return status
    print("Linux 0.12 boot verified and `ls` succeeded.")
    if baseline_prompt:
        print(f"Prompt: {baseline_prompt}")
    print(f"Screen capture: {paths.screen_text}")
    return 0


def run_interactive(paths: DriverPaths, qemu_bin: str) -> int:
    status, _, process = drive_to_shell(paths=paths, qemu_bin=qemu_bin, mode="interactive", send_ls=False)
    if status != 0 or process is None:
        return status
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            return process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait(timeout=5.0)


def bootstrap_host(qemu_bin: str, platform: HostPlatform) -> int:
    if not qemu_binary_exists(qemu_bin):
        print(f"{platform.qemu_names[0]} not found. Install it with: {platform.install_hint}", file=sys.stderr)
        return 1
    completed = subprocess.run([qemu_bin, "--version"], check=False)
    return int(completed.returncode)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["bootstrap-host", "run", "verify"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--qemu-bin")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    platform = resolve_host_platform()
    qemu_bin = resolve_qemu_binary(args.qemu_bin, platform)
    if args.mode == "bootstrap-host":
        return bootstrap_host(qemu_bin, platform)
    session = "run" if args.mode == "run" else "verify"
    mode = "interactive" if args.mode == "run" else "verify"
    paths = DriverPaths.from_root(repo_root(), session=session, platform=platform)
    command = build_qemu_command(paths=paths, mode=mode, qemu_bin=qemu_bin)
    if args.dry_run:
        print(f"boot source: {paths.boot_source_image}")
        print(" ".join(shlex.quote(part) for part in command))
        return 0
    if not qemu_binary_exists(qemu_bin):
        print(f"{platform.qemu_names[0]} not found. Install it with: {platform.install_hint}", file=sys.stderr)
        return 1
    if args.mode == "run":
        return run_interactive(paths=paths, qemu_bin=qemu_bin)
    return automate_verification(paths=paths, qemu_bin=qemu_bin)


if __name__ == "__main__":
    raise SystemExit(main())
