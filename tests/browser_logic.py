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

    def new_page(self, legacy_core=False, legacy_recovery=False):
        context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            color_scheme="light",
            accept_downloads=True,
        )
        self.contexts.append(context)
        page = context.new_page()
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        if legacy_recovery:
            page.add_init_script("window.__legacyRecoveryCore = true;")
        if legacy_core:
            page.add_init_script("window.__legacyLogicCore = true;")
        page.route("**/core/genplus.js", lambda route: route.fulfill(
            path=str(ROOT / "tests/fixtures/mock-core.js"),
            content_type="application/javascript"))
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
        expect(self.page.locator("#connectionLabel")).to_have_text("NONE — OPEN CIRCUIT")
        expect(self.page.locator("#logicStatus")).to_have_text(
            "Clean restart: VRAM/work RAM faults cleared; counters reset.")
        self.assertEqual(self.page.evaluate("window.mockCore.short"), [-1, -1])
        self.assertFalse(self.page.evaluate("window.mockCore.logic.active"))
        self.assertEqual(self.page.evaluate("window.mockCore.logic.reads"), 0)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.writes"), 0)
        self.assertEqual(self.page.evaluate("window.mockCore.logic.storedWrites"), 0)
        self.assertEqual(
            self.page.evaluate("window.mockCore.logic.frame"),
            self.page.evaluate("window.mockCore.ticks - window.mockCore.lastStartTick"),
            "clean restart must reset the synthetic frame counter",
        )

    def test_older_logic_core_disables_only_recovery(self):
        page = self.new_page(legacy_recovery=True)
        self.load_rom(page)
        expect(page.locator("#logicApplyBtn")).to_be_enabled()
        expect(page.locator("#logicResumeBtn")).to_be_disabled()
        expect(page.locator("#logicCpuResetBtn")).to_be_disabled()
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

    def test_experiment_export_contains_hash_and_metadata_not_rom_bytes(self):
        rom = self.load_rom()
        self.page.locator("#logicApplyBtn").click()
        self.page.wait_for_function("window.mockCore.logic.reads > 0")
        self.page.evaluate("window.mockCore.logic.cpuFlags = 3")
        with self.page.expect_download() as download_info:
            self.page.locator("#logicExperimentBtn").click()
        download = download_info.value
        payload = json.loads(Path(download.path()).read_text())
        self.assertEqual(payload["modelVersion"], "2.1-experimental")
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
