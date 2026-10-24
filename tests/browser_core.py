"""Actual compiled-core browser smoke with an original video/PSG test cartridge.

No commercial ROM, mock emulator, or game-derived data is used.
"""
import argparse
import json
import os
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


class AnnotatedBrowserResult(unittest.TextTestResult):
    """Keep CI failures readable when signed job-log downloads are unavailable."""
    def annotate(self, test, error):
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            message = self._exc_info_to_string(error, test)[-12000:]
            message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::error title=Actual-core browser failure::{message}', flush=True)

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.annotate(test, error)

    def addError(self, test, error):
        super().addError(test, error)
        self.annotate(test, error)


class ActualCoreBrowserTests(unittest.TestCase):
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
                    page = browser.new_page(viewport={'width': 1366, 'height': 768}, accept_downloads=True)
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
                    self.assertEqual(saved['configuration'], {
                        'vram': {'modelId': 1, 'mask': 0, 'pair': None},
                        'ram': None, 'psg': None, 'fm': None
                    })
                    self.assertNotIn('rom', saved)
                    self.assertNotIn('inputWrites', json.dumps(saved))
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
                    page = browser.new_page(viewport={'width': 1366, 'height': 768}, accept_downloads=True)
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
                    self.assertTrue(state['psg']['configured'])
                    self.assertEqual((state['psg']['bridgeA'], state['psg']['bridgeB']), (1, 6))
                    self.assertTrue(state['fm']['configured'])
                    self.assertEqual((state['fm']['bridgeA'], state['fm']['bridgeB']), (0, 7))
                    with page.expect_download() as download_info:
                        page.locator('#circuitConfigDownload').click()
                    saved = json.loads(Path(download_info.value.path()).read_text())
                    self.assertEqual(saved, payload)
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
                    self.assertTrue(ram_state['psg']['configured'] and ram_state['fm']['configured'],
                                    'RAM handoff leaves independent PSG and FM configurations intact')
                    with page.expect_download() as download_info:
                        page.locator('#circuitConfigDownload').click()
                    self.assertEqual(json.loads(Path(download_info.value.path()).read_text()), ram_payload)
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

    def test_audio_queue_is_bounded_across_pause_resume_and_visibility_event(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
        with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(p, OPTIONS.browser).launch(**kwargs)
                    page = browser.new_page(viewport={'width': 1366, 'height': 768})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.add_init_script("""
                        const audioKey = window.AudioContext ? 'AudioContext' : 'webkitAudioContext';
                        const NativeAudioContext = window[audioKey];
                        window.__audioScheduleProbe = {starts: []};
                        if (NativeAudioContext) {
                            const nativeCreateBufferSource = NativeAudioContext.prototype.createBufferSource;
                            NativeAudioContext.prototype.createBufferSource = function(...args) {
                                const source = Reflect.apply(nativeCreateBufferSource, this, args);
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
                                    window.__audioScheduleProbe.starts.push({
                                        now, when, lead: when - now, sampleRate: buffer?.sampleRate ?? 0,
                                        channels: buffer?.numberOfChannels ?? 0, finite,
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
                    build_info={'application':'VRAMpage MD','application_version':'0.4.0',
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

                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                    paused_count = page.evaluate('window.__audioScheduleProbe.starts.length')
                    page.wait_for_timeout(250)
                    self.assertEqual(page.evaluate('window.__audioScheduleProbe.starts.length'), paused_count,
                                     'pause stops scheduling new sources')
                    page.locator('#pauseBtn').click()
                    expect(page.locator('#pauseBtn')).to_have_text('Pause')
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.length > n',
                                            arg=paused_count)

                    before_visibility = page.evaluate('''() => {
                        const count = window.__audioScheduleProbe.starts.length;
                        const hidden = document.hidden;
                        window.__syntheticVisibilityProbe = true;
                        document.dispatchEvent(new Event('visibilitychange'));
                        return {count, hidden};
                    }''')
                    self.assertFalse(before_visibility['hidden'],
                                     'visibility check uses a visible page and a synthetic event')
                    page.wait_for_function('n=>window.__audioScheduleProbe.starts.slice(n).some(s=>s.visibilityEventSynthetic)',
                                            arg=before_visibility['count'])
                    visibility_start = page.evaluate('''n=>window.__audioScheduleProbe.starts
                        .slice(n).find(s=>s.visibilityEventSynthetic)''',
                        before_visibility['count'])
                    self.assertTrue(visibility_start['visibilityEventSynthetic'],
                                    'this is a dispatched visibility event, not OS backgrounding')
                    self.assertLessEqual(visibility_start['lead'], 0.055,
                                         'observed source start after the synthetic event is near current time')
                    all_starts = page.evaluate('window.__audioScheduleProbe.starts')
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

    def test_original_video_audio_and_controls(self):
        handler = partial(SimpleHTTPRequestHandler, directory=OPTIONS.site_root)
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
                    build_info={'application':'VRAMpage MD','application_version':'0.4.0',
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
                    self.assertEqual(payload['modelVersion'],'0.4.0-experimental')
                    self.assertEqual(payload['schemaVersion'],1)
                    self.assertEqual(payload['build'],{'status':'available','applicationVersion':'0.4.0','sourceCommit':'b'*40})
                    self.assertEqual(payload['vramFault']['addressMask'],0)
                    self.assertEqual([e['mask'] for e in payload['vramAddressLineChanges']],[1,129,0])
                    self.assertEqual(payload['rom']['name'],'original-video-tone.bin')
                    self.assertEqual(len(payload['rom']['sha256']),64)
                    self.assertNotIn('romBytes',payload)
                    self.assertEqual(payload['psgInputFault']['available'],psg_api)
                    if psg_api:
                        self.assertEqual(payload['psgInputFault']['modelVersion'],'psg-data-low-dominant-v1')
                        self.assertTrue(payload['psgInputFault']['configured'])
                    self.assertEqual(payload['fmInputFault']['available'],fm_api)
                    if fm_api:
                        self.assertEqual(payload['fmInputFault']['modelVersion'],'fm-register-data-low-dominant-v1')
                        self.assertTrue(payload['fmInputFault']['configured'])
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


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--executable')
    parser.add_argument('--site-root',type=Path,default=ROOT / 'site')
    OPTIONS, remaining=parser.parse_known_args()
    unittest.main(argv=[__file__,*remaining],verbosity=2,
                  testRunner=unittest.TextTestRunner(verbosity=2,resultclass=AnnotatedBrowserResult))
