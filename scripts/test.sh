#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check site/app.js
node --check site/framebuffer.js
node tests/test_framebuffer.cjs
node tests/test_framebuffer_properties.cjs
cc -std=c11 -O2 -Wall -Wextra -Werror tests/fault_engine_smoke.c -o /tmp/vrambender_fault_smoke
/tmp/vrambender_fault_smoke