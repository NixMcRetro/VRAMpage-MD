#!/usr/bin/env python3
"""Embed the pinned Musashi binary notice in a WebAssembly custom section."""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile


MAGIC = b"\0asm\x01\0\0\0"
SECTION_NAME = "license.Musashi"
_NOTICE = re.compile(
    rb"/\* ={8,} \*/\r?\n"
    rb"/\* =+ LICENSING & COPYRIGHT =+ \*/\r?\n"
    rb"/\* ={8,} \*/\r?\n"
    rb"/\*.*?\*/",
    re.DOTALL,
)


class NoticeError(ValueError):
    """Raised when the module or pinned notice does not match expectations."""


def _read_uleb(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for index in range(5):
        if offset >= len(data):
            raise NoticeError("Truncated WebAssembly section length.")
        byte = data[offset]
        offset += 1
        if index == 4 and byte & 0xF0:
            raise NoticeError("WebAssembly section length exceeds u32.")
        value |= (byte & 0x7F) << (index * 7)
        if not byte & 0x80:
            return value, offset
    raise NoticeError("Malformed WebAssembly unsigned LEB128 value.")


def _uleb(value: int) -> bytes:
    if value < 0 or value > 0xFFFFFFFF:
        raise NoticeError("WebAssembly section length exceeds u32.")
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def musashi_notice(header: bytes) -> bytes:
    """Return the unchanged pinned Musashi licensing/copyright comment."""
    match = _NOTICE.search(header)
    if not match:
        raise NoticeError("Pinned m68k.h Musashi licensing comment was not found.")
    notice = match.group()
    required = (
        b"MUSASHI", b"Copyright Karl Stenerud", b"binary files",
        b"All other licensing terms must be negotiated",
    )
    if not all(marker in notice for marker in required):
        raise NoticeError("The extracted notice is not the expected Musashi license block.")
    return notice


def _sections(module: bytes):
    if not module.startswith(MAGIC):
        raise NoticeError("Input is not a WebAssembly 1 module.")
    offset = len(MAGIC)
    while offset < len(module):
        start = offset
        section_id = module[offset]
        offset += 1
        size, payload_start = _read_uleb(module, offset)
        end = payload_start + size
        if end > len(module):
            raise NoticeError("WebAssembly section extends beyond end of module.")
        name = None
        payload = module[payload_start:end]
        if section_id == 0:
            name_size, name_start = _read_uleb(module, payload_start)
            name_end = name_start + name_size
            if name_end > end:
                raise NoticeError("WebAssembly custom-section name exceeds its section.")
            try:
                name = module[name_start:name_end].decode("utf-8")
            except UnicodeDecodeError as error:
                raise NoticeError("WebAssembly custom-section name is not UTF-8.") from error
        yield start, end, section_id, name, payload
        offset = end


def append_notice(module: bytes, header: bytes) -> bytes:
    """Append the pinned notice once; accept only an already-identical section."""
    notice = musashi_notice(header)
    matches = [section for section in _sections(module)
               if section[2] == 0 and section[3] == SECTION_NAME]
    if len(matches) > 1:
        raise NoticeError("WebAssembly module contains duplicate Musashi notice sections.")
    if matches:
        _start, _end, _section_id, _name, payload = matches[0]
        name_size, name_start = _read_uleb(payload, 0)
        name_end = name_start + name_size
        if payload[name_end:] != notice:
            raise NoticeError("WebAssembly module contains a conflicting Musashi notice section.")
        return module

    name = SECTION_NAME.encode("utf-8")
    payload = _uleb(len(name)) + name + notice
    section = b"\0" + _uleb(len(payload)) + payload
    return module + section


def remove_notice(module: bytes) -> bytes:
    """Remove exactly one Musashi section, preserving every other module byte."""
    matches = [section for section in _sections(module)
               if section[2] == 0 and section[3] == SECTION_NAME]
    if len(matches) != 1:
        raise NoticeError("Expected exactly one Musashi notice section to remove.")
    start, end, _section_id, _name, _payload = matches[0]
    return module[:start] + module[end:]


def embed_file(wasm_path: Path, header_path: Path) -> None:
    wasm_path, header_path = Path(wasm_path), Path(header_path)
    if wasm_path.is_symlink():
        raise NoticeError("Refusing to replace a symlink WebAssembly file.")
    original = wasm_path.read_bytes()
    updated = append_notice(original, header_path.read_bytes())
    if updated == original:
        return
    mode = stat.S_IMODE(wasm_path.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{wasm_path.name}.", dir=wasm_path.parent)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as output:
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, wasm_path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wasm", type=Path, help="WebAssembly file to update in place")
    parser.add_argument("m68k_header", type=Path, help="Pinned Musashi m68k.h source")
    args = parser.parse_args()
    embed_file(args.wasm, args.m68k_header)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, NoticeError) as error:
        parser = argparse.ArgumentParser()
        parser.error(str(error))
