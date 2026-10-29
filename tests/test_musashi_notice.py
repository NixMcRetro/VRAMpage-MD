"""The pinned Musashi source notice is embedded byte-for-byte in Wasm metadata."""
import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "embed_musashi_notice", ROOT / "scripts/embed_musashi_notice.py"
)
EMBED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EMBED)
HEADER = (ROOT / "site/source/runtime-profile/source/wasm-genplus/src/main/c/core/m68k/m68k.h")


class MusashiNoticeTests(unittest.TestCase):
    def setUp(self):
        self.header = HEADER.read_bytes() if HEADER.is_file() else (
            b"/* ======================================================================== */\n"
            b"/* ========================= LICENSING & COPYRIGHT ======================== */\n"
            b"/* ======================================================================== */\n"
            b"/* MUSASHI\n * Copyright Karl Stenerud. All rights reserved.\n"
            b" * This notice remains in source code and any binary files.\n"
            b" * All other licensing terms must be negotiated with the author.\n */\n"
            b" /* Modified by Eke-Eke */"
        )
        self.original = EMBED.MAGIC + b"\x01\x01\x00"

    def test_appends_exact_notice_and_removes_to_original_bytes(self):
        notice = EMBED.musashi_notice(self.header)
        embedded = EMBED.append_notice(self.original, self.header)
        self.assertTrue(embedded.startswith(self.original))
        self.assertEqual(EMBED.append_notice(embedded, self.header), embedded)
        self.assertEqual(EMBED.remove_notice(embedded), self.original)
        sections = list(EMBED._sections(embedded))
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[-1][3], EMBED.SECTION_NAME)
        size, name_start = EMBED._read_uleb(sections[-1][4], 0)
        self.assertEqual(sections[-1][4][name_start + size:], notice)

    def test_preserves_existing_custom_sections_byte_for_byte(self):
        existing = b"\0\x06\x04name\x01"
        module = self.original + existing
        embedded = EMBED.append_notice(module, self.header)
        self.assertEqual(EMBED.remove_notice(embedded), module)

    def test_conflicting_or_duplicate_notice_sections_are_rejected(self):
        embedded = EMBED.append_notice(self.original, self.header)
        altered = bytearray(embedded)
        altered[-1] ^= 1
        with self.assertRaises(EMBED.NoticeError):
            EMBED.append_notice(bytes(altered), self.header)
        duplicate = embedded + embedded[len(self.original):]
        with self.assertRaises(EMBED.NoticeError):
            EMBED.append_notice(duplicate, self.header)
        with self.assertRaises(EMBED.NoticeError):
            EMBED.remove_notice(self.original)

    def test_rejects_malformed_modules_and_sections(self):
        malformed = (
            b"bad",
            EMBED.MAGIC + b"\x00\x80",
            EMBED.MAGIC + b"\x00\x05x",
            EMBED.MAGIC + b"\x00\x02\x05x",
            EMBED.MAGIC + b"\x00\x03\x01\xffx",
        )
        for module in malformed:
            with self.subTest(module=module), self.assertRaises(EMBED.NoticeError):
                EMBED.append_notice(module, self.header)

    def test_rejects_non_musashi_header(self):
        with self.assertRaises(EMBED.NoticeError):
            EMBED.append_notice(self.original, b"/* no license here */")

    def test_file_update_is_idempotent_and_preserves_permissions(self):
        with tempfile.TemporaryDirectory(prefix="musashi-notice-file-") as temporary:
            wasm = Path(temporary) / "core.wasm"
            header = Path(temporary) / "m68k.h"
            wasm.write_bytes(self.original)
            header.write_bytes(self.header)
            wasm.chmod(0o644)
            EMBED.embed_file(wasm, header)
            first = wasm.read_bytes()
            EMBED.embed_file(wasm, header)
            self.assertEqual(wasm.read_bytes(), first)
            self.assertEqual(stat.S_IMODE(wasm.stat().st_mode), 0o644)
            self.assertEqual(EMBED.remove_notice(wasm.read_bytes()), self.original)


if __name__ == "__main__":
    unittest.main()
