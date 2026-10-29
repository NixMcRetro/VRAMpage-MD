#!/usr/bin/env python3
"""Build the pinned original Demo Cart v0.3.5 for future release packages."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo-cart" / "fx-lab" / "build_fx.py"
GENERATED = ROOT / "demo-cart" / "fx-lab" / "build" / "VRAMpage-MD-FX-Lab-v0.3.5-Demoscene.bin"
DEST = ROOT / "site" / "demo" / "VRAMpage-MD-Demo-Cart-v0.3.5.bin"
EXPECTED_SHA = "89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f"
EXPECTED_BYTES = 150564

def main():
    subprocess.run([sys.executable, str(SOURCE)], cwd=ROOT, check=True)
    binary = GENERATED.read_bytes()
    actual = hashlib.sha256(binary).hexdigest()
    if len(binary) != EXPECTED_BYTES or actual != EXPECTED_SHA or binary[0x100:0x104] != b"SEGA":
        raise SystemExit(f"Unapproved Demo Cart generated: size={len(binary)} sha256={actual}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GENERATED, DEST)
    if hashlib.sha256(DEST.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise SystemExit("Demo Cart checksum mismatch after copy")
    print(f"Verified Demo Cart v0.3.5: {DEST.relative_to(ROOT)}, sha256={actual}")

if __name__ == "__main__":
    main()
