# Bounded instruction-origin diagnostic

## Objective

Identify the executed store behind the first affected byte write at CPU address
`$FFF62A`, remapped to logical RAM `$F22A`, during tick 1801 of the existing
A10/A11 one-write experiment. Pinned source identifies `$F62A` as the VBlank
routine flag. Both setting and clearing it remain candidates. The prior
[audio/state protocol](RAM-ALIAS-AUDIO-PHASE.md) cannot distinguish them from
frame-boundary samples.

This is a developer-only diagnostic, not a new fault model or an app feature.
Keep the published v0.2.7 package, normal runtime API, original game code and
historical experiment records unchanged. Normal users need no new download.

## Required evidence

- Capture instruction-start PC before opcode fetch. A PC read during the write
  may already have advanced through opcode and extension words.
- Classify the original attempted bus write as zero, nonzero or unknown. Do not
  expose its byte/word value, ROM instructions or RAM contents.
- Keep one bounded first-affected-write record. Preserve original address,
  mapped address, bus width, frame, reason and the exact pulse cutoff.
- Treat interrupt-entry writes outside decoded instruction execution as having
  unknown instruction origin. Document synchronous exception attribution.
- Validate byte, word and split-longword accesses, extension words, branch and
  interrupt/exception lifecycle, no-op writes and disabled diagnostics.
- Use an isolated staged core/build. Record its source and tool identity plus
  source/binary hashes separately from the unchanged public package.
- Repeat baseline and one-write trials from fresh cores, with zero host input,
  arm after tick 1800, no CPU recovery and the existing 2400-tick bound. Require
  equivalent observations with diagnostics disabled/enabled and against the
  pinned public core before interpreting the result.

Do not infer electrical accuracy, an audible effect or sustained gameplay
trajectory divergence from an identified store. No commercial cartridge, raw
samples, private paths, captures or full timelines belong in public evidence.

## Developer procedure

Use the existing pinned core checkout and the normal build prerequisites from
[deployment](DEPLOYMENT.md). Activate Emscripten before staging. The output must
be an empty directory outside the repository, never the application's `site`
or normal `vendor` build. No changes to the normal build script are required.

```sh
python3 scripts/build-store-origin-diagnostic.py /tmp/vrampage-store-origin
mkdir -p /tmp/vrampage-store-origin/wasm-genplus/build
cd /tmp/vrampage-store-origin/wasm-genplus/build
emcmake cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5
emmake make -j2
```

Back in the repository, run the synthetic CPU tests before a private experiment:

```sh
node tests/test_store_origin_wasm.cjs /tmp/vrampage-store-origin/wasm-genplus/src/main/js/genplus.js
node scripts/run-store-origin-diagnostic.cjs /private/path/sonic.md /tmp/vrampage-store-origin /path/to/extracted-public-v0.2.7 > /tmp/store-origin.json
```

Commit the diagnostic sources before staging evidence. If any tool source or
its dependencies change, use a new empty output directory and rebuild. The
runner verifies staged source/tool hashes and compares fresh-core observations
against the exact pinned public package. The custom core is not that release;
its source and binary hashes must remain separately identified. Do not put the
custom binary into an existing release or normal Mac package.

## Recorded result

[Protocol 1 record](experiments/2026-10-23-vblank-store-origin-v1.json) was
produced from clean diagnostic commit `a62439e`, using a separate custom build
and the exact pinned public v0.2.7 reference. Six fresh custom cores (baseline
and fault, each disabled/enabled/repeated) plus two fresh public cores ran
2400 ticks with zero host input and no recovery. All acceptance gates passed:
observational equivalence, repeats, prefault equality, timing/input, absence of
unexpected records and the exact one-write pulse budget.

The repeated first-affected record identifies a byte write at instruction-start
PC `$B46`, original CPU address `$FFF62A`, mapped logical offset `$F22A`, and
completed-frame counter 1800 (access during tick 1801). Its original target-byte
classification is zero. Thus the intercepted access writes zero to the VBlank
flag address, rather than the nonzero routine setup. No raw value or opcode
bytes are exported.

Independent specialist review reran all eight cores and reproduced the report
byte for byte. In pinned [s1disasm source](https://github.com/sonicretro/s1disasm/tree/15dfa3a6ee4c53aeb482233e493755c84b4f3479),
`$B46` maps to `move.b #id_VBlank_Lag,(v_vblank_routine).w`, with
`id_VBlank_Lag` equal to zero. This identifies the flag-clear store.
The source copies the flag
before clearing it, then dispatches VBlank work and updates music. Redirecting
that clear is consistent with leaving the game loop waiting for an extra
VBlank. The previous phase comparison still shows a one-tick player/demo shift,
not sustained gameplay trajectory divergence. This diagnostic does not directly
trace the entire wait/release sequence or establish an audible effect.

## Verification scope

The full local source suite passed 76 Python tests, existing native strict and
sanitizer coverage, framebuffer/protocol suites and eight runner test groups.
Nine actual-WASM synthetic CPU groups verify instruction-start PC with extension
words, byte/word classification, longword pulse cutoff, a branch, address-error
exception PC unknown, disabled tracing, unchanged writes and record reset.
Independent specialist review reran the focused source, runner and synthetic
WASM tests. General external interrupt handling also received source review;
it is not claimed as a separate synthetic IRQ test. Fresh CI additionally
builds the isolated core and runs the synthetic CPU tests outside the package.
