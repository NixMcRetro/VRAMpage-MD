# First affected work-RAM write trace

v0.2.7 adds an optional developer diagnostic for the first changed work-RAM bus
write after fault activation. It does not change the fault model, rescue a CPU,
edit game-specific variables or add a browser control. Normal play leaves it off.

## Record and timing

Enable with `set_logic_write_trace_enabled(1)` after starting the cartridge.
The fixed record contains only the original 24-bit bus address, its 16-bit RAM
offset, mapped logical byte offset, bus width in bytes, completed-frame counter
and reason flags. Bit 0 means address remapping; bit 1 means data projection.
No RAM value, instruction bytes, ROM bytes or game capture is recorded.

The mapped offset is a logical 68000 byte offset, before the native byte-lane XOR.
A 32-bit operation uses two 16-bit bus cycles. The first changed cycle is recorded,
not the high-level instruction size. A one-write budget can release between
those cycles. A no-op projection does not create a record or spend write budget.

The frame field uses the same completed-frame counter as `get_logic_frame`.
During tick N the access sees N-1, because the counter increments after emulation.
This is not a cycle-accurate timestamp or a CPU instruction trace.

State 0 means empty, 1 is an internal capture-in-progress state, and 2 means a
completed record. Read getters only when state is 2. Enabling starts a new capture;
a new non-clear fault activation also clears the previous record. Clean restart
clears and disables tracing. Invalid enable values are rejected without change.
See the runtime header for exact lifecycle and disabling behaviour.

## Bounded private experiment

Build and package a committed v0.2.7 checkout using the documented release tools,
or extract its complete public download once published. From a developer checkout:

```sh
node scripts/trace-attract-write.cjs "/private/path/sonic.md" --app "/path/to/VRAMpage-MD" > /tmp/first-write.json
```

The runner accepts the same exact privately supplied cartridge fingerprint as
[the read-only observer](ATTRACT-MODE-OBSERVATIONS.md). It verifies matching
package manifests, version and WASM signature before loading the user-selected
local core. Unlike the immutable v0.2.6 observer, this diagnostic records actual
core hashes rather than claiming a pre-pinned binary profile. Use only a trusted
local package; manifest checks are not a signature or authenticity check.

Six fresh-core runs cover baseline and A10/A11 one-affected-write contact with
tracing disabled once and enabled twice. Every run uses zero external input for
2,400 ticks. The fault is armed after tick 1800, before tick 1801. There is no CPU
recovery. The original observer computes demo/player samples and timeline hashes;
raw timelines are not serialized. The runner checks exact traced/untraced and
repeat equivalence, and separately reports comparison with the historical v0.2.6
protocol-2 observation. A mismatch must be investigated, not ignored.

Output includes scalar samples, address metadata, hashes, source identity and
runtime settings. Keep the cartridge and all raw game data outside Git. Any
source-level interpretation of an address must cite the matching game revision;
an address alone does not prove the cause of gameplay divergence.

## Acceptance limits

Synthetic native and actual-WASM tests must establish unchanged memory, counters,
write budgets, byte lanes and longword cutoff. The real-cartridge comparison
checks diagnostic noninterference for this bounded experiment only. It does not
establish electrical accuracy, native macOS behaviour, audible output, continued
healthy gameplay for arbitrary faults or sustained attract-mode divergence.

## Recorded first-write result

[Exact six-trial record](experiments/2026-10-22-first-affected-write-v1.json)
uses committed source/tool `f0cc664d7b2bd22d5eaa03e5d00b02064236c678` and a
locally built complete review package from that commit. This is a pre-merge
review package, not a claim about a later public release binary. Tool source was
clean and both actual core hashes are in the record. Runner SHA-256:
`acbe20236e8ba94b8050fd02560bf255550e019f1a43dfb59bcdeac5f31a0ac5`.

Baseline tracing stayed empty. The A10/A11 pulse recorded the first affected
write in both enabled trials at CPU address `$FFF62A`, logical RAM offset
`$F62A`, mapped offset `$F22A`, bus width one byte and completed-frame counter
1800 (access during tick 1801). Reason bit 0 indicates address remapping. Exactly
one affected write was reported and the pulse released. No memory value is in
the record.

Both traced runs matched the untraced run in all monitored fields and timeline
hashes for each scenario. Both untraced observations matched the immutable
v0.2.6 protocol-2 record exactly. This supports noninterference in this bounded
experiment and localizes the changed bus access; it does not by itself identify
the game routine or prove sustained gameplay divergence. The phase-delay result
and RAM-stage acceptance limits remain unchanged.

Independent Luna High review reran all six trials and produced a byte-identical
record (SHA-256 `4789fc74fb3cfda95aa67d08f4b4ae413b65e97df4cbe9110f6b5459b0ff1f6c`).
## Corrected source interpretation

The original generic trace and six-trial JSON remain valid and unchanged. The
previous living-document claim that `$F62A` was `v_spritetablebuffer + $4A` was
wrong. Do not use that annotation as experimental evidence.

At pinned public [s1disasm source](https://github.com/sonicretro/s1disasm/tree/15dfa3a6ee4c53aeb482233e493755c84b4f3479),
`_Variables.asm` places `v_gamemode` at `$F600` and `v_vblank_routine` at
`$F600 + $2A = $F62A`. The sprite-table buffer is `$F800`, not `$F5E0`.
The sound-driver allocation must include the `$220`-byte `v_1up_ram_copy`;
`SMPS_RAM` totals `$5C0`, followed by `$40` unused bytes before game mode.
The separate target calculation remains `$F000 + $40 + 10 * $30 + $A = $F22A`,
the `AMSFMSPan` byte of the first FM3 sound-effects track. New literal fixtures
must distinguish `$F62A` from sprite-entry `$F84A` and verify the full allocation.

In `sonic.asm`, `Level_MainLoop` sets the VBlank routine flag to 8 and calls
`WaitForVBlank`, which loops until the flag is zero. The VBlank handler copies
the flag, clears it, dispatches work and updates music. Both setting and clearing
the flag are candidate writes to the observed address. Redirecting a clear could
leave the wait condition set for an additional frame. The address trace does not
record the CPU PC or written value, so it does not establish the exact executed
instruction or prove that mechanism.

## Bounded developer protocol

Use the same one-write scenario with repeated fresh-core baseline/fault trials,
zero host input and no CPU recovery. Retain phase-aligned player/demo/raw-frame
observations. Add per-tick audio sample counts and left/right hashes plus
source-verified named VBlank and target state, without serializing raw samples,
RAM dumps, protected captures, local paths or full timelines.

Compare complete fixed windows at same tick and nearby lags, report missing and
zero-sample pairs explicitly, and require matching pre-fault observations and
repeats. Audio can retain its timing while game logic is delayed: the source
updates music even along its lag-frame path. Residual hashes or named state alone
do not prove an audible effect or causality. Do not reuse the older sweep's
post-contact force-resume behaviour, add an audio fault model or change game code.

Keep the immutable v0.2.6 observer, published v0.2.7 binary and all earlier records
unchanged. Developer observation tools use separate tool/protocol provenance.
