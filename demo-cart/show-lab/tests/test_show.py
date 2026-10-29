"""Focused structural and reproducibility checks for the v0.3.8 rough cut."""
from pathlib import Path
import hashlib
import json
import runpy
import struct
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "demo-cart/show-lab/build_show.py"
OUTPUT = ROOT / "demo-cart/show-lab/build"
ROM = OUTPUT / "VRAMpage-MD-Demo-Cart-v0.3.8-Show.bin"

class OriginalShowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = runpy.run_path(str(SOURCE))
        cls.report = json.loads((OUTPUT/"rom_report.json").read_text())
        cls.rom = ROM.read_bytes()

    def test_six_scene_180_second_score(self):
        music = self.report["music"]
        self.assertTrue(music["original"])
        self.assertEqual(music["tempoBPM"],150)
        self.assertEqual(music["steps"],900)
        self.assertEqual(music["eventBytes"],14400)
        self.assertEqual(music["lengthSeconds"],180)
        self.assertEqual(music["fmChannels"],[0,1,2,3,4,5])
        self.assertEqual(music["eventStrideBytes"],16)
        self.assertEqual(len(music["patches"]),6)
        self.assertEqual(music["tonality"],"major")
        self.assertEqual(music["percussion"],["kick","snare","hat","fill"])
        self.assertEqual(music["eventsPerSecond"],5)
        self.assertEqual([n for n,_ in music["scenes"]],
            ["Captain Intro","Chromatic Vortex","Neon Aurora",
             "Sprite Storm","Chroma Reactor","Finale"])
        self.assertEqual(sum(sec for _,sec in music["scenes"]),180)

    def test_score_has_notes_rests_and_percussion(self):
        rows=[self.values["SHOW_MUSIC"][i:i+16] for i in range(0,14400,16)]
        self.assertEqual(len(rows),900)
        self.assertGreater(len(set(rows)),50)
        for row in rows:
            self.assertEqual(len(row),16)
            for offset in (0,2,4,6,8,10):
                self.assertTrue(row[offset] == 0 or (row[offset]&0x38) in
                                (0x18,0x20,0x28,0x30))
            self.assertIn(row[12],(0,1,2,3,4))
            self.assertIn(row[13],(0,1))
            self.assertEqual(row[14:],b'\x00\x00')
        self.assertEqual({row[12] for row in rows},{0,1,2,3,4})
        self.assertGreater(sum(row[0]!=0 for row in rows),250)
        self.assertGreater(sum(row[6]!=0 for row in rows),300)
        self.assertEqual(sum(row[6]!=0 and i%2==0 for i,row in enumerate(rows)
                             if 100<=i<250),0)
        self.assertGreater(sum(row[10]!=0 for row in rows),100)
        self.assertGreater(len(set(rows)),150)

    def test_rom_is_valid_and_original_artwork_is_unchanged(self):
        self.assertEqual(self.rom[0x100:0x104],b"SEGA")
        self.assertIn(b"V0.3.8",self.rom[0x120:0x180])
        self.assertEqual(len(self.rom),self.report["romSize"])
        self.assertEqual(len(self.rom)%2,0)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),self.report["sha256"])
        self.assertEqual(sum(struct.unpack_from(">H",self.rom,i)[0]
                             for i in range(0x200,len(self.rom),2))&65535,
                         struct.unpack_from(">H",self.rom,0x18E)[0])
        self.assertEqual(self.report["baseKitSHA256"],
                         "fb073ee201ce73072c83a569742a644c2f8c7816e102ffd55ce723154bd67403")
        self.assertEqual(self.report["assetSHA256"]["title_patterns.bin"],
            hashlib.sha256(self.values["PATTERNS"]).hexdigest())
        self.assertTrue({"music_start","music_tick","music_event","show_intro",
                         "show_finale","show_music","ym_write","ym_write_high"}.issubset(
            self.values["asm"].labels))
        self.assertIn(bytes.fromhex("00a04000"),self.rom)
        self.assertIn(bytes.fromhex("00a04001"),self.rom)
        self.assertIn(bytes.fromhex("00a04002"),self.rom)
        self.assertIn(bytes.fromhex("00a04003"),self.rom)

    def test_experimental_candidate_does_not_change_default(self):
        manifest=json.loads((ROOT/"site/cartridges.json").read_text())
        self.assertEqual(manifest["defaultCartridge"],"demo")
        self.assertEqual(manifest["cartridges"][0]["version"],"0.3.5")
        self.assertNotIn("0.3.8",json.dumps(manifest))
        self.assertEqual((ROOT/"VERSION").read_text().strip(),"0.5.0")

if __name__=="__main__":
    unittest.main()
