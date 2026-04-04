from __future__ import annotations

import argparse
from pathlib import Path
import struct
import subprocess
import tempfile


ZMAGIC = 0o413
TEXT_OFFSET = 1024


def build_exec_header(*, text_size: int, data_size: int, bss_size: int, entry: int) -> bytes:
    return struct.pack("<8I", ZMAGIC, text_size, data_size, bss_size, 0, entry, 0, 0)


def write_zmagic_image(output: Path, *, text: bytes, data: bytes, bss_size: int, entry: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    header = build_exec_header(text_size=len(text), data_size=len(data), bss_size=bss_size, entry=entry)
    padding = b"\x00" * (TEXT_OFFSET - len(header))
    output.write_bytes(header + padding + text + data)


def parse_nm_output(output: str) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        symbols[parts[2]] = int(parts[0], 16)
    return symbols


def pack_elf_to_zmagic(elf_path: Path, output: Path) -> None:
    nm_output = subprocess.run(
        ["nm", "-n", str(elf_path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    symbols = parse_nm_output(nm_output)
    required = ["_start", "__data_start", "__bss_start", "__bss_end"]
    missing = [name for name in required if name not in symbols]
    if missing:
        raise KeyError(f"Missing linker symbols: {', '.join(missing)}")

    with tempfile.TemporaryDirectory() as tempdir:
        flat_path = Path(tempdir) / "flat.bin"
        subprocess.run(["objcopy", "-O", "binary", str(elf_path), str(flat_path)], check=True)
        blob = flat_path.read_bytes()

    text_end = symbols["__data_start"]
    data_end = symbols["__bss_start"]
    bss_end = symbols["__bss_end"]
    write_zmagic_image(
        output,
        text=blob[:text_end],
        data=blob[text_end:data_end],
        bss_size=bss_end - data_end,
        entry=symbols["_start"],
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf_path", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pack_elf_to_zmagic(args.elf_path, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
