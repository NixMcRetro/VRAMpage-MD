import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from website_bundle import BundleError, build, verify_source_archive, verify_website  # noqa: E402
from cartridges import CartridgeError  # noqa: E402


PIN = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"


def _put(root, relative, data):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    return path


def _fixture(tmp_path, *, licence=True, symlink=False, missing_source=False):
    root = tmp_path / "source"
    root.mkdir()
    _put(root, "VERSION", "0.5.1\n")
    for relative in (
        "README.md", "START.command", "docs/RUNNING-LOCALLY.md",
        "scripts/cartridges.py", "scripts/build-demo-cart.py", "scripts/build-core.sh",
        "scripts/build-core-runtime.py", "scripts/install-runtime-site.py",
        "scripts/patch_core.py", "scripts/session_checkpoint_patch.py", "scripts/serve.py",
        "scripts/package-website.py", "scripts/website_bundle.py",
        "site/style.css", "site/app.js", "site/cartridges.js", "site/framebuffer.js",
        "site/rgb-encoder.js", "site/circuit-config.js", "site/experiment-comparison.js",
    ):
        _put(root, relative, f"source:{relative}\n")
    _put(root, "docs/LICENCE-AUDIT-v0.5.1.md", "Licence audit.\n")
    _put(root, "THIRD-PARTY-NOTICES.md", "Project notices.\n")
    _put(root, "licences/EMSCRIPTEN-LICENSE.txt", "Emscripten dual MIT and NCSA.\n")
    _put(root, "site/index.html", "<!doctype html><body><footer>VRAMpage</footer></body>\n")
    _put(root, "site/core/genplus.js", b"// wasm glue fixture\n")
    _put(root, "site/core/genplus.wasm", b"\0asm\x01\0\0\0")
    cart = bytearray(512)
    cart[0x100:0x104] = b"SEGA"
    cart_sha = hashlib.sha256(cart).hexdigest()
    _put(root, "site/demo/cart.bin", bytes(cart))
    legacy = bytearray(512)
    legacy[0x100:0x104] = b"SEGA"
    _put(root, "site/demo/legacy-v0.1.bin", bytes(legacy))
    _put(root, "demo-cart/cart/build.py", "print('build')\n")
    _put(root, "demo-cart/CARTRIDGE-NOTICES.md", "Original homebrew notice.\n")
    legacy_kit = b"legacy source kit\n"
    _put(root, "demo-cart/legacy-source.zip", legacy_kit)
    _put(root, "demo-cart/legacy-notice.txt", "legacy attribution\n")
    manifest = {
        "schemaVersion": 1, "defaultCartridge": "demo",
        "cartridges": [{
            "id": "demo", "version": "0.1", "displayName": "Demo Cart",
            "approved": True, "path": "demo/cart.bin", "source": "demo-cart/cart/build.py",
            "build": {"method": "python3", "output": "demo-cart/cart/out.bin"},
            "size": len(cart), "sha256": cart_sha, "regions": ["U"],
            "license": {"type": "original", "attribution": "author",
                         "redistribution": "allowed", "notice": "demo-cart/CARTRIDGE-NOTICES.md"},
        }],
        "preservedAssets": [
            {"path": "site/demo/legacy-v0.1.bin", "size": len(legacy),
             "sha256": hashlib.sha256(legacy).hexdigest()},
            {"path": "demo-cart/legacy-source.zip", "size": len(legacy_kit),
             "sha256": hashlib.sha256(legacy_kit).hexdigest()},
        ],
    }
    _put(root, "site/cartridges.json", json.dumps(manifest))
    js_hash = hashlib.sha256((root / "site/core/genplus.js").read_bytes()).hexdigest()
    wasm_hash = hashlib.sha256((root / "site/core/genplus.wasm").read_bytes()).hexdigest()
    _put(root, "site/source/runtime-profile/.vrampage-site-runtime-profile",
         f"VRAMpage site runtime profile v1\n{PIN}\n")
    _put(root, "site/source/runtime-profile/BUILDING.txt",
         f"Pinned wasm-genplus source: {PIN}\ngenplus.js SHA-256: {js_hash}\n"
         f"genplus.wasm SHA-256: {wasm_hash}\n")
    _put(root, "site/source/runtime-profile/THIRD-PARTY-NOTICES.md", "Core notices.\n")
    source = "site/source/runtime-profile/source"
    _put(root, f"{source}/THIRD-PARTY-NOTICES.md", "Source notices.\n")
    _put(root, f"{source}/wasm-genplus/README.md", "wrapper build instructions\n")
    _put(root, f"{source}/wasm-genplus/CMakeLists.txt",
         "add_source_files(\n  ./src/main/c/core/genesis.c\n"
         "  ./src/main/c/core/sound/ym2612.c\n)\n"
         "add_compile_flags(LD \"--pre-js=${CMAKE_SOURCE_DIR}/../scripts/runtime.js\")\n")
    _put(root, f"{source}/wasm-genplus/cmake/macros.cmake", "macro(add_source_files)\nendmacro()\n")
    for relative in (
        "src/main/c/core/genesis.c", "src/main/c/core/sound/ym3438.c",
        "src/main/c/core/sound/ym2612.c", "src/main/c/core/sound/ym2413.c",
        "src/main/c/core/sound/eq.c",
        "src/main/c/core/m68k/m68k.h", "src/main/c/core/z80/z80.c",
        "src/main/c/core/sound/blip_buf.c",
        "src/main/c/wasm/scrc32.c",
    ):
        if missing_source and relative.endswith("sound/ym2612.c"):
            continue
        _put(root, f"{source}/wasm-genplus/{relative}", f"source {relative}\n")
    if licence:
        _put(root, f"{source}/wasm-genplus/src/main/c/core/ntsc/license.txt",
             "GNU LESSER GENERAL PUBLIC LICENSE Version 2.1\n")
    _put(root, f"{source}/scripts/patch_core.py", "# patcher\n")
    _put(root, f"{source}/scripts/session_checkpoint_patch.py", "# patcher\n")
    _put(root, f"{source}/scripts/runtime.js", "// runtime shim\n")
    if symlink:
        (root / source / "scripts" / "bad.py").symlink_to(root / "scripts" / "patch_core.py")
    source_root = root / source
    inventory = {p.relative_to(source_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in source_root.rglob("*") if p.is_file()}
    _put(root, source + "/SOURCE-FILES.json", json.dumps(inventory))
    _put(root, ".gitignore", "/site/source/\n/site/core/\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    return root


def _refresh_bundle_checksums(dest):
    info_path = dest / "build-info.json"
    info = json.loads(info_path.read_text())
    archive_path = dest / info["source_archive"]["path"]
    data = archive_path.read_bytes()
    info["source_archive"].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
    info_path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n")
    sums_path = dest / "SHA256SUMS.txt"
    files = {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in dest.rglob("*") if p.is_file() and p != sums_path}
    sums_path.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(files.items())))


class WebsiteBundleTests(unittest.TestCase):
  def setUp(self):
    self.temp = tempfile.TemporaryDirectory()
    self.tmp_path = Path(self.temp.name)

  def tearDown(self):
    self.temp.cleanup()

  def test_ignored_runtime_source_extras_are_rejected_without_destination_writes(self):
    root = _fixture(self.tmp_path)
    private = root / "site/source/runtime-profile/source/private-build-notes.txt"
    private.write_text("Private build notes must never be published")
    destination = self.tmp_path / "website"
    with self.assertRaisesRegex(BundleError, "inventory"):
        build(root, destination)
    self.assertFalse(destination.exists())

  def test_build_is_deterministic_and_verified(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    one, two = tmp_path / "one", tmp_path / "two"
    result = build(root, one)
    verify_website(one, root)
    build(root, two)
    first = {p.relative_to(one).as_posix(): p.read_bytes() for p in one.rglob("*") if p.is_file()}
    second = {p.relative_to(two).as_posix(): p.read_bytes() for p in two.rglob("*") if p.is_file()}
    assert first == second
    assert result["files"] == len(first)
    assert "legacy-v0.1.bin" not in {p.relative_to(one).as_posix() for p in one.rglob("*") if p.is_file()}
    assert "Source Code &amp; Licences" in (one / "index.html").read_text()
    assert "planned; not yet published or verified" in (one / "source-and-licences.html").read_text()
    page = (one / "source-and-licences.html").read_text()
    assert "Full LGPL 2.1 text" in page and "GNU LESSER GENERAL PUBLIC LICENSE" in page
    build_info = json.loads((one / "build-info.json").read_text())
    assert build_info["application_version"] == "0.5.1" and build_info["package_format"] == 1
    archive = next((one / "source").glob("*.zip"))
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        assert "SOURCE-INFO.json" in names
        assert any(name.endswith("project/site/demo/legacy-v0.1.bin") for name in names)
        assert "runtime/core/genplus.wasm" in names
        assert "project/licences/EMSCRIPTEN-LICENSE.txt" in names


  def test_failed_validation_leaves_nonempty_destination_untouched(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()
    sentinel = dest / "keep.txt"
    sentinel.write_text("keep")
    with self.assertRaisesRegex(BundleError, "new or empty"):
        build(root, dest)
    assert sentinel.read_text() == "keep"

  def test_source_archive_validator_rejects_invalid_zip(self):
    with self.assertRaisesRegex(BundleError, "Invalid corresponding-source archive"):
        verify_source_archive(b"not a zip")


  def test_missing_lgpl_text_fails_before_destination_creation(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path, licence=False)
    dest = tmp_path / "dest"
    with self.assertRaisesRegex(BundleError, "LGPL text"):
        build(root, dest)
    assert not dest.exists()

  def test_missing_cmake_component_fails_before_destination_creation(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path, missing_source=True)
    dest = tmp_path / "dest"
    with self.assertRaisesRegex(BundleError, "ym2612.c"):
        build(root, dest)
    assert not dest.exists()


  def test_unapproved_rom_fails_before_destination_creation(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    _put(root, "site/demo/unknown.bin", b"unknown")
    dest = tmp_path / "dest"
    with self.assertRaises(CartridgeError):
        build(root, dest)
    assert not dest.exists()

  def test_untracked_private_inputs_are_never_archived(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    _put(root, "demo-cart/.env", "SECRET=not-for-archive\n")
    _put(root, "demo-cart/private.zip", b"unapproved nested archive")
    dest = tmp_path / "dest"
    build(root, dest)
    with zipfile.ZipFile(next((dest / "source").glob("*.zip"))) as archive:
        names = archive.namelist()
        self.assertNotIn("project/demo-cart/.env", names)
        self.assertNotIn("project/demo-cart/private.zip", names)


  def test_symlink_source_fails_before_destination_creation(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path, symlink=True)
    dest = tmp_path / "dest"
    with self.assertRaisesRegex((BundleError, CartridgeError), "Symlinks"):
        build(root, dest)
    assert not dest.exists()

  def test_stale_corresponding_source_is_rejected(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    dest = tmp_path / "dest"
    build(root, dest)
    info = json.loads((dest / "build-info.json").read_text())
    archive_path = dest / info["source_archive"]["path"]
    temp_archive = archive_path.with_suffix(".tmp")
    with zipfile.ZipFile(archive_path) as original, zipfile.ZipFile(temp_archive, "w") as changed:
        source_info = json.loads(original.read("SOURCE-INFO.json"))
        entries = {entry.filename: (entry, original.read(entry.filename)) for entry in original.infolist()}
        source_path = "project/README.md"
        entries[source_path] = (entries[source_path][0], b"stale source\n")
        source_info["files"][source_path] = hashlib.sha256(b"stale source\n").hexdigest()
        entries["SOURCE-INFO.json"] = (entries["SOURCE-INFO.json"][0],
                                        (json.dumps(source_info, indent=2, sort_keys=True) + "\n").encode())
        for name in sorted(entries):
            entry, data = entries[name]
            changed.writestr(entry, data)
    temp_archive.replace(archive_path)
    _refresh_bundle_checksums(dest)
    with self.assertRaisesRegex(BundleError, "differs from checkout"):
        verify_website(dest, root)


  def test_unsafe_zip_entry_is_rejected_even_with_updated_outer_checksums(self):
    tmp_path = self.tmp_path
    root = _fixture(tmp_path)
    dest = tmp_path / "dest"
    build(root, dest)
    info_path = dest / "build-info.json"
    info = json.loads(info_path.read_text())
    archive_path = dest / info["source_archive"]["path"]
    temp_archive = archive_path.with_suffix(".tmp")
    with zipfile.ZipFile(archive_path) as original, zipfile.ZipFile(temp_archive, "w") as changed:
        for entry in original.infolist():
            changed.writestr(entry, original.read(entry.filename))
        changed.writestr("../escape.txt", b"escape")
    temp_archive.replace(archive_path)
    data = archive_path.read_bytes()
    _refresh_bundle_checksums(dest)
    with self.assertRaisesRegex(BundleError, "Unsafe source ZIP entry"):
        verify_website(dest, root)
