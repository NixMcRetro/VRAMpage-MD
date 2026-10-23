# Transaction-level VRAM semantics

**Status:** reviewed implementation contract. Originally written as documentation
at base `97964a06adaf2668acbe975998d30b53dd121ddc` for application v0.2.7.
Current version follows root `VERSION`. Native/diagnostic integration and
[optional core API groundwork](VRAM-PUBLIC-MODEL-API.md) implement stages of this
contract; public application and v0.3.0 milestone acceptance remain future work.
It refines [the architecture and test plan](TRANSACTION-VRAM-PLAN.md).

Source evidence is the pinned `h1romas4/wasm-genplus` revision
[`6090aff9e9b2f578cd28882bd4571d2e35b1d674`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674).
The plan's source map links the VDP family/mode switch, 68000 and Z80 data
handlers, DMA scheduler and copy/fill paths. The byte-lane rules here follow
[`macros.h`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/macros.h#L6-L30),
the aligned write/SAT/cache path in
[`vdp_bus_w`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2127-L2174),
the M5 byte-read case in
[`vdp_68k_data_r_m5`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L2440-L2550),
and mixed SAT fields in
[`parse_satb_m5`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c#L3793-L3900).

## Model boundary and support

The explicit model ID is `logical-byte-transaction-v1`. It represents a
deterministic low-dominant address transform at logical byte access sites in
the pinned emulator. It does not model electrical contention, analog voltage,
floating nets, data-line faults, beam-dot fetch timing, or a DRAM waveform.
Rendering remains line-batched. A rendered table or pattern read is mapped at
the time the current renderer function reads it, not at a claimed physical
pixel-fetch dot.

Enable the model only when the VDP family is Genesis/Mega Drive
(`system_hw & SYSTEM_MD`) and Mode 5 is active (`reg[1] & 0x04`). `vdp_ctrl.c`
sets Mode 4 versus Mode 5 read/write and render handlers from that register in
its VDP register switch. All address-helper entry points must recheck this
predicate. A request selecting the transaction model outside the supported
state returns unsupported and changes no configuration or memory. If
software later leaves Mode 5, the configured model is suspended: accesses use
the original core path, exported
state says `effective: false` and `reason: unsupported-mode`, and physical
VRAM is not restored or rewritten. On leaving Mode 5, discard the reverse
dependency index, invalidate decoded patterns, and zero transaction counters.
On re-entering Mode 5, zero the transaction counters, rebuild the index and
invalidate decoded patterns before the next transaction render. This ensures
a frame that moves in and out of unsupported mode reports only accesses while
the model was effective. It also prevents Mode 4 or compatibility writes made
while suspended from leaving stale transaction cache entries. The configured
model and mask remain selected, so the explicitly selected model resumes in
Mode 5. Clearing or
selecting another model remains available. Non-MD and Mode 4/compatibility
handlers never receive this transform.

Mask and pair settings are immutable during an emulated operation. The
JavaScript API can change them between synchronous `tick()` calls only. An
invalid model ID, mask, or pair is rejected atomically; no partial settings
change is allowed.

## Address and byte semantics

The address domain is a 16-bit logical byte offset. First reduce every access
address modulo `0x10000`, then map its row and column address lines using the
existing low-dominant rule in `scripts/vram_fault_patch.c::bend_pair`: a paired
net keeps high/high and low/low, while either low forces both mapped bits low.
For the current AD mapping, AD `n` couples row bit `n+2` with column bit `n`
for `n < 2`, or column bit `n+8` for `n >= 2`. Apply enabled pairs in ascending
AD order. A stuck-low mask clears both mapped bits for each selected AD. The
result is always a 16-bit address. The single address function accepts a
logical byte offset and returns a logical byte offset; it never accepts a C
pointer, a host word index, or an address already translated by a byte-lane
macro.

All core storage access goes through `READ_BYTE(vram, logical)` and
`WRITE_BYTE(vram, logical, value)` after mapping. `macros.h` defines these as
`(ADDR)^1` on LSB-first hosts and direct indexing otherwise. This keeps the
fault transform independent of the host's backing-array lane convention.
Renderer multi-byte reads must likewise use logical byte helpers and assemble
their original core values explicitly. For each source `uint16` or `uint32`,
map each logical byte address independently and read in ascending logical
address order with `READ_BYTE`, yielding `b0..bN`. A `uint16` value is
`(b0 << 8) | b1` on both host types. A `uint32` value expected by the pinned
render code is `(b2 << 24) | (b3 << 16) | (b0 << 8) | b1` on LSB-first hosts,
and `(b0 << 24) | (b1 << 16) | (b2 << 8) | b3` on big-endian hosts. Thus
logical bytes `11 22 33 44` produce `0x33441122` on LSB-first and `0x11223344`
on big-endian hosts, matching `DRAW_COLUMN` and pattern decode. Remapping a
`uint16 *` or `uint32 *` host pointer is forbidden.

For a Mode 5 68000 data-port word operation, preserve the existing core
alignment and odd-address swap first. The two logical destination/read lanes
are `even = addr & 0xFFFE` and `even + 1`; an odd starting address does not
make the word span `addr` and `addr + 1`. A write serializes the post-swap
word as high byte to `even`, low byte to `even + 1`, then maps each lane
independently. A read maps and reads those same two lanes and reassembles the
same core-native word expected by the caller. This preserves the pinned
`vdp_bus_w` odd-address swap and aligned word behavior while allowing a
bridge to make the two lanes alias independently. The data-port byte-write
handler duplicates the byte into both word lanes as it does today; each lane
then maps independently. The undocumented Mode 5 read command `0x0c` is a
single byte operation at the exact logical lane selected by the current core
expression `addr ^ 1`; it is not converted to an aligned word read. The normal
Mode 5 read advances `addr` once by `reg[15]`, even for this byte command.

Z80 Mode 5 VDP data accesses are one logical byte per operation. Map the
logical byte passed to `READ_BYTE`/`WRITE_BYTE` after removing the macro's
host-lane conversion. Preserve the Z80 handler's own address increment and do
not transform Z80 RAM, banked 68000 memory, or Z80 accesses in other VDP modes.

DMA has no new scheduler or bulk projection. External, internal-RAM and I/O
68000-source DMA retain their existing source reads and transfer timing;
only the VRAM destination lanes are mapped. The 68000 DMA source window wraps
as the current core specifies and is not faulted. In VRAM copy, preserve the
source logical lane expression `source ^ 1` and destination logical lane
expression `addr ^ 1`, then map each resulting logical byte offset, then apply
the host `READ_BYTE`/`WRITE_BYTE` storage conversion. Fill preserves the
destination expression `addr ^ 1`, maps that logical byte, then applies host
lane conversion. Fill also preserves its existing arming/trigger write,
prelatched FIFO byte, byte count, and `reg[15]` increment. Every VRAM byte
operation wraps at 16 bits before mapping. No logging or counter may perform a
second read or write.

## Worked mapping and ordering vectors

These vectors use the current `bend_pair` formula and 16-bit offsets. An
independent small script implementing `bend_pair` and the stated mask formula
produced each listed value; the runtime helper must have identical results.

| Configuration | Input | Output | Reason |
|---|---:|---:|---|
| mask AD0 | `0x0025` | `0x0020` | AD0 clears A0 and A2 |
| mask AD7 | `0x8180` | `0x0180` | AD7 clears A9 and A15 |
| bridge AD1/AD3 | `0x0822` | `0x0802` | A3 low forces A5 low; other enabled pair bits remain high |
| no fault, wrapped byte address | `0x10000` | `0x0000` | Address domain is 16-bit |

For AD0, logical pattern row 0 uses bytes `0x0000..0x0003`, which map to
`[0, 0, 2, 2]`. Logical row 1 uses `0x0004..0x0007`, which also maps to
`[0, 0, 2, 2]`. If physical byte `0` changes, both logical cache keys
`(pattern 0, row 0)` and `(pattern 0, row 1)` are invalidated. A subsequent
read through either alias returns the one new physical byte. This is an
intentional collision, not a byte-lane reversal.

For word lane order, with a no-fault map and logical bytes initially
`[0x12, 0x34]` at `[0x1200, 0x1201]`, an even-address write of `0xABCD` stores
`[0xAB, 0xCD]`. An odd-address write of `0xABCD` follows the pinned swap and
stores `[0xCD, 0xAB]` at the aligned pair. With AD0 enabled, the even-address
pair maps both lane addresses as `0x1200 -> 0x1200` and `0x1201 -> 0x1200`;
the sequential high-byte then low-byte stores leave `0xCD` at physical
`0x1200`. A following read returns the two logical reads of that same byte,
`0xCDCD`, before the existing address increment. The test also verifies the
increment happens once, not once per lane.

For SAT collision, choose a programmed destination outside the SAT window
whose mapped byte lands inside it. Verify the physical byte changes, the
internal SAT mirror byte is updated at the mapped destination's SAT offset,
and the mixed-field parser below sees that updated byte. Repeat the same write
with mapping off to confirm the legacy logical-destination behavior remains
untouched.

Concrete M5 boundary vector: set the Mode 5 SAT base to `0x0000` with
`sat_base_mask = 0xFE00` and `sat_addr_mask = 0x01FF`, then enable mask AD7.
Logical destination `0x8200` is outside the selected SAT window, while its
mapped physical destination is `0x0000` because AD7 clears A9 and A15. A byte
write of `0x5A` must store `0x5A` at physical `vram[0]` and update SAT mirror
byte offset zero; a no-fault write to `0x8200` must update neither. This
verifies the chosen policy without asserting which side of a real VDP's
internal capture boundary owns address remapping.

## SAT mirror policy and limit

When a transaction write reaches physical VRAM byte `p`, update the internal
SAT mirror only if `p` matches the currently configured Mode 5 SAT decode
window. Use the mapped destination for the existing SAT base/mask test and
the mapped offset for the mirror slot. A word write applies this independently
to its two serialized byte lanes. A byte write updates only its matching
mirror byte. DMA copy/fill use the same byte rule. This is the selected
software-model policy because the renderer's `parse_satb_m5` combines Y,
size, and link bytes from `sat[]` with attribute and X bytes read from `vram[]`;
keeping those representations synchronized to the modeled physical store
prevents a remapped write from splitting one synthetic table across old and
new destinations.

This policy does not establish the physical VDP's SAT capture or cache timing.
The pinned code intercepts writes at a software logical address and maintains
its internal mirror as an emulator optimization. Whether actual hardware
captures an aliased write before or after external address-line remapping is
not established by these source files. Treat mapped-destination mirroring as
part of `logical-byte-transaction-v1`, not as a hardware claim.

Synthetic mixed-field fixture: configure a SAT base with distinct Y/size/link
values in the mirror and distinct attribute/X values in VRAM. Render and assert
all fields match the fixture. Then perform a mapped byte write to each field
class, including a destination that aliases from outside into the SAT window.
Assert Y/size/link use the updated mirror bytes and attribute/X use the
updated physical VRAM bytes. Include word writes at aligned addresses
immediately before and after the SAT window boundary, plus separate byte
writes on each side. The core aligns every word operation before its odd-
address swap, so an odd word operation cannot cross this word-aligned SAT
boundary. Also include a DMA-copy byte, a DMA-fill byte and a no-fault
reference. The expected SAT behavior is the mapped-destination rule above, not
an inferred silicon timing result.

## Renderer coverage and tile-cache coherence

At the pinned source revision the M5 renderer has raw `vram[]` reads in
`render_bg_m5`, `render_bg_m5_vs`, `render_bg_m5_im2`, and
`render_bg_m5_im2_vs` for horizontal scroll and Plane A, Plane B, and Window
name words. The `ALT_RENDERER` alternatives contain corresponding direct
reads and are in scope too. `parse_satb_m5` reads SAT attribute/X words from
VRAM and Y/size/link from `sat[]`. `update_bg_pattern_cache_m5` reads decoded
pattern bytes directly. `render_obj_m5` variants consume the decoded cache;
their source pattern reads therefore depend on that cache invalidation. The
Mode 0-4 renderer functions and TMS compatibility functions also contain raw
VRAM access, but transaction mode is unsupported there and their code remains
on the existing path. `render_line` continues to schedule cache updates,
background drawing and sprite parsing as before. Before integration, repeat a
`vram[` audit on the exact pinned source after patching and require every M5
raw read to be routed or explicitly listed as an excluded access.

Keep logical cache keys `(pattern, row)` because the renderer requests
patterns by logical name. On a nonzero mask/pair change, rebuild a reverse
dependency index from every logical source byte used by each of 2,048 patterns
and eight rows. For each logical row, map its four byte addresses, deduplicate
the at-most-four physical addresses within that row, and append the 16-bit
`(pattern << 3) | row` key to each physical address's dependent list. A write
to physical byte `p` marks every listed logical row dirty. If the byte value
does not change, no row is dirtied. A settings change invalidates all decoded
rows once after rebuilding; it does not rebuild or clear caches each frame.

The maximum dependency edge count is 65,536: 2,048 patterns times eight rows
times four bytes before per-row deduplication. Store 65,537 `uint32_t` prefix
offsets (262,148 bytes) and up to 65,536 `uint16_t` row keys (131,072 bytes),
for 393,220 bytes (384 KiB + 4) of persistent index storage. Build with a
temporary `uint32_t[65536]` cursor (262,144 bytes), then release it; peak
index-build storage is bounded at 655,364 bytes (640 KiB + 4).
No unbounded allocation or per-write full-row scan is allowed. With no fault
selected, use the existing direct core reads and dirty marking without
building or consulting this index. A narrow fault-off fast path is an
acceptance requirement, not a benchmark-only optimization.

## API migration, state and exports

The existing `_set_vram_short` and `_set_vram_address_mask` remain legacy
frame-projection controls. Calling either selects `frame-projection-v1` and
applies its original behavior; it never changes transaction settings. The new
API is one atomic explicit call,
`_set_vram_fault_model(modelId, mask, bridgeA, bridgeB)`, with numeric model
IDs `VRAM_MODEL_OFF = 0`, `VRAM_MODEL_FRAME_PROJECTION_V1 = 1`, and
`VRAM_MODEL_LOGICAL_BYTE_TRANSACTION_V1 = 2`. It returns `VRAM_OK = 0`,
`VRAM_INVALID_ARGUMENT = 1` for invalid arguments, and
`VRAM_UNSUPPORTED_MODE = 2` when the requested model is unsupported by the
active VDP family/mode. All four arguments must be integers; fractional or
non-numeric values return `VRAM_INVALID_ARGUMENT` and do not rely on WASM
truncation or coercion. On either error, active model, settings, memory,
counters and caches are unchanged. IDs 1 and 2 accept exactly one setting
form: a mask in
`0..255` with both bridge arguments `-1`, or mask `0` with two distinct bridge
indices in `0..7`. Mask and bridge forms cannot be combined. ID 0 requires
mask `0` and bridge arguments `-1, -1`. Selecting the transaction ID is the
only way to opt into the new semantics. Keep the shipped `0.2.7` API and
runtime unchanged; this is a `0.3.0` implementation contract. Invalid or
unsupported selections leave the active model, masks, memory and counters
untouched.

Default after clean start is `frame-projection-v1` with no fault, preserving
the current default behavior. Explicit `off` selects no fault. Reconnect
clears the selected fault and restores ordinary address lookup, but does not
roll back physical VRAM mutations already made; it resets transaction counters
and invalidates transaction caches. Clean core restart clears
fault configuration, both model counter sets and reverse indexes after core
reset, then invalidates derived caches. Model selection clears only the new
model's last-frame counters and invalidates caches as needed; it never rewrites
VRAM. Preserve current RAM/VRAM mutual exclusion and failed-takeover behavior.

Selecting `logical-byte-transaction-v1` with mask `0` and bridge arguments
`-1, -1` is an explicit identity configuration. Export it as `effective: false`
with `reason: no-fault`; use the original direct path, allocate no reverse
index, and report zero transaction counters. It does not activate a dormant
fault or select the frame-projection model.

Exports retain legacy frame-projection fields and their existing meanings.
Add a separate object with `modelId`, `modelVersion`, `effective`, `reason`,
mask/pair settings, and last-frame `logicalByteReads`, `logicalByteWrites`,
`redirectedByteReads`, `redirectedByteWrites`, and
`changedPhysicalByteWrites`.
These are software helper counts, not VDP bus cycles or pixel fetches. Counts
are per logical byte lane, including cache/table reads when those actual
renderer reads pass through the helper. Word operations count two lanes;
Mode 5 command `0x0c` counts one. Do not include values, ROM data, timelines,
or per-access addresses in exports. `changedPhysicalByteWrites` counts
changed write operations, not unique addresses: a changed write increments it
once; a same-value write does not. Reset these five counters at the start of
each `tick()` and export the completed frame's counts. Suspension and re-entry
also zero them so counts cannot mix effective and bypassed periods. A
suspended or non-selected transaction model reports zero effective
transaction counts.
Model metadata must be included in diagnostic snapshots so frame-projection
and transaction results cannot be mistaken for one another. Application version follows root `VERSION`; optional API groundwork does not
publish v0.3.0. Complete milestone acceptance and independent review before
releasing that version.

## Native helper acceptance before core integration

Implement the map and byte helper as an isolated native C module first. Before
patching `vdp_ctrl.c` or the renderer:

- Exhaust all 65,536 addresses for all 256 masks, checking range, idempotence,
  mask-zero identity, selected-bit clearing and pair vectors above. Run strict
  C compilation plus AddressSanitizer and UndefinedBehaviorSanitizer.
- Check exact logical byte serialization on little-endian and big-endian
  helper fixtures, odd/even word writes, duplicated 68000 byte writes, the
  `0x0c` selected lane, and 16-bit wrap. Confirm the two-lane collision vector
  yields `0xCDCD` and increments once.
- Check order-sensitive collisions: write alias A, read alias B, overwrite
  through B, read A. Check repeated same-value writes do not spuriously dirty
  dependent rows, while changed writes invalidate every reverse dependency.
- Verify AD0's row-0/row-1 cache alias fixture, maximum-mask dependency count,
  mask replacement rebuild, fault-off index bypass, invalid setting atomicity,
  reconnect persistence and clean-restart clearing.
- Check SAT mixed-field vectors against an independent byte-array fixture,
  including outside-to-inside aliasing and no-fault reference behavior.

Only after these pass should implementation patch exact pinned source anchors,
then proceed through DMA, renderer/cache, actual WASM, browser and performance
gates in `TRANSACTION-VRAM-PLAN.md`. A passing native helper establishes this
defined digital model only; it does not establish physical pin or fetch timing.
