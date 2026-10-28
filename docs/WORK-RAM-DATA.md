# Work RAM Data Lines

The development runtime adds deterministic D0–D15 stuck-low masks. The reference
is Sega's documented PAL Model 1 VA6.5 two-device Work RAM circuit: IC2 carries
VD0–VD7 and IC3 VD8–VD15. See the [primary-source map](SEGA-MANUAL-EVIDENCE.md#verified-pal-va65-reference-topology).
This is sufficient for a useful digital model; exact NTSC VA6 validation in
[#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73) is optional follow-up.

Choose **Data** under **SRAM (Work RAM)**, select **Read**, **Write** or
**Read + Write**, then click
the data legs. Any combination across both bytes can be forced low. **Reconnect
All D Lines** removes the mask; previously corrupted writes remain in memory.
**Address** restores the existing address view without changing the fault.
Only one Work RAM address mask, data mask or bridge pair is active at a time.
**Bridge Pair** uses the existing low-dominant bridge, restricted to either
D0–D7 or D8–D15; cross-byte bridges are rejected without changing the fault.

The 68000 bus is big-endian: an even byte accesses D8–D15; an odd byte accesses
D0–D7. A word applies both bytes, and a longword follows two word transactions.
Read, Write and Read + Write modes retain the existing access rules. Counters
count changed bus transactions, not changed bits. DMA and Z80 accesses reuse
the existing Work RAM hooks. RAM and VRAM faults remain mutually exclusive;
sound-chip and independent Z80 RAM faults retain their existing coexistence rules.

The optional runtime API is `_set_logic_data_mask(mask, access)` and
`_get_logic_data_mask()`. Masks are integers 0–65535, access is 1/2/3, and zero
clears. Invalid calls preserve the previous configuration. Existing accepted RAM
setters clear a data mask. Disconnect, CPU Reset, Force Resume and Clean Restart
reuse their established lifecycle; CPU Reset preserves the checkpoint and sound
state. Circuit schema 5 saves stable masks and imports versions 1–4. Exports
include the observed mask and `model1-pal-va65-two-byte-v1` reference identity;
unavailable legacy observations compare as Unknown.

Acceptance covers literal low/high byte and word/longword results, directions,
counter/trace semantics, invalid-call atomicity, replacement and recovery in
native/sanitized and actual-WASM tests. Browser tests cover controls, keyboard
access, configuration round-trips, legacy capability rejection before mutation,
uncertain setter/getter outcomes and compact layouts. Integration requires the
full applicable suites, independent specialist review and passing PR/main CI.

The unchanged normal core lacks this optional mask API; byte-local bridges remain
available. No new ROM, public release or website deployment accompanies this slice.
Cuts approximate a disconnected input as stuck low; they do not predict floating
voltages, contention, refresh failure or physical short-circuit behavior. Region
clock selection does not establish a motherboard revision. Add a physical model
selector only when a second evidenced model has meaningful implemented differences.
