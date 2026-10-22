# Read-only Sonic demo observations

This developer experiment uses a privately supplied, unmodified cartridge and the
published v0.2.6 core. It does not change the emulator, game variables or game code.
It is not required to launch the normal Mac application.

## Scope and provenance

The supported cartridge is exactly 524,288 bytes with SHA-256
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
The observer refuses other ROMs and packages before loading executable core JS.
Its fixed package profile verifies the two build manifests, VERSION, exact source
commit and both core-file hashes. Package source is
`6d18f8e80191f1d60e5aa7b5899d3524c6dcbc07`; tool identity is recorded separately.
No cartridge, RAM dump, framebuffer, game capture or audio data is distributed.

Field names and addresses are based on public Sonic Retro s1disasm AS source at
[15dfa3a6](https://github.com/sonicretro/s1disasm/tree/15dfa3a6ee4c53aeb482233e493755c84b4f3479),
particularly `_Variables.asm`, `_Constants.asm` and `_inc/MoveSonicInDemo.asm`.
These are diagnostic reads, not game-specific fault behaviour. The actual fault
uses the existing generic hardware-informed work-RAM API.

The pinned core stores logical 68000 RAM byte address `a` at raw offset `a ^ 1`.
Words combine two logical bytes in 68000 order. Game mode, held/pressed input and
the countdown at logical `$F792` are bytes; the cursor and demo flag are words.
Tests use distinct adjacent bytes and independent literal addresses to catch
byte-order, width and offset mistakes. These details matter: an early temporary
reader combined adjacent bytes and confused held with pressed input. It was
corrected before the tracked evidence below was produced.

## Reproduce privately

Download and extract the complete v0.2.6 package, then use Node.js from a source
checkout. Node is a developer experiment dependency, not a requirement for play.

```sh
node scripts/observe-attract-demo.cjs /private/path/sonic.md --app /path/to/extracted/VRAMpage-MD > /tmp/attract-observations.json
```

Every scenario starts a fresh core twice and runs 2,400 ticks. Host controller
input is zeroed and measured each tick, input update is called, and audio is
consumed. Faults are armed after the tick-1800 sample, before tick 1801. Requested
tick, setter/core frame and reported activation frame are recorded separately.
There is no forced CPU resume, recovery or reset after activation.

The named scalar observations, hashes, counters and repeat comparisons do not
include raw game bytes. The profile is ROM-specific and does not support other
revisions without separate validation. Package identity is not proof of physical
electrical accuracy. Synthetic tests do not establish actual game behaviour.

## Protocol 1 results

[Exact six-trial record](experiments/2026-10-22-attract-demo-observer-v1.json),
produced with tool commit `344bd861d97796f0b71ead763d8932290696cf71` and SHA-256
`21ea2585820674941f75da3a85e0db8acd7976afd90b90e6cd8536f2a2aa731b`.
All three scenarios repeated identically. Both fault cases matched the baseline
before activation. Host input was zero for all 2,400 ticks in every trial.

| Scenario | Observed result | Acceptance implication |
|---|---|---|
| No fault | Demo mode 8, flag 1, cursor 26 at tick 1800 advancing to 96 at 2400; changing internal pad state | Source-backed internal demo playback under zero external input |
| Sustained D0/D1 read fault | Cursor and pad clear at 1801; raw frame hash becomes static, mode corrupts, demo flag later clears; CPU flags remain zero | Negative control: ticks and clear CPU flags do not establish playback |
| A10/A11, one affected write | Budget releases at 1801 after exactly one write; internal demo markers continue; raw frame hashes differ from same-tick baseline | Continuation candidate; gameplay trajectory divergence is not established |

Protocol 1's `visibleFrameSHA256` means the raw 320x224 active rectangle inside
the core's 640x480 buffer. It is not the image after browser framebuffer recovery.
Do not describe these hashes as captured browser displays.

A timing offset can change same-tick hashes without changing the gameplay path.
Phase-aligned comparisons and source-backed player-state or private visual
observations are needed before claiming genuine gameplay divergence. The RAM
attract-mode milestone remains incomplete. Native Mac/Firefox, audible playback,
physical hardware, longer durations and other cartridge revisions were not
validated by this experiment. Earlier recorded experiments remain unchanged.
