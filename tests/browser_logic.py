"""Synthetic browser regressions for the logic/work-RAM UI and metadata export."""
import argparse
import hashlib
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from browser_result import AnnotatedBrowserResult
from browser_cartridge import choose_cartridge

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=ROOT / "site"))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        launch_options = {"executable_path": OPTIONS.executable} if OPTIONS.executable else {}
        cls.browser = getattr(cls.playwright, OPTIONS.browser).launch(**launch_options)
        cls.addClassCleanup(cls.browser.close)
        print(f"Browser: {OPTIONS.browser} {cls.browser.version}", flush=True)

    def setUp(self):
        self.contexts = []
        self.errors = []
        self.page = self.new_page()

    def tearDown(self):
        if OPTIONS.artifacts:
            OPTIONS.artifacts.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(
                path=str(OPTIONS.artifacts / f"{OPTIONS.browser}-{self._testMethodName}.png"),
                full_page=True,
            )
        for context in self.contexts:
            context.close()
        self.assertEqual(self.errors, [], "Uncaught application errors")

    def new_page(self, legacy_core=False, legacy_recovery=False, legacy_write_pulse=False, legacy_chip=False, legacy_vram_chip=False, build_info=None, stalled_build_info=False, circuit_config=False, legacy_psg_data=False, legacy_fm_data=False, legacy_psg_mask=False, legacy_fm_mask=False, manual_frames=False, session_checkpoint=False, automatic_recovery=False, legacy_z80_ram=False, region_core=False, demo_rom=False, stalled_demo=False, legacy_ram_data=False, legacy_write_inhibit=False, fm_output_model_core=False, unsupported_fm_output_model=False):
        context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            color_scheme="light",
            accept_downloads=True,
        )
        self.contexts.append(context)
        page = context.new_page()
        if legacy_write_inhibit:
            page.add_init_script("window.__legacyWriteInhibitCore = true;")
        if legacy_ram_data:
            page.add_init_script("window.__legacyRamDataCore = true;")
        if region_core:
            page.add_init_script("window.__regionCore = true;")
        if fm_output_model_core:
            page.add_init_script("window.__fmOutputModelCore = true;")
        if unsupported_fm_output_model:
            page.add_init_script("window.__unsupportedFmOutputModel = true;")
        if legacy_z80_ram:
            page.add_init_script("window.__legacyZ80RamCore = true;")
        if session_checkpoint:
            page.add_init_script("window.__sessionCheckpointCore = true;")
        if manual_frames:
            page.add_init_script("""
                window.testFrames=[];window.testTime=0;
                window.requestAnimationFrame=cb=>testFrames.push(cb);
                window.stepTestFrame=()=>{const callbacks=testFrames.splice(0);testTime+=17;callbacks.forEach(cb=>cb(testTime));};
            """)
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        if circuit_config:
            page.add_init_script("window.__circuitConfigCore = true;")
        if legacy_psg_data:
            page.add_init_script("window.__legacyPsgDataCore = true;")
        if legacy_fm_data:
            page.add_init_script("window.__legacyFmDataCore = true;")
        if legacy_psg_mask:
            page.add_init_script("window.__legacyPsgMaskCore = true;")
        if legacy_fm_mask:
            page.add_init_script("window.__legacyFmMaskCore = true;")
        if legacy_vram_chip:
            page.add_init_script("window.__legacyVramChipCore = true;")
        if legacy_chip:
            page.add_init_script("window.__legacyChipCore = true;")
        if legacy_write_pulse:
            page.add_init_script("window.__legacyWritePulseCore = true;")
        if legacy_recovery:
            page.add_init_script("window.__legacyRecoveryCore = true;")
        if legacy_core:
            page.add_init_script("window.__legacyLogicCore = true;")
        page.route("**/core/genplus.js", lambda route: route.fulfill(
            path=str(ROOT / "tests/fixtures/mock-core.js"),
            content_type="application/javascript"))
        # All existing tests exercise the manual-ROM workflow unless opted in.
        manifest=json.loads((ROOT / 'site/cartridges.json').read_text())
        self.demo_cart=next(c for c in manifest['cartridges'] if c['id']==manifest['defaultCartridge'])
        self.colour_cart=next(c for c in manifest['cartridges'] if c['id']=='colour-test')
        page.route("**/"+self.demo_cart['path'], lambda route: route.fulfill(
            status=200 if demo_rom else 404,
            content_type="application/octet-stream",
            body=(ROOT / 'site' / self.demo_cart['path']).read_bytes() if demo_rom else b"Missing test demo"))
        if stalled_demo:
            page.add_init_script('window.__testDemoUrl='+json.dumps('./'+self.demo_cart['path'])+';')
            page.add_init_script("""(() => {
                const originalFetch=window.fetch;
                window.fetch=(url,opts)=>{
                    if(String(url)===window.__testDemoUrl)
                        return new Promise(resolve=>{
                            window.__resumeDemoFetch=()=>originalFetch(url,opts).then(resolve);
                        });
                    return originalFetch(url,opts);
                };
            })();""")
        if stalled_build_info:
            # This fetch deliberately ignores abort, proving the export race is bounded.
            page.add_init_script("""(() => {
                const nativeFetch=window.fetch;
                const nativeTimeout=window.setTimeout;
                window.setTimeout=(callback,delay,...args)=>{
                    if(delay===1500) {
                        window.__finishBuildInfoTimeout=callback;
                        return nativeTimeout(()=>{},60000);
                    }
                    return nativeTimeout(callback,delay,...args);
                };
                window.__buildInfoRequests=0;
                window.fetch=(url,options)=>{
                    if(String(url)==='./build-info.json') {
                        window.__buildInfoRequests++;
                        window.__buildInfoOptions={credentials:options.credentials,cache:options.cache};
                        options.signal.addEventListener('abort',()=>{window.__buildInfoAborted=true;});
                        return new Promise(()=>{});
                    }
                    return nativeFetch(url,options);
                };
            })();""")
        else:
            page.route('**/build-info.json', lambda route: route.fulfill(
                status=404 if build_info is None else 200,
                content_type='application/json',
                body='Not found' if build_info is None else
                    json.dumps(build_info) if isinstance(build_info, (dict,list)) else build_info))
        page.goto(f"http://127.0.0.1:{self.server.server_port}/")
        expect(page.locator("#powerLabel")).to_have_text(
            "CONSOLE ON" if demo_rom and not stalled_demo else "WAITING FOR ROM")
        if legacy_core:
            expect(page.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        elif not demo_rom or stalled_demo:
            expect(page.locator("#logicStatus")).to_contain_text("Load a ROM")
        details = page.locator("#logicExperiment")
        if not details.evaluate("node => node.open"):
            details.locator(":scope > summary").click()
        # Most regressions explicitly select unassisted operation; recovery tests cover the defaults.
        if not automatic_recovery:
            page.locator('#logicResumeBtn').click()
            page.locator('#armCpuRecoveryBtn').click()
        return page

    @staticmethod
    def synthetic_rom():
        data = bytearray(512)
        data[0x100:0x104] = b"SEGA"
        return bytes(data)

    def test_demo_auto_loads_and_custom_cartridge_wins(self):
        page=self.new_page(demo_rom=True)
        expect(page.locator("#romName")).to_have_text("VRAMPAGE MD DEMO CART")
        self.assertEqual(page.evaluate("window.mockCore.starts"),1)
        page.locator("#romFile").set_input_files({
            "name":"my-cartridge.bin","mimeType":"application/octet-stream","buffer":self.synthetic_rom()})
        expect(page.locator("#romName")).to_have_text("MY-CARTRIDGE.BIN")
        self.assertEqual(page.evaluate("window.mockCore.starts"),2)
        page.reload()
        expect(page.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        self.assertEqual(page.evaluate("window.mockCore.starts"),0)

    def test_pending_demo_fetch_cannot_replace_user_cartridge(self):
        page=self.new_page(demo_rom=True,stalled_demo=True)
        page.wait_for_function("typeof window.__resumeDemoFetch==='function'")
        page.locator("#romFile").set_input_files({
            "name":"preferred.bin","mimeType":"application/octet-stream","buffer":self.synthetic_rom()})
        expect(page.locator("#romName")).to_have_text("PREFERRED.BIN")
        page.evaluate("window.__resumeDemoFetch()")
        page.wait_for_timeout(100)
        expect(page.locator("#romName")).to_have_text("PREFERRED.BIN")
        self.assertEqual(page.evaluate("window.mockCore.starts"),1)

    def test_cartridge_selector_switches_builtins_and_keeps_session_choice(self):
        page=self.new_page(demo_rom=True)
        options=page.locator('#cartridgeChooser button').all_text_contents()
        self.assertIn(self.demo_cart['displayName']+' v'+self.demo_cart['version'],options)
        self.assertIn(self.colour_cart['displayName']+' v'+self.colour_cart['version'],options)
        self.assertIn('Load Your Own ROM…',options)
        choose_cartridge(page,'colour-test')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        self.assertEqual(page.evaluate('mockCore.starts'),2)
        page.reload()
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        choose_cartridge(page,'demo')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD DEMO CART')
        self.assertEqual(page.evaluate('mockCore.starts'),2)

    def test_cartridge_picker_cancels_pending_demo_even_when_dismissed(self):
        page=self.new_page(demo_rom=True,stalled_demo=True)
        page.wait_for_function("typeof window.__resumeDemoFetch==='function'")
        with page.expect_file_chooser() as chooser:
            choose_cartridge(page,'local')
        chooser.value.set_files([])
        page.evaluate('window.__resumeDemoFetch()')
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('mockCore.starts'),0)
        expect(page.locator('#powerLabel')).to_have_text('WAITING FOR ROM')
        with page.expect_file_chooser() as chooser:
            choose_cartridge(page,'local')
        chooser.value.set_files({'name':'private-local.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#romName')).to_have_text('PRIVATE-LOCAL.BIN')

    def test_cartridge_picker_direct_click_enter_space_cancel_and_reopen(self):
        page=self.page
        summary=page.locator('#cartridgeChooser > summary')
        local=page.locator('#cartridgeChooser button[data-cartridge="local"]')
        page.evaluate("""() => {
          window.cartridgeActivations=[];
          document.querySelector('[data-cartridge="local"]').addEventListener('click',event=>
            cartridgeActivations.push({trusted:event.isTrusted,active:navigator.userActivation.isActive}));
        }""")
        for action in ['click','Enter','Space']:
            with self.subTest(action=action):
                if action=='click':
                    summary.click()
                else:
                    summary.focus()
                    page.keyboard.press(action)
                    for _ in range(3): page.keyboard.press('Tab')
                    expect(local).to_be_focused()
                with page.expect_file_chooser() as chooser:
                    if action=='click': local.click()
                    else: page.keyboard.press(action)
                chooser.value.set_files([])
                self.assertFalse(page.locator('#cartridgeChooser').evaluate('node=>node.open'))
                expect(summary).to_be_focused()
        self.assertEqual(page.evaluate('cartridgeActivations'),[{'trusted':True,'active':True}]*3)
        self.assertEqual(page.evaluate('mockCore.starts'),0)
        with page.expect_file_chooser() as chooser:
            choose_cartridge(page,'local')
        chooser.value.set_files({'name':'after-cancel.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#romName')).to_have_text('AFTER-CANCEL.BIN')

    def test_cartridge_chooser_escape_outside_and_keyboard_do_not_control_emulator(self):
        page=self.page
        self.load_rom(page)
        summary=page.locator('#cartridgeChooser > summary')
        summary.click()
        state="""() => JSON.stringify({pause:document.querySelector('#pauseBtn').textContent,
          starts:mockCore.starts,logic:mockCore.logic.setterCalls,vram:mockCore.vramModel.calls,
          masks:mockCore.vramMaskCalls,psg:mockCore.psg.calls,fm:mockCore.fm.calls})"""
        before=page.evaluate(state)
        for control in [summary,page.locator('#cartridgeChooser button[data-cartridge="local"]')]:
            control.focus()
            for key in ['ArrowRight','ArrowDown','KeyZ','KeyX','KeyC','Digit1','Digit0','KeyP']:
                with self.subTest(control=control,key=key):
                    ticks=page.evaluate('mockCore.ticks')
                    page.keyboard.down(key)
                    page.wait_for_function('before=>mockCore.ticks>before',arg=ticks)
                    self.assertFalse(page.evaluate('mockCore.inputs.some(Boolean)'))
                    self.assertEqual(page.evaluate(state),before)
                    page.keyboard.up(key)
        page.keyboard.press('Escape')
        self.assertFalse(page.locator('#cartridgeChooser').evaluate('node=>node.open'))
        expect(summary).to_be_focused()
        page.keyboard.press('Enter')
        self.assertTrue(page.locator('#cartridgeChooser').evaluate('node=>node.open'))
        outside=page.locator('#rawVideoToggle')
        outside.focus()
        outside.click()
        self.assertFalse(page.locator('#cartridgeChooser').evaluate('node=>node.open'))
        expect(outside).to_be_focused()

    def test_cartridge_chooser_fits_short_and_mobile_windows_without_resizing_toolbar(self):
        page=self.page
        for width,height in [(1366,768),(390,844),(360,640),(844,390)]:
            with self.subTest(viewport=(width,height)):
                page.set_viewport_size({'width':width,'height':height})
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                toolbar=page.locator('.toolbar').bounding_box()
                page.locator('#cartridgeChooser > summary').click()
                choices=page.locator('.cartridge-choices').bounding_box()
                self.assertEqual(page.locator('.toolbar').bounding_box(),toolbar)
                self.assertGreaterEqual(choices['x'],0)
                self.assertGreaterEqual(choices['y'],0)
                self.assertLessEqual(choices['x']+choices['width'],width)
                self.assertLessEqual(choices['y']+choices['height'],height)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                page.keyboard.press('Escape')

    def test_cartridge_latest_builtin_wins_over_pending_demo(self):
        page=self.new_page(demo_rom=True,stalled_demo=True)
        page.wait_for_function("typeof window.__resumeDemoFetch==='function'")
        choose_cartridge(page,'colour-test')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        page.evaluate('window.__resumeDemoFetch()')
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')

    def test_cartridge_builtin_selection_cancels_pending_local_read(self):
        page=self.page
        page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          File.prototype.arrayBuffer=function(){return new Promise(resolve=>window.finishLocalRead=()=>native.call(this).then(resolve));};
        }""")
        page.locator('#romFile').set_input_files({'name':'slow-local.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        page.wait_for_function("typeof window.finishLocalRead==='function'")
        choose_cartridge(page,'colour-test')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        page.evaluate('window.finishLocalRead()')
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')

    def test_cartridge_hash_failure_retains_faults_checkpoint_and_restart(self):
        page=self.checkpoint_page()
        self.load_rom(page)
        page.locator('#pauseBtn').click()
        page.locator('#saveCheckpointBtn').click()
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#randomPsgBtn').click()
        before=page.evaluate('({starts:mockCore.starts,psg:JSON.stringify(mockCore.psg)})')
        approved=(ROOT/'site'/self.colour_cart['path']).read_bytes()
        altered=bytearray(approved);altered[-1]^=1
        page.route('**/'+self.colour_cart['path'],lambda route:route.fulfill(body=bytes(altered)))
        choose_cartridge(page,'colour-test')
        expect(page.locator('#experimentLog')).to_contain_text('SHA-256 does not match')
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')
        self.assertEqual(page.evaluate('({starts:mockCore.starts,psg:JSON.stringify(mockCore.psg)})'),before)
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#compactResetBtn').click()
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')
        page.unroute('**/'+self.colour_cart['path'])
        choose_cartridge(page,'colour-test')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        expect(page.locator('#restoreCheckpointBtn')).to_be_disabled()

    def test_cartridge_manifest_failure_keeps_local_loading_available(self):
        page=self.page
        manifest=json.loads((ROOT/'site/cartridges.json').read_text())
        manifest['cartridges'][0]['approved']=False
        page.route('**/cartridges.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(manifest)))
        page.reload()
        expect(page.locator('#placeholderTitle')).to_have_text('BUILT-IN CARTRIDGE UNAVAILABLE')
        self.assertEqual(page.locator('#cartridgeChooser button').count(),1)
        self.load_rom(page)
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')

    def test_cartridge_user_selection_precedes_delayed_manifest_and_core(self):
        page=self.page
        page.add_init_script("""(() => {
          const nativeFetch=window.fetch;
          window.fetch=(url,opts)=>String(url)==='./cartridges.json'
            ? new Promise(resolve=>window.finishManifest=()=>nativeFetch(url,opts).then(resolve))
            : nativeFetch(url,opts);
        })();""")
        page.route('**/core/genplus.js',lambda route:route.fulfill(content_type='application/javascript',body=
            (ROOT/'tests/fixtures/mock-core.js').read_text()+
            '\nconst realFactory=window.Module;window.Module=opts=>new Promise(resolve=>window.finishCore=()=>realFactory(opts).then(resolve));'))
        page.reload()
        page.wait_for_function("typeof window.finishCore==='function' && typeof window.finishManifest==='function'")
        page.locator('#romFile').set_input_files({'name':'early-local.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        page.evaluate('window.finishCore()')
        expect(page.locator('#romName')).to_have_text('EARLY-LOCAL.BIN')
        page.evaluate('window.finishManifest()')
        page.wait_for_function("document.querySelector('#cartridgeChooser button[data-cartridge=demo]')")
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        expect(page.locator('#romName')).to_have_text('EARLY-LOCAL.BIN')

    def test_cartridge_stale_verification_cannot_replace_new_local_rom(self):
        page=self.page
        page.evaluate("""() => {
          const native=VRAMpageCartridges.verify;
          VRAMpageCartridges.verify=(bytes,cart)=>new Promise(resolve=>window.finishVerification=()=>native(bytes,cart).then(resolve));
        }""")
        choose_cartridge(page,'colour-test')
        page.wait_for_function("typeof window.finishVerification==='function'")
        self.load_rom(page)
        page.evaluate('window.finishVerification()')
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')

    def test_cartridge_static_http_without_webcrypto_still_verifies(self):
        page=self.page
        page.evaluate("Object.defineProperty(window.crypto,'subtle',{value:undefined})")
        choose_cartridge(page,'colour-test')
        expect(page.locator('#romName')).to_have_text('VRAMPAGE MD COLOUR TEST')
        self.assertEqual(page.evaluate('mockCore.starts'),1)

    def test_cartridge_builtin_native_failure_uses_existing_clean_restart_recovery(self):
        page=self.new_page(circuit_config=True)
        self.load_rom(page)
        page.evaluate('mockCore.rejectVramModel=true')
        choose_cartridge(page,'colour-test')
        expect(page.locator('#placeholderTitle')).to_have_text('CARTRIDGE ACTIVATION UNCERTAIN')
        expect(page.locator('#powerLabel')).to_have_text('WAITING FOR ROM')
        page.evaluate('mockCore.rejectVramModel=false')
        page.locator('#compactResetBtn').click()
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        self.assertEqual(page.evaluate('mockCore.starts'),3)

    def test_cartridge_size_and_unknown_choice_rejected_before_core_mutation(self):
        self.load_rom()
        page=self.page
        page.route('**/'+self.colour_cart['path'],lambda route:route.fulfill(body=b'too short'))
        choose_cartridge(page,'colour-test')
        expect(page.locator('#experimentLog')).to_contain_text('size does not match')
        page.evaluate("const button=document.createElement('button');button.type='button';button.dataset.cartridge='unapproved';button.textContent='Unapproved';document.querySelector('.cartridge-choices').append(button)")
        choose_cartridge(page,'unapproved')
        expect(page.locator('#experimentLog')).to_contain_text('not approved')
        self.assertEqual(page.evaluate('mockCore.starts'),1)
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')

    def test_cartridge_clean_restart_cancels_pending_builtin_verification(self):
        self.load_rom()
        page=self.page
        page.evaluate("""() => {
          const native=VRAMpageCartridges.verify;
          VRAMpageCartridges.verify=(bytes,cart)=>new Promise(resolve=>window.finishVerification=()=>native(bytes,cart).then(resolve));
        }""")
        choose_cartridge(page,'colour-test')
        page.wait_for_function("typeof window.finishVerification==='function'")
        page.locator('#resetBtn').click()
        page.wait_for_function('mockCore.starts===2')
        page.evaluate('window.finishVerification()')
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate('mockCore.starts'),2)
        expect(page.locator('#romName')).to_have_text('SYNTHETIC-TEST.BIN')

    def load_rom(self, page=None):
        page = page or self.page
        data = self.synthetic_rom()
        page.locator("#romFile").set_input_files({
            "name": "synthetic-test.bin",
            "mimeType": "application/octet-stream",
            "buffer": data,
        })
        expect(page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        page.wait_for_function("window.mockCore.ticks > 0")
        return data

    def checkpoint_page(self):
        page=self.new_page(session_checkpoint=True, manual_frames=True, circuit_config=True)
        page.locator("#romFile").set_input_files({"name":"synthetic.bin", "mimeType":"application/octet-stream", "buffer":self.synthetic_rom()})
        expect(page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        page.evaluate("stepTestFrame();stepTestFrame()")
        # The checkpoint controls live in the advanced panel.
        page.locator("#saveCheckpointBtn").evaluate("el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}")
        return page

    def test_region_selection_is_staged_and_applies_on_restart(self):
        page=self.new_page(region_core=True,manual_frames=True,session_checkpoint=True,circuit_config=True)
        expect(page.locator('#regionSelect')).to_be_enabled()
        page.locator('#romFile').set_input_files({'name':'region.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-U')
        page.locator('#saveCheckpointBtn').evaluate("el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}")
        page.locator('#saveCheckpointBtn').click()
        starts=page.evaluate('mockCore.starts');ticks=page.evaluate('mockCore.ticks')
        page.locator('#regionSelect').select_option('2')
        expect(page.locator('#regionStatus')).to_contain_text('Pending')
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-U')
        self.assertEqual(page.evaluate('mockCore.starts'),starts)
        self.assertEqual(page.evaluate('mockCore.ticks'),ticks)
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#logicCpuResetBtn').click()
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-U')
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#resetBtn').click()
        expect(page.locator('#machineSummary')).to_contain_text('PAL (Europe)')
        expect(page.locator('#regionStatus')).to_contain_text('Active')
        expect(page.locator('#restoreCheckpointBtn')).to_be_disabled()
        self.assertEqual(page.evaluate("[document.getElementById('screen').width,document.getElementById('screen').height]"),[320,240])
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        self.assertEqual(page.evaluate('mockCore.region.linesPerFrame'),313)

    def test_region_unavailable_legacy_and_rejected_change(self):
        expect(self.page.locator('#regionSelect')).to_be_disabled()
        expect(self.page.locator('#regionStatus')).to_contain_text('Unavailable')
        page=self.new_page(region_core=True)
        page.evaluate('mockCore.rejectRegion=true')
        page.locator('#regionSelect').select_option('2')
        expect(page.locator('#regionSelect')).to_have_value('1')
        expect(page.locator('#regionStatus')).to_contain_text('refused')
        self.assertEqual(page.evaluate('mockCore.region.requestedRegion'),1)
        page.evaluate('mockCore.rejectRegion=false')
        page.locator('#regionSelect').select_option('3')
        self.load_rom(page)
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-J')

    def test_region_native_cadence_and_viewport(self):
        for region,fps in [('1',59.92274),('2',49.701459)]:
            page=self.new_page(region_core=True,manual_frames=True)
            page.locator('#regionSelect').select_option(region)
            page.locator('#romFile').set_input_files({'name':'timing.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
            expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
            page.evaluate('testTime=performance.now();for(let i=0;i<61;i++)stepTestFrame()')
            self.assertEqual(page.evaluate('mockCore.ticks'),int(60*17*fps/1000))
            expect(page.locator('#fpsIndicator')).to_contain_text(f'{fps:.2f} TARGET')
        for width,height in [(256,224),(320,240),(320,480)]:
            page.evaluate('([w,h])=>{mockCore.region.width=w;mockCore.region.height=h;mockCore.region.interlaced=h>240;stepTestFrame();stepTestFrame();}',[width,height])
            for viewport in [{'width':1366,'height':768},{'width':390,'height':844}]:
                page.set_viewport_size(viewport)
                page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
                shape=page.locator('#screen').evaluate('(el)=>{const r=el.getBoundingClientRect();return [el.width,el.height,r.width/r.height,document.documentElement.scrollWidth>innerWidth];}')
                self.assertEqual(shape[:2],[width,height])
                self.assertAlmostEqual(shape[2],width/height,delta=0.003)
                self.assertFalse(shape[3])

    def test_region_auto_and_missing_observation(self):
        page=self.new_page(region_core=True)
        page.locator('#regionSelect').select_option('0')
        self.load_rom(page)
        expect(page.locator('#machineSummary')).to_contain_text('PAL (Europe)')
        expect(page.locator('#regionSelect')).to_have_value('0')
        page.evaluate('mockCore.throwRegionState=true')
        expect(page.locator('#regionStatus')).to_contain_text('Unavailable')
        expect(page.locator('#regionSelect')).to_be_disabled()

    def test_region_export_observations_and_rejected_rom(self):
        page=self.new_page(region_core=True,manual_frames=True)
        page.locator('#romFile').set_input_files({'name':'accepted.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        page.locator('#regionSelect').select_option('2')
        before=page.evaluate('[mockCore.starts,mockCore.ticks]')
        page.locator('#romFile').set_input_files({'name':'invalid.bin','mimeType':'application/octet-stream','buffer':bytes(512)})
        self.assertEqual(page.evaluate('[mockCore.starts,mockCore.ticks]'),before)
        expect(page.locator('#romName')).to_have_text('ACCEPTED.BIN')
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-U')
        expect(page.locator('#regionStatus')).to_contain_text('Pending')
        machine=self.export_payload_for(page)['machine']
        self.assertTrue(machine['available'])
        self.assertEqual((machine['requestedRegion'],machine['activeRequestedRegion'],machine['regionCode']),(2,1,128))
        page.evaluate('mockCore.throwRegionState=true')
        machine=self.export_payload_for(page)['machine']
        self.assertFalse(machine['available'])
        self.assertIsNone(machine['frameRate'])
        self.assertIsNone(machine['regionCode'])
        self.assertEqual(machine['reason'],'state-unavailable')

    def test_region_restart_releases_held_controls(self):
        page=self.new_page(region_core=True,manual_frames=True)
        page.locator('#romFile').set_input_files({'name':'input.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        page.keyboard.down('ArrowRight')
        page.locator('#regionSelect').select_option('2')
        page.locator('#resetBtn').click()
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        self.assertEqual(page.evaluate('mockCore.inputs[6]'),0)
        page.keyboard.up('ArrowRight')

    def test_fm_output_model_unavailable_legacy_core_still_starts(self):
        expect(self.page.locator('#fmOutputModelSelect')).to_be_disabled()
        expect(self.page.locator('#fmOutputModelStatus')).to_contain_text('Unavailable')
        self.load_rom(self.page)
        model=self.export_payload_for(self.page)['machine']['fmOutputModel']
        self.assertEqual(model,{'schemaVersion':1,'available':False,'supported':False,'loaded':False,
            'requestedModel':None,'effectiveModel':None,'backend':None,'reason':'api-unavailable'})

    def test_fm_output_model_is_staged_through_cpu_reset_restore_and_restart(self):
        page=self.new_page(fm_output_model_core=True,manual_frames=True,session_checkpoint=True,circuit_config=True)
        expect(page.locator('#fmOutputModelSelect')).to_be_enabled()
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Discrete')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Applied on ROM Load')
        page.locator('#fmOutputModelSelect').select_option('1')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated')
        page.locator('#romFile').set_input_files({'name':'fm-model.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        page.evaluate('stepTestFrame();stepTestFrame()')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated Active')
        page.evaluate('stepTestFrame();stepTestFrame()')
        page.locator('#saveCheckpointBtn').evaluate("el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}")
        page.locator('#saveCheckpointBtn').click()
        page.keyboard.down('ArrowRight')
        starts=page.evaluate('mockCore.starts')
        ticks=page.evaluate('mockCore.ticks')
        page.locator('#fmOutputModelSelect').select_option('0')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Discrete Pending')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated Active')
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.effectiveModel'),'integrated')
        self.assertEqual(page.evaluate('mockCore.starts'),starts)
        self.assertEqual(page.evaluate('mockCore.ticks'),ticks)
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#logicCpuResetBtn').click()
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.effectiveModel'),'integrated')
        expect(page.locator('#restoreCheckpointBtn')).to_be_enabled()
        page.locator('#restoreCheckpointBtn').click()
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.effectiveModel'),'integrated')
        machine=self.export_payload_for(page)['machine']
        self.assertFalse(machine['available'], 'FM identity remains independently observed when Region API is absent')
        self.assertEqual(machine['fmOutputModel'],{'schemaVersion':1,'available':True,'supported':True,'loaded':True,
            'requestedModel':'discrete','effectiveModel':'integrated','backend':'mame-opn2','reason':'none'})
        page.locator('#resetBtn').click()
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Discrete Active')
        expect(page.locator('#restoreCheckpointBtn')).to_be_disabled()
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        self.assertEqual(page.evaluate('mockCore.inputs[6]'),0,
            'Clean Restart releases a held input while applying the pending model')
        page.keyboard.up('ArrowRight')
        page.keyboard.down('ArrowRight')
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        self.assertEqual(page.evaluate('mockCore.inputs[6]'),1)
        page.keyboard.up('ArrowRight')

    def test_fm_output_model_rejection_unknown_state_and_unsupported_backend(self):
        page=self.new_page(fm_output_model_core=True)
        page.evaluate('mockCore.rejectFmOutputModel=true')
        page.locator('#fmOutputModelSelect').select_option('1')
        expect(page.locator('#fmOutputModelSelect')).to_have_value('0')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('refused')
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.requestedModel'),'discrete')
        page.evaluate('mockCore.rejectFmOutputModel=false;mockCore.throwFmOutputModelState=true')
        page.locator('#fmOutputModelSelect').select_option('1')
        expect(page.locator('#fmOutputModelSelect')).to_be_disabled()
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('State Unavailable')

        unsupported=self.new_page(fm_output_model_core=True,unsupported_fm_output_model=True)
        unsupported.locator('#romFile').set_input_files({'name':'nuked.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(unsupported.locator('#powerLabel')).to_have_text('CONSOLE ON')
        expect(unsupported.locator('#fmOutputModelSelect')).to_be_disabled()
        expect(unsupported.locator('#fmOutputModelStatus')).to_contain_text('Unsupported')
        model=self.export_payload_for(unsupported)['machine']['fmOutputModel']
        self.assertTrue(model['available'])
        self.assertFalse(model['supported'])
        self.assertTrue(model['loaded'])
        self.assertIsNone(model['effectiveModel'])
        self.assertEqual(model['backend'],'nuked-opn2')

    def test_fm_output_model_stays_within_mobile_machine_controls(self):
        page=self.new_page(fm_output_model_core=True,manual_frames=True)
        page.locator('#fmOutputModelSelect').select_option('1')
        page.locator('#romFile').set_input_files({'name':'fm-layout.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        page.evaluate('stepTestFrame();stepTestFrame()')
        page.locator('#fmOutputModelSelect').select_option('0')
        for viewport in [{'width':1366,'height':768},{'width':390,'height':844},{'width':844,'height':390}]:
            page.set_viewport_size(viewport)
            if viewport['height']<=420:
                page.evaluate('stepTestFrame()')
                expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated Active')
                expect(page.locator('#fmOutputModelStatus')).to_contain_text('Discrete Pending')
                expect(page.locator('#fmOutputModelStatus')).not_to_contain_text('Use Clean Restart')
            shape=page.locator('.machine-options').evaluate("el=>({scroll:document.documentElement.scrollWidth,client:innerWidth,height:el.getBoundingClientRect().height})")
            self.assertLessEqual(shape['scroll'],shape['client'])
            for select_id,status_id in [('regionSelect','regionStatus'),('fmOutputModelSelect','fmOutputModelStatus')]:
                grouped=page.evaluate("""([selectId,statusId])=>{
                  const select=document.getElementById(selectId),status=document.getElementById(statusId),label=document.querySelector(`label[for="${selectId}"]`);
                  const group=select.parentElement,lr=label.getBoundingClientRect(),sr=select.getBoundingClientRect(),tr=status.getBoundingClientRect();
                return {sameGroup:status.parentElement===group&&label.parentElement===group&&select.parentElement===group,
                    statusBelow:tr.top>=Math.max(lr.bottom,sr.bottom)};
                }""",[select_id,status_id])
                self.assertTrue(grouped['sameGroup'] and grouped['statusBelow'])
            if viewport['height']<=420:
                aligned=page.locator('.machine-option-group').evaluate_all("els=>Math.abs(els[0].getBoundingClientRect().top-els[1].getBoundingClientRect().top)<3")
                self.assertTrue(aligned,'Short landscape keeps both model fields on one row')

    def test_region_and_integrated_model_apply_together_on_clean_restart(self):
        page=self.new_page(region_core=True,fm_output_model_core=True,manual_frames=True)
        page.locator('#romFile').set_input_files({'name':'region-fm.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        expect(page.locator('#machineSummary')).to_contain_text('NTSC-U')
        page.locator('#regionSelect').select_option('2')
        page.locator('#fmOutputModelSelect').select_option('1')
        expect(page.locator('#regionStatus')).to_contain_text('Pending')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated Pending')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Discrete Active')
        self.assertEqual(page.evaluate('mockCore.region.regionCode'),128)
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.effectiveModel'),'discrete')
        page.locator('#resetBtn').click()
        expect(page.locator('#machineSummary')).to_contain_text('PAL (Europe)')
        expect(page.locator('#regionStatus')).to_contain_text('Active')
        expect(page.locator('#fmOutputModelStatus')).to_contain_text('Integrated Active')
        self.assertEqual(page.evaluate('mockCore.region.regionCode'),192)
        self.assertEqual(page.evaluate('mockCore.fmOutputModel.effectiveModel'),'integrated')
        page.keyboard.down('ArrowRight')
        page.evaluate('stepTestFrame();stepTestFrame();stepTestFrame()')
        self.assertEqual(page.evaluate('mockCore.inputs[6]'),1)
        page.keyboard.up('ArrowRight')

    def test_checkpoint_save_restore_no_ticks_and_immediate_saved_image(self):
        page=self.checkpoint_page()
        page.evaluate("""() => {
            window.setCheckpointTestImage=value=>{
                const pixels=mockCore.core.HEAPU8.subarray(0,640*480*4);
                pixels.fill(value);
                for(let i=3;i<pixels.length;i+=4)pixels[i]=255;
            };
            setCheckpointTestImage(80);
        }""")
        ticks=page.evaluate("mockCore.ticks")
        page.locator("#saveCheckpointBtn").click()
        expect(page.locator("#checkpointStatus")).to_contain_text("Saved Frame")
        expect(page.locator("#pauseBtn")).to_have_text("Pause")
        page.evaluate("setCheckpointTestImage(170)")
        page.locator("#randomFmBtn").click()
        page.locator("#restoreCheckpointBtn").click()
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(page.evaluate("mockCore.ticks"),ticks)
        self.assertEqual(page.evaluate("mockCore.core.HEAPU8[0]"),80)
        self.assertEqual(page.evaluate("document.querySelector('#screen').getContext('2d').getImageData(0,0,1,1).data[0]"),80)
        self.assertFalse(page.evaluate("mockCore.fm.configured"))
        payload=self.export_payload_for(page)
        self.assertEqual([e["outcome"] for e in payload["checkpointEvents"]],["saved","restored"])
        self.assertEqual(payload["checkpointSegment"],1)
        self.assertNotIn('pixels',json.dumps(payload))
        page.locator("#restoreCheckpointBtn").click()
        self.assertEqual(self.export_payload_for(page)["checkpointSegment"],2)

    def test_checkpoint_failed_save_keeps_slot_and_pause_state(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.locator("#pauseBtn").click()
        page.evaluate("mockCore.checkpoint.saveStatus=4")
        page.locator("#saveCheckpointBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        page.locator("#restoreCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.restores"),1)

    def test_checkpoint_save_rejects_contacts_inputs_and_unknown_fault_state(self):
        page=self.checkpoint_page()
        page.keyboard.down("KeyZ")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),0)
        page.keyboard.up("KeyZ")
        page.evaluate("mockCore.fm.configured=true")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),0)
        page.evaluate("() => {mockCore.fm.configured=false;mockCore.core._get_vram_fault_model_state=()=>{throw Error('unavailable')};}")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),0)
        expect(page.locator("#pauseBtn")).to_have_text("Pause")

    def test_checkpoint_clear_failure_never_loads_and_stays_paused(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.evaluate("() => {mockCore.fm.configured=true;mockCore.core._set_fm_data_bridge=()=>5;}")
        page.locator("#restoreCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.restores"),0)
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        self.assertEqual(self.export_payload_for(page)["checkpointSegment"],0)

    def test_checkpoint_native_partial_failure_invalidates_uncertain_slot(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.evaluate("mockCore.checkpoint.restoreStatus=5")
        page.locator("#restoreCheckpointBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_disabled()
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        payload=self.export_payload_for(page)
        self.assertEqual(payload["checkpointSegment"],1)
        self.assertEqual(payload["checkpointEvents"][-1]["outcome"],"uncertain")

    def test_checkpoint_rejected_restore_retains_slot(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.evaluate("mockCore.checkpoint.restoreStatus=6")
        page.locator("#restoreCheckpointBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        self.assertEqual(self.export_payload_for(page)["checkpointSegment"],0)

    def test_checkpoint_lifecycle_preserves_rejected_rom_and_cpu_reset(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.locator("#logicCpuResetBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        page.evaluate("mockCore.rejectRomAllocation=true")
        page.locator("#romFile").set_input_files({"name":"rejected.bin","mimeType":"application/octet-stream","buffer":self.synthetic_rom()})
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        page.evaluate("mockCore.rejectRomAllocation=false")
        page.locator("#resetBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_disabled()
        self.assertEqual(self.export_payload_for(page)["checkpointEvents"],[])

    def test_checkpoint_restore_suppresses_held_input_until_release(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.keyboard.down("KeyZ")
        page.locator("#restoreCheckpointBtn").click()
        page.keyboard.down("KeyZ")
        page.locator("#pauseBtn").click()
        page.evaluate("stepTestFrame();stepTestFrame()")
        self.assertEqual(page.evaluate("mockCore.inputs[9]"),0)
        page.keyboard.up("KeyZ")
        page.keyboard.down("KeyZ")
        page.evaluate("stepTestFrame();stepTestFrame()")
        self.assertEqual(page.evaluate("mockCore.inputs[9]"),1)
        page.keyboard.up("KeyZ")

    def test_checkpoint_held_fault_restore_cancels_release_callback(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.keyboard.down("Shift")
        page.keyboard.down("Digit1")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),1)
        page.locator("#restoreCheckpointBtn").click()
        page.keyboard.up("Digit1")
        page.keyboard.up("Shift")
        self.assertEqual(page.evaluate("mockCore.short"),[-1,-1])
        self.assertEqual(page.evaluate("mockCore.checkpoint.restores"),1)
        expect(page.locator("#pauseBtn")).to_have_text("Resume")

    def test_checkpoint_gamepad_release_and_save_preflight(self):
        page=self.checkpoint_page()
        page.evaluate("() => {window.testPad={axes:[0,0],buttons:Array.from({length:10},()=>({pressed:false}))};navigator.getGamepads=()=>[testPad];}")
        page.locator("#saveCheckpointBtn").click()
        page.evaluate("testPad.buttons[0].pressed=true")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),1)
        page.locator("#restoreCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.inputs[9]"),0)
        page.locator("#pauseBtn").click()
        page.evaluate("stepTestFrame();stepTestFrame()")
        self.assertEqual(page.evaluate("mockCore.inputs[9]"),0)
        page.evaluate("testPad.buttons[0].pressed=false;stepTestFrame();testPad.buttons[0].pressed=true;stepTestFrame()")
        self.assertEqual(page.evaluate("mockCore.inputs[9]"),1)

    def test_checkpoint_uncertain_save_disables_slot_without_claiming_success(self):
        page=self.checkpoint_page()
        page.locator("#saveCheckpointBtn").click()
        page.evaluate("mockCore.checkpoint.throwSave=true")
        page.locator("#saveCheckpointBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_disabled()
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        payload=self.export_payload_for(page)
        self.assertEqual(payload["checkpointEvents"][-1]["outcome"],"unknown")
        self.assertEqual(payload["checkpointSegment"],0)

    def test_checkpoint_saved_frame_preserves_unsigned_wasm_frame(self):
        page=self.checkpoint_page()
        page.evaluate("() => {mockCore.core._get_session_checkpoint_saved_frame=()=>-1;}")
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(self.export_payload_for(page)["checkpointEvents"][-1]["savedFrame"],4294967295)

    def test_checkpoint_saved_frame_telemetry_failure_keeps_successful_capture(self):
        page=self.checkpoint_page()
        page.evaluate("() => {mockCore.core._get_session_checkpoint_saved_frame=()=>{throw Error('frame telemetry')};}")
        page.locator("#saveCheckpointBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        payload=self.export_payload_for(page)
        self.assertEqual(payload["checkpointEvents"][-1]["outcome"],"saved")
        self.assertIn("telemetryError",payload["checkpointEvents"][-1])

    def test_checkpoint_legacy_core_and_throwing_getters_are_optional(self):
        self.load_rom()
        expect(self.page.locator("#saveCheckpointBtn")).to_be_disabled()
        page=self.checkpoint_page()
        page.evaluate("() => {mockCore.core._get_session_checkpoint_support=()=>{throw Error('optional getter')};}")
        page.locator("#pauseBtn").click()
        expect(page.locator("#saveCheckpointBtn")).to_be_disabled()
        expect(page.locator("#restoreCheckpointBtn")).to_be_disabled()

    def test_rejected_roms_keep_the_accepted_cartridge_and_initial_errors_are_helpful(self):
        self.load_rom()
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicApplyBtn").click()
        self.page.locator("#pauseBtn").click()
        starts = self.page.evaluate("window.mockCore.starts")
        fault = self.page.evaluate("({active:window.mockCore.logic.active, config:{...window.mockCore.logic.config}})")
        for name, data in (("short.bin", b"tiny"),
                           ("bad-header.bin", bytes(512))):
            self.page.locator("#romFile").set_input_files({"name": name, "mimeType": "application/octet-stream", "buffer": data})
            expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
            expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
            expect(self.page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
            self.assertEqual(self.page.evaluate("window.mockCore.starts"), starts)
            self.assertEqual(self.page.evaluate("({active:window.mockCore.logic.active, config:{...window.mockCore.logic.config}})"), fault)
            self.assertTrue(self.page.locator("#screenPlaceholder").evaluate("node => node.hidden"))
        self.page.evaluate("window.mockCore.rejectRomAllocation=true")
        self.page.locator("#romFile").set_input_files({
            "name": "allocation-rejected.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), starts)
        self.assertEqual(self.page.evaluate("({active:window.mockCore.logic.active, config:{...window.mockCore.logic.config}})"), fault)

        self.page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          window.oversizeReadCalls=0;
          File.prototype.arrayBuffer=function(){window.oversizeReadCalls++;return native.call(this);};
        }""")
        self.page.locator("#romFile").set_input_files({
            "name": "oversize.bin", "mimeType": "application/octet-stream", "buffer": bytes(4*1024*1024+1)})
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        self.assertEqual(self.page.evaluate("window.oversizeReadCalls"), 0)
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), starts)
        self.assertEqual(self.page.evaluate("({active:window.mockCore.logic.active, config:{...window.mockCore.logic.config}})"), fault)

        self.page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          File.prototype.arrayBuffer=function(){
            return this.name==='read-rejected.bin'
              ? Promise.reject(new Error('synthetic file read rejection'))
              : native.call(this);
          };
        }""")
        self.page.locator("#romFile").set_input_files({
            "name": "read-rejected.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), starts)
        self.assertEqual(self.page.evaluate("({active:window.mockCore.logic.active, config:{...window.mockCore.logic.config}})"), fault)

        with self.page.expect_download() as download_event:
            self.page.locator("#logicExperimentBtn").click()
        export_path=download_event.value.path()
        exported=json.loads(export_path.read_text())
        self.assertEqual(exported["rom"], {
            "name": "synthetic-test.bin",
            "sha256": hashlib.sha256(self.synthetic_rom()).hexdigest(),
        })

        initial = self.new_page()
        initial.locator("#romFile").set_input_files({"name": "bad-header.bin", "mimeType": "application/octet-stream", "buffer": bytes(512)})
        expect(initial.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        expect(initial.locator("#placeholderTitle")).to_have_text("CARTRIDGE COULD NOT START")
        expect(initial.locator("#placeholderMessage")).to_contain_text('ROM header missing "SEGA"')

    def test_latest_rom_selection_wins_even_when_the_latest_file_is_invalid(self):
        self.page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          window.pendingRomReads={};
          File.prototype.arrayBuffer=function(){
            return new Promise((resolve,reject)=>window.pendingRomReads[this.name]={
              resolve:()=>native.call(this).then(resolve,reject), reject});
          };
        }""")
        self.page.locator("#romFile").set_input_files({"name": "older-valid.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        self.page.wait_for_function("window.pendingRomReads['older-valid.bin']")
        self.page.locator("#romFile").set_input_files({"name": "latest-invalid.bin", "mimeType": "application/octet-stream", "buffer": bytes(512)})
        self.page.wait_for_function("window.pendingRomReads['latest-invalid.bin']")
        self.page.evaluate("window.pendingRomReads['latest-invalid.bin'].resolve()")
        expect(self.page.locator("#placeholderTitle")).to_have_text("CARTRIDGE COULD NOT START")
        self.page.evaluate("window.pendingRomReads['older-valid.bin'].resolve()")
        expect(self.page.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), 0)

    def test_stale_file_read_error_does_not_cover_the_latest_valid_game(self):
        self.page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          window.pendingRomReads={};
          File.prototype.arrayBuffer=function(){
            return new Promise((resolve,reject)=>window.pendingRomReads[this.name]={
              resolve:()=>native.call(this).then(resolve,reject), reject});
          };
        }""")
        self.page.locator("#romFile").set_input_files({
            "name": "older-read-error.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        self.page.wait_for_function("window.pendingRomReads['older-read-error.bin']")
        self.page.locator("#romFile").set_input_files({
            "name": "latest-valid.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        self.page.wait_for_function("window.pendingRomReads['latest-valid.bin']")
        self.page.evaluate("window.pendingRomReads['latest-valid.bin'].resolve()")
        expect(self.page.locator("#romName")).to_have_text("LATEST-VALID.BIN")
        self.page.evaluate("window.pendingRomReads['older-read-error.bin'].reject(new Error('stale read failure'))")
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(self.page.locator("#romName")).to_have_text("LATEST-VALID.BIN")
        self.assertTrue(self.page.locator("#screenPlaceholder").evaluate("node => node.hidden"))
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), 1)

    def test_clean_restart_cancels_a_pending_rom_read(self):
        self.load_rom()
        self.page.evaluate("""() => {
          const native=File.prototype.arrayBuffer;
          window.pendingResetRead=null;
          File.prototype.arrayBuffer=function(){
            return new Promise((resolve,reject)=>window.pendingResetRead={
              resolve:()=>native.call(this).then(resolve,reject), reject});
          };
        }""")
        self.page.locator("#romFile").set_input_files({"name": "delayed.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        self.page.wait_for_function("window.pendingResetRead")
        self.page.locator("#resetBtn").click()
        self.page.wait_for_function("window.mockCore.starts === 2")
        self.page.evaluate("window.pendingResetRead.resolve()")
        expect(self.page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), 2)

    def test_post_start_failure_reports_uncertainty_and_retains_restart_source(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.evaluate("window.mockCore.rejectVramModel=true")
        page.locator("#romFile").set_input_files({
            "name": "post-start-failure.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(page.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        expect(page.locator("#placeholderTitle")).to_have_text("CARTRIDGE ACTIVATION UNCERTAIN")
        self.assertTrue(page.locator("#resetBtn").is_enabled())
        self.assertTrue(page.locator("#compactResetBtn").is_enabled())
        page.evaluate("window.mockCore.rejectVramModel=false")
        page.locator("#compactResetBtn").click()
        expect(page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
        self.assertEqual(page.evaluate("window.mockCore.starts"), 3)

    def test_native_start_that_mutates_then_throws_stops_unknown_core(self):
        self.load_rom()
        self.page.evaluate("""() => {
          const native=window.mockCore.core._start;
          window.__nativeTestStart=function(...args) {
            return Reflect.apply(native,this,args);
          };
          window.mockCore.core._start=function(...args) {
            Reflect.apply(window.__nativeTestStart,this,args);
            throw new Error('synthetic native start trap after mutation');
          };
        }""")
        self.page.locator("#romFile").set_input_files({
            "name": "uncertain.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(self.page.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        expect(self.page.locator("#placeholderTitle")).to_have_text("CARTRIDGE ACTIVATION UNCERTAIN")
        expect(self.page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
        self.assertTrue(self.page.locator("#logicExperimentBtn").is_disabled())
        startsAfterTrap=self.page.evaluate("window.mockCore.starts")
        self.assertEqual(startsAfterTrap, 2)
        self.page.evaluate("window.mockCore.core._start=window.__nativeTestStart")
        self.page.locator("#resetBtn").click()
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(self.page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
        self.assertGreater(self.page.evaluate("window.mockCore.starts"), startsAfterTrap)

    def test_export_cancels_if_rom_identity_changes_while_hashing(self):
        self.page.evaluate("""() => {
          const native=crypto.subtle.digest.bind(crypto.subtle);
          let delayed=false;
          window.finishPendingHash=null;
          window.digestCalls=0;
          Object.defineProperty(crypto.subtle,'digest',{configurable:true,value:(algorithm,data)=>
            (window.digestCalls++, delayed ? native(algorithm,data) : (delayed=true,new Promise(resolve=>{
              window.finishPendingHash=()=>resolve(new Uint8Array(32).buffer);
            })))});
        }""")
        self.assertTrue(self.page.evaluate("!!crypto.subtle && crypto.subtle.digest.toString().includes('delayed')"))
        self.page.locator("#romFile").set_input_files({
            "name": "first.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        self.assertEqual(self.page.evaluate("window.digestCalls"), 1)
        self.assertEqual(self.page.evaluate("typeof window.finishPendingHash"), "function")
        downloads=[]
        self.page.on("download", lambda download: downloads.append(download.suggested_filename))
        self.page.locator("#logicExperimentBtn").click()
        self.page.locator("#romFile").set_input_files({
            "name": "replacement.bin", "mimeType": "application/octet-stream", "buffer": self.synthetic_rom()})
        expect(self.page.locator("#romName")).to_have_text("REPLACEMENT.BIN")
        self.page.evaluate("window.finishPendingHash()")
        expect(self.page.locator("#logicStatus")).to_contain_text("ROM changed while preparing export")
        self.assertEqual(downloads, [])

    def test_rom_gates_logic_controls_and_legacy_core_degrades_gracefully(self):
        for control in ("#logicKind", "#logicAccess", "#logicLineA", "#logicLineB",
                        "#logicApplyBtn", "#logicDisconnectBtn", "#logicExperimentBtn"):
            self.assertTrue(self.page.locator(control).is_disabled(), control)
        expect(self.page.locator("#logicStatus")).to_have_text("Load a ROM to enable logic faults.")

        self.load_rom()
        for control in ("#logicKind", "#logicAccess", "#logicLineA", "#logicLineB",
                        "#logicApplyBtn", "#logicDisconnectBtn", "#logicExperimentBtn"):
            self.assertFalse(self.page.locator(control).is_disabled(), control)
        expect(self.page.locator("#logicStatus")).to_have_text("Load or apply a logic fault when ready.")
        expect(self.page.locator("#pauseBtn")).to_have_text("Pause")

        legacy = self.new_page(legacy_core=True)
        for control in ("#logicKind", "#logicAccess", "#logicLineA", "#logicLineB",
                        "#logicApplyBtn", "#logicDisconnectBtn"):
            self.assertTrue(legacy.locator(control).is_disabled(), control)
        expect(legacy.locator("#manualForceResumeBtn")).to_be_disabled()
        expect(legacy.locator("#logicCpuResetBtn")).to_be_disabled()
        expect(legacy.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        self.load_rom(legacy)
        expect(legacy.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(legacy.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        expect(legacy.locator("#pauseBtn")).to_have_text("Pause")

    def test_ram_data_masks_span_both_bytes_and_replace_address_faults(self):
        self.page.locator('#ramChipSignals').select_option('2')
        pins=self.page.locator('[data-chip-line]')
        self.assertEqual(pins.count(),16)
        expect(pins.nth(15)).to_be_disabled()
        self.load_rom()
        expect(self.page.locator('#ramChipSignals')).to_have_value('1')
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.locator('#logicAccess').select_option('2')
        for line in (0,8,15): pins.nth(line).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.dataMask,mockCore.logic.addressMask]'),[0x8101,0])
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMaskCalls.at(-1)'),[0x8101,2])
        pins.nth(8).focus()
        self.page.keyboard.press('Space')
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0x8001)
        expect(pins.nth(0)).to_have_attribute('aria-pressed','true')
        expect(pins.nth(15)).to_have_attribute('aria-pressed','true')
        payload=self.export_payload()
        self.assertEqual(payload['logicFault']['lines'],['D0','D15'])
        self.assertEqual(payload['logic']['dataMask'],0x8001)
        self.assertTrue(payload['logic']['dataMaskAvailable'])
        self.assertEqual(payload['logic']['referenceProfile'],'model1-pal-va65-two-byte-v1')
        calls=self.page.evaluate('mockCore.logic.setterCalls.length')
        self.page.locator('#ramChipSignals').select_option('1')
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),calls)
        pins.nth(4).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.dataMask,mockCore.logic.addressMask]'),[0,16])
        self.page.locator('#ramChipSignals').select_option('2')
        pins.nth(9).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.dataMask,mockCore.logic.addressMask]'),[512,0])
        for width,height in [(1366,768),(390,844),(844,390)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
        self.page.locator('#chipRestoreBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)

    def test_ram_data_bridge_rejects_cross_byte_pair_and_replaces_mask(self):
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('2')
        pins=self.page.locator('[data-chip-line]')
        pins.nth(15).click()
        self.page.locator('#ramLegAction').select_option('bridge')
        calls=self.page.evaluate('mockCore.logic.setterCalls.length')
        pins.nth(7).click();pins.nth(8).click()
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),calls)
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0x8000)
        expect(self.page.locator('#logicStatus')).to_contain_text('Data pairs must stay within')
        pins.nth(1).click();pins.nth(7).click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.at(-1)'),[2,1,1,7])

    def test_ram_data_mask_configuration_roundtrip_and_legacy_preflight(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.locator('#logicAccess').select_option('3')
        for line in (1,14): self.page.locator('[data-chip-line]').nth(line).click()
        with self.page.expect_download() as info:
            self.page.locator('#circuitConfigDownload').click()
        saved=json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved['schemaVersion'],6)
        self.assertEqual(saved['configuration']['ram'],{'type':'data-mask','mask':0x4002,'access':3})
        self.page.locator('#disconnectAllFaultsBtn').click()
        self.stage_circuit_file(saved)
        self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0x4002)
        expect(self.page.locator('#ramChipSignals')).to_have_value('2')
        legacy=self.new_page(circuit_config=True,legacy_ram_data=True)
        self.load_rom(legacy)
        self.stage_circuit_file(saved,legacy)
        before=legacy.evaluate('[mockCore.logic.setterCalls.length,mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]')
        legacy.locator('#circuitConfigApply').click()
        self.assertEqual(legacy.evaluate('[mockCore.logic.setterCalls.length,mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]'),before)
        expect(legacy.locator('#circuitConfigStatus')).to_contain_text('cannot apply or verify')
        legacy.locator('#ramChipSignals').select_option('2')
        expect(legacy.locator('[data-chip-line]').nth(0)).to_be_disabled()
        legacy.locator('#ramLegAction').select_option('bridge')
        legacy.locator('[data-chip-line]').nth(8).click()
        legacy.locator('[data-chip-line]').nth(15).click()
        self.assertEqual(legacy.evaluate('mockCore.logic.setterCalls.at(-1)'),[2,1,8,15])
        self.assertIsNone(self.export_payload_for(legacy)['logic']['dataMask'])

    def test_ram_data_mask_rejection_restores_previous_vram(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#pinGrid .pin').nth(2).click()
        before=self.page.evaluate('mockCore.vramModel.mask')
        self.assertNotEqual(before,0)
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.evaluate('mockCore.rejectDataMask=true')
        self.page.locator('[data-chip-line]').nth(8).click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.vramModel.mask'),before)
        expect(self.page.locator('#logicStatus')).to_contain_text('previous VRAM configuration restored')

    def test_ram_data_mask_partial_failure_and_unknown_readback_pause(self):
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.evaluate('mockCore.throwDataMaskAfter=true')
        self.page.locator('[data-chip-line]').nth(9).click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),512)
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#logicStatus')).to_contain_text('outcome is unknown')
        self.page.evaluate('mockCore.throwDataMaskAfter=false')
        self.page.locator('#disconnectAllFaultsBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)
        self.page.evaluate('mockCore.throwDataMaskState=true')
        self.page.locator('[data-chip-line]').nth(0).click()
        expect(self.page.locator('#logicStatus')).to_contain_text('could not be confirmed')
        self.assertIsNone(self.export_payload()['logic']['dataMask'])
        self.page.locator('#circuitConfigDownload').click()
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('no file was created')
        self.page.locator('#disconnectAllFaultsBtn').click()
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#disconnectAllFaultsStatus')).to_contain_text('RAM: clear failed')
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)

    def test_ram_data_mask_restores_after_temporary_address_shortcut_and_cpu_reset(self):
        self.page.close();self.page=self.new_page(session_checkpoint=True,circuit_config=True)
        self.load_rom()
        self.page.locator('#saveCheckpointBtn').click()
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.locator('[data-chip-line]').nth(12).click()
        self.page.locator('#screen').click()
        self.page.keyboard.press('Digit0')
        self.page.keyboard.down('Shift');self.page.keyboard.down('Digit1')
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)
        self.page.keyboard.up('Digit1');self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),4096)
        saves=self.page.evaluate('mockCore.checkpoint.saves')
        self.page.locator('#saveCheckpointBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.checkpoint.saves'),saves)
        self.page.locator('#psgChip .pin').nth(1).click()
        self.page.locator('#psgChip .pin').nth(2).click()
        self.page.locator('#logicCpuResetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.dataMask'),0)
        self.assertTrue(self.page.evaluate('mockCore.psg.configured'))
        expect(self.page.locator('#restoreCheckpointBtn')).to_be_enabled()

    def test_write_inhibit_controls_toggle_independently_and_keep_layout_compact(self):
        self.page.locator('#ramChipSignals').select_option('3')
        pins=self.page.locator('[data-chip-line]')
        self.assertEqual(pins.count(),2)
        expect(pins.nth(0)).to_be_disabled()
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('3')
        expect(self.page.locator('#logicAccess')).to_have_value('2')
        expect(self.page.locator('#logicAccess')).to_be_disabled()
        expect(self.page.locator('#ramLegAction')).to_be_hidden()
        pins.nth(0).focus();self.page.keyboard.press('Space')
        expect(pins.nth(0)).to_have_attribute('aria-pressed','true')
        expect(pins.nth(0)).to_have_attribute('aria-label','Lower Byte Write Enable (/LWR): inhibited, held inactive/high; restore writes')
        pins.nth(1).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.writeInhibit,mockCore.logic.dataMask,mockCore.logic.addressMask]'),[3,0,0])
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibitCalls'),[1,3])
        self.assertTrue(self.page.locator('[data-keyboard-chip="WRAM"]').evaluate("e=>e.classList.contains('fault-active')"))
        payload=self.export_payload()
        self.assertEqual(payload['logic']['writeInhibitMask'],3)
        self.assertTrue(payload['logic']['writeInhibitAvailable'])
        self.assertEqual(payload['logicFault']['lines'],['/LWR','/UWR'])
        self.assertEqual(payload['logicFault']['kind'],'write-inhibit')
        for width,height in [(1366,768),(390,844),(844,390)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
        self.page.locator('#chipRestoreBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        expect(pins.nth(1)).to_have_attribute('aria-pressed','false')

    def test_write_inhibit_view_and_other_ram_modes_replace_without_extra_faults(self):
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('2')
        self.page.locator('[data-chip-line]').nth(15).click()
        calls=self.page.evaluate('mockCore.logic.setterCalls.length')
        self.page.locator('#ramChipSignals').select_option('3')
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),calls)
        self.page.locator('[data-chip-line]').nth(1).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.writeInhibit,mockCore.logic.dataMask]'),[2,0])
        self.page.locator('#ramChipSignals').select_option('1')
        expect(self.page.locator('#logicAccess')).to_be_enabled()
        self.page.locator('[data-chip-line]').nth(4).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.writeInhibit,mockCore.logic.addressMask]'),[0,16])
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.locator('[data-chip-line]').nth(0).click()
        self.page.locator('#logicKind').select_option('2')
        self.page.locator('#logicLineA').select_option('0')
        self.page.locator('#logicLineB').select_option('7')
        self.page.locator('#logicApplyBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.at(-1)'),[2,2,0,7])

    def test_write_inhibit_configuration_roundtrip_and_legacy_preflight(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.locator('[data-chip-line]').nth(1).click()
        with self.page.expect_download() as info:self.page.locator('#circuitConfigDownload').click()
        saved=json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved['schemaVersion'],6)
        self.assertEqual(saved['configuration']['ram'],{'type':'write-inhibit','mask':2})
        self.page.locator('#disconnectAllFaultsBtn').click()
        self.stage_circuit_file(saved);self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),2)
        expect(self.page.locator('#ramChipSignals')).to_have_value('3')
        calls=self.page.evaluate('mockCore.logic.writeInhibitCalls.length')
        self.stage_circuit_file(saved);self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibitCalls.length'),calls)
        legacy=self.new_page(circuit_config=True,legacy_write_inhibit=True)
        self.load_rom(legacy);self.stage_circuit_file(saved,legacy)
        before=legacy.evaluate('[mockCore.logic.setterCalls.length,mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]')
        legacy.locator('#circuitConfigApply').click()
        self.assertEqual(legacy.evaluate('[mockCore.logic.setterCalls.length,mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]'),before)
        expect(legacy.locator('#circuitConfigStatus')).to_contain_text('cannot apply or verify')
        legacy.locator('#ramChipSignals').select_option('3')
        expect(legacy.locator('[data-chip-line]').nth(0)).to_be_disabled()
        legacy.locator('#ramChipSignals').select_option('2')
        expect(legacy.locator('[data-chip-line]').nth(0)).to_be_enabled()
        self.assertFalse(self.export_payload_for(legacy)['logic']['writeInhibitAvailable'])
        self.assertIsNone(self.export_payload_for(legacy)['logic']['writeInhibitMask'])

    def test_write_inhibit_unknown_native_state_pauses_and_blocks_false_configuration(self):
        self.load_rom()
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.evaluate('mockCore.throwWriteInhibitAfter=true')
        self.page.locator('[data-chip-line]').nth(0).click()
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#logicStatus')).to_contain_text('outcome is unknown')
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),1)
        self.page.evaluate('mockCore.throwWriteInhibitAfter=false;mockCore.throwWriteInhibitState=true')
        self.assertIsNone(self.export_payload()['logic']['writeInhibitMask'])
        self.page.locator('#circuitConfigDownload').click()
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('no file was created')
        self.page.locator('#disconnectAllFaultsBtn').click()
        expect(self.page.locator('#disconnectAllFaultsStatus')).to_contain_text('RAM: clear failed')
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        self.page.evaluate('mockCore.throwWriteInhibitState=false')
        self.page.locator('#chipRestoreBtn').click()
        self.assertFalse(self.export_payload()['faultActive'])

    def test_write_inhibit_rejection_restores_vram_and_shift_shortcut_restores_inhibit(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#pinGrid .pin').nth(2).click()
        before=self.page.evaluate('mockCore.vramModel.mask')
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.evaluate('mockCore.rejectWriteInhibit=true')
        self.page.locator('[data-chip-line]').nth(0).click()
        self.assertEqual(self.page.evaluate('mockCore.vramModel.mask'),before)
        expect(self.page.locator('#logicStatus')).to_contain_text('previous VRAM configuration restored')
        self.page.evaluate('mockCore.rejectWriteInhibit=false')
        self.page.locator('[data-chip-line]').nth(1).click()
        self.assertEqual(self.page.evaluate('mockCore.vramModel.mask'),0)
        self.page.locator('#screen').click();self.page.keyboard.press('Digit0')
        self.page.keyboard.down('Shift');self.page.keyboard.down('Digit1')
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        self.page.keyboard.up('Digit1');self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),2)

    def test_write_inhibit_untracked_or_mismatched_state_cannot_be_saved_or_applied(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.evaluate('mockCore.core._set_logic_write_inhibit(3)')
        self.page.locator('#circuitConfigDownload').click()
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('no file was created')
        self.stage_circuit_file(self.circuit_configuration(psg=[0,7]))
        before=self.page.evaluate('[mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.vramModel.calls.length]')
        self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.vramModel.calls.length]'),before)
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('differs from the app state')
        self.page.locator('#disconnectAllFaultsBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        expect(self.page.locator('#disconnectAllFaultsStatus')).to_contain_text('RAM: cleared')
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.evaluate('mockCore.invalidWriteInhibitState=0')
        self.page.locator('[data-chip-line]').nth(0).click()
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#logicStatus')).to_contain_text('could not be confirmed')
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),1)

    def test_write_inhibit_checkpoint_reset_restore_and_clean_restart(self):
        self.page.close();self.page=self.checkpoint_page()
        self.page.locator('#saveCheckpointBtn').click()
        self.page.locator('#ramChipSignals').select_option('3')
        self.page.locator('[data-chip-line]').nth(0).click()
        saves=self.page.evaluate('mockCore.checkpoint.saves')
        self.page.locator('#saveCheckpointBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.checkpoint.saves'),saves)
        self.page.locator('#randomPsgBtn').click()
        self.page.locator('#logicCpuResetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        self.assertTrue(self.page.evaluate('mockCore.psg.configured'))
        expect(self.page.locator('#restoreCheckpointBtn')).to_be_enabled()
        self.page.locator('[data-chip-line]').nth(1).click()
        self.page.locator('#restoreCheckpointBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        self.assertFalse(self.page.evaluate('mockCore.psg.configured'))
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        self.page.locator('[data-chip-line]').nth(0).click()
        self.page.locator('#resetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.logic.writeInhibit'),0)
        expect(self.page.locator('#ramChipSignals')).to_have_value('1')
        expect(self.page.locator('#restoreCheckpointBtn')).to_be_disabled()

    def test_configuration_validation_and_cross_lane_rejection(self):
        self.load_rom()
        self.page.locator("#logicKind").select_option("2")
        self.assertEqual(self.page.locator("#logicLineA option").count(), 16)
        expect(self.page.locator("#logicLineA option").nth(0)).to_have_text("D0")
        expect(self.page.locator("#logicLineB option").nth(15)).to_have_text("D15")
        self.page.locator("#logicLineA").select_option("0")
        self.page.locator("#logicLineB").select_option("8")
        calls_before = self.page.evaluate("window.mockCore.logic.setterCalls.length")
        self.page.locator("#logicApplyBtn").click()
        expect(self.page.locator("#logicStatus")).to_have_text(
            "Data pairs must stay within D0–D7 or D8–D15. No fault was applied.")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.setterCalls.length"), calls_before)
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))

        self.page.locator("#logicLineB").select_option("0")
        self.page.locator("#logicApplyBtn").click()
        expect(self.page.locator("#logicStatus")).to_have_text(
            "Choose two different lines. No fault was applied.")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.setterCalls.length"), calls_before)

        self.page.locator("#logicLineB").select_option("7")
        self.page.locator("#logicAccess").select_option("3")
        self.page.locator("#logicApplyBtn").click()
        expect(self.page.locator("#logicStatus")).to_have_text("Applied data D0 ↔ D7 on read + write.")
        expect(self.page.locator("#ramChipState")).to_contain_text("Data bridge D0 ↔ D7 active")
        self.assertEqual(
            self.page.evaluate("window.mockCore.logic.setterCalls.at(-1)"), [2, 3, 0, 7])
        active = self.page.evaluate("({ ...window.mockCore.logic.config })")
        rejected = self.page.evaluate("window.mockCore._set_logic_fault(2, 3, 0, 8)")
        self.assertEqual(rejected, 6, "core setter must reject cross-lane pairs even if UI validation is bypassed")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.config"), active)

    def test_access_counts_cpu_flags_and_disconnect_persistence(self):
        self.load_rom()
        self.page.locator("#logicAccess").select_option("3")
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("window.mockCore.logic.reads > 0 && window.mockCore.logic.writes > 0")
        self.page.wait_for_function("window.mockCore.logic.frame > window.mockCore.logic.activationFrame")
        expect(self.page.locator("#logicReadCount")).not_to_have_text("0")
        expect(self.page.locator("#logicWriteCount")).not_to_have_text("0")
        expect(self.page.locator("#logicActivationFrame")).not_to_have_text("—")

        self.page.evaluate("window.mockCore.logic.cpuFlags = 3")
        expect(self.page.locator("#logicCpuStatus")).to_have_text("STOP + HALT")
        before = self.page.evaluate("({ starts: mockCore.starts, ticks: mockCore.ticks })")
        self.page.wait_for_function("last => window.mockCore.ticks > last", arg=before["ticks"])
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), before["starts"],
                         "STOP/HALT status must not trigger automatic recovery")
        self.page.locator("#logicDisconnectBtn").click()
        expect(self.page.locator("#logicStatus")).to_contain_text("Any projected writes remain")
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        stored_writes = self.page.evaluate("window.mockCore.logic.storedWrites")
        self.assertGreater(stored_writes, 0)
        ticks = self.page.evaluate("window.mockCore.ticks")
        self.page.wait_for_function("last => window.mockCore.ticks > last", arg=ticks)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.storedWrites"), stored_writes,
                         "mocked backing writes should survive disconnect")

    def test_access_mode_metrics_follow_selected_direction(self):
        self.load_rom()
        for access, wanted in (("1", "reads"), ("2", "writes"), ("3", "both")):
            self.page.locator("#logicAccess").select_option(access)
            self.page.locator("#logicApplyBtn").click()
            if wanted == "reads":
                self.page.wait_for_function("window.mockCore.logic.reads > 0")
                self.assertEqual(self.page.evaluate("window.mockCore.logic.writes"), 0)
            elif wanted == "writes":
                self.page.wait_for_function("window.mockCore.logic.writes > 0")
                self.assertEqual(self.page.evaluate("window.mockCore.logic.reads"), 0)
            else:
                self.page.wait_for_function(
                    "window.mockCore.logic.reads > 0 && window.mockCore.logic.writes > 0")
            self.page.locator("#logicDisconnectBtn").click()
            self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))

    def test_vram_and_logic_domains_are_exclusive_and_clean_restart_resets(self):
        self.load_rom()
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("window.mockCore.logic.writes > 0")
        expect(self.page.locator("#logicStatus")).to_contain_text("Applied address")

        self.page.locator("#vramMode").select_option("bridge")
        pins = self.page.locator("#pinGrid .pin")
        pins.nth(0).click()
        pins.nth(1).click()
        expect(self.page.locator("#connectionLabel")).to_have_text("AD0 ↔ AD1")
        expect(self.page.locator("#logicStatus")).to_have_text(
            "VRAM patch active; logic/Work RAM fault disconnected.")
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("window.mockCore.short"), [0, 1])

        self.page.locator("#resetBtn").click()
        self.page.wait_for_function("window.mockCore.starts === 2")
        expect(self.page.locator("#connectionLabel")).to_have_text("NONE — NORMAL ADDRESSING")
        expect(self.page.locator("#logicStatus")).to_have_text(
            "Clean Restart: VRAM/Work RAM faults cleared; counters reset.")
        self.assertEqual(self.page.evaluate("window.mockCore.short"), [-1, -1])
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("window.mockCore.logic.reads"), 0)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.writes"), 0)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.storedWrites"), 0)
        # Read one synchronous snapshot: animation frames can advance between
        # separate Playwright calls, even when the reset invariant is correct.
        counters = self.page.evaluate("""() => ({
            frame: window.mockCore.logic.frame,
            ticks: window.mockCore.ticks,
            lastStartTick: window.mockCore.lastStartTick
        })""")
        self.assertEqual(
            counters["frame"], counters["ticks"] - counters["lastStartTick"],
            "clean restart must reset the synthetic frame counter",
        )

    def apply_z80_bridge(self, page=None, a="0", b="1"):
        page = page or self.page
        page.locator("#z80RamBridgeA").select_option(a)
        page.locator("#z80RamBridgeB").select_option(b)
        page.locator("#z80RamBridgeApply").click()

    def test_z80_ram_defaults_validation_drafts_and_domain_isolation(self):
        expect(self.page.locator("#z80RamBridgeApply")).to_be_disabled()
        self.load_rom()
        self.assertFalse(self.page.evaluate("mockCore.z80Ram.configured"))
        self.apply_z80_bridge(a="12", b="12")
        self.assertEqual(self.page.evaluate("mockCore.z80Ram.calls"), [])
        self.apply_z80_bridge(a="0", b="12")
        self.assertEqual(self.page.evaluate("mockCore.z80Ram.calls"), [[1,0,12]])
        self.assertFalse(self.page.evaluate("mockCore.logic.active || mockCore.psg.configured || mockCore.fm.configured"))
        self.assertEqual(self.page.evaluate("mockCore.short"), [-1,-1])
        self.page.locator("#z80RamBridgeA").select_option("4")
        self.assertEqual(self.page.evaluate("[mockCore.z80Ram.bridgeA,mockCore.z80Ram.bridgeB]"), [0,12])
        self.page.evaluate("Object.assign(mockCore.z80Ram,{ramWrites:'9007199254740993',changedAddresses:'2',z80Writes:'1',m68kWrites:'9007199254740992'})")
        payload=self.export_payload()["z80RamFault"]
        self.assertTrue(payload["available"] and payload["configured"])
        self.assertEqual(payload["ramWrites"], '9007199254740993')
        self.assertEqual(payload["bridgeB"],12)
        expect(self.page.locator("#z80RamBridgeCounts")).to_contain_text('9007199254740993')
        self.assertNotIn('9007199254740993',self.page.locator("#z80RamBridgeStatus").inner_text(),
                         'per-frame counters must not flood the live status announcement')
        self.page.locator("#z80RamBridgeRemove").click()
        self.assertFalse(self.page.evaluate("mockCore.z80Ram.configured"))
        self.assertEqual(self.page.evaluate("mockCore.logic.recoveries"), [])

    def test_z80_ram_keeps_randomiser_appearance_and_ram_contacts_independent(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        styles="""() => ['randomPsgBtn','randomFmBtn','randomVramBtn'].map(id=>{
          const s=getComputedStyle(document.getElementById(id));
          return [s.color,s.opacity,s.backgroundColor,s.borderColor];
        })"""
        before=self.page.evaluate(styles)
        self.apply_z80_bridge(a="0",b="12")
        self.assertEqual(self.page.evaluate(styles),before)
        button=self.page.locator("[data-ram-frame-pair='10,11']")
        button.dispatch_event('pointerdown',{'pointerId':5,'button':0,'isPrimary':True})
        self.assertTrue(self.page.evaluate('mockCore.z80Ram.configured'))
        self.assertEqual(self.page.evaluate('[mockCore.z80Ram.bridgeA,mockCore.z80Ram.bridgeB]'),[0,12])
        button.dispatch_event('pointerup',{'pointerId':5,'button':0,'isPrimary':True})
        self.assertTrue(self.page.evaluate('mockCore.z80Ram.configured'))

    def test_z80_ram_config_round_trip_legacy_clear_and_noop_counters(self):
        self.load_rom()
        self.apply_z80_bridge(a="2",b="11")
        with self.page.expect_download() as download:
            self.page.locator("#circuitConfigDownload").click()
        saved=json.loads(Path(download.value.path()).read_text())
        self.assertEqual(saved["schemaVersion"],6)
        self.assertEqual(saved["configuration"]["z80Ram"],{"pair":[2,11]})
        self.stage_circuit_file(saved)
        calls=self.page.evaluate("mockCore.z80Ram.calls.length")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("already matches")
        self.assertEqual(self.page.evaluate("mockCore.z80Ram.calls.length"),calls)
        self.stage_circuit_file(self.circuit_configuration())
        self.page.locator("#circuitConfigApply").click()
        self.assertFalse(self.page.evaluate("mockCore.z80Ram.configured"))
        self.stage_circuit_file(saved)
        self.page.locator("#circuitConfigApply").click()
        self.assertEqual(self.page.evaluate("[mockCore.z80Ram.bridgeA,mockCore.z80Ram.bridgeB]"),[2,11])
        self.assertEqual(self.page.evaluate("mockCore.logic.recoveries"),[])

    def test_z80_ram_legacy_and_unsupported_profile_fail_before_mutation(self):
        page=self.new_page(legacy_z80_ram=True)
        self.load_rom(page)
        expect(page.locator("#z80RamBridgeApply")).to_be_disabled()
        config=self.circuit_configuration()
        config["schemaVersion"]=3;config["configuration"]["z80Ram"]={"pair":[0,1]}
        config["configuration"].pop("rgbEncoder",None)
        self.stage_circuit_file(config,page=page)
        page.locator("#circuitConfigApply").click()
        expect(page.locator("#circuitConfigStatus")).to_contain_text("refused before mutation")
        self.assertEqual(page.evaluate("mockCore.logic.setterCalls"),[])
        self.load_rom()
        self.page.evaluate("mockCore.z80Ram.supported=false")
        expect(self.page.locator("#z80RamBridgeApply")).to_be_disabled()
        self.stage_circuit_file(config)
        self.page.locator("#circuitConfigApply").click()
        self.assertEqual(self.page.evaluate("mockCore.z80Ram.calls"),[])

    def test_z80_ram_unverified_clear_pauses_and_blocks_cpu_recovery(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.apply_z80_bridge()
        self.page.evaluate("() => {mockCore.rejectZ80Ram=true;mockCore.fm.configured=true;mockCore.fm.bridgeA=0;mockCore.fm.bridgeB=1;}")
        self.page.locator("#disconnectAllFaultsBtn").click()
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertTrue(self.page.evaluate("mockCore.z80Ram.configured"))
        self.assertFalse(self.page.evaluate("mockCore.fm.configured"))
        expect(self.page.locator("#disconnectAllFaultsStatus")).to_contain_text("Z80 RAM: clear failed or unverified")
        self.page.locator("#logicCpuResetBtn").click()
        self.assertEqual(self.page.evaluate("mockCore.logic.recoveries"),[])
        self.page.evaluate("mockCore.rejectZ80Ram=false;mockCore.throwZ80RamState=true")
        self.page.locator("#disconnectAllFaultsBtn").click()
        self.assertFalse(self.export_payload()["z80RamFault"]["available"])
        expect(self.page.locator("#disconnectAllFaultsStatus")).to_contain_text("runtime state unknown")

    def test_rgb_encoder_controls_export_raw_bypass_and_lifecycle(self):
        page=self.new_page(circuit_config=True)
        self.load_rom(page)
        native_before=page.evaluate("""() => ({
          logic:mockCore.logic.setterCalls.length,vram:mockCore.vramModel.calls.length,
          psg:mockCore.psg.calls.length,fm:mockCore.fm.calls.length,z80:mockCore.z80Ram.calls.length,
          starts:mockCore.starts,recoveries:mockCore.logic.recoveries.length
        })""")
        recovery_before=self.export_payload_for(page)['automaticRecovery']
        page.locator('[data-rgb-cut="0"]').click()
        page.locator('[data-rgb-pair="0,1"]').click()
        self.assertEqual(page.evaluate("""() => ({
          logic:mockCore.logic.setterCalls.length,vram:mockCore.vramModel.calls.length,
          psg:mockCore.psg.calls.length,fm:mockCore.fm.calls.length,z80:mockCore.z80Ram.calls.length,
          starts:mockCore.starts,recoveries:mockCore.logic.recoveries.length
        })"""),native_before,"RGB output contacts must not call native fault setters or recovery")
        self.assertEqual(self.export_payload_for(page)['automaticRecovery'],recovery_before,
                         'direct RGB changes must preserve recovery policy and pending state')
        state=self.export_payload_for(page)['rgbEncoderFault']
        self.assertTrue(state['configured'] and state['effective'])
        self.assertEqual(state['cutMask'],1)
        self.assertEqual(state['pair'],[0,1])
        page.wait_for_function("""() => {
          const p=document.querySelector('#screen').getContext('2d').getImageData(0,0,1,1).data;
          return p[0]===32 && p[1]===32 && p[2]===192;
        }""")
        page.locator('#rawVideoToggle').check()
        expect(page.locator('#rgbEncoderStatus')).to_contain_text('Bypassed by Raw Output')
        page.wait_for_function("""() => {
          const p=document.querySelector('#screen').getContext('2d').getImageData(0,0,1,1).data;
          return p[0]===64 && p[1]===64 && p[2]===192;
        }""")
        page.locator('#rawVideoToggle').uncheck()
        page.locator('#logicCpuResetBtn').click()
        self.assertTrue(self.export_payload_for(page)['rgbEncoderFault']['configured'],
                        'CPU Reset retains output-only RGB contacts')
        page.locator('#resetBtn').click()
        self.assertFalse(self.export_payload_for(page)['rgbEncoderFault']['configured'],
                         'Clean Restart clears RGB contacts with the cartridge lifecycle')

    def test_rgb_encoder_only_circuit_apply_does_not_mutate_native_faults_or_recovery(self):
        page=self.new_page(circuit_config=True)
        self.load_rom(page)
        config=self.circuit_configuration()
        config['schemaVersion']=4
        config['configuration']['z80Ram']={'pair':None}
        config['configuration']['rgbEncoder']={'cutMask':2,'pair':[1,2]}
        self.stage_circuit_file(config,page)
        before=page.evaluate("""() => ({
          logic:mockCore.logic.setterCalls.length,vram:mockCore.vramModel.calls.length,
          psg:mockCore.psg.calls.length,fm:mockCore.fm.calls.length,z80:mockCore.z80Ram.calls.length,
          starts:mockCore.starts,recoveries:mockCore.logic.recoveries.length
        })""")
        recovery_before=self.export_payload_for(page)['automaticRecovery']
        page.locator('#circuitConfigApply').click()
        self.assertEqual(page.evaluate("""() => ({
          logic:mockCore.logic.setterCalls.length,vram:mockCore.vramModel.calls.length,
          psg:mockCore.psg.calls.length,fm:mockCore.fm.calls.length,z80:mockCore.z80Ram.calls.length,
          starts:mockCore.starts,recoveries:mockCore.logic.recoveries.length
        })"""),before,"RGB-only configuration must stay in the display path")
        self.assertEqual(self.export_payload_for(page)['automaticRecovery'],recovery_before,
                         'RGB-only configuration must preserve recovery policy and pending state')
        self.assertEqual(self.export_payload_for(page)['rgbEncoderFault']['cutMask'],2)
        with page.expect_download() as download:
            page.locator('#circuitConfigDownload').click()
        saved=json.loads(Path(download.value.path()).read_text())
        self.assertEqual(saved['schemaVersion'],6)
        self.assertEqual(saved['configuration']['rgbEncoder'],{'cutMask':2,'pair':[1,2]})
        legacy_v3=json.loads(json.dumps(saved))
        legacy_v3['schemaVersion']=3
        legacy_v3['configuration'].pop('rgbEncoder')
        self.stage_circuit_file(legacy_v3,page)
        page.locator('#circuitConfigApply').click()
        self.assertFalse(self.export_payload_for(page)['rgbEncoderFault']['configured'],
                         'v3 imports default RGB contacts to off')

    def test_rgb_encoder_blocks_checkpoint_save_and_restore_clears_it_paused(self):
        page=self.checkpoint_page()
        page.locator('[data-rgb-cut="1"]').click()
        page.locator('#saveCheckpointBtn').click()
        self.assertEqual(page.evaluate('mockCore.checkpoint.saves'),0,
                         'checkpoint save refuses configured RGB contacts')
        expect(page.locator('#pauseBtn')).to_have_text('Pause')
        page.locator('#rgbEncoderClear').click()
        page.locator('#saveCheckpointBtn').click()
        self.assertEqual(page.evaluate('mockCore.checkpoint.saves'),1)
        page.locator('[data-rgb-pair="1,2"]').click()
        page.locator('#restoreCheckpointBtn').click()
        expect(page.locator('#pauseBtn')).to_have_text('Resume')
        self.assertFalse(self.export_payload_for(page)['rgbEncoderFault']['configured'])

    def test_vram_export_marks_unavailable_runtime_metadata_unknown(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        page=self.page
        self.load_rom();page.locator('#pauseBtn').click()
        self.stage_circuit_file(self.circuit_configuration(model_id=2,vram_pair=[2,5]))
        page.locator('#circuitConfigApply').click()
        before=page.evaluate("""() => ({vram:structuredClone(mockCore.vramModel),
          ticks:mockCore.ticks,recoveries:structuredClone(mockCore.logic.recoveries),starts:mockCore.starts})""")
        page.evaluate('window.observedVramGetter=mockCore.core._get_vram_fault_model_state')
        healthy=self.export_payload()
        self.assertTrue(healthy['vramTransaction']['available'])
        self.assertEqual(healthy['vramTransaction']['modelId'],2)
        self.assertEqual(healthy['vramTransaction']['modelVersion'],'logical-byte-transaction-v1')
        for failure in ['null','throw','absent']:
            with self.subTest(failure=failure):
                page.evaluate("""failure=>{
                  if(failure==='null')mockCore.core._get_vram_fault_model_state=()=>null;
                  else if(failure==='throw')mockCore.core._get_vram_fault_model_state=()=>{throw Error('metadata unavailable')};
                  else delete mockCore.core._get_vram_fault_model_state;
                }""",failure)
                try:
                    payload=self.export_payload()
                    self.assertFalse(payload['vramTransaction']['available'])
                    self.assertEqual(payload['vramFault'],healthy['vramFault'],
                                     'tracked contacts remain independent of missing runtime observations')
                    rows=page.evaluate('(record)=>VRAMpageExperimentComparison.compare(record,record)',payload)
                    for label in ['VRAM Model ID','VRAM Model Version','VRAM Transaction Mask','VRAM Transaction Counts']:
                        row=next(row for row in rows if row['label']==label)
                        self.assertEqual((row['a'],row['b'],row['status']),('Unknown','Unknown','unknown'))
                    self.assertEqual(page.evaluate("""() => ({vram:structuredClone(mockCore.vramModel),
                      ticks:mockCore.ticks,recoveries:structuredClone(mockCore.logic.recoveries),starts:mockCore.starts})"""),before)
                    expect(page.locator('#pauseBtn')).to_have_text('Resume')
                finally:
                    page.evaluate('mockCore.core._get_vram_fault_model_state=observedVramGetter')
        self.assertEqual(self.export_payload()['vramTransaction'],healthy['vramTransaction'])

    def test_z80_ram_setter_partial_failure_reports_actual_state_and_pauses(self):
        self.load_rom()
        self.page.evaluate("mockCore.throwZ80RamAfter=true")
        self.apply_z80_bridge()
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertTrue(self.page.evaluate("mockCore.z80Ram.configured"))
        expect(self.page.locator("#z80RamBridgeStatus")).to_contain_text("paused for inspection")
        self.assertTrue(self.export_payload()["z80RamFault"]["configured"])

    def test_z80_ram_incomplete_api_blocks_recovery_and_configuration(self):
        self.load_rom()
        self.apply_z80_bridge()
        self.page.evaluate('delete mockCore.core._set_z80_ram_bridge')
        self.page.locator('#logicCpuResetBtn').click()
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries'),[])
        self.stage_circuit_file(self.circuit_configuration())
        self.page.locator('#circuitConfigApply').click()
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('refused before mutation')
        self.assertTrue(self.page.evaluate('mockCore.z80Ram.configured'))

    def test_z80_ram_success_status_without_clear_is_unverified(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.apply_z80_bridge()
        self.page.evaluate('mockCore.leaveZ80RamConfigured=true')
        self.page.locator('#disconnectAllFaultsBtn').click()
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#disconnectAllFaultsStatus')).to_contain_text('Z80 RAM: clear failed or unverified')
        self.assertTrue(self.page.evaluate('mockCore.z80Ram.configured'))

    def test_z80_ram_checkpoint_and_reset_lifecycle(self):
        page=self.checkpoint_page()
        self.apply_z80_bridge(page)
        page.locator("#saveCheckpointBtn").click()
        self.assertEqual(page.evaluate("mockCore.checkpoint.saves"),0)
        page.locator("#z80RamBridgeRemove").click()
        page.locator("#saveCheckpointBtn").click()
        self.apply_z80_bridge(page)
        page.locator("#restoreCheckpointBtn").click()
        self.assertFalse(page.evaluate("mockCore.z80Ram.configured"))
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        self.apply_z80_bridge(page)
        page.evaluate("() => {mockCore.fm.configured=true;mockCore.fm.bridgeA=1;mockCore.fm.bridgeB=2;}")
        page.locator("#logicCpuResetBtn").click()
        self.assertFalse(page.evaluate("mockCore.z80Ram.configured"))
        self.assertTrue(page.evaluate("mockCore.fm.configured"))
        expect(page.locator("#restoreCheckpointBtn")).to_be_enabled()
        page.locator("#resetBtn").click()
        expect(page.locator("#restoreCheckpointBtn")).to_be_disabled()
        self.assertFalse(page.evaluate("mockCore.z80Ram.configured || mockCore.fm.configured"))

    def test_all_domain_disconnect_clears_configured_domains_and_preserves_running_state(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator('[data-rgb-cut="2"]').click()
        self.apply_z80_bridge(page)
        page.locator("#ramLegAction").select_option("cut")
        page.locator("[data-chip-line]").nth(0).click()
        self.assertTrue(page.evaluate("window.mockCore.logic.active"))
        # Simultaneous domains are injected at the mock core boundary so the
        # action is tested against every native setter in one pass.
        page.evaluate("""() => {
          const c=window.mockCore;
          c.vramModel.calls.length=0;
          c.vramModel.modelId=2;c.vramModel.mask=0;c.vramModel.bridgeA=2;c.vramModel.bridgeB=5;
          c.short=[2,5];
          window.mockCore.psg.configured=true;window.mockCore.psg.dataMask=5;
          window.mockCore.psg.inputWrites='19';window.mockCore.psg.changedWrites='7';
          window.mockCore.fm.configured=true;window.mockCore.fm.bridgeA=1;window.mockCore.fm.bridgeB=6;
          window.mockCore.fm.inputWrites='11';window.mockCore.fm.changedWrites='4';
        }""")
        starts = page.evaluate("window.mockCore.starts")
        page.keyboard.down("ArrowRight")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#pauseBtn")).to_have_text("Pause")
        self.assertFalse(page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(page.evaluate("window.mockCore.vramModel.mask"), 0)
        self.assertEqual(page.evaluate("window.mockCore.vramModel.bridgeA"), -1)
        self.assertFalse(page.evaluate("window.mockCore.psg.configured"))
        self.assertFalse(page.evaluate("window.mockCore.fm.configured"))
        self.assertEqual(page.evaluate("window.mockCore.starts"), starts)
        self.assertEqual(page.evaluate("window.mockCore.logic.recoveries"), [])
        ticks = page.evaluate("window.mockCore.ticks")
        page.wait_for_timeout(120)
        self.assertGreater(page.evaluate("window.mockCore.ticks"), ticks)
        self.assertEqual(page.evaluate("window.mockCore.inputs[6]"),1,
                         "held player input continues across a successful live disconnect")
        page.keyboard.up("ArrowRight")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("Running state preserved")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("VRAM: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RAM: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("FM: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("Z80 RAM: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RGB Encoder: cleared")
        self.assertFalse(page.evaluate("mockCore.z80Ram.configured"))
        self.assertFalse(self.export_payload_for(page)["rgbEncoderFault"]["configured"])
        with page.expect_download() as info:
            page.locator("#logicExperimentBtn").click()
        payload = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(payload["cpuInterventions"], [])
        self.assertEqual(len(payload["faultDisconnects"]), 1)
        self.assertEqual(payload["faultDisconnects"][0]["action"], "all-domain-disconnect")
        self.assertEqual(len(payload["faultDisconnects"][0]["results"]), 6)

    def test_all_domain_disconnect_continues_after_audio_rejection_or_throw(self):
        for failure in ("reject", "throw"):
            page = self.new_page(circuit_config=True)
            self.load_rom(page)
            page.locator("#psgBridgeApply").click()
            page.locator("#fmBridgeApply").click()
            page.evaluate(f"window.mockCore.{ 'rejectPsgBridge' if failure == 'reject' else 'throwPsgBridge' }=true")
            starts = page.evaluate("window.mockCore.starts")
            page.locator("#disconnectAllFaultsBtn").click()
            expect(page.locator("#pauseBtn")).to_have_text("Resume")
            expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("FM: cleared")
            expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG:")
            self.assertTrue(page.evaluate("window.mockCore.psg.configured"))
            self.assertFalse(page.evaluate("window.mockCore.fm.configured"))
            self.assertEqual(page.evaluate("window.mockCore.starts"), starts)
            self.assertEqual(page.evaluate("window.mockCore.logic.recoveries"), [])
            if failure == "reject":
                expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: clear rejected (1)")
            else:
                expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: clear threw")

    def test_all_domain_disconnect_continues_after_ram_reject_or_throw(self):
        for failure in ("reject", "throw"):
            page = self.new_page(circuit_config=True)
            self.load_rom(page)
            page.locator("#logicApplyBtn").click()
            page.locator("#psgBridgeApply").click()
            page.locator("#fmBridgeApply").click()
            page.evaluate(f"window.mockCore.{ 'rejectLogicClear' if failure == 'reject' else 'throwLogicClearAfter' }=true")
            page.locator("#disconnectAllFaultsBtn").click()
            expect(page.locator("#pauseBtn")).to_have_text("Resume")
            expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RAM: clear")
            expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: cleared")
            expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("FM: cleared")
            self.assertFalse(page.evaluate("window.mockCore.psg.configured || window.mockCore.fm.configured"))
            self.assertEqual(page.evaluate("window.mockCore.logic.recoveries"), [])
            if failure == "reject":
                self.assertTrue(page.evaluate("window.mockCore.logic.active"))
                expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RAM: clear failed")
            else:
                self.assertFalse(page.evaluate("window.mockCore.logic.active"))
                expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RAM: clear threw")
                expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("core setter outcome")

    def test_all_domain_disconnect_preserves_paused_state_after_confirmed_clear(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#pauseBtn").click()
        ticks = page.evaluate("window.mockCore.ticks")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("Paused state preserved")
        page.wait_for_timeout(80)
        self.assertEqual(page.evaluate("window.mockCore.ticks"), ticks)

    def test_all_domain_disconnect_cancels_pulse_and_never_restores_momentary_vram(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicPulseFrames").select_option("writes:8")
        self.page.locator("#logicPulseBtn").click()
        self.assertEqual(self.page.evaluate("window.mockCore.logic.pulseState"), 1)
        self.page.evaluate("window.mockCore.throwFrameOnce=true")
        self.page.locator("#disconnectAllFaultsBtn").click()
        self.assertEqual(self.page.evaluate("window.mockCore.logic.pulseState"), 4)
        pulse = self.export_payload()["faultPulses"][0]
        self.assertEqual(pulse["status"], "cancelled")
        self.assertIsNone(pulse["endFrame"], "missing telemetry must not block cancellation or other domain clears")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries"), [])

        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.keyboard.down("Shift")
        page.keyboard.down("Digit1")
        self.assertEqual(page.evaluate("window.mockCore.vramModel.bridgeA"), 0)
        page.evaluate("window.mockCore.rejectVramModel=true")
        call_count = page.evaluate("window.mockCore.vramModel.calls.length")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("VRAM: clear failed")
        self.assertEqual(page.evaluate("window.mockCore.vramModel.calls.length"), call_count + 1)
        page.keyboard.up("Digit1")
        page.keyboard.up("Shift")
        self.assertEqual(page.evaluate("window.mockCore.vramModel.calls.length"), call_count + 1)
        self.assertEqual(page.evaluate("window.mockCore.vramModel.bridgeA"), 0)
        expect(page.locator("#connectionLabel")).to_have_text("AD0 ↔ AD1")

    def test_all_domain_disconnect_legacy_audio_state_is_explicitly_unavailable(self):
        page = self.new_page(legacy_psg_data=True, legacy_fm_data=True)
        self.load_rom(page)
        calls = page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        starts = page.evaluate("window.mockCore.starts")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: unavailable")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("FM: unavailable")
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"), calls)
        self.assertEqual(page.evaluate("window.mockCore.starts"), starts)

    def test_all_domain_disconnect_does_not_report_unknown_vram_state_as_off(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.evaluate("window.mockCore.nullVramState=true")
        calls = page.evaluate("window.mockCore.vramModel.calls.length")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "VRAM: clear accepted; runtime state unknown")
        self.assertEqual(page.evaluate("window.mockCore.vramModel.calls.length"), calls + 1)

    def test_all_domain_disconnect_uses_safe_vram_clear_when_support_metadata_throws(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        page.locator("#psgBridgeApply").click()
        page.evaluate("window.mockCore.throwVramSupport=true")
        calls = page.evaluate("window.mockCore.vramModel.calls.length")
        page.locator("#disconnectAllFaultsBtn").click()
        self.assertEqual(page.evaluate("window.mockCore.vramModel.calls.length"), calls + 1)
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("VRAM: cleared")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("PSG: cleared")
        self.assertFalse(page.evaluate("window.mockCore.vramModel.mask || window.mockCore.vramModel.bridgeA>=0"))
        self.assertFalse(page.evaluate("window.mockCore.psg.configured"))

    def test_all_domain_disconnect_reports_a_readable_vram_fault_left_after_accepted_clear(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        page.evaluate("window.mockCore.throwVramSupport=true;window.mockCore.leaveVramModelConfiguredAfterSet=true")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "VRAM: clear accepted; fault remains configured (runtime model 1, fault remains configured)")
        self.assertEqual(page.evaluate("[mockCore.vramModel.modelId,mockCore.vramModel.bridgeA,mockCore.vramModel.bridgeB]"), [1, 0, 1])

    def test_all_domain_disconnect_attempts_clear_when_optional_state_getters_throw(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#psgBridgeApply").click()
        page.locator("#fmBridgeApply").click()
        page.evaluate("window.mockCore.throwPsgState=true;window.mockCore.throwFmState=true")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "PSG: clear accepted; runtime state unknown")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "FM: clear accepted; runtime state unknown")
        self.assertFalse(page.evaluate("mockCore.psg.configured || mockCore.fm.configured"),
                         "unavailable telemetry must not prevent either clear setter")
        self.assertEqual(page.evaluate("mockCore.vramModel.calls.at(-1)"), [1, 0, -1, -1],
                         "VRAM clear still runs while both optional getters fail")
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(page.evaluate("mockCore.logic.recoveries"), [])

    def test_all_domain_disconnect_clears_orphan_native_pulse_and_reports_unverified_pulse(self):
        page = self.new_page()
        self.load_rom(page)
        page.evaluate("window.mockCore.logic.pulseState=1")
        self.assertEqual(self.export_payload_for(page)["faultPulses"], [],
                         "the core pulse has no matching app-scheduled pulse record")
        page.locator("#disconnectAllFaultsBtn").click()
        self.assertEqual(page.evaluate("window.mockCore.logic.pulseState"), 4)
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("RAM: cleared")

        page = self.new_page()
        self.load_rom(page)
        page.evaluate("window.mockCore.logic.pulseState=1;window.mockCore.leavePulseArmedAfterClear=true")
        page.locator("#disconnectAllFaultsBtn").click()
        self.assertEqual(page.evaluate("window.mockCore.logic.pulseState"), 1)
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "RAM: clear accepted; pulse remains armed")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "core pulse remains armed while paused")

    def test_all_domain_disconnect_syncs_vram_tracking_after_throwing_clear_mutates(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        page.evaluate("window.mockCore.throwVramModelAfter=true")
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text(
            "VRAM: clear threw (runtime model 1, no fault configured)")
        expect(page.locator("#connectionLabel")).to_have_text("NONE — NORMAL ADDRESSING")
        payload=self.export_payload_for(page)
        self.assertEqual(payload["vramFault"]["kind"], "none")
        self.assertEqual(payload["vramTransaction"]["mask"], 0)
        self.assertEqual(payload["vramTransaction"]["bridgeA"], -1)

    def test_cpu_recovery_leaves_audio_faults_active_and_names_cleared_domains(self):
        page = self.new_page(circuit_config=True)
        self.load_rom(page)
        page.locator("#psgBridgeApply").click()
        page.locator("#fmBridgeApply").click()
        page.locator("#logicApplyBtn").click()
        page.locator("#logicCpuResetBtn").click()
        self.assertFalse(page.evaluate("window.mockCore.logic.active"))
        self.assertFalse(page.evaluate("window.mockCore.vramModel.mask || window.mockCore.vramModel.bridgeA>=0"))
        self.assertTrue(page.evaluate("window.mockCore.psg.configured"))
        self.assertTrue(page.evaluate("window.mockCore.fm.configured"))
        expect(page.locator("#logicStatus")).to_contain_text("RAM/VRAM faults disconnected; audio faults unchanged")
        self.assertEqual(page.evaluate("window.mockCore.logic.recoveries"), [2])

    def test_all_domain_action_status_and_history_reset_on_new_rom(self):
        page = self.new_page()
        self.load_rom(page)
        page.locator("#disconnectAllFaultsBtn").click()
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("All-domain disconnect was incomplete")
        expect(page.locator("#disconnectAllFaultsStatus")).to_contain_text("Emulation paused before the next frame")
        self.assertEqual(len(self.export_payload_for(page)["faultDisconnects"]), 1)
        page.locator("#resetBtn").click()
        page.wait_for_function("window.mockCore.starts===2")
        expect(page.locator("#disconnectAllFaultsStatus")).to_have_text(
            "No all-domain disconnect has been attempted for this cartridge.")
        self.assertEqual(self.export_payload_for(page)["faultDisconnects"], [])

    def export_payload(self):
        with self.page.expect_download() as info:
            self.page.locator("#logicExperimentBtn").click()
        return json.loads(Path(info.value.path()).read_text())

    @staticmethod
    def export_payload_for(page):
        with page.expect_download() as info:
            page.locator("#logicExperimentBtn").click()
        return json.loads(Path(info.value.path()).read_text())

    def test_workbench_combined_configuration_randomisation_pulse_recovery_and_comparison(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        setters_before_preview=self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        config=self.circuit_configuration(vram_pair=[2,5],psg=[1,6],fm=[0,7])
        self.stage_circuit_file(config)
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Nothing has been applied")
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD2↔AD5")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"),setters_before_preview)
        self.page.locator("#circuitConfigApply").click()
        self.page.wait_for_function("mockCore.vramModel.bridgeA===2 && mockCore.psg.configured && mockCore.fm.configured")

        self.open_vram_settings()
        self.page.locator("#presetGrid .preset").first.click()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.bridgeA,mockCore.vramModel.bridgeB]"),[0,1])
        self.page.locator("#disconnectBtn").click()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.mask,mockCore.vramModel.bridgeA]"),[0,-1])

        self.page.locator("#randomPsgBtn").evaluate("button=>{const old=Math.random;Math.random=()=>0;try{button.click()}finally{Math.random=old}}")
        self.assertEqual(self.page.evaluate("mockCore.psg.dataMask"),1)
        self.assertEqual(self.page.evaluate("[mockCore.fm.bridgeA,mockCore.fm.bridgeB,mockCore.fm.dataMask]"),[0,7,0])
        self.page.locator("#randomFmBtn").evaluate("button=>{const old=Math.random;Math.random=()=>0;try{button.click()}finally{Math.random=old}}")
        self.assertEqual(self.page.evaluate("mockCore.fm.dataMask"),1)
        self.assertEqual(self.page.evaluate("mockCore.psg.dataMask"),1)

        with self.page.expect_download() as config_download:
            self.page.locator("#circuitConfigDownload").click()
        saved_config=json.loads(Path(config_download.value.path()).read_text())
        self.assertIsNone(saved_config["configuration"]["vram"]["pair"])
        self.assertEqual([saved_config["configuration"]["psg"]["dataMask"],saved_config["configuration"]["fm"]["dataMask"]],[1,1])
        self.assertNotIn("rom",saved_config)
        self.assertNotIn("history",saved_config)

        if not self.page.locator("#logicExperiment").evaluate("element=>element.open"):
            self.page.locator("#logicExperiment > summary").click()
        self.page.locator("#logicApplyBtn").click()
        self.page.evaluate("mockCore.logic.cpuFlags=3")
        self.page.locator("#logicCpuResetBtn").click()
        self.assertFalse(self.page.evaluate("mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("[mockCore.psg.dataMask,mockCore.fm.dataMask]"),[1,1])
        self.assertEqual(self.page.evaluate("mockCore.logic.recoveries"),[2])

        active_config=self.circuit_configuration(vram_pair=[2,5],psg_mask=1,fm_mask=1)
        self.stage_circuit_file(active_config)
        self.page.locator("#circuitConfigApply").click()
        self.page.locator("#disconnectAllFaultsBtn").click()
        expect(self.page.locator("#disconnectAllFaultsStatus")).to_contain_text("Running state preserved")
        self.page.locator("#pauseBtn").click()
        self.stage_circuit_file(active_config)
        self.page.locator("#circuitConfigApply").click()
        self.page.locator("#disconnectAllFaultsBtn").click()
        expect(self.page.locator("#disconnectAllFaultsStatus")).to_contain_text("Paused state preserved")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")

        self.stage_circuit_file(active_config)
        self.page.locator("#ramWriteMode").select_option("pulse")
        self.page.locator("[data-ram-frame-pair='10,14']").click()
        calls_before_apply=self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("active RAM pulse")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"),calls_before_apply)
        self.page.locator("#circuitConfigDownload").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("active RAM pulse")
        expect(self.page.locator("#circuitConfigPreview")).to_be_visible()
        self.page.locator("#pauseBtn").click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("ended after 8 emulated frames",timeout=5000)
        self.page.evaluate("window.scrollTo(0,0)")
        pair_bounds=self.page.locator("[data-ram-frame-pair]").last.evaluate(
            "button=>({top:button.getBoundingClientRect().top,bottom:button.getBoundingClientRect().bottom})")
        self.assertGreaterEqual(pair_bounds["top"],0)
        self.assertLessEqual(pair_bounds["bottom"],768)
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("applied",ignore_case=True)
        first_experiment=self.export_payload()
        pulse=first_experiment["faultPulses"][-1]
        self.assertEqual(pulse["mode"],"address-frames")
        self.assertEqual(pulse["endFrame"]-pulse["startFrame"],8)
        self.assertEqual(len(first_experiment["cpuInterventions"]),1)
        self.assertEqual(first_experiment["cpuInterventions"][0]["action"],"cpu-only-reset")
        self.assertEqual(first_experiment["cpuInterventions"][0]["flagsBefore"],3)

        self.page.locator("#randomVramBtn").evaluate("button=>{const old=Math.random;Math.random=()=>0;try{button.click()}finally{Math.random=old}}")
        setters_before_compare=self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        second_experiment=self.export_payload()
        self.page.locator("#compareFileA").set_input_files({"name":"before.json","mimeType":"application/json","buffer":json.dumps(first_experiment).encode()})
        self.page.locator("#compareFileB").set_input_files({"name":"after.json","mimeType":"application/json","buffer":json.dumps(second_experiment).encode()})
        expect(self.page.locator("#compareStatus")).to_contain_text("Both exports loaded")
        expect(self.page.locator("#compareOutput")).to_contain_text("mismatch")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"),setters_before_compare,
                         "local export comparison must not call core setters")

        starts=self.page.evaluate("mockCore.starts")
        self.page.locator("#resetBtn").click()
        self.page.wait_for_function("start=>window.mockCore.starts===start+1",arg=starts)
        reset_config=self.export_payload()
        self.assertEqual(reset_config["faultPulses"],[])
        self.assertEqual(reset_config["cpuInterventions"],[])
        self.assertFalse(reset_config["faultActive"])
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.mask,mockCore.psg.configured,mockCore.fm.configured]"),[0,False,False])

    @staticmethod
    def circuit_configuration(vram_pair=None, vram_mask=0, model_id=1, ram=None, psg=None, fm=None, psg_mask=0, fm_mask=0):
        audio = lambda pair, mask: {"pair": pair, "dataMask": mask}
        return {
            "format": "vrampage-md-circuit-config",
            "schemaVersion": 2,
            "configuration": {
                "vram": {"modelId": model_id, "mask": vram_mask, "pair": vram_pair},
                "ram": ram,
                "psg": audio(psg, psg_mask),
                "fm": audio(fm, fm_mask),
            },
        }

    def stage_circuit_file(self, payload, page=None):
        page = page or self.page
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        page.locator("#circuitConfigFile").set_input_files({
            "name": "circuit-config.json", "mimeType": "application/json", "buffer": raw.encode()
        })

    def open_vram_settings(self, page=None):
        page = page or self.page
        details = page.locator("#vramSettings")
        if not details.evaluate("element => element.open"):
            details.locator("summary").click()

    @staticmethod
    def defer_circuit_file_reads(page):
        page.evaluate("""() => {
            window.__pendingCircuitReads=[];
            File.prototype.text=function() {
                return new Promise(resolve=>window.__pendingCircuitReads.push({name:this.name,resolve}));
            };
            window.__resolveCircuitRead=(name,text)=>{
                const entry=[...window.__pendingCircuitReads].reverse().find(read=>read.name===name&&!read.done);
                if(!entry) throw new Error(`No pending circuit file read named ${name}`);
                entry.done=true; entry.resolve(text);
            };
        }""")

    def test_circuit_config_import_is_inert_then_explicit_apply_roundtrips(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        payload = self.circuit_configuration(vram_pair=[2, 5], psg=[1, 6], fm=[0, 7])
        before = self.page.evaluate("""() => ({
            vramCalls: mockCore.vramModel.calls.length,
            psgCalls: mockCore.psg.calls.length, fmCalls: mockCore.fm.calls.length,
            vramSelector: document.querySelector('#vramModel').value,
            psgA: document.querySelector('#psgBridgeA').value,
            logicCalls: mockCore.logic.setterCalls.length
        })""")
        self.stage_circuit_file(payload)
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Nothing has been applied")
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD2↔AD5")
        after_import = self.page.evaluate("""() => ({
            vramCalls: mockCore.vramModel.calls.length,
            psgCalls: mockCore.psg.calls.length, fmCalls: mockCore.fm.calls.length,
            vramSelector: document.querySelector('#vramModel').value,
            psgA: document.querySelector('#psgBridgeA').value,
            logicCalls: mockCore.logic.setterCalls.length
        })""")
        self.assertEqual(after_import, before, "preview does not call setters or change selectors")

        self.page.locator("#circuitConfigApply").click()
        self.page.wait_for_function("mockCore.psg.configured && mockCore.fm.configured")
        self.assertEqual(self.page.evaluate("mockCore.vramModel.bridgeA"), 2)
        self.assertEqual(self.page.evaluate("mockCore.vramModel.bridgeB"), 5)
        self.assertEqual(self.page.evaluate("[mockCore.psg.bridgeA,mockCore.psg.bridgeB]"), [1, 6])
        self.assertEqual(self.page.evaluate("[mockCore.fm.bridgeA,mockCore.fm.bridgeB]"), [0, 7])
        expect(self.page.locator("#circuitConfigApply")).to_be_disabled()

        with self.page.expect_download() as info:
            self.page.locator("#circuitConfigDownload").click()
        saved = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved, {**payload,"schemaVersion":6,
            "configuration":{**payload["configuration"],"z80Ram":{"pair":None},
                "rgbEncoder":{"cutMask":0,"pair":None}}})
        self.assertEqual(set(saved), {"format", "schemaVersion", "configuration"})
        self.assertNotIn("rom", saved)
        self.assertNotIn("inputWrites", json.dumps(saved))

        self.page.evaluate("""() => {
            mockCore.psg.inputWrites='42';
            mockCore.fm.inputWrites='27';
        }""")
        calls = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        self.stage_circuit_file(payload)
        self.page.locator("#circuitConfigApply").click()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"), calls,
                         "applying an identical configuration skips selectors and preserves counters")
        self.assertEqual(self.page.evaluate("mockCore.psg.inputWrites"), "42")
        self.assertEqual(self.page.evaluate("mockCore.fm.inputWrites"), "27")

    def test_chip_workbench_shows_four_compact_chips_at_mac_viewport(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        # The shared logic fixture opens diagnostics below the chip workbench.
        self.page.evaluate('window.scrollTo(0,0)')
        self.page.wait_for_function('window.scrollY === 0')
        bodies=self.page.evaluate("""() => ['#pinGrid .chip-middle','#ramChip .ram-chip-body',
          '#fmChip .chip-middle','#psgChip .chip-middle'].map(selector=>{
            const r=document.querySelector(selector).getBoundingClientRect();
            return {selector,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
          })""")
        self.assertEqual(len(bodies),4)
        for body in bodies:
            self.assertGreater(body['width'],50,body)
            self.assertGreater(body['height'],20,body)
            self.assertGreaterEqual(body['top'],0,body)
            self.assertLessEqual(body['bottom'],768,body)
        for selector in ('#ramChip [data-chip-line]','#pinGrid .pin','#fmChip .pin','#psgChip .pin'):
            self.assertGreaterEqual(self.page.locator(selector).first.evaluate('el=>el.getBoundingClientRect().height'),24)

    def test_randomiser_independently_applies_chip_settings_and_preserves_ram(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.assertEqual(self.page.locator('.randomiser-row button').all_text_contents(),
                         ['PSG','FM','VRAM','Force Resume: Off','CPU Recovery: Off','CPU Reset','Clean Restart'])
        expect(self.page.locator('#randomiserStatus')).to_have_text('Choose PSG, FM, or VRAM to randomise a chip.')
        before=self.page.evaluate('({starts:mockCore.starts,ramCalls:mockCore.logic.setterCalls.length,fm:mockCore.fm.calls.length,vram:mockCore.vramModel.calls.length})')
        def randomise(selector, value):
            return self.page.locator(selector).evaluate('''(button,value)=>{
              const saved=Math.random;let calls=0;Math.random=()=>{calls++;return value};
              try { button.click(); return calls; } finally { Math.random=saved; }
            }''',value)
        self.assertEqual(randomise('#randomPsgBtn',0),2)
        self.assertEqual(self.page.evaluate('mockCore.psg.dataMask'),1,
                         self.page.evaluate("({status:document.querySelector('#randomiserStatus').textContent,calls:mockCore.psg.maskCalls,psg:mockCore.psg,disabled:document.querySelector('#randomPsgBtn').disabled})"))
        self.assertEqual(self.page.evaluate('mockCore.fm.dataMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),before['vram'])
        self.assertEqual(randomise('#randomFmBtn',0.999999),3)
        self.assertEqual(self.page.evaluate('[mockCore.fm.bridgeA,mockCore.fm.bridgeB]'),[6,7])
        self.assertEqual(self.page.evaluate('mockCore.psg.dataMask'),1)
        self.assertEqual(randomise('#randomVramBtn',0),2)
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.at(-1).slice(1)'),[1,-1,-1])
        self.assertEqual(randomise('#randomVramBtn',0.999999),3)
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.at(-1).slice(1)'),[0,6,7])
        self.assertEqual(self.page.evaluate('mockCore.starts'),before['starts'])

        # VRAM randomisation refuses before its setter while RAM is active; audio remains independent.
        self.page.locator('#logicApplyBtn').click()
        logic_before=self.page.evaluate('({active:mockCore.logic.active,calls:mockCore.logic.setterCalls.length,vram:mockCore.vramModel.calls.length})')
        self.assertTrue(self.page.locator('#randomVramBtn').is_disabled())
        self.assertEqual(self.page.locator('#randomVramBtn').get_attribute('title'),'Disconnect the active Work RAM fault first.')
        self.page.locator('#randomVramBtn').dispatch_event('click')
        self.assertEqual(self.page.evaluate('mockCore.logic.active'),logic_before['active'])
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),logic_before['calls'])
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),logic_before['vram'])
        self.page.locator('#randomPsgBtn').evaluate('''button=>{
          const saved=Math.random;Math.random=()=>0;
          try { button.click(); } finally { Math.random=saved; }
        }''')
        self.assertNotEqual(self.page.evaluate('mockCore.psg.dataMask'),0)
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.locator('#logicDisconnectBtn').click()
        with self.page.expect_download() as info:
            self.page.locator('#circuitConfigDownload').click()
        saved=json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved['configuration']['psg']['dataMask'],self.page.evaluate('mockCore.psg.dataMask'))
        self.assertEqual(saved['configuration']['fm']['pair'],[6,7])

    def test_randomiser_refuses_armed_pulse_and_momentary_vram_bridge(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        before=self.page.evaluate('mockCore.vramModel.calls.length')
        self.page.evaluate('mockCore.logic.pulseState=1')
        self.page.locator('#randomVramBtn').dispatch_event('click')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),before)
        expect(self.page.locator('#randomiserStatus')).to_contain_text('pulse state is active')
        self.assertEqual(self.page.locator('#randomVramBtn').get_attribute('title'),
                         'An active RAM pulse prevents VRAM randomisation.')
        self.page.evaluate('mockCore.logic.pulseState=0')
        restore_state=self.page.evaluate('''()=>({model:mockCore.vramModel.modelId,mask:mockCore.vramModel.mask,
          a:mockCore.vramModel.bridgeA,b:mockCore.vramModel.bridgeB})''')
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertTrue(self.page.locator('#randomVramBtn').is_disabled())
        self.assertEqual(self.page.locator('#randomVramBtn').get_attribute('title'),'Release the held VRAM bridge first.')
        momentary_calls=self.page.evaluate('mockCore.vramModel.calls.length')
        self.page.locator('#randomVramBtn').dispatch_event('click')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),momentary_calls)
        expect(self.page.locator('#randomiserStatus')).to_contain_text('momentary VRAM bridge is active')
        self.page.keyboard.up('Digit1')
        self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('''()=>({model:mockCore.vramModel.modelId,mask:mockCore.vramModel.mask,
          a:mockCore.vramModel.bridgeA,b:mockCore.vramModel.bridgeB})'''),restore_state,
          'a refused Randomiser press must preserve the held bridge restore action')

    def test_randomiser_legacy_audio_uses_distinct_bridges_and_unavailable_getter_disables(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True,legacy_psg_mask=True,legacy_fm_mask=True)
        self.load_rom()
        def randomise(selector):
            return self.page.locator(selector).evaluate('''button=>{
              const saved=Math.random;let calls=0;Math.random=()=>{calls++;return 0};
              try { button.click(); return calls; } finally { Math.random=saved; }
            }''')
        self.assertEqual(randomise('#randomPsgBtn'),2)
        self.assertEqual(randomise('#randomFmBtn'),2)
        self.assertEqual(self.page.evaluate('[mockCore.psg.bridgeA,mockCore.psg.bridgeB,mockCore.fm.bridgeA,mockCore.fm.bridgeB]'),[0,1,0,1])
        self.page.evaluate('mockCore.throwPsgState=true')
        self.page.locator('#randomPsgBtn').dispatch_event('click')
        self.assertTrue(self.page.locator('#randomPsgBtn').is_disabled())

    def test_randomiser_partial_setter_changes_refresh_observed_chip_and_pause(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.evaluate('mockCore.rejectPsgMaskAfterMutation=true')
        self.page.locator('#randomPsgBtn').evaluate('''button=>{
          const saved=Math.random;Math.random=()=>0;
          try { button.click(); } finally { Math.random=saved; }
        }''')
        self.assertEqual(self.page.evaluate('mockCore.psg.dataMask'),1)
        self.assertTrue(self.page.locator('#psgChip .pin').nth(0).get_attribute('class').endswith('cut'))
        expect(self.page.locator('#randomiserStatus')).to_contain_text('partial state observed and emulation paused')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')

        self.page.locator('#pauseBtn').click()
        self.page.evaluate('mockCore.rejectVramModelAfterMutation=true')
        self.page.locator('#randomVramBtn').evaluate('''button=>{
          const saved=Math.random;Math.random=()=>0;
          try { button.click(); } finally { Math.random=saved; }
        }''')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.mask'),1)
        self.assertEqual(self.page.locator('#vramModel').input_value(),'1')
        self.assertIn('cut',self.page.locator('#pinGrid .pin').nth(0).get_attribute('class'))
        expect(self.page.locator('#randomiserStatus')).to_contain_text('partial runtime state observed and emulation paused')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')

    def test_randomiser_refuses_unreadable_pulse_state_before_mutating(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.evaluate('mockCore.logic.pulseState=undefined')
        self.page.locator('#psgLegMode').dispatch_event('change')
        calls=self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length]')
        self.assertTrue(self.page.locator('#randomVramBtn').is_disabled())
        self.page.locator('#randomVramBtn').dispatch_event('click')
        self.assertEqual(self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length]'),calls)
        expect(self.page.locator('#randomiserStatus')).to_contain_text('pulse state is active or unavailable')

    def test_audio_chip_inputs_are_independent_and_masks_replace_pairs(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#psgChip .pin').nth(0).click()
        self.page.locator('#fmChip .pin').nth(1).click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.configured,mockCore.fm.configured]'),[False,False],
                         'a first selection stays local to its chip')
        self.page.locator('#psgChip .pin').nth(7).click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.bridgeA,mockCore.psg.bridgeB]'),[0,7])
        self.assertFalse(self.page.evaluate('mockCore.fm.configured'))
        self.page.locator('#fmChip .pin').nth(6).click()
        self.assertEqual(self.page.evaluate('[mockCore.fm.bridgeA,mockCore.fm.bridgeB]'),[1,6])

        self.page.locator('#psgLegMode').select_option('ground')
        self.page.locator('#psgChip .pin').nth(0).click()
        self.page.locator('#psgChip .pin').nth(7).click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.configured,mockCore.psg.bridgeA,mockCore.psg.dataMask]'),[True,-1,129])
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.page.locator('#fmLegMode').select_option('ground')
        self.page.locator('#fmChip .pin').nth(3).click()
        self.assertEqual(self.page.evaluate('[mockCore.fm.bridgeA,mockCore.fm.dataMask]'),[-1,8])
        self.assertEqual(self.page.evaluate('mockCore.psg.dataMask'),129)

        self.page.evaluate("mockCore.psg.inputWrites='91';mockCore.fm.inputWrites='37'")
        calls=self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.psg.maskCalls.length,mockCore.fm.maskCalls.length]')
        with self.page.expect_download() as info:
            self.page.locator('#circuitConfigDownload').click()
        saved=json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved['schemaVersion'],6)
        self.assertEqual(saved['configuration']['psg'],{'pair':None,'dataMask':129})
        self.assertEqual(saved['configuration']['fm'],{'pair':None,'dataMask':8})
        experiment=self.export_payload()
        self.assertEqual(experiment['psgInputFault']['dataMask'],129)
        self.assertEqual(experiment['fmInputFault']['dataMask'],8)
        self.assertEqual(self.page.evaluate('[mockCore.psg.configured,mockCore.psg.bridgeA,mockCore.psg.bridgeB,mockCore.psg.dataMask,mockCore.fm.configured,mockCore.fm.bridgeA,mockCore.fm.bridgeB,mockCore.fm.dataMask]'),
                         [True,-1,-1,129,True,-1,-1,8])
        self.stage_circuit_file(saved)
        self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.psg.maskCalls.length,mockCore.fm.maskCalls.length]'),
                         calls, 'identical config should not invoke any setter')
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('already matches')
        self.assertEqual(self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.psg.maskCalls.length,mockCore.fm.maskCalls.length]'),calls)
        self.assertEqual(self.page.evaluate('[mockCore.psg.inputWrites,mockCore.fm.inputWrites]'),['91','37'])

    def test_pair_selections_stay_local_to_each_chip(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramLegAction').select_option('bridge')
        self.page.locator('#ramChip [data-chip-line]').nth(0).click()
        self.page.locator('#psgChip .pin').nth(0).click()
        self.page.locator('#fmChip .pin').nth(2).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.active,mockCore.psg.configured,mockCore.fm.configured]'),
                         [False,False,False], 'one leg on each bank is only a local pending selection')
        self.page.locator('#ramChip [data-chip-line]').nth(2).click()
        self.assertEqual(self.page.evaluate('[mockCore.logic.config.kind,mockCore.logic.config.a,mockCore.logic.config.b]'),[1,0,2])
        self.assertEqual(self.page.evaluate('[mockCore.psg.configured,mockCore.fm.configured]'),[False,False])
        self.page.locator('#psgChip .pin').nth(7).click()
        self.page.locator('#fmChip .pin').nth(6).click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.bridgeA,mockCore.psg.bridgeB,mockCore.fm.bridgeA,mockCore.fm.bridgeB]'),
                         [0,7,2,6])
        self.assertEqual(self.page.evaluate('[mockCore.logic.config.a,mockCore.logic.config.b]'),[0,2])

    def test_audio_mask_unavailable_keeps_pair_bridge_mode_available(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True,legacy_psg_mask=True)
        self.load_rom()
        self.assertTrue(self.page.locator('#psgLegMode option[data-audio-mask]').evaluate('e=>e.disabled'))
        expect(self.page.locator('#psgChip .pin').first).to_be_enabled()
        self.page.locator('#psgChip .pin').nth(0).click()
        self.page.locator('#psgChip .pin').nth(7).click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.bridgeA,mockCore.psg.bridgeB]'),[0,7])
        self.assertEqual(self.page.locator('#psgLegMode').input_value(),'bridge')

    def test_circuit_config_imports_v1_pairs_and_preflights_mask_capability(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True,legacy_psg_mask=True)
        self.load_rom()
        old={"format":"vrampage-md-circuit-config","schemaVersion":1,"configuration":{
            "vram":{"modelId":1,"mask":0,"pair":None},"ram":None,"psg":[0,7],"fm":None}}
        self.stage_circuit_file(old)
        self.page.locator('#circuitConfigApply').click()
        self.assertEqual(self.page.evaluate('[mockCore.psg.bridgeA,mockCore.psg.bridgeB]'),[0,7])
        requested=self.circuit_configuration(vram_pair=[1,5],psg_mask=128)
        before=self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.psg.calls.length]')
        self.stage_circuit_file(requested)
        self.page.locator('#circuitConfigApply').click()
        expect(self.page.locator('#circuitConfigStatus')).to_contain_text('does not support the requested PSG input cuts')
        self.assertEqual(self.page.evaluate('[mockCore.vramModel.calls.length,mockCore.psg.calls.length]'),before,
                         'missing mask capability is rejected before VRAM or PSG mutation')

    def test_circuit_config_rejects_invalid_unsupported_and_pulse_before_mutation(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        valid = self.circuit_configuration(vram_pair=[0, 1], psg=[0, 3])
        self.stage_circuit_file(valid)
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length]")
        conflict = self.circuit_configuration(vram_pair=[0, 1],
            ram={"type":"line-pair","kind":1,"access":1,"a":0,"b":1})
        self.stage_circuit_file(conflict)
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("not staged")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length]"), before)
        self.assertIn("VRAM AD0↔AD1", self.page.locator("#circuitConfigPreview").inner_text(),
                      "invalid replacement preserves the last valid staged preview")

        unsupported = self.circuit_configuration(model_id=2)
        self.page.evaluate("mockCore.vramModel.supportedModelsMask=3")
        self.stage_circuit_file(unsupported)
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        selector = self.page.locator("#vramModel").input_value()
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("refused before mutation")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"), before)
        self.assertEqual(self.page.locator("#vramModel").input_value(), selector)
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()

        self.page.evaluate("mockCore.logic.pulseState=1")
        self.stage_circuit_file(valid)
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length]")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("active RAM pulse")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length]"), before)

    def test_circuit_config_ram_handoff_late_audio_failure_pauses_and_keeps_draft(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("mockCore.logic.active")
        payload = self.circuit_configuration(vram_pair=[3, 6], psg=[0, 5])
        self.stage_circuit_file(payload)
        self.page.evaluate("mockCore.rejectPsgBridge=true")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Apply stopped at PSG")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(self.page.evaluate("mockCore.logic.active"), False,
                         "VRAM handoff disconnected the prior RAM fault before the later audio rejection")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.bridgeA,mockCore.vramModel.bridgeB]"), [3, 6])
        self.assertEqual(self.page.evaluate("mockCore.psg.configured"), False)
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()
        self.assertIn("VRAM AD3↔AD6", self.page.locator("#circuitConfigPreview").inner_text(),
                      "late failure retains the staged configuration for review")

    def test_circuit_config_setter_trap_pauses_and_reports_observed_state(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        payload = self.circuit_configuration(vram_pair=[2, 7], psg=[0, 5])
        self.stage_circuit_file(payload)
        self.page.evaluate("mockCore.throwPsgBridge=true")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("PSG setter/runtime error")
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("runtime VRAM model 1")
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("PSG state unavailable")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.bridgeA,mockCore.vramModel.bridgeB]"), [2, 7])
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()
        self.assertIn("VRAM AD2↔AD7", self.page.locator("#circuitConfigPreview").inner_text())
        if not self.page.locator("#logicExperiment").evaluate("element => element.open"):
            self.page.locator("#logicExperiment > summary").click()
        with self.page.expect_download() as info:
            self.page.locator("#logicExperimentBtn").click()
        experiment = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(experiment["vramTransaction"]["bridgeA"], 2)
        self.assertEqual(experiment["vramTransaction"]["bridgeB"], 7)
        self.assertFalse(experiment["psgInputFault"]["available"], "a failed optional getter is exported as unavailable")

    def test_circuit_config_unordered_pairs_do_not_reset_live_counters(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.stage_circuit_file(self.circuit_configuration(vram_pair=[2, 5], psg=[1, 6], fm=[0, 7]))
        self.page.locator("#circuitConfigApply").click()
        self.page.evaluate("mockCore.psg.inputWrites='42'; mockCore.fm.inputWrites='27'")
        calls = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        self.stage_circuit_file(self.circuit_configuration(vram_pair=[5, 2], psg=[6, 1], fm=[7, 0]))
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD2↔AD5")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("already matches")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"), calls)
        self.assertEqual(self.page.evaluate("[mockCore.psg.inputWrites,mockCore.fm.inputWrites]"), ["42", "27"])

    def test_circuit_config_saved_reversed_audio_selection_preserves_live_counters(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        for domain, pair in [("psg", [7, 0]), ("fm", [6, 1])]:
            self.page.locator(f"#{domain}BridgeA").select_option(str(pair[0]))
            self.page.locator(f"#{domain}BridgeB").select_option(str(pair[1]))
            self.page.locator(f"#{domain}BridgeApply").click()
        self.page.evaluate("mockCore.psg.inputWrites='42'; mockCore.fm.inputWrites='27'")
        calls = self.page.evaluate("[mockCore.psg.calls.length,mockCore.fm.calls.length]")
        with self.page.expect_download() as info:
            self.page.locator("#circuitConfigDownload").click()
        saved = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved["configuration"]["psg"], {"pair":[0,7],"dataMask":0})
        self.assertEqual(saved["configuration"]["fm"], {"pair":[1,6],"dataMask":0})
        self.stage_circuit_file(saved)
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("already matches")
        self.assertEqual(self.page.evaluate("[mockCore.psg.calls.length,mockCore.fm.calls.length]"), calls)
        self.assertEqual(self.page.evaluate("[mockCore.psg.inputWrites,mockCore.fm.inputWrites]"), ["42", "27"])

    def test_circuit_config_reversed_ram_pair_does_not_reset_fault_or_counters(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        active = self.circuit_configuration(ram={"type":"line-pair","kind":1,"access":3,"a":1,"b":0})
        self.stage_circuit_file(active)
        self.page.locator("#circuitConfigApply").click()
        self.assertTrue(self.page.evaluate("mockCore.logic.active"))
        self.page.evaluate("mockCore.logic.reads=17; mockCore.logic.writes=9")
        calls = self.page.evaluate("mockCore.logic.setterCalls.length")
        reversed_pair = self.circuit_configuration(ram={"type":"line-pair","kind":1,"access":3,"a":0,"b":1})
        self.stage_circuit_file(reversed_pair)
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("already matches")
        self.assertEqual(self.page.evaluate("mockCore.logic.setterCalls.length"), calls)
        self.assertEqual(self.page.evaluate("[mockCore.logic.active,mockCore.logic.reads,mockCore.logic.writes]"), [True,17,9])

    def test_circuit_config_saves_applied_ram_not_unapplied_selector_draft(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("mockCore.logic.active")
        self.page.locator("#logicKind").select_option("2")
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicLineA").select_option("0")
        self.page.locator("#logicLineB").select_option("1")
        with self.page.expect_download() as info:
            self.page.locator("#circuitConfigDownload").click()
        saved = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved["configuration"]["ram"],
                         {"type":"line-pair","kind":1,"access":1,"a":0,"b":1},
                         "file captures the actual applied fault, not changed form controls")
        mask_config = self.circuit_configuration(ram={"type":"address-mask","mask":5,"access":2})
        self.stage_circuit_file(mask_config)
        self.page.locator("#circuitConfigApply").click()
        self.assertEqual(self.page.evaluate("mockCore.logic.addressMask"), 5)
        with self.page.expect_download() as info:
            self.page.locator("#circuitConfigDownload").click()
        saved_mask = json.loads(Path(info.value.path()).read_text())
        self.assertEqual(saved_mask["configuration"]["ram"],
                         {"type":"address-mask","mask":5,"access":2})

    def test_circuit_config_legacy_core_allows_disabled_optional_domains_only(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True, legacy_psg_data=True, legacy_fm_data=True)
        self.load_rom()
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length]")
        self.stage_circuit_file(self.circuit_configuration())
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("already matches")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length]"), before)

        self.stage_circuit_file(self.circuit_configuration(psg=[0, 5]))
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("does not support the requested PSG")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.logic.setterCalls.length]"), before,
                         "unsupported optional input API is rejected before memory selectors change")

    def test_circuit_config_refuses_live_pending_pulse_before_setters(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicPulseFrames").select_option("writes:1")
        self.page.locator("#logicPulseBtn").click()
        self.assertEqual(self.page.evaluate("mockCore.logic.pulseState"), 1)
        self.stage_circuit_file(self.circuit_configuration(vram_pair=[0, 1], psg=[1, 4]))
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]")
        self.page.locator("#circuitConfigApply").click()
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("active RAM pulse")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length]"), before)

    def test_circuit_config_async_reads_latest_selection_only_and_blocks_apply(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        self.defer_circuit_file_reads(self.page)
        old = self.circuit_configuration(vram_pair=[0, 2])
        latest = self.circuit_configuration(vram_pair=[3, 7], psg=[1, 5], fm=[2, 6])
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.logic.setterCalls.length]")
        self.page.locator("#circuitConfigFile").set_input_files({
            "name":"older.json", "mimeType":"application/json", "buffer":json.dumps(old).encode()})
        self.page.wait_for_function("window.__pendingCircuitReads.length===1")
        expect(self.page.locator("#circuitConfigApply")).to_be_disabled()
        expect(self.page.locator("#circuitConfigCancel")).to_be_enabled()
        self.page.locator("#circuitConfigApply").evaluate("button=>{button.disabled=false;button.click()}")
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Wait for the selected configuration file")
        self.page.locator("#circuitConfigFile").set_input_files({
            "name":"latest.json", "mimeType":"application/json", "buffer":json.dumps(latest).encode()})
        self.page.wait_for_function("window.__pendingCircuitReads.length===2")
        self.page.evaluate("text=>window.__resolveCircuitRead('latest.json',text)", json.dumps(latest))
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Preview loaded")
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD3↔AD7")
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()
        self.page.evaluate("text=>window.__resolveCircuitRead('older.json',text)", json.dumps(old))
        self.page.wait_for_timeout(30)
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD3↔AD7")
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.logic.setterCalls.length]"), before,
                         "file reads and previews do not mutate selectors, core state, or history")
        self.page.locator("#circuitConfigApply").click()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.bridgeA,mockCore.vramModel.bridgeB]"), [3, 7])
        self.assertEqual(self.page.evaluate("[mockCore.psg.bridgeA,mockCore.psg.bridgeB]"), [1, 5])
        self.assertEqual(self.page.evaluate("[mockCore.fm.bridgeA,mockCore.fm.bridgeB]"), [2, 6])

    def test_circuit_config_invalid_replacement_preserves_preview_and_cancel_stales_read(self):
        self.page.close()
        self.page = self.new_page(circuit_config=True)
        self.load_rom()
        valid = self.circuit_configuration(vram_pair=[1, 4])
        self.stage_circuit_file(valid)
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("Preview loaded")
        self.defer_circuit_file_reads(self.page)
        before = self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.logic.setterCalls.length]")
        self.page.locator("#circuitConfigFile").set_input_files({
            "name":"invalid.json", "mimeType":"application/json", "buffer":b"{"})
        self.page.wait_for_function("window.__pendingCircuitReads.length===1")
        expect(self.page.locator("#circuitConfigApply")).to_be_disabled()
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD1↔AD4")
        self.page.evaluate("window.__resolveCircuitRead('invalid.json','{')")
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("previous valid preview is still available")
        expect(self.page.locator("#circuitConfigPreview")).to_contain_text("VRAM AD1↔AD4")
        expect(self.page.locator("#circuitConfigApply")).to_be_enabled()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.logic.setterCalls.length]"), before)
        self.page.locator("#circuitConfigCancel").click()
        expect(self.page.locator("#circuitConfigPreview")).to_be_hidden()

        self.page.locator("#circuitConfigFile").set_input_files({
            "name":"cancelled.json", "mimeType":"application/json", "buffer":json.dumps(valid).encode()})
        self.page.wait_for_function("window.__pendingCircuitReads.length===2")
        expect(self.page.locator("#circuitConfigApply")).to_be_disabled()
        expect(self.page.locator("#circuitConfigCancel")).to_be_enabled()
        self.page.locator("#circuitConfigCancel").click()
        self.page.evaluate("text=>window.__resolveCircuitRead('cancelled.json',text)", json.dumps(valid))
        self.page.wait_for_timeout(30)
        expect(self.page.locator("#circuitConfigStatus")).to_contain_text("pending file read canceled")
        expect(self.page.locator("#circuitConfigPreview")).to_be_hidden()
        expect(self.page.locator("#circuitConfigApply")).to_be_disabled()
        self.assertEqual(self.page.evaluate("[mockCore.vramModel.calls.length,mockCore.psg.calls.length,mockCore.fm.calls.length,mockCore.logic.setterCalls.length]"), before)

    def test_pulses_end_on_exact_emulated_frame_and_preserve_writes(self):
        self.load_rom()
        for index, duration in enumerate([1, 2, 4, 8]):
            self.page.locator("#pauseBtn").click()
            self.page.locator("#logicAccess").select_option("2")
            self.page.locator("#logicPulseFrames").select_option(str(duration))
            self.page.locator("#logicPulseBtn").click()
            before = self.page.evaluate("window.mockCore.logic.frame")
            self.page.wait_for_timeout(80)
            self.assertEqual(self.page.evaluate("window.mockCore.logic.frame"), before)
            self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"), index)
            self.page.locator("#pauseBtn").click()
            self.page.wait_for_function(f"window.mockCore.logic.recoveries.length === {index+1}")
            self.page.locator("#pauseBtn").click()
            data = self.export_payload()
            pulse = data["faultPulses"][-1]
            self.assertEqual(pulse["endFrame"]-pulse["startFrame"], duration)
            self.assertEqual(pulse["status"], "completed")
            self.assertTrue(pulse["recoveryAccepted"])
            self.assertEqual(pulse["access"], 2)
            self.assertEqual(data["writeCount"], duration)
            self.assertEqual(pulse["writeCount"], duration)
            self.assertEqual(pulse["readCount"], 0)
            self.assertFalse(data["faultActive"])
            self.assertEqual(data["cpuInterventions"][-1]["frame"], pulse["endFrame"])
            self.assertGreater(self.page.evaluate("window.mockCore.logic.storedWrites"), 0)
            # Leave running so the next loop pauses it again.
            self.page.locator("#pauseBtn").click()

    def test_quick_address_pair_keyboard_pulse_uses_writes(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        pairs = self.page.locator("[data-ram-pulse]")
        self.assertEqual(pairs.count(), 14)
        pairs.nth(13).focus()
        self.page.keyboard.press("Enter")
        self.assertEqual(self.page.locator("#logicKind").input_value(), "1")
        self.assertEqual(self.page.locator("#logicAccess").input_value(), "2")
        self.page.locator("#pauseBtn").click()
        self.page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        pulse = self.export_payload()["faultPulses"][0]
        self.assertEqual((pulse["a"], pulse["b"]), (13, 14))
        self.assertEqual(pulse["status"], "completed")

    def test_address_frame_ram_pairs_are_exact_eight_frame_write_only_bridges(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#ramWriteMode").select_option("pulse")
        pairs=self.page.locator("[data-ram-frame-pair]")
        self.assertEqual(pairs.count(),10)
        self.assertEqual(self.page.locator("#randomRamPulseBtn").count(),0)
        self.assertEqual(self.page.locator("[aria-label=\"RAM write pairs\"] > strong").inner_text(),"RAM Write")
        expect(self.page.locator('#ramWriteMode')).to_have_value('pulse')
        rows=self.page.evaluate("""() => [...document.querySelectorAll('[data-ram-frame-pair]')].map(button=>{
          const rect=button.getBoundingClientRect();return {text:button.textContent,x:rect.x,right:rect.right,y:rect.y};
        })""")
        self.assertEqual([row["text"] for row in rows], [
            "A11 ↔ A12","A11 ↔ A13","A11 ↔ A14","A11 ↔ A15",
            "A12 ↔ A13","A12 ↔ A14","A12 ↔ A15",
            "A13 ↔ A14","A13 ↔ A15","A14 ↔ A15"])
        self.assertEqual(len({row["y"] for row in rows[:5]}),1)
        self.assertEqual(len({row["y"] for row in rows[5:]}),1)
        self.assertLess(rows[0]["y"],rows[5]["y"])
        self.page.set_viewport_size({"width":360,"height":800})
        self.assertTrue(all(row["x"]>=0 and row["right"]<=360 for row in self.page.evaluate(
            """() => [...document.querySelectorAll('[data-ram-frame-pair]')].map(button=>{
              const rect=button.getBoundingClientRect();return {x:rect.x,right:rect.right};
            })""")))
        self.page.set_viewport_size({"width":1366,"height":768})
        self.page.locator("#pauseBtn").click()
        self.page.evaluate("window.mockCore.logic.writesPerTick=20")
        for index, pair in enumerate(rows):
            if index:
                self.page.locator("#pauseBtn").click()
            # Use the stable numeric data key; labels remain human-readable.
            a,b=[int(value)-1 for value in pair["text"].replace("A","").split(" ↔ ")]
            button=self.page.locator(f"[data-ram-frame-pair='{a},{b}']")
            button.click()
            self.assertEqual(self.page.evaluate("window.mockCore.logic.config.access"),2)
            self.assertEqual(self.page.evaluate("window.mockCore.logic.config.a"),a)
            self.assertEqual(self.page.evaluate("window.mockCore.logic.config.b"),b)
            self.assertEqual(self.page.evaluate("window.mockCore.logic.writes"),0)
            self.page.locator("#pauseBtn").click()
            expect(self.page.locator("#randomiserStatus")).to_contain_text(
                "ended after 8 emulated frames",timeout=5000)
            self.page.evaluate("window.scrollTo(0,0)")
            pair_bounds=self.page.locator("[data-ram-frame-pair]").last.evaluate(
                "button=>({top:button.getBoundingClientRect().top,bottom:button.getBoundingClientRect().bottom})")
            self.assertGreaterEqual(pair_bounds["top"],0)
            self.assertLessEqual(pair_bounds["bottom"],768)
            data=self.export_payload()
            pulse=data["faultPulses"][-1]
            self.assertEqual((pulse["a"],pulse["b"]),(a,b))
            self.assertEqual(pulse["mode"],"address-frames")
            self.assertEqual(pulse["requestedFrames"],8)
            self.assertNotIn("requestedWrites",pulse)
            self.assertEqual(pulse["writeCount"],160,"more than the former eight-write budget must remain bridged")
            self.assertEqual(pulse["readCount"],0)
            self.assertEqual(pulse["endFrame"]-pulse["startFrame"],8)
            self.assertEqual(pulse["releaseReason"],"frame-limit")
            self.assertFalse(pulse["cpuRecoveryAttempted"])
            self.assertFalse(pulse["recoveryAccepted"])
            self.assertEqual(pulse["status"],"completed")
            self.assertFalse(data["faultActive"])
            self.assertEqual(len(data["cpuInterventions"]),0)

    def test_address_frame_ram_pair_failures_cancel_and_release_without_cpu_recovery(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#ramWriteMode").select_option("pulse")
        pair=self.page.locator("[data-ram-frame-pair]").first
        self.page.evaluate("window.mockCore.rejectLogicFault=true")
        pair.click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("Core rejected this logic fault")
        self.assertEqual(self.export_payload()["faultPulses"],[])
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"),0)

        self.page.evaluate("window.mockCore.rejectLogicFault=false;window.mockCore.throwLogicFaultAfter=true")
        pair.click()
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        pulse=self.export_payload()["faultPulses"][0]
        self.assertEqual(pulse["status"],"incomplete")
        self.assertEqual(pulse["releaseReason"],"unknown")
        self.assertEqual(pulse["mode"],"address-frames")
        self.assertFalse(pulse["cpuRecoveryAttempted"])
        self.page.locator("#logicDisconnectBtn").click()
        self.assertEqual(self.export_payload()["faultPulses"][0]["status"],"incomplete")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"),0)

        self.page.evaluate("window.mockCore.throwLogicFaultAfter=false")
        pair.click()
        self.page.evaluate("window.mockCore.rejectLogicClear=true")
        self.page.locator("#pauseBtn").click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("release is unknown",timeout=5000)
        pulse=self.export_payload()["faultPulses"][-1]
        self.assertEqual(pulse["status"],"incomplete")
        self.assertIsNone(pulse["endFrame"])
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"),0)

        self.page.evaluate("window.mockCore.rejectLogicClear=false")
        self.page.locator("#logicDisconnectBtn").click()
        pair.click()
        self.page.evaluate("window.mockCore.throwLogicClearAfter=true")
        self.page.locator("#pauseBtn").click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("release is unknown",timeout=5000)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"),0)

    def test_address_frame_pair_waits_while_paused_and_cancellation_never_clears_later_ram(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.evaluate("window.mockCore.logic.writesPerTick=0")
        self.page.locator("#ramWriteMode").select_option("pulse")
        pair=self.page.locator("[data-ram-frame-pair='10,11']")
        expect(pair).to_be_enabled()
        pair.focus()
        self.assertEqual(pair.evaluate("button=>document.activeElement===button"),True)
        pair.press("Enter")
        expect(self.page.locator("#randomiserStatus")).to_contain_text("bridge active",timeout=3000)
        self.assertTrue(self.page.evaluate("window.mockCore.logic.active"))
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        pulse=self.export_payload()["faultPulses"][-1]
        self.assertEqual(pulse["status"],"active")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.writes"),0)
        self.page.locator("#pauseBtn").click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("ended after 8 emulated frames",timeout=5000)
        pulse=self.export_payload()["faultPulses"][-1]
        self.assertEqual(pulse["endFrame"]-pulse["startFrame"],8)
        self.assertEqual((pulse["readCount"],pulse["writeCount"]),(0,0))
        self.assertFalse(pulse["cpuRecoveryAttempted"])
        self.assertFalse(pulse["recoveryAccepted"])
        self.assertEqual(self.export_payload()["cpuInterventions"],[])

        for action in ("disconnect","replace","cpu-reset","new-rom","restart"):
            with self.subTest(action=action):
                self.page.close()
                self.page=self.new_page(circuit_config=True)
                self.load_rom()
                self.page.locator("#pauseBtn").click()
                self.page.locator("#ramWriteMode").select_option("pulse")
                self.page.locator("[data-ram-frame-pair='10,11']").click()

                if action=="disconnect":
                    self.page.locator("#logicDisconnectBtn").click()
                elif action=="replace":
                    self.page.locator("#logicAccess").select_option("1")
                    self.page.locator("#logicLineA").select_option("0")
                    self.page.locator("#logicLineB").select_option("1")
                    self.page.locator("#logicApplyBtn").click()
                elif action=="cpu-reset":
                    self.page.locator("#logicCpuResetBtn").click()
                elif action=="new-rom":
                    self.page.locator("#romFile").set_input_files({
                        "name":"replacement.bin","mimeType":"application/octet-stream",
                        "buffer":self.synthetic_rom()})
                    expect(self.page.locator("#romName")).to_have_text("REPLACEMENT.BIN")
                else:
                    self.page.locator("#resetBtn").click()
                    self.page.wait_for_function("window.mockCore.starts===2")

                if action in ("disconnect","replace","cpu-reset"):
                    cancelled=self.export_payload()["faultPulses"][0]
                    self.assertEqual(cancelled["status"],"cancelled")
                    if action=="cpu-reset":
                        self.assertEqual(self.export_payload()["cpuInterventions"][0]["action"],"cpu-only-reset")
                else:
                    expect(self.page.locator("#randomiserStatus")).to_contain_text("pulse cancelled")

                if action!="replace":
                    self.page.locator("#logicAccess").select_option("1")
                    self.page.locator("#logicLineA").select_option("0")
                    self.page.locator("#logicLineB").select_option("1")
                    self.page.locator("#logicApplyBtn").click()
                self.assertTrue(self.page.evaluate("window.mockCore.logic.active"),action)
                calls_after_apply=self.page.evaluate("window.mockCore.logic.setterCalls.length")
                frame=self.page.evaluate("window.mockCore.logic.frame")
                if self.page.locator("#pauseBtn").inner_text()=="Resume":
                    self.page.locator("#pauseBtn").click()
                target=frame+10
                self.page.wait_for_function("target=>window.mockCore.logic.frame>=target",arg=target,timeout=5000)
                self.assertTrue(self.page.evaluate("window.mockCore.logic.active"),
                                f"{action}: an expired pair pulse must not clear a later RAM fault")
                self.assertEqual(self.page.evaluate("window.mockCore.logic.setterCalls.length"),calls_after_apply,
                                 f"{action}: no late RAM clear setter call")
                expected_recoveries=1 if action=="cpu-reset" else 0
                self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"),expected_recoveries)

    def test_address_frame_ram_pairs_refuse_active_domains_before_mutation_and_need_no_recovery_api(self):
        page=self.new_page(legacy_recovery=True,circuit_config=True)
        self.load_rom(page)
        expect(page.locator("[data-ram-frame-pair]").first).to_be_enabled()
        page.locator("#logicApplyBtn").click()
        calls=page.evaluate("window.mockCore.logic.setterCalls.length")
        page.locator("#ramWriteMode").select_option("pulse")
        page.locator("[data-ram-frame-pair]").first.click()
        self.assertEqual(page.evaluate("window.mockCore.logic.setterCalls.length"),calls)
        self.assertEqual(self.export_payload_for(page)["faultPulses"],[])
        expect(page.locator("#logicStatus")).to_contain_text("No fault was applied")
        expect(page.locator("#pauseBtn")).to_have_text("Pause")

        page=self.new_page(circuit_config=True)
        self.load_rom(page)
        page.keyboard.down("Shift")
        page.keyboard.down("Digit1")
        calls=page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]")
        page.locator("#ramWriteMode").select_option("pulse")
        page.locator("[data-ram-frame-pair]").first.click()
        self.assertEqual(page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]"),calls)
        self.assertEqual(self.export_payload_for(page)["faultPulses"],[])
        expect(page.locator("#logicStatus")).to_contain_text("held VRAM bridge active")
        page.keyboard.up("Digit1")
        page.keyboard.up("Shift")

        page=self.new_page(circuit_config=True)
        self.load_rom(page)
        page.keyboard.down("Digit1")
        calls=page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]")
        page.locator("#ramWriteMode").select_option("pulse")
        page.locator("[data-ram-frame-pair]").first.click()
        self.assertEqual(page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]"),calls)
        self.assertEqual(self.export_payload_for(page)["faultPulses"],[])
        expect(page.locator("#logicStatus")).to_contain_text("VRAM fault active")
        page.keyboard.up("Digit1")

        for vram_state in (
            {"modelId":1,"mask":256,"bridgeA":-1,"bridgeB":-1},
            {"modelId":1,"mask":0,"bridgeA":0,"bridgeB":-2},
        ):
            page=self.new_page(circuit_config=True)
            self.load_rom(page)
            page.evaluate("state=>window.mockCore.vramStateOverride=state",vram_state)
            calls=page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]")
            page.locator("#ramWriteMode").select_option("pulse")
            page.locator("[data-ram-frame-pair]").first.click()
            self.assertEqual(page.evaluate("[window.mockCore.logic.setterCalls.length,window.mockCore.vramModel.calls.length]"),calls)
            self.assertEqual(self.export_payload_for(page)["faultPulses"],[])
            expect(page.locator("#logicStatus")).to_contain_text("VRAM runtime state unavailable")
            page.close()

    def test_invalid_selection_keeps_existing_pulse_and_restart_cancels(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("#logicLineB").select_option("0")
        self.page.locator("#logicApplyBtn").click()
        self.assertEqual(self.export_payload()["faultPulses"][0]["status"], "active")
        self.page.locator("#pauseBtn").click()
        self.page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicLineB").select_option("1")
        self.page.locator("#logicPulseFrames").select_option("8")
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("#resetBtn").click()
        self.assertEqual(self.export_payload()["faultPulses"], [])
        self.page.wait_for_timeout(200)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries.length"), 1)

    def test_bad_rom_rejection_preserves_paused_address_frame_pulse(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        rom=self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.evaluate("window.mockCore.logic.writesPerTick=0")
        self.page.locator("#ramWriteMode").select_option("pulse")
        self.page.locator("[data-ram-frame-pair='10,11']").click()
        before=self.export_payload()
        beforePulse=before["faultPulses"][-1]
        self.assertEqual(beforePulse["status"],"active")
        self.assertTrue(self.page.evaluate("window.mockCore.logic.active"))
        starts=self.page.evaluate("window.mockCore.starts")
        frame=self.page.evaluate("window.mockCore.logic.frame")

        self.page.locator("#romFile").set_input_files({
            "name":"bad-header-during-pulse.bin","mimeType":"application/octet-stream","buffer":bytes(512)})
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(self.page.locator("#pauseBtn")).to_have_text("Resume")
        expect(self.page.locator("#romName")).to_have_text("SYNTHETIC-TEST.BIN")
        after=self.export_payload()
        self.assertEqual(after["rom"],before["rom"])
        self.assertEqual(after["rom"]["sha256"],hashlib.sha256(rom).hexdigest())
        self.assertEqual(self.page.evaluate("window.mockCore.starts"),starts)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.frame"),frame)
        self.assertTrue(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(after["faultPulses"][-1]["status"],"active")
        self.assertEqual(after["faultPulses"][-1]["startFrame"],beforePulse["startFrame"])

        self.page.locator("#pauseBtn").click()
        expect(self.page.locator("#randomiserStatus")).to_contain_text("ended after 8 emulated frames",timeout=5000)
        finished=self.export_payload()["faultPulses"][-1]
        self.assertEqual(finished["endFrame"]-finished["startFrame"],8)
        self.assertFalse(finished["cpuRecoveryAttempted"])
        self.assertFalse(finished["recoveryAccepted"])
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries"),[])

    def test_manual_disconnect_and_replacement_cancel_pending_pulse(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicPulseFrames").select_option("8")
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("#logicDisconnectBtn").click()
        self.assertEqual(self.export_payload()["faultPulses"][0]["status"], "cancelled")
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("#logicPulseFrames").select_option("1")
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("#pauseBtn").click()
        self.page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        data = self.export_payload()
        self.assertEqual([p["status"] for p in data["faultPulses"]],
                         ["cancelled", "cancelled", "completed"])
        self.page.locator("#resetBtn").click()
        self.assertEqual(self.export_payload()["faultPulses"], [])

    def test_affected_write_budget_exhaustion_records_limit(self):
        self.load_rom()
        for index, limit in enumerate([1,2,4,8]):
            self.page.locator("#pauseBtn").click()
            self.page.evaluate("window.mockCore.logic.writesPerTick = 20")
            self.page.locator("#logicPulseFrames").select_option(f"writes:{limit}")
            self.page.locator("[data-ram-pulse]").first.click()
            self.page.locator("#pauseBtn").click()
            self.page.wait_for_function(f"window.mockCore.logic.recoveries.length === {index+1}")
            pulse = self.export_payload()["faultPulses"][-1]
            self.assertEqual(pulse["writeCount"], limit)
            self.assertEqual(pulse["requestedWrites"], limit)
            self.assertEqual(pulse["releaseReason"], "affected-write-limit")
            self.assertEqual(pulse["corePulseState"], 2)
            self.assertEqual(pulse["mode"], "affected-writes")
            self.assertEqual(pulse["endFrame"]-pulse["startFrame"], 1)
            self.assertTrue(pulse["recoveryAccepted"])

    def test_affected_write_timeout_and_read_rejection(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicPulseFrames").select_option("writes:1")
        self.page.locator("#logicPulseBtn").click()
        expect(self.page.locator("#logicStatus")).to_contain_text("require Access: Write")
        self.assertEqual(self.export_payload()["faultPulses"], [])
        self.page.evaluate("window.mockCore.logic.writesPerTick = 0")
        self.page.locator("[data-ram-pulse]").first.click()
        self.page.locator("#pauseBtn").click()
        self.page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        pulse = self.export_payload()["faultPulses"][0]
        self.assertEqual(pulse["writeCount"], 0)
        self.assertEqual(pulse["releaseReason"], "frame-limit")
        self.assertEqual(pulse["corePulseState"], 3)
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))

    def test_older_pulse_core_keeps_frame_and_eight_frame_pair_controls(self):
        page = self.new_page(legacy_write_pulse=True,circuit_config=True)
        self.load_rom(page)
        expect(page.locator("#logicPulseFrames option[value='writes:1']")).to_be_disabled()
        expect(page.locator("#logicPulseBtn")).to_be_enabled()
        page.locator("[data-ram-pulse]").first.click()
        page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        expect(page.locator("#logicStatus")).to_contain_text("Forced resume attempted")
        page.locator("#ramWriteMode").select_option("pulse")
        page.locator("[data-ram-frame-pair='10,11']").click()
        expect(page.locator("#randomiserStatus")).to_contain_text("ended after 8 emulated frames",timeout=5000)
        pulse=self.export_payload_for(page)["faultPulses"][-1]
        self.assertEqual(pulse["mode"],"address-frames")
        self.assertEqual(pulse["endFrame"]-pulse["startFrame"],8)
        self.assertFalse(pulse["cpuRecoveryAttempted"])
        self.assertNotIn("corePulseState",pulse)

    def test_vram_legs_mouse_keyboard_crosses_and_export(self):
        legs=self.page.locator('#pinGrid .pin')
        expect(legs.first).to_be_disabled()
        self.load_rom()
        expect(self.page.locator('#vramMode')).to_have_value('disconnect')
        legs.nth(0).click()
        legs.nth(7).focus()
        self.page.keyboard.press('Space')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),129)
        expect(legs.nth(0)).to_have_attribute('aria-pressed','true')
        expect(legs.nth(7).locator('.chip-cut')).to_have_css('visibility','visible')
        expect(legs.nth(7)).to_have_attribute('aria-label','AD7: forced low; reconnect')
        if OPTIONS.artifacts:
            OPTIONS.artifacts.mkdir(parents=True, exist_ok=True)
            self.page.locator('#pinGrid').screenshot(path=str(OPTIONS.artifacts / f'{OPTIONS.browser}-vram-crosses.png'))
        legs.nth(0).click()
        expect(legs.nth(0).locator('.chip-cut')).to_have_css('visibility','hidden')
        payload=self.export_payload()
        self.assertEqual(payload['vramFault'],{'kind':'address-stuck-low','addressMask':128,'lines':['AD7'],'bridge':None})
        self.assertEqual([e['mask'] for e in payload['vramAddressLineChanges']],[1,129,128])
        self.assertTrue(all(isinstance(e['reason'],str) for e in payload['vramAddressLineChanges']))
        self.open_vram_settings()
        self.page.locator('#disconnectBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.export_payload()['vramAddressLineChanges'][-1]['mask'],0)
        legs.nth(2).focus()
        self.page.keyboard.press('Enter')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),4)
        self.page.locator('#disconnectBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(2).click()
        self.page.locator('#resetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.export_payload()['vramAddressLineChanges'],[])
        self.assertEqual(self.export_payload()['vramFault']['kind'],'none')

    def test_numeric_target_cycle_is_chip_local_and_marks_target(self):
        self.page.close()
        self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        self.page.locator('#screen').click()
        target=self.page.locator('#keyboardTarget')
        expect(target).to_have_text('Keyboard Fault Target: VRAM')
        expect(self.page.locator('[data-keyboard-chip="VRAM"]')).to_have_class('chip-card keyboard-target')
        self.assertFalse(self.page.locator('[data-keyboard-chip="VRAM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="VRAM"] .chip-middle').evaluate("node=>getComputedStyle(node).outlineStyle"),'none')
        vram_body_color=self.page.locator('[data-keyboard-chip="VRAM"] .chip-middle').evaluate("node=>getComputedStyle(node).backgroundColor")
        self.page.keyboard.press('Digit0')
        expect(target).to_have_text('Keyboard Fault Target: WRAM')
        wram_body_color=self.page.locator('[data-keyboard-chip="WRAM"] .ram-chip-body').evaluate("node=>getComputedStyle(node).backgroundColor")
        self.page.keyboard.down('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertTrue(self.page.locator('[data-keyboard-chip="WRAM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="WRAM"] .ram-chip-body').evaluate("node=>getComputedStyle(node).outlineStyle"),'solid')
        self.assertEqual(self.page.locator('[data-keyboard-chip="WRAM"] .ram-chip-body').evaluate("node=>getComputedStyle(node).backgroundColor"),'rgb(220, 235, 216)')
        self.assertFalse(self.page.locator('[data-keyboard-chip="VRAM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.page.keyboard.up('Digit1')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertFalse(self.page.locator('[data-keyboard-chip="WRAM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="WRAM"] .ram-chip-body').evaluate("node=>getComputedStyle(node).backgroundColor"),wram_body_color)
        self.page.keyboard.press('Digit0')
        self.page.keyboard.press('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.assertTrue(self.page.locator('[data-keyboard-chip="FM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="FM"] .data-chip .chip-middle').evaluate("node=>getComputedStyle(node).outlineStyle"),'solid')
        self.page.emulate_media(color_scheme='dark')
        self.assertEqual(self.page.locator('#fmChip .pin').nth(0).evaluate("p=>getComputedStyle(p.querySelector('.chip-signal')).color"),self.page.locator('#fmChip .pin').nth(0).evaluate('p=>getComputedStyle(p).color'))
        self.assertEqual(self.page.locator('#fmChip .pin').nth(2).evaluate("p=>getComputedStyle(p.querySelector('.chip-signal')).color"),'rgb(36, 61, 39)')
        self.page.locator('#fmChip .pin').nth(2).hover()
        self.assertEqual(self.page.locator('#fmChip .pin').nth(2).evaluate("p=>getComputedStyle(p.querySelector('.chip-signal')).color"),self.page.locator('#fmChip .pin').nth(2).evaluate('p=>getComputedStyle(p).color'))
        self.page.emulate_media(color_scheme='light')
        self.page.keyboard.press('Digit0')
        self.page.keyboard.press('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.psg.configured'))
        self.assertTrue(self.page.locator('[data-keyboard-chip="PSG"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="PSG"] .data-chip .chip-middle').evaluate("node=>getComputedStyle(node).outlineStyle"),'solid')
        self.page.keyboard.press('Digit0')
        self.page.keyboard.press('Digit9')
        self.assertTrue(self.page.locator('[data-keyboard-chip="VRAM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertEqual(self.page.locator('[data-keyboard-chip="VRAM"] .chip-middle').evaluate("node=>getComputedStyle(node).outlineStyle"),'solid')
        self.assertEqual(self.page.locator('[data-keyboard-chip="VRAM"] .chip-middle').evaluate("node=>getComputedStyle(node).backgroundColor"),'rgb(220, 235, 216)')
        self.assertTrue(self.page.locator('[data-keyboard-chip="FM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.assertTrue(self.page.locator('[data-keyboard-chip="PSG"]').evaluate("node=>node.classList.contains('fault-active')"))

    def test_audio_fault_outline_requires_supported_runtime_state(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.keyboard.press('Digit0')
        self.page.keyboard.press('Digit0')
        self.page.keyboard.press('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.assertTrue(self.page.locator('[data-keyboard-chip="FM"]').evaluate("node=>node.classList.contains('fault-active')"))
        self.page.evaluate("""() => {
          const native=mockCore.core._get_fm_data_bridge_state;
          mockCore.core._get_fm_data_bridge_state=()=>{const {supported,...state}=native();return state};
          document.querySelector('#fmLegMode').dispatchEvent(new Event('change'));
        }""")
        self.assertFalse(self.page.locator('[data-keyboard-chip="FM"]').evaluate("node=>node.classList.contains('fault-active')"),
                         'unknown profile support must not be presented as a confirmed active FM fault')

    def test_focused_wram_preset_does_not_route_digits_to_vram(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        pair=self.page.locator('[data-ram-frame-pair="10,11"]')
        vram_calls=self.page.evaluate('mockCore.vramModel.calls.length')
        pair.focus()
        self.page.keyboard.down('Space')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.keyboard.press('Digit1')
        observed=self.page.evaluate('({vramCalls:mockCore.vramModel.calls,ramActive:mockCore.logic.active,ramCalls:mockCore.logic.setterCalls})')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),vram_calls,
                         f'digit shortcuts must not escape a focused native Work RAM preset: {observed}')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'),
                        'a key on the focused Work RAM preset must not hand the fault to VRAM')
        self.page.keyboard.up('Space')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'),
                         'the original Space owner still releases the held Work RAM fault')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),vram_calls)
        self.page.keyboard.press('Digit0')
        expect(self.page.locator('#keyboardTarget')).to_have_text('Keyboard Fault Target: WRAM')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.calls.length'),vram_calls,
                         'zero remains a keyboard-target selector while the RAM button is focused')

    def test_ram_write_keeps_all_randomiser_button_styles_unchanged(self):
        for theme in ['light','dark']:
            for mode in ['hold','pulse']:
                with self.subTest(theme=theme,mode=mode):
                    page=self.new_page(circuit_config=True,manual_frames=True)
                    page.emulate_media(color_scheme=theme)
                    buttons=page.locator('#randomPsgBtn, #randomFmBtn, #randomVramBtn')
                    style="buttons=>buttons.map(button=>{const s=getComputedStyle(button);return {opacity:s.opacity,background:s.backgroundColor,border:s.borderColor,borderStyle:s.borderStyle,color:s.color,textFill:s.webkitTextFillColor,appearance:s.appearance};})"
                    before_rom=buttons.evaluate_all(style)
                    self.assertEqual(before_rom[0],before_rom[1])
                    self.assertEqual(before_rom[1],before_rom[2])
                    page.locator('#romFile').set_input_files({'name':'synthetic.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
                    expect(page.locator('#powerLabel')).to_have_text('CONSOLE ON')
                    page.evaluate('stepTestFrame();stepTestFrame()')
                    page.locator('#ramWriteMode').select_option(mode)
                    idle=buttons.evaluate_all(style)
                    self.assertEqual(idle[0],idle[1])
                    self.assertEqual(idle[1],idle[2])
                    pair=page.locator('[data-ram-frame-pair="10,11"]')
                    if mode=='hold':
                        pair.hover();page.mouse.down()
                    else:
                        pair.click()
                    button=page.locator('#randomVramBtn')
                    expect(button).to_be_disabled()
                    expect(page.locator('#randomPsgBtn')).to_be_enabled()
                    expect(page.locator('#randomFmBtn')).to_be_enabled()
                    self.assertEqual(buttons.evaluate_all(style),idle,'RAM Write must not dim any Randomiser button')
                    self.assertFalse(button.evaluate("button=>button.matches(':active')"))
                    self.assertNotEqual(button.get_attribute('aria-pressed'),'true')
                    before=page.evaluate('mockCore.vramModel.calls.length')
                    button.evaluate('button=>button.click()')
                    self.assertEqual(page.evaluate('mockCore.vramModel.calls.length'),before)
                    self.assertTrue(page.evaluate('mockCore.logic.active'))
                    if OPTIONS.artifacts:
                        page.screenshot(path=str(OPTIONS.artifacts / f'{OPTIONS.browser}-{theme}-{mode}-randomiser-unchanged.png'),full_page=True)
                    if mode=='hold':
                        page.mouse.up()
                    else:
                        page.evaluate('for(let i=0;i<8;i++)stepTestFrame()')
                    expect(button).to_be_enabled()
                    self.assertEqual(buttons.evaluate_all(style),idle)
                    page.close()

    def test_ram_write_hold_persists_past_eight_frames_and_releases_same_owned_pair(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        expect(self.page.locator('#ramWriteMode')).to_have_value('hold')
        button=self.page.locator('[data-ram-frame-pair="10,11"]')
        button.hover()
        self.page.mouse.down()
        expect(button).to_have_attribute('aria-pressed','true')
        before=self.page.evaluate('mockCore.logic.frame')
        self.page.wait_for_function('(before)=>mockCore.logic.frame>=before+10',arg=before,timeout=5000)
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.logic.pulseState'),0)
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries.length'),0)
        self.page.mouse.up()
        expect(button).to_have_attribute('aria-pressed','false')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries.length'),0)

    def test_ram_write_hold_releases_keyboard_cancel_blur_and_replacement(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        button=self.page.locator('[data-ram-frame-pair="10,11"]')
        self.page.locator('#screen').click()
        self.page.keyboard.down('Digit0')
        self.page.keyboard.up('Digit0')
        self.page.keyboard.down('Digit9')
        expect(button).to_have_attribute('aria-pressed','false')
        expect(self.page.locator('#logicStatus')).to_contain_text('held on A13 ↔ A15')
        self.page.keyboard.down('Digit0')
        self.page.keyboard.up('Digit0')
        expect(self.page.locator('#keyboardTarget')).to_have_text('Keyboard Fault Target: FM')
        self.page.keyboard.up('Digit9')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))

        # Focused native buttons use Space/Enter as held controls without firing the click path.
        button.focus()
        self.page.keyboard.down('Space')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.keyboard.up('Space')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries.length'),0)

        # Replacing the held owner clears its release token; a later pointerup cannot clear a new fault.
        button.hover()
        self.page.mouse.down()
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.locator('#logicLineA').select_option('1')
        self.page.locator('#logicLineB').select_option('2')
        self.page.locator('#logicApplyBtn').evaluate('(button)=>button.click()')
        self.page.mouse.up()
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries.length'),0)

    def test_shift_wram_shortcut_cannot_take_ownership_from_pointer_hold(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        self.page.locator('#screen').click()
        self.page.keyboard.press('Digit0')
        pair=self.page.locator('[data-ram-frame-pair="10,11"]')
        pair.hover();self.page.mouse.down()
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),1,
                         'the second hold is rejected without replacing the pointer-owned fault')
        self.page.keyboard.up('Digit1')
        self.page.keyboard.up('Shift')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.mouse.up()
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.logic.recoveries.length'),0)

    def test_pointer_ram_release_preserves_unrelated_audio_keyboard_hold(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        self.page.locator('#screen').click()
        self.page.keyboard.press('Digit0');self.page.keyboard.press('Digit0')
        pair=self.page.locator('[data-ram-frame-pair="10,11"]')
        pair.hover();self.page.mouse.down()
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.page.mouse.up()
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.page.keyboard.up('Digit1')
        self.page.keyboard.up('Shift')
        self.assertFalse(self.page.evaluate('mockCore.fm.configured'))

    def test_blur_catches_throwing_vram_hold_restore(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#screen').click()
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.vramModel.bridgeA>=0'))
        self.page.evaluate("mockCore.throwVramModel=true")
        self.page.evaluate('window.dispatchEvent(new Event("blur"))')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#vramModelStatus')).to_contain_text('release/restoration was not confirmed')
        self.assertEqual(self.errors,[])

    def test_ram_write_hold_releases_pointercancel_and_window_blur(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        button=self.page.locator('[data-ram-frame-pair="10,11"]')
        button.evaluate('(el)=>el.addEventListener("pointerdown",e=>el.dataset.pointerId=e.pointerId,{once:true})')
        button.hover()
        self.page.mouse.down()
        pointer_id=int(button.get_attribute('data-pointer-id'))
        button.dispatch_event('pointercancel',{'pointerId':pointer_id})
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.page.mouse.up()  # Synthetic cancellation does not release Playwright's physical mouse state.
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        button.hover()
        self.page.mouse.down()
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.evaluate('window.dispatchEvent(new Event("blur"))')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.page.mouse.up()
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))

    def test_ram_write_hold_release_exceptions_are_reported_and_pause(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        self.page.locator('#screen').click()
        self.page.keyboard.press('Digit0')
        self.page.keyboard.down('Digit9')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.locator('#pauseBtn').click()
        self.page.evaluate("() => { mockCore.core._get_logic_reads=()=>{throw new Error('synthetic release getter trap')}; }")
        self.page.keyboard.up('Digit9')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#logicStatus')).to_contain_text('release/restoration was not confirmed')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.errors,[])

        self.page.evaluate("() => { mockCore.core._get_logic_reads=()=>mockCore.logic.reads; }")
        self.page.locator('#logicDisconnectBtn').evaluate('(button)=>button.click()')
        self.page.locator('#pauseBtn').click()
        self.page.keyboard.down('Digit9')
        self.page.evaluate('mockCore.throwLogicClearAfter=true')
        self.page.keyboard.up('Digit9')
        expect(self.page.locator('#logicStatus')).to_contain_text('release/restoration was not confirmed')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.errors,[])

        self.page.evaluate('mockCore.throwLogicClearAfter=false;mockCore.rejectLogicClear=false')
        self.page.locator('#logicDisconnectBtn').evaluate('(button)=>button.click()')
        self.page.keyboard.down('Digit9')
        self.page.evaluate('mockCore.rejectLogicClear=true')
        self.page.keyboard.up('Digit9')
        expect(self.page.locator('#logicStatus')).to_contain_text('release/restoration was not confirmed')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.errors,[])

    def test_pointer_ram_hold_release_exception_pauses_and_reports(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        pair=self.page.locator('[data-ram-frame-pair="10,11"]')
        pair.hover();self.page.mouse.down()
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.page.locator('#pauseBtn').evaluate('(button)=>button.click()')
        self.page.evaluate("() => { mockCore.core._get_logic_reads=()=>{throw new Error('synthetic pointer release getter trap')}; }")
        self.page.mouse.up()
        self.page.evaluate("() => { mockCore.core._get_logic_reads=()=>mockCore.logic.reads; }")
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#logicStatus')).to_contain_text('release/restoration was not confirmed')
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.errors,[])

    def test_audio_shortcut_release_rejection_pauses_and_reports(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#screen').click()
        self.page.keyboard.press('Digit0');self.page.keyboard.press('Digit0')
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.page.evaluate('mockCore.rejectFmBridge=true')
        self.page.keyboard.up('Digit1')
        self.page.keyboard.up('Shift')
        expect(self.page.locator('#pauseBtn')).to_have_text('Resume')
        expect(self.page.locator('#fmBridgeStatus')).to_contain_text('release/restoration was not confirmed')
        self.assertTrue(self.page.evaluate('mockCore.fm.configured'))
        self.assertEqual(self.errors,[])

    def test_ram_write_hold_refuses_active_vram_or_unreadable_pulse_state(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#ramWriteMode').select_option('hold')
        pair=self.page.locator('[data-ram-frame-pair="10,11"]')
        self.page.locator('#pinGrid .pin').first.click()
        pair.hover();self.page.mouse.down();self.page.mouse.up()
        expect(self.page.locator('#logicStatus')).to_contain_text('VRAM fault active')
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),0)
        self.page.locator('#disconnectBtn').evaluate('(button)=>button.click()')
        self.page.evaluate('mockCore.logic.pulseState=1')
        pair.hover();self.page.mouse.down();self.page.mouse.up()
        expect(self.page.locator('#logicStatus')).to_contain_text('RAM pulse state active or unreadable')
        self.assertEqual(self.page.evaluate('mockCore.logic.setterCalls.length'),0)

    def test_shift_vram_shortcut_restores_selected_chip_and_prior_mask_across_target_cycle(self):
        self.page.close();self.page=self.new_page(circuit_config=True)
        self.load_rom()
        self.page.locator('#pinGrid .pin').first.click()
        self.page.locator('#screen').click()
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit1')
        self.assertEqual(self.page.evaluate('mockCore.vramModel.bridgeA>=0'),True)
        self.page.keyboard.press('Digit0')
        expect(self.page.locator('#keyboardTarget')).to_have_text('Keyboard Fault Target: WRAM')
        self.page.keyboard.up('Digit1')
        self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),1)
        self.assertEqual(self.page.evaluate('mockCore.vramModel.bridgeA'),-1)

    def test_clean_restart_copy_uses_same_handler_as_toolbar(self):
        self.load_rom()
        before=self.page.evaluate('mockCore.starts')
        self.page.locator('#compactResetBtn').click()
        expect(self.page.locator('#randomiserStatus')).to_be_visible()
        self.assertEqual(self.page.evaluate('mockCore.starts'),before+1)

    def test_vram_masks_bridges_ram_pulses_and_recovery_replace(self):
        self.load_rom()
        legs=self.page.locator('#pinGrid .pin')
        legs.nth(1).click()
        self.page.locator('#vramMode').select_option('bridge')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),2,'Mode changes alone do not apply a fault')
        legs.nth(0).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),2)
        legs.nth(3).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.short'),[0,3])
        expect(self.page.locator('#pinGrid .pin.cut')).to_have_count(0)
        self.page.locator('#vramMode').select_option('disconnect')
        legs.nth(4).click()
        self.assertEqual(self.page.evaluate('mockCore.short'),[-1,-1])
        self.page.locator('#logicApplyBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        legs.nth(5).click()
        self.assertFalse(self.page.evaluate('mockCore.logic.active'))
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),32)
        self.page.locator('[data-chip-line]').nth(0).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.page.locator('#pauseBtn').click()
        self.page.locator('#logicPulseFrames').select_option('8')
        self.page.locator('#logicPulseBtn').click()
        legs.nth(6).click()
        payload=self.export_payload()
        self.assertEqual(payload['faultPulses'][-1]['status'],'active')
        self.assertTrue(payload['faultActive'])
        self.assertEqual(payload['vramFault']['addressMask'],0)
        self.assertIn('remaining budget is preserved',self.page.locator('#logicStatus').inner_text())
        self.page.locator('#manualForceResumeBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(3).click()
        self.page.locator('#logicCpuResetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(2).click()
        self.open_vram_settings()
        self.page.locator('.preset').first.click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        expect(self.page.locator('#pinGrid .pin.connected')).to_have_count(2)
        legs.nth(7).click()
        # Remove focus from the button before global shortcuts.
        self.page.locator('#screen').click()
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit2')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.short'),[0,2])
        self.page.keyboard.up('Digit2')
        self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),128)

    def test_vram_mask_rejection_and_failed_ram_disconnect(self):
        self.load_rom()
        self.page.locator('#pinGrid .pin').first.click()
        self.page.evaluate('mockCore.rejectVramMask=true')
        self.page.locator('#pinGrid .pin').nth(1).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),1)
        expect(self.page.locator('#pinGrid .pin').nth(1)).to_have_attribute('aria-pressed','false')
        self.page.evaluate('mockCore.rejectVramMask=false')
        self.page.locator('#logicApplyBtn').click()
        self.page.locator('#pauseBtn').click()
        self.page.locator('#logicPulseFrames').select_option('8')
        self.page.locator('#logicPulseBtn').click()
        self.page.evaluate('mockCore.rejectLogicClear=true')
        self.page.locator('#pinGrid .pin').nth(3).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        expect(self.page.locator('#pinGrid .pin.cut')).to_have_count(0)
        self.assertEqual(self.export_payload()['faultPulses'][-1]['status'],'active',
                         'Failed takeover must preserve the armed pulse timer')
        self.page.locator('#manualForceResumeBtn').click()
        self.assertEqual(self.export_payload()['faultPulses'][-1]['status'],'active')
        self.page.evaluate('mockCore.rejectLogicClear=false')
        self.page.locator('#pauseBtn').click()
        self.page.wait_for_function('!mockCore.logic.active')
        self.assertEqual(self.export_payload()['faultPulses'][-1]['status'],'completed')

    def test_legacy_vram_core_keeps_bridge_controls(self):
        page=self.new_page(legacy_vram_chip=True)
        self.load_rom(page)
        expect(page.locator('#vramMode')).to_have_value('bridge')
        self.assertTrue(page.locator('#vramMode option[value="disconnect"]').evaluate('e=>e.disabled'))
        expect(page.locator('#vramModeHint')).to_contain_text('older core')
        page.locator('#pinGrid .pin').nth(0).click()
        page.locator('#pinGrid .pin').nth(1).click()
        expect(page.locator('#pinGrid .pin.connected')).to_have_count(2)
        expect(page.locator('#pinGrid .pin .chip-cut').first).to_have_css('visibility','hidden')
        self.open_vram_settings(page)
        page.locator('#disconnectBtn').click()
        expect(page.locator('#pinGrid .pin.connected')).to_have_count(0)

    def test_compact_chip_geometry_and_bridge_controls(self):
        self.load_rom()
        for scheme in ('light', 'dark'):
            self.page.emulate_media(color_scheme=scheme)
            for width, height in ((1366, 768), (1280, 720), (1280, 800), (390, 844), (844, 390)):
                self.page.set_viewport_size({'width': width, 'height': height})
                for container, body, pins, max_height in (
                    ('#pinGrid', '.chip-middle', '.pin', 132),
                    ('#ramChip', '.ram-chip-body', '[data-chip-line]', 194),
                ):
                    geometry = self.page.locator(container).evaluate("""(chip, args) => {
                        const body = chip.querySelector(args.body).getBoundingClientRect();
                        return {
                            height: chip.getBoundingClientRect().height,
                            labelsInside: [...chip.querySelectorAll('.chip-signal')].every(e => {
                                const r = e.getBoundingClientRect();
                                return r.left >= body.left && r.right <= body.right &&
                                    r.top >= body.top && r.bottom <= body.bottom;
                            }),
                            shortLegs: [...chip.querySelectorAll('.chip-wire')].every(e =>
                                e.getBoundingClientRect().width <= 20),
                            targets: [...chip.querySelectorAll(args.pins)].every(e => {
                                const r = e.getBoundingClientRect();
                                return r.width >= 24 && r.height >= 24;
                            }),
                            count: chip.querySelectorAll(args.pins).length
                        };
                    }""", {'body': body, 'pins': pins})
                    self.assertLessEqual(geometry['height'], max_height)
                    self.assertTrue(geometry['labelsInside'], (scheme, width, container))
                    self.assertTrue(geometry['shortLegs'])
                    self.assertTrue(geometry['targets'], (scheme, width, container))
                    self.assertEqual(geometry['count'], 8 if container == '#pinGrid' else 15)
        self.page.locator('#vramMode').select_option('bridge')
        self.page.locator('#pinGrid .pin').nth(0).click()
        self.page.locator('#pinGrid .pin').nth(7).focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('#pinGrid .pin.connected')).to_have_count(2)
        self.open_vram_settings()
        self.page.locator('#disconnectBtn').click()
        expect(self.page.locator('#pinGrid .pin.connected')).to_have_count(0)

    def test_chip_multiple_lines_keyboard_restore_and_export(self):
        self.load_rom()
        pins = self.page.locator("[data-chip-line]")
        self.assertEqual(pins.count(), 15)
        pins.nth(0).click()
        pins.nth(14).focus()
        self.page.keyboard.press("Space")
        expect(pins.nth(0)).to_have_attribute("aria-pressed", "true")
        expect(pins.nth(14).locator(".chip-cut")).to_have_css("visibility", "visible")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.addressMask"), 0x4001)
        if OPTIONS.artifacts:
            OPTIONS.artifacts.mkdir(parents=True, exist_ok=True)
            self.page.locator("#ramChip").screenshot(path=str(OPTIONS.artifacts / f"{OPTIONS.browser}-chip-crosses.png"))
        self.page.locator("#logicLineB").select_option("0")
        self.page.locator("#logicApplyBtn").click()
        expect(pins.nth(0)).to_have_attribute("aria-pressed", "true")
        data = self.export_payload()
        self.assertEqual(data["logicFault"]["kind"], "address-stuck-low")
        self.assertEqual(data["logicFault"]["lines"], ["A1", "A15"])
        self.assertEqual([e["mask"] for e in data["addressLineChanges"]], [1,0x4001])
        pins.nth(0).click()
        expect(pins.nth(0).locator(".chip-cut")).to_have_css("visibility", "hidden")
        self.page.locator("#chipRestoreBtn").click()
        self.assertEqual(self.page.evaluate("window.mockCore.logic.addressMask"), 0)
        self.assertFalse(self.export_payload()["faultActive"])

    def test_chip_replacement_restart_and_mobile_layout(self):
        self.load_rom()
        self.page.locator("#pauseBtn").click()
        self.page.locator("#logicPulseBtn").click()
        self.page.locator("[data-chip-line]").nth(1).click()
        self.assertEqual(self.export_payload()["faultPulses"][0]["status"], "cancelled")
        self.page.locator("#logicApplyBtn").click()
        expect(self.page.locator("[data-chip-line]").nth(1)).to_have_attribute("aria-pressed", "true")
        self.page.locator("[data-chip-line]").nth(2).click()
        self.page.locator("#manualForceResumeBtn").click()
        self.assertEqual(self.page.evaluate("window.mockCore.logic.addressMask"), 0)
        idle_light=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.page.emulate_media(color_scheme="dark")
        idle_dark=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.assertNotEqual(idle_light,idle_dark)
        self.page.emulate_media(color_scheme="light")
        self.page.locator("[data-chip-line]").nth(3).click()
        light=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.page.emulate_media(color_scheme="dark")
        dark=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.assertEqual(light,'rgb(220, 235, 216)')
        self.assertEqual(dark,light)
        self.assertEqual(self.page.locator('.ram-chip-body strong').evaluate('e=>getComputedStyle(e).color'),'rgb(36, 61, 39)')
        self.page.emulate_media(color_scheme="light")
        for width,height in [(1366,768),(390,844),(844,390)]:
            self.page.set_viewport_size({"width":width,"height":height})
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width)
        self.page.locator("#resetBtn").click()
        self.assertEqual(self.export_payload()["addressLineChanges"], [])
        expect(self.page.locator("[data-chip-line]").nth(3)).to_have_attribute("aria-pressed", "false")

    def test_older_core_disables_chip_only(self):
        page=self.new_page(legacy_chip=True)
        self.load_rom(page)
        expect(page.locator("[data-chip-line]").first).to_be_disabled()
        expect(page.locator("#logicApplyBtn")).to_be_enabled()
        expect(page.locator("#logicPulseBtn")).to_be_enabled()

    def test_older_logic_core_disables_only_recovery(self):
        page = self.new_page(legacy_recovery=True)
        self.load_rom(page)
        expect(page.locator("#logicApplyBtn")).to_be_enabled()
        expect(page.locator("#manualForceResumeBtn")).to_be_disabled()
        expect(page.locator("#logicCpuResetBtn")).to_be_disabled()
        expect(page.locator("#logicPulseBtn")).to_be_disabled()
        expect(page.locator("[data-ram-pulse]").first).to_be_disabled()
        page.locator("#logicApplyBtn").click()
        expect(page.locator("#logicStatus")).to_contain_text("Applied address")

    def test_recovery_preserves_ram_and_exports_each_intervention(self):
        self.load_rom()
        self.page.locator("#logicAccess").select_option("2")
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("window.mockCore.logic.storedWrites > 0")
        self.page.locator("#pauseBtn").click()
        stored = self.page.evaluate("window.mockCore.logic.storedWrites")
        self.page.evaluate("window.mockCore.logic.cpuFlags = 3")
        self.page.locator("#manualForceResumeBtn").focus()
        self.page.keyboard.press("Enter")
        expect(self.page.locator("#logicCpuStatus")).to_have_text("No STOP/HALT flag")
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("window.mockCore.logic.storedWrites"), stored)
        self.page.locator("#logicCpuResetBtn").focus()
        self.page.keyboard.press("Space")
        self.assertEqual(self.page.evaluate("window.mockCore.logic.recoveries"), [1,2])
        self.assertEqual(self.page.evaluate("window.mockCore.starts"), 1)
        with self.page.expect_download() as info:
            self.page.locator("#logicExperimentBtn").click()
        payload = json.loads(Path(info.value.path()).read_text())
        self.assertEqual([e["action"] for e in payload["cpuInterventions"]],
                         ["force-resume", "cpu-only-reset"])
        self.assertEqual(payload["cpuInterventions"][0]["flagsBefore"], 3)
        self.assertEqual(payload["cpuInterventions"][0]["flagsAfter"], 0)
        self.page.locator("#resetBtn").click()
        with self.page.expect_download() as info:
            self.page.locator("#logicExperimentBtn").click()
        self.assertEqual(json.loads(Path(info.value.path()).read_text())["cpuInterventions"], [])

    def ordered_page(self, **options):
        self.page.close()
        self.page=self.new_page(circuit_config=True,manual_frames=True,automatic_recovery=True,**options)
        self.page.locator('#romFile').set_input_files({'name':'ordered.bin','mimeType':'application/octet-stream','buffer':self.synthetic_rom()})
        expect(self.page.locator('#powerLabel')).to_have_text('CONSOLE ON')
        self.recovery_frames(2)
        return self.page

    def recovery_frames(self, count):
        self.page.evaluate('n=>{for(let i=0;i<n;i++)stepTestFrame()}',count)

    def persistent_halt(self):
        self.page.evaluate("() => {mockCore.cpuFlagsByFrame=new Proxy({}, {get:()=>2});}")

    def test_ordered_recovery_defaults_on_and_preferences_survive_restart(self):
        page=self.ordered_page()
        for selector,label in [('#logicResumeBtn','Force Resume: On'),('#armCpuRecoveryBtn','CPU Recovery: On')]:
            expect(page.locator(selector)).to_have_text(label)
            expect(page.locator(selector)).to_have_attribute('aria-pressed','true')
            self.assertTrue(page.locator(selector).evaluate("button=>!!button.closest('.randomiser-row')"))
        page.evaluate('window.scrollTo(0,0)')
        bounds=page.locator('[data-ram-frame-pair="13,14"]').evaluate('button=>button.getBoundingClientRect().bottom')
        self.assertLessEqual(bounds,768,'Default-On recovery switches must retain the compact RAM button budget')
        page.locator('#logicResumeBtn').click()
        page.locator('#resetBtn').click()
        expect(page.locator('#logicResumeBtn')).to_have_text('Force Resume: Off')
        expect(page.locator('#armCpuRecoveryBtn')).to_have_text('CPU Recovery: On')
        self.assertEqual(self.export_payload()['automaticRecovery']['waitFrames'],8)

    def test_ordered_recovery_ignores_stop_static_output_and_both_off(self):
        page=self.ordered_page()
        for flags in [0,1]:
            page.evaluate('flags=>mockCore.logic.cpuFlags=flags',flags)
            self.recovery_frames(20)
            self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        page.locator('#logicResumeBtn').click();page.locator('#armCpuRecoveryBtn').click()
        self.persistent_halt();self.recovery_frames(20)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])

    def test_ordered_recovery_confirms_halt_and_cancels_reset_after_flag_clears(self):
        page=self.ordered_page()
        page.evaluate('mockCore.logic.cpuFlags=2')
        self.recovery_frames(1)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        page.evaluate('mockCore.logic.cpuFlags=0');self.recovery_frames(1)
        page.evaluate('mockCore.logic.cpuFlags=2');self.recovery_frames(2)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        self.recovery_frames(1)  # Native Force Resume cleared the flag.
        self.persistent_halt();self.recovery_frames(20)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        event=self.export_payload()['cpuInterventions'][-1]
        self.assertEqual(event['trigger'],'halt-recovery-sequence')
        self.assertEqual(event['stage'],'force-resume')
        self.assertEqual(len(event['observedFrames']),2)
        self.assertEqual(event['outcome'],'issued')

    def test_ordered_recovery_waits_eight_halt_frames_and_never_loops(self):
        page=self.ordered_page()
        page.evaluate('mockCore.core._set_psg_data_bridge(1,0,1);mockCore.core._set_fm_data_bridge(1,2,3)')
        self.persistent_halt();self.recovery_frames(2)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        self.assertTrue(self.export_payload()['automaticRecovery']['waitingAfterForceResume'])
        for _ in range(7):
            self.recovery_frames(1)
            self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        self.recovery_frames(1)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2])
        self.recovery_frames(30)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2])
        self.assertTrue(page.evaluate('mockCore.psg.configured && mockCore.fm.configured'))
        payload=self.export_payload()
        self.assertFalse(payload['automaticRecovery']['waitingAfterForceResume'])
        events=payload['cpuInterventions']
        self.assertEqual([e['action'] for e in events],['force-resume','cpu-only-reset'])
        self.assertEqual(events[-1]['frame']-events[0]['frame'],8)
        self.assertEqual(events[-1]['waitFrames'],8)
        self.assertEqual(len(events[-1]['observedFrames']),8)
        self.assertTrue(all(e['attempted'] and e['outcome']=='issued' for e in events))
        expect(page.locator('#logicResumeBtn')).to_have_attribute('aria-pressed','true')
        expect(page.locator('#armCpuRecoveryBtn')).to_have_attribute('aria-pressed','true')

    def test_rgb_encoder_edits_preserve_pending_recovery_without_rearming_it(self):
        page=self.ordered_page()
        self.persistent_halt();self.recovery_frames(2)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        before=self.export_payload()['automaticRecovery']
        self.assertTrue(before['waitingAfterForceResume'])
        page.locator('[data-rgb-cut="0"]').click()
        self.assertEqual(self.export_payload()['automaticRecovery'],before)
        with page.expect_download() as downloaded:page.locator('#circuitConfigDownload').click()
        config=json.loads(Path(downloaded.value.path()).read_text())
        config['configuration']['rgbEncoder']={'cutMask':2,'pair':[0,1]}
        self.stage_circuit_file(config)
        expect(page.locator('#circuitConfigApply')).to_be_enabled()
        page.locator('#circuitConfigApply').click()
        self.assertEqual(self.export_payload()['automaticRecovery'],before,
                         'RGB-only imports must preserve a genuinely pending eight-frame escalation')
        self.recovery_frames(7)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        self.recovery_frames(1)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2])
        self.assertEqual(self.export_payload()['rgbEncoderFault']['cutMask'],2)
        page.locator('[data-rgb-cut="2"]').click()
        self.recovery_frames(30)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2],
                         'RGB edits must not start a second automatic CPU recovery sequence')

    def test_ordered_recovery_toggles_work_independently(self):
        for off_selector,expected in [('#armCpuRecoveryBtn',[1]),('#logicResumeBtn',[2])]:
            with self.subTest(off=off_selector):
                page=self.ordered_page()
                page.locator(off_selector).click()
                self.persistent_halt();self.recovery_frames(20)
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),expected)

    def test_ordered_recovery_explicit_resume_or_fault_edit_permits_new_sequence(self):
        page=self.ordered_page()
        self.persistent_halt();self.recovery_frames(10)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2])
        page.locator('#pauseBtn').click();page.locator('#pauseBtn').click()
        self.recovery_frames(10)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2,1,2])
        page.locator('#logicApplyBtn').click();self.recovery_frames(10)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,2,1,2,1,2])

    def test_ordered_recovery_toggle_change_cancels_old_escalation(self):
        page=self.ordered_page()
        self.persistent_halt();self.recovery_frames(2)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        page.locator('#armCpuRecoveryBtn').click()  # Explicit policy change starts a new opportunity.
        self.recovery_frames(15)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1,1])
        self.assertFalse(self.export_payload()['automaticRecovery']['cpuRecoveryEnabled'])

    def test_ordered_recovery_defers_entire_ram_pulse_and_contact_end_frame(self):
        page=self.ordered_page()
        page.locator('#ramWriteMode').select_option('pulse')
        page.locator('[data-ram-frame-pair="10,11"]').click()
        self.persistent_halt()
        for _ in range(8):
            self.recovery_frames(1)
            self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        self.recovery_frames(1)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        self.recovery_frames(1)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        payload=self.export_payload();end=payload['faultPulses'][-1]['endFrame']
        self.assertEqual(payload['cpuInterventions'][-1]['observedFrames'],[end+1,end+2])

    def test_ordered_recovery_held_contact_blur_and_hidden_cancel_without_turning_off(self):
        page=self.ordered_page()
        pair=page.locator('[data-ram-frame-pair="10,11"]')
        pair.hover();page.mouse.down()
        self.persistent_halt();self.recovery_frames(12)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        page.mouse.up();self.recovery_frames(12)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        for selector in ['#logicResumeBtn','#armCpuRecoveryBtn']:
            expect(page.locator(selector)).to_have_attribute('aria-pressed','true')
        page.locator('#logicApplyBtn').click();self.recovery_frames(2)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
        self.recovery_frames(12)
        page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'))")
        self.recovery_frames(12)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])

    def test_ordered_recovery_manual_actions_and_checkpoints_cancel_pending_reset(self):
        for action in ['disconnect','manual-resume','manual-reset','save']:
            with self.subTest(action=action):
                page=self.ordered_page(session_checkpoint=True)
                self.persistent_halt();self.recovery_frames(2)
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
                selector={'disconnect':'#disconnectAllFaultsBtn','manual-resume':'#manualForceResumeBtn',
                          'manual-reset':'#logicCpuResetBtn','save':'#saveCheckpointBtn'}[action]
                page.locator(selector).click()
                expected={'disconnect':[1],'manual-resume':[1,1],'manual-reset':[1,2],'save':[1]}[action]
                self.recovery_frames(20)
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),expected)
                expect(page.locator('#armCpuRecoveryBtn')).to_have_attribute('aria-pressed','true')

    def test_ordered_recovery_telemetry_and_clear_failures_pause_and_record(self):
        for fault in ['flags','frame','invalid','ram-clear','vram-clear']:
            with self.subTest(fault=fault):
                page=self.ordered_page()
                if fault=='flags':page.evaluate('mockCore.throwCpuFlags=true')
                elif fault=='frame':page.evaluate('mockCore.throwLogicFrame=true')
                elif fault=='invalid':page.evaluate('mockCore.invalidCpuFlags=4')
                elif fault=='ram-clear':
                    page.locator('#logicApplyBtn').click()
                    page.evaluate('mockCore.rejectLogicClear=true')
                    self.persistent_halt()
                else:
                    page.keyboard.press('1')
                    page.evaluate('mockCore.rejectVramModel=true')
                    self.persistent_halt()
                self.recovery_frames(2)
                expect(page.locator('#pauseBtn')).to_have_text('Resume')
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
                page.evaluate('mockCore.throwCpuFlags=false;mockCore.throwLogicFrame=false;delete mockCore.invalidCpuFlags')
                event=self.export_payload()['cpuInterventions'][-1]
                self.assertEqual(event['trigger'],'halt-recovery-sequence')
                self.assertEqual(event['stage'],'force-resume')
                self.assertEqual(event['waitFrames'],2)
                self.assertFalse(event['attempted'])
                self.assertEqual(event['outcome'],'aborted')
                expect(page.locator('#logicResumeBtn')).to_have_attribute('aria-pressed','true')

    def test_ordered_recovery_waiting_telemetry_failure_records_cpu_stage(self):
        page=self.ordered_page()
        self.persistent_halt();self.recovery_frames(5)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
        page.evaluate('mockCore.throwCpuFlags=true');self.recovery_frames(1)
        expect(page.locator('#pauseBtn')).to_have_text('Resume')
        page.evaluate('mockCore.throwCpuFlags=false')
        event=self.export_payload()['cpuInterventions'][-1]
        self.assertEqual(event['stage'],'cpu-reset')
        self.assertEqual(event['waitFrames'],8)
        self.assertEqual(len(event['observedFrames']),3)
        self.assertFalse(event['attempted'])
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])

    def test_ordered_recovery_native_rejection_and_trap_do_not_retry(self):
        for trap in [False,True]:
            with self.subTest(trap=trap):
                page=self.ordered_page()
                page.evaluate("trap=>{mockCore.core._recover_logic_cpu=mode=>{mockCore.logic.recoveries.push(mode);if(trap)throw Error('native trap');return 5;};}",trap)
                self.persistent_halt();self.recovery_frames(2)
                expect(page.locator('#pauseBtn')).to_have_text('Resume')
                self.recovery_frames(20)
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[1])
                event=self.export_payload()['cpuInterventions'][-1]
                self.assertTrue(event['attempted'])
                self.assertEqual(event['outcome'],'aborted' if trap else 'rejected')

    def test_ordered_recovery_post_native_telemetry_error_preserves_issued_record(self):
        for mode in [1,2]:
            with self.subTest(mode=mode):
                page=self.ordered_page()
                if mode==2:page.locator('#logicResumeBtn').click()
                page.evaluate("""() => {
                    const native=mockCore.core._recover_logic_cpu;
                    mockCore.core._recover_logic_cpu=mode=>{const status=native(mode);mockCore.throwCpuFlags=true;return status;};
                    mockCore.logic.cpuFlags=2;
                }""")
                self.recovery_frames(2)
                expect(page.locator('#pauseBtn')).to_have_text('Resume')
                page.evaluate('mockCore.throwCpuFlags=false')
                self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[mode])
                event=self.export_payload()['cpuInterventions'][-1]
                self.assertEqual(event['outcome'],'issued')
                self.assertTrue(event['attempted'])
                self.assertIsNone(event['flagsAfter'])
                self.assertIn('telemetryError',event)

    def test_ordered_recovery_legacy_core_reports_unavailable_without_actions(self):
        page=self.ordered_page(legacy_recovery=True)
        self.persistent_halt();self.recovery_frames(20)
        self.assertEqual(page.evaluate('mockCore.logic.recoveries'),[])
        expect(page.locator('#cpuRecoveryStatus')).to_have_text('Automatic Recovery Unavailable')

    def assert_build_export(self, expected):
        rom=self.load_rom()
        self.page.locator('#logicApplyBtn').click()
        payload=self.export_payload()
        self.assertEqual(payload['schemaVersion'],1)
        self.assertEqual(payload['build'],expected)
        self.assertEqual(payload['modelVersion'],'0.5.1-experimental')
        self.assertEqual(payload['rom']['sha256'],hashlib.sha256(rom).hexdigest())
        self.assertEqual(payload['logicFault']['kind'],'address')
        self.assertTrue(payload['faultActive'])
        self.assertNotIn('romBytes',payload)
        return payload

    @staticmethod
    def valid_build_info():
        return {'application':'VRAMpage MD','application_version':'0.5.1',
                'source_commit':'a'*40,'package_format':1}

    def test_export_provenance_valid_and_filters_unknown_fields(self):
        info=self.valid_build_info()
        info.update({'token':'must-not-be-exported','private':{'secret':'ignore'}})
        self.page=self.new_page(build_info=info)
        payload=self.assert_build_export({'status':'available','applicationVersion':'0.5.1','sourceCommit':'a'*40})
        self.assertNotIn('must-not-be-exported',json.dumps(payload))
        self.assertNotIn('private',payload['build'])
        self.page.locator('#resetBtn').click()
        self.assertEqual(self.export_payload()['build']['sourceCommit'],'a'*40)

    def test_export_provenance_missing(self):
        self.assert_build_export({'status':'unavailable','applicationVersion':'0.5.1','sourceCommit':None})

    def test_export_provenance_malformed(self):
        for malformed in ('{broken', 'null', [], self.valid_build_info() | {'source_commit':'A'*40},
                          self.valid_build_info() | {'source_commit':'a'*39},
                          self.valid_build_info() | {'package_format':'1'}):
            with self.subTest(metadata=malformed):
                self.page=self.new_page(build_info=malformed)
                self.assert_build_export({'status':'unavailable','applicationVersion':'0.5.1','sourceCommit':None})

    def test_export_provenance_mismatched_application_or_version(self):
        for mismatch in ({'application':'Other app'},{'application_version':'0.2.5'},
                         {'package_format':2}):
            with self.subTest(metadata=mismatch):
                self.page=self.new_page(build_info=self.valid_build_info() | mismatch)
                self.assert_build_export({'status':'unavailable','applicationVersion':'0.5.1','sourceCommit':None})

    def test_export_provenance_timeout_never_blocks_play_or_export(self):
        self.page=self.new_page(stalled_build_info=True)
        self.assert_build_export({'status':'unavailable','applicationVersion':'0.5.1','sourceCommit':None})
        self.assertEqual(self.page.evaluate('window.__buildInfoRequests'),1)
        self.assertEqual(self.page.evaluate('window.__buildInfoOptions'),{'credentials':'omit','cache':'no-store'})
        self.assertGreater(self.page.evaluate('mockCore.ticks'),0)
        self.assertFalse(self.page.evaluate('!!window.__buildInfoAborted'), 'Export must finish while metadata is still pending')
        self.page.evaluate('window.__finishBuildInfoTimeout()')
        self.assertTrue(self.page.evaluate('window.__buildInfoAborted'))
        self.assertEqual(self.export_payload()['build']['status'],'unavailable')

    def test_experiment_export_contains_hash_and_metadata_not_rom_bytes(self):
        rom = self.load_rom()
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("window.mockCore.logic.reads > 0")
        self.page.evaluate("window.mockCore.logic.cpuFlags = 3")
        with self.page.expect_download() as download_info:
            self.page.locator("#logicExperimentBtn").click()
        download = download_info.value
        payload = json.loads(Path(download.path()).read_text())
        self.assertEqual(payload["modelVersion"], "0.5.1-experimental")
        self.assertEqual(payload["rom"]["name"], "synthetic-test.bin")
        self.assertEqual(payload["rom"]["sha256"], hashlib.sha256(rom).hexdigest())
        self.assertNotIn("bytes", payload["rom"])
        self.assertNotIn("romBytes", payload)
        self.assertFalse(any(isinstance(value, list) and len(value) > 128
                             for value in payload.values()))
        self.assertTrue(payload["faultActive"])
        self.assertEqual(payload["logicFault"]["kind"], "address")
        self.assertEqual(payload["logicFault"]["access"], "read")
        self.assertEqual(payload["logicFault"]["lines"], ["A1", "A2"])
        self.assertEqual(payload["cpuFlags"], 3)

    def test_read_only_experiment_comparison_uses_unknown_and_inert_text(self):
        first={"schemaVersion":1,"corePin":"d"*40,"build":{"applicationVersion":"0.5.1","sourceCommit":"a"*40},
               "modelVersion":"0.5.1-experimental","rom":{"name":"<img src=x onerror=alert(1)>","sha256":"b"*64},
               "vramFault":{"kind":"none","addressMask":0,"bridge":None},"logic":{"fault":None,"active":False,"readCount":0,"writeCount":0},
               "currentFrame":10,"cpuFlags":0,"psgInputFault":{"available":False},"fmInputFault":{"available":False}}
        second=json.loads(json.dumps(first));second["rom"]["sha256"]="c"*64
        before=self.page.locator("#powerLabel").inner_text()
        self.page.evaluate("""() => {
          const nativeText=File.prototype.text;
          File.prototype.text=function(){return this.name==='slow.json'
            ?new Promise(resolve=>window.__finishCompareRead=()=>resolve('{"rom":{"name":"stale"}}'))
            :this.name==='stale.json'
              ?new Promise(resolve=>window.__finishStaleRead=()=>resolve('{"rom":{"name":"stale replacement"}}'))
              :nativeText.call(this);};
        }""")
        self.page.locator("#compareFileA").set_input_files({"name":"slow.json","mimeType":"application/json","buffer":b'{"rom":{"name":"slow"}}'})
        expect(self.page.locator("#compareStatus")).to_contain_text("Reading export A")
        self.page.locator("#compareCancel").click()
        self.page.evaluate("window.__finishCompareRead()")
        expect(self.page.locator("#compareOutput table")).to_have_count(0)
        self.page.locator("#compareFileA").set_input_files({"name":"a.json","mimeType":"application/json","buffer":json.dumps(first).encode()})
        self.page.locator("#compareFileB").set_input_files({"name":"b.json","mimeType":"application/json","buffer":json.dumps(second).encode()})
        expect(self.page.locator("#compareOutput")).to_contain_text("mismatch")
        expect(self.page.locator("#compareOutput")).to_contain_text("unknown")
        self.assertEqual(self.page.locator("#compareOutput img").count(),0)
        self.assertEqual(self.page.locator("#powerLabel").inner_text(),before)
        self.page.locator("#compareFileA").set_input_files({"name":"stale.json","mimeType":"application/json","buffer":b'{"rom":{"name":"slow"}}'})
        self.page.locator("#compareFileA").set_input_files({"name":"fresh.json","mimeType":"application/json","buffer":json.dumps(first).encode()})
        expect(self.page.locator("#compareOutput")).to_contain_text("img src=x")
        self.page.evaluate("window.__finishStaleRead()")
        expect(self.page.locator("#compareOutput")).to_contain_text("img src=x")
        self.page.locator("#compareCancel").click()
        expect(self.page.locator("#compareOutput table")).to_have_count(0)

    def test_actual_experiment_export_roundtrips_without_mutators_or_mobile_overflow(self):
        self.load_rom()
        self.page.locator("#ramLegAction").select_option("cut")
        self.page.locator("#ramChip [data-chip-line]").nth(0).click()
        with self.page.expect_download() as mask_download:
            self.page.locator("#logicExperimentBtn").click()
        mask_payload=json.loads(Path(mask_download.value.path()).read_text())
        self.assertEqual(mask_payload["schemaVersion"],1)
        self.assertTrue(mask_payload["logic"]["available"])
        self.assertEqual(mask_payload["logic"]["fault"]["kind"],"address-stuck-low")
        self.assertEqual(mask_payload["logic"]["fault"]["lines"],["A1"])
        self.page.locator("#logicDisconnectBtn").click()
        self.page.locator("#logicKind").select_option("2")
        self.page.locator("#logicLineA").select_option("0")
        self.page.locator("#logicLineB").select_option("7")
        self.page.locator("#logicApplyBtn").click()
        with self.page.expect_download() as pair_download:
            self.page.locator("#logicExperimentBtn").click()
        pair_payload=json.loads(Path(pair_download.value.path()).read_text())
        self.assertEqual(pair_payload["logic"]["fault"]["kind"],"data")
        self.assertEqual(pair_payload["logic"]["fault"]["lines"],["D0","D7"])
        snapshot=self.page.evaluate("""() => JSON.stringify({
          logic:mockCore.logic.setterCalls, vram:mockCore.vramModel.calls,
          psg:mockCore.psg.calls, psgMask:mockCore.psg.maskCalls,
          fm:mockCore.fm.calls, fmMask:mockCore.fm.maskCalls
        })""")
        self.page.locator("#compareFileA").set_input_files({"name":"export-a.json","mimeType":"application/json","buffer":json.dumps(mask_payload).encode()})
        self.page.locator("#compareFileB").set_input_files({"name":"export-b.json","mimeType":"application/json","buffer":json.dumps(pair_payload).encode()})
        expect(self.page.locator("#compareOutput table")).to_be_visible()
        expect(self.page.locator("#compareOutput")).to_contain_text("ROM SHA-256")
        expect(self.page.locator("#compareOutput")).to_contain_text("RAM Recorded Kind")
        expect(self.page.locator("#compareOutput")).to_contain_text("mismatch")
        self.assertLessEqual(self.page.locator("#compareOutput").evaluate("el=>el.clientHeight"),460)
        self.assertGreater(self.page.locator("#compareOutput table").evaluate("el=>el.scrollWidth"),
                           self.page.locator("#compareOutput").evaluate("el=>el.clientWidth"))
        self.assertEqual(self.page.evaluate("""() => JSON.stringify({
          logic:mockCore.logic.setterCalls, vram:mockCore.vramModel.calls,
          psg:mockCore.psg.calls, psgMask:mockCore.psg.maskCalls,
          fm:mockCore.fm.calls, fmMask:mockCore.fm.maskCalls
        })"""),snapshot)
        self.page.set_viewport_size({"width":390,"height":844})
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"),390)
        self.assertLessEqual(self.page.locator("#compareOutput").evaluate("el=>el.clientWidth"),390)

    def test_comparison_results_focus_keeps_keyboard_scroll_and_blocks_game_hotkeys(self):
        self.load_rom()
        export={"schemaVersion":1,"rom":{"name":"keyboard test","sha256":"a"*64},
                "faultDisconnects":[{"action":"disconnect","results":[]} for _ in range(50)]}
        encoded=json.dumps(export).encode()
        self.page.locator("#compareFileA").set_input_files({"name":"keyboard-a.json","mimeType":"application/json","buffer":encoded})
        self.page.locator("#compareFileB").set_input_files({"name":"keyboard-b.json","mimeType":"application/json","buffer":encoded})
        output=self.page.locator("#compareOutput")
        expect(output.locator("table")).to_be_visible()
        output.focus()
        before_scroll=output.evaluate("el=>el.scrollTop")
        before_state=self.page.evaluate("""() => JSON.stringify({
          pause:document.querySelector('#pauseBtn').textContent,
          starts:mockCore.starts, logic:mockCore.logic.setterCalls,
          vram:mockCore.vramModel.calls, masks:mockCore.vramMaskCalls,
          psg:mockCore.psg.calls, fm:mockCore.fm.calls, input:mockCore.inputs
        })""")
        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_function("before=>document.querySelector('#compareOutput').scrollTop>before",arg=before_scroll)
        self.page.keyboard.press("1")
        self.page.keyboard.press("P")
        after_state=self.page.evaluate("""() => JSON.stringify({
          pause:document.querySelector('#pauseBtn').textContent,
          starts:mockCore.starts, logic:mockCore.logic.setterCalls,
          vram:mockCore.vramModel.calls, masks:mockCore.vramMaskCalls,
          psg:mockCore.psg.calls, fm:mockCore.fm.calls, input:mockCore.inputs
        })""")
        self.assertEqual(after_state,before_state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--executable", help="Optional local browser executable")
    parser.add_argument("--artifacts", type=Path, help="Screenshot directory outside the source tree")
    OPTIONS, remaining = parser.parse_known_args()
    unittest.main(argv=[__file__, *remaining], verbosity=2,
                  testRunner=unittest.TextTestRunner(verbosity=2, resultclass=AnnotatedBrowserResult))
