# One-frame address-pulse survey — 22 October 2026

This survey tests the v2.2 quick-pair behavior without changing the fault model
or choosing game-specific RAM locations. It identifies configurations worth
investigating; it does not establish safe settings or physical electrical behavior.

**Historical binary:** v2.3 regression work found that the first half of a
32-bit write bypassed the fault hook in v2.2. This report preserves the recorded
v2.2 outcomes. Reproducing it requires the source/runtime from commit
`f26501f` and its corresponding core, not a newly patched core. See
[corrected-core comparisons](ACCESS-LIMITED-PULSES.md#actual-cartridge-comparison)
for current results. No-fault baseline samples still matched exactly.

## Protocol and reproducibility

Use the pinned core built with Emscripten 4.0.23. From the repository root:

```sh
node scripts/sweep-ram-pulses.cjs /private/path/cartridge.md > /tmp/pulse-survey.json
```

The default protocol uses a fresh core and cartridge boot for every trial, all
external controller inputs zero, and `_sound()` consumed after every tick.
It runs a no-fault baseline twice and each of the 14 adjacent address write pairs
twice: **30 trials**. Finish tick 1800, connect before tick 1801, disconnect and
request force resume after that tick, then observe another 600 ticks through
2401. At normal NTSC speed the contact represents approximately 17 ms; this is
Node frame stepping, not browser wall-clock timing or audible playback testing.

`--activation N`, `--pulse N`, `--observe N` and `--core path/to/genplus.js`
allow other explicit protocols. The survey's default 1-frame pulse matches the
browser control; the CLI accepts other positive frame counts for research.
The expected upstream pin, exact tested JS/WASM digests, ROM SHA-256, Node
version and architecture are recorded. A supplied binary's provenance is not
independently proven by its API or a declared pin.

The [recorded results](experiments/2026-10-22-one-frame-pulses.json) use the supplied
512 KiB backup with SHA-256
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
Private inspection of frame 1800 showed a Green Hill gameplay scene. The internal
demo-controller input stream was not traced. No ROM, RAM dump or game screenshot
is included in the repository.

## Measurements and their limits

- Compare the 64 KiB RAM snapshot at the end of the contact with the no-fault
  snapshot at the **same** tick. Report only a changed-byte count and hashes.
  This includes CPU control-flow consequences and normal writes that diverged;
  it is not a count of directly shorted cells or a damage percentage.
- Record affected-access counters and CPU flags before recovery, immediately
  after recovery, and later sample points. These counters count changed bus
  transactions, not distinct bytes or all CPU accesses.
- Hash the native visible 320×224 RGBA picture from the 640-pixel source stride,
  both audio channels' emitted float bytes and RAM at ticks 1800, 1801,
  1861, 1921, …, 2401. Audio digests cover those sampled ticks only.
- Compare consecutive post-contact pictures: ten samples give nine intervals.
  Moving output does not prove normal gameplay; static output does not alone
  prove a stopped CPU. STOP/HALT flags do not detect every software hang.
- Compare every repeated trial's complete scalar/hash record. A mismatch keeps
  both records rather than silently selecting one. Individual trial errors are
  recorded separately and repeated, with no fabricated comparison; a failed
  baseline aborts because a valid comparison is unavailable.

## Results at this activation point

Every first trial matched its independent repeat, including the baseline. A
second complete 30-trial sweep reproduced the same scalar/hash report.
All 14 pulses ended with flags 0 and accepted force-resume requests. Every request
preserved the RAM snapshot synchronously. All later sampled flags also stayed 0.
Most configurations nevertheless produced static sampled output.

| Write pair | Affected writes in contact | RAM bytes different at contact end | Changed picture intervals / 9 | Final picture matches baseline |
| --- | ---: | ---: | ---: | --- |
| A1/A2 | 743 | 954 | 0 | No |
| A2/A3 | 85 | 962 | 0 | No |
| A3/A4 | 31 | 944 | 0 | No |
| A4/A5 | 1202 | 940 | 0 | No |
| A5/A6 | 1212 | 964 | 0 | No |
| A6/A7 | 1179 | 978 | 0 | No |
| A7/A8 | 296 | 756 | 0 | No |
| A8/A9 | 1207 | 985 | 0 | No |
| A9/A10 | 1237 | 989 | 0 | No |
| A10/A11 | 15 | 894 | 9 | No |
| A11/A12 | 55 | 948 | 0 | No |
| A12/A13 | 86 | 406 | 9 | Yes |
| A13/A14 | 312 | 1084 | 9 | Yes |
| A14/A15 | 46 | 28 | 9 | Yes |

All final RAM hashes differed from baseline, even where the final picture
matched. The baseline's ten post-contact pictures were all different.

**A14/A15** is a useful candidate for a smaller immediate change at this specific
frame: 28 differing bytes with sampled output matching the baseline. That does
not imply the changed state is harmless or that other activation times work.
**A10/A11** is a candidate for visible divergence with continuing output, despite
only 15 affected writes and much larger downstream RAM differences. Private inspection at tick 2401 still showed Green Hill gameplay with the
in-game timer advanced from 0:10 to 0:20, but it has not
established continued demo input or the desired obstacle-sticking outcome.

A low affected-write count is not a reliable measure of a gentle experiment.
The next useful control is a deterministic limit on affected accesses, followed
by trials at multiple activation points and diagnostic observation of demo input.
Do not automatically rescue static output or alter game variables to get a result.

## Automated checks

`node tests/test_pulse_sweep.cjs` uses an original synthetic core fixture to check
apply/tick/sound/disconnect ordering, zero input, exact frame duration,
RAM-difference calculations, repeat mismatch preservation, error recording,
static-picture detection and invalid settings/buffers. It does not emulate the
68000; the cartridge survey uses the actual rebuilt WASM separately. The helper
suite runs in `bash scripts/test.sh`. Application source and browser behavior are
unchanged by this research-only change.
