from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'site/index.html').read_text()
CSS = (ROOT / 'site/style.css').read_text()
JS = (ROOT / 'site/app.js').read_text()

class CompactWorkbenchTests(unittest.TestCase):
    def test_native_video_pixel_buffer_unchanged(self):
        self.assertIn('width="320" height="224"', HTML)
        self.assertIn('const GAME_WIDTH = 320, GAME_HEIGHT = 224', JS)
        self.assertIn('const SCREEN_WIDTH = 640, SCREEN_HEIGHT = 480', JS)
    def test_no_artificial_scanlines(self):
        self.assertNotIn('repeating-linear-gradient', CSS)
        self.assertNotIn('scanline-overlay', HTML)
        self.assertNotIn('scanline-overlay', JS)
    def test_compact_viewport(self):
        self.assertIn('width:min(1060px', CSS)
        self.assertIn('width:min(100%, 570px', CSS)
        self.assertIn('49dvh', CSS)
        self.assertIn('calc(100vh * 10 / 7)', CSS)
    def test_clean_restart_is_a_real_reset(self):
        self.assertIn('id="resetBtn"',HTML)
        self.assertIn('Clean restart', HTML)
        self.assertRegex(JS, r"\$\('resetBtn'\)\.addEventListener\('click'[\s\S]*?disconnect\(\);[\s\S]*?startCartridge\(romBytes,loadedName\)")
        self.assertIn('possibleVramResidue = false;', JS)
        self.assertIn('id="faultHint"',HTML)
    def test_compact_diagnostics_retain_log(self):
        self.assertIn('<details class="log-block">', HTML)
        self.assertIn('<details class="notes-block">', HTML)
        self.assertIn('id="experimentLog"', HTML)
        self.assertIn('id="clearLogBtn"', HTML)
    def test_fullscreen_does_not_resize_native_pixels(self):
        self.assertIn('document.fullscreenElement === displayViewport', JS)
        self.assertIn('canvas.width = GAME_WIDTH', JS)
        self.assertIn('canvas.height = GAME_HEIGHT', JS)
        self.assertIn('window.addEventListener(\'resize\'', JS)

if __name__ == '__main__':
    unittest.main()