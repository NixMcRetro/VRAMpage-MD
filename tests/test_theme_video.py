from pathlib import Path
import unittest

ROOT=Path(__file__).parents[1]
HTML=(ROOT/'site/index.html').read_text()
CSS=(ROOT/'site/style.css').read_text()
JS=(ROOT/'site/app.js').read_text()

class AppearanceAndVideoTest(unittest.TestCase):
    def test_auto_theme_without_manual_override(self):
        self.assertIn('(prefers-color-scheme: dark)',CSS)
        self.assertIn('color-scheme:dark',CSS)
        self.assertIn('color-scheme: light;',CSS)
        self.assertIn('media="(prefers-color-scheme: dark)"', HTML)
    def test_video_adapter_script_loads_before_app(self):
        self.assertLess(HTML.index('src="framebuffer.js"'),HTML.index('src="app.js"'))
        self.assertIn('frameAdapter.copyActiveFrame(',JS)
        self.assertIn('id="rawVideoToggle"',HTML)
    def test_canvas_is_native_resolution(self):
        self.assertIn('id="screen" width="320" height="224"',HTML)
        self.assertIn('image-rendering:pixelated',CSS)
    def test_fullscreen_remains_on_container(self):
        self.assertIn('displayViewport',HTML)
        self.assertIn('#displayViewport:fullscreen',CSS)
    def test_build_retains_core(self):
        self.assertIn('site/core/genplus.js', (ROOT/'docs/VIDEO-OUTPUT.md').read_text())

if __name__=='__main__': unittest.main()