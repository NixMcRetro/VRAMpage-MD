#!/usr/bin/env python3
"""Create a local review ZIP containing only approved original cartridges from a built VRAMpage MD checkout."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

from cartridges import (CartridgeError, approved_assets, load_manifest, source_paths,
                        verify_asset, verify_site)


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CACHE_PARTS = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    ".tox", ".venv", "venv", "node_modules", "coverage",
}
REQUIRED_FILES = (
    "START.command",
    "README.md",
    "docs/RUNNING-LOCALLY.md",
    "scripts/serve.py",
    "site/index.html",
    "site/style.css",
    "site/app.js",
    "site/cartridges.js",
    "site/cartridges.json",
    "site/framebuffer.js",
    "site/rgb-encoder.js",
    "site/core/genplus.js",
    "site/core/genplus.wasm",
    "site/source/README.txt",
    "site/source/patch_core.py",
    "site/source/vram_fault_patch.c",
    "site/source/vram_transaction_render.h",
    "site/source/src/main/c/core/vdp_render.h",
    "site/source/src/main/c/core/ntsc/license.txt",
)
BUILD_INFO_PATHS = {"BUILD-INFO.json", "site/build-info.json"}
NATIVE_BLITTER_MARKER = b"VRAMpage MD: native RGBA output blitter"


class BundleError(Exception):
    pass


def _repo_path(relative):
    """Resolve a checkout-relative file and reject traversal or outside symlinks."""
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise BundleError(f"Unsafe path in package input: {relative!r}")
    path = ROOT.joinpath(*candidate.parts)
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise BundleError(f"Missing package input {relative}: {error}") from error
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise BundleError(f"Package input escapes the checkout: {relative}") from error
    if not resolved.is_file():
        raise BundleError(f"Package input is not a regular file: {relative}")
    return path


def _excluded_cache(relative):
    parts = PurePosixPath(relative).parts
    return any(part == ".git" or part in CACHE_PARTS or part.endswith(".pyc")
               for part in parts)


def _git_tracked_paths():
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace").strip()
        raise BundleError(f"Could not list tracked checkout files with git: {detail or error}") from error
    return [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


def _collect_paths(output_path):
    manifest = verify_site(ROOT, load_manifest(ROOT))
    assets = approved_assets(manifest)
    paths = set(_git_tracked_paths())
    if not SITE.is_dir():
        raise BundleError("The checkout is missing the site/ directory.")
    for path in SITE.rglob("*"):
        if path.is_file():
            paths.add(path.relative_to(ROOT).as_posix())

    output_resolved = output_path.resolve()
    selected = []
    for relative in sorted(paths):
        # Metadata is generated from this clean HEAD, never copied from local
        # files left by another build or supplied by a user.
        if relative in BUILD_INFO_PATHS or _excluded_cache(relative):
            continue
        source = _repo_path(relative)
        if source.resolve() == output_resolved:
            continue
        data = source.read_bytes()
        verify_asset(relative, data, assets)
        selected.append((relative, source, data))

    by_name = {name: data for name, _source, data in selected}
    missing = [name for name in set(REQUIRED_FILES) | assets.keys() | source_paths(manifest)
               if name not in by_name or not by_name[name]]
    if missing:
        raise BundleError("The built review bundle is incomplete; missing or empty files:\n  "
                          + "\n  ".join(missing)
                          + "\nBuild the modified core and corresponding source before packaging.")
    if not by_name["site/core/genplus.wasm"].startswith(b"\0asm"):
        raise BundleError("site/core/genplus.wasm does not have the WebAssembly binary signature.")
    if NATIVE_BLITTER_MARKER not in by_name["site/source/src/main/c/core/vdp_render.h"]:
        raise BundleError("The included emulator source is missing the native output blitter marker.")
    return selected


def _build_info():
    """Tie a runnable download to a clean, committed application source tree."""
    try:
        dirty = subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
            text=True).strip()
        commit = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD^{commit}"],
            text=True).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise BundleError("Package source must have a readable Git commit.") from error
    if dirty:
        raise BundleError("Commit tracked source changes before packaging so BUILD-INFO.json identifies the exact source.")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return json.dumps({"application": "VRAMpage MD", "application_version": version,
                       "source_commit": commit, "package_format": 1}, indent=2).encode() + b"\n"


def create_package(output_path):
    output_path = Path(output_path).expanduser().absolute()
    selected = _collect_paths(output_path)
    build_info = _build_info()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for relative in sorted(BUILD_INFO_PATHS):
            info = zipfile.ZipInfo(f"VRAMpage-MD/{relative}")
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, build_info)
        for relative, source, data in selected:
            info = zipfile.ZipInfo(f"VRAMpage-MD/{relative}")
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = stat.S_IMODE(source.stat().st_mode)
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, data)
    return len(selected) + len(BUILD_INFO_PATHS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="path for the ZIP file to create")
    args = parser.parse_args(argv)
    try:
        count = create_package(args.output)
    except (BundleError, CartridgeError) as error:
        print(f"Cannot create local review bundle: {error}", file=sys.stderr)
        return 1
    print(f"Created {args.output.expanduser().absolute()} with {count} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
