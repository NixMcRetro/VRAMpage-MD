# v0.2 logic bending: work RAM

**Status:** experimental runtime integration is implemented and the actual rebuilt
WASM passes nine original-cartridge checks. Genuine-game observations are recorded
separately below; physical validation remains pending. The C model has byte and word operations;
core hooks cover CPU data/fetch accesses, VDP DMA reads and Z80 bank byte
accesses. A separate RAM panel, CPU status monitor and experiment metadata export
are available. Do not treat model output as a physical electrical result.

## Pinned emulator map and transaction paths

This work targets pinned `wasm-genplus` revision
[`6090aff9`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674).
In Genesis mode, [`genesis.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L49-L50)
declares a 64 KiB `work_ram` array, and its
[main-CPU map](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L101-L112)
maps the `$E00000–$FFFFFF` window to that array. Every 64 KiB page shares the
same backing array and uses the low 16 address bits. This documents the emulator
map; it does not verify a physical RAM chip pinout or a particular Model 1 board.

The integration covers the paths that can touch this RAM: 68000 byte, word and
longword data operations; immediate instruction and PC-relative fetches; VDP DMA
reads; and byte accesses through the Z80 bank window. The pinned Genesis map
allows Z80 writes to work RAM while its bank read map returns an unused-read
handler; integration must preserve this existing no-fault behavior. This matters
because the pinned core has direct mapped-memory paths in its
[68000 handlers and fetch macros](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.h#L526-L535),
its [DMA reader](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L3041-L3072),
and a [separate Z80 bank path](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/memz80.c#L121-L192).
Integration tests must show which transaction paths are covered and that an
unfaulted RAM access still returns or stores the same value.

## Digital bus approximation

The transaction implementation is in
[`scripts/work_ram_fault.h`](../scripts/work_ram_fault.h) and
[`scripts/work_ram_fault.c`](../scripts/work_ram_fault.c), with core hooks in
[`scripts/work_ram_runtime.h`](../scripts/work_ram_runtime.h) and
[`scripts/work_ram_runtime.c`](../scripts/work_ram_runtime.c). It models a 64 KiB
big-endian byte array and accepts byte and word transactions. Its abstract
address inputs are A1–A15, represented as word-address bits WA0–WA14; CPU A0
selects the byte lane and is preserved by address faults. Its data inputs are
D0–D15. These signal names describe the digital model, not verified physical
connections on a Sega motherboard.

The MC68000's big-endian bus convention places the upper byte on
D15–D8 at an even byte address and the lower byte on D7–D0 at an odd address.
The pinned core's byte helpers implement that lane selection in
[`macros.h`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/macros.h#L1-L32);
see also Motorola's [M68000 Family User's Manual](https://www.nxp.com/docs/en/reference-manual/M68000UM.pdf).
The model follows this convention but does not simulate UDS/LDS electrical
timing, partially driven buses, or a physical SRAM package.

One pair of address or data bits may be selected at a time. The model applies an
explicit low-dominant rule: if either bit in a connected pair is zero, both are
projected to zero for the selected transaction. A short can affect reads,
writes, or both. A read fault changes the mapped word or returned data without
mutating RAM. A faulted write can redirect an address or store a changed value;
clearing the fault does not undo that stored change. This is persistent state in
the emulator's RAM array, not permanent damage to physical memory.

For byte data accesses, a connected pair must lie within the lane selected by
the byte address. The byte API returns `WORK_RAM_FAULT_UNSUPPORTED_LANE` without
changing memory for a cross-lane pair, and the runtime/UI rejects cross-lane data
pairs for the whole RAM fault domain. Word transactions can represent any pair
on D0–D15. This restriction is a consistency rule for this digital model; it is
not a claim that cross-lane electrical shorts cannot occur.

## Controls, monitor, and experiment record

The work-RAM controls are kept separate from the existing VRAM patchbay. Only
one fault domain is active at a time, so a RAM experiment cannot silently run
alongside the frame-scoped VRAM approximation. The collapsible RAM panel selects
an address or data pair and read, write, or both directions; selecting a pair
does not apply it until **Apply RAM fault** is pressed. The monitor shows
affected read/write counts, the model frame and activation frame, plus the
emulated CPU STOP/HALT flags. It never automatically rescues a stopped game. Explicit v0.2.1
[CPU recovery](CPU-RECOVERY.md) can attempt resume/reset while preserving RAM. The
JSON export records model version, pinned core revision, ROM filename and
SHA-256, fault setup, activation/current frame, reset state, counters and CPU
flags. It contains no ROM or RAM bytes. Disconnect preserves the last experiment's
counts for export; applying a new fault or clean-restarting starts fresh counters.

The controls pass six synthetic Chromium tests and an actual-core cartridge
smoke test. A passing digital transaction test establishes the selected projection
rule only; it does not establish analogue bus contention, a physical pin map, or
a predictable Sonic outcome. See [the experiment procedure](EXPERIMENTS.md).

## Scope and remaining acceptance work

- Actual WASM tests cover CPU byte/word/long transfers, read/write address faults,
  byte-lane data faults, RAM instruction and PC-relative fetches, VDP DMA,
  disconnect persistence and restart counters. Z80 bank hooks are patch-tested
  and native-adapter-tested; actual Z80 instruction execution remains untested.
- Read-only source integrity and persistent writes after disconnect pass actual
  WASM assertions. Clean restart clears configuration/counters.
- Chromium 1366×768 actual-core smoke covers cartridge loading, RAM application,
  disconnect, SHA-256 metadata export and clean restart. Native macOS acceptance
  and real-game Firefox/WebKit checks remain outstanding.
- Keep the existing VRAM fault model frame-scoped. Only work-RAM faults use the
  new transaction-level model.
- Establish the exact NTSC Model 1 board revision and cite board-level pinout
  evidence before making any physical pin-fidelity claim.

No ROM bytes, RAM dumps, or game-derived screenshots belong in the repository.

The pinned core enables data address-error handling but disables PC address-error
checking. Active word projections assume aligned accesses; behavior after a fault
creates an odd instruction PC is not a validated hardware outcome. STOP/HALT flags
do not detect every exception, hang or invalid game state.

## v0.2.3 transaction cutoff and longword correction

[Affected-write pulses](ACCESS-LIMITED-PULSES.md) release the RAM fault after a
selected number of changed write transactions or at the next frame boundary.
The related regression uncovered/fixed a missing first-half longword write hook.
Earlier claims of complete longword fault coverage were too broad: the original
WASM checks exercised no-fault longwords, not both faulted halves. Current
original-cartridge checks assert both halves and a cutoff between them.

## Independent address-line omission

v0.2.4 adds an [address-line chip view](ADDRESS-LINE-CHIP.md). Its multiple-line
mask forces selected address bits low, separately from bridging a pair. A0 is
preserved for byte lanes, reads do not mutate storage, and aliased writes
persist. This is a deterministic stuck-low approximation of omitted inputs,
not a model of floating disconnected wires or a verified physical pinout.
