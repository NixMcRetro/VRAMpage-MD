# Eight-write object-memory follow-up

## Predefined question

The [one-write candidate](RAM-GAMEPLAY-CANDIDATE.md) redirected a byte write at
player status offset `$D022` to `$C022`, while every monitored frame/demo/player
tuple matched baseline. That record remains immutable. This is one separately
defined follow-up, not a revision of that experiment or an escalating sweep.

Keep the generic A12/A13 address contact, activation before tick 1801 at completed
frame 1800, 2400-tick bound, exact public v0.2.7 core and supported private ROM.
Change only the predefined affected-write budget from one to eight:
`_arm_logic_write_pulse(1, 11, 12, 8)`. The new trial name is
`a12-a13-object-region-eight-writes`; protocol `object-alias-eight-writes-v1`.

## Source basis and uncertainty

The matched Revision 0 source is sonicretro/s1disasm commit
`15dfa3a6ee4c53aeb482233e493755c84b4f3479`. Its complete build matches ROM SHA-256
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
`_Constants.asm` defines player status at offset `$22`, positions at `$08` and
`$0C`, velocities at `$10` and `$12`, and ground speed at `$14`.
`_incObj/01 Sonic.asm` runs movement before `SpeedToPos` on the ordinary movement
path. Object memory occupies `$D000` through `$EFFF`; this contact redirects
eligible writes into the pre-object buffers at `$C000` through `$CFFF`, while
preserving `$F62A` and the `$FFxx` stack region.

A simple movement sequence can involve one status-byte write, one ground-speed
word, two velocity words and two position longwords. The runtime counts changed
bus accesses, so two longwords can occupy four word accesses. Eight is a small,
fixed opportunity to extend beyond the previously observed first status write.
Source order does not establish the actual branch path, next seven affected
addresses, instruction PC or whether the pulse will reach a kinematic field.
The first-write diagnostic cannot provide that full sequence. Do not claim it
was observed. No game-variable targeting, instruction edits or CPU recovery are
introduced; the existing generic fault model applies to every eligible write.

## Fixed acceptance

Reuse the prior observer driver, exact package verifier, trace invariants and
phase/trajectory analysis without changing their defaults or criteria.

- Six fresh public cores: baseline and eight-write fault, tracing off/on/repeated.
- Equivalent reset and prefault state, zero host input, deterministic repeats and
  observational trace noninterference. Release after exactly eight affected bus
  writes in tick 1801. Invalid metadata or an incorrect count fails integrity.
- Distinguish protocol integrity from scientific success. An unchanged game,
  frozen execution or a source-hypothesis miss can be a valid negative result.
- Positive evidence requires the source-consistent object alias, active demo and
  internal cursor/pad progression, player ID 1 and no recorded CPU STOP/HALT.
  Preserve the prior scopes: CPU/demo ticks 1802 through 2400, player identity
  ticks 1799 through 2400.
- Use ticks 1803 through 2398 and offsets -2 through +2. Require exactly one
  offset matching all 596 demo tuples, no missing pairs, shared by both repeats.
  Require at least one pixel of wrap-aware max-axis position difference for at
  least 60 consecutive ticks at that offset. A whole-sequence phase shift or
  frame-hash difference alone does not qualify.
- Record clean source identity and hashes for all reused and new tool/test files.
  Keep full timelines in memory; publish only bounded scalar samples, hashes,
  first-write metadata and comparison summaries.

Do not adjust the budget, activation time, phase range or threshold after seeing
the result. Preserve the one-write record and all earlier evidence. No normal
app, emulator API, version, release artifact or Mac download change is planned.
A bounded result does not establish audible, native Mac or physical behaviour.
