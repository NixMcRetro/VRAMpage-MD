# VRAM renderer diagnostic

## Scope and acceptance

This stage extends the developer-only [access diagnostic](VRAM-ACCESS-DIAGNOSTIC.md)
to the pinned core's Mode 5 renderer. It is not a public model selector or a
v0.3.0 release. The normal application and downloadable v0.2.8 package retain
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

## Correctness checkpoint

The helper and pinned source routing passed independent specialist review. Six
focused strict/sanitizer tests cover both host-layout configurations, literal
packing, wrap and inactive direct loads. All eight Mode 5 background variants,
pattern decoding and SAT attribute/X reads are routed. Six pinned-source tests
reject missing, extra and post-patch raw reads and verify idempotence.

A separately rebuilt original-renderer baseline, new normal build, diagnostic-off
and selected identity match the complete visible synthetic framebuffer, audio
channels/sample count, work RAM, logic frame and CPU flags at fixed ticks. The
normal JS/WASM hashes also match the public v0.2.7 core. Active cases use literal
CRAM-derived pixel expectations rather than the implementation's address mapper.
They cover name-table and horizontal-scroll reads; pattern aliases with two
logical dependents dirtied by a third physical write; reconnect; invalid settings;
identity transitions; unsupported-mode exit/reentry; and clean restart.

All four standard and alternate Mode 5 render paths have active pixel assertions.
The vertical-scroll/interlace cases assert line-zero results and actual renderer
function selection; they do not establish full-field vertical-scroll timing. The
mixed SAT fixture independently separates internal Y/size/link from mapped VRAM
attribute/X, checking sprite position, height, hidden Y and link termination in
standard and alternate builds. This validates the selected software policy only.

The full routing checkpoint passed 89 Python tests without skips and the existing
JavaScript/native suites with normal leak detection. Later visible and SAT
fixtures passed fresh normal, diagnostic, alternate and original-renderer WASM
builds. Final integrated regression and the fixed performance gate remain required
before merge. A preliminary fixed-tick benchmark preflight independently passed
whole-state equivalence, CPU-loop progress and active mapped DMA writes. A
preflight is not a timing result.

## Reproduce

After the pinned SDK and vendor setup in [deployment](DEPLOYMENT.md), run
`bash scripts/test.sh`. The actual-WASM test also invokes the six pinned-renderer
patch tests with the vendor prerequisite, then the visible four-core matrix. A
source-only run that skips missing SDK/vendor prerequisites is not acceptance.
Set `VRAM_TX_WASM_BUILD_ROOT` to an empty persistent directory to retain builds.

For a separate quiet-host performance run, use:

```sh
node scripts/benchmark-vram-renderer.cjs \
  --baseline /path/to/baseline/src/main/js/genplus.js \
  --normal /path/to/normal/src/main/js/genplus.js \
  --diagnostic /path/to/diagnostic/src/main/js/genplus.js \
  --out /path/to/new-benchmark-record.json
```

`--preflight-only` runs fixed-tick checks without timing. The full run fixes five
paired blocks and 30 seconds per variant, alternating forward/reverse order. It
uses a visible synthetic cartridge with a recurring 32-word VRAM DMA loop. For
normal, diagnostic-off and identity, both the median of paired median ratios and
the median of paired per-run p95 ratios must be at most 1.05. Active AD3 is
descriptive only. Every raw frame duration is retained. Do not exclude or rerun
samples based on results. Source HEAD/tree, clean tracked state, runtime/host
metadata and core hashes are recorded before and checked after measurement.
The report is saved before a failed performance/provenance gate exits nonzero.

Public model identity, browser controls, complete transaction exports and
milestone packaging remain separate gates in the
[architecture plan](TRANSACTION-VRAM-PLAN.md).
