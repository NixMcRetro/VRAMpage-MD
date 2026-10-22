# RAM alias, VBlank state and audio phase observations

This developer-only experiment follows the first affected write at CPU address
`$FFF62A`, mapped to logical RAM `$F22A`. It uses the unchanged published v0.2.7
emulator, not an audio-bending feature. Normal Mac users need no new download or
Node installation. No game code or game variables are edited by the observer.

## Corrected source interpretation

The earlier sprite-buffer interpretation was incorrect. At pinned public
[s1disasm source](https://github.com/sonicretro/s1disasm/tree/15dfa3a6ee4c53aeb482233e493755c84b4f3479),
`v_vblank_routine` is at `$F600 + $2A = $F62A`. The full sound-driver allocation
includes its `$220`-byte 1-up backup; omitting it shifts later labels incorrectly.
The actual sprite-table buffer starts at `$F800`. The target `$F22A` remains the
`AMSFMSPan` byte of the first FM3 sound-effects track.

`sonic.asm` sets the VBlank flag to 8 before `WaitForVBlank`. That routine waits
until the flag is zero. The VBlank handler copies the flag, clears it, dispatches
work and updates music. A redirected flag clear could extend the wait by a frame,
but the generic address trace does not capture PC or written value. Treat both
flag set and flag clear as candidate instructions, not a proven executed path.

## Reproduce privately

Use the exact legally supplied cartridge fingerprint documented in
[the demo observer](ATTRACT-MODE-OBSERVATIONS.md) and the complete v0.2.7 package.
The new tool verifies the ROM, manifests, version, source and core-file hashes
before loading executable JavaScript.

```sh
node scripts/observe-ram-alias-audio-phase.cjs "/private/path/sonic.md" --app "/path/to/extracted/VRAMpage-MD" > /tmp/ram-alias-audio-phase.json
```

Baseline and A10/A11 one-affected-write scenarios each run twice with observation
and twice without it: eight fresh cores, 2,400 ticks each. Host input is zero.
The contact is armed after tick 1800, before tick 1801. No CPU resume, recovery,
reset or game-specific intervention occurs after activation.

After each tick, the core generates audio once. The observer reads the returned
sample count and hashes exactly that many Float32 samples from each channel in
canonical little-endian WebAssembly memory order. Raw audio and full timelines
remain private/in memory; output contains hashes, counts, named scalar samples
and aggregate comparisons only. Zero-sample pairs do not establish audio output.

Phase comparisons use fixed candidate ticks 1803 through 2398, 596 pairs per
lag, comparing candidate tick `t` to baseline tick `t + lag` for lags -2 through
+2. Missing and zero-sample pairs must be explicit. Compare sound, VBlank/target
state, player/demo state and raw-frame hashes separately. Matching sound at one
lag does not require game state to match at the same lag.

## Recorded result

[Protocol 1 evidence](experiments/2026-10-23-ram-alias-audio-phase-v1.json)
was produced with clean observer commit `21c40e3` and the pinned public v0.2.7
package. All eight fresh-core trials passed repeat, prefault and observational
noninterference checks. The pulse released after exactly one affected write.
Independent Luna High review checked the implementation, tests, source mapping,
provenance and bounded report shape.

Each scenario generated 1,766,274 stereo sample pairs across 2,400 ticks, with
735 or 736 samples per channel per tick and no empty ticks. Across the fixed
596-pair window, demo and player state match baseline at lag -1 in all pairs;
raw frames match in 561 pairs. Neither channel's audio hash matches at any of
the five tested offsets. Sample counts match at lag 0 in all 596 pairs, which
does not imply matching audio. Selected VBlank flag and FM3 target values remain
8 and 0 respectively; both named bytes match at every tested offset.

This reproduces a one-tick game-state shift without an audio-byte phase match
within the tested window. Boundary samples do not reveal an intermediate flag
write. The exact executed instruction and an audible effect remain unproven.
The next bounded investigation should distinguish VBlank flag set versus clear
using generic instruction/write-value metadata, only if existing hooks cannot
answer that question. It must preserve the fault model and repeat the same
observational-equivalence and pulse-budget checks.

## Evidence limits

Generated-sample hashes do not establish what a person hears. Named state and
phase differences do not prove causality, physical electrical behaviour, exact
executed PC, healthy gameplay or sustained trajectory divergence. Preserve all
prior JSON and public artifacts. Never publish the cartridge, RAM dumps, raw
samples, game captures or local private paths. Node testing is separate from
native Mac Firefox acceptance.
