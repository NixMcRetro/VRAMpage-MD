"""Regression checks for video canvas sizing and fullscreen wiring (stdlib only)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DisplayContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'site' / 'index.html').read_text()
        cls.css = (ROOT / 'site' / 'style.css').read_text()
        cls.js = (ROOT / 'site' / 'app.js').read_text()

    def test_native_canvas_geometry(self):
        self.assertRegex(self.html, r'<canvas\s+id="screen"\s+width="320"\s+height="224"')
        self.assertIn('const GAME_WIDTH = 320, GAME_HEIGHT = 224;', self.js)
        self.assertIn('const SCREEN_WIDTH = 640, SCREEN_HEIGHT = 480;', self.js)
        # v0.1.3 routes pixels through the tested display adapter, not direct copying.
        self.assertIn('src="framebuffer.js"', self.html)
        self.assertIn('frameAdapter.copyActiveFrame(', self.js)

    def test_fullscreen_targets_container_not_canvas(self):
        self.assertIn('id="displayViewport"', self.html)
        self.assertIn('displayViewport.requestFullscreen()', self.js)
        self.assertNotIn('canvas.requestFullscreen()', self.js)
        self.assertIn('#displayViewport:fullscreen', self.css)
        self.assertIn('aspect-ratio:10/7', self.css)

    def test_resize_restores_native_buffer(self):
        for text in ['canvas.width = GAME_WIDTH', 'canvas.height = GAME_HEIGHT',
                     "window.addEventListener('resize', scheduleDisplayRefresh)",
                     "document.addEventListener('fullscreenchange', scheduleDisplayRefresh)",
                     'ResizeObserver(scheduleDisplayRefresh)', 'drawActiveVideo()']:
            self.assertIn(text, self.js)

    def test_no_crt_effects_and_core_inputs_intact(self):
        self.assertNotIn('scanline', self.html.lower())
        self.assertIn('image-rendering:pixelated', self.css)
        for element_id in ['screenPlaceholder', 'romFile', 'resetBtn', 'pauseBtn',
                           'soundBtn', 'fullscreenBtn', 'pinGrid', 'presetGrid',
                           'disconnectBtn', 'experimentLog', 'powerLed', 'powerLabel',
                           'connectionLabel', 'readCount', 'writeCount', 'fpsIndicator']:
            self.assertIn(f'id="{element_id}"', self.html)


if __name__ == '__main__':
    unittest.main()