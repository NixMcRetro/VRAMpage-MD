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

## Developer procedure

Use a clean committed checkout and the unchanged complete public v0.2.7 package.
The runner rejects mismatched source/version/core hashes before loading its JS.
Only the supported private cartridge fingerprint is accepted. No SDK or browser
installation is needed for this developer Node experiment.

```sh
node scripts/observe-ram-gameplay-candidate.cjs /private/path/sonic.md --app /path/to/extracted-public-v0.2.7 > /tmp/object-alias-result.json
```

An exit status of zero means the protocol integrity checks passed. Consult
`scientificOutcome.boundedTrajectoryDivergenceObserved` separately. A correctly
executed negative result must not be described as a positive experiment.
The JSON includes scoped tool hashes, commit identity, package/ROM fingerprints,
trace metadata, selected samples and phase summaries. Full timelines stay in
memory and are not serialized.

## Recorded negative result

The [immutable record](experiments/2026-10-23-object-alias-candidate-v1.json)
was collected from clean commit `f24697efb074dd598246425c4049903ae1b55de7`.
All six fresh-core execution, trace noninterference, repeat, prefault, zero-input
and exact one-write pulse gates passed. Independent specialist review approved the observer, trace invariants and
recorded evidence before integration.

| Observation | Measured result |
| --- | --- |
| First affected access | Byte write at CPU `$FFD022`, logical `$D022` to `$C022`, completed frame 1800 / effective tick 1801 |
| Source interpretation | Object alias, specifically the player slot's `obStatus` field at offset `$22`; not a position or velocity field |
| Pulse | Released after exactly one affected write at tick 1801 |
| Demo and CPU safety | Active demo and internal cursor/pad progression; zero CPU flags in the recorded 1802 through 2400 scope; player ID 1 throughout 1799 through 2400 |
| Unique demo-aligned offset | 0 ticks in both repeats |
| Compared frame/demo/player pairs | All 596 match baseline at offset 0 |
| One-pixel position difference | 0 ticks; longest qualifying run 0 |
| Bounded trajectory divergence | Not observed |

The object-region hypothesis was reached, but its predicted trajectory effect
was not. Do not infer an instruction or bit operation from the address-only
trace. This result does not exclude a transient effect before tick 1803, a later
effect after tick 2398, or an effect under different predetermined settings.
No raw frames, audible output, native Mac behaviour or physical hardware were
verified by this experiment.

The shared driver was also checked against the earlier immutable public-core
baseline and A10/A11 observations; both match exactly. The latter check used one
additional fresh actual-core trial, separate from the six candidate trials.
The next RAM-stage task is a separately defined, source-backed follow-up using
the observed status-write location and the generic pulse semantics. No larger
budget or different activation time was tried in this record.


## Subsequent follow-up

The separately predefined [eight-write follow-up](RAM-STATUS-FOLLOWUP.md) now
meets the bounded same-input-phase trajectory criterion. That positive result
does not change this one-write negative record or its original settings.
