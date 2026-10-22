#!/usr/bin/env python3
"""Serve a built VRAMpage MD bundle on this computer only."""

import argparse
import errno
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


def validate_bundle():
    required_files = (
        SITE / "index.html",
        SITE / "style.css",
        SITE / "app.js",
        SITE / "framebuffer.js",
        SITE / "core" / "genplus.js",
        SITE / "core" / "genplus.wasm",
        SITE / "source" / "README.txt",
        SITE / "source" / "patch_core.py",
        SITE / "source" / "vram_fault_patch.c",
    )
    missing = [path.relative_to(ROOT).as_posix() for path in required_files
               if not path.is_file() or path.stat().st_size == 0]
    if missing:
        print("This download is missing files needed to run the local review bundle:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        print("Re-download and unzip the complete review bundle. A source checkout also needs the core build; see README.md.",
              file=sys.stderr)
        return False
    return True


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080,
                        help="local port to use (default: 8080; use 0 for an available port)")
    parser.add_argument("--no-browser", action="store_true",
                        help="serve without opening a browser (useful for tests and cloud environments)")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    return args


def main(argv=None):
    args = parse_args(argv)
    if not validate_bundle():
        return 1

    handler = partial(QuietHandler, directory=str(SITE))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            print(f"Port {args.port} is already in use. Close the other local server or run: "
                  "python3 scripts/serve.py --port 0", file=sys.stderr)
            return 1
        print(f"Could not start the local server: {error}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Serving the local review bundle at {url}", flush=True)
    print("Press Ctrl+C to stop the server.", flush=True)
    if not args.no_browser:
        try:
            if not webbrowser.open(url):
                print(f"Open this address in your browser: {url}", flush=True)
        except webbrowser.Error as error:
            print(f"Could not open a browser automatically ({error}). Open: {url}", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping the local server.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
