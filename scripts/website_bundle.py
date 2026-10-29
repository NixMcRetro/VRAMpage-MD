"""Build a small static website bundle with exact corresponding source and notices."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile

from cartridges import CartridgeError, approved_assets, load_manifest, repo_file, verify_site


STATIC_FILES = (
    "index.html", "style.css", "app.js", "cartridges.js", "cartridges.json",
    "framebuffer.js", "rgb-encoder.js", "circuit-config.js", "experiment-comparison.js",
    "core/genplus.js", "core/genplus.wasm",
)
RUNTIME_PROFILE = "site/source/runtime-profile"
BUILDING = f"{RUNTIME_PROFILE}/BUILDING.txt"
NOTICES = f"{RUNTIME_PROFILE}/THIRD-PARTY-NOTICES.md"
PINNED_UPSTREAM = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
EMSCRIPTEN = "4.0.23"
MAX_SOURCE_ARCHIVE_SIZE = 32 * 1024 * 1024
MAX_SOURCE_ARCHIVE_EXPANDED_SIZE = 64 * 1024 * 1024
MAX_SOURCE_ARCHIVE_FILES = 4000
SOURCE_LINK = '<a href="source-and-licences.html">Source Code &amp; Licences</a>'
SOURCE_INSTRUCTIONS = (
    "From the extracted source ZIP, activate Emscripten 4.0.23 and run:\n\n"
    "  cd emulator/wasm-genplus\n"
    "  emcmake cmake -S . -B build -DCMAKE_POLICY_VERSION_MINIMUM=3.5\n"
    "  emmake make -C build -j2\n\n"
    "The generated core is in src/main/js/. Compare both files with runtime/core/ "
    "using SOURCE-INFO.json. The source ZIP also contains the frontend, approved "
    "cartridge source and notices."
)


class BundleError(ValueError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_file(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if not relative or rel.is_absolute() or ".." in rel.parts or "\\" in relative:
        raise BundleError(f"Unsafe source path: {relative!r}")
    path = root.joinpath(*rel.parts)
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise BundleError(f"Symlinks are not allowed in bundle inputs: {relative}")
    try:
        path.resolve(strict=True).relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise BundleError(f"Missing or escaping bundle input: {relative}") from error
    if not path.is_file():
        raise BundleError(f"Bundle input is not a regular file: {relative}")
    return path


def _git_identity(root: Path) -> tuple[str, str]:
    try:
        status = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"], text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD^{commit}"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise BundleError("Source must be a readable Git checkout.") from error
    if status:
        raise BundleError("Commit tracked source changes before packaging the website.")
    return commit, status


def _profile(root: Path) -> tuple[bytes, bytes, dict[str, str]]:
    marker = _safe_file(root, f"{RUNTIME_PROFILE}/.vrampage-site-runtime-profile").read_text(encoding="utf-8")
    if marker != f"VRAMpage site runtime profile v1\n{PINNED_UPSTREAM}\n":
        raise BundleError("The staged runtime profile marker is missing or invalid.")
    building = _safe_file(root, BUILDING).read_bytes()
    notices = _safe_file(root, NOTICES).read_bytes()
    text = building.decode("utf-8")
    if f"Pinned wasm-genplus source: {PINNED_UPSTREAM}" not in text:
        raise BundleError("The staged runtime profile does not identify the pinned core source.")
    hashes: dict[str, str] = {}
    for name in ("genplus.js", "genplus.wasm"):
        match = re.search(rf"{re.escape(name)} SHA-256: ([0-9a-f]{{64}})", text)
        if not match:
            raise BundleError(f"Runtime build record is missing the {name} SHA-256.")
        deployed = _safe_file(root, f"site/core/{name}").read_bytes()
        if _sha(deployed) != match.group(1):
            raise BundleError(f"Deployed {name} does not match the corresponding-source build record.")
        hashes[name] = match.group(1)
    if not _safe_file(root, f"{RUNTIME_PROFILE}/source/wasm-genplus/CMakeLists.txt").read_bytes():
        raise BundleError("The runtime profile is missing its CMake build definition.")
    vendor = root / RUNTIME_PROFILE / "source/wasm-genplus"
    license_file = vendor / "src/main/c/core/ntsc/license.txt"
    if not license_file.is_file() or license_file.is_symlink():
        raise BundleError("The corresponding source is missing the full LGPL text.")
    required_licences = (
        "src/main/c/core/genesis.c", "src/main/c/core/sound/ym3438.c",
        "src/main/c/core/m68k/m68k.h", "src/main/c/core/z80/z80.c",
        "src/main/c/core/sound/blip_buf.c",
    )
    for relative in required_licences:
        _safe_file(vendor, relative)
    if b"GNU LESSER GENERAL PUBLIC LICENSE" not in _safe_file(
        vendor, "src/main/c/core/ntsc/license.txt"
    ).read_bytes():
        raise BundleError("The corresponding source is missing the full LGPL text.")
    if not _safe_file(root, f"{RUNTIME_PROFILE}/source/THIRD-PARTY-NOTICES.md").read_bytes():
        raise BundleError("The runtime source archive is missing its component notices.")
    return building, notices, hashes


def _source_paths(root: Path, manifest: dict) -> list[str]:
    # These are project and build inputs; experiments, test suites, generated build
    # trees and unrelated development documentation do not belong in the release ZIP.
    paths = {
        "VERSION", "README.md", "START.command", "docs/RUNNING-LOCALLY.md",
        "docs/LICENCE-AUDIT-v0.5.1.md", "THIRD-PARTY-NOTICES.md",
        "licences/EMSCRIPTEN-LICENSE.txt",
        "scripts/cartridges.py", "scripts/build-demo-cart.py", "scripts/build-core.sh",
        "scripts/build-core-runtime.py", "scripts/install-runtime-site.py",
        "scripts/patch_core.py", "scripts/session_checkpoint_patch.py",
        "scripts/serve.py", "scripts/package-website.py", "scripts/website_bundle.py",
        "site/index.html", "site/style.css", "site/app.js", "site/cartridges.js",
        "site/cartridges.json", "site/framebuffer.js", "site/rgb-encoder.js",
        "site/circuit-config.js", "site/experiment-comparison.js",
    }
    from cartridges import source_paths
    paths.update(source_paths(manifest))
    paths.update(asset["path"] for asset in manifest["preservedAssets"]
                 if asset["path"].startswith("site/"))
    # Include the whole approved cartridge source kits (including graphics and source
    # notices), but not generated ROM outputs or tests.
    for base in (root / "demo-cart",):
        for path in base.rglob("*"):
            if path.is_symlink():
                raise BundleError(f"Symlinks are not allowed in cartridge source: {path}")
            if path.is_file() and "tests" not in path.relative_to(base).parts and path.suffix.lower() not in {
                ".bin", ".rom", ".smd", ".md", ".wasm", ".o", ".a", ".pyc",
            }:
                paths.add(path.relative_to(root).as_posix())
    # The runtime profile is the source actually used by this binary. Copy the full
    # upstream C/C++ tree, build definitions and VRAMpage shims, pruning build assets.
    profile_source = root / RUNTIME_PROFILE / "source"
    for path in profile_source.rglob("*"):
        if path.is_symlink():
            raise BundleError(f"Symlinks are not allowed in runtime source: {path}")
        relative = path.relative_to(profile_source).as_posix()
        parts = PurePosixPath(relative).parts
        if not path.is_file() or any(part in {".git", "build", "docs", "assets", ".vscode", "node_modules"} for part in parts):
            continue
        if path.name.endswith((".pyc", ".o", ".a", ".wasm.map", ".dbg")):
            continue
        if parts[:4] == ("wasm-genplus", "src", "main", "js") and (
            path.name in {"genplus.js", "genplus.wasm"} or path.suffix in {".map", ".dbg"}
        ):
            continue
        paths.add(f"emulator/{relative}")
    paths.update({
        "emulator/wasm-genplus/README.md", "emulator/wasm-genplus/CMakeLists.txt",
        "emulator/wasm-genplus/cmake/macros.cmake",
    })
    missing = []
    for name in sorted(paths):
        source = (root / RUNTIME_PROFILE / "source" / name[len("emulator/"):]
                  if name.startswith("emulator/") else root / name)
        try:
            source.resolve(strict=True).relative_to(root.resolve())
        except (OSError, ValueError):
            missing.append(name)
            continue
        if not source.is_file() or source.is_symlink() or not source.read_bytes():
            missing.append(name)
    if missing:
        raise BundleError("Missing or empty corresponding-source files:\n  " + "\n  ".join(missing))
    return sorted(paths)


def _zip_info(name: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    return info


def _source_archive(root: Path, paths: list[str], version: str, commit: str,
                    core_hashes: dict[str, str], archive_path: Path) -> dict:
    files: dict[str, bytes] = {}
    for relative in paths:
        target = relative if relative.startswith("emulator/") else f"project/{relative}"
        source = (root / RUNTIME_PROFILE / "source" / relative[len("emulator/"):]
                  if relative.startswith("emulator/") else _safe_file(root, relative))
        data = source.read_bytes()
        if relative == "site/index.html":
            html = data.decode("utf-8")
            if html.count("<footer>") != 1:
                raise BundleError("Corresponding source index has no unique footer insertion point.")
            data = html.replace("<footer>", f"<footer>{SOURCE_LINK}", 1).encode("utf-8")
        files[target] = data
    # The saved complete profile notes are separate from upstream source root.
    profile_building = _safe_file(root, f"{RUNTIME_PROFILE}/BUILDING.txt").read_text(encoding="utf-8")
    profile_building = (profile_building.replace("cd source/wasm-genplus", "cd emulator/wasm-genplus")
                        .replace("source/scripts", "emulator/scripts"))
    files["emulator/BUILDING.txt"] = (f"Required Emscripten SDK: {EMSCRIPTEN}\n\n" + profile_building).encode()
    files["emulator/PROFILE-THIRD-PARTY-NOTICES.md"] = _safe_file(
        root, f"{RUNTIME_PROFILE}/THIRD-PARTY-NOTICES.md").read_bytes()
    for name in ("genplus.js", "genplus.wasm"):
        files[f"runtime/core/{name}"] = _safe_file(root, f"site/core/{name}").read_bytes()
    files["SOURCE-INFO.json"] = b""  # filled after source entries are hashed
    entries = {name: _sha(data) for name, data in sorted(files.items()) if name != "SOURCE-INFO.json"}
    source_info = {
        "application": "VRAMpage MD", "version": version, "source_commit": commit,
        "wasm_genplus_commit": PINNED_UPSTREAM, "emscripten_version": EMSCRIPTEN,
        "core_sha256": core_hashes, "rebuild": SOURCE_INSTRUCTIONS,
        "files": entries,
    }
    files["SOURCE-INFO.json"] = (json.dumps(source_info, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name in sorted(files):
            mode = 0o755 if name.endswith("START.command") else 0o644
            archive.writestr(_zip_info(name, mode), files[name])
    return source_info


def _render_source_page(version: str, archive_name: str, archive_hash: str) -> bytes:
    return (f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Source Code &amp; Licences · VRAMpage MD v{version}</title>
<link rel="stylesheet" href="style.css"></head>
<body><main class="source-page"><h1>Source Code &amp; Licences</h1>
<p>Corresponding source for VRAMpage MD v{version}, including the modified WebAssembly core and component notices.</p>
<p><a href="source/{archive_name}">Download corresponding source ZIP</a> (SHA-256: <code>{archive_hash}</code>).</p>
<p>GitHub source mirror: planned; not yet published or verified.</p>
<h2>Rebuild the WebAssembly core</h2><pre>{SOURCE_INSTRUCTIONS}</pre>
<p>For terms and attributions, see <code>emulator/THIRD-PARTY-NOTICES.md</code> in the ZIP and the original notices retained with each component's source.</p>
<p>Release source commit and binary hashes are recorded in <code>SOURCE-INFO.json</code> at the ZIP root.</p>
<p><a href="index.html">Return to VRAMpage MD</a></p></main></body></html>\n''').encode()


def verify_source_archive(archive: bytes | bytearray | memoryview | Path | str,
                          expected_metadata: dict | None = None) -> dict:
    """Validate ZIP paths and every SOURCE-INFO hash before extraction; return metadata.

    This proves internal consistency, not publisher identity. Bind the archive SHA-256
    to trusted build metadata before using it as a release artifact.
    """
    try:
        data = Path(archive).read_bytes() if isinstance(archive, (Path, str)) else bytes(archive)
    except OSError as error:
        raise BundleError(f"Cannot read corresponding-source archive: {error}") from error
    if len(data) > MAX_SOURCE_ARCHIVE_SIZE:
        raise BundleError("Corresponding-source archive exceeds the supported size limit.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as source_zip:
            members = source_zip.infolist()
            names = [member.filename for member in members]
            if len(members) > MAX_SOURCE_ARCHIVE_FILES or len(names) != len(set(names)):
                raise BundleError("Source archive has too many files or duplicate paths.")
            if sum(member.file_size for member in members) > MAX_SOURCE_ARCHIVE_EXPANDED_SIZE:
                raise BundleError("Source archive expands beyond the supported size limit.")
            for name, member in zip(names, members):
                path = PurePosixPath(name)
                mode = member.external_attr >> 16
                if (not name or path.is_absolute() or path.as_posix() != name or not path.parts
                        or any(part in {"", ".", ".."} for part in path.parts)
                        or "\\" in name or ":" in name or stat.S_ISLNK(mode)
                        or stat.S_ISDIR(mode)):
                    raise BundleError(f"Unsafe source ZIP entry: {name}")
            if "SOURCE-INFO.json" not in names:
                raise BundleError("Source archive is missing root SOURCE-INFO.json.")
            metadata = json.loads(source_zip.read("SOURCE-INFO.json"))
            if not isinstance(metadata, dict) or not isinstance(metadata.get("files"), dict):
                raise BundleError("SOURCE-INFO.json must contain a file hash map.")
            expected_names = set(metadata["files"]) | {"SOURCE-INFO.json"}
            if set(names) != expected_names:
                raise BundleError("Source archive entries do not match SOURCE-INFO.json.")
            for relative, digest in metadata["files"].items():
                path = PurePosixPath(relative)
                if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                        or path.is_absolute() or path.as_posix() != relative
                        or any(part in {"", ".", ".."} for part in path.parts)):
                    raise BundleError(f"Invalid SOURCE-INFO file entry: {relative}")
                if _sha(source_zip.read(relative)) != digest:
                    raise BundleError(f"Source archive SHA-256 mismatch: {relative}")
            if (metadata.get("application") != "VRAMpage MD"
                    or not re.fullmatch(r"\d+\.\d+\.\d+", metadata.get("version", ""))
                    or not re.fullmatch(r"[0-9a-f]{40}", metadata.get("source_commit", ""))
                    or metadata.get("wasm_genplus_commit") != PINNED_UPSTREAM
                    or metadata.get("emscripten_version") != EMSCRIPTEN
                    or not isinstance(metadata.get("core_sha256"), dict)
                    or set(metadata["core_sha256"]) != {"genplus.js", "genplus.wasm"}):
                raise BundleError("SOURCE-INFO.json has invalid version, commit, toolchain or core metadata.")
            required = {
                "project/VERSION", "project/THIRD-PARTY-NOTICES.md",
                "project/licences/EMSCRIPTEN-LICENSE.txt", "emulator/BUILDING.txt",
                "emulator/THIRD-PARTY-NOTICES.md", "emulator/PROFILE-THIRD-PARTY-NOTICES.md",
                "emulator/scripts/patch_core.py", "emulator/scripts/session_checkpoint_patch.py",
                "emulator/wasm-genplus/CMakeLists.txt",
                "emulator/wasm-genplus/src/main/c/core/genesis.c",
                "emulator/wasm-genplus/src/main/c/core/sound/ym3438.c",
                "emulator/wasm-genplus/src/main/c/core/sound/ym2612.c",
                "emulator/wasm-genplus/src/main/c/core/sound/ym2413.c",
                "emulator/wasm-genplus/src/main/c/core/sound/blip_buf.c",
                "emulator/wasm-genplus/src/main/c/core/sound/eq.c",
                "emulator/wasm-genplus/src/main/c/core/m68k/m68k.h",
                "emulator/wasm-genplus/src/main/c/core/z80/z80.c",
                "emulator/wasm-genplus/src/main/c/wasm/scrc32.c",
                "emulator/wasm-genplus/src/main/c/core/ntsc/license.txt",
                "runtime/core/genplus.js", "runtime/core/genplus.wasm",
            }
            if not required.issubset(names):
                raise BundleError("Source archive is missing required source, licence or runtime files.")
            if source_zip.read("project/VERSION").decode("utf-8").strip() != metadata["version"]:
                raise BundleError("Project VERSION does not match SOURCE-INFO metadata.")
            for name, digest in metadata["core_sha256"].items():
                if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                        or _sha(source_zip.read(f"runtime/core/{name}")) != digest):
                    raise BundleError(f"Archived runtime core hash does not match SOURCE-INFO: {name}")
    except BundleError:
        raise
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        raise BundleError(f"Invalid corresponding-source archive: {error}") from error
    if expected_metadata:
        for key, value in expected_metadata.items():
            if metadata.get(key) != value:
                raise BundleError(f"Source archive metadata mismatch for {key}.")
    return metadata


def _expected_runtime_paths(root: Path, manifest: dict) -> set[str]:
    paths = {"source-and-licences.html", "build-info.json", "SHA256SUMS.txt", *STATIC_FILES}
    paths.update(entry["path"] for entry in manifest["cartridges"])
    paths.add("source/VRAMpage-MD-v" + (root / "VERSION").read_text().strip() + "-corresponding-source.zip")
    return paths


def build(root: Path, dest: Path) -> dict:
    """Create a conservative static package. Validate all inputs before writing dest."""
    root, dest = Path(root).resolve(), Path(dest).expanduser().absolute()
    if any(part.is_symlink() for part in (dest, *dest.parents)):
        raise BundleError("Destination path must not contain symlinks.")
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise BundleError("Destination must be a new or empty directory.")
    commit, _ = _git_identity(root)
    version = _safe_file(root, "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise BundleError("VERSION must contain a semantic application version.")
    manifest = load_manifest(root)
    verify_site(root, manifest)
    building, notices, core_hashes = _profile(root)
    source_paths_list = _source_paths(root, manifest)
    footer = _safe_file(root, "site/index.html").read_text(encoding="utf-8")
    if footer.count("<footer>") != 1 or "Source Code &amp; Licences" in footer:
        raise BundleError("Expected one unmodified footer insertion point in site/index.html.")
    for relative in STATIC_FILES:
        if not _safe_file(root, "site/" + relative).read_bytes():
            raise BundleError(f"Empty static application file: {relative}")

    # Stage completely elsewhere, then move into the empty destination in one step.
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".website-bundle-", dir=parent))
    try:
        archive_name = f"VRAMpage-MD-v{version}-corresponding-source.zip"
        archive_path = temp / "source" / archive_name
        archive_path.parent.mkdir(parents=True)
        source_info = _source_archive(root, source_paths_list, version, commit, core_hashes, archive_path)
        archive_data = archive_path.read_bytes()
        rendered = _render_source_page(version, archive_name, _sha(archive_data))
        (temp / "source-and-licences.html").write_bytes(rendered)
        for relative in STATIC_FILES:
            data = _safe_file(root, "site/" + relative).read_bytes()
            if relative == "index.html":
                text = data.decode("utf-8")
                text = text.replace("<footer>", f"<footer>{SOURCE_LINK}", 1)
                data = text.encode("utf-8")
            target = temp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for entry in manifest["cartridges"]:
            target_rel = entry["path"]
            source = _safe_file(root, "site/" + target_rel)
            target = temp / target_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (temp / "build-info.json").write_text(json.dumps({
            "application": "VRAMpage MD", "version": version, "source_commit": commit,
            "wasm_genplus_commit": PINNED_UPSTREAM, "emscripten_version": EMSCRIPTEN,
            "core_sha256": core_hashes,
            "source_archive": {"path": f"source/{archive_name}", "sha256": _sha(archive_data),
                               "size": len(archive_data)},
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        files = {path.relative_to(temp).as_posix(): _sha(path.read_bytes())
                 for path in sorted(temp.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"}
        sums = "".join(f"{digest}  {name}\n" for name, digest in sorted(files.items()))
        (temp / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
        expected = _expected_runtime_paths(root, manifest)
        actual = {p.relative_to(temp).as_posix() for p in temp.rglob("*") if p.is_file()}
        if actual != expected:
            raise BundleError(f"Generated runtime paths differ from allowlist; unexpected={sorted(actual - expected)}, missing={sorted(expected - actual)}")
        if dest.exists():
            dest.rmdir()
        temp.rename(dest)
        return {"files": len(actual), "source_info": source_info,
                "sha256": _sha((dest / "SHA256SUMS.txt").read_bytes())}
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def verify_website(dest: Path, root: Path) -> None:
    """Verify runtime allowlist, checksums, source archive paths and every source hash."""
    dest, root = Path(dest).resolve(), Path(root).resolve()
    manifest = load_manifest(root)
    expected = _expected_runtime_paths(root, manifest)
    actual = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()}
    if any(p.is_symlink() for p in dest.rglob("*")) or actual != expected:
        raise BundleError("Static output has symlinks or files outside the exact runtime allowlist.")
    sums_path = dest / "SHA256SUMS.txt"
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)", line)
        if not match:
            raise BundleError("Malformed SHA256SUMS.txt entry.")
        relative = match.group(2)
        if PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
            raise BundleError(f"Unsafe checksum path: {relative}")
        target = dest / relative
        if not target.is_file() or _sha(target.read_bytes()) != match.group(1):
            raise BundleError(f"Static output checksum mismatch: {relative}")
    if set(line.split("  ", 1)[1] for line in sums_path.read_text().splitlines()) != actual - {"SHA256SUMS.txt"}:
        raise BundleError("SHA256SUMS.txt does not cover every bundle file.")
    info = json.loads((dest / "build-info.json").read_text(encoding="utf-8"))
    archive_rel = info["source_archive"]["path"]
    if archive_rel not in actual or _sha((dest / archive_rel).read_bytes()) != info["source_archive"]["sha256"]:
        raise BundleError("Corresponding-source archive does not match build-info.json.")
    source_info = verify_source_archive((dest / archive_rel).read_bytes(), {
        "source_commit": info["source_commit"], "version": info["version"],
        "core_sha256": info["core_sha256"],
    })
    with zipfile.ZipFile(dest / archive_rel) as archive:
        names = archive.namelist()
        if source_info["source_commit"] != info["source_commit"] or source_info["core_sha256"] != info["core_sha256"]:
            raise BundleError("Corresponding-source metadata does not match runtime build metadata.")
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        commit, _ = _git_identity(root)
        if (info.get("version") != version or info.get("source_commit") != commit
                or source_info.get("version") != version
                or source_info.get("wasm_genplus_commit") != PINNED_UPSTREAM
                or source_info.get("emscripten_version") != EMSCRIPTEN
                or source_info.get("rebuild") != SOURCE_INSTRUCTIONS):
            raise BundleError("Bundle metadata does not match the current source checkout.")
        for name, digest in info["core_sha256"].items():
            archived = f"runtime/core/{name}"
            if archived not in names or _sha(archive.read(archived)) != digest:
                raise BundleError(f"Archive runtime binary mismatch: {name}")
        expected_sources = _source_paths(root, manifest)
        for relative in expected_sources:
            archive_name = relative if relative.startswith("emulator/") else f"project/{relative}"
            expected_data = ((root / RUNTIME_PROFILE / "source" / relative[len("emulator/"):]).read_bytes()
                             if relative.startswith("emulator/") else _safe_file(root, relative).read_bytes())
            if relative == "site/index.html":
                expected_data = expected_data.decode("utf-8").replace(
                    "<footer>", f"<footer>{SOURCE_LINK}", 1).encode("utf-8")
            if archive.read(archive_name) != expected_data:
                raise BundleError(f"Corresponding-source file differs from checkout: {relative}")
        expected_runtime = _profile(root)[2]
        archive_sha = _sha((dest / archive_rel).read_bytes())
        archive_name = PurePosixPath(archive_rel).name
        if (archive_name != f"VRAMpage-MD-v{version}-corresponding-source.zip"
                or (dest / "source-and-licences.html").read_bytes()
                != _render_source_page(version, archive_name, archive_sha)):
            raise BundleError("Source page or archive name differs from verified release metadata.")
        for relative in STATIC_FILES:
            expected_data = _safe_file(root, "site/" + relative).read_bytes()
            if relative == "index.html":
                expected_data = expected_data.decode("utf-8").replace(
                    "<footer>", f"<footer>{SOURCE_LINK}", 1).encode("utf-8")
            if (dest / relative).read_bytes() != expected_data:
                raise BundleError(f"Static runtime file differs from source: {relative}")
        for entry in manifest["cartridges"]:
            relative = entry["path"]
            if (dest / relative).read_bytes() != _safe_file(root, "site/" + relative).read_bytes():
                raise BundleError(f"Static cartridge differs from approved source: {relative}")
        if info["core_sha256"] != expected_runtime:
            raise BundleError("Runtime core hashes differ from the staged build record.")
        profile_building = _safe_file(root, f"{RUNTIME_PROFILE}/BUILDING.txt").read_text(encoding="utf-8")
        profile_building = (profile_building.replace("cd source/wasm-genplus", "cd emulator/wasm-genplus")
                            .replace("source/scripts", "emulator/scripts"))
        expected_building = (f"Required Emscripten SDK: {EMSCRIPTEN}\n\n" + profile_building).encode()
        if archive.read("emulator/BUILDING.txt") != expected_building:
            raise BundleError("Archive build instructions differ from staged build metadata.")
        if archive.read("emulator/PROFILE-THIRD-PARTY-NOTICES.md") != _safe_file(
            root, f"{RUNTIME_PROFILE}/THIRD-PARTY-NOTICES.md").read_bytes():
            raise BundleError("Archive emulator notices differ from the staged source.")
    verify_site(root, manifest)


__all__ = ["BundleError", "build", "verify_source_archive", "verify_website"]
