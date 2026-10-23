# Transaction-level VRAM architecture and test plan

**Status:** architecture plan with [reviewed semantics](TRANSACTION-VRAM-SEMANTICS.md). No VDP runtime or application changes are part of this
plan. The reviewed base is `2fa2845c99941ecefcbd1de598eab25391b411fb`, after
the bounded RAM trajectory acceptance. `VERSION` remains `0.2.7`; a completed
transaction-level VRAM milestone is reserved for `0.3.0` by
[versioning policy](VERSIONING.md).

## Purpose and fidelity boundary

The current AD0-AD7 controls use a frame projection. A future transaction model
should apply the deterministic address fault at each supported VDP VRAM
operation, with the core's existing FIFO, address increment, byte order, DMA
schedule, sprite-table mirror, renderer and cache behavior retained around that
operation. This is a digital address-remapping approximation. It is not a
cycle-accurate VDP, a model of contention between driven electrical nets, or a
model of analog, floating-pin or board behavior.

The scope must name its access boundary. Genesis Plus GX has real CPU-port and
DMA access functions, but its renderer is not a sequence of beam-timed external
VRAM transactions. `render_line()` renders a whole line when called, reads some
tables directly, and uses a decoded tile cache. A transaction wrapper can make
those software reads observe a mapped logical address at the core's current
render point. That still does not reproduce the exact pixel fetch cycle,
mid-scanline bus arbitration or a physical DRAM row/column waveform. The
milestone and UI must say which logical render reads are routed through the
fault and must not call that electrical or raster-fetch accuracy.

## Source map at the pinned core

The inspected source is `h1romas4/wasm-genplus` commit
[`6090aff9e9b2f578cd28882bd4571d2e35b1d674`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674),
which vendors Genesis Plus GX code. The local vendor checkout is that revision;
its working tree contains the existing RAM/WASM patch and generated build
outputs, so source claims below refer to the pinned commit's source files and
functions, not those local modifications.

| Path | Pinned source evidence | Design consequence |
|---|---|---|
| Main 68000 VDP mapping | [`genesis.c`, Genesis memory map](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L90-L99) maps `$C0/$C8/$D0/$D8` port windows to `vdp_read_byte/word` and `vdp_write_byte/word`. [`mem68k.c`, handlers](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/mem68k.c#L1132-L1315) distinguish DATA, CTRL, HVC, PSG and TEST ports. | Enter VRAM logic only after the port command selects VRAM. Do not bend register, HVC, CRAM, VSRAM, PSG or invalid-port behavior. Byte writes duplicate the byte across a word in these handlers. |
| 68000 data reads and writes | [`vdp_ctrl.c`, `vdp_68k_data_w_m5`, `vdp_68k_data_r_m5` and `vdp_bus_w`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2124-L2174) use an internal data path, byte swap on odd address, FIFO bookkeeping, SAT interception, VRAM store and `MARK_BG_DIRTY`. The M5 read path reads an aligned word or an undocumented adjacent byte and advances `addr` by register 15: [`vdp_ctrl.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2369-L2550). | Wrap the VRAM address operation at the byte-lane boundary and retain word/byte ordering, FIFO and address increment behavior. The [FIFO comment at lines 823-826](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L823-L826) states that a word write consumes two byte access slots. Test byte and word ports independently. |
| Z80 VDP data port | [`memz80.c`, Z80 memory handlers](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/memz80.c#L100-L200) routes `$7F00-$7FFF` through the VDP map. [`vdp_ctrl.c`, Z80 M5 data handlers](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2610-L2786) directly reads and writes VRAM bytes and increments the VDP address. | Include Z80-originated VDP reads and writes in the inventory; preserve their byte lane and their distinct address increment. They are separate from the Z80 banked access to 68000 memory. |
| DMA scheduling and entry | [`vdp_dma_update`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L575-L686) computes transfer allowance from cycles, active/blank display and width, freezes the 68000 for bus DMA, and dispatches a mode-specific handler. | Never replace the scheduler or turn a scheduled partial transfer into a full-frame loop. The address fault belongs at the VRAM endpoint of each dispatched operation. |
| DMA sources to VDP | [`vdp_dma_68k_ext`, `vdp_dma_68k_ram`, `vdp_dma_68k_io`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2980-L3091) read external, internal and I/O-window source words and pass destination words to `vdp_bus_w`. | Keep the source-side 68000 bus semantics unchanged. Map the destination only when the VDP command selects VRAM. At this pin, handler dispatch separates external, internal-RAM and I/O sources; the internal-RAM/I/O handlers do not forward VDP source windows to VDP data ports. Preserve that existing source behavior. |
| VRAM copy and fill DMA | [`vdp_dma_copy` and `vdp_dma_fill`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L3093-L3175) access `vram[]` directly, maintain the internal SAT copy, mark tile-cache rows dirty and increment addresses per byte. | These direct paths bypass `vdp_bus_w`; add explicit source and destination VRAM accessors. Copy source reads and destination writes are separate operations. Do not apply the mask to DMA source addresses outside VRAM. |
| Renderer and pattern cache | [`render_line`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c#L4107-L4135) updates dirty patterns before rendering BG and sprites. [`update_bg_pattern_cache_m5`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c#L3940-L3997) reads pattern bytes from VRAM; Mode 5 renderers also directly read name tables and scroll tables, for example [`render_bg_m5`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c#L1509-L1660). Sprite parsing uses VRAM and an internal SAT mirror. | Audit every direct `vram[]` read in `vdp_render.c` and the VDP control code before claiming render-read coverage. Route the chosen logical table, pattern and sprite reads through accessors, invalidate decoded cache entries after mapped writes or mask changes, and make the SAT mirror follow the mapped physical destination. Validate this policy with synthetic cases. Batched line rendering remains batched and is not a beam-timed fetch model. |

The code uses Mode 4 paths as well as Mode 5. The application targets Genesis Mode 5, but the patcher modifies a shared emulator source tree. Future implementation must either cover the relevant Mode 4 and compatibility paths with no-fault tests or fail closed outside its documented target; it must not accidentally apply a Mega Drive-specific address transform to unrelated VDP families.

## Existing frame model and migration

[`scripts/vram_fault_patch.c`](../scripts/vram_fault_patch.c) inserts
`bend_before_frame()` and `bend_after_frame()` around `system_frame_gen(0)` in
the WASM `tick()` hook added by [`scripts/patch_core.py`](../scripts/patch_core.py).
Before a frame it snapshots 64 KiB of VRAM, maps every logical byte into a
projected array and invalidates all 2,048 pattern names. After the frame it
compares all 64 KiB against that projection, reconciles changed logical bytes
to the snapshot in ascending address order, restores the physical byte array
and leaves cache restoration pending. This detects net frame changes, not
individual accesses. Reads/writes counters report projection differences, not
transaction counts. Reconnection preserves writes already reconciled into
physical VRAM.

A per-operation implementation removes the full-VRAM projection from each
active frame and changes faulted-frame outcomes: access order matters, reads
can alias writes made earlier in the same frame, and repeated or colliding
writes are handled at their actual software call sites rather than reconstructed
from a final diff. Treat these results as a new model and protocol.

Keep the shipped `0.2.7` package and its frame model untouched. For a future
`0.3.0` build, retain a no-fault default and expose the transaction model under
an explicit model/capability identifier. Do not silently reinterpret the
existing `_set_vram_short` or `_set_vram_address_mask` controls or the old
projection counters. Keep the frame model available behind an explicitly named
legacy mode for comparison during migration, or document and version an
intentional removal in `0.3.0`; the reviewed semantics retain legacy controls and require explicit selection of the new model. Name
new diagnostics as transaction counts or mapped-operation counts, and keep
legacy frame-difference counters distinct. In all modes, disconnecting a fault
restores normal address lookup but does not undo VRAM mutations. Clean restart
must clear fault configuration and counters after the core reset, invalidate
derived caches, and prevent state leaking between cartridges. Preserve current
RAM/VRAM exclusivity and failed-takeover behavior.

## Proposed access architecture

1. Add a small pinned-source helper with an explicit supported VDP/mode check,
   `map_vram_address(logical)`, and byte read/write primitives over the existing
   `vram[0x10000]` backing. Map within 16 bits and document wrap behavior. A
   fault-off read/write must take the original direct path or prove equivalent
   output and side effects. Keep the selected mask immutable during one core
   operation; setters run between synchronous `tick()` calls.
2. Route 68000 and Z80 data-port reads/writes through the helper only for VRAM
   command codes. Preserve port behavior, address progression, status/FIFO
   timing, mode-specific byte ordering and existing VDP bus cycle bookkeeping.
   The current model is low-dominant: paired nets preserve high/high and low/low; if either net is low,
   both mapped bits become low; a mask clears the modeled row and column address bits. It does not
   model contention strength, floating lines, open bus, data-line faults or
   analog voltages. The row/column mapping follows the current logical model in
   `bend_map`, not a new physical measurement.
3. Route the VDP VRAM access in every DMA mode. 68K-source DMA keeps its source
   bus read and maps the VDP destination; copy maps its VRAM source read and
   destination write; fill maps each VRAM destination byte. Preserve transfer
   counts, cycle timing, DMA busy/frozen flags, register updates, `reg[15]`
   increments, wrap and SAT side effects. A transaction log or counters must
   not invoke a second memory access.
4. Route renderer VRAM reads at the existing logical access sites, including
   Mode 5 pattern decode, name/scroll table loads, sprite-table accesses and
   other audited direct reads. Define cache keys and invalidation together: if decoded tiles remain keyed
   by logical addresses, invalidate every logical tile/row whose mapped source
   includes a written physical byte. Marking only the physical pattern dirty is
   insufficient when multiple logical tiles alias that byte. Alternatively,
   prove a canonical physical-key cache design preserves all mapped reads.
   Resolve this choice before implementation and test reverse dependencies. On mask change, invalidate the affected patterns at minimum; a
   full invalidation is acceptable for a setting transition but not every
   frame. Keep line rendering and pixel fetch timing limitations visible in
   the model label.
5. Keep `vram[]` as the sole persistent physical store. Do not write a whole
   projected image before/after frame generation, shadow the complete VRAM
   per tick, alter game variables, or recover/restart the CPU to hide a bad
   state. A small access trace for tests may record direction, logical and
   mapped byte address, width, origin class and count, but must omit data values
   from user exports and be disabled in production unless explicitly needed.

## Measurable acceptance gates

### Pure/native access engine

- Compile strict C and run AddressSanitizer and UndefinedBehaviorSanitizer.
- Exhaust all 65,536 logical byte addresses for every 8-bit AD mask. Assert
  mapped addresses stay in range, all selected modeled low bits clear, mapping
  is idempotent, mask zero is identity, and pair behavior agrees with the
  already recorded formula.
- Test two or more logical addresses aliasing one physical byte. A read after a
  write in the same sequence must observe the new physical byte; last-write
  order must match operation order. Include `0x0000`, `0x0001`, odd/even pairs,
  `0xFFFE`, `0xFFFF`, address wrap, max mask, empty mask, invalid settings and
  pair/mask replacement.
- No-fault reference fixtures must match bytes, counters unrelated to the new
  model, and renderer output exactly. Reconnection must not reverse prior
  writes; restart must clear the fault and caches.

### Core-path coverage

- Exercise 68000 byte and word port reads/writes, odd/even lane ordering,
  address-increment register values, VRAM and non-VRAM command codes, and
  mirrored VDP port windows. Explicitly cover M5 undocumented byte-read
  command `0x0c`, including its `READ_BYTE(vram, addr ^ 1)` lane at odd and even
  addresses. Assert exact physical bytes and readback, not only an access counter.
- Exercise Z80 byte port reads/writes and the `$7F00-$7FFF` VDP forwarding
  path. Verify CPU-side Z80 RAM/banked-memory behavior remains unchanged.
- Exercise each DMA handler: 68K external, internal RAM and I/O source, VRAM
  copy, and VRAM fill. Cover short transfers, one-line partial progress, active
  versus blanking rate, odd/wrapped destination addresses and a destination
  whose alias is also in the SAT range. Assert source bytes are unchanged,
  mapped destination bytes/readback are correct, programmed counters advance
  exactly as before, and CPU freeze or busy-state behavior matches the pinned
  core. Separately test 128-KiB 68K-source DMA window wrap: initialize
  `source = (reg[23] << 17) | (dma_src << 1)`, then preserve the high window
  while wrapping the low 17 bits. This is distinct from 64-KiB VRAM destination
  wrap; an address fault must never remap a non-VRAM source read. Test fill
  arming and the triggering data-port write, its destination increment, the
  prelatched FIFO high byte used by `vdp_dma_fill`, and the exact first fill
  destination/lane. Assert no duplicate trigger write, skipped first fill or
  additional count caused by instrumentation.
- Exercise renderer reads for pattern data, Plane A/B and Window names, scroll
  tables, and sprite attributes through an actual render. Force a tile to be
  cached, change an aliased source byte, render again, and assert the next frame
  contains the updated expected pixels. Cache two distinct logical tiles that
  alias the same physical pattern, update it through a third alias, and require
  both displayed tiles to refresh. Toggle mask on/off between frames and
  verify stale decoded data is not reused. These are logical-render tests, not
  claims about the physical fetch dot.
- Exercise cache saturation and dirty-list capacity under broad changes. The
  dirty-list index must stay within its 2,048 pattern entries; no duplicate or
  missing cache updates may occur after aliases converge on the same physical
  byte.

### Actual WebAssembly and browser integration

- Rebuild the exact pinned core through the idempotent patcher. Check patch
  anchors, generated exports, source provenance, and repeat-build byte identity
  where the toolchain permits. Keep generated JS/WASM outside Git.
- Run a small synthetic 68000 test cartridge through the actual WASM API. Its
  reset/program flow must write and read VRAM through VDP ports, trigger each
  supported DMA type and render deterministic patterns. The test must fail if
  an operation bypasses the transaction helper. No commercial ROM is needed.
- Compare fault-off actual-WASM frames, sound samples, input response, RAM
  behavior, VDP status and no-fault DMA results with the pre-change pinned core
  for a fixed synthetic test set. Require byte-identical active framebuffer
  hashes and identical output/counters where currently exposed.
- Add actual-core Chromium coverage for no fault, one paired bridge, one stuck
  line, simultaneous line masks, reconnect, restart, RAM/VRAM takeover,
  generated export metadata, and persistence of already-written VRAM. Retain
  the existing mock-browser tests. Run Chromium, Firefox and WebKit in CI using
  the checked-in workflow; a mock core alone is not acceptance.
- Establish a reproducible 30-second actual-WASM benchmark with the same
  synthetic scene and DMA workload, at least five runs per build. Report median
  and p95 frame time with fault off and with representative masks. Pre-register
  a no-fault overhead limit of 5% for median and p95 versus the pinned baseline;
  investigate any larger regression. Also record per-frame VRAM operations,
  cache invalidations and DMA bytes to show that the new path does not retain an
  unconditional full-64-KiB projection per frame. Do not claim browser timing
  proves hardware accuracy.

## Staged implementation gates

1. **Close the semantics first.** Decide byte-lane mapping for word data-port
   operations, mapped SAT mirror behavior, render-read access inventory,
   supported modes, API migration and diagnostic counter names. Record these
   decisions in a reviewed protocol before runtime changes. This gate is now
   recorded in [VRAM transaction semantics](TRANSACTION-VRAM-SEMANTICS.md).
2. **Native primitives completed.** The isolated helper and strict/sanitizer
   tests cover exhaustive maps, byte collisions, boundaries, no-fault bypass,
   reverse cache dependencies and lifecycle state. They use canonical byte-array
   fixtures; core SAT/parser, cache adaptation and rendering remain integration
   gates. See [semantics](TRANSACTION-VRAM-SEMANTICS.md) and [testing](TESTING.md).
3. **Integrate source accessors and DMA.** Patch exact pinned anchors in
   `scripts/patch_core.py`, test idempotence and source drift, then pass actual
   synthetic-WASM CPU/Z80/DMA tests. No public package rebuild yet.
4. **Integrate render/cache reads.** Route the fully audited renderer reads,
   prove deterministic visible changes for the positive fault case, and pass
   no-fault frame/sound and performance gates. If any direct path remains out
   of scope, name it and narrow the user-facing claim before proceeding.
5. **Integrate UI/API and review.** Add explicit model identity and separate
   exports/counters; preserve RAM/VRAM exclusion and reconnect semantics. Pass
   actual-core Chromium and three-browser CI. Require independent specialist
   review of access completeness, cache coherence, DMA ordering, memory safety
   and the physical-fidelity wording.
6. **Version only after acceptance.** A new clean source commit and all required
   checks must pass before updating the application version to `0.3.0`. Keep
   public `0.2.7` files and historical experiment JSON immutable. If any gate
   remains open, stay on the current development version and describe the
   milestone as incomplete.

## Limitations

The inspected emulator source establishes which C functions read or write its
VRAM array and how the current renderer/cache reacts. It does not establish the
physical VDP's exact bus waveform, driven-net collision resolution, pin-level
row/column timing, dynamic scanout fetch order, or model/revision-specific
electrical behavior. A passing software test establishes the specified digital
model and its integration only. Physical claims would require separate
hardware-informed evidence.
