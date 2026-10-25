# v0.2.1 experimental CPU recovery

The workbench offers two explicit interventions after a fault. They are
emulator debugging actions, not additional simulated hardware shorts. Neither
repairs corrupted RAM or guarantees that gameplay continues.

- **Disconnect and force resume:** disconnect RAM and VRAM faults, then clear the
  68000 core's STOP/HALT bits. Keep its current PC, registers and memory. Execution
  is attempted on subsequent unpaused ticks and can immediately stop again.
- **CPU-only reset:** disconnect RAM and VRAM faults, then call upstream
  `m68k_pulse_reset()`. The core clears stopped state/tracing, selects supervisor
  mode, masks interrupts at level 7, loads SP/PC from reset vectors, and accounts
  for reset cycles. Work RAM, VRAM, VDP, Z80, YM2612 and PSG are not reset. This
  mixed state can fail even when a complete console restart works.

Both CPU interventions leave PSG/FM input faults and sound-chip state unchanged.
This describes the reset operation itself: it calls neither `gen_reset()` nor
`sound_reset()`. Once the CPU runs again, cartridge code may issue ordinary
sound writes and alter registers or audio. **Clean restart** is the workbench's
full sound-chip reset path; removing an audio fault alone affects future writes
and does not guarantee repair of previously changed chip state.
The development workbench also exposes **CPU reset** beside the Randomiser
buttons. It invokes the same CPU-only reset action; it is not a full reboot and
does not change the app's pause state. A **Clean restart** copy immediately
to its right invokes the same full reboot as the original toolbar button.
Use the separate development-source all-fault action below when audio faults
also need to be removed. CPU recovery does not reset the whole system.

These semantics follow the pinned [m68kcpu.c reset implementation](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.c#L348-L397).
Force resume deliberately bypasses normal CPU behavior. It does not synthesize
an interrupt, rewind an exception or establish physical-hardware fidelity.
**Clean restart** remains the full cartridge reboot. Pausing is independent:
recovery never changes pause state, so press Resume if the application is paused.

The compact A11–A15 pair buttons default to **Hold while pressed**, keeping a
write-only fault active only while the mouse/key is down. Explicit **8-frame
pulse** mode disconnects after eight emulated frames without CPU recovery. They preserve play/pause and audio
settings; use CPU reset explicitly if desired. See [RAM pulses](RAM-PULSES.md).

## Development source: disconnect all faults

The new **Disconnect all faults** action is separate from CPU recovery and
**Clean restart**. It cancels app-side RAM pulse completion and
held/momentary restore actions, then attempts to clear VRAM, work RAM, PSG and
FM through their existing APIs. Successful clears are retained if another
domain fails; old faults are never reinstalled as rollback. Status distinguishes
cleared, failed and unavailable state. Older cores without pulse telemetry are
reported conservatively as unverified after an accepted RAM clear. A confirmed
complete clear preserves the app's prior pause state: running stays running and
paused stays paused. Partial, failed or unverified clears pause emulation for
inspection before another tick; successful clears are retained. The synchronous
operation does not run an emulator tick between its domain setters.

This action does not resume/reset the 68000, reload the cartridge, undo earlier
memory writes or restore sound-chip registers. Existing audio clear operations
reset their configuration counters; already-off audio domains are left alone.
A failed RAM clear can leave its core pulse armed, so do not resume until the
reported fault state is understood or use **Clean restart**.

This addition is development source after public v0.4.1. That immutable release
ZIP does not contain this new action. A later workbench milestone will package
it with the remaining coordinated-workbench improvements.

## Recording and compatibility

The original v0.2.1 experimental exports used `2.1-experimental` and remain unchanged as historical evidence. New exports from the current release use `0.4.1-experimental` and retain `cpuInterventions`:
an ordered list of action, current frame, flags before and immediately after.
The after-value precedes execution of the next frame; zero does not prove a
healthy CPU/game. Fault access counters and activation/current frame survive
recovery. Clean restart or loading a cartridge clears intervention history.
No RAM contents are exported. Download the record before restarting.

Development-source exports also include `faultDisconnects`, a separate list of
all-domain removal attempts and per-domain results. These are not CPU
interventions. Status identifies observed runtime state versus tracked or
unavailable state; a failed clear must not be interpreted as restored gameplay.
Clean restart/new-ROM initialization clears this attempt history.

An older core with work-RAM hooks but without `_recover_logic_cpu` can still
play/apply faults; only recovery controls remain disabled. Rebuild the WASM to
use the new controls. Manual actions never enable automatic recovery. The development-source single-arm
option below is separately opt-in; older public releases have no automatic recovery.

## Verification and reproduction

`node tests/test_wasm_logic.cjs site/core/genplus.js` runs original generated
cartridges. Recovery checks resume from STOP into a known instruction, clear
HALT from a nested address error, reject invalid modes, preserve all 64 KiB
synchronously during CPU-only reset, and demonstrate reset returning to the
cartridge entry point. Native adapter tests check counters, fault disconnect and
memory preservation. Synthetic browser tests check keyboard activation, retained
stored writes, legacy compatibility and JSON history/reset behavior.

For a real cartridge: load it, apply a RAM fault, note frame/flags, then choose a
recovery action. Observe subsequent frames and download JSON before Clean
restart. Repeat with the same activation point for each action. A new halt,
static output, broken sound or total failure is a valid result; do not describe
clearing the flags alone as recovered gameplay. Commercial-cartridge recovery
and native macOS behavior remain manual acceptance checks.

## Observed halted-cartridge trial

Using the same cartridge fingerprint and pinned core as the
[initial work-RAM experiments](EXPERIMENTS.md#initial-actual-cartridge-results--22-october-2026),
each action was tested in an independent zero-external-input Node run. Apply
A1/A2 read at tick 1800, run to tick 2000, recover, then run another 120 ticks.
At recovery the CPU was halted (flag 2) and affected reads were 327.

- Force resume: immediate flags became 0, but returned to HALT by tick 2120.
  The sampled RAM digest remained unchanged. Recovery failed in this trial.
- CPU-only reset: immediate flags became 0 and remained 0 at tick 2120. The RAM
  digest changed over the subsequent ticks, indicating resumed activity, without
  establishing normal gameplay or continued demo input.

Both actions retained the exact RAM digest, frame and affected-read count
synchronously on invocation. The unchanged read counter after recovery is
consistent with disconnecting the fault, not evidence of no subsequent reads.
[Scalar/hash results](experiments/2026-10-22-cpu-recovery.json) contain no game bytes.
Reproduce after building:

```sh
node scripts/run-cpu-recovery.cjs /private/path/cartridge.md > /tmp/recovery.json
```

This is one trial per action, not a repeated recovery success rate. Actual
post-recovery visuals, sound and native macOS behavior remain unverified.

## Development source: arm CPU recovery once

**Arm CPU recovery once** is off by default. After explicit arming, two consecutive
eligible completed frames with the 68000 HALT bit set cause one CPU-only reset
attempt, then disarm. A legitimate STOP instruction, static picture, silence or
software loop is not a trigger. It cannot rescue a browser blocked inside a core
tick. The action clears RAM/VRAM faults and preserves FM/PSG exactly like manual
CPU reset; it does not guarantee continued gameplay.

Held/momentary faults and pending RAM pulses defer observation and reset the HALT
streak. Arming is unavailable during those contacts. Ordinary fault edits restart
the streak but retain arming. Pause, blur/hidden tab, manual recovery, imported
configuration application, Disconnect all faults, new ROM activation and Clean
restart disarm. Failed telemetry, rejected clears or rejected recovery disarm and
pause; no repeated attempts, escalation or rewind follows. Re-arm explicitly to
allow another attempt. Additive intervention metadata distinguishes the armed
trigger from a manual action and records attempts/aborts, not gameplay success.

The [v0.5.0 design](RECOVERY-CHECKPOINT-PLAN.md) also covers one-slot in-memory
checkpoints. Those remain planned until serializer bounds and complete state
replay are verified. This recovery slice does not expose checkpoint controls or
advance the public v0.4.1 release.
