# Bounded VBlank wait/release observations

## Objective

The [instruction-origin experiment](VBLANK-STORE-ORIGIN.md) identified the first
affected store at PC `$B46`: a zero byte write to CPU `$FFF62A`, redirected to
logical `$F22A` during tick 1801. This follow-up observes the short sequence
around that access and the subsequent wait-loop release. It does not edit game
code or variables, apply CPU recovery, or introduce an audio or hardware model.

Pinned [s1disasm source](https://github.com/sonicretro/s1disasm/tree/15dfa3a6ee4c53aeb482233e493755c84b4f3479)
was assembled with `Revision = 0`, bug fixes, cheats and optimizations disabled.
The resulting complete cartridge SHA-256 matches the supported private ROM:
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
Neither the generated cartridge nor private ROM is published.

That matching Revision 0 listing identifies the poll at `$29AC`, branch at
`$29B0`, return at `$29B2`, main-loop flag setter at `$3AE6`, and caller
successor at `$3AF0`. The VBlank handler tests the flag at `$B14`, reads it again
at `$B42`, and clears it at `$B46`. Source semantics guide the profile; actual
instruction visits and bus events must establish which paths execute. The public
record retains selected milestones, not the full handler event buffer; `$B42`
is source-backed profile context, not a separately published execution claim.

The first attempted run failed closed: the original candidate profile used
Revision 1 addresses and omitted the `$B42` read. The bounded scout had no
overflow but detected an unlisted access. An isolated first-unexpected-PC check
identified `$29AC`, and the matching whole-cartridge build established the
revision correction. No failed run is presented as accepted evidence.

## Evidence requirements

- Stage the private diagnostic outside the checkout, retaining the existing v1
  hooks and tests. The normal app, runtime API, version and public release remain
  unchanged. All older JSON records remain immutable.
- Use a fixed instruction allowlist, one configured work-RAM byte, a window of
  at most four ticks and a fixed event capacity. Compress repeated matching
  events while retaining counts and ordering. Overflow must fail acceptance.
- Distinguish an instruction-start memory probe from an actual CPU bus read.
  Classify bytes as zero/nonzero, without exporting values or opcode bytes.
  Capture native flag state around the targeted store, including stores after
  the one-write pulse has disconnected.
- Preserve unknown PC attribution through exception paths. Unexpected profile
  PCs, missing milestones or invalid ordering must not produce a passing result.
- Verify the poll, flag clear, wait exit and subsequent setup with synthetic
  actual-CPU tests, alongside disabled/non-target/window/overflow checks.
- Reuse one staged diagnostic compilation for both the existing origin CPU
  tests and the new sequence tests. Compare fresh baseline/fault repeats with
  diagnostics disabled/enabled and with the exact public v0.2.7 core. Retain
  prefault, zero-host-input, tick-1801 activation and one-write budget gates.

An observed delayed release can explain a bounded phase shift. It does not by
itself establish sustained gameplay trajectory divergence, audible effects,
native Mac acceptance or physical electrical behaviour. Never publish the
cartridge, raw ROM/RAM/audio, opcode bytes, full execution traces or private paths.

## Developer procedure

Commit the diagnostic tools before collecting evidence. Activate the pinned
Emscripten toolchain and use an empty directory outside this checkout. The
runner rejects changed tools, dirty diagnostic sources and mismatched staged
source hashes. It validates the exact public v0.2.7 reference package separately.

```sh
python3 scripts/build-vblank-wait-diagnostic.py /tmp/vrampage-vblank-wait
mkdir -p /tmp/vrampage-vblank-wait/store-origin/wasm-genplus/build
cd /tmp/vrampage-vblank-wait/store-origin/wasm-genplus/build
emcmake cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5
emmake make -j2
cd /path/to/VRAMpage-MD
node tests/test_store_origin_wasm.cjs /tmp/vrampage-vblank-wait/store-origin/wasm-genplus/src/main/js/genplus.js
node tests/test_vblank_wait_wasm.cjs /tmp/vrampage-vblank-wait/store-origin/wasm-genplus/src/main/js/genplus.js
node scripts/run-vblank-wait-sequence.cjs /private/path/sonic.md /tmp/vrampage-vblank-wait /path/to/extracted-public-v0.2.7 > /tmp/vblank-wait-evidence.json
```

The private ROM must match the existing pinned fingerprint. One fresh baseline
scout selects the setup-store PC from the pinned source candidates. Six fresh
custom-core trials compare disabled, enabled and repeated observations for each
scenario; two additional trials use the public core. This is nine fresh cores
including the scout. Baseline and fault sequence summaries refer to the same
tick-1801 clear attempt. Do not compare an earlier baseline wait iteration with
the faulted iteration.

## Recorded result

The [immutable scalar/hash record](experiments/2026-10-23-vblank-wait-sequence-v1.json)
was collected from clean tool commit `431d1dd9890f578135db2d62f0ed49b12f8ddfcf`.
The scout retained 36 compressed events without overflow or unexpected accesses
and selected `$3AE6`. All origin and sequence acceptance gates passed: fresh-core
repeats, tracing noninterference, exact public-core equivalence, prefault equality,
zero host input, activation at tick 1801 and release after exactly one affected
write. No CPU recovery was applied.

| Milestone | Baseline tick | A10/A11 one-write tick |
| --- | --- | --- |
| Poll observes nonzero before clear | 1801 | 1801 |
| First `$B46` clear attempt | 1801, flag becomes zero | 1801, native flag stays nonzero |
| Continued nonzero poll after affected clear | Not applicable | 1801, 5142 contiguous reads in the recorded run |
| Successful clear, zero poll and wait return | 1801 | 1802 |
| Caller successor `$3AF0` and next setup `$3AE6` | 1801 | 1802 |

The attempted zero-write is redirected away from the original flag by the
one-write address fault. The flag remains nonzero, the wait loop continues, and
the next ordinary VBlank clear releases it one tick later. This directly
localizes the bounded delay and is consistent with the prior demo/player lag.
The one-write pulse disconnects at tick 1801; the delayed release at tick 1802
is a later normal write, not continued fault activation.

The six instrumented/plain custom trials and two public trials preserve the
same recorded observations. Repeated enabled sequence summaries match exactly.
This does not establish whole-game equivalence, sustained gameplay trajectory
divergence, an audible difference, native Mac Firefox acceptance or physical
hardware behaviour. The next RAM-stage task remains a source-backed, bounded
search for genuine gameplay divergence while demo inputs continue.
