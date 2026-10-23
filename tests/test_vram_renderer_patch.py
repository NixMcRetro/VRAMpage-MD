"""Fail-closed patch checks for the pinned Mode 5 renderer read paths."""
from pathlib import Path
import importlib.util
import os
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PINNED_RENDER = (Path(os.environ.get(
    "VRAMPAGE_WASM_GENPLUS", ROOT / "vendor/wasm-genplus")) /
    "src/main/c/core/vdp_render.c")
SPEC = importlib.util.spec_from_file_location(
    "patch_core", ROOT / "scripts/patch_core.py")
patch_core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patch_core)


class VramRendererPatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PINNED_RENDER.is_file():
            raise unittest.SkipTest("Pinned wasm-genplus source is required")
        cls.source = PINNED_RENDER.read_text()

    def test_routes_all_standard_and_alt_mode5_sources_idempotently(self):
        patched = patch_core.patch_mode5_render_reads(self.source)
        self.assertEqual(patch_core.patch_mode5_render_reads(patched), patched)
        self.assertEqual(patched.count(patch_core.VRAM_RENDER_READS), 1)
        self.assertEqual(patched.count("VRAM_TX_RENDER_U32(hscb +"), 8)
        self.assertEqual(patched.count("atbuf = VRAM_TX_RENDER_U32("), 48)
        self.assertEqual(patched.count("bp = VRAM_TX_RENDER_U32("), 1)
        self.assertEqual(patched.count("object_info->attr  = VRAM_TX_RENDER_U16("), 1)
        self.assertEqual(patched.count("object_info->xpos  = VRAM_TX_RENDER_U16("), 1)
        self.assertNotIn("atbuf = nt[", patched)
        self.assertNotRegex(patched, r"uint32 xscroll\s*=\s*\*\(uint32 \*\)&vram\[")
        self.assertNotIn("bp = *(uint32 *)&vram[(name << 5) | (y << 2)];", patched)
        self.assertIn("ypos = (q[link] >> im2_flag) & 0x1FF;", patched)
        self.assertIn("size = q[link + 1] >> 8;", patched)
        self.assertIn("link = (q[link + 1] & 0x7F) << 2;", patched)

    def test_raw_name_read_reintroduced_after_marker_fails_closed(self):
        patched = patch_core.patch_mode5_render_reads(self.source)
        pattern = re.compile(r"(?m)^(\s*)atbuf = VRAM_TX_RENDER_U32\([^\n]+\);$")
        drifted, count = pattern.subn(r"\1atbuf = nt[0];", patched, count=1)
        self.assertEqual(count, 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted)

    def test_fresh_source_missing_name_load_or_new_raw_byte_load_fails_closed(self):
        raw = re.compile(r"(?m)^\s*atbuf = nt\[[^\n]+\];$")
        drifted, count = raw.subn("", self.source, count=1)
        self.assertEqual(count, 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted)

        patched = patch_core.patch_mode5_render_reads(self.source)
        name = "void render_bg_m5(int line"
        start = patched.index(name)
        raw_read = "  uint8 unexpected_read = vram[0x1234];\n"
        drifted = patched[:start] + patched[start:].replace(
            "  uint32 *nt =", raw_read + "  uint32 *nt =", 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted)

    def test_raw_scroll_and_pattern_reads_reintroduced_after_marker_fail(self):
        patched = patch_core.patch_mode5_render_reads(self.source)
        drifted_scroll = patched.replace(
            "uint32 xscroll      = VRAM_TX_RENDER_U32(hscb + ((line & hscroll_mask) << 2));",
            "uint32 xscroll      = *(uint32 *)&vram[hscb + ((line & hscroll_mask) << 2)];",
            1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted_scroll)
        drifted_pattern = patched.replace(
            "bp = VRAM_TX_RENDER_U32((name << 5) | (y << 2));",
            "bp = *(uint32 *)&vram[(name << 5) | (y << 2)];", 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted_pattern)

    def test_sat_internal_fields_stay_internal_and_raw_attr_read_fails(self):
        patched = patch_core.patch_mode5_render_reads(self.source)
        self.assertIn("ypos = (q[link] >> im2_flag) & 0x1FF;", patched)
        self.assertIn("size = q[link + 1] >> 8;", patched)
        self.assertIn("link = (q[link + 1] & 0x7F) << 2;", patched)
        drifted = patched.replace(
            "object_info->attr  = VRAM_TX_RENDER_U16((uint32)((uint8 *)p - vram) + ((link + 2) << 1));",
            "object_info->attr  = p[link + 2];", 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(drifted)

    def test_partial_include_marker_fails_closed(self):
        patched = patch_core.patch_mode5_render_reads(self.source)
        partial = patched.replace(patch_core.VRAM_RENDER_MARKER,
                                  "VRAM TX MODE 5 RENDER READS v0", 1)
        with self.assertRaises(SystemExit):
            patch_core.patch_mode5_render_reads(partial)


if __name__ == "__main__":
    unittest.main()
