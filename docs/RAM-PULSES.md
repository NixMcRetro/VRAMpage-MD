# Short RAM fault pulses (v2.2 experimental)

**Pulse selected fault → force resume** applies the current RAM pair/direction
for 1, 2, 4 or 8 emulated frames, then disconnects the fault and attempts forced
CPU resume. One NTSC frame is approximately 17 ms at normal playback speed.
These are frame-length contacts, not per-access or cycle-accurate pulses. A
single frame may corrupt many accesses; smaller or recoverable damage is not
guaranteed. Nothing edits game-specific variables or targets known game objects.

The 14 quick-pair buttons cover adjacent address lines A1/A2 through A14/A15.
Each selects address faults on **writes** and starts a pulse with the selected
length. These are address-line bridges, not matched numeric RAM locations or
cartridge-specific safe settings. Writes are selected explicitly because redirected
writes can leave persistent RAM changes after disconnect. Read faults do not
modify source RAM directly, but erroneous reads can cause the CPU to write bad
state. The ordinary selectors still permit read/write/both and same-lane data
pairs for the main pulse button.

## Timing, interruption and recording

The frontend checks completion immediately after each emulator tick, before the
next tick can run, including when animation catch-up executes multiple ticks.
Completion disconnects and uses the same explicit force-resume API as v2.1.
The CPU can halt again; no repeated automatic recovery is scheduled. Selecting
another quick pair replaces the pulse rather than stacking faults.

Pause and hidden tabs suspend emulated ticks, so a pending pulse waits; it is
not a wall-clock timer. Resume advances the remaining frames. Manual disconnect,
CPU recovery, a successfully applied replacement fault or VRAM activation cancels
the pending pulse. Invalid selections leave it intact. Loading a cartridge or
Clean restart clears pulse/intervention history and cannot trigger stale recovery.
A stopped CPU does not stop the emulator's frame counter, so the scheduled
contact still ends. Recovery leaves the app's pause state unchanged.

Experiment exports use `2.2-experimental` and include `faultPulses`, ordered
records of kind/access/zero-based line indices, requested frame count, start/end
frame, active/completed/cancelled status and cancellation reason. For address
pairs, indices 0–14 correspond to A1–A15. A completed pulse also records affected reads/writes and the CPU flags at the
end of the contact, before recovery. It records whether its
recovery request was accepted and the associated `cpuInterventions` index.
Acceptance does not prove resumed gameplay. RAM bytes are never exported.

## Reproduce

1. Load a private cartridge, open Logic / work RAM, and choose 1 frame.
2. Press an adjacent-address quick pair. Observe counters, CPU flags and output.
3. Download JSON before clean restart. Repeat from the same reset and activation
   frame to compare configurations. Failed or unchanged output is a valid result.
4. For a data pulse, select Data, two lines in one byte lane and Write, then use
   **Pulse selected fault → force resume**. A read experiment may be compared
   separately; it is not a promise of persistent or gentler corruption.

The scheduler/keyboard/export/cancellation checks use a synthetic browser core.
They establish frame counts and state transitions, not successful Sonic recovery
or electrical fidelity. Actual-core browser results are recorded in [Testing](TESTING.md).
See [CPU recovery](CPU-RECOVERY.md) for the intervention's limitations.

## Measured candidates

A repeated actual-core [one-frame survey](PULSE-EXPERIMENTS.md) at tick 1800
found A14/A15 left 28 RAM bytes different at the contact boundary with later
sampled output matching baseline. A10/A11 produced different, changing output.
These are activation-specific observations, not safe presets or proof that demo
input continues. Most other pairs gave static output despite clear CPU flags.
