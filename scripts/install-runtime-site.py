#!/usr/bin/env python3
"""Install a verified optional runtime profile into the static site tree."""
from pathlib import Path
import os
import shutil
import sys


PINNED_COMMIT = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
PROFILE_MARKER = ".vrampage-runtime-profile"
PROFILE_MARKER_TEXT = f"VRAMpage runtime build profile v1\n{PINNED_COMMIT}\n"
SITE_MARKER = ".vrampage-site-runtime-profile"
SITE_MARKER_TEXT = f"VRAMpage site runtime profile v1\n{PINNED_COMMIT}\n"


def runtime_output(root: Path) -> Path:
    configured = os.environ.get("VRAM_RUNTIME_OUTPUT_DIR")
    return Path(configured).absolute() if configured else root / "build/runtime-profile"


def reject_symlink_path(path: Path) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise RuntimeError(f"Refusing symlink path: {current}")
        if current.parent == current:
            return
        current = current.parent


def install(root: Path, output: Path) -> None:
    core_src = output / "core"
    source_src = output / "source"
    marker_src = output / PROFILE_MARKER
    if (not core_src.is_dir() or not source_src.is_dir() or
            not marker_src.is_file() or marker_src.read_text() != PROFILE_MARKER_TEXT):
        raise RuntimeError(f"No complete marked runtime build found at {output}")
    for name in ("genplus.js", "genplus.wasm"):
        item = core_src / name
        if not item.is_file() or item.stat().st_size == 0:
            raise RuntimeError(f"Runtime output is missing {item}")

    site = root / "site"
    core_dst = site / "core"
    source_dst = site / "source"
    runtime_dst = source_dst / "runtime-profile"
    reject_symlink_path(site)
    reject_symlink_path(core_dst)
    reject_symlink_path(source_dst)
    reject_symlink_path(runtime_dst)
    if not core_dst.is_dir() or not source_dst.is_dir():
        raise RuntimeError("Build the normal site tree first so README and source metadata are present")
    if runtime_dst.exists():
        marker = runtime_dst / SITE_MARKER
        if marker.is_symlink() or not marker.is_file() or marker.read_text() != SITE_MARKER_TEXT:
            raise RuntimeError(f"Refusing to replace unmarked runtime source: {runtime_dst}")

    stage = source_dst / ".runtime-profile-staging"
    reject_symlink_path(stage)
    if stage.exists():
        raise RuntimeError(f"Refusing existing staging path: {stage}")
    stage.mkdir()
    try:
        shutil.copytree(source_src, stage / "source")
        shutil.copy2(output / "BUILDING.txt", stage / "BUILDING.txt")
        shutil.copy2(output / "THIRD-PARTY-NOTICES.md", stage / "THIRD-PARTY-NOTICES.md")
        (stage / SITE_MARKER).write_text(SITE_MARKER_TEXT)
        if runtime_dst.exists():
            shutil.rmtree(runtime_dst)
        os.replace(stage, runtime_dst)
        for name in ("genplus.js", "genplus.wasm"):
            shutil.copy2(core_src / name, core_dst / name)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    try:
        repository = Path(__file__).resolve().parents[1]
        install(repository, runtime_output(repository))
        print(f"Installed runtime core and source into {repository / 'site'}")
    except (OSError, RuntimeError, shutil.Error) as error:
        print(f"Runtime site installation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
