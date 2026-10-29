#!/usr/bin/env python3
"""Build and verify the thin static VRAMpage MD deployment bundle."""
import argparse
from pathlib import Path
import sys

from cartridges import CartridgeError
from website_bundle import BundleError, build, verify_website


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="new or empty directory for the website bundle")
    args = parser.parse_args(argv)
    destination = args.output.expanduser().absolute()
    try:
        result = build(ROOT, destination)
        verify_website(destination, ROOT)
    except (BundleError, CartridgeError, OSError, ValueError) as error:
        print(f"Cannot build website bundle: {error}", file=sys.stderr)
        return 1
    print(f"Created and verified {destination} ({result['files']} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
