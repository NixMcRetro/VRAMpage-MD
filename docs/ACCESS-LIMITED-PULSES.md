# v2.3 affected-write pulses

Select **1 affected write (≤1 frame)** in Pulse length, then press a quick address
pair. Limits of 2, 4 and 8 affected writes are also available. For a custom address
or same-lane data pair, choose **Access: Write** and use Pulse selected fault.
Read/both selections are rejected for this mode without replacing an existing
contact. Existing 1/2/4/8-frame controls keep their previous timing.

## What one affected write means

The core counts a byte or 16-bit write when the model changes its mapped address
or outgoing data. An unaffected address/value or the other byte lane does not
consume budget. Read accesses never consume it. An address alias counts even if
it happens to store bytes already present at the redirected destination. It does
not mean one changed byte, one instruction or one specific game variable.

After the last budgeted write is stored, the core clears the fault before the
next bus access. A 32-bit write consists of two 16-bit operations in the pinned
core's [`m68ki_write_32`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.h):
a budget may expire between those halves. All hooked RAM writers share the
budget, including the Z80 bank-write path. Actual Z80 instruction execution
remains untested; byte adapter tests do not establish it.

A contact also expires at the end of its first emulated frame if the budget was
not reached. It may therefore affect zero writes or fewer than requested. The
CPU keeps executing normally after core disconnection for the rest of that
frame; the frontend requests force resume once the tick returns. It never
rewinds memory or inserts a CPU reset. Pause/hidden tabs suspend emulator ticks.

This is a deterministic experimental **transaction-count cutoff**, not a
physical pulse duration, analogue contention model or guaranteed gentle fault.
One altered stack/data write can cause many subsequent changes or a crash.

## Recording and API

v2.3 exports retain the earlier fields and add these pulse fields:

- `mode: "affected-writes"`, `requestedWrites`, `requestedFrames: 1`.
- `releaseReason`: `affected-write-limit` or `frame-limit`.
- `corePulseState`, affected read/write counts, flags and linked CPU intervention.

The core API `arm_logic_write_pulse(kind, a, b, limit)` atomically selects Write
and arms 1–1024 affected writes. The UI offers 1/2/4/8. Invalid kind, pair or
limit leaves the previous state unchanged. `get_logic_pulse_state()` reports:

| Value | Meaning |
| --- | --- |
| 0 | No budgeted pulse in this configuration |
| 1 | Armed; budget remaining |
| 2 | Disconnected because affected-write budget was exhausted |
| 3 | Disconnected at the frame cutoff |
| 4 | Cancelled through explicit disconnect/recovery |

States 2/3 survive disconnect/recovery for export. A new ordinary fault resets
the budget state, a new budgeted pulse replaces it, and cartridge start resets
it to 0. Counters and activation/current frame survive budget exhaustion. Older
cores disable affected-write options while retaining working frame controls.

## Longword integration defect fixed

The new actual-WASM regression exposed a pre-existing omission: the first
16-bit half of a 32-bit RAM write still used the original direct-memory path.
The second half was hooked. The patcher now hooks both halves independently,
retaining original branches with faults off. This changes ordinary **faulted**
longword behavior too; previous v2.2 surveys are historical evidence for their
recorded binary, not current-core predictions. No-fault scalar, RAM, picture
and sampled stereo-audio records matched the v2.2 baseline exactly.

## Actual-cartridge comparison

Two corrected-core surveys used the existing protocol: connect after tick 1800,
observe tick 1801 and through 2401 with no external input. Each survey ran a
baseline twice and all 14 adjacent address pairs twice (30 fresh-core trials).
Every pair repeated identically. Private cartridge SHA-256 and exact JS/WASM
hashes are in the records; no ROM, RAM dump or game screenshot is included.

```sh
# Corrected ordinary one-frame pulse:
node scripts/sweep-ram-pulses.cjs /private/cartridge.md > /tmp/frame.json
# One affected write, with a one-frame maximum:
node scripts/sweep-ram-pulses.cjs /private/cartridge.md --writes 1 > /tmp/write.json
```

[One-write results](experiments/2026-10-22-one-write-pulses.json) and
[corrected-frame results](experiments/2026-10-22-corrected-frame-pulses.json)
compare these cases. All one-write contacts exhausted exactly one affected write.

| Pair | One-write: RAM bytes different at frame end | Frame pulse: RAM bytes different at frame end | One-write sampled output |
| --- | ---: | ---: | --- |
| A1/A2 through A9/A10 | 0 for each pair | 823–1000 | Final picture matched baseline |
| A10/A11 | 886 | 894 | Changing; final picture differed |
| A11/A12 | 886 | 949 | Changing; final picture differed |
| A12/A13 | 1 | 885 | Final picture matched baseline |
| A13/A14 | 1 | 1778 | Final picture matched baseline |
| A14/A15 | 106 | 28 | Static sampled output; final picture differed |

These snapshot differences are measured at **frame end**, after the CPU has
continued beyond the exact budget release. They include downstream behavior,
not just directly altered bytes. Zero differences at that point does not prove
no interference: an aliased write may store an identical value or later writes
may overwrite its consequences. In protocol-v2 JSON this metric is named
`frameEndRAMBytesDifferentFromBaseline`; the historical frame protocol retains
`contactEndRAMBytesDifferentFromBaseline`.

A12/A13 and A13/A14 are smaller-change candidates at this activation point.
A14/A15 demonstrates that a shorter contact can have a worse observed outcome.
All sampled flags remained clear, including static output. Continued internal
demo inputs, healthy gameplay, effects beyond 600 ticks and physical fidelity
remain unverified. Do not automatically rescue or hard-code a desired outcome.

## Regression coverage

Native strict-C and sanitizer checks cover exact budgets, no-op/lane/read
non-consumption, timeout, invalid settings, cancellation and restart. Actual-WASM
original cartridges test both ordinary longword halves, cutoff between halves,
byte-lane identity, zero-write/partial-budget timeout and clean restart. Synthetic
browser tests check limits, keyboard controls, legacy options and export reasons.
See [Testing](TESTING.md) for observed counts and remaining manual acceptance.
