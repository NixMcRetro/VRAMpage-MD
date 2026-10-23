# VDP VRAM access diagnostic

This developer-only stage connects the reviewed [transaction primitives](TRANSACTION-VRAM-SEMANTICS.md)
to Mode 5 CPU/Z80 data ports and DMA VRAM endpoints in the pinned Genesis Plus GX
core. It is a partial digital model, not the v0.3.0 release. The public app remains
v0.2.8 with its existing frame-scoped VRAM controls.

## Scope

The access adapter maps a logical byte address exactly once and then uses the
core's existing host-lane conversion to access the real VRAM store. It does not
project or copy all VRAM before and after a frame. CPU word lanes retain their
alignment, odd-address swap and sequential write order. Z80, undocumented byte
reads, VRAM-copy and fill paths retain their original logical lane selection.

External, work-RAM and I/O DMA sources retain their existing reads and 128-KiB
source-window behavior. Only supported VRAM endpoints are faulted. VRAM-copy
source and destination are separate byte operations. Fill retains its triggering
CPU write, FIFO byte, destination progression and transfer count.

Changed physical bytes invalidate only their reverse-dependent logical cache
rows. SAT mirror updates follow the selected mapped-destination policy, including
writes whose VRAM value is unchanged. This is a documented digital policy, not
evidence about silicon cache capture timing.

## Diagnostic interface

Only the separately compiled test variant exposes
`set_vram_transaction_diagnostic(model, mask, bridgeA, bridgeB)`. Model `2`
selects the partial transaction path and model `0` disconnects it. Masks and
bridges follow the reviewed mutually exclusive setting rules. Errors preserve
existing state; this is not the future public model selector.

`get_vram_tx_counter(index)` reports the five 64-bit counters in order: logical
reads, logical writes, redirected reads, redirected writes, changed physical
writes. The Emscripten binding returns BigInt values. Test-only bridge/inspection
exports operate on original synthetic data and are absent from normal builds.
They are not user experiment exports or a general gameplay validation tool.

## State transitions

The diagnostic selector is separate from helper OFF and legacy frame settings.
A successful selection validates and configures the helper before clearing the
legacy fault. Invalid or unsupported requests preserve prior settings and counters.
Disabling returns to neutral legacy behavior, without resurrecting a dormant
bridge. Explicit legacy controls exit the diagnostic and keep their established
argument behavior. Cartridge start and clean restart clear diagnostic state.

Mode 5 transitions are handled at the register change, as well as guarded at
accesses. Leaving the supported mode suspends the helper; returning rebuilds
dependencies and invalidates decoded state before use. Identity settings use the
original core access path with no dependency allocation or transaction counts.

## Remaining gates

The initial access-only checkpoint did not map renderer reads. The separate
[renderer diagnostic](VRAM-RENDER-DIAGNOSTIC.md) now has locally reviewed routing
and visible/cache/SAT fixtures. Final integrated regression, performance and CI
remain gates before that checkpoint can be merged. Public model/API selection,
browser controls and complete Mac milestone release acceptance remain separate
stages in the [architecture plan](TRANSACTION-VRAM-PLAN.md).

Synthetic CPU/core checks establish only the specified emulator access behavior.
They do not establish commercial-game outcomes, audible or native Mac acceptance,
physical pin mapping, contention, floating voltages or beam-timed fetch accuracy.

## Reproduce the automated checks

These commands are for core development, not normal Mac launching. Follow
[the developer build setup](DEPLOYMENT.md) for the pinned Emscripten toolchain
and vendor checkout, then run:

```sh
python3 tests/test_vram_transaction_wasm.py
```

The test stages the pinned source in temporary directories outside the checkout,
checks repeat application and source-drift rejection, builds normal and diagnostic
variants, and runs the synthetic Node checks. It does not replace `site/core` or
ship an alternate playable app. The required CI gate runs after the ordinary
core build and checks its SDK/vendor prerequisites explicitly.

A generated original cartridge executes 68000 memory-mapped VDP writes. A bounded
diagnostic bridge additionally invokes real 68000/Z80 port and DMA handlers for
precise boundary tests; it does not substitute a mock memory model. The ordinary
build exposes neither the transaction selector nor that test bridge.

No-fault and identity-selected runs compare the normal and diagnostic variants'
framebuffer, audio sample counts and channels, work RAM, frame count and available
CPU STOP/HALT flags. Full CPU registers and internal VDP status are outside this
comparison. Other cases check alias ordering, mapped SAT/cache updates,
mode transitions, source/destination wrap, fill triggering and partial DMA progress.

## Verified result

The final full local suite passed 79 Python tests with no skips, including fresh
normal/diagnostic WASM builds, native strict/sanitizer tests and the existing
JavaScript/native regression suites. It ran outside the restricted executor so
launcher tests could bind localhost and normal leak detection remained enabled.
Independent specialist review approved source routing, lifecycle, patching and
test design and rebuilt the pinned variants separately.
