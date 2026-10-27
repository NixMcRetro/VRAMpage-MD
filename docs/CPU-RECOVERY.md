# v0.2.1 experimental CPU recovery

Development-source CPU Reset/Force Resume also retain [RGB encoder contacts](RGB-ENCODER-INPUTS.md). Direct RGB edits do not arm/cancel recovery. Disconnect All clears the additional Z80 RAM and RGB domains; Clean Restart clears every domain.

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
sound writes and alter registers or audio. **Clean Restart** is the workbench's
full sound-chip reset path; removing an audio fault alone affects future writes
and does not guarantee repair of previously changed chip state.
The development workbench also exposes **CPU Reset** beside the Randomiser
buttons. It invokes the same CPU-only reset action; it is not a full reboot and
does not change the app's pause state. A **Clean Restart** copy immediately
to its right invokes the same full reboot as the original toolbar button.
Use the separate development-source all-fault action below when audio faults
also need to be removed. CPU recovery does not reset the whole system.

These semantics follow the pinned [m68kcpu.c reset implementation](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.c#L348-L397).
Force resume deliberately bypasses normal CPU behavior. It does not synthesize
an interrupt, rewind an exception or establish physical-hardware fidelity.
**Clean Restart** remains the full cartridge reboot. Pausing is independent:
recovery never changes pause state, so press Resume if the application is paused.

The compact A11–A15 pair buttons default to **Hold while pressed**, keeping a
write-only fault active only while the mouse/key is down. Explicit **8-frame
pulse** mode disconnects after eight emulated frames without CPU recovery. They preserve play/pause and audio
settings; use CPU Reset explicitly if desired. See [RAM pulses](RAM-PULSES.md).

## Development source: disconnect all faults

The new **Disconnect All Faults** action is separate from CPU recovery and
**Clean Restart**. It cancels app-side RAM pulse completion and
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
reported fault state is understood or use **Clean Restart**.

This addition is development source after public v0.4.1. That immutable release
ZIP does not contain this new action. A later workbench milestone will package
it with the remaining coordinated-workbench improvements.

## Recording and compatibility

The original v0.2.1 experimental exports used `2.1-experimental` and remain unchanged as historical evidence. New exports from the current release use `0.4.1-experimental` and retain `cpuInterventions`:
an ordered list of action, current frame, flags before and immediately after.
The after-value precedes execution of the next frame; zero does not prove a
healthy CPU/game. Fault access counters and activation/current frame survive
recovery. Clean Restart or loading a cartridge clears intervention history.
No RAM contents are exported. Download the record before restarting.

Development-source exports also include `faultDisconnects`, a separate list of
all-domain removal attempts and per-domain results. These are not CPU
interventions. Status identifies observed runtime state versus tracked or
unavailable state; a failed clear must not be interpreted as restored gameplay.
Clean Restart/new-ROM initialization clears this attempt history.

An older core with work-RAM hooks but without `_recover_logic_cpu` can still
play/apply faults. Manual CPU actions require that API; the preference switches
remain selectable and report Automatic Recovery Unavailable. Rebuild the WASM to
use recovery. Manual actions never change the On/Off preferences. Current
development defaults both On; older public releases have no automatic recovery.

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

<a id="development-source-arm-cpu-recovery-once"></a>
## Development Source: Ordered Recovery

The compact **Force Resume** and **CPU Recovery** On/Off switches sit beside
Randomiser. Both initially **On**, following the user's updated instruction;
this supersedes the earlier default-Off one-shot arming design. Their preferences
survive pause, blur and cartridge changes. Turn both **Off** for unassisted outcomes.
The advanced **Disconnect and Force Resume** action remains a manual intervention.

1. Observe HALT bit2 on two consecutive eligible completed frames.
2. If Force Resume is On, attempt it once while preserving CPU registers/PC and
   RAM. If CPU Recovery is On, wait eight further eligible completed HALT frames
   (~0.13 s). A frame without HALT cancels escalation.
3. If HALT persists for that window, issue one CPU-only reset. If Force Resume is
   Off, CPU Recovery can instead issue its one reset after the initial two frames.

Neither intervention directly clears RAM or resets VDP/Z80/FM/PSG. Both disconnect
RAM/VRAM faults; development source also removes the independent Z80 RAM write
bridge before intervention. Audio faults remain. ROM startup code after CPU Reset may itself
initialize RAM or reprogram sound. STOP alone, static pictures, silence, unchanged
RAM access counters and software loops are not triggers. No observer can rescue a
browser blocked inside a native tick. An eight-frame wait prolongs frozen output;
it does not guarantee additional glitches or successful gameplay.

One sequence is allowed per explicit fault experiment. Automatic helper clears
cannot replenish its budget. A new fault action, toggle change, cartridge/Restart
or explicit Resume permits another sequence. Pause, blur/hidden, checkpoints,
Disconnect All Faults and manual CPU interventions cancel pending escalation;
they preserve the On/Off preferences. Held/momentary contacts and pending RAM
pulses defer observation, including their ending frame. Native/clear/telemetry
failures consume the opportunity and pause for inspection without blind retry.
The status distinguishes watching, waiting, paused, unavailable and used/cancelled.

Experiment exports include `automaticRecovery` preferences and the eight-frame
threshold, plus per-action trigger, stage, observed frames and issued/rejected/
aborted outcomes. A reset accepted before a post-action telemetry failure remains
recorded as issued. Export comparison treats absent older policy fields as unknown.

Manual [session checkpoints](SESSION-CHECKPOINT-API.md) are implemented separately;
there is no automatic capture, rewind or Clean Restart escalation. VERSION and
public v0.4.1 assets remain unchanged.
