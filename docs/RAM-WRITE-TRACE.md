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
