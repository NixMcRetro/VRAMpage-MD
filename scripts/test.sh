#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s tests -v
node --check site/app.js
cc -std=c11 -O2 -Wall -Wextra -Werror tests/fault_engine_smoke.c -o /tmp/vrambender_fault_smoke
/tmp/vrambender_fault_smoke