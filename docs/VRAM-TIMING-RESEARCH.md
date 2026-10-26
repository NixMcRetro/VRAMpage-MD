# VRAM Serial Access and Scanline Timing Research

**Status: research, no timing-model implementation.** Follow-up to
[#74](https://github.com/NixMcRetro/VRAMpage-MD/issues/74), inspected
27 October 2026 (Sydney). Logical transactions and cache coherence already
shipped in v0.3.0. Retain both public Frame and Transaction modes. A physical
serial-port model needs evidence beyond the current logical mapper and the
inspected FPGA implementation.

## Primary Component Evidence

Hitachi's *HM53461 Series* datasheet
([13-page scan](https://radio-hobby.org/uploads/datasheet/161/hm53/hm53461p-10.pdf))
was visually inspected, including the block/pin diagrams, read-transfer,
write-transfer and serial-mode waveforms. It describes a 64K × 4 DRAM port
and a separate 256 × 4 serial-access memory (SAM). A0–A7 are multiplexed:
RAS selects a row and CAS selects a column. DT/OE controls transfers between
the RAM row and SAM; SC clocks serial access, with SOE controlling serial
output. Serial access and the DRAM-port operation have separate timing
constraints. A buffered row is therefore state, not simply a new random-port
lookup for every displayed pixel.

This establishes component capabilities. It does not establish a particular
VA6's fitted VRAM, the VDP's exact row/column bit permutation, transfer phase,
serial tap sequence, or behavior of physically cut/shorted driven nets. The
existing mapping in `scripts/vram_fault_patch.c` uses row bits A2–A9 and column
bits A0/A1/A10–A15; that project assumption is not independently proven by a
generic memory datasheet. Do not turn it into a measured board pinout.

## Inspected HDL Revision and Its Boundary

Inspected `MiSTer-devel/Genesis_MiSTer` revision
[`adc0c42cfb1fa5d484cc8566767f7d68982bc44a`](https://github.com/MiSTer-devel/Genesis_MiSTer/tree/adc0c42cfb1fa5d484cc8566767f7d68982bc44a)
(commit dated 24 February 2023). This is the specific inspected revision, not a
claim about every MiSTer release or the original VDP silicon. Credits and
license remain with Gregory Estrade, Till Harbaum, Alexey Melnikov and the
other upstream contributors named in those files. No HDL is copied here.

| HDL Location | Observed Implementation | What It Can Establish |
| --- | --- | --- |
| [`rtl/system.sv`, VRAM blocks](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/system.sv#L332-L402) | Four byte-wide `dpram #(14)` instances provide 64 KiB, with a 16-bit transfer interface and a separate 32-bit render interface. Request acknowledgements are registered. | Storage/handshake choices; this is not an external HM53461 RAS/CAS/SC waveform. |
| [`rtl/vdp.vhd`, render arbitration](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L941-L1047) | A 32-bit request arbiter selects SP3, SP2, horizontal scroll, Plane A, then Plane B when their respective conditions hold, and latches returned data. | Ordering and buffering in this HDL; priority alone is not a measured physical fetch schedule. |
| [`vdp.vhd`, counters/slots](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L2286-L2512) | H/V counters generate display-dependent FIFO opportunities, refresh exclusions, name/sprite engine enables and next-line `PRE_Y`. H32/H40 differ. | Access opportunities depend on raster state; whole-line rendering cannot express every such ordering. Upstream explicitly notes uncertainty around border/blanking slots. |
| [`vdp.vhd`, FIFO/data transfer](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L3050-L3198) | Four-entry FIFO bookkeeping, queued addresses/data, delayed completion and odd-address byte swapping. A 16-bit normal VRAM transfer skips the next FIFO slot to account for original 8-bit bandwidth. | Useful reference for transfer ordering; a native physical byte pair is not represented as two independent RAM-chip waveforms here. |
| [`system.sv`, speed selection](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/system.sv#L440-L456) | `FAST_FIFO` / `TURBO` can bypass normal FIFO throttling through `VRAM_SPEED`. | Any comparison must record these settings; accelerated output is not a hardware timing oracle. |

The HDL is valuable comparative evidence, but copying its RAM storage or
slot constants would not supply the missing physical serial-buffer evidence.
No HDL simulation or hardware trace capture was performed for this report.

## Comparison With the Current Emulator

The pinned Genesis Plus GX source is
[`h1romas4/wasm-genplus@6090aff9e9b2f578cd28882bd4571d2e35b1d674`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674).
Its active-display loop in
[`system.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/system.c#L588-L641)
updates DMA, renders a scanline and then runs the CPUs to the line boundary.
Other register/port paths can redraw lines, so this is the main schedule,
not a claim that `render_line` is called exactly once under all conditions.

[`vdp_68k_data_w_m5`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2368-L2428)
accounts for FIFO capacity/stalls, then calls `vdp_bus_w`, which updates VRAM,
SAT and dirty-pattern state at that software call. It does not defer each
backing-byte change until a later physical DRAM write strobe. The renderer
uses decoded patterns and table reads at its own call sites:
[`vdp_render.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c#L3940-L4158).
Retaining FIFO timing accounting therefore does not imply physical commit or
pixel-fetch timing.

The delivered [logical transaction contract](TRANSACTION-VRAM-SEMANTICS.md)
maps bytes at these existing software boundaries and maintains alias-aware
cache coherence. It has no separate SAM row, tap pointer or transfer event.
Settings change between synchronous whole-frame ticks; the UI cannot currently
place a contact edge at an arbitrary pixel inside a frame.

| Gap | Likely Observable Effect, Not Yet a Hardware Result |
| --- | --- |
| No persistent SAM snapshot / independent transfer event | A later DRAM write or changed contact may become visible at a different time than serial output from an already-buffered row. A RAM read and a displayed pixel can legitimately disagree until refill. |
| Fault remapping at logical reads rather than separate RAS/CAS/transfer phases | A contact could affect a latched row, column/tap selection or a later transfer differently. Applying both modelled phases on every logical read cannot distinguish them. |
| Whole-line cache/render reads | Mid-line changes can affect a whole rendered region or a later line instead of the particular future fetches. Cache correctness does not determine beam timing. |
| Native software write vs physical FIFO completion | A read, render fetch or contact edge near a queued write can observe a different ordering, even when FIFO status and final memory agree. |
| Sprite parsing, internal SAT and next-line work | Already-latched sprite fields may outlive changed VRAM; a redraw cannot automatically stand in for a physical sprite-fetch pipeline. |

## Bounded Fixtures Before Any Implementation

Use original generated cartridges and literal expected bytes/pixels. Keep
component-level tests, HDL comparisons and physical traces labelled separately.

1. **SAM component oracle.** Initialize two distinct 256-nibble rows. Transfer
   row R at a specified tap, clock a recorded count, write a different value to
   DRAM R and continue serial reads. The expected buffer stays at the
   transferred values until the next legal read-transfer. Cover tap 255 wrap,
   row replacement and documented transfer/SC boundaries. Derive expectations
   from the selected device's waveform; this is not yet a VDP fixture.
2. **Phase-separated contact.** Hold the sampled row fixed, change column/tap
   conditions, then reverse the experiment around a transfer event. Specify
   exact selected row, serial sequence and persistent DRAM bytes. No assumption
   that the same logical transform belongs on all three operations.
3. **FIFO ordering.** An original H32/H40 cartridge fills and drains the FIFO
   during active display and blanking, with distinguishable writes to one
   address. Record enqueue, native backing-store change, status/stall and any
   proposed commit event in master-clock units. Compare to the pinned HDL with
   fast FIFO/turbo disabled. Preserve native no-fault results before proposing
   a changed timing contract; HDL agreement alone cannot settle silicon.
4. **Raster boundary.** Generate known name/pattern/sprite rows and place
   instruction-timed writes before and after candidate fetch boundaries. Record
   H/V/cycle identity and literal expected affected pixels from independently
   established timing evidence. Include line −1, first/last active line,
   blanking, interlace and display enable transitions. Current frame-granular
   browser controls cannot serve as the event injector.
5. **Regression/performance.** Preserve exact inactive PCM/pixels, existing
   port/DMA byte lanes, SAT policy, counters, mode transitions and both public
   models. Run existing actual-WASM and three-browser gates, native sanitizers,
   and the unchanged paired renderer-performance gate if runtime work follows.

Tests 1–2 can establish a proposed component model. Tests 3–4 require an
explicit timing oracle before they can validate VDP fidelity. Do not adjust
expected images merely until a new renderer agrees with itself.

## Decision and Unresolved Claims

Complete the research follow-up with this source inventory and test plan;
defer a new physical/raster model. The independently useful next step, if
implementation is selected later, is a bounded developer trace of existing
FIFO/store/render ordering. It must answer a named discrepancy, not grow into
a second emulator or a permanent tracing framework.

Still unverified: fitted device and VDP revision on the target VA6, physical
address permutation, serial tap/transfer scheduling, contention behavior,
border/refresh edge cases, and changed pixels on real hardware. No claim of
cycle accuracy, fewer lockups or a particular game's glitch appearance follows
from this research. The current digital experiments remain valid within their
published model boundary; their immutable evidence is unchanged.
