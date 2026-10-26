# v0.5.0 recovery and checkpoints — reviewed design

Status: **Step 1 merged; explicit session checkpoint implementation is under integration review and CI validation.** Based on main
`5d0425a64acb0f883789c67e8c6ec41e5d2c0c02` and upstream core
`6090aff9e9b2f578cd28882bd4571d2e35b1d674`. The public release and `VERSION`
remain v0.4.1. Existing manual CPU Reset and Clean Restart retain their semantics.

The goal is to offer two independent ways to continue experimenting: a bounded
CPU intervention and returning to a deliberately saved machine state. Neither
can guarantee that a game continues. Default operation remains unassisted.

## 1. One armed CPU recovery attempt

Add an **Arm CPU Recovery Once** control near existing recovery controls, with
an explicit armed/off status. It starts off and is never enabled by loading a
configuration, restoring a checkpoint or starting a cartridge.

- Observe the existing `_get_logic_cpu_flags()` only after completed emulated
  frames. Two consecutive eligible frames with HALT bit 2 set trigger one
  CPU-only reset through the existing app recovery function, then disarm.
- STOP bit 1 alone is not failure: games can legitimately STOP while waiting for
  interrupts. Static output, repeated PC values, silence and elapsed wall time
  are not triggers. Running software loops and Z80-only hangs are undetected.
- Held/momentary contacts and pending RAM pulses make a frame ineligible; reset
  the observation count rather than interrupt a deliberate contact. Arming with
  a transient contact in progress is disabled. Persistent faults may be present;
  recovery clears RAM/VRAM faults using the existing checked operations.
- Pause, visibility loss/window blur, manual recovery, imported configuration
  application, Disconnect All Faults, checkpoint operations, Clean Restart and
  new ROM disarm and reset observation. Ordinary fault edits reset the observation
  count but retain arming, so a user can arm before applying a randomiser.
  Automatic pulse expiry alone does not arm anything. No hidden-tab catch-up.
- Consume the single attempt **before** invoking recovery. A rejected/throwing
  getter, rejected clear or recovery failure disarms and pauses for inspection.
  Never retry, escalate to full reboot, restore a checkpoint or fake a bus status.
- On successful intervention preserve play/pause semantics and FM/PSG faults and
  chip state, exactly as manual CPU Reset does. Game code may later reprogram
  sound. A cleared HALT flag is an attempted intervention, not gameplay success.

This is opt-in automatic intervention after arming, not a lockup detector for all
software. One attempt per explicit arm bounds resets even if HALT returns on the
next tick. A game that locks the browser inside `_tick()` cannot be rescued by a
post-frame JS observer; keep that limitation visible in the feature documentation.

Reuse `recoverLogicCPU(2)`, the current fault clear/failure paths and
`cpuInterventions`. Add trigger source, observed flags/frames and attempted
outcome without breaking old experiment exports. Record an abort even when no
CPU action is issued. Do not claim a monotonic counter is the restored game time.

## 2. One explicit session checkpoint

Provide **Save Checkpoint** and **Restore Checkpoint**, with a slot status and
saved frame. First scope: one in-memory slot in this tab, same cartridge load,
core instance, profile and build. No file import/export, persistent browser
storage, automatic capture, multiple slots or automatic rewind. These avoid a
new untrusted binary format and accidental retention of game memory.

Save is available only with a loaded supported Mega Drive cartridge, all four
fault configurations confirmed off, and no held controls or armed pulse. It
captures at an inter-frame boundary without ticking. Reject unavailable telemetry,
unsupported hardware/core capability, allocation failure or invalid length without
replacing an existing valid slot. A clean circuit does not prove uncorrupted RAM;
a saved broken game can still restore broken. Saving preserves prior pause state.

Restore is deliberate and requires a valid same-session slot. Before mutation,
validate slot metadata/capability and expected length; mismatches leave the
running machine unchanged. Then pause, disarm recovery, cancel pulses and pending
held restoration, release controller inputs, flush queued browser audio, and clear
all four fault domains using existing verified clear operations. If any clear
fails, stay paused and report partial changes; do not invoke the native loader.
Successful clears are not rolled back to faults.

Restore the native machine state, reconcile/reset external fault-layer counters
and frame bookkeeping, rebuild views/video caches as necessary, and display the
checkpoint’s saved frame as metadata while remaining paused until explicit Resume. Muting,
volume, theme and keyboard target remain user preferences. Browser audio queues
are never restored; only newly synthesized audio may play after Resume. Block
currently held gamepad/keyboard inputs until released so the first resumed tick
cannot inherit a stale press.

New ROM activation or Clean Restart invalidates the slot; rejected ROM selection
before activation leaves it valid. CPU-only reset does not invalidate it. Saving
again atomically replaces it only after capture succeeds. Restore failure after
native mutation stays paused and invalidates the slot if its safety is uncertain;
report that Clean Restart may be needed. Do not promise transactional rollback.

Restoration starts a new experiment segment: retain the intervention/restore
history in order, record saved and pre-restore frame plus segment ID, and reset
or explicitly delimit external fault counters. Do not silently rewind experiment
history or call the restored machine healthy. Configuration JSON remains settings
only; experiment JSON remains metadata only. Neither contains checkpoint bytes.

## Native evidence and implementation constraints

The pinned core already compiles `core/state.c`. `state_save`/`state_load` cover
work RAM, ZRAM and bank/bus state, IO, VDP/VRAM, sound contexts (including FM/PSG),
68000 registers/cycles/IRQ/stopped flags, Z80 and cartridge context. However:

- `core/state.h` uses unchecked memcpy macros, a fixed `STATE_SIZE`, and pointer-only
  APIs. `state_load` checks a loose version header and calls `system_reset()`
  before completing restoration. A post-load error can leave partial mutation.
- Z80 context includes process pointers; the loader rebinds the IRQ callback.
  This is not a portable or safe user-supplied file format.
- Injected WRAM/VRAM/FM/PSG fault configuration, counters, pulse/trace bookkeeping,
  app state, browser input and queued audio are outside the stock payload.
- `wasm/wasm.c` exposes start/tick but no checkpoint API. Existing configuration
  save/preview/apply does not capture game state.

Keep the buffer owned and private in C; expose capability/save/restore/status,
not an arbitrary pointer-based loader. Only restore bytes generated by this
instance for its still-active cartridge. Validate slot identity and saved length
before load; publish a completed replacement slot atomically. A returned length
check alone cannot prevent an unchecked writer overflow. Before exposing Save,
prove bounds for every supported context against allocated capacity or add bounded
serialization. Reject hardware/mappers without demonstrated coverage. Verify
all context/timing omissions in the first native round-trip slice; patch only
proven gaps. Do not call `state_load` a complete exact checkpoint until the gates
below pass. No memory dump or game-derived payload is committed or exported.

Source anchors: `scripts/work_ram_runtime.c:recover_logic_cpu/get_logic_cpu_flags`,
`site/app.js:recoverLogicCPU/renderFrame/startCartridge/clearAudioQueue`, and pinned
upstream `core/state.c`, `core/state.h`, `core/vdp_ctrl.c:vdp_context_*`,
`core/sound/sound.c:sound_context_*`, `core/z80/z80.h`.

## Ordered implementation and measurable gates

1. **Bounded recovery first:** minimal app/UI/export changes; no new CPU model.
   Deterministic browser tests cover off by default, HALT on frames 1/2, STOP-only,
   intervening clear flag, held/pulse exclusion, pause/blur/new-ROM cancellation,
   throwing/missing capability, partial clear failure, one attempt even on repeated
   HALT, explicit rearm, and no audio reset. Actual-WASM generated cartridges
   demonstrate nested-error HALT and legitimate STOP; compare disabled-policy runs
   with the current baseline. Keep manual reset and Clean Restart regressions.
2. **Private checkpoint core wrapper:** verify capacity and context coverage before
   UI exposure. Original synthetic ROM round trips compare all 64 KiB WRAM,
   ZRAM/banking, CPU/IRQ/HALT, VDP/VRAM/cache, FM/PSG output and cart state. Replay
   identical input from a saved boundary must reproduce subsequent state, pixels
   and finite audio samples/sample counts. Check timers/filter/resampler phase,
   external fault frame/counters and nonzero audio state; RAM-only hashes are
   insufficient. Empty/invalidated slot and unsupported profile reject without
   mutation; failed saves preserve the previous slot. Run native sanitizers.
3. **Checkpoint UI and experiment segments:** exercise Save, deliberate corruption,
   Restore, pause/Resume, stale keyboard/gamepad contacts, queue flushing, failed
   clears, repeated capture, ROM replacement races, CPU Reset and Clean Restart.
   Verify runtime/fallback capability handling; no import or persistent memory.
4. **v0.5.0 integration:** independent specialist review, full applicable source,
   native/WASM and packaged Chromium/Firefox/WebKit checks, meaningful manual Mac
   audio/game checks, matching ROM-free Mac package and provenance. Require all
   seven PR checks before merge and all seven main checks after merge. Bump labels
   and publish a new release only once the milestone is tested; preserve v0.4.1
   tag/assets and leave McRetro.net untouched.

The design checkpoint requires source audit, independent review and Markdown/link
checks. It does not justify rerunning unchanged emulator builds or claiming new
recovery/checkpoint execution. The bounded recovery implementation follows step 1; step 2's exact
state coverage and capacity proof remain release blockers, not completed work.

Independent Luna High source/design review found no blocking issue. The audit was
read-only; no recovery/checkpoint implementation or new execution is claimed.


## Private replay proof checkpoint

The [native proof](CHECKPOINT-REPLAY-PROOF.md) demonstrates capacity guards and
same-instance audio/pixel replay for original synthetic ordinary MD cartridges.
Stock serialized state alone fails PCM replay; a separate audio-runtime supplement
passes the five recorded scenarios. It is not installed in production cores.
Native Blip sanitizer coverage also identified signed-shift UB; equivalent defined
arithmetic preserves all recorded PCM/pixel outputs. Production checkpoint work
still needs complete device/input state, mapper/SRAM policy and validated lifecycle
orchestration. Do not expose Save/Restore on the strength of these narrow cases.
