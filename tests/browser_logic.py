"""Synthetic browser regressions for the logic/work-RAM UI and metadata export."""
import argparse
import hashlib
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

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

    def new_page(self, legacy_core=False, legacy_recovery=False, legacy_write_pulse=False, legacy_chip=False, legacy_vram_chip=False, build_info=None, stalled_build_info=False, circuit_config=False, legacy_psg_data=False, legacy_fm_data=False, legacy_psg_mask=False, legacy_fm_mask=False):
        context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            color_scheme="light",
            accept_downloads=True,
        )
        self.contexts.append(context)
        page = context.new_page()
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
        expect(page.locator("#powerLabel")).to_have_text("WAITING FOR ROM")
        if legacy_core:
            expect(page.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        else:
            expect(page.locator("#logicStatus")).to_contain_text("Load a ROM")
        details = page.locator("#logicExperiment")
        if not details.evaluate("node => node.open"):
            details.locator(":scope > summary").click()
        return page

    @staticmethod
    def synthetic_rom():
        data = bytearray(512)
        data[0x100:0x104] = b"SEGA"
        return bytes(data)

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
        expect(legacy.locator("#logicResumeBtn")).to_be_disabled()
        expect(legacy.locator("#logicCpuResetBtn")).to_be_disabled()
        expect(legacy.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        self.load_rom(legacy)
        expect(legacy.locator("#powerLabel")).to_have_text("CONSOLE ON")
        expect(legacy.locator("#logicStatus")).to_have_text("Rebuild core for logic faults")
        expect(legacy.locator("#pauseBtn")).to_have_text("Pause")

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
        pins = self.page.locator(".pin")
        pins.nth(0).click()
        pins.nth(1).click()
        expect(self.page.locator("#connectionLabel")).to_have_text("AD0 ↔ AD1")
        expect(self.page.locator("#logicStatus")).to_have_text(
            "VRAM patch active; logic/work RAM fault disconnected.")
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("window.mockCore.short"), [0, 1])

        self.page.locator("#resetBtn").click()
        self.page.wait_for_function("window.mockCore.starts === 2")
        expect(self.page.locator("#connectionLabel")).to_have_text("NONE — NORMAL ADDRESSING")
        expect(self.page.locator("#logicStatus")).to_have_text(
            "Clean restart: VRAM/work RAM faults cleared; counters reset.")
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

    def export_payload(self):
        with self.page.expect_download() as info:
            self.page.locator("#logicExperimentBtn").click()
        return json.loads(Path(info.value.path()).read_text())

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
        self.assertEqual(saved, payload)
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
        self.assertEqual(saved['schemaVersion'],2)
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

    def test_older_pulse_core_keeps_frame_controls(self):
        page = self.new_page(legacy_write_pulse=True)
        self.load_rom(page)
        expect(page.locator("#logicPulseFrames option[value='writes:1']")).to_be_disabled()
        expect(page.locator("#logicPulseBtn")).to_be_enabled()
        page.locator("[data-ram-pulse]").first.click()
        page.wait_for_function("window.mockCore.logic.recoveries.length === 1")
        expect(page.locator("#logicStatus")).to_contain_text("Forced resume attempted")

    def test_vram_legs_mouse_keyboard_crosses_and_export(self):
        legs=self.page.locator('.pin')
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
        self.page.keyboard.press('Digit0')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(2).click()
        self.page.locator('#resetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.export_payload()['vramAddressLineChanges'],[])
        self.assertEqual(self.export_payload()['vramFault']['kind'],'none')

    def test_vram_masks_bridges_ram_pulses_and_recovery_replace(self):
        self.load_rom()
        legs=self.page.locator('.pin')
        legs.nth(1).click()
        self.page.locator('#vramMode').select_option('bridge')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),2,'Mode changes alone do not apply a fault')
        legs.nth(0).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),2)
        legs.nth(3).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.short'),[0,3])
        expect(self.page.locator('.pin.cut')).to_have_count(0)
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
        self.page.locator('#logicResumeBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(3).click()
        self.page.locator('#logicCpuResetBtn').click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        legs.nth(2).click()
        self.open_vram_settings()
        self.page.locator('.preset').first.click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        expect(self.page.locator('.pin.connected')).to_have_count(2)
        legs.nth(7).click()
        # Remove focus from the button before global shortcuts.
        self.page.locator('#screen').click()
        self.page.keyboard.down('Shift')
        self.page.keyboard.down('Digit2')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertEqual(self.page.evaluate('mockCore.short'),[0,2])
        self.page.keyboard.up('Digit2')
        self.page.keyboard.up('Shift')
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)

    def test_vram_mask_rejection_and_failed_ram_disconnect(self):
        self.load_rom()
        self.page.locator('.pin').first.click()
        self.page.evaluate('mockCore.rejectVramMask=true')
        self.page.locator('.pin').nth(1).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),1)
        expect(self.page.locator('.pin').nth(1)).to_have_attribute('aria-pressed','false')
        self.page.evaluate('mockCore.rejectVramMask=false')
        self.page.locator('#logicApplyBtn').click()
        self.page.locator('#pauseBtn').click()
        self.page.locator('#logicPulseFrames').select_option('8')
        self.page.locator('#logicPulseBtn').click()
        self.page.evaluate('mockCore.rejectLogicClear=true')
        self.page.locator('.pin').nth(3).click()
        self.assertEqual(self.page.evaluate('mockCore.vramAddressMask'),0)
        self.assertTrue(self.page.evaluate('mockCore.logic.active'))
        expect(self.page.locator('.pin.cut')).to_have_count(0)
        self.assertEqual(self.export_payload()['faultPulses'][-1]['status'],'active',
                         'Failed takeover must preserve the armed pulse timer')
        self.page.locator('#logicResumeBtn').click()
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
        page.locator('.pin').nth(0).click()
        page.locator('.pin').nth(1).click()
        expect(page.locator('.pin.connected')).to_have_count(2)
        expect(page.locator('.pin .chip-cut').first).to_have_css('visibility','hidden')
        self.open_vram_settings(page)
        page.locator('#disconnectBtn').click()
        expect(page.locator('.pin.connected')).to_have_count(0)

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
        self.page.locator('.pin').nth(0).click()
        self.page.locator('.pin').nth(7).focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.pin.connected')).to_have_count(2)
        self.open_vram_settings()
        self.page.locator('#disconnectBtn').click()
        expect(self.page.locator('.pin.connected')).to_have_count(0)

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
        self.page.locator("#logicResumeBtn").click()
        self.assertEqual(self.page.evaluate("window.mockCore.logic.addressMask"), 0)
        self.page.locator("[data-chip-line]").nth(3).click()
        light=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.page.emulate_media(color_scheme="dark")
        dark=self.page.locator(".ram-chip-body").evaluate("e=>getComputedStyle(e).backgroundColor")
        self.assertNotEqual(light,dark)
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
        expect(page.locator("#logicResumeBtn")).to_be_disabled()
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
        self.page.locator("#logicResumeBtn").focus()
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

    def assert_build_export(self, expected):
        rom=self.load_rom()
        self.page.locator('#logicApplyBtn').click()
        payload=self.export_payload()
        self.assertEqual(payload['schemaVersion'],1)
        self.assertEqual(payload['build'],expected)
        self.assertEqual(payload['modelVersion'],'0.4.1-experimental')
        self.assertEqual(payload['rom']['sha256'],hashlib.sha256(rom).hexdigest())
        self.assertEqual(payload['logicFault']['kind'],'address')
        self.assertTrue(payload['faultActive'])
        self.assertNotIn('romBytes',payload)
        return payload

    @staticmethod
    def valid_build_info():
        return {'application':'VRAMpage MD','application_version':'0.4.1',
                'source_commit':'a'*40,'package_format':1}

    def test_export_provenance_valid_and_filters_unknown_fields(self):
        info=self.valid_build_info()
        info.update({'token':'must-not-be-exported','private':{'secret':'ignore'}})
        self.page=self.new_page(build_info=info)
        payload=self.assert_build_export({'status':'available','applicationVersion':'0.4.1','sourceCommit':'a'*40})
        self.assertNotIn('must-not-be-exported',json.dumps(payload))
        self.assertNotIn('private',payload['build'])
        self.page.locator('#resetBtn').click()
        self.assertEqual(self.export_payload()['build']['sourceCommit'],'a'*40)

    def test_export_provenance_missing(self):
        self.assert_build_export({'status':'unavailable','applicationVersion':'0.4.1','sourceCommit':None})

    def test_export_provenance_malformed(self):
        for malformed in ('{broken', 'null', [], self.valid_build_info() | {'source_commit':'A'*40},
                          self.valid_build_info() | {'source_commit':'a'*39},
                          self.valid_build_info() | {'package_format':'1'}):
            with self.subTest(metadata=malformed):
                self.page=self.new_page(build_info=malformed)
                self.assert_build_export({'status':'unavailable','applicationVersion':'0.4.1','sourceCommit':None})

    def test_export_provenance_mismatched_application_or_version(self):
        for mismatch in ({'application':'Other app'},{'application_version':'0.2.5'},
                         {'package_format':2}):
            with self.subTest(metadata=mismatch):
                self.page=self.new_page(build_info=self.valid_build_info() | mismatch)
                self.assert_build_export({'status':'unavailable','applicationVersion':'0.4.1','sourceCommit':None})

    def test_export_provenance_timeout_never_blocks_play_or_export(self):
        self.page=self.new_page(stalled_build_info=True)
        self.assert_build_export({'status':'unavailable','applicationVersion':'0.4.1','sourceCommit':None})
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
        self.assertEqual(payload["modelVersion"], "0.4.1-experimental")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--executable", help="Optional local browser executable")
    parser.add_argument("--artifacts", type=Path, help="Screenshot directory outside the source tree")
    OPTIONS, remaining = parser.parse_known_args()
    unittest.main(argv=[__file__, *remaining], verbosity=2)
