# Short RAM fault pulses

The advanced **Pulse selected fault → force resume** control applies the current RAM pair/direction
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

## Affected-write limits (v0.2.3)

Pulse length also offers 1/2/4/8 affected writes, each with a one-frame maximum.
These options require a rebuilt core and Access: Write; they use the same quick
pairs. See [Affected-write pulses](ACCESS-LIMITED-PULSES.md) for cutoff semantics,
export reasons and the longword-hook correction. The frame options below remain.

## Timing, interruption and recording

### Development-source A11–A15 individual eight-frame write pulses

The compact workbench provides ten **RAM WRITE · 8 frames** buttons, one for
every distinct pair within **A11–A15**: A11/A12, A11/A13, A11/A14, A11/A15,
A12/A13, A12/A14, A12/A15, A13/A14, A13/A15 and A14/A15. Clicking a button joins
that pair on **writes only** for **eight emulated frames** (about 134 ms at normal
NTSC playback), then disconnects. These are logical address-line bridges, not
writes to particular numeric RAM locations. The earlier random eight-write/
one-frame shortcut is replaced: these frame pulses have **no affected-write
limit**. The original advanced controls retain their selected limits and
force-resume behavior.

This new burst disconnects at completion without issuing CPU recovery. Use the
nearby **CPU reset** explicitly when wanted. Starting and completing it preserve
the app's pause state; when paused, it waits for emulated ticks after Resume.
Existing RAM/VRAM faults, active pulses and held contacts must be cleared or
released first rather than silently replaced. FM/PSG settings remain unchanged.
Disconnect all faults, CPU reset, cartridge replacement and clean restart cancel
the pending burst so it cannot trigger later recovery or restore a fault.

Download experiment JSON to retain the selected pair, eight-frame duration, result
and no-recovery metadata in `faultPulses`. Stable configuration files do not
store pulses. The A11–A15 restriction and short duration do not guarantee that
gameplay continues or that prior corruption is repaired. Reuse the existing
ordinary frame-based fault model; no additional hardware model or game-specific edits are
introduced.

### Existing advanced pulse behavior

The frontend checks completion immediately after each emulator tick, before the
next tick can run, including when animation catch-up executes multiple ticks.
Completion disconnects and uses the same explicit force-resume API as v0.2.1.
The CPU can halt again; no repeated automatic recovery is scheduled. Selecting
another quick pair replaces the pulse rather than stacking faults.

Pause and hidden tabs suspend emulated ticks, so a pending pulse waits; it is
not a wall-clock timer. Resume advances the remaining frames. Manual disconnect,
CPU recovery, a successfully applied replacement fault or VRAM activation cancels
the pending pulse. Invalid selections leave it intact. Loading a cartridge or
Clean restart clears pulse/intervention history and cannot trigger stale recovery.
A stopped CPU does not stop the emulator's frame counter, so the scheduled
contact still ends. Recovery leaves the app's pause state unchanged.

Current experiment exports use `0.4.1-experimental` and include `faultPulses`, ordered
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

## Development-source sustained write option

The compact A11–A15 controls default to **8 frames**. Choose **Hold** to latch
a write-only pair without a frame or affected-write limit, then click the active
pair again to release it. Explicit release performs no CPU recovery and does not
undo earlier writes. Capability, existing memory-fault and pulse guards remain.
Disconnect/recovery/restart actions clear the owned contact so a later release
cannot clear a newer fault. This option does not change the advanced historical
pulse controls above. Sustained faults can still halt or corrupt games.

## Measured candidates

**Historical v0.2.2 evidence:** a repeated actual-core [one-frame survey](PULSE-EXPERIMENTS.md) at tick 1800
found A14/A15 left 28 RAM bytes different at the contact boundary with later
sampled output matching baseline. A10/A11 produced different, changing output.
These are activation-specific observations, not safe presets or proof that demo
input continues. Most other pairs gave static output despite clear CPU flags.

The v0.2.3 longword correction changes ordinary faulted writes. Use the
[corrected-core comparisons](ACCESS-LIMITED-PULSES.md#actual-cartridge-comparison)
for current observations rather than treating the earlier survey as universal.
