"""Actual compiled-core browser smoke with an original video/PSG test cartridge.

No commercial ROM, mock emulator, or game-derived data is used.
"""
import argparse
import json
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import struct
import threading
import unittest

from playwright.sync_api import sync_playwright, expect
from browser_result import AnnotatedBrowserResult

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


def prefer_manual_startup(page):
    """Keep actual-core tests at the manual cartridge insertion screen."""
    page.add_init_script("window.sessionStorage.setItem('vrampage-custom-rom-preferred', '1')")


def new_manual_startup_page(browser, **kwargs):
    page = browser.new_page(**kwargs)
    prefer_manual_startup(page)
    return page


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


def original_z80_store_cartridge():
    """Original video/PSG cartridge with a Z80 program storing $44/$55."""
    rom = bytearray(original_cartridge())
    words = []
    def word(address, value):
        words.extend([0x33fc, value, address >> 16, address & 0xffff])
    def byte(address, value):
        words.extend([0x13fc, value, address >> 16, address & 0xffff])
    z80 = [0x3e,0x44,0x32,0x00,0x01, 0x3e,0x55,0x32,0x00,0x11,
           0x3a,0x00,0x01,0x32,0x11,0x7f, 0x3e,0x22,0x32,0x00,0x40,
           0x3e,0x00,0x32,0x01,0x40, 0xc3,0x00,0x00]
    word(0xa11100,0x0100);word(0xa11200,0x0100)
    for i, value in enumerate(z80):
        byte(0xa00000+i,value)
    word(0xa11100,0)
    words.extend([0x5279,0x00ff,0x0800,0x60f8])
    # Preserve the original VDP/tone setup; replace only its final RAM loop.
    offset=rom.index(bytes.fromhex('527900ff100060f8'),0x200)
    for i, value in enumerate(words):
        struct.pack_into('>H',rom,offset+2*i,value)
    return bytes(rom)


class ActualCoreBrowserTests(unittest.TestCase):
    def test_bundled_demo_boots_renders_and_respects_manual_override(self):
        # Use the actual compiled WASM core, never a mock or a synthetic screenshot.
        rom = OPTIONS.site_root / 'demo/VRAMpage-MD-Demo-Cart-v0.1.bin'
        self.assertTrue(rom.is_file(), 'The original homebrew Demo Cart must be in the built site')
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    try:
                        page = browser.new_page(viewport={'width': 1366, 'height': 768})
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        core_js = (OPTIONS.site_root / 'core/genplus.js').read_text()
                        core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                        page.route('**/core/genplus.js', lambda route: route.fulfill(
                            content_type='text/javascript', body=core_js))
                        page.goto(f'http://127.0.0.1:{server.server_port}/')
                        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD DEMO CART')
                        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                        page.wait_for_function('window.testCore?._get_logic_frame()>12')
                        screen = page.locator('#screen').evaluate('''canvas => {
                            const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
                            const colours=new Set();
                            for(let y=0;y<canvas.height;y+=4)for(let x=0;x<canvas.width;x+=4){
                                let i=(y*canvas.width+x)*4;
                                colours.add(pixels[i]+','+pixels[i+1]+','+pixels[i+2]);
                            }
                            return {width:canvas.width,height:canvas.height,uniqueColours:colours.size};
                        }''')
                        self.assertEqual((screen['width'], screen['height']), (320,224))
                        self.assertGreater(screen['uniqueColours'], 4,
                                           f'Original Demo Cart rendered a blank or uniform image: {screen}')
                        self.assertEqual(page.locator('#soundBtn').inner_text(), 'Enable Sound')
                        page.locator('#romFile').set_input_files({
                            'name':'user-choice.bin','mimeType':'application/octet-stream',
                            'buffer':original_cartridge()})
                        expect(page.locator('#romName')).to_have_text('USER-CHOICE.BIN')
                        page.locator('#resetBtn').click()
                        expect(page.locator('#romName')).to_have_text('USER-CHOICE.BIN')
                        self.assertEqual(errors, [])
                    finally:
                        browser.close()
            finally:
                server.shutdown()

    def test_region_selection_uses_native_timing_video_audio_and_lifecycle(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    try:
                        page = new_manual_startup_page(browser, accept_downloads=True)
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.add_init_script('''window.testFrames=[];window.testTime=0;
                            window.requestAnimationFrame=cb=>testFrames.push(cb);
                            window.stepTestFrame=()=>{const q=testFrames.splice(0);testTime+=17;q.forEach(cb=>cb(testTime));};''')
                        core_js = (OPTIONS.site_root/'core/genplus.js').read_text()
                        core_js += '''\nconst originalFactory=window.Module;
                            window.regionCalls={starts:0,ticks:0,audio:[]};
                            window.Module=opts=>originalFactory(opts).then(c=>{
                              window.testCore=c;
                              for(const key of ['_start','_tick','_sound']){
                                const native=c[key];c[key]=(...args)=>{
                                  const result=Reflect.apply(native,c,args);
                                  if(key==='_start')regionCalls.starts++;
                                  if(key==='_tick')regionCalls.ticks++;
                                  if(key==='_sound'){
                                    const left=new Float32Array(c.HEAPF32.buffer,c._get_web_audio_l_ref(),result);
                                    const right=new Float32Array(c.HEAPF32.buffer,c._get_web_audio_r_ref(),result);
                                    regionCalls.audio.push({count:result,finite:left.every(Number.isFinite)&&right.every(Number.isFinite),
                                      nonzero:left.some(v=>v!==0)||right.some(v=>v!==0)});
                                  }return result;
                                };
                              }return c;
                            });\n'''
                        page.route('**/core/genplus.js', lambda route: route.fulfill(content_type='text/javascript', body=core_js))
                        page.goto(f'http://127.0.0.1:{server.server_port}/')
                        page.wait_for_function('!!window.testCore', polling=10)
                        # Header Europe deliberately disagrees with forced NTSC modes.
                        rom = bytearray(original_cartridge())
                        rom[0x1f0] = ord('E')
                        offset = rom.index(bytes.fromhex('527900ff100060f8'), 0x200)
                        for i, value in enumerate([0x13f9,0x00a1,0x0001,0x00ff,0x1002,0x5279,0x00ff,0x1000,0x60f8]):
                            struct.pack_into('>H', rom, offset+2*i, value)
                        for request, code, pal in [(1,128,False),(3,0,False),(2,192,True),(0,192,True),(4,64,True)]:
                            struct.pack_into('>H', rom, 0x20a, 0x814c if pal else 0x8144)
                            page.locator('#regionSelect').select_option(str(request))
                            starts = page.evaluate('regionCalls.starts')
                            page.locator('#romFile').set_input_files({'name':f'original-region-{request}.bin',
                                'mimeType':'application/octet-stream','buffer':bytes(rom)})
                            page.wait_for_function('n=>regionCalls.starts===n+1', arg=starts, polling=10)
                            expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                            page.evaluate('regionCalls.audio=[];for(let i=0;i<9;i++)stepTestFrame()')
                            state = page.evaluate('testCore._get_region_state()')
                            self.assertEqual((state['requestedRegion'],state['regionCode'],state['pal']), (request,code,pal))
                            self.assertEqual((state['linesPerFrame'],state['masterClock']), (313,53203424) if pal else (262,53693175))
                            self.assertAlmostEqual(state['frameRate'], state['masterClock']/(3420*state['linesPerFrame']), places=9)
                            self.assertEqual((state['width'],state['height']), (320,240 if pal else 224))
                            # Native Work RAM exposes swapped byte lanes on this build.
                            self.assertEqual(page.evaluate('testCore.HEAPU8[testCore._get_logic_ram_ref()+0x1003]&0xc0'), code)
                            expect(page.locator('#machineSummary')).to_contain_text(f"{state['frameRate']:.2f} Hz")
                            pixels = page.evaluate('''() => {
                              const c=document.querySelector('#screen'),p=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
                              return {width:c.width,height:c.height,top:Array.from(p.slice(0,4)),bottom:Array.from(p.slice(-4))};
                            }''')
                            self.assertEqual((pixels['width'],pixels['height']), (state['width'],state['height']))
                            self.assertGreater(pixels['top'][0], 0)
                            self.assertGreater(pixels['bottom'][0], 0, 'last active line must be copied')
                            audio = page.evaluate('regionCalls.audio')
                            self.assertTrue(audio and all(700 <= s['count'] <= 1024 and s['finite'] for s in audio))
                            self.assertTrue(any(s['nonzero'] for s in audio))
                            self.assertLess(abs(audio[-1]['count']-44100/state['frameRate']), 8)
                        page.locator('#pauseBtn').click()
                        page.locator('#logicExperiment > summary').click()
                        page.locator('#saveCheckpointBtn').click()
                        expect(page.locator('#checkpointStatus')).to_contain_text('Saved Frame')
                        ticks = page.evaluate('regionCalls.ticks')
                        page.locator('#regionSelect').select_option('1')
                        expect(page.locator('#regionStatus')).to_contain_text('Pending')
                        page.locator('#logicCpuResetBtn').click()
                        self.assertEqual(page.evaluate('regionCalls.ticks'), ticks)
                        self.assertEqual(page.evaluate('testCore._get_region_state().regionCode'), 64)
                        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
                        with page.expect_download() as info:
                            page.locator('#logicExperimentBtn').click()
                        machine = json.loads(Path(info.value.path()).read_text())['machine']
                        self.assertEqual((machine['requestedRegion'],machine['activeRequestedRegion'],machine['regionCode']), (1,4,64))
                        page.locator('#resetBtn').click()
                        expect(page.locator('#restoreCheckpointBtn')).to_be_disabled()
                        self.assertEqual(page.evaluate('testCore._get_region_state().regionCode'), 128)
                        page.locator('#regionSelect').select_option('2')
                        page.locator('#resetBtn').click()
                        page.evaluate('for(let i=0;i<5;i++)stepTestFrame()')
                        page.locator('#ramWriteMode').select_option('pulse')
                        page.locator('[data-ram-frame-pair="10,11"]').click()
                        pulse = page.evaluate('''() => {
                          const start=testCore._get_logic_frame();let steps=0;
                          while(testCore._get_logic_frame()<start+7&&steps++<30)stepTestFrame();
                          const before=document.querySelector('#randomiserStatus').textContent;
                          while(testCore._get_logic_frame()<start+8&&steps++<30)stepTestFrame();
                          return {frames:testCore._get_logic_frame()-start,before,after:document.querySelector('#randomiserStatus').textContent};
                        }''')
                        self.assertEqual(pulse['frames'], 8)
                        self.assertIn('active', pulse['before'])
                        self.assertIn('ended after 8 emulated frames', pulse['after'])
                        self.assertEqual(errors, [])
                    finally:
                        browser.close()
            finally:
                server.shutdown()

    def test_normal_core_rejects_optional_configuration_before_mutation(self):
        normal_source = OPTIONS.site_root / 'source/src/main/js'
        normal_js = normal_source / 'genplus.js'
        normal_wasm = normal_source / 'genplus.wasm'
        if not normal_js.is_file() or not normal_wasm.is_file():
            self.fail(f'complete source package must provide normal core assets at {normal_source}')
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width': 1366, 'height': 768}, accept_downloads=True)
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    core_js = normal_js.read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js', lambda route: route.fulfill(
                        content_type='text/javascript', body=core_js))
                    page.route('**/core/genplus.wasm', lambda route: route.fulfill(
                        content_type='application/wasm', path=str(normal_wasm)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    page.locator('#romFile').set_input_files({
                        'name': 'original-normal-config.bin',
                        'mimeType': 'application/octet-stream',
                        'buffer': original_cartridge()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.wait_for_function('window.testCore._get_logic_frame()>10')
                    self.assertEqual(page.evaluate("typeof testCore._set_vram_fault_model"), 'undefined')
                    self.assertEqual(page.evaluate("typeof testCore._set_psg_data_bridge"), 'undefined')
                    self.assertEqual(page.evaluate("typeof testCore._set_fm_data_bridge"), 'undefined')
                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    before = page.evaluate('''() => ({
                        addressMask: testCore._get_vram_address_mask(),
                        ramMask: testCore._get_logic_address_mask(),
                        vramModel: document.querySelector('#vramModel').value,
                        psgA: document.querySelector('#psgBridgeA').value,
                        fmA: document.querySelector('#fmBridgeA').value
                    })''')
                    requested = {
                        'format': 'vrampage-md-circuit-config', 'schemaVersion': 1,
                        'configuration': {
                            'vram': {'modelId': 1, 'mask': 0, 'pair': None},
                            'ram': None, 'psg': [1, 6], 'fm': [0, 7]
                        }
                    }
                    page.locator('#circuitConfigFile').set_input_files({
                        'name': 'unsupported-normal-config.json', 'mimeType': 'application/json',
                        'buffer': json.dumps(requested).encode()})
                    expect(page.locator('#circuitConfigApply')).to_be_enabled()
                    page.locator('#circuitConfigApply').click()
                    expect(page.locator('#circuitConfigStatus')).to_contain_text('does not support the requested PSG bridge')
                    after_reject = page.evaluate('''() => ({
                        addressMask: testCore._get_vram_address_mask(),
                        ramMask: testCore._get_logic_address_mask(),
                        vramModel: document.querySelector('#vramModel').value,
                        psgA: document.querySelector('#psgBridgeA').value,
                        fmA: document.querySelector('#fmBridgeA').value
                    })''')
                    self.assertEqual(after_reject, before, 'unsupported normal-core request is rejected before any mutation')
                    with page.expect_download() as download_info:
                        page.locator('#circuitConfigDownload').click()
                    saved = json.loads(Path(download_info.value.path()).read_text())
                    self.assertEqual(saved['schemaVersion'], 4)
                    self.assertEqual(saved['configuration'], {
                        'vram': {'modelId': 1, 'mask': 0, 'pair': None},
                        'ram': None, 'psg': {'pair':None,'dataMask':0}, 'fm': {'pair':None,'dataMask':0}, 'z80Ram':{'pair':None},
                        'rgbEncoder':{'cutMask':0,'pair':None}
                    })
                    self.assertNotIn('rom', saved)
                    self.assertNotIn('inputWrites', json.dumps(saved))
                    page.locator("#ramWriteMode").select_option("pulse")
                    pair=page.locator("[data-ram-frame-pair='10,11']")
                    expect(pair).to_be_enabled()
                    pair.click()
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    self.assertEqual(page.evaluate('testCore._get_logic_pulse_state()'),0,
                                     'eight-frame bridge uses the ordinary RAM setter, not native pulse expiry')
                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Pause')
                    expect(page.locator('#randomiserStatus')).to_contain_text(
                        'ended after 8 emulated frames',timeout=8000)
                    page.locator('#logicExperiment > summary').click()
                    with page.expect_download() as pulse_download:
                        page.locator('#logicExperimentBtn').click()
                    pulse_payload=json.loads(Path(pulse_download.value.path()).read_text())
                    pulse=pulse_payload['faultPulses'][-1]
                    self.assertEqual((pulse['a'],pulse['b']),(10,11))
                    self.assertEqual(pulse['access'],2)
                    self.assertGreater(pulse['writeCount'],8)
                    self.assertEqual(pulse['requestedFrames'],8)
                    self.assertNotIn('requestedWrites',pulse)
                    self.assertEqual(pulse['endFrame']-pulse['startFrame'],8)
                    self.assertFalse(pulse['cpuRecoveryAttempted'])
                    self.assertFalse(pulse['recoveryAccepted'])
                    self.assertEqual(errors, [])
                    browser.close()
            finally:
                server.shutdown()

    def test_circuit_configuration_uses_runtime_core_and_roundtrips_without_rom_data(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width': 1366, 'height': 768}, accept_downloads=True)
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    core_js = (OPTIONS.site_root / 'core/genplus.js').read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js', lambda route: route.fulfill(
                        content_type='text/javascript', body=core_js))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    page.locator('#romFile').set_input_files({
                        'name': 'original-circuit-config.bin',
                        'mimeType': 'application/octet-stream',
                        'buffer': original_cartridge()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.wait_for_function('window.testCore._get_logic_frame()>10')
                    api = page.evaluate('''() => ({
                        runtime: typeof testCore._set_vram_fault_model === 'function',
                        vram: testCore._get_vram_fault_model_state(),
                        supported: testCore._get_vram_supported_model_mask(),
                        psg: testCore._get_psg_data_bridge_state(),
                        fm: testCore._get_fm_data_bridge_state()
                    })''')
                    self.assertTrue(api['runtime'], 'the packaged browser core exposes the optional runtime model API')
                    self.assertEqual(api['supported'] & 4, 4, 'synthetic cartridge enables Mode 5 transaction support')
                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    expect(page.locator('#z80RamBridgeApply')).to_be_enabled()
                    self.assertFalse(page.evaluate('testCore._get_z80_ram_bridge_state().configured'))
                    page.locator('#z80RamBridgeA').select_option('0')
                    page.locator('#z80RamBridgeB').select_option('12')
                    page.locator('#z80RamBridgeApply').click()
                    z80=page.evaluate('testCore._get_z80_ram_bridge_state()')
                    self.assertEqual((z80['modelVersion'],z80['bridgeA'],z80['bridgeB']),
                                     ('z80-ram-write-address-pair-v1',0,12))
                    self.assertTrue(z80['configured'] and z80['effective'])
                    with page.expect_download() as z80_download:
                        page.locator('#circuitConfigDownload').click()
                    z80_saved=json.loads(Path(z80_download.value.path()).read_text())
                    self.assertEqual(z80_saved['configuration']['z80Ram'],{'pair':[0,12]})
                    payload = {
                        'format': 'vrampage-md-circuit-config', 'schemaVersion': 1,
                        'configuration': {
                            'vram': {'modelId': 2, 'mask': 0, 'pair': [2, 5]},
                            'ram': None, 'psg': [1, 6], 'fm': [0, 7]
                        }
                    }
                    before = page.evaluate('''() => ({
                        model: testCore._get_vram_fault_model_state(),
                        psg: testCore._get_psg_data_bridge_state(),
                        fm: testCore._get_fm_data_bridge_state(),
                        selector: document.querySelector('#vramModel').value
                    })''')
                    page.locator('#circuitConfigFile').set_input_files({
                        'name': 'runtime-config.json', 'mimeType': 'application/json',
                        'buffer': json.dumps(payload).encode()})
                    expect(page.locator('#circuitConfigStatus')).to_contain_text('Nothing has been applied')
                    after_preview = page.evaluate('''() => ({
                        model: testCore._get_vram_fault_model_state(),
                        psg: testCore._get_psg_data_bridge_state(),
                        fm: testCore._get_fm_data_bridge_state(),
                        selector: document.querySelector('#vramModel').value
                    })''')
                    self.assertEqual(after_preview, before, 'loading a file leaves actual core state and selectors unchanged')
                    page.locator('#circuitConfigApply').click()
                    state = page.evaluate('''() => ({
                        vram: testCore._get_vram_fault_model_state(),
                        psg: testCore._get_psg_data_bridge_state(),
                        fm: testCore._get_fm_data_bridge_state()
                    })''')
                    self.assertEqual((state['vram']['modelId'], state['vram']['bridgeA'], state['vram']['bridgeB']), (2, 2, 5))
                    self.assertFalse(page.evaluate('testCore._get_z80_ram_bridge_state().configured'),
                                     'legacy config import explicitly removes the new RAM fault')
                    self.assertTrue(state['psg']['configured'])
                    self.assertEqual((state['psg']['bridgeA'], state['psg']['bridgeB']), (1, 6))
                    self.assertTrue(state['fm']['configured'])
                    self.assertEqual((state['fm']['bridgeA'], state['fm']['bridgeB']), (0, 7))
                    # The chip-leg UI must call the production mask API. Grounding
                    # PSG inputs replaces its bridge while FM stays independent.
                    page.locator('#psgLegMode').select_option('ground')
                    page.locator('#psgChip .pin').nth(0).click()
                    page.locator('#psgChip .pin').nth(7).click()
                    masked = page.evaluate('testCore._get_psg_data_bridge_state()')
                    self.assertTrue(masked['configured'])
                    self.assertEqual(masked['dataMask'], 129)
                    self.assertEqual((masked['bridgeA'], masked['bridgeB']), (-1, -1))
                    self.assertEqual((page.evaluate('testCore._get_fm_data_bridge_state().bridgeA'),
                                      page.evaluate('testCore._get_fm_data_bridge_state().bridgeB')), (0, 7))
                    page.locator('#fmLegMode').select_option('ground')
                    page.locator('#fmChip .pin').nth(2).click()
                    self.assertEqual(page.evaluate('testCore._get_fm_data_bridge_state().dataMask'), 4)
                    self.assertEqual(page.evaluate('testCore._get_psg_data_bridge_state().dataMask'), 129,
                                     'FM leg changes preserve the independent PSG mask')
                    with page.expect_download() as download_info:
                        page.locator('#circuitConfigDownload').click()
                    saved = json.loads(Path(download_info.value.path()).read_text())
                    self.assertEqual(saved['schemaVersion'], 4)
                    self.assertEqual(saved['configuration']['fm'], {'pair':None,'dataMask':4})
                    self.assertEqual(saved['configuration']['psg'], {'pair':None,'dataMask':129})
                    self.assertNotIn('rom', saved)
                    self.assertNotIn('lastFrameCounts', json.dumps(saved))
                    ram_payload = {
                        'format': 'vrampage-md-circuit-config', 'schemaVersion': 1,
                        'configuration': {
                            'vram': {'modelId': 2, 'mask': 0, 'pair': None},
                            'ram': {'type': 'address-mask', 'mask': 1, 'access': 3},
                            'psg': [1, 6], 'fm': [0, 7]
                        }
                    }
                    page.locator('#circuitConfigFile').set_input_files({
                        'name': 'runtime-ram-config.json', 'mimeType': 'application/json',
                        'buffer': json.dumps(ram_payload).encode()})
                    expect(page.locator('#circuitConfigApply')).to_be_enabled()
                    page.locator('#circuitConfigApply').click()
                    ram_state = page.evaluate('''() => ({
                        mask: testCore._get_logic_address_mask(),
                        vram: testCore._get_vram_fault_model_state(),
                        psg: testCore._get_psg_data_bridge_state(),
                        fm: testCore._get_fm_data_bridge_state()
                    })''')
                    self.assertEqual(ram_state['mask'], 1)
                    self.assertEqual((ram_state['vram']['mask'],ram_state['vram']['bridgeA'],ram_state['vram']['bridgeB']), (0,-1,-1))
                    self.assertEqual(ram_state['fm']['dataMask'],0,
                                     'legacy pair import replaces the FM mask')
                    self.assertTrue(ram_state['psg']['configured'] and ram_state['fm']['configured'],
                                    'RAM handoff leaves independent PSG and FM configurations intact')
                    self.assertEqual(ram_state['psg']['dataMask'],0,
                                     'the imported pair replaces the previous PSG data mask')
                    with page.expect_download() as download_info:
                        page.locator('#circuitConfigDownload').click()
                    ram_saved=json.loads(Path(download_info.value.path()).read_text())
                    self.assertEqual(ram_saved['schemaVersion'], 4)
                    self.assertEqual(ram_saved['configuration']['psg'], {'pair':[1,6],'dataMask':0})
                    self.assertEqual(ram_saved['configuration']['fm'], {'pair':[0,7],'dataMask':0})
                    if not page.locator('#logicExperiment').evaluate('element => element.open'):
                        page.locator('#logicExperiment > summary').click()
                    with page.expect_download() as export_info:
                        page.locator('#logicExperimentBtn').click()
                    experiment = json.loads(Path(export_info.value.path()).read_text())
                    self.assertTrue(experiment['logic']['active'])
                    self.assertEqual(experiment['logic']['fault']['addressMask'], 1)
                    self.assertEqual(experiment['vramTransaction']['modelId'], 2)
                    self.assertTrue(experiment['psgInputFault']['configured'])
                    self.assertTrue(experiment['fmInputFault']['configured'])

                    page.locator('#circuitConfigFile').set_input_files({
                        'name': 'runtime-config.json', 'mimeType': 'application/json',
                        'buffer': json.dumps(payload).encode()})
                    page.locator('#circuitConfigApply').click()
                    self.assertEqual(page.evaluate('testCore._get_logic_address_mask()'), 0,
                                     'VRAM target handoff clears the active RAM fault')
                    state = page.evaluate('testCore._get_vram_fault_model_state()')
                    self.assertEqual((state['bridgeA'],state['bridgeB']), (2,5))
                    self.assertEqual(errors, [])
                    browser.close()
            finally:
                server.shutdown()

    def test_randomiser_mutates_only_selected_runtime_chip_and_exports_values(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width':1366,'height':768},accept_downloads=True)
                    errors=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    core_js=(OPTIONS.site_root/'core/genplus.js').read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='text/javascript',body=core_js))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    page.locator('#romFile').set_input_files({
                        'name':'original-randomiser.bin','mimeType':'application/octet-stream',
                        'buffer':original_cartridge()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.wait_for_function('window.testCore._get_logic_frame()>10')
                    page.locator('#pauseBtn').click()
                    starts=page.evaluate('window.testCore._get_logic_frame()')
                    def randomise(selector,value):
                        return page.locator(selector).evaluate('''(button,value)=>{
                          const saved=Math.random;let calls=0;Math.random=()=>{calls++;return value};
                          try { button.click(); return calls; } finally { Math.random=saved; }
                        }''',value)
                    self.assertEqual(randomise('#randomPsgBtn',0),2)
                    psg=page.evaluate('testCore._get_psg_data_bridge_state()')
                    self.assertEqual(psg['dataMask'],1)
                    self.assertEqual(page.evaluate('testCore._get_fm_data_bridge_state().dataMask'),0)
                    self.assertEqual(page.evaluate('testCore._get_vram_fault_model_state().mask'),0)

                    self.assertEqual(randomise('#randomFmBtn',0.999999),3)
                    fm=page.evaluate('testCore._get_fm_data_bridge_state()')
                    self.assertTrue(fm['configured'])
                    self.assertEqual((fm['bridgeA'],fm['bridgeB']),(6,7))
                    self.assertEqual(page.evaluate('testCore._get_psg_data_bridge_state().dataMask'),1)

                    page.locator('#vramModel').select_option('2')
                    selected_model=page.locator('#vramModel').input_value()
                    self.assertEqual(randomise('#randomVramBtn',0.999999),3)
                    vram=page.evaluate('testCore._get_vram_fault_model_state()')
                    self.assertEqual(vram['modelId'],int(selected_model))
                    self.assertEqual((vram['bridgeA'],vram['bridgeB']),(6,7))
                    self.assertEqual(page.evaluate('testCore._get_logic_address_mask()'),0)
                    self.assertEqual(page.locator('#pauseBtn').inner_text(),'Resume')
                    self.assertEqual(page.evaluate('testCore._get_logic_frame()'),starts,
                                     'randomisation does not start or advance a paused core')
                    with page.expect_download() as info:
                        page.locator('#circuitConfigDownload').click()
                    saved=json.loads(Path(info.value.path()).read_text())
                    self.assertEqual(saved['configuration']['psg'],{'pair':None,'dataMask':1})
                    self.assertEqual(saved['configuration']['fm'],{'pair':[6,7],'dataMask':0})
                    self.assertEqual(saved['configuration']['vram'],{'modelId':2,'mask':0,'pair':[6,7]})
                    self.assertEqual(errors,[])
                    browser.close()
            finally:
                server.shutdown()

    def test_audio_queue_is_bounded_across_pause_resume_and_visibility_event(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width': 1366, 'height': 768})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.add_init_script("""
                        const audioKey = window.AudioContext ? 'AudioContext' : 'webkitAudioContext';
                        const NativeAudioContext = window[audioKey];
                        window.__audioScheduleProbe = {starts: [], live: 0, connected: 0, created: 0,
                            peakConnected: 0, sources: []};
                        if (NativeAudioContext) {
                            const nativeCreateBufferSource = NativeAudioContext.prototype.createBufferSource;
                            NativeAudioContext.prototype.createBufferSource = function(...args) {
                                const source = Reflect.apply(nativeCreateBufferSource, this, args);
                                window.__audioScheduleProbe.created++;
                                source.__probeEnded = false;
                                source.__probeStopped = false;
                                window.__audioScheduleProbe.live++;
                                source.addEventListener('ended', () => {
                                    window.__audioScheduleProbe.live--;
                                    source.__probeEnded = true;
                                    if (source.__probeConnected) {
                                        source.__probeConnected = false;
                                        window.__audioScheduleProbe.connected--;
                                    }
                                }, {once: true});
                                const nativeConnect = source.connect;
                                source.connect = function(...args) {
                                    window.__audioScheduleProbe.connected++;
                                    window.__audioScheduleProbe.peakConnected = Math.max(
                                        window.__audioScheduleProbe.peakConnected,
                                        window.__audioScheduleProbe.connected);
                                    return Reflect.apply(nativeConnect, source, args);
                                };
                                const nativeDisconnect = source.disconnect;
                                source.disconnect = function(...args) {
                                    if (source.__probeConnected) {
                                        source.__probeConnected = false;
                                        window.__audioScheduleProbe.connected--;
                                    }
                                    return Reflect.apply(nativeDisconnect, source, args);
                                };
                                const trackedConnect = source.connect;
                                source.connect = function(...args) {
                                    source.__probeConnected = true;
                                    return Reflect.apply(trackedConnect, source, args);
                                };
                                const nativeStop = source.stop;
                                source.stop = function(...args) {
                                    source.__probeStopped = true;
                                    return Reflect.apply(nativeStop, source, args);
                                };
                                const nativeStart = source.start;
                                source.start = function(...startArgs) {
                                    const buffer = source.buffer;
                                    let finite = !!buffer;
                                    if (buffer) {
                                        for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
                                            const samples = buffer.getChannelData(channel);
                                            for (let i = 0; i < samples.length; i++) {
                                                if (!Number.isFinite(samples[i])) { finite = false; break; }
                                            }
                                        }
                                    }
                                    const now = source.context.currentTime;
                                    const when = startArgs.length ? startArgs[0] : now;
                                    window.__audioScheduleProbe.sources.push({source, when});
                                    window.__audioScheduleProbe.starts.push({
                                        now, when, lead: when - now, sampleRate: buffer?.sampleRate ?? 0,
                                        channels: buffer?.numberOfChannels ?? 0,
                                        duration: buffer?.duration ?? 0, finite,
                                        visibilityEventSynthetic: window.__syntheticVisibilityProbe || false
                                    });
                                    return Reflect.apply(nativeStart, source, startArgs);
                                };
                                return source;
                            };
                            window[audioKey] = new Proxy(NativeAudioContext, {
                                construct(target, args) {
                                    const context = Reflect.construct(target, args);
                                    window.testAudioContext = context;
                                    return context;
                                }
                            });
                        }
                    """)
                    core_js = (OPTIONS.site_root / 'core/genplus.js').read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js', lambda route: route.fulfill(
                        content_type='text/javascript', body=core_js))
                    build_info={'application':'VRAMpage MD','application_version':'0.5.0',
                                'source_commit':'b'*40,'package_format':1}
                    page.route('**/build-info.json',lambda route:route.fulfill(
                        content_type='application/json',body=json.dumps(build_info)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    page.locator('#romFile').set_input_files({
                        'name':'original-audio-queue.bin',
                        'mimeType':'application/octet-stream',
                        'buffer':original_cartridge()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Mute Sound')
                    page.wait_for_function('window.__audioScheduleProbe.starts.length >= 6')

                    initial = page.evaluate('''() => ({
                        contextRate: window.testAudioContext.sampleRate,
                        starts: window.__audioScheduleProbe.starts.slice()
                    })''')
                    self.assertEqual(initial['contextRate'], 44100)
                    self.assertTrue(initial['starts'])
                    for start in initial['starts']:
                        self.assertEqual(start['sampleRate'], 44100)
                        self.assertEqual(start['channels'], 2)
                        self.assertTrue(start['finite'], 'real AudioBuffer samples are finite')
                        self.assertGreaterEqual(start['lead'], -0.005)
                        self.assertLessEqual(start['lead'], 0.205,
                                             'scheduled audio lead stays within the 200 ms cap plus tolerance')

                    suspended = page.evaluate('''async () => {
                        await window.testAudioContext.suspend();
                        const stateAtSuspension = window.testAudioContext.state;
                        // suspend() can leave rendering active until its promise resolves.
                        const before = {created: window.__audioScheduleProbe.created,
                            connected: window.__audioScheduleProbe.connected};
                        const frame = testCore._get_logic_frame();
                        await new Promise(resolve => {
                            const check = () => testCore._get_logic_frame() >= frame + 60
                                ? resolve() : requestAnimationFrame(check);
                            requestAnimationFrame(check);
                        });
                        const during = window.__audioScheduleProbe.created;
                        const connected = window.__audioScheduleProbe.connected;
                        const stateAfterFrames = window.testAudioContext.state;
                        await window.testAudioContext.resume();
                        const resumeStartCount = window.__audioScheduleProbe.starts.length;
                        return {before, during, connected, resumeStartCount,
                            stateAtSuspension, stateAfterFrames};
                    }''')
                    self.assertEqual(suspended['stateAtSuspension'], 'suspended')
                    self.assertEqual(suspended['stateAfterFrames'], 'suspended')
                    self.assertLessEqual(suspended['during'] - suspended['before']['created'], 1,
                                         'suspended context does not accumulate new source buffers')
                    self.assertEqual(suspended['connected'], 0,
                                     'suspended context disconnects prior live sources once')
                    resume_start_count = suspended['resumeStartCount']
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.length > n',
                                           arg=resume_start_count)
                    resumed_start = page.evaluate('n=>window.__audioScheduleProbe.starts[n]',
                                                  resume_start_count)
                    self.assertLessEqual(resumed_start['lead'], 0.055,
                                         'audio resumes with a fresh source near current time')

                    page.wait_for_function('''() => window.__audioScheduleProbe.sources.some(({source,when}) =>
                        when > window.testAudioContext.currentTime && !source.__probeEnded &&
                        !source.__probeStopped && source.__probeConnected)''',
                                           timeout=3000)
                    pause_probe = page.evaluate('''() => {
                        const future = window.__audioScheduleProbe.sources.filter(({source,when}) =>
                            when > window.testAudioContext.currentTime && !source.__probeEnded &&
                            !source.__probeStopped && source.__probeConnected).length;
                        document.querySelector('#pauseBtn').click();
                        return {future, live: window.__audioScheduleProbe.live,
                                connected: window.__audioScheduleProbe.connected};
                    }''')
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    paused_count = page.evaluate('window.__audioScheduleProbe.starts.length')
                    paused_connected = pause_probe['connected']
                    self.assertGreater(pause_probe['future'], 0,
                                       'pause reproduction begins with genuinely future-scheduled sources')
                    self.assertEqual(paused_connected, 0,
                                     f'pause disconnects future real sources: {pause_probe}')
                    page.wait_for_timeout(250)
                    self.assertEqual(page.evaluate('window.__audioScheduleProbe.starts.length'), paused_count,
                                     'pause stops scheduling new sources')
                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Pause')
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.length > n',
                                            arg=paused_count)
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Enable Sound')
                    self.assertEqual(page.evaluate('window.__audioScheduleProbe.connected'), 0,
                                     'mute disconnects every queued real AudioBufferSource')
                    muted_count = page.evaluate('window.__audioScheduleProbe.starts.length')
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Mute Sound')
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.length > n',
                                            arg=muted_count)

                    before_visibility = page.evaluate('''() => {
                        const count = window.__audioScheduleProbe.starts.length;
                        const hidden = document.hidden;
                        window.__syntheticVisibilityProbe = true;
                        document.dispatchEvent(new Event('visibilitychange'));
                        return {count, hidden, connected: window.__audioScheduleProbe.connected};
                    }''')
                    self.assertFalse(before_visibility['hidden'],
                                     'visibility check uses a visible page and a synthetic event')
                    self.assertEqual(before_visibility['connected'], 0,
                                     'visibility change disconnects queued real sources')
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.slice(n).some(s=>s.visibilityEventSynthetic)',
                                            arg=before_visibility['count'])
                    visibility_start = page.evaluate('''n=>window.__audioScheduleProbe.starts
                        .slice(n).find(s=>s.visibilityEventSynthetic)''',
                        before_visibility['count'])
                    self.assertTrue(visibility_start['visibilityEventSynthetic'],
                                    'this is a dispatched visibility event, not OS backgrounding')
                    self.assertLessEqual(visibility_start['lead'], 0.055,
                                         'observed source start after the synthetic event is near current time')
                    page.wait_for_function('window.__audioScheduleProbe.connected > 0')
                    page.evaluate('''() => {
                        const start = testCore._start;
                        window.__startConnectedSources = [];
                        testCore._start = function(...args) {
                            window.__startConnectedSources.push(window.__audioScheduleProbe.connected);
                            return Reflect.apply(start, this, args);
                        };
                    }''')
                    page.locator('#romFile').set_input_files({
                        'name':'replacement-audio-queue.bin',
                        'mimeType':'application/octet-stream',
                        'buffer':original_cartridge()})
                    expect(page.locator('#romName')).to_have_text('REPLACEMENT-AUDIO-QUEUE.BIN')
                    self.assertEqual(page.evaluate('window.__startConnectedSources'), [0],
                                     'ROM replacement drains live old sources before the new core starts')
                    all_starts = page.evaluate('window.__audioScheduleProbe.starts')
                    peak_connected = page.evaluate('window.__audioScheduleProbe.peakConnected')
                    self.assertLessEqual(peak_connected, 16,
                                         'connected genuine buffers remain within the scheduling horizon')
                    for start in all_starts:
                        self.assertEqual(start['sampleRate'], 44100)
                        self.assertEqual(start['channels'], 2)
                        self.assertTrue(start['finite'])
                        self.assertLessEqual(start['lead'], 0.205,
                                             'all real source starts respect the bounded scheduling lead')
                    self.assertEqual(errors, [])
                    browser.close()
            finally:
                server.shutdown()

    def test_chip_shortcuts_held_writes_and_compact_restart_use_runtime_core(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width': 1366, 'height': 768})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    core_js = (OPTIONS.site_root / 'core/genplus.js').read_text()
                    core_js += '''
                        const originalFactory=window.Module;
                        window.Module=opts=>originalFactory(opts).then(c=>{
                          window.testCore=c;
                          window.nativeCalls={_start:[],_set_logic_fault:[],_recover_logic_cpu:[]};
                          for(const key of Object.keys(nativeCalls)) {
                            const native=c[key];
                            c[key]=(...args)=>{nativeCalls[key].push(args);return native(...args)};
                          }
                          return c;
                        });
                    '''
                    page.route('**/core/genplus.js', lambda route: route.fulfill(
                        content_type='text/javascript', body=core_js))
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    page.wait_for_function('!!window.testCore')
                    expect(page.locator('#resetBtn')).to_be_disabled()
                    expect(page.locator('#compactResetBtn')).to_be_disabled()
                    page.locator('#romFile').set_input_files({
                        'name': 'original-shortcut-hold.bin',
                        'mimeType': 'application/octet-stream', 'buffer': original_cartridge()})
                    expect(page.locator('#romName')).to_have_text('ORIGINAL-SHORTCUT-HOLD.BIN')
                    expect(page.locator('#compactResetBtn')).to_be_enabled()
                    page.wait_for_function('testCore._get_logic_frame()>3')
                    page.locator('#pauseBtn').click()
                    page.locator('h1').click()
                    self.assertEqual(page.locator('.chip-card.fault-active').count(), 0)
                    expect(page.locator('[data-keyboard-chip="VRAM"]')).to_have_class(
                        re.compile(r'.*keyboard-target.*'))
                    page.keyboard.press('Digit9')
                    self.assertEqual(page.evaluate('''() => {
                      const v=testCore._get_vram_fault_model_state();return [v.bridgeA,v.bridgeB];
                    }'''), [0, 7])
                    page.keyboard.press('Digit9')
                    page.keyboard.press('Digit0')
                    expect(page.locator('#keyboardTarget')).to_contain_text('WRAM')
                    expect(page.locator('#ramWriteMode')).to_have_value('hold')
                    page.locator('h1').click()
                    page.keyboard.down('Digit9')
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [1, 2, 12, 14])
                    expect(page.locator('[data-keyboard-chip=WRAM]')).to_have_class(re.compile(r'.*fault-active.*'))
                    self.assertEqual(page.locator('[data-keyboard-chip=VRAM].fault-active').count(), 0)
                    calls = page.evaluate('nativeCalls._set_logic_fault.length')
                    start = page.evaluate('testCore._get_logic_frame()')
                    page.locator('#pauseBtn').click()
                    page.wait_for_function('(n)=>testCore._get_logic_frame()>=n+12', arg=start)
                    page.locator('#pauseBtn').click()
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.length'), calls,
                                     'held writes do not expire after eight frames')
                    page.locator('h1').click()
                    page.keyboard.up('Digit9')
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [0, 0, -1, -1])
                    self.assertEqual(page.evaluate('nativeCalls._recover_logic_cpu'), [])
                    pair = page.locator('[data-ram-frame-pair="10,11"]')
                    pair.hover()
                    page.mouse.down()
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [1, 2, 10, 11])
                    start = page.evaluate('testCore._get_logic_frame()')
                    page.keyboard.press('KeyP')
                    page.wait_for_function('(n)=>testCore._get_logic_frame()>=n+12', arg=start)
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [1, 2, 10, 11])
                    # This generated cartridge writes FF1000, which distinguishes A11/A12.
                    self.assertGreater(page.evaluate('Number(testCore._get_logic_writes())'), 0)
                    page.mouse.up()
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [0, 0, -1, -1])
                    page.keyboard.press('KeyP')
                    self.assertEqual(page.evaluate('nativeCalls._recover_logic_cpu'), [])
                    page.locator('h1').click()
                    page.keyboard.press('Digit0')
                    expect(page.locator('#keyboardTarget')).to_contain_text('FM')
                    page.keyboard.press('Digit9')
                    page.keyboard.press('Digit0')
                    expect(page.locator('#keyboardTarget')).to_contain_text('PSG')
                    page.keyboard.press('Digit9')
                    state = page.evaluate('''() => {
                      const f=testCore._get_fm_data_bridge_state(),p=testCore._get_psg_data_bridge_state();
                      return {fm:[f.bridgeA,f.bridgeB],psg:[p.bridgeA,p.bridgeB]};
                    }''')
                    self.assertEqual(state, {'fm': [0, 7], 'psg': [0, 7]})
                    audio_before=page.evaluate('''() => ({fm:testCore._get_fm_data_bridge_state(),psg:testCore._get_psg_data_bridge_state()})''')
                    page.locator('#logicCpuResetBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    self.assertEqual(page.evaluate('''() => ({fm:testCore._get_fm_data_bridge_state(),psg:testCore._get_psg_data_bridge_state()})'''),audio_before,
                                     'paused CPU Reset preserves audio fault settings and counters')
                    self.assertEqual(page.evaluate('nativeCalls._recover_logic_cpu'), [[2]])
                    self.assertEqual(page.evaluate('nativeCalls._start.length'), 1)
                    self.assertEqual(page.locator('[data-keyboard-chip=FM].fault-active,[data-keyboard-chip=PSG].fault-active').count(), 2)
                    page.keyboard.press('Digit0')
                    expect(page.locator('#keyboardTarget')).to_contain_text('VRAM')
                    self.assertEqual(page.evaluate('nativeCalls._start.length'), 1)
                    for index, reset in enumerate(['#compactResetBtn', '#resetBtn'], start=2):
                        page.locator(reset).click()
                        page.wait_for_function('(n)=>nativeCalls._start.length===n', arg=index)
                        self.assertFalse(page.evaluate('testCore._get_fm_data_bridge_state().configured'))
                        self.assertFalse(page.evaluate('testCore._get_psg_data_bridge_state().configured'))
                        expect(page.locator('#resetBtn')).to_be_enabled()
                        expect(page.locator('#compactResetBtn')).to_be_enabled()
                    self.assertEqual(page.evaluate('nativeCalls._recover_logic_cpu'), [[2]])
                    self.assertEqual(page.locator('.chip-card.fault-active').count(), 0)
                    page.locator('#pauseBtn').click()
                    page.locator('#ramWriteMode').select_option('hold')
                    button = page.locator('[data-ram-frame-pair="10,11"]')
                    page.evaluate("window.randomVramClicks=0;document.querySelector('#randomVramBtn').addEventListener('click',()=>window.randomVramClicks++)")
                    button.focus()
                    page.keyboard.down('Space')
                    expect(page.locator('#randomVramBtn')).to_be_disabled()
                    self.assertFalse(page.locator('#randomVramBtn').evaluate("b=>b.matches(':active')"))
                    ram_calls = page.evaluate('nativeCalls._set_logic_fault.length')
                    before_vram = page.evaluate('''() => {
                      const v=testCore._get_vram_fault_model_state();return [v.modelId,v.mask,v.bridgeA,v.bridgeB];
                    }''')
                    page.keyboard.press('Digit1')
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.length'), ram_calls,
                                     'a focused WRAM contact must not be cleared by a VRAM shortcut')
                    self.assertEqual(page.evaluate('''() => {
                      const v=testCore._get_vram_fault_model_state();return [v.modelId,v.mask,v.bridgeA,v.bridgeB];
                    }'''), before_vram)
                    expect(page.locator('[data-keyboard-chip=WRAM]')).to_have_class(re.compile(r'.*fault-active.*'))
                    self.assertEqual(page.locator('[data-keyboard-chip=VRAM].fault-active').count(), 0)
                    page.keyboard.press('Digit0')
                    expect(page.locator('#keyboardTarget')).to_contain_text('WRAM')
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.length'), ram_calls)
                    page.keyboard.up('Space')
                    self.assertEqual(page.evaluate('nativeCalls._set_logic_fault.at(-1)'), [0, 0, -1, -1])
                    expect(page.locator('#randomVramBtn')).to_be_enabled()
                    self.assertEqual(page.evaluate('window.randomVramClicks'), 0)
                    self.assertEqual(page.locator('.chip-card.fault-active').count(), 0)
                    self.assertEqual(errors, [])
                    browser.close()
            finally:
                server.shutdown()

    def test_original_video_audio_and_controls_from_static_subdirectory(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root.parent)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = new_manual_startup_page(browser, viewport={'width': 1366, 'height': 768}, accept_downloads=True)
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    console_messages = []
                    page.on('console', lambda entry: console_messages.append(f'{entry.type}: {entry.text}'))
                    # Observe the genuine context without replacing its audio implementation.
                    page.add_init_script("""
                        const audioKey = window.AudioContext ? 'AudioContext' : 'webkitAudioContext';
                        const NativeAudioContext = window[audioKey];
                        if (NativeAudioContext) window[audioKey] = new Proxy(NativeAudioContext, {
                            construct(target, args) {
                                const context = Reflect.construct(target, args);
                                window.testAudioContext = context;
                                return context;
                            }
                        });
                    """)
                    # Capture the real instantiated module without replacing its behavior.
                    core_js = (OPTIONS.site_root / 'core/genplus.js').read_text()
                    core_js += '\nconst originalFactory=window.Module; window.Module=opts=>originalFactory(opts).then(c=>{window.testCore=c; return c;});\n'
                    page.route('**/core/genplus.js', lambda route: route.fulfill(content_type='text/javascript', body=core_js))
                    # A fixture manifest exercises provenance without mocking the real core.
                    build_info={'application':'VRAMpage MD','application_version':'0.5.0',
                                'source_commit':'b'*40,'package_format':1}
                    page.route('**/build-info.json',lambda route:route.fulfill(
                        content_type='application/json',body=json.dumps(build_info)))
                    wasm_responses = []
                    page.on('response', lambda response: wasm_responses.append(response)
                            if response.url.endswith('/core/genplus.wasm') else None)
                    page.goto(f'http://127.0.0.1:{server.server_port}/{OPTIONS.site_root.name}/')
                    page.wait_for_function('!!window.testCore')
                    self.assertTrue(wasm_responses, 'Core WASM must load from the hosting subdirectory')
                    self.assertTrue(all(response.ok and response.headers.get('content-type') == 'application/wasm'
                                        for response in wasm_responses))
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
                    try:
                        expect(page.locator('#soundBtn')).to_have_text('Mute Sound')
                    except AssertionError as error:
                        audio_state = page.evaluate("""() => {
                            const c = window.testAudioContext;
                            return c ? {state:c.state,sampleRate:c.sampleRate,currentTime:c.currentTime} : null;
                        }""")
                        self.fail(f"{error}\nNative audio state: {audio_state}\nBrowser console: {console_messages}"
                                  f"\nApplication event log:\n{page.locator('#experimentLog').text_content()}")
                    page.wait_for_function("window.testAudioContext?.state==='running' && window.testAudioContext.currentTime>0")
                    page.locator('#soundBtn').click()
                    expect(page.locator('#soundBtn')).to_have_text('Enable Sound')
                    psg_api=page.evaluate("typeof testCore._set_psg_data_bridge==='function'")
                    fm_api=page.evaluate("typeof testCore._set_fm_data_bridge==='function'")
                    if psg_api:
                        page.evaluate('''() => {
                            window.__nativePsgState=testCore._get_psg_data_bridge_state;
                            testCore._get_psg_data_bridge_state=()=>{throw new Error('injected state failure')};
                        }''')
                        expect(page.locator('#psgBridgeStatus')).to_contain_text('runtime state is unavailable')
                        expect(page.locator('#psgBridgeApply')).to_be_disabled()
                        self.assertEqual(errors,[], 'optional PSG state failure does not break the page')
                        page.evaluate('testCore._get_psg_data_bridge_state=window.__nativePsgState')
                        expect(page.locator('#psgBridgeApply')).to_be_enabled()
                        page.locator('#psgBridgeA').select_option('0')
                        page.locator('#psgBridgeB').select_option('7')
                        page.locator('#psgBridgeApply').click()
                        psg_state=page.evaluate('testCore._get_psg_data_bridge_state()')
                        self.assertTrue(psg_state['effective'])
                        self.assertEqual((psg_state['bridgeA'],psg_state['bridgeB']),(0,7))
                        self.assertIn('D0',page.locator('#psgBridgeStatus').inner_text())
                        frame_before=page.evaluate('testCore._get_logic_frame()')
                        page.locator('#psgBridgeA').select_option('2')
                        page.locator('#psgBridgeB').select_option('6')
                        page.wait_for_function('frame=>testCore._get_logic_frame()>=frame+4',arg=frame_before)
                        self.assertEqual((page.locator('#psgBridgeA').input_value(),page.locator('#psgBridgeB').input_value()),('2','6'),
                                         'frame refresh preserves the uncommitted pair draft')
                        page.locator('#psgBridgeApply').click()
                        psg_state=page.evaluate('testCore._get_psg_data_bridge_state()')
                        self.assertTrue(psg_state['effective'])
                        self.assertEqual((psg_state['bridgeA'],psg_state['bridgeB']),(2,6),
                                         'Apply commits the retained pair draft to the core')
                    else:
                        expect(page.locator('#psgBridgeApply')).to_be_disabled()
                        self.assertIn('does not provide',page.locator('#psgBridgeStatus').inner_text())
                    if fm_api:
                        page.evaluate('''() => {
                            window.__nativeFmState=testCore._get_fm_data_bridge_state;
                            testCore._get_fm_data_bridge_state=()=>{throw new Error('injected FM state failure')};
                        }''')
                        expect(page.locator('#fmBridgeStatus')).to_contain_text('runtime state is unavailable')
                        expect(page.locator('#fmBridgeApply')).to_be_disabled()
                        self.assertEqual(errors,[], 'optional FM state failure does not break the page')
                        page.evaluate('testCore._get_fm_data_bridge_state=window.__nativeFmState')
                        expect(page.locator('#fmBridgeApply')).to_be_enabled()
                        page.locator('#fmBridgeA').select_option('0')
                        page.locator('#fmBridgeB').select_option('5')
                        page.locator('#fmBridgeApply').click()
                        fm_state=page.evaluate('testCore._get_fm_data_bridge_state()')
                        self.assertTrue(fm_state['effective'])
                        self.assertEqual((fm_state['bridgeA'],fm_state['bridgeB']),(0,5))
                        frame_before=page.evaluate('testCore._get_logic_frame()')
                        page.locator('#fmBridgeA').select_option('2')
                        page.locator('#fmBridgeB').select_option('6')
                        page.wait_for_function('frame=>testCore._get_logic_frame()>=frame+4',arg=frame_before)
                        self.assertEqual((page.locator('#fmBridgeA').input_value(),page.locator('#fmBridgeB').input_value()),('2','6'),
                                         'frame refresh preserves the uncommitted FM pair draft')
                        page.locator('#fmBridgeApply').click()
                        fm_state=page.evaluate('testCore._get_fm_data_bridge_state()')
                        self.assertTrue(fm_state['effective'])
                        self.assertEqual((fm_state['bridgeA'],fm_state['bridgeB']),(2,6),
                                         'Apply commits the retained FM pair draft to the core')
                    else:
                        expect(page.locator('#fmBridgeApply')).to_be_disabled()
                        self.assertIn('does not provide',page.locator('#fmBridgeStatus').inner_text())
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
                    page.locator('#pinGrid .pin').nth(0).click()
                    page.locator('#pinGrid .pin').nth(1).click()
                    expect(page.locator('#pinGrid .pin.connected')).to_have_count(2)
                    page.locator('#vramSettings').evaluate('(details)=>{details.open=true}')
                    page.locator('#disconnectBtn').click()
                    expect(page.locator('#pinGrid .pin.connected')).to_have_count(0)
                    page.locator('#vramMode').select_option('disconnect')
                    page.locator('#pinGrid .pin').nth(0).click()
                    page.locator('#pinGrid .pin').nth(7).focus()
                    page.keyboard.press('Space')
                    page.wait_for_function('testCore._get_vram_address_mask()===129')
                    expect(page.locator('#pinGrid .pin').nth(7).locator('.chip-cut')).to_have_css('visibility','visible')
                    page.locator('#disconnectBtn').click()
                    page.wait_for_function('testCore._get_vram_address_mask()===0')
                    page.locator('#logicExperiment > summary').click()
                    page.locator('[data-chip-line]').nth(0).click()
                    page.wait_for_function('testCore._get_logic_address_mask()===1')
                    expect(page.locator('[data-chip-line]').nth(0).locator('.chip-cut')).to_have_css('visibility','visible')
                    page.locator('#chipRestoreBtn').click()
                    page.wait_for_function('testCore._get_logic_address_mask()===0')
                    page.locator('#logicApplyBtn').click()
                    page.locator('#manualForceResumeBtn').click()
                    page.locator('#logicCpuResetBtn').click()
                    with page.expect_download() as download:
                        page.locator('#logicExperimentBtn').click()
                    payload=json.loads(Path(download.value.path()).read_text())
                    self.assertEqual(payload['modelVersion'],'0.5.0-experimental')
                    self.assertEqual(payload['schemaVersion'],1)
                    self.assertEqual(payload['build'],{'status':'available','applicationVersion':'0.5.0','sourceCommit':'b'*40})
                    self.assertEqual(payload['vramFault']['addressMask'],0)
                    self.assertEqual([e['mask'] for e in payload['vramAddressLineChanges']],[1,129,0])
                    self.assertEqual(payload['rom']['name'],'original-video-tone.bin')
                    self.assertEqual(len(payload['rom']['sha256']),64)
                    self.assertNotIn('romBytes',payload)
                    self.assertEqual(payload['psgInputFault']['schemaVersion'],2)
                    self.assertEqual(payload['psgInputFault']['available'],psg_api)
                    if psg_api:
                        self.assertEqual(payload['psgInputFault']['modelVersion'],'psg-data-low-dominant-v2')
                        self.assertTrue(payload['psgInputFault']['configured'])
                    self.assertEqual(payload['fmInputFault']['schemaVersion'],2)
                    self.assertEqual(payload['fmInputFault']['available'],fm_api)
                    if fm_api:
                        self.assertEqual(payload['fmInputFault']['modelVersion'],'fm-register-data-low-dominant-v2')
                        self.assertTrue(payload['fmInputFault']['configured'])
                    # Exercise coordinated removal against the actual native configuration.
                    if page.locator('#pauseBtn').inner_text()=='Pause':
                        page.locator('#pauseBtn').click()
                    for kind,bit,available in [('psg',4,psg_api),('fm',3,fm_api)]:
                        if available:
                            page.locator(f'#{kind}LegMode').select_option('ground')
                            page.locator(f'#{kind}Chip .pin').nth(bit).click()
                            self.assertEqual(page.evaluate(f'testCore._get_{kind}_data_bridge_state().dataMask'),1<<bit)
                    page.locator('#vramMode').select_option('disconnect')
                    page.locator('#pinGrid .pin').nth(0).click()
                    page.evaluate("""() => {
                      window.__disconnectCpuCalls=0; window.__disconnectStartCalls=0;
                      window.__disconnectRecover=testCore._recover_logic_cpu;
                      window.__disconnectStart=testCore._start;
                      testCore._recover_logic_cpu=(...args)=>{++window.__disconnectCpuCalls;return window.__disconnectRecover(...args)};
                      testCore._start=(...args)=>{++window.__disconnectStartCalls;return window.__disconnectStart(...args)};
                    }""")
                    frame=page.evaluate('testCore._get_logic_frame()')
                    for attempt in range(2):
                        if attempt:
                            # The first clear began paused and deliberately kept it paused.
                            # Exercise the running-success path separately after an explicit resume.
                            page.locator('#pauseBtn').click()
                            page.wait_for_function('frame=>testCore._get_logic_frame()>frame',arg=frame)
                            frame=page.evaluate('testCore._get_logic_frame()')
                            page.locator('[data-chip-line]').nth(0).click()
                            self.assertEqual(page.evaluate('testCore._get_logic_address_mask()'),1)
                        paused_before=page.locator('#pauseBtn').inner_text()=='Resume'
                        frame=page.evaluate("""() => {
                          const frame=testCore._get_logic_frame();
                          document.querySelector('#disconnectAllFaultsBtn').click();
                          return frame;
                        }""")
                        all_domains_available=psg_api and fm_api
                        expected_pause='Resume' if paused_before or not all_domains_available else 'Pause'
                        self.assertEqual(page.locator('#pauseBtn').inner_text(),expected_pause,
                                         page.locator('#disconnectAllFaultsStatus').inner_text())
                        if paused_before or not all_domains_available:
                            self.assertEqual(page.evaluate('testCore._get_logic_frame()'),frame,
                                             'paused or incomplete disconnect must stop before another frame')
                        else:
                            self.assertGreaterEqual(page.evaluate('testCore._get_logic_frame()'),frame)
                        frame=page.evaluate('testCore._get_logic_frame()')
                        self.assertEqual(page.evaluate('[window.__disconnectCpuCalls,window.__disconnectStartCalls]'),[0,0])
                        self.assertEqual(page.evaluate('testCore._get_vram_address_mask()'),0)
                        self.assertEqual(page.evaluate('testCore._get_logic_address_mask()'),0)
                        for kind,available in [('psg',psg_api),('fm',fm_api)]:
                            if available:
                                self.assertFalse(page.evaluate(f'testCore._get_{kind}_data_bridge_state().configured'))
                        page.wait_for_timeout(40)
                        if all_domains_available and not paused_before:
                            self.assertGreater(page.evaluate('testCore._get_logic_frame()'),frame,
                                               'confirmed running clear must keep emulation ticking')
                        else:
                            self.assertEqual(page.evaluate('testCore._get_logic_frame()'),frame,
                                             'paused or incomplete disconnect must stop before another frame')
                        frame=page.evaluate('testCore._get_logic_frame()')
                    self.assertTrue(page.evaluate("typeof testCore._set_logic_fault==='function'"),
                                    'actual core exposes ordinary Work RAM bridge support')
                    if page.locator('#pauseBtn').inner_text()!='Pause':
                        page.locator('#pauseBtn').click()
                    before=page.evaluate("testCore._get_logic_frame()")
                    page.locator("#ramWriteMode").select_option("pulse")
                    page.locator("[data-ram-frame-pair='10,11']").click()
                    expect(page.locator('#randomiserStatus')).to_contain_text('ended after 8 emulated frames',timeout=8000)
                    expect(page.locator('#pauseBtn')).to_have_text('Pause')
                    with page.expect_download() as download:
                        page.locator('#logicExperimentBtn').click()
                    cleared=json.loads(Path(download.value.path()).read_text())
                    self.assertEqual(cleared['cpuInterventions'],payload['cpuInterventions'])
                    self.assertEqual(len(cleared['faultDisconnects']),2)
                    self.assertEqual([row['domain'] for row in cleared['faultDisconnects'][-1]['results']],['VRAM','RAM','PSG','FM','Z80 RAM','RGB Encoder'])
                    self.assertEqual(cleared['faultDisconnects'][-1]['action'],'all-domain-disconnect')
                    burst=cleared['faultPulses'][-1]
                    self.assertEqual((burst['a'],burst['b']),(10,11))
                    self.assertEqual(burst['access'],2)
                    self.assertGreater(burst['writeCount'],8)
                    self.assertEqual(burst['requestedFrames'],8)
                    self.assertNotIn('requestedWrites',burst)
                    self.assertEqual(burst['endFrame']-burst['startFrame'],8)
                    self.assertFalse(burst['cpuRecoveryAttempted'])
                    self.assertFalse(burst['recoveryAccepted'])
                    self.assertGreaterEqual(burst['endFrame'],before)
                    page.evaluate('testCore._recover_logic_cpu=window.__disconnectRecover;testCore._start=window.__disconnectStart')
                    page.locator('#resetBtn').click()
                    page.wait_for_function('testCore._get_logic_address_mask()===0')
                    if psg_api:
                        page.wait_for_function('!testCore._get_psg_data_bridge_state().configured')
                    if fm_api:
                        page.wait_for_function('!testCore._get_fm_data_bridge_state().configured')
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    self.assertEqual(errors,[])
                    browser.close()
            finally:
                server.shutdown()


    def test_rgb_encoder_changes_canvas_without_mutating_actual_core(self):
        handler=partial(SimpleHTTPRequestHandler,directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs={'executable_path':OPTIONS.executable} if OPTIONS.executable else {}
                    browser=getattr(p,OPTIONS.browser).launch(**kwargs)
                    try:
                        for profile in ['runtime','normal']:
                            with self.subTest(profile=profile):
                                page=new_manual_startup_page(browser, accept_downloads=True)
                                errors=[]
                                page.on('pageerror',lambda error:errors.append(str(error)))
                                page.add_init_script("""window.testFrames=[];window.testTime=0;
                                    window.requestAnimationFrame=cb=>testFrames.push(cb);
                                    window.stepTestFrame=()=>{const q=testFrames.splice(0);testTime+=17;q.forEach(cb=>cb(testTime));};""")
                                core_dir=OPTIONS.site_root/('core' if profile=='runtime' else 'source/src/main/js')
                                core_js=(core_dir/'genplus.js').read_text()
                                core_js+='''\nconst originalFactory=window.Module;
                                    window.Module=opts=>originalFactory(opts).then(c=>{
                                        window.testCore=c;window.rgbNativeCalls=[];
                                        for(const key of ['_tick','_sound','_recover_logic_cpu','_start']) {
                                            const original=c[key];
                                            c[key]=(...args)=>{rgbNativeCalls.push(key);return original(...args);};
                                        }return c;
                                    });\n'''
                                page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='text/javascript',body=core_js))
                                if profile=='normal':
                                    page.route('**/core/genplus.wasm',lambda route:route.fulfill(
                                        content_type='application/wasm',body=(core_dir/'genplus.wasm').read_bytes()))
                                page.goto(f'http://127.0.0.1:{server.server_port}/')
                                expect(page.locator('[data-rgb-cut="0"]')).to_be_disabled()
                                page.locator('#romFile').set_input_files({'name':'original-rgb.bin','mimeType':'application/octet-stream','buffer':original_cartridge()})
                                expect(page.locator('#romName')).to_have_text('ORIGINAL-RGB.BIN')
                                expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                                page.evaluate('for(let i=0;i<32;i++)stepTestFrame()')
                                page.locator('#pauseBtn').click()
                                page.locator('#logicExperiment > summary').click()
                                page.evaluate("""window.rgbRegions=[
                                    [testCore._get_frame_buffer_ref(),640*480*4],
                                    [testCore._get_logic_ram_ref(),65536],
                                    [testCore._get_web_audio_l_ref(),700*4],
                                    [testCore._get_web_audio_r_ref(),700*4]];
                                    if(testCore._get_z80_ram_ref)rgbRegions.push([testCore._get_z80_ram_ref(),8192]);
                                    window.rgbBefore=rgbRegions.map(([start,n])=>testCore.HEAPU8.slice(start,start+n));
                                    window.rgbCanvasIs=expected=>{
                                        const pixels=document.querySelector('#screen').getContext('2d').getImageData(0,0,320,224).data;
                                        return pixels.every((v,i)=>v===expected[i%4]);
                                    };
                                    rgbNativeCalls.length=0;""")
                                self.assertTrue(page.evaluate('rgbCanvasIs([238,0,0,255])'),'literal Mode 5 red palette output')
                                page.locator('[data-rgb-pair="0,1"]').click()
                                self.assertTrue(page.evaluate('rgbCanvasIs([119,119,0,255])'),'equal source impedances join red and green')
                                page.locator('#rawVideoToggle').check()
                                self.assertTrue(page.evaluate('rgbCanvasIs([238,0,0,255])'),'Raw Output bypasses configured contacts')
                                with page.expect_download() as downloaded:page.locator('#logicExperimentBtn').click()
                                payload=json.loads(Path(downloaded.value.path()).read_text())
                                self.assertEqual(payload['rgbEncoderFault'],{
                                    'schemaVersion':1,'available':True,'modelVersion':'rgb-input-code-voltage-v1',
                                    'cutMask':0,'pair':[0,1],'configured':True,'effective':False,'reason':'raw-output-bypass'})
                                page.locator('#rawVideoToggle').uncheck()
                                page.locator('[data-rgb-cut="0"]').click()
                                self.assertTrue(page.evaluate('rgbCanvasIs([0,0,0,255])'),'cuts apply before the joined pair')
                                page.locator('#rgbEncoderClear').click()
                                self.assertTrue(page.evaluate('rgbCanvasIs([238,0,0,255])'))
                                self.assertEqual(page.evaluate('rgbNativeCalls'),[],'paused output edits must not tick, synthesize sound or intervene in the CPU')
                                self.assertTrue(page.evaluate('rgbRegions.every(([start,n],i)=>rgbBefore[i].every((v,j)=>v===testCore.HEAPU8[start+j]))'),
                                    'native frame, full Work RAM, Z80 RAM and generated stereo PCM stay byte-identical')
                                if profile=='runtime':
                                    page.locator('#saveCheckpointBtn').click()
                                    expect(page.locator('#checkpointStatus')).to_contain_text('Saved Frame')
                                page.locator('[data-rgb-pair="0,2"]').click()
                                page.locator('#logicCpuResetBtn').click()
                                expect(page.locator('[data-rgb-pair="0,2"]')).to_have_attribute('aria-pressed','true')
                                if profile=='runtime':
                                    page.locator('#restoreCheckpointBtn').click()
                                    expect(page.locator('#checkpointStatus')).to_contain_text('Restored Frame')
                                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                                    expect(page.locator('[data-rgb-pair="0,2"]')).to_have_attribute('aria-pressed','false')
                                page.locator('[data-rgb-cut="2"]').click()
                                page.locator('#compactResetBtn').click()
                                expect(page.locator('[data-rgb-cut="2"]')).to_have_attribute('aria-pressed','false')
                                expect(page.locator('#rgbEncoderClear')).to_be_disabled()
                                self.assertEqual(errors,[])
                                page.close()
                    finally:browser.close()
            finally:server.shutdown()

    def test_session_checkpoint_restores_actual_image_without_ticking(self):
        handler=partial(SimpleHTTPRequestHandler,directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs={'executable_path':OPTIONS.executable} if OPTIONS.executable else {}
                    browser=getattr(p,OPTIONS.browser).launch(**kwargs)
                    try:
                        page=new_manual_startup_page(browser, accept_downloads=True)
                        errors=[]
                        page.on('pageerror',lambda error:errors.append(str(error)))
                        page.add_init_script("""window.testFrames=[];window.testTime=0;
                            window.requestAnimationFrame=cb=>testFrames.push(cb);
                            window.stepTestFrame=()=>{const q=testFrames.splice(0);testTime+=17;q.forEach(cb=>cb(testTime));};""")
                        core_js=(OPTIONS.site_root/'core/genplus.js').read_text()
                        core_js+='''\nconst originalFactory=window.Module;
                            window.Module=opts=>originalFactory(opts).then(c=>{
                                window.testCore=c;window.checkpointTicks=0;
                                const tick=c._tick;c._tick=()=>{checkpointTicks++;return tick();};return c;
                            });\n'''
                        page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='text/javascript',body=core_js))
                        page.goto(f'http://127.0.0.1:{server.server_port}/')
                        page.locator('#romFile').set_input_files({'name':'original-checkpoint.bin','mimeType':'application/octet-stream','buffer':original_cartridge()})
                        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                        page.evaluate('for(let i=0;i<32;i++)stepTestFrame()')
                        page.locator('#pauseBtn').click()
                        page.locator('#logicExperiment > summary').click()
                        expect(page.locator('#saveCheckpointBtn')).to_be_enabled()
                        page.evaluate("""window.checkpointImage=Array.from(testCore.HEAPU8.subarray(testCore._get_frame_buffer_ref(),testCore._get_frame_buffer_ref()+640*480*4));
                            window.checkpointCanvas=document.querySelector('#screen').toDataURL();""")
                        ticks=page.evaluate('checkpointTicks')
                        page.locator('#saveCheckpointBtn').click()
                        expect(page.locator('#checkpointStatus')).to_contain_text('Saved Frame')
                        self.assertEqual(page.evaluate('checkpointTicks'),ticks)
                        page.locator('#pauseBtn').click()
                        page.evaluate('for(let i=0;i<10;i++)stepTestFrame()')
                        page.locator('#pauseBtn').click()
                        page.evaluate('testCore.HEAPU8.fill(0,testCore._get_frame_buffer_ref(),testCore._get_frame_buffer_ref()+640*480*4)')
                        page.locator('#rawVideoToggle').check()
                        self.assertFalse(page.evaluate("document.querySelector('#screen').toDataURL()===checkpointCanvas"))
                        ticks=page.evaluate('checkpointTicks')
                        page.locator('#randomPsgBtn').click()
                        page.locator('#restoreCheckpointBtn').click()
                        expect(page.locator('#checkpointStatus')).to_contain_text('Restored Frame')
                        expect(page.locator('#pauseBtn')).to_have_text('Resume')
                        self.assertEqual(page.evaluate('checkpointTicks'),ticks)
                        self.assertTrue(page.evaluate('checkpointImage.every((v,i)=>v===testCore.HEAPU8[testCore._get_frame_buffer_ref()+i])'))
                        self.assertFalse(page.evaluate('testCore._get_psg_data_bridge_state().configured'))
                        page.locator('#rawVideoToggle').uncheck()
                        self.assertTrue(page.evaluate("document.querySelector('#screen').toDataURL()===checkpointCanvas"))
                        with page.expect_download() as info:page.locator('#logicExperimentBtn').click()
                        payload=json.loads(Path(info.value.path()).read_text())
                        self.assertEqual(payload['checkpointSegment'],1)
                        self.assertEqual([event['outcome'] for event in payload['checkpointEvents']],['saved','restored'])
                        page.locator('#resetBtn').click()
                        expect(page.locator('#restoreCheckpointBtn')).to_be_disabled()
                        self.assertEqual(errors,[])
                    finally:browser.close()
            finally:server.shutdown()

    def test_ordered_recovery_defaults_on_and_observes_real_halt_and_stop(self):
        handler=partial(SimpleHTTPRequestHandler,directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs={'executable_path':OPTIONS.executable} if OPTIONS.executable else {}
                    browser=getattr(p,OPTIONS.browser).launch(**kwargs)
                    try:
                        halt_words=[0x2e7c,0,1,0x3039,0x00ff,1,0x4e72,0x2700]
                        for kind,words,force_on,cpu_on in [
                            ('halt',halt_words,True,True),
                            ('stop',[0x4e72,0x2700,0x60fe],True,True),
                            ('halt-force-off',halt_words,False,True),
                            ('halt-cpu-off',halt_words,True,False)]:
                            with self.subTest(cpu=kind):
                                page=new_manual_startup_page(browser, accept_downloads=True)
                                errors=[]
                                page.on('pageerror',lambda error:errors.append(str(error)))
                                page.add_init_script("""window.testFrames=[];window.testTime=0;
                                    window.requestAnimationFrame=cb=>testFrames.push(cb);
                                    window.stepTestFrame=()=>{const q=testFrames.splice(0);testTime+=17;q.forEach(cb=>cb(testTime));};""")
                                core_js=(OPTIONS.site_root/'core/genplus.js').read_text()
                                core_js+='''\nconst originalFactory=window.Module;
                                window.Module=opts=>originalFactory(opts).then(c=>{
                                    window.testCore=c;window.recoveryCalls=[];
                                    const recover=c._recover_logic_cpu;
                                    c._recover_logic_cpu=mode=>{
                                        const before=[c._get_psg_data_bridge_state?.(),c._get_fm_data_bridge_state?.()];
                                        const ramStart=c._get_logic_ram_ref()>>>0;
                                        const ramBefore=Array.from(c.HEAPU8.subarray(ramStart,ramStart+65536));
                                        const status=recover(mode);
                                        const ramAfter=c.HEAPU8.subarray(ramStart,ramStart+65536);
                                        recoveryCalls.push({mode,status,frame:c._get_logic_frame(),flagsAfter:c._get_logic_cpu_flags(),
                                            before,after:[c._get_psg_data_bridge_state?.(),c._get_fm_data_bridge_state?.()],
                                            ramPreserved:ramBefore.every((value,index)=>value===ramAfter[index])});
                                        return status;
                                    };return c;
                                });\n'''
                                page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='text/javascript',body=core_js))
                                page.goto(f'http://127.0.0.1:{server.server_port}/')
                                expect(page.locator('#logicResumeBtn')).to_have_text('Force Resume: On')
                                expect(page.locator('#armCpuRecoveryBtn')).to_have_text('CPU Recovery: On')
                                expect(page.locator('#logicResumeBtn')).to_have_attribute('aria-pressed','true')
                                expect(page.locator('#armCpuRecoveryBtn')).to_have_attribute('aria-pressed','true')
                                if not force_on:page.locator('#logicResumeBtn').click()
                                if not cpu_on:page.locator('#armCpuRecoveryBtn').click()
                                expect(page.locator('#logicResumeBtn')).to_have_attribute('aria-pressed',str(force_on).lower())
                                expect(page.locator('#armCpuRecoveryBtn')).to_have_attribute('aria-pressed',str(cpu_on).lower())
                                rom=bytearray(original_cartridge())
                                for i,value in enumerate(words):struct.pack_into('>H',rom,0x200+2*i,value)
                                page.locator('#romFile').set_input_files({'name':f'original-{kind}.bin','mimeType':'application/octet-stream','buffer':bytes(rom)})
                                expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                                page.evaluate('stepTestFrame()') # Prime the app clock before the first emulated frame.
                                page.locator('#logicExperiment > summary').click()
                                if kind!='stop':
                                    page.locator('#psgBridgeApply').click()
                                    page.locator('#fmBridgeApply').click()
                                if kind!='stop':
                                    expected_calls=1
                                    page.evaluate(f'for(let i=0;i<35 && recoveryCalls.length<{expected_calls};i++)stepTestFrame()')
                                    calls=page.evaluate('recoveryCalls')
                                    expected_modes=[1] if force_on else [2]
                                    self.assertEqual([call['mode'] for call in calls],expected_modes,
                                        'Enabled recovery stages run in order and disabled stages are skipped')
                                    self.assertTrue(all(call['status']==0 for call in calls))
                                    self.assertTrue(all(call['ramPreserved'] for call in calls),
                                        'Synchronous CPU interventions preserve all 64 KiB of Work RAM')
                                    self.assertTrue(all(call['before']==call['after'] for call in calls),
                                        'CPU interventions preserve synchronous PSG/FM fault snapshots')
                                    self.assertFalse(calls[0]['flagsAfter'] & 2,
                                        'The issued CPU action clears HALT synchronously')
                                    self.assertTrue(all(state['configured'] for state in calls[0]['before']))
                                    if kind=='halt':
                                        # This real CPU continues after Force Resume; do not escalate to reset.
                                        page.evaluate('for(let i=0;i<20;i++)stepTestFrame()')
                                        self.assertEqual(page.evaluate('recoveryCalls.length'),1)
                                        self.assertFalse(page.evaluate('(testCore._get_logic_cpu_flags() & 2)!==0'))
                                        expect(page.locator('#cpuRecoveryStatus')).to_contain_text('Recovery Used / Cancelled')
                                    with page.expect_download() as downloaded:page.locator('#logicExperimentBtn').click()
                                    payload=json.loads(Path(downloaded.value.path()).read_text())
                                    entries=[entry for entry in payload['cpuInterventions'] if entry.get('trigger')=='halt-recovery-sequence']
                                    self.assertEqual(len(entries),expected_calls)
                                    self.assertEqual([entry['action'] for entry in entries],
                                        ['force-resume'] if expected_modes==[1] else ['cpu-only-reset'])
                                    if expected_modes==[1]:
                                        self.assertEqual(entries[0]['stage'],'force-resume')
                                        self.assertEqual(entries[0]['waitFrames'],2)
                                        self.assertEqual(len(entries[0]['observedFrames']),2)
                                        self.assertEqual(entries[0]['observedFrames'][1]-entries[0]['observedFrames'][0],1)
                                    else:
                                        self.assertEqual(entries[0]['stage'],'cpu-reset')
                                        self.assertEqual(entries[0]['waitFrames'],2)
                                else:
                                    # A genuine STOP is ignored even with both automatic controls On.
                                    page.evaluate('for(let i=0;i<20;i++)stepTestFrame()')
                                    self.assertEqual(page.evaluate('recoveryCalls'),[])
                                    self.assertTrue(page.evaluate('(testCore._get_logic_cpu_flags() & 1)!==0'))
                                self.assertEqual(errors,[])
                                page.close()
                    finally:browser.close()
            finally:server.shutdown()

    def test_mixed_fault_endurance_128_actual_core_cycles(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    try:
                        page = new_manual_startup_page(browser, viewport={'width':1366,'height':768})
                        errors=[]
                        page.on('pageerror',lambda error:errors.append(str(error)))
                        page.add_init_script("""
                          window.testFrames=[];window.testTime=0;
                          window.requestAnimationFrame=cb=>testFrames.push(cb);
                          window.stepTestFrame=()=>{const q=testFrames.splice(0);testTime+=17;q.forEach(cb=>cb(testTime));};
                          const Native=window.AudioContext||window.webkitAudioContext;
                          window.soakAudio={contexts:0,created:0,active:new Set(),maxActive:0,finite:true};
                          if(Native){
                            const create=Native.prototype.createBufferSource;
                            Native.prototype.createBufferSource=function(...args){
                              const source=Reflect.apply(create,this,args),p=window.soakAudio;
                              p.created++;const connect=source.connect,disconnect=source.disconnect,start=source.start;
                              source.connect=function(...a){const r=Reflect.apply(connect,this,a);p.active.add(source);p.maxActive=Math.max(p.maxActive,p.active.size);return r;};
                              source.disconnect=function(...a){p.active.delete(source);return Reflect.apply(disconnect,this,a);};
                              source.addEventListener('ended',()=>p.active.delete(source),{once:true});
                              source.start=function(...a){const b=source.buffer;if(!b)p.finite=false;else for(let c=0;c<b.numberOfChannels;c++)for(const v of b.getChannelData(c))if(!Number.isFinite(v))p.finite=false;return Reflect.apply(start,this,a);};
                              return source;
                            };
                            window.AudioContext=new Proxy(Native,{construct(t,a){window.soakAudio.contexts++;window.testAudioContext=Reflect.construct(t,a);return window.testAudioContext;}});
                            if(window.webkitAudioContext)window.webkitAudioContext=window.AudioContext;
                          }
                        """)
                        core_js=(OPTIONS.site_root/'core/genplus.js').read_text()
                        core_js+='''\nconst originalFactory=window.Module;window.testModuleCount=0;window.Module=opts=>{window.testModuleCount++;return originalFactory(opts).then(c=>{window.testCore=c;window.soakCalls={ticks:0,starts:0,samples:0,recovery:[]};for(const key of ['_tick','_start','_sound','_recover_logic_cpu']){const native=c[key];c[key]=(...args)=>{if(key===\"_tick\")soakCalls.ticks++;if(key===\"_start\")soakCalls.starts++;if(key===\"_recover_logic_cpu\")soakCalls.recovery.push(args[0]);const result=Reflect.apply(native,c,args);if(key===\"_sound\")soakCalls.samples=result;return result;};}return c;});};\n'''
                        page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='text/javascript',body=core_js))
                        page.goto(f'http://127.0.0.1:{server.server_port}/')
                        # RAF is controlled by this test; readiness must use timer polling.
                        page.wait_for_function('!!window.testCore',polling=10)
                        page.locator('#romFile').set_input_files({'name':'original-mixed-z80.bin','mimeType':'application/octet-stream','buffer':original_z80_store_cartridge()})
                        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                        page.locator('#soundBtn').click()
                        expect(page.locator('#soundBtn')).to_have_text('Mute Sound')
                        page.wait_for_function('testAudioContext.currentTime>0',polling=10)
                        page.locator('#logicExperiment > summary').evaluate('(b)=>b.click()')
                        page.locator('#logicResumeBtn').evaluate('(b)=>{if(b.getAttribute("aria-pressed")==="true")b.click()}')
                        page.locator('#armCpuRecoveryBtn').evaluate('(b)=>{if(b.getAttribute("aria-pressed")==="true")b.click()}')
                        page.evaluate('for(let i=0;i<2;i++)stepTestFrame()')
                        self.assertEqual(page.evaluate('''() => ({force:document.querySelector('#logicResumeBtn').getAttribute('aria-pressed'),cpu:document.querySelector('#armCpuRecoveryBtn').getAttribute('aria-pressed'),heap:testCore.HEAPU8.buffer.byteLength})''')['force'],'false')
                        page.evaluate('(rom)=>{window.enduranceRom=Uint8Array.from(rom)}',list(original_z80_store_cartridge()))
                        page.locator('#z80RamBridgeA').select_option('11')
                        page.locator('#z80RamBridgeB').select_option('12')
                        page.locator('#ramWriteMode').select_option('pulse')
                        report=page.evaluate('''async () => {
  const c=testCore, audio=soakAudio;
  const $=s=>document.querySelector(s), click=s=>$(s).click();
  let cycle=-1, warmHeap, driven=0, boundaries=0, warmups=0, measured=0;
  const check=(ok,label)=>{if(!ok)throw Error(`cycle ${cycle}: ${label}`)};
  const bytes=(ref,n)=>c.HEAPU8.slice(ref>>>0,(ref>>>0)+n);
  const equal=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
  const inputs=()=>Array.from(new Float32Array(c.HEAPF32.buffer,c._get_input_buffer_ref(),32));
  const image=()=>bytes(c._get_frame_buffer_ref(),640*480*4);
  const canvas=()=>$('#screen').toDataURL();
  const paused=()=>$('#pauseBtn').textContent==='Resume';
  const vram=()=>c._get_vram_fault_model_state();
  const sound=()=>[c._get_fm_data_bridge_state(),c._get_psg_data_bridge_state()];
  const pcm=()=>[bytes(c._get_web_audio_l_ref(),soakCalls.samples*4),bytes(c._get_web_audio_r_ref(),soakCalls.samples*4)];
  const off=()=>{
    const v=vram();
    return !v.mask&&v.bridgeA===-1&&v.bridgeB===-1&&!v.effective&&
      !c._get_logic_address_mask()&&!c._get_z80_ram_bridge_state().configured&&
      sound().every(s=>!s.configured)&&$('#rgbEncoderClear').disabled&&
      !document.querySelector('[data-ram-frame-pair][aria-pressed="true"]');
  };
  const clear=()=>{
    const prior=paused(),tick=soakCalls.ticks;click('#disconnectAllFaultsBtn');
    check(paused()===prior&&soakCalls.ticks===tick,'disconnect changed pause/tick state');
    check($('#disconnectAllFaultsStatus').textContent.includes('completed')&&off(),'six-domain clear incomplete');
  };
  const step=n=>{
    const start=soakCalls.ticks,nativeFrame=c._get_logic_frame()>>>0;
    for(let i=0;i<n+5&&soakCalls.ticks-start<n;i++)stepTestFrame();
    check(soakCalls.ticks-start===n,`expected ${n} completed ticks, got ${soakCalls.ticks-start}`);
    check(((c._get_logic_frame()-nativeFrame)>>>0)===n,'native completed-frame counter delta differed');
    driven+=n;
  };
  const random=(selector,value)=>{
    const old=Math.random;Math.random=()=>value;
    try{click(selector)}finally{Math.random=old}
  };
  const wait=async(predicate,label)=>{
    for(let i=0;i<100&&!predicate();i++)await new Promise(resolve=>setTimeout(resolve,5));
    check(predicate(),label);
  };
  const load=bytes=>{
    const dt=new DataTransfer();dt.items.add(new File([bytes],`accepted-${cycle}.bin`));
    $('#romFile').files=dt.files;$('#romFile').dispatchEvent(new Event('change',{bubbles:true}));
  };
  step(4);
  check(image().some((v,i)=>i%4!==3&&v!==0),'generated video must contain coloured RGB pixels');
  const base=new Float32Array(c.HEAPF32.buffer,c._get_web_audio_l_ref(),soakCalls.samples);
  check(base.some(v=>Math.abs(v)>0.0001)&&base.every(Number.isFinite),'generated baseline tone must be nonzero and finite');
  for(cycle=0;cycle<130;cycle++){
    check(!paused(),'cycle did not begin running');clear();
    check($('#logicResumeBtn').getAttribute('aria-pressed')==='false'&&$('#armCpuRecoveryBtn').getAttribute('aria-pressed')==='false','automatic recovery was enabled');
    $('#vramModel').value=cycle%2?'1':'2';$('#vramModel').dispatchEvent(new Event('change',{bubbles:true}));
    random('#randomFmBtn',cycle%3===0?0:0.999999);
    random('#randomPsgBtn',cycle%3===1?0:0.999999);
    click('#z80RamBridgeApply');click('[data-rgb-pair="0,1"]');
    if(cycle%2){
      click('[data-ram-frame-pair="10,11"]');step(7);
      check(c._get_logic_writes()>0,'Work RAM pulse did not affect eligible writes');
      check($('#randomiserStatus').textContent.includes('active'),'pulse ended before eight frames');
      step(1);
      check($('#randomiserStatus').textContent.includes('ended after 8 emulated frames'),'pulse did not end at eight frames');
      const count=c._get_logic_writes();step(1);
      check(c._get_logic_writes()===count,'Work RAM pulse kept affecting writes after release');
    }else{
      random('#randomVramBtn',0.999999);
      check(vram().effective,'transaction VRAM fault did not activate');step(8);
      check(vram().lastFrameCounts.logicalByteReads>0,'transaction VRAM saw no reads');
    }
    const activeSound=sound(),z=c._get_z80_ram_bridge_state();
    check(z.configured&&z.effective&&BigInt(z.z80Writes)>0n,'active Z80 bridge saw no driver stores');
    check(activeSound.every(s=>s.configured&&BigInt(s.inputWrites)>0n),'FM/PSG contacts saw no driver writes');
    check($('#rgbEncoderClear').disabled===false,'RGB pair did not activate');
    click('#pauseBtn');
    check(audio.active.size===0,'pause left connected audio sources');
    const ticks=soakCalls.ticks,nativeFrame=c._get_logic_frame()>>>0,ram=bytes(c._get_logic_ram_ref(),65536),zram=bytes(c._get_z80_ram_ref(),8192),samples=pcm();
    click('#logicCpuResetBtn');
    check(soakCalls.ticks===ticks&&(c._get_logic_frame()>>>0)===nativeFrame&&paused(),'CPU Reset ticked or resumed');
    check(equal(ram,bytes(c._get_logic_ram_ref(),65536))&&equal(zram,bytes(c._get_z80_ram_ref(),8192)),'CPU Reset changed RAM');
    const afterPcm=pcm();
    check(equal(samples[0],afterPcm[0])&&equal(samples[1],afterPcm[1])&&JSON.stringify(sound())===JSON.stringify(activeSound),'CPU Reset changed PCM/audio fault state');
    check(!c._get_z80_ram_bridge_state().configured&&!vram().effective&&!vram().mask&&vram().bridgeA===-1&&vram().bridgeB===-1,'CPU Reset retained memory contacts');
    check($('#rgbEncoderClear').disabled===false,'CPU Reset removed RGB contacts');
    click('#pauseBtn');
    if(cycle<2||(cycle-2)%16===15){
      clear();click('#pauseBtn');
      const savedImage=image(),savedCanvas=canvas(),savedRam=bytes(c._get_logic_ram_ref(),65536),savedZram=bytes(c._get_z80_ram_ref(),8192);
      const savedFrame=c._get_logic_frame()>>>0;
      click('#saveCheckpointBtn');check($('#checkpointStatus').textContent.includes('Saved Frame'),'checkpoint save refused');
      check((c._get_session_checkpoint_saved_frame()>>>0)===savedFrame,'saved-frame telemetry differed');
      check(!$('#restoreCheckpointBtn').disabled,'saved checkpoint unavailable');
      // A held Work RAM contact excludes VRAM; exercise both sequentially.
      random('#randomVramBtn',0.999999);clear();
      $('#ramWriteMode').value='hold';$('#ramWriteMode').dispatchEvent(new Event('change',{bubbles:true}));
      const hold=$('[data-ram-frame-pair="10,11"]');hold.focus();
      hold.dispatchEvent(new KeyboardEvent('keydown',{key:' ',code:'Space',bubbles:true}));
      check(hold.getAttribute('aria-pressed')==='true','RAM hold did not activate');
      random('#randomFmBtn',0);random('#randomPsgBtn',0);click('#z80RamBridgeApply');click('[data-rgb-pair="0,1"]');
      document.body.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',code:'ArrowRight',bubbles:true}));
      click('#pauseBtn');step(1);check(inputs()[6]===1,'held controller input missing');click('#pauseBtn');
      c.HEAPU8.fill(0,c._get_frame_buffer_ref(),c._get_frame_buffer_ref()+640*480*4);
      click('#rawVideoToggle');click('#rawVideoToggle');
      check(!equal(savedImage,image())&&savedCanvas!==canvas(),'checkpoint image-change probe was vacuous');
      const beforeRestore=soakCalls.ticks,beforeRestoreFrame=c._get_logic_frame()>>>0;click('#restoreCheckpointBtn');
      check($('#checkpointStatus').textContent.includes('Restored Frame'),'checkpoint restore refused');
      check(paused()&&soakCalls.ticks===beforeRestore&&(c._get_logic_frame()>>>0)===beforeRestoreFrame&&off(),'restore did not clear contacts and stay paused without ticks');
      check((c._get_session_checkpoint_saved_frame()>>>0)===savedFrame,'restore changed saved-frame telemetry');
      check(equal(savedImage,image())&&canvas()===savedCanvas,'checkpoint did not restore raw/canvas image');
      check(equal(savedRam,bytes(c._get_logic_ram_ref(),65536))&&equal(savedZram,bytes(c._get_z80_ram_ref(),8192)),'checkpoint RAM replay differed');
      check(inputs().every(v=>v===0),'restore retained held controller input');
      document.body.dispatchEvent(new KeyboardEvent('keyup',{key:'ArrowRight',code:'ArrowRight',bubbles:true}));
      hold.dispatchEvent(new KeyboardEvent('keyup',{key:' ',code:'Space',bubbles:true}));
      check(off(),'late key release reinstalled contacts');
      $('#ramWriteMode').value='pulse';$('#ramWriteMode').dispatchEvent(new Event('change',{bubbles:true}));
      click('#pauseBtn');step(1);check(audio.active.size>0,'boundary audio drain probe had no connected source');
      click('#soundBtn');check(audio.active.size===0,'mute did not drain sources');click('#soundBtn');
      step(1);check(audio.active.size>0,'visibility drain probe had no connected source');
      document.dispatchEvent(new Event('visibilitychange'));check(audio.active.size===0,'synthetic visibility did not drain');
      click('#pauseBtn');click('[data-rgb-cut="0"]');
      const acceptedName=$('#romName').textContent,startCount=soakCalls.starts;
      load(new Uint8Array(256));
      await wait(()=>$('#experimentLog').firstElementChild.textContent.includes('Expected a 512-byte'),'rejected load did not finish');
      check($('#romName').textContent===acceptedName&&soakCalls.starts===startCount&&!$('#restoreCheckpointBtn').disabled&&!$('#rgbEncoderClear').disabled&&paused(),'rejected cartridge changed accepted session');
      click('#resetBtn');
      check(soakCalls.starts===startCount+1&&off()&&$('#restoreCheckpointBtn').disabled&&!paused(),'Clean Restart did not reset contacts/checkpoint');
      load(window.enduranceRom);
      await wait(()=>$('#romName').textContent===`ACCEPTED-${cycle}.BIN`,'accepted replacement did not finish');
      check(soakCalls.starts===startCount+2&&off()&&$('#restoreCheckpointBtn').disabled&&!paused(),'accepted cartridge lifecycle differed');
      step(2);boundaries++;
    }
    if(cycle===1)warmHeap=c.HEAPU8.buffer.byteLength;
    if(cycle>=2)check(c.HEAPU8.buffer.byteLength===warmHeap,'WASM heap grew after warm-up');
    if(cycle<2)warmups++;else measured++;
  }
  click('#pauseBtn');check(audio.active.size===0,'final pause retained audio sources');
  check(soakCalls.recovery.length===130&&soakCalls.recovery.every(mode=>mode===2),'unexpected CPU intervention sequence');
  return {warmupCycles:warmups,measuredCycles:measured,warmupBoundaries:2,measuredBoundaries:boundaries-2,
    totalDrivenFrames:driven,heap:c.HEAPU8.buffer.byteLength,warmHeap,modules:testModuleCount,
    contexts:audio.contexts,createdSources:audio.created,peakConnected:audio.maxActive,
    finalConnected:audio.active.size,finitePcm:audio.finite,lastSamples:soakCalls.samples};
}
''')
                        self.assertEqual(report['measuredCycles'],128)
                        self.assertEqual(report['warmupCycles'],2)
                        self.assertEqual(report['measuredBoundaries'],8)
                        self.assertEqual(report['warmupBoundaries'],2)
                        self.assertEqual(report['modules'],1)
                        self.assertEqual(report['contexts'],1)
                        self.assertEqual(report['heap'],report['warmHeap'])
                        self.assertEqual(report['finalConnected'],0)
                        self.assertLessEqual(report['peakConnected'],16)
                        self.assertTrue(report['finitePcm'])
                        self.assertGreater(report['createdSources'],1000)
                        self.assertEqual(report['totalDrivenFrames'],1159)
                        self.assertGreater(report['lastSamples'],0)
                        self.assertEqual(errors,[])
                        print('Mixed-fault endurance metrics: '+json.dumps(report,sort_keys=True))
                    finally:browser.close()
            finally:server.shutdown()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--executable')
    parser.add_argument('--site-root',type=Path,default=ROOT / 'site')
    OPTIONS, remaining=parser.parse_known_args()
    unittest.main(argv=[__file__,*remaining],verbosity=2,
                  testRunner=unittest.TextTestRunner(verbosity=2,resultclass=AnnotatedBrowserResult))
