# v0.2 logic bending: work RAM foundation

**Status:** foundation in progress. The current C model is standalone; it is not
connected to the browser UI or emulated 68000. No Sonic-specific fault or gameplay
result is implemented or claimed.

## Pinned emulator memory map

This work targets the pinned `wasm-genplus` revision
[`6090aff9`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674).
In Genesis mode, [`genesis.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L49-L50)
declares `work_ram` as 64 KiB, and its
[main-CPU map](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L101-L112)
maps the `$E00000–$FFFFFF` window onto that array. Each 64 KiB page uses the
same backing array and the low 16 address bits, so this emulator map mirrors the
64 KiB store throughout that range. This describes the pinned emulator, not a
verified RAM chip pinout or a specific Model 1 motherboard revision.

The emulator's 68000 core has separate 8-, 16- and 32-bit access paths. Its
[normal read/write handlers](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.h#L842-L950)
can dispatch mapped callbacks or access the mapped backing array directly.
Immediate instruction and PC-relative reads also use
[direct memory macros](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.h#L526-L535).
VDP DMA reads work RAM directly in
[`vdp_ctrl.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L3041-L3072),
and the Z80 bank window has its own accesses in
[`memz80.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/memz80.c#L121-L192).
Runtime integration must account for these paths or clearly state which ones are
outside the experiment; a single new callback would not cover every read/write.

## Standalone transaction model

[`scripts/work_ram_fault.h`](../scripts/work_ram_fault.h) and
[`scripts/work_ram_fault.c`](../scripts/work_ram_fault.c) define a deterministic
foundation over a 64 KiB byte array. The API accepts aligned 16-bit word
transactions and stores bytes in big-endian order. In this model's naming,
address lines 0–14 represent CPU A1–A15, the word-address bits WA0–WA14; data
lines 0–15 represent D0–D15. These are model inputs, not a claim that the
physical RAM package has been traced to those signals.

One pair of address lines or data lines may be bridged at a time. A bridge uses
a low-dominant rule: if either modeled bit is low, both connected bits are forced
low in the projected address or data value for that selected operation. Address faults can apply to reads, writes or both;
data faults have the same operation choices. A read fault changes which word is read or the value returned, and leaves
backing RAM untouched. A projected write
can redirect an address or alter stored data, so its memory effect remains after
the caller clears the fault. Clearing a fault does not roll back earlier writes. This models persistent
stored-byte corruption, not permanent electrical damage to a physical RAM chip.

The word-transaction layer is a testable foundation, not a completed runtime
model. Byte-lane accesses, odd/misaligned accesses, instruction-fetch behavior,
CPU fault statistics and the browser patchbay are not integrated. The emulator's
byte-lane and endian conventions are handled in its
[core macros](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/macros.h#L1-L32);
integration must preserve those semantics and the 68000's address-error behavior.
Reset and power-on RAM initialization also need explicit handling rather than
being inferred from the standalone API.

## Planned Sonic experiment and acceptance

The v0.2 goal is to compare a normal attract-mode replay with an otherwise
unchanged game under a reproducible modeled RAM transaction fault. The model
must affect bus transactions, not edit Sonic variables or script a desired
screen effect. No pin pair is expected to produce a particular result, and no
gameplay result is available yet. Use a legally obtained local ROM; record its
title, region and SHA-256 fingerprint only, along with emulator revision, model
version, fault pair and direction, reset state, and activation frame. Never put
the ROM or game-derived screenshots in the repository.

Before calling v0.2 integrated, add tests for no-fault read/write identity,
address aliasing, read-only behavior, stored write effects after fault removal,
byte-lane preservation, CPU fetch and data paths, reset semantics, and any DMA or
Z80 access paths included in scope. Then run a genuine local-game comparison and
record what happened, including failures. Hardware pin fidelity remains
unverified until an exact board revision and supporting pinout evidence are
documented.
