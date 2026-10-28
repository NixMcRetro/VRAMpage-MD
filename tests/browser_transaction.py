"""Actual-core browser tests for VRAM model selection and RAM/VRAM handoff."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from playwright.sync_api import expect, sync_playwright

from browser_core import original_cartridge, prefer_manual_startup


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class TransactionBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=OPTIONS.site_root))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        launch = {"executable_path": OPTIONS.executable_path} if OPTIONS.executable_path else {}
        cls.browser = getattr(cls.playwright, OPTIONS.browser).launch(**launch)
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1366, "height": 768}, accept_downloads=True)
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        prefer_manual_startup(self.page)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def open_core(self, core_dir):
        core_dir = Path(core_dir)
        core_js = (core_dir / "genplus.js").read_text()
        core_js += r'''
const originalFactory=window.Module;
window.Module=opts=>originalFactory(opts).then(core=>{
  window.testCore=core;
  const nativeModel=core._set_vram_fault_model?.bind(core);
  const nativeState=core._get_vram_fault_model_state?.bind(core);
  const nativeSupport=core._get_vram_supported_model_mask?.bind(core);
  const nativeLogic=core._set_logic_fault?.bind(core);
  if(nativeModel) core._set_vram_fault_model=(...args)=>{
    if(window.__rejectAllVram) return 5;
    if(window.__rejectVramClear && args[1]===0 && args[2]===-1) return 6;
    if(window.__vramAllowedCalls!==undefined) {
      if(window.__vramAllowedCalls===0) return 9;
      window.__vramAllowedCalls--;
    }
    return nativeModel(...args);
  };
  if(nativeLogic) core._set_logic_fault=(...args)=>{
    if(window.__rejectRamDisconnect && args[0]===0) return 7;
    if(window.__rejectRamApply && args[0]!==0) return 8;
    return nativeLogic(...args);
  };
  if(nativeState) core._get_vram_fault_model_state=()=>{
    const state=nativeState();
    return window.__forceUnsupported
      ? {...state,supportedModelsMask:3,reason:state.modelId===2?'unsupported-mode':state.reason}
      : state;
  };
  if(nativeSupport) core._get_vram_supported_model_mask=()=>window.__forceUnsupported?3:nativeSupport();
  if(window.__hideRuntimeApi) {
    for(const name of ['_set_vram_fault_model','_get_vram_fault_model_state','_get_vram_supported_model_mask'])
      core[name]=undefined;
  }
  return core;
});
'''
        self.page.route("**/core/genplus.js", lambda route: route.fulfill(
            content_type="application/javascript", body=core_js))
        self.page.route("**/core/genplus.wasm", lambda route: route.fulfill(
            content_type="application/wasm", path=str(core_dir / "genplus.wasm")))
        self.page.goto(f"http://127.0.0.1:{self.server.server_port}/")
        self.page.wait_for_function("!!window.testCore")
        # Handoff failures are checked without an automatic intervention changing the fixture.
        self.page.locator('#logicResumeBtn').click()
        self.page.locator('#armCpuRecoveryBtn').click()
        self.page.locator("#romFile").set_input_files({
            "name": "original-video-tone.bin",
            "mimeType": "application/octet-stream",
            "buffer": original_cartridge(),
        })
        expect(self.page.locator("#romName")).to_have_text("ORIGINAL-VIDEO-TONE.BIN")
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        self.page.wait_for_function("testCore._get_logic_frame()>5")

    def test_runtime_model_handoffs_failures_and_export(self):
        self.open_core(OPTIONS.site_root / "core")
        page = self.page
        expect(page.locator('#vramModel option[value="2"]')).to_be_enabled()
        page.locator("#vramModel").select_option("2")
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)
        self.assertEqual(page.evaluate("testCore._get_vram_supported_model_mask()"), 7)
        page.evaluate("window.__forceUnsupported=true")
        expect(page.locator("#vramModelStatus")).to_contain_text("suspended outside supported VDP Mode 5")
        page.locator("#vramSettings").evaluate("details=>{details.open=true}")
        page.locator("#disconnectBtn").click()
        unsupported_disconnect=page.evaluate("testCore._get_vram_fault_model_state()")
        self.assertEqual((unsupported_disconnect["modelId"],unsupported_disconnect["mask"],
                          unsupported_disconnect["bridgeA"]),(1,0,-1))
        page.evaluate("window.__forceUnsupported=false")
        page.locator("#vramModel").select_option("2")
        page.locator("#logicExperiment > summary").click()

        # A transaction bridge is cleared before RAM activation; RAM is then active.
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), 0)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeB"), 1)
        page.evaluate("window.__rejectRamApply=true")
        page.locator("#logicApplyBtn").click()
        page.evaluate("window.__rejectRamApply=false")
        rejected = page.evaluate("testCore._get_vram_fault_model_state()")
        self.assertEqual((rejected["modelId"], rejected["bridgeA"], rejected["bridgeB"]), (2, 0, 1))
        expect(page.locator("#logicStatus")).to_contain_text("previous VRAM configuration restored")

        # A successful RAM activation clears the bridge after validation.
        page.locator("#logicApplyBtn").click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), -1)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)

        # A later VRAM bridge disconnects RAM first.
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), 0)
        expect(page.locator("#logicStatus")).to_contain_text("RAM fault disconnected")

        # If RAM rejects its disconnect, a selector target must be rolled back.
        page.locator("#vramSettings").evaluate("details=>{details.open=true}")
        page.locator("#disconnectBtn").click()
        page.locator("#logicApplyBtn").click()
        page.evaluate("window.__rejectRamDisconnect=true")
        page.locator("#pinGrid .pin").nth(2).click()
        page.locator("#pinGrid .pin").nth(3).click()
        page.evaluate("window.__rejectRamDisconnect=false")
        state = page.evaluate("testCore._get_vram_fault_model_state()")
        self.assertEqual((state["modelId"], state["bridgeA"], state["bridgeB"]), (2, -1, -1))
        expect(page.locator("#vramModelStatus")).to_contain_text("VRAM settings were restored")

        # Selector rejection happens before any RAM disconnect or model change.
        page.evaluate("window.__rejectAllVram=true")
        page.locator("#pinGrid .pin").nth(4).click()
        page.locator("#pinGrid .pin").nth(5).click()
        page.evaluate("window.__rejectAllVram=false")
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), -1)
        expect(page.locator("#vramModelStatus")).to_contain_text("RAM settings were not changed")

        # A pulse refuses a VRAM takeover and keeps its active budget.
        page.locator("#pauseBtn").click()
        page.locator("#logicPulseBtn").click()
        expect(page.locator("#logicStatus")).to_contain_text("RAM pulse active")
        page.locator("#pinGrid .pin").nth(6).click()
        page.locator("#pinGrid .pin").nth(7).click()
        expect(page.locator("#logicStatus")).to_contain_text("remaining budget is preserved")

        # Export preserves historical top-level data and adds versioned namespaces.
        with page.expect_download() as download:
            page.locator("#logicExperimentBtn").click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["modelVersion"], "0.5.0-experimental")
        self.assertIn("readCount", data)
        self.assertIn("vramFault", data)
        self.assertIn("vramAddressLineChanges", data)
        self.assertEqual(data["logic"]["modelVersion"], "work-ram-transaction-v3")
        self.assertEqual(data["logic"]["schemaVersion"], 3)
        self.assertTrue(data["logic"]["dataMaskAvailable"])
        self.assertEqual(data["logic"]["dataMask"], 0)
        self.assertEqual(data["vramTransaction"]["modelId"], 2)
        self.assertTrue(data["vramModelTransitions"])
        self.assertTrue(any(change["result"]=="ram-fault-rejected"
                            for change in data["vramModelTransitions"]))
        counts=data["vramTransaction"]["lastFrameCounts"]
        self.assertEqual(set(counts),{"logicalByteReads","logicalByteWrites",
                                      "redirectedByteReads","redirectedByteWrites",
                                      "changedPhysicalByteWrites"})
        self.assertTrue(all(isinstance(value,int) and value>=0 for value in counts.values()))

        # Cartridge start restores the default model and identity settings.
        page.locator("#romFile").set_input_files({
            "name": "second-original.bin",
            "mimeType": "application/octet-stream",
            "buffer": original_cartridge(),
        })
        expect(page.locator("#romName")).to_have_text("SECOND-ORIGINAL.BIN")
        page.wait_for_function("testCore._get_vram_fault_model_state().modelId===1")
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 1)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().mask"), 0)
        self.assertEqual(self.errors, [])

    def test_normal_core_uses_legacy_frame_fallback(self):
        self.open_core(OPTIONS.normal_core)
        page = self.page
        self.assertTrue(page.locator('#vramModel option[value="2"]').evaluate("option=>option.disabled"))
        expect(page.locator("#transactionMetrics")).to_be_hidden()
        page.locator("#pinGrid .pin").nth(0).click()
        page.wait_for_function("testCore._get_vram_address_mask()===1")
        expect(page.locator("#pinGrid .pin").nth(0).locator(".chip-cut")).to_have_css("visibility", "visible")
        with page.expect_download() as download:
            page.locator("#logicExperiment > summary").click()
            page.locator("#logicExperimentBtn").click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertEqual(data["vramFault"]["addressMask"], 1)
        self.assertEqual(data["vramAddressLineChanges"][-1]["mask"], 1)
        page.locator("#logicExperiment > summary").click()
        page.locator("#vramSettings").evaluate("details=>{details.open=true}")
        page.locator("#disconnectBtn").click()
        page.wait_for_function("testCore._get_vram_address_mask()===0")
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        expect(page.locator("#pinGrid .pin.connected")).to_have_count(2)
        page.locator("#vramSettings").evaluate("details=>{details.open=true}")
        page.locator("#disconnectBtn").click()
        expect(page.locator("#pinGrid .pin.connected")).to_have_count(0)
        self.assertEqual(self.errors, [])

    def test_failed_rollback_pauses_and_recovery_exports_partial_cleanup(self):
        self.open_core(OPTIONS.site_root / "core")
        page = self.page
        page.locator("#vramModel").select_option("2")
        page.locator("#logicExperiment > summary").click()
        page.locator("#logicApplyBtn").click()
        page.evaluate("window.__rejectRamDisconnect=true; window.__vramAllowedCalls=1")
        page.locator("#vramMode").select_option("bridge")
        page.locator("#pinGrid .pin").nth(0).click()
        page.locator("#pinGrid .pin").nth(1).click()
        page.evaluate("window.__rejectRamDisconnect=false")
        expect(page.locator("#pauseBtn")).to_have_text("Resume")
        expect(page.locator("#vramModelStatus")).to_contain_text("Both fault states are retained")
        state = page.evaluate("testCore._get_vram_fault_model_state()")
        self.assertEqual((state["modelId"], state["bridgeA"], state["bridgeB"]), (2, 0, 1))
        frozen = page.evaluate("testCore._get_logic_frame()")
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate("testCore._get_logic_frame()"), frozen,
                         "emulation must pause before another tick after dual-active rollback failure")
        with page.expect_download() as download:
            page.locator("#logicExperimentBtn").click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertTrue(data["logic"]["active"])
        self.assertEqual(data["vramTransaction"]["bridgeA"], 0)
        self.assertTrue(any(change.get("result")=="ram-disconnect-rejected" and
                             change.get("ramFaultStillActive") is True
                             for change in data["vramModelTransitions"]))

        # Force an already-active VRAM state to test recovery's partial-cleanup path.
        # Normal UI handoff prevents this dual-active configuration.
        page.evaluate("window.__vramAllowedCalls=undefined")
        page.locator("#resetBtn").click()
        page.wait_for_function("testCore._get_logic_frame()>5")
        page.locator("#vramModel").select_option("2")
        page.locator("#logicApplyBtn").click()
        page.evaluate("testCore._set_vram_fault_model(2,0,0,1)")
        page.evaluate("window.__rejectVramClear=true")
        page.locator("#manualForceResumeBtn").click()
        page.evaluate("window.__rejectVramClear=false")
        expect(page.locator("#logicStatus")).to_contain_text("RAM fault is disconnected")
        expect(page.locator("#logicStatus")).to_contain_text("no CPU intervention was issued")
        with page.expect_download() as download:
            page.locator("#logicExperimentBtn").click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertFalse(data["logic"]["active"])
        self.assertEqual(data["vramTransaction"]["bridgeA"], 0)
        self.assertTrue(any(item.get("action")=="recovery-aborted" and
                            item.get("ramFaultDisconnected") is True and
                            item.get("vramFaultDisconnected") is False
                            for item in data["cpuInterventions"]))
        self.assertEqual(self.errors, [])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium", "firefox", "webkit"), default="chromium")
    parser.add_argument("--executable-path")
    parser.add_argument("--normal-core", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, default=ROOT / "site",
                        help="site tree to serve (defaults to the checked-out site)")
    return parser.parse_args()


if __name__ == "__main__":
    OPTIONS = parse_args()
    OPTIONS.site_root = OPTIONS.site_root.resolve()
    unittest.main(argv=[__file__], verbosity=2)
