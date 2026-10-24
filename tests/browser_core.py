"""Actual compiled-core browser smoke with an original video/PSG test cartridge.

No commercial ROM, mock emulator, or game-derived data is used.
"""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import struct
import threading
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


def original_cartridge():
    rom = bytearray(65536)
    for offset in range(0, 256, 4):
        struct.pack_into('>I', rom, offset, 0x300)
    struct.pack_into('>II', rom, 0, 0xffff00, 0x200)
    rom[0x100:0x110] = b'SEGA MEGA DRIVE '
    rom[0x120:0x140] = b'VRAMPAGE ORIGINAL VIDEO TONE TEST'
    struct.pack_into('>IIII', rom, 0x1a0, 0, len(rom)-1, 0xff0000, 0xffffff)
    rom[0x1f0] = ord('U')
    words = []
    def word(address, value):
        words.extend([0x33fc, value, address >> 16, address & 0xffff])
    def byte(address, value):
        words.extend([0x13fc, value, address >> 16, address & 0xffff])
    word(0xc00004, 0x8004)  # Mode 5
    word(0xc00004, 0x8144)  # Display on, DMA enabled
    word(0xc00004, 0x8c81)  # H40, non-interlaced
    word(0xc00004, 0x8f02)  # Auto-increment
    words.extend([0x23fc, 0xc000, 0x0000, 0x00c0, 0x0004])  # CRAM write
    word(0xc00000, 0x000e)  # Red backdrop
    byte(0xc00011, 0x8a)  # PSG channel 0 period
    byte(0xc00011, 0x10)
    byte(0xc00011, 0x90)  # Channel 0 audible
    words.extend([0x5279, 0x00ff, 0x1000, 0x60f8])  # Increment RAM forever.
    for i, value in enumerate(words):
        struct.pack_into('>H', rom, 0x200+2*i, value)
    for i, value in enumerate([0x4e72, 0x2700, 0x60fe]):
        struct.pack_into('>H', rom, 0x300+2*i, value)
    return bytes(rom)


class ActualCoreBrowserTests(unittest.TestCase):
    def test_original_video_audio_and_controls(self):
        handler = partial(SimpleHTTPRequestHandler, directory=ROOT / 'site')
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = browser.new_page(viewport={'width': 1366, 'height': 768}, accept_downloads=True)
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    # Capture the real instantiated module without replacing its behavior.
                    core_js = (ROOT / 'site/core/genplus.js').read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js', lambda route: route.fulfill(content_type='text/javascript', body=core_js))
                    # A fixture manifest exercises provenance without mocking the real core.
                    build_info={'application':'VRAMpage MD','application_version':'0.3.0',
                                'source_commit':'b'*40,'package_format':1}
                    page.route('**/build-info.json',lambda route:route.fulfill(
                        content_type='application/json',body=json.dumps(build_info)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    page.locator('#romFile').set_input_files({'name':'original-video-tone.bin', 'mimeType':'application/octet-stream', 'buffer':original_cartridge()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.wait_for_function('window.testCore._get_logic_frame()>10')
                    pixels = page.locator('#screen').evaluate('''canvas => {
                        const p=canvas.getContext('2d').getImageData(0,0,320,224).data;
                        return {rows:Array.from({length:224},(_,y)=>{
                            const i=(y*320+160)*4;return p[i]>150 && p[i+1]<80 && p[i+2]<80;
                        }), width:canvas.width,height:canvas.height};
                    }''')
                    self.assertEqual((pixels['width'],pixels['height']), (320,224))
                    self.assertTrue(all(pixels['rows']), 'Every native output row must contain the red backdrop')
                    self.assertTrue(page.evaluate('''() => {
                        const c=testCore;const a=new Float32Array(c.HEAPF32.buffer,c._get_web_audio_l_ref(),700);
                        return a.every(Number.isFinite) && a.some(x=>Math.abs(x)>0.0001);
                    }'''), 'Actual PSG must generate nonzero finite samples')
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Mute Sound')
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Enable Sound')
                    psg_api=page.evaluate("typeof testCore._set_psg_data_bridge==='function'")
                    if psg_api:
                        expect(page.locator('#psgBridgeApply')).to_be_enabled()
                        page.locator('#psgBridgeA').select_option('0')
                        page.locator('#psgBridgeB').select_option('7')
                        page.locator('#psgBridgeApply').click()
                        psg_state=page.evaluate('testCore._get_psg_data_bridge_state()')
                        self.assertTrue(psg_state['effective'])
                        self.assertEqual((psg_state['bridgeA'],psg_state['bridgeB']),(0,7))
                        self.assertIn('D0',page.locator('#psgBridgeStatus').inner_text())
                    else:
                        expect(page.locator('#psgBridgeApply')).to_be_disabled()
                        self.assertIn('does not provide',page.locator('#psgBridgeStatus').inner_text())
                    page.locator('#screen').click()
                    page.keyboard.down('x')
                    page.wait_for_function('new Float32Array(testCore.HEAPF32.buffer,testCore._get_input_buffer_ref(),32)[11]===1')
                    page.keyboard.up('x')
                    page.wait_for_function('new Float32Array(testCore.HEAPF32.buffer,testCore._get_input_buffer_ref(),32)[11]===0')
                    # Inject standard gamepad state only, keeping the real input adapter/core.
                    page.evaluate("navigator.getGamepads=()=>[{axes:[1,0],buttons:[{pressed:true}]}]")
                    page.wait_for_function('new Float32Array(testCore.HEAPF32.buffer,testCore._get_input_buffer_ref(),32)[9]===1')
                    page.evaluate('navigator.getGamepads=()=>[]')
                    page.locator('#vramMode').select_option('bridge')
                    page.locator('.pin').nth(0).click()
                    page.locator('.pin').nth(1).click()
                    expect(page.locator('.pin.connected')).to_have_count(2)
                    page.locator('#disconnectBtn').click()
                    expect(page.locator('.pin.connected')).to_have_count(0)
                    page.locator('#vramMode').select_option('disconnect')
                    page.locator('.pin').nth(0).click()
                    page.locator('.pin').nth(7).focus()
                    page.keyboard.press('Space')
                    page.wait_for_function('testCore._get_vram_address_mask()===129')
                    expect(page.locator('.pin').nth(7).locator('.chip-cut')).to_have_css('visibility','visible')
                    page.locator('#disconnectBtn').click()
                    page.wait_for_function('testCore._get_vram_address_mask()===0')
                    page.locator('#logicExperiment > summary').click()
                    page.locator('[data-chip-line]').nth(0).click()
                    page.wait_for_function('testCore._get_logic_address_mask()===1')
                    expect(page.locator('[data-chip-line]').nth(0).locator('.chip-cut')).to_have_css('visibility','visible')
                    page.locator('#chipRestoreBtn').click()
                    page.wait_for_function('testCore._get_logic_address_mask()===0')
                    page.locator('#logicApplyBtn').click()
                    page.locator('#logicResumeBtn').click()
                    page.locator('#logicCpuResetBtn').click()
                    with page.expect_download() as download:
                        page.locator('#logicExperimentBtn').click()
                    payload=json.loads(Path(download.value.path()).read_text())
                    self.assertEqual(payload['modelVersion'],'0.3.0-experimental')
                    self.assertEqual(payload['schemaVersion'],1)
                    self.assertEqual(payload['build'],{'status':'available','applicationVersion':'0.3.0','sourceCommit':'b'*40})
                    self.assertEqual(payload['vramFault']['addressMask'],0)
                    self.assertEqual([e['mask'] for e in payload['vramAddressLineChanges']],[1,129,0])
                    self.assertEqual(payload['rom']['name'],'original-video-tone.bin')
                    self.assertEqual(len(payload['rom']['sha256']),64)
                    self.assertNotIn('romBytes',payload)
                    self.assertEqual(payload['psgInputFault']['available'],psg_api)
                    if psg_api:
                        self.assertEqual(payload['psgInputFault']['modelVersion'],'psg-data-low-dominant-v1')
                        self.assertTrue(payload['psgInputFault']['configured'])
                    page.locator('#resetBtn').click()
                    page.wait_for_function('testCore._get_logic_address_mask()===0')
                    if psg_api:
                        page.wait_for_function('!testCore._get_psg_data_bridge_state().configured')
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    self.assertEqual(errors,[])
                    browser.close()
            finally:
                server.shutdown()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--executable')
    OPTIONS, remaining=parser.parse_known_args()
    unittest.main(argv=[__file__,*remaining],verbosity=2)
