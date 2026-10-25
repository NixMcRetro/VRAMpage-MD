"""Real browser layout/input regressions using an original synthetic core.

Run separately from the dependency-free unit suite; missing browsers are errors.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from browser_result import AnnotatedBrowserResult

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=ROOT / 'site'))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
        cls.browser = getattr(cls.playwright, OPTIONS.browser).launch(**kwargs)
        cls.addClassCleanup(cls.browser.close)
        print(f'Browser: {OPTIONS.browser} {cls.browser.version}', flush=True)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1366, 'height': 768}, color_scheme='light')
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.route('**/core/genplus.js', lambda route: route.fulfill(
            path=str(ROOT / 'tests/fixtures/mock-core.js'), content_type='application/javascript'))
        self.page.goto(f'http://127.0.0.1:{self.server.server_port}/')
        expect(self.page.locator('#powerLabel')).to_have_text('WAITING FOR ROM')
        # A format stub accepted by the UI, NOT an executable game ROM.
        stub = bytearray(512)
        stub[0x100:0x104] = b'SEGA'
        self.page.locator('#romFile').set_input_files({
            'name': 'synthetic-test.bin', 'mimeType': 'application/octet-stream', 'buffer': bytes(stub)})
        expect(self.page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        self.page.wait_for_function('window.mockCore.ticks > 0')

    def tearDown(self):
        self.screenshot(self._testMethodName)
        self.assertEqual(self.errors, [], 'Uncaught application errors')

    def settle(self):
        # Wait for sizing observer + queued repaint, without assuming CPU speed.
        self.page.evaluate('''() => new Promise(resolve => {
          requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        })''')

    def geometry(self):
        self.settle()
        return self.page.evaluate('''() => {
          const rect = s => { const r = document.querySelector(s).getBoundingClientRect();
            return {width:r.width, height:r.height, top:r.top, bottom:r.bottom}; };
          return {scrollWidth:document.documentElement.scrollWidth,frame:rect('#displayViewport'), canvas:rect('#screen'),
            section:rect('.screen-section'), toolbar:rect('.toolbar'),
            availableWidth:document.querySelector('.screen-well').clientWidth -
              parseFloat(getComputedStyle(document.querySelector('.screen-well')).paddingLeft) -
              parseFloat(getComputedStyle(document.querySelector('.screen-well')).paddingRight),
            buffer:[document.getElementById('screen').width, document.getElementById('screen').height],
            overflow:document.documentElement.scrollWidth > innerWidth,
            viewport:[innerWidth,innerHeight],
            overflowNodes:document.documentElement.scrollWidth > innerWidth
              ? [...document.querySelectorAll('body *')].map(el=>({
                  tag:el.tagName,id:el.id,classes:el.className,
                  right:el.getBoundingClientRect().right,width:el.getBoundingClientRect().width
                })).filter(el=>el.right>innerWidth).slice(0,20) : []};
        }''')

    def assert_native(self, geometry):
        self.assertEqual(geometry['buffer'], [320, 224])
        self.assertAlmostEqual(geometry['canvas']['width'] / geometry['canvas']['height'], 10 / 7, delta=0.002)
        self.assertFalse(geometry['overflow'], f'Horizontal page overflow: {geometry}')

    def screenshot(self, name):
        if OPTIONS.artifacts:
            OPTIONS.artifacts.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(OPTIONS.artifacts / f'{OPTIONS.browser}-{name}.png'), full_page=True)

    def test_responsive_window_budget(self):
        for width, height in [(1366, 768), (1280, 720), (1440, 900), (1920, 1080),
                              (1024, 600), (768, 768), (390, 844), (360, 640), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.page.set_viewport_size({'width': width, 'height': height})
                g = self.geometry()
                self.assert_native(g)
                self.assertLessEqual(g['section']['bottom'], height - 8)
                self.assertLessEqual(g['toolbar']['bottom'], height)
                self.assertGreater(g['canvas']['height'], 90)
                # Use the limiting dimension; avoid an arbitrary small player.
                self.assertTrue(abs(g['frame']['width'] - g['availableWidth']) < 2 or
                                abs(g['section']['bottom'] - (height - 12)) < 2, g)
                self.screenshot(f'{width}x{height}-light')
        self.page.set_viewport_size({'width': 1366, 'height': 768})
        self.assertGreater(self.geometry()['canvas']['width'], 630)

    def test_raw_recovery_resize_and_scroll(self):
        self.page.locator('#pauseBtn').click()
        def pixel():
            return self.page.evaluate("Array.from(document.getElementById('screen').getContext('2d').getImageData(10,1,1,1).data)")
        expect(self.page.locator('#videoStatus')).to_contain_text('112 missing output lines recovered')
        recovered = pixel()
        self.assertEqual(recovered, [74, 64, 192, 255])
        self.page.locator('#rawVideoToggle').check()
        expect(self.page.locator('#videoStatus')).to_have_text('Video: raw core pixels')
        self.assertEqual(pixel(), [0, 0, 0, 255])
        for width, height in [(390, 844), (1366, 768), (1024, 600)]:
            self.page.set_viewport_size({'width': width, 'height': height})
            self.assert_native(self.geometry())
            self.assertEqual(pixel(), [0, 0, 0, 255])
        self.page.locator('#rawVideoToggle').uncheck()
        self.assertEqual(pixel(), recovered)
        before = self.geometry()['frame']
        self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        after = self.geometry()['frame']
        self.assertAlmostEqual(before['height'], after['height'], delta=0.1)
        self.assertAlmostEqual(before['width'], after['width'], delta=0.1)

    def test_live_system_appearance(self):
        def background():
            return self.page.evaluate('getComputedStyle(document.body).backgroundColor')
        self.assertEqual(background(), 'rgb(222, 219, 210)')
        self.page.emulate_media(color_scheme='dark')
        self.assertEqual(background(), 'rgb(23, 28, 32)')
        self.screenshot('1366x768-dark')
        self.page.emulate_media(color_scheme='light')
        self.assertEqual(background(), 'rgb(222, 219, 210)')
        self.assert_native(self.geometry())

    def test_native_fullscreen_entry_resize_exit(self):
        self.page.locator('#pauseBtn').click()
        before = self.geometry()
        # Browser automation cannot resize a maximized native fullscreen
        # window, so exercise fullscreen at both sizes around normal-window
        # resizes instead of sending an unsupported resize while fullscreen.
        for width, height in [(1280, 720), (1366, 768)]:
            self.page.set_viewport_size({'width': width, 'height': height})
            self.assert_native(self.geometry())
            self.page.locator('#fullscreenBtn').click()
            self.page.wait_for_function("document.fullscreenElement?.id === 'displayViewport'")
            self.settle()
            self.assert_native(self.geometry())
            self.assertEqual(self.page.locator('#fullscreenBtn').get_attribute('aria-pressed'), 'true')
            self.screenshot(f'fullscreen-{width}x{height}')
            self.page.evaluate('document.exitFullscreen()')
            self.page.wait_for_function('!document.fullscreenElement')
            self.assert_native(self.geometry())
            expect(self.page.locator('#fullscreenBtn')).to_have_text('Fullscreen')
            self.assertLessEqual(self.geometry()['toolbar']['bottom'], height)
        self.page.set_viewport_size({'width': 1366, 'height': 768})
        self.assertAlmostEqual(self.geometry()['frame']['width'], before['frame']['width'], delta=1)
        self.assertEqual(self.page.evaluate('window.mockCore.starts'), 1, 'Resize/fullscreen must not reset the game')
        expect(self.page.locator('#videoStatus')).to_contain_text('112 missing output lines recovered')

    def test_patchbay_keyboard_mouse_and_clean_restart(self):
        self.page.locator('#vramMode').select_option('bridge')
        pins = self.page.locator('#pinGrid .pin')
        pins.nth(0).focus()
        self.page.keyboard.press('Enter')
        expect(pins.nth(0)).to_have_class('pin selected')
        pins.nth(3).focus()
        self.page.keyboard.press('Space')
        expect(self.page.locator('#connectionLabel')).to_have_text('AD0 ↔ AD3')
        self.assertEqual(self.page.evaluate('window.mockCore.short'), [0, 3])
        self.page.keyboard.press('Digit0')
        pins.nth(1).click()
        pins.nth(2).click()
        expect(self.page.locator('#connectionLabel')).to_have_text('AD1 ↔ AD2')
        self.page.keyboard.press('Digit1')
        expect(self.page.locator('#connectionLabel')).to_have_text('AD0 ↔ AD1')
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit2')
        expect(self.page.locator('#connectionLabel')).to_have_text('AD0 ↔ AD2')
        self.page.keyboard.up('Digit2')
        self.page.keyboard.up('Shift')
        expect(self.page.locator('#connectionLabel')).to_have_text('AD0 ↔ AD1')
        self.page.locator('#resetBtn').click()
        expect(self.page.locator('#connectionLabel')).to_have_text('NONE — NORMAL ADDRESSING')
        self.assertEqual(self.page.evaluate('window.mockCore.short'), [-1, -1])
        self.assertEqual(self.page.evaluate('window.mockCore.starts'), 2)
        expect(self.page.locator('#faultHint')).to_be_hidden()
        expect(self.page.locator('#powerLabel')).to_have_text('CONSOLE ON')

    def test_controller_and_pause(self):
        self.page.locator('h1').click()  # No focused button should consume Enter/Space.
        for key, index in [('ArrowRight', 6), ('ArrowDown', 7), ('KeyZ', 9),
                           ('KeyX', 11), ('KeyC', 10), ('Enter', 15)]:
            with self.subTest(key=key):
                self.page.keyboard.down(key)
                self.page.wait_for_function('(i) => window.mockCore.inputs[i] === 1', arg=index)
                self.page.keyboard.up(key)
                self.page.wait_for_function('(i) => window.mockCore.inputs[i] === 0', arg=index)
        self.page.keyboard.press('KeyP')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        self.settle()
        ticks = self.page.evaluate('window.mockCore.ticks')
        self.settle()
        self.assertEqual(self.page.evaluate('window.mockCore.ticks'), ticks)
        self.page.locator('#pauseBtn').click()
        self.page.wait_for_function('(n) => window.mockCore.ticks > n', arg=ticks)

    def test_modified_shortcuts_do_not_control_game(self):
        self.page.locator('h1').click()
        for code, key, modifier in [
                ('KeyP', 'p', 'ctrlKey'), ('KeyP', 'p', 'metaKey'),
                ('KeyP', 'p', 'altKey'), ('Digit1', '1', 'ctrlKey'),
                ('KeyC', 'c', 'metaKey')]:
            with self.subTest(code=code, modifier=modifier):
                allowed = self.page.evaluate('''({code,key,modifier}) => {
                  const event = new KeyboardEvent('keydown', {
                    code,key,bubbles:true,cancelable:true,[modifier]:true
                  });
                  return document.dispatchEvent(event);
                }''', {'code': code, 'key': key, 'modifier': modifier})
                self.assertTrue(allowed, f'{modifier}+{key} must remain available to the browser')
        self.assertEqual(self.page.evaluate('''() => ({
          pause:document.querySelector('#pauseBtn').textContent.trim(),
          connection:document.querySelector('#connectionLabel').textContent.trim(),
          a:window.mockCore.inputs[10]
        })'''), {
            'pause': 'Pause', 'connection': 'NONE — NORMAL ADDRESSING', 'a': 0})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--executable', help='Optional local browser executable (e.g. /usr/bin/chromium)')
    parser.add_argument('--artifacts', type=Path, help='Screenshot directory outside the source tree')
    OPTIONS, remaining = parser.parse_known_args()
    unittest.main(argv=[__file__, *remaining], verbosity=2,
                  testRunner=unittest.TextTestRunner(verbosity=2, resultclass=AnnotatedBrowserResult))
