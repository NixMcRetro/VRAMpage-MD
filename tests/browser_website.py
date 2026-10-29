"""Exercise the thin static artifact and its real source/licence links."""
import argparse
import hashlib
import io
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
import zipfile

from playwright.sync_api import expect, sync_playwright
from browser_core import original_cartridge
from browser_cartridge import choose_cartridge

OPTIONS = None


class WebsiteBundleBrowserTests(unittest.TestCase):
    def test_static_runtime_selector_local_files_and_source_links(self):
        root = OPTIONS.site_root.resolve()
        manifest = json.loads((root / 'cartridges.json').read_text())
        build = json.loads((root / 'build-info.json').read_text())
        with ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=root.parent)) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as playwright:
                    kwargs = {'executable_path': OPTIONS.executable} if OPTIONS.executable else {}
                    browser = getattr(playwright, OPTIONS.browser).launch(**kwargs)
                    try:
                        page = browser.new_page(accept_downloads=True)
                        errors, requests = [], []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.on('request', lambda request: requests.append((request.url, request.method)))
                        origin = f'http://127.0.0.1:{server.server_port}/'
                        page.context.route('**/*', lambda route: route.continue_()
                                           if route.request.url.startswith(origin) else route.abort())
                        core_js = (root / 'core/genplus.js').read_text() + '''
const coreFactory=window.Module;
window.Module=opts=>coreFactory(opts).then(core=>{window.testCore=core;return core;});
'''
                        page.route('**/core/genplus.js', lambda route: route.fulfill(
                            content_type='application/javascript', body=core_js))
                        page.goto(origin + root.name + '/')
                        default = next(c for c in manifest['cartridges'] if c['id'] == manifest['defaultCartridge'])
                        expect(page.locator('#romName')).to_have_text(default['displayName'].upper())
                        for cartridge in manifest['cartridges']:
                            choose_cartridge(page,cartridge['id'])
                            expect(page.locator('#romName')).to_have_text(cartridge['displayName'].upper())
                            page.wait_for_function('testCore._get_logic_frame()>12')
                        page.locator('#regionSelect').select_option('2')
                        page.locator('#resetBtn').click()
                        page.wait_for_function('testCore._get_region_state().pal && testCore._get_logic_frame()>12')
                        page.locator('#romFile').set_input_files({
                            'name': 'private-original.bin', 'mimeType': 'application/octet-stream',
                            'buffer': original_cartridge()})
                        expect(page.locator('#romName')).to_have_text('PRIVATE-ORIGINAL.BIN')
                        page.locator('#logicExperiment').evaluate('node=>node.open=true')
                        with page.expect_download() as download:
                            page.locator('#logicExperimentBtn').click()
                        exported = json.loads(Path(download.value.path()).read_text())
                        self.assertEqual(exported['build']['status'], 'available')
                        self.assertEqual(exported['build']['applicationVersion'], build['application_version'])
                        self.assertEqual(exported['build']['sourceCommit'], build['source_commit'])
                        page.set_viewport_size({'width': 390, 'height': 844})
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
                        page.get_by_role('link', name='Source Code & Licences', exact=True).click()
                        expect(page.get_by_role('heading', name='Source Code & Licences', exact=True)).to_be_visible()
                        expect(page.locator('body')).to_contain_text('Karl Stenerud')
                        expect(page.locator('body')).to_contain_text('GNU LESSER GENERAL PUBLIC LICENSE')
                        expect(page.locator('body')).to_contain_text('Rich Felker')
                        expect(page.locator('body')).to_contain_text('LLVM Exceptions')
                        expect(page.locator('body')).to_contain_text('Sun Microsystems')
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
                        source_link = page.locator('a[href^="source/"][href$="-corresponding-source.zip"]')
                        expect(page.get_by_role('link', name='GitHub Release Source Mirror', exact=True)).to_have_attribute(
                            'href', f'https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v{build["application_version"]}/VRAMpage-MD-v{build["application_version"]}-corresponding-source.zip')
                        response = page.request.get(source_link.evaluate('node=>node.href'))
                        self.assertEqual(response.status, 200)
                        data = response.body()
                        self.assertEqual(hashlib.sha256(data).hexdigest(), build['source_archive']['sha256'])
                        with zipfile.ZipFile(io.BytesIO(data)) as sources:
                            info = json.loads(sources.read('SOURCE-INFO.json'))
                            self.assertEqual(info['source_commit'], build['source_commit'])
                            for name, digest in info['core_sha256'].items():
                                self.assertEqual(hashlib.sha256(sources.read('runtime/core/' + name)).hexdigest(), digest)
                                self.assertEqual(hashlib.sha256((root / 'core' / name).read_bytes()).hexdigest(), digest)
                        self.assertTrue(all(url.startswith(origin) and method == 'GET' for url, method in requests))
                        self.assertEqual(errors, [])
                    finally:
                        browser.close()
            finally:
                server.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--executable')
    parser.add_argument('--site-root', type=Path, required=True)
    OPTIONS, remaining = parser.parse_known_args()
    unittest.main(argv=[__file__, *remaining], verbosity=2)
