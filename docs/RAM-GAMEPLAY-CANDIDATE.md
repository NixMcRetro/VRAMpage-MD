# Bounded object-memory alias experiment

## Objective and hypothesis

The prior [wait-sequence experiment](VBLANK-WAIT-SEQUENCE.md) explains the
A10/A11 one-write result as a one-tick wait delay. It does not establish genuine
trajectory divergence. This follow-up selects one source-backed candidate, not
an undirected sweep: a low-dominant A12/A13 write contact for one affected write.

Use the unchanged public v0.2.7 core and the existing supported private cartridge.
The pinned s1disasm source at `15dfa3a6ee4c53aeb482233e493755c84b4f3479`, built
with Revision 0 and default fixes/cheats/optimizations disabled, matches cartridge
SHA-256 `46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
No cartridge, generated disassembly build, RAM dump or capture is published.

The generic RAM model indexes CPU address lines A1 through A15 from zero. The
selected API call is `_arm_logic_write_pulse(1, 11, 12, 1)`, immediately before
tick 1801, at completed frame 1800. It preserves `$F62A` and `$FFxx` stack offsets
because both selected byte-address bits are high there. It redirects object
memory in `$D000` through `$EFFF` into `$C000` through `$CFFF`. The actual first
affected write must be measured; a one-write pulse can be consumed before any
player position or velocity update. Do not treat the source hypothesis as an
observed target.

The source allocates object space at `$D000`, with 128 slots of 64 bytes. Player
slot zero has fixed-point position at offsets `$08`/`$0C` and signed velocity at
`$10`/`$12`. A natural object-memory write redirected by a generic bus fault may
change subsequent gameplay. No experiment writes those game variables directly,
changes game instructions, targets a specific variable in the fault model, or
silently restarts the CPU.

## Defined acceptance before execution

- Keep the original observer's default scenarios, protocol and recorded JSON
  unchanged. Reuse its bounded driver through a validated, separately named
  configured-write-pulse entry point. Preserve the public API's 1 to 1024 budget.
- Use six fresh public cores: baseline and candidate, each with tracing disabled,
  enabled and enabled again. Preserve equivalent reset, prefault observations,
  zero host input for 2400 ticks, exact one-write release, trace noninterference
  and deterministic repeats.
- Record scalar first-write metadata and compare it with the generic mapping.
  Distinguish an object-region alias, a player-field alias and an unrelated first
  write. Do not increase the budget after seeing an inconvenient result.
- Record CPU STOP/HALT flags after the activation tick (ticks 1802 through
  2400), and player identity across the retained timeline (1799 through 2400).
  Require an active
  demo with continued internal cursor/input progression for a positive result.
  Frozen or stopped execution is a negative outcome, not a recovery opportunity.
- Reuse ticks 1803 through 2398 and offsets -2 through +2. Require exactly one complete
  demo-aligned comparison (596 matching demo tuples and no missing pairs),
  then measure residual player position differences. Multiple matching offsets
  are ambiguous and do not qualify. Require player object ID 1 throughout both
  comparison windows.
  The predefined operational threshold for bounded trajectory divergence is at
  least one pixel of position difference for at least 60 consecutive ticks at
  that unique demo-aligned offset. Positions retain the existing unsigned 16.16
  representation. Compute each axis delta as a wrap-aware signed 32-bit
  difference between those unsigned values; the maximum absolute axis delta
  must be at least 65536 raw units. A whole-sequence timing shift does not qualify.
- Separate valid experimental execution from scientific success. A repeatable
  negative result is useful evidence. Never weaken the acceptance after a run.
- Publish only scalar summaries, selected samples and hashes. Keep full timelines,
  raw ROM/RAM/audio, frames, opcode bytes and private paths out of the record.

This threshold supports a bounded observation on one cartridge/core revision.
It does not establish physical electrical accuracy, whole-game equivalence,
audible differences or native Mac Firefox acceptance. No application version,
normal emulator API or downloadable package change is planned.
