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
separately rebuilt original-renderer baseline JS/WASM hashes match the public
v0.2.7 core. The new normal build is checked for observable equivalence, not
binary identity. Active cases use literal
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

## First measured performance result: failed

The immutable [summary](experiments/2026-10-23-vram-renderer-performance-v1-summary.json)
and [losslessly compressed complete raw record](experiments/2026-10-23-vram-renderer-performance-v1.json.gz)
retain all five pairs and 25 runs from source `41140b4`. Each run measured 30
seconds. Independent review recomputed every per-run median/p95 and the paired
gates, verified stable source/artifact provenance and found no exclusions.

| Variant | Median of paired median ratios | Median of paired p95 ratios | Gate |
|---|---:|---:|---|
| New normal | 0.992305 | 0.991985 | Pass |
| Diagnostic off | 1.033545 | 1.069346 | Fail: p95 |
| Selected identity | 1.126256 | 1.021468 | Fail: median |

The threshold remains 1.05 for both statistics. Active AD3 is descriptive only.
The observed host load is recorded, but does not excuse the failure. No timing
was repeated or excluded to obtain a passing result. Renderer integration must
remain unmerged until a reviewed correction passes fresh acceptance.

Compressed SHA-256: `7494bd6470f3306b2c9ae1f391ef6ddf29b2367f7644b1fd2e902d24f28c00bc`.
Uncompressed SHA-256: `9bee24513cffc6d5ef414d17d2100a18851d6c02300f647c0c2a7a8913260bee`
(34,543,556 bytes). Decompressing the gzip reproduces the complete JSON exactly;
the summary is a reading aid and does not replace the raw record.

The integrated correctness suite subsequently passed 89 Python tests with no
skips, six required pinned-source patch checks, fresh four-core WASM builds and
all existing JavaScript/native suites with normal leak detection. The production
core build, actual-core Chromium and all six patch tests on the already-patched
vendor working tree also passed. Correctness success does not override the
performance failure.

## Reviewed performance correction

The CPU/DMA predicate previously synchronized mode state, recomputed the renderer
flag and checked pending cache invalidation on every guarded access, even for
selected identity. The repeated path is visible in the adapter source; identity
was slower than diagnostic-off in all five measured pairs.

A minimal correction first checks the existing cached effective-fault flag. OFF,
identity and suspended settings take the original access path immediately. An
active fault still synchronizes mode and rechecks effectiveness before mapping.
The pinned register-1 hook updates the flag after final mode-bit handling;
configure/reset/legacy override update it as well. Independent specialist review
approved these lifecycle assumptions and the actual source change.

A strict and ASan/UBSan native harness proves inactive accesses skip both
callbacks, active accesses call both, and a mode change suspends the active
path. Existing actual-WASM cases verify real mode exit/re-entry and cache
recovery. The corrected integrated suite passed all 91 Python tests without
skips, six required patch checks, fresh four-core WASM and all JavaScript/native
regressions with normal leak detection. Actual-core Chromium also passed using
the fresh normal artifact. This establishes correctness checks for the candidate,
not its performance. A new complete measurement must retain the same fixed
protocol and threshold, with the failed first record preserved unchanged.
