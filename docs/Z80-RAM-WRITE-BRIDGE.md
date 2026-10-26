# Z80 RAM Write Bridge

**Development source only; off by default.** The published v0.5.0 and older
downloads are unchanged. This implements the bounded RAM proposal from
[Z80 research](Z80-RAM-RESEARCH.md), using the existing pinned emulator.
It does not inject bus-arbitration faults or claim physical pin accuracy.

## Controls

Load a cartridge, find **Z80 RAM Write** near **Randomiser** and **RAM Write**,
choose two distinct **Address A / Address B** lines A0–A12, then select
**Apply Bridge**. The bridge remains active until **Remove Bridge**, memory
fault recovery, **Disconnect All Faults**, **Clean Restart** or cartridge
replacement removes it. Editing the selectors prepares a new pair; it does
not change an applied pair. There is no timer, momentary mode or automatic
sound-driver repair in this first model.

These are local byte-address bits in the Z80's 8 KiB sound RAM. They are
separate from the main CPU's 64 KiB **SRAM (Work RAM)** and cartridge save RAM.
The new bridge can coexist with existing VRAM/Work RAM and FM/PSG settings.
The existing Work RAM/VRAM exclusion still applies to those two domains only.
Z80 RAM controls do not press or dim the Randomiser buttons.

## Write Rule and Scope

Model ID: `z80-ram-write-address-pair-v1`. After the original core has decoded
an allowed local-RAM store, reduce its address to 13 bits. For the selected
bits, high/high stays high/high; either low makes both low. Store the original
byte once at that mapped address. A0/A1 therefore map offsets 0, 1, 2, 3 to
0, 0, 0, 3. This is a write-only digital approximation. Reads and instruction
fetches are unmodified and observe the stored bytes, including damaged code.

Both Z80 stores at `$0000–$3FFF` (including the native 8 KiB mirror) and the
68000's granted RAM-window stores are covered. The native word-store high-byte
behavior and latency are preserved. Denied stores, FM/PSG/VDP input writes,
bank-register changes and banked main-RAM accesses are not redirected by this
model. Bus ownership and native reset wiring are unchanged.

Support is restricted to the runtime core's standalone Mega Drive/Genesis
system profile. Unsupported profiles cannot activate it; legacy/normal cores
without the optional API show unavailable controls. The normal core remains
the existing fallback.

## State, Exports and Failure Handling

`_set_z80_ram_bridge(1, a, b)` activates a pair; `(0, -1, -1)` removes it.
Inputs must be exact integers, with distinct active lines in 0–12. Rejected
requests preserve prior native settings and RAM. The state getter is
`_get_z80_ram_bridge_state()`:

| Field | Meaning |
| --- | --- |
| `modelVersion`, `supported`, `configured`, `effective`, `reason` | Model identity, profile support and actual runtime state. |
| `bridgeA`, `bridgeB` | Selected local address bits; −1 when disconnected. |
| `activationFrame` | Unsigned emulated frame of activation. |
| `ramWrites` | Eligible local-RAM stores while effective, including repeated values/addresses. |
| `changedAddresses` | Stores whose local destination address changed. |
| `z80Writes`, `m68kWrites` | Eligible stores attributed to each owner. |

The four write counters saturate at uint64 maximum and export as decimal
strings, preserving values above 2^53. A new applied pair or removal resets
these counters. No counters count denied or non-RAM stores. Experiment exports
record `z80RamFault` separately; old exports show unknown Z80 information in
comparison instead of invented zero measurements.

Circuit configuration **v3** adds `z80Ram: {"pair": [0, 12]}` or
`z80Ram: {"pair": null}`. Existing v1/v2 files remain importable with the new
bridge off. Preview remains inert, unchanged pairs preserve counters, and
unsupported requests fail before any domain mutation. After a partial setter
failure, emulation pauses and the actual/unknown domain state is reported.

## Removal and Recovery

Removing a bridge stops future aliased stores. It cannot undo earlier memory
changes or restore music. Export before removal to retain the counters.

- **CPU Reset** and **Force Resume** remove the new memory fault before acting
  on the 68000. They preserve Z80 RAM and existing sound-chip state at the
  intervention; subsequent game code can reload/reset its sound driver.
- A cartridge-requested **native Z80 reset** retains the RAM contact, counters
  and stored RAM; its original FM-reset behavior remains intact.
- **Clean Restart** reboots, clears faults/counters and discards the checkpoint.
- **Save Checkpoint** refuses an active/unverified RAM bridge. **Restore
  Checkpoint** verifies fault removal before loading and remains paused.
- **Disconnect All Faults** includes the new domain. It preserves run/pause
  after confirmed success and pauses incomplete or unverified clears.

Corrupted sound-driver code can halt or loop. This feature does not guarantee
game recovery, physical equivalence, or a particular audible result. Verification
uses original generated cartridges and automated PCM/memory observations;
real-board and audible listening checks remain separate.
