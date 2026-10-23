# VRAM renderer diagnostic

## Scope and acceptance

This stage extends the developer-only [access diagnostic](VRAM-ACCESS-DIAGNOSTIC.md)
to the pinned core's Mode 5 renderer. It is not a public model selector or a
v0.3.0 release. The normal application and downloadable v0.2.7 package retain
the existing frame-scoped model.

The source inventory includes all eight standard/alternate Mode 5 background
variants: normal and interlace rendering, including vertical-scroll variants.
Their direct VRAM reads cover horizontal scroll and Plane A, Plane B and Window
names. Pattern decoding reads mapped source bytes while retaining logical cache
keys. Mode 5 sprite parsing reads attributes and X coordinates from VRAM, while
Y, size and link come from the core's internal SAT mirror. Sprite drawing then
uses parsed metadata and decoded patterns. Earlier TMS and Mode 0 through Mode 4
paths are outside this model and must retain their original behavior.

Map every logical byte once, wrap each lane within 16 bits, and reconstruct the
core's original host word packing. Mapping a word's base alone is insufficient.
Fault-off and identity settings must retain direct original loads. Mode and
configuration transitions update the fast-path state and invalidate decoded
patterns before their next use. Changed physical bytes invalidate all logical
cache rows that depend on them, without a full cache scan for each write.

The internal SAT mirror follows the previously selected mapped-destination
write policy. A mixed-field sprite fixture checks this software policy; it does
not establish how physical VDP revisions capture sprite fields.

Acceptance requires a visible original synthetic scene, exact fault-off and
identity comparison with the normal core, independently expected fault pixels,
cache alias updates and reconnect, mixed SAT behavior, and explicit standard,
interlace and alternate branch coverage. Repeated patching must be stable and
source drift must fail closed. Independent specialist review must inspect both
the routing and the test oracles.

The preregistered performance gate is five paired 30-second samples per variant,
with median and p95 no-fault overhead at most 5% against the normal core. Compare
both diagnostic-off and selected identity, retain raw measurements, and report
noise honestly. Active-fault timing is a separate observation, not a substitute
for this no-fault gate.

## Reference construction

The regression reference uses a separate clean tree of the pinned upstream core.
Apply the normal application patches, then restore the original pinned
`vdp_render.c` before compilation. Use the same toolchain and flags as the new
normal build. The reference must not be repatched after restoration. This isolates
the renderer rewrite while keeping the established framebuffer and runtime fixes.
Compare the resulting source and binary hashes with the independently rebuilt
PR #36 reference before accepting this construction.

Use the same display-enabled original synthetic cartridge for reference, new
normal, diagnostic-off and selected-identity observations. A diagnostic-only
fixture is useful for exact fault cases, but cannot alone establish normal-core
equivalence.

## Fidelity boundary

These are mapped logical software reads at the core's existing render points.
The renderer still batches scanlines and uses a decoded pattern cache. Passing
checks do not establish beam-timed external bus fetches, contention, floating
voltages, physical pin mapping, commercial-game results, audible acceptance or
native macOS Firefox behavior.

## Current result

The reconstructed read helper passed independent specialist review and six
focused strict/sanitizer tests covering both host-layout configurations. The full
existing suite passed 83 Python tests with no skips, plus JavaScript/native
regressions and fresh normal/diagnostic WASM builds. Renderer routing is still
unimplemented in this checkpoint; these results do not establish visible
renderer acceptance or performance. The earlier temporary renderer source was
lost before it was committed, so its observations cannot certify this rebuild. Public model identity,
browser controls, complete transaction exports and milestone packaging remain
separate gates in the [architecture plan](TRANSACTION-VRAM-PLAN.md).
