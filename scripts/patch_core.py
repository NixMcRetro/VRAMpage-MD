#!/usr/bin/env python3
"""Apply the initial experimental address-net patch to wasm-genplus.

This intentionally patches just the two stable anchors of the checked
wasm-genplus source. Fail closed if upstream structure changes.
"""
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
patch = pathlib.Path(__file__).with_name('vram_fault_patch.c').read_text()
wasm_c = root / 'src/main/c/wasm/wasm.c'
config_c = root / 'src/main/c/wasm/config.c'
wasm = wasm_c.read_text()
if 'VRAM Circuit Bender: initial frame-scoped' in wasm:
    raise SystemExit('Refusing to patch twice; use a clean wasm-genplus clone.')
anchor = 'void EMSCRIPTEN_KEEPALIVE tick(void) {\n    system_frame_gen(0);\n}'
if wasm.count(anchor) != 1:
    raise SystemExit('Expected tick() anchor missing; upstream changed. No modifications made.')
if wasm.count('#define SOUND_FREQUENCY 44100') != 1:
    raise SystemExit('Expected wasm.c header missing; upstream changed. No modifications made.')
# Place the runtime C shim before the public tick() entrypoint.
wasm = wasm.replace(anchor,
    patch + '\nvoid EMSCRIPTEN_KEEPALIVE tick(void) {\n'
    '    bend_before_frame();\n    system_frame_gen(0);\n'
    '    bend_after_frame();\n}', 1)
config = config_c.read_text()
old_region = 'config.region_detect  = 3;'
if config.count(old_region) != 1:
    raise SystemExit('Expected NTSC region config missing; upstream changed.')
# Force North America/NTSC regardless of international cartridge metadata.
config = config.replace(old_region, 'config.region_detect  = 1;', 1)
if not ('config.vdp_mode       = 1;' in config and 'config.master_clock   = 1;' in config):
    raise SystemExit('Expected VDP / oscillator defaults changed.')
wasm_c.write_text(wasm)
config_c.write_text(config)
print('Patched wasm-genplus: NTSC-U with experimental AD0..AD7 shorts.')