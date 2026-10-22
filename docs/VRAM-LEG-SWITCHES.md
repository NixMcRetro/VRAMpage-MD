# v0.2.5 VRAM leg switches

Load a cartridge, then click any AD0–AD7 leg in the VRAM chip diagram. A **×**
means that signal is forced low. Click it again to reconnect. Several legs can
be crossed simultaneously. Tab and Enter/Space work as well as the mouse;
pressed state and accessible labels describe the fault without relying on colour.
**Reconnect all [0]**, the 0 key, CPU recovery and Clean restart clear the mask.

Choose **Bridge two nets** to select two legs for the existing low-dominant
paired bridge. Presets 1–8 and Shift+1–8 contacts remain available in either
mode. Choosing a mode alone changes no active fault. Applying a bridge replaces
the mask, and toggling a leg replaces a bridge. Releasing a momentary bridge
never resurrects an old mask. VRAM faults and work-RAM faults remain exclusive;
a refused RAM disconnection prevents VRAM leg activation and preserves any armed
RAM pulse timer. Older cores without
the mask API automatically retain Bridge mode and explain why switches are unavailable.

## What disconnect means

This is the same explicit **stuck-low approximation** as the work-RAM UI, not
an analogue floating input and not removal of the whole VRAM chip. No electrical
noise, pull resistors or pin-voltage fidelity is claimed. Labels describe logical
multiplexed nets, not verified motherboard/package pin numbers.

The existing frame-scoped VRAM projection is unchanged in scope. This is an
incremental v0.2.x improvement; per-access VRAM remains the v0.3.0 milestone.
There is no graphical glitch filter or game-specific memory edit.

For mask M (0–255), bit i represents ADi. The modeled row phase maps AD0–AD7
to logical A2–A9. The column phase maps AD0/AD1 to A0/A1 and AD2–AD7 to A10–A15.
The logical clear mask is `(M << 2) | (M & 3) | ((M & 0xfc) << 8)`.
The projected address is `address & ~clearMask` within 16 bits.

A frame snapshots physical VRAM, projects reads through the address map and
reconciles changed logical bytes back into the snapshot. Collisions retain the
existing ascending-address reconciliation order. Reconnecting restores normal
addressing but does not undo faulted writes; the pattern cache is invalidated
when restoring normal addressing. Use Clean restart for a clean cartridge boot.

## API and exports

`set_vram_address_mask(mask)` returns 0 for masks 0–255, or 1 for invalid input
without changing the current fault. Zero reconnects all lines and clears bridges.
`get_vram_address_mask()` reports the current mask. Setting a paired short clears
the mask; setting a mask clears the pair. Native cartridge start clears both,
counters and cached projection state. The patcher refreshes an older embedded
VRAM patch safely and idempotently when rebuilding an existing vendor tree.

New exports retain RAM experiment fields and add `vramFault` (kind, addressMask,
line labels, bridge) and `vramAddressLineChanges` (frame, previous/new mask,
reason and pre-transition projected-difference/changed-byte counters). Loading
another cartridge or Clean restart clears that history. Counters are frame
projections, not individual transaction counts. A legacy core without frame
metadata records a null frame. No ROM or VRAM bytes are exported. Historical
JSON under docs/experiments remains unchanged. The existing `faultActive` field
continues to describe the RAM fault; use `vramFault.kind` for VRAM state.

## Verification and manual reproduction

Native tests exhaust every 16-bit address under all 256 masks and check pair
replacement, invalid input, reset, cache restoration, source integrity, collision
order and persistent writes. Actual-WASM original-cartridge tests exercise API
replacement/reset and VDP writes/readback after reconnect. Browser checks cover
mouse/keyboard crosses, multiple lines, reconnect, mode/bridge replacement,
RAM/pulse takeover, recovery/restart, export and old-core fallback.

On your Mac in Firefox: load your own cartridge, click AD0 and AD7, open Logic / work RAM and choose **Download experiment JSON**,
then reconnect AD0 only and confirm AD7 remains crossed. Try Reconnect all,
then Bridge mode/presets. Finally Clean restart. Changes in game behaviour are
not guaranteed; corruption and halted execution may persist after reconnection.
Native macOS, audible playback and physical electrical behaviour remain manual
or research acceptance checks. See [Testing](TESTING.md).
