#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check site/app.js
node --check site/framebuffer.js
node tests/test_framebuffer.cjs
node tests/test_framebuffer_properties.cjs
node tests/test_pulse_sweep.cjs
node --check scripts/observe-attract-demo.cjs
node tests/test_attract_diagnostics.cjs
node --check scripts/trace-attract-write.cjs
node tests/test_write_trace_runner.cjs
node --check scripts/observe-ram-alias-audio-phase.cjs
node tests/test_ram_alias_audio_phase.cjs
cc -std=c11 -O2 -Wall -Wextra -Werror tests/fault_engine_smoke.c -o /tmp/vrambender_fault_smoke
/tmp/vrambender_fault_smoke
cc -std=c11 -O2 -Wall -Wextra -Werror \
  scripts/work_ram_fault.c tests/work_ram_fault_smoke.c -o /tmp/vrampage_work_ram_fault_smoke
/tmp/vrampage_work_ram_fault_smoke
