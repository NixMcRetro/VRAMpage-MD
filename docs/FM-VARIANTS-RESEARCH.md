# FM Engine and Output-Model Research

Research only, 28 October 2026 (UTC), against project main
`9b29a5b9380ed4fe760f41015d15c51c53674e1e` and exact upstream
`h1romas4/wasm-genplus@6090aff9e9b2f578cd28882bd4571d2e35b1d674`.
The upstream Git objects were read directly; generated source with project
checkpoint additions was not mistaken for pristine upstream code.

## Finding

There are useful native differences to investigate, but three choices must stay
separate: **emulation engine**, **digital output model**, and **board output
circuit**. The existing variable name `ym3438` does not establish a motherboard
profile or simply select one physical chip.

| Choice | What the Pinned Integration Actually Does | Current Default |
| --- | --- | --- |
| `config.ym3438` | Selects MAME OPN2 at zero, Nuked OPN2 at nonzero | MAME |
| `config.ym2612` | Selects MAME Discrete / Integrated / Enhanced model behavior | Discrete |
| Nuked `OPN2_SetChipType` | Independently selects DAC approximation and status-port mode bits | Read-any-status-port bit only; no integration caller |
| Filter/preamp/board circuit | Separate processing; not supplied by the engine or chip-model name | Existing app/core settings |

These facts come from the pinned
[defaults](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/wasm/config.c#L7-L26),
[engine dispatch](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/sound.c#L287-L321),
[MAME model enum](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.h#L19-L26)
and [Nuked mode bits](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym3438.h#L48-L53).
They are implementation evidence, not manufacturer measurements of every YM2612,
YM3438 or integrated Sega ASIC. No fresh Yamaha hardware measurement is claimed.

## Meaningful Differences Already in the Core

MAME's Discrete and Integrated models use the 9-bit operator-output mask;
Enhanced uses 14-bit output. The discrete path also applies its DAC ladder
approximation. Status-port and wrapper busy behavior depend on the model.
Enhanced is an emulator enhancement, so it should not be presented as another
motherboard revision. See the
[model configuration](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.c#L2157-L2203),
[discrete DAC branch](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.c#L2107-L2127)
and [busy/status rules](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/sound.c#L115-L153).

Nuked has separate YM2612-like DAC and any-port-status bits. Its default is mode
2, the latter bit alone. Mode 3 adds its YM2612-like DAC approximation while
keeping status mode fixed. The upstream DAC branch explicitly says it is not
verified; enabling it would not establish physical fidelity. The global mode
setter has no caller in the pinned console integration. See the
[default mode](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym3438.c#L236-L238),
[DAC branch](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym3438.c#L998-L1026)
and [setter](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym3438.c#L1216-L1219).

Changing the engine changes native update granularity, internal scaling and
status behavior, not Z80 bus ownership. Both engines retain the shared register
handler and project fault boundary. Nominal clock relationships remain distinct
from backend stepping. Board filters, amplifiers and analogue loading need their
own evidence; none follows automatically from either selector.

## New Native Characterization

The original [standalone probe](../tests/fm_output_mode_probe.c) compiles against
exact pinned Nuked `ym3438.c/.h`. It clocks legal address/data writes, programs
DAC bytes 0/128/255 and channel-6 stereo/left/right pan, then captures 2,304 raw
per-clock stereo outputs for each of modes 2 and 3. Assertions verify the DAC
and pan writes were actually accepted, literal midpoint behavior and pan-muted
outputs, so a difference cannot be attributed merely to an unprogrammed core.

| DAC Byte / Pan | Mode 2 L/R Min–Max | Mode 3 L/R Min–Max |
| --- | --- | --- |
| 128 / Stereo | `[0,0] / [0,0]` | `[3,3] / [3,3]` |
| 255 / Left | `[0,254] / [0,0]` | `[3,765] / [3,3]` |
| 0 / Left | `[-256,0] / [0,0]` | `[-768,3] / [-3,3]` |

All nine paired DAC/pan cases differed. Strict C11 (`-Wall -Wextra -Werror
-pedantic`) and ASan/UBSan runs passed and produced identical output summaries:
SHA-256 `98bd338cec8355256efd054ab3d507a4d4f69cb7fa2be897f8a5c3eb307c77ef`.
The initial specialist probe and the reviewed probe with added state/literal
assertions independently produced that same summary. LeakSanitizer was disabled
locally because it fails under container ptrace; ASan/UBSan remained enabled.

These are raw internal core units before the console wrapper's accumulation,
scaling, resampling and filters. They are not final browser PCM or measurements
of audible volume, quality, physical ladder voltages, MAME behavior or a game.
No audio-engine switch or new fault was implemented by this experiment.

To reproduce after obtaining the project's pinned vendor checkout:

```sh
mkdir -p build/fm-mode-research
 git -C vendor/wasm-genplus show 6090aff9e9b2f578cd28882bd4571d2e35b1d674:src/main/c/core/sound/ym3438.c > build/fm-mode-research/ym3438.c
 git -C vendor/wasm-genplus show 6090aff9e9b2f578cd28882bd4571d2e35b1d674:src/main/c/core/sound/ym3438.h > build/fm-mode-research/ym3438.h
cc -std=c11 -Wall -Wextra -Werror -pedantic -DHAVE_YM3438_CORE \
  -Ibuild/fm-mode-research build/fm-mode-research/ym3438.c \
  tests/fm_output_mode_probe.c -o build/fm-mode-research/probe
build/fm-mode-research/probe
```

For the sanitizer variant add `-g -O1 -fsanitize=address,undefined
-fno-sanitize-recover=all`, and run with leak detection disabled only where the
local environment requires it. Keep upstream notices/source with any binary
redistribution. Upstream source/header SHA-256 values used here:
`ffde87dc4e4675e3e71cdcbf81fd66cf4f008c76c25e4b115f57662d6780a2b8` and
`46dd11554f21812c2127b83bd2aa3498d9dbd2e064e36a1cd14153cdb470e557`.

## Checkpoints Are the Main Integration Constraint

The project's [checkpoint profile gate](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/scripts/session_checkpoint_runtime.c#L125-L132)
rejects the Nuked backend. Its
[stock-sound bound patch](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/scripts/session_checkpoint_patch.py#L142-L148)
also returns zero for it. These are project constraints, not claims about the
physical chip. A backend menu would therefore remove a working checkpoint
feature unless serialization support or explicit capability handling came first.

MAME Discrete/Integrated is a more promising small candidate that retains the
current backend. However, `config.ym2612`, static `chip_type` and `op_mask` are
not saved by the current checkpoint path. Upstream saves the MAME register state
and an engine-identification byte, not the MAME model choice. See
[model globals](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.c#L615-L635),
[MAME context serialization](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.c#L2205-L2256)
and [sound context](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/sound.c#L465-L486).
A passing backend gate alone does not prove cross-model checkpoint safety.

A future staged **FM Output Model: Discrete / Integrated** could keep the active
model fixed for a checkpoint's lifetime. CPU Reset and Restore would retain it;
Clean Restart/new-cartridge activation would discard the old checkpoint before
applying the pending model. Apply the choice after startup defaults and before
sound initialization; merely changing `config.ym2612` after initialization does
not update the core's static model. Reuse the existing staged-machine lifecycle.
This is a source-based proposal, not a verified new checkpoint capability.

## Required Next Evidence and Decision

Before any public selector, add actual-WASM tests for each MAME model's PCM,
DAC/status behavior, selected-chip fault routing and default parity. Prove
save → CPU Reset → restore while the active model remains fixed; rejected and
pending changes must preserve the live slot, while Clean Restart applies the
choice only after discarding it. Export requested/effective model identity so
comparisons cannot silently treat different models as the same machine. Retain
normal/fallback hashes and the existing release/build gates.

The [existing paired engine test recipe](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/tests/test_vram_transaction_wasm.py#L195-L231)
and [FM cartridge assertions](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/tests/test_fm_data_runtime.cjs#L285-L340)
provide starting fixtures. They test MAME/Nuked engine paths, not the new model
selection proposed here. They were inspected, not rerun in this research slice.

Recommend [RAM Write Enables](WORK-RAM-WRITE-ENABLE-RESEARCH.md) first, then a
bounded MAME model/replay proof before exposing a selector. Defer a Nuked engine
menu and any physical VA catalogue. Composite burst/sync and physical VRAM timing
retain their existing independent evidence gaps; neither is solved by changing
an FM engine or by this native probe. Application/native runtime behavior,
VERSION, public releases, Demo Cart assets and McRetro.net remain unchanged.
