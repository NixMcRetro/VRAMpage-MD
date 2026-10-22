# v2.1 experimental CPU recovery

The work-RAM panel offers two explicit interventions after a fault. They are
emulator debugging actions, not additional simulated hardware shorts. Neither
repairs corrupted RAM or guarantees that gameplay continues.

- **Disconnect and force resume:** disconnect RAM and VRAM faults, then clear the
  68000 core's STOP/HALT bits. Keep its current PC, registers and memory. Execution
  is attempted on subsequent unpaused ticks and can immediately stop again.
- **CPU-only reset:** disconnect both fault domains, then call upstream
  `m68k_pulse_reset()`. The core clears stopped state/tracing, selects supervisor
  mode, masks interrupts at level 7, loads SP/PC from reset vectors, and accounts
  for reset cycles. Work RAM, VRAM, VDP, Z80, YM2612 and PSG are not reset. This
  mixed state can fail even when a complete console restart works.

These semantics follow the pinned [m68kcpu.c reset implementation](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68kcpu.c#L348-L397).
Force resume deliberately bypasses normal CPU behavior. It does not synthesize
an interrupt, rewind an exception or establish physical-hardware fidelity.
**Clean restart** remains the full cartridge reboot. Pausing is independent:
recovery never changes pause state, so press Resume if the application is paused.

## Recording and compatibility

Experiment JSON uses model version `2.1-experimental` and adds `cpuInterventions`:
an ordered list of action, current frame, flags before and immediately after.
The after-value precedes execution of the next frame; zero does not prove a
healthy CPU/game. Fault access counters and activation/current frame survive
recovery. Clean restart or loading a cartridge clears intervention history.
No RAM contents are exported. Download the record before restarting.

An older core with work-RAM hooks but without `_recover_logic_cpu` can still
play/apply faults; only recovery controls remain disabled. Rebuild the WASM to
use the new controls. No automatic or repeated recovery is performed.

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
