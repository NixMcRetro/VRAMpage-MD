"""Fail-closed checks for manifest builds, full bundles and static staging."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cartridges import (CartridgeError, STATIC_FILES, approved_assets, build_cartridges, load_manifest,
                        source_paths, stage_site, validate_manifest, verify_site)


class CartridgeManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_cartridges(ROOT)
        cls.manifest = load_manifest(ROOT)

    def fixture(self, root):
        for relative in approved_assets(self.manifest).keys() | source_paths(self.manifest):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)
        (root / 'site/app.js').write_text('// deliberately no cartridge-name marker')
        for relative in STATIC_FILES:
            target=root/'site'/relative
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b'\0asmfixture' if relative.endswith('.wasm') else b'static fixture')

    def test_both_outputs_reproduce_published_identities_and_region_headers(self):
        for entry in self.manifest['cartridges']:
            with self.subTest(cartridge=entry['id']):
                data = (ROOT / 'site' / entry['path']).read_bytes()
                self.assertEqual(len(data), entry['size'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
                self.assertEqual(list(data[0x1f0:0x200].decode('ascii').strip(' \0')), entry['regions'])
        original = ROOT / 'demo-cart/colour-test/build_colour_test.py'
        # Historical source is retained verbatim; its own standalone output is
        # checked by the same manifest pin as the hosted cartridge.
        self.assertIn(b'Original program and graphics created for the VRAMpage MD blog illustration.', original.read_bytes())

    def test_malformed_approval_identity_and_build_metadata_fail(self):
        changes = [
            ('id', 'demo'), ('id', 'local'), ('id', '2027-demo'), ('id', '-demo'),
            ('path', 'demo/sub/cart.bin'), ('size', 511), ('size', 4194305),
            ('approved', False), ('size', True), ('size', 0),
            ('sha256', '0' * 63), ('version', ''), ('displayName', ''),
            ('source', '../build.py'), ('regions', []), ('license', {}),
            ('build', {'method': 'sh', 'output': 'demo-cart/colour-test/test.bin'}),
            ('build', {'method': 'python3', 'output': '../outside.bin'}),
        ]
        for field, value in changes:
            manifest = copy.deepcopy(self.manifest)
            manifest['cartridges'][1][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CartridgeError):
                validate_manifest(manifest)
        for field, value in [('schemaVersion', 2), ('schemaVersion', True),
                             ('defaultCartridge', 'missing'), ('defaultCartridge', {})]:
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CartridgeError):
                validate_manifest(manifest)

    def test_paths_cannot_escape_or_alias_an_approved_name(self):
        for path in ('../game.bin', '/tmp/game.bin', 'demo/../game.bin',
                     'demo//game.bin', './demo/game.bin', 'demo/game.bin?x',
                     'demo\\game.bin', 'https://host/game.bin'):
            manifest = copy.deepcopy(self.manifest)
            manifest['cartridges'][1]['path'] = path
            with self.subTest(path=path), self.assertRaises(CartridgeError):
                validate_manifest(manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest['cartridges'][1]['path'] = manifest['cartridges'][0]['path']
        with self.assertRaises(CartridgeError):
            validate_manifest(manifest)

    def test_missing_manifest_and_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(CartridgeError):
                load_manifest(root)
            (root / 'site').mkdir()
            (root / 'site/cartridges.json').write_text('{"schemaVersion":1,"schemaVersion":1}')
            with self.assertRaisesRegex(CartridgeError, 'Duplicate'):
                load_manifest(root)

    def test_every_required_asset_fails_before_static_destination_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root, destination = Path(directory) / 'source', Path(directory) / 'static'
            self.fixture(root)
            destination.mkdir()
            sentinel = destination / 'app.js'
            sentinel.write_text('keep existing destination')
            for relative in approved_assets(self.manifest):
                target = root / relative
                data = target.read_bytes()
                for mutation in ('missing', 'changed'):
                    with self.subTest(relative=relative, mutation=mutation):
                        if mutation == 'missing':
                            target.unlink()
                        else:
                            target.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
                        with self.assertRaises(CartridgeError):
                            stage_site(destination, root)
                        self.assertEqual(sentinel.read_text(), 'keep existing destination')
                        self.assertEqual(list(destination.iterdir()), [sentinel])
                        target.write_bytes(data)

    def test_static_bundle_requires_complete_nonempty_application_and_wasm(self):
        with tempfile.TemporaryDirectory() as directory:
            root,destination=Path(directory)/'source',Path(directory)/'static'
            self.fixture(root)
            for relative in STATIC_FILES:
                target=root/'site'/relative;original=target.read_bytes()
                for mutation in ('missing','empty'):
                    if target.exists():target.unlink()
                    if mutation=='empty':target.write_bytes(b'')
                    with self.subTest(relative=relative,mutation=mutation),self.assertRaises(CartridgeError):
                        stage_site(destination,root)
                    self.assertFalse(destination.exists())
                target.write_bytes(original)
            (root/'site/core/genplus.wasm').write_bytes(b'invalid wasm')
            with self.assertRaisesRegex(CartridgeError,'WebAssembly'):
                stage_site(destination,root)
            self.assertFalse(destination.exists())

    def test_unknown_roms_and_archives_are_rejected_before_static_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root, destination = Path(directory) / 'source', Path(directory) / 'static'
            self.fixture(root)
            for name, data in [('game.bin', b'unknown'), ('game.GEN', b'unknown'),
                               ('game.iso', b'unknown'), ('game.md', bytes(0x100) + b'SEGA'),
                               ('Sonic.md', b'unknown'), ('extra.zip', b'unknown'),
                               ('.env', b'private'), ('credentials.json', b'private')]:
                target = root / 'site' / name
                target.write_bytes(data)
                with self.subTest(name=name), self.assertRaises(CartridgeError):
                    stage_site(destination, root)
                self.assertFalse(destination.exists())
                target.unlink()
            destination.mkdir()
            (destination / 'old.bin').write_bytes(b'unapproved stale ROM')
            with self.assertRaises(CartridgeError):
                stage_site(destination, root)
            self.assertEqual(list(destination.iterdir()), [destination / 'old.bin'])

    def test_static_site_has_all_cartridges_and_rebuildable_source_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root, destination = Path(directory) / 'source', Path(directory) / 'static'
            self.fixture(root)
            stage_site(destination, root)
            for entry in self.manifest['cartridges']:
                self.assertEqual((destination / entry['path']).read_bytes(),
                                 (ROOT / 'site' / entry['path']).read_bytes())
            snapshot = destination / 'source/cartridges'
            for relative in source_paths(self.manifest):
                self.assertEqual((snapshot / relative).read_bytes(), (ROOT / relative).read_bytes())
            result = subprocess.run([sys.executable, str(snapshot / 'scripts/build-demo-cart.py')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            verify_site(snapshot)
            # A stale or disguised ROM anywhere in a prior snapshot is rejected.
            (snapshot / 'bad.rom').write_bytes(b'unknown')
            with self.assertRaises(CartridgeError):
                stage_site(destination, root)

    def test_unapproved_generator_output_does_not_replace_staged_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            entry = self.manifest['cartridges'][1]
            source = root / entry['source']
            source.write_text("from pathlib import Path\nPath(__file__).with_name('VRAMpage-MD-Colour-Test.bin').write_bytes(b'wrong')\n")
            before = {path: (root / path).read_bytes() for path in approved_assets(self.manifest)}
            with self.assertRaisesRegex(CartridgeError, 'unexpected checksum'):
                build_cartridges(root)
            self.assertEqual(before, {path: (root / path).read_bytes() for path in before})

    def test_source_file_and_parent_symlinks_cannot_disclose_in_root_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root, destination = Path(directory)/'source', Path(directory)/'static'
            self.fixture(root)
            secret=root/'.env';secret.write_text('private fixture')
            entry=self.manifest['cartridges'][1]
            source=root/entry['source'];original=source.read_bytes()
            source.unlink();source.symlink_to(secret)
            with self.assertRaisesRegex(CartridgeError,'Symlinks'):
                stage_site(destination,root)
            self.assertFalse(destination.exists())
            source.unlink();source.write_bytes(original)
            parent=source.parent;renamed=parent.with_name('aliased-source')
            parent.rename(renamed);parent.symlink_to(renamed,target_is_directory=True)
            with self.assertRaisesRegex(CartridgeError,'Symlinks'):
                stage_site(destination,root)
            self.assertFalse(destination.exists())

    def test_symlinks_cannot_supply_or_receive_static_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root, outside = Path(directory) / 'source', Path(directory) / 'outside'
            self.fixture(root)
            outside.mkdir()
            (outside / 'private.txt').write_text('private')
            git_dir=root/'site/.git';git_dir.mkdir()
            (git_dir/'config').write_text('url=https://credential@example.invalid/repo.git')
            with self.assertRaises(CartridgeError):
                stage_site(Path(directory)/'static',root)
            self.assertFalse((Path(directory)/'static').exists())
            shutil.rmtree(git_dir)
            parent=Path(directory)/'linked-parent'
            parent.symlink_to(outside,target_is_directory=True)
            with self.assertRaises(CartridgeError):
                stage_site(parent/'staged',root)
            self.assertFalse((outside/'staged').exists())
            (root / 'site/leak').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(CartridgeError):
                stage_site(Path(directory) / 'static', root)
            (root / 'site/leak').unlink()
            destination = Path(directory) / 'static'
            destination.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(CartridgeError):
                stage_site(destination, root)
            self.assertEqual(list(outside.iterdir()), [outside / 'private.txt'])


if __name__ == '__main__':
    unittest.main()
