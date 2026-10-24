"""Actual-core browser tests for VRAM model selection and RAM/VRAM handoff."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from playwright.sync_api import expect, sync_playwright

from browser_core import original_cartridge


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = None


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class TransactionBrowserTests(unittest.TestCase):
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
        launch = {"executable_path": OPTIONS.executable} if OPTIONS.executable else {}
        cls.browser = getattr(cls.playwright, OPTIONS.browser).launch(**launch)
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1366, "height": 768}, accept_downloads=True)
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
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
  const nativeLogic=core._set_logic_fault?.bind(core);
  const nativeAddress=core._set_logic_address_mask?.bind(core);
  if(nativeModel) core._set_vram_fault_model=(...args)=>{
    if(window.__rejectAllVram) return 5;
    if(window.__rejectVramClear && args[1]===0 && args[2]===-1) return 6;
    return nativeModel(...args);
  };
  if(nativeLogic) core._set_logic_fault=(...args)=>{
    if(window.__rejectRamDisconnect && args[0]===0) return 7;
    if(window.__rejectRamApply && args[0]!==0) return 8;
    return nativeLogic(...args);
  };
  if(nativeAddress) core._set_logic_address_mask=(...args)=>{
    if(window.__rejectRamAddressApply && args[0]!==0) return 8;
    return nativeAddress(...args);
  };
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
        self.page.locator("#romFile").set_input_files({
            "name": "original-video-tone.bin",
            "mimeType": "application/octet-stream",
            "buffer": original_cartridge(),
        })
        expect(self.page.locator("#powerLabel")).to_have_text("CONSOLE ON")
        self.page.wait_for_function("testCore._get_logic_frame()>5")

    def test_runtime_model_handoffs_failures_and_export(self):
        self.open_core(ROOT / "site/core")
        page = self.page
        expect(page.locator('#vramModel option[value="2"]')).to_be_enabled()
        page.locator("#vramModel").select_option("2")
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)
        self.assertEqual(page.evaluate("testCore._get_vram_supported_model_mask()"), 7)
        page.locator("#logicExperiment > summary").click()

        # A transaction bridge is cleared before RAM activation; RAM is then active.
        page.locator("#vramMode").select_option("bridge")
        page.locator(".pin").nth(0).click()
        page.locator(".pin").nth(1).click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), 0)
        page.locator("#logicApplyBtn").click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), -1)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)

        # A later VRAM bridge disconnects RAM first.
        page.locator(".pin").nth(0).click()
        page.locator(".pin").nth(1).click()
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), 0)
        expect(page.locator("#logicStatus")).to_contain_text("RAM fault disconnected")

        # If RAM rejects its disconnect, a selector target must be rolled back.
        page.locator("#disconnectBtn").click()
        page.locator("#logicApplyBtn").click()
        page.evaluate("window.__rejectRamDisconnect=true")
        page.locator(".pin").nth(2).click()
        page.locator(".pin").nth(3).click()
        page.evaluate("window.__rejectRamDisconnect=false")
        state = page.evaluate("testCore._get_vram_fault_model_state()")
        self.assertEqual((state["modelId"], state["bridgeA"], state["bridgeB"]), (2, -1, -1))
        expect(page.locator("#vramModelStatus")).to_contain_text("configuration restored")

        # Selector rejection happens before any RAM disconnect or model change.
        page.evaluate("window.__rejectAllVram=true")
        page.locator(".pin").nth(4).click()
        page.locator(".pin").nth(5).click()
        page.evaluate("window.__rejectAllVram=false")
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 2)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().bridgeA"), -1)
        expect(page.locator("#logicStatus")).to_contain_text("RAM fault remains unchanged")

        # A pulse refuses a VRAM takeover and keeps its active budget.
        page.locator("#logicPulseBtn").click()
        expect(page.locator("#logicStatus")).to_contain_text("RAM pulse active")
        page.locator(".pin").nth(6).click()
        page.locator(".pin").nth(7).click()
        expect(page.locator("#logicStatus")).to_contain_text("remaining budget is preserved")

        # Export preserves historical top-level data and adds versioned namespaces.
        with page.expect_download() as download:
            page.locator("#logicExperimentBtn").click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertEqual(data["schemaVersion"], 1)
        self.assertIn("readCount", data)
        self.assertEqual(data["logic"]["modelVersion"], "work-ram-transaction-v1")
        self.assertEqual(data["vramTransaction"]["modelId"], 2)
        self.assertTrue(data["vramModelTransitions"])

        # Cartridge start restores the default model and identity settings.
        page.locator("#romFile").set_input_files({
            "name": "second-original.bin",
            "mimeType": "application/octet-stream",
            "buffer": original_cartridge(),
        })
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().modelId"), 1)
        self.assertEqual(page.evaluate("testCore._get_vram_fault_model_state().mask"), 0)
        self.assertEqual(self.errors, [])

    def test_normal_core_uses_legacy_frame_fallback(self):
        self.open_core(OPTIONS.normal_core)
        page = self.page
        expect(page.locator('#vramModel option[value="2"]')).to_be_disabled()
        expect(page.locator("#transactionMetrics")).to_be_hidden()
        page.locator("#vramMode").select_option("bridge")
        page.locator(".pin").nth(0).click()
        page.locator(".pin").nth(1).click()
        expect(page.locator(".pin.connected")).to_have_count(2)
        page.locator("#disconnectBtn").click()
        expect(page.locator(".pin.connected")).to_have_count(0)
        self.assertEqual(self.errors, [])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium", "firefox", "webkit"), default="chromium")
    parser.add_argument("--executable-path")
    parser.add_argument("--normal-core", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    OPTIONS = parse_args()
    unittest.main(argv=[__file__], verbosity=2)
