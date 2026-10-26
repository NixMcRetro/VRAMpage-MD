# Session Checkpoint Implementation Contract

Implementation scope: one explicit in-memory slot in the current runtime core,
with no file import/export or automatic restore. Based on the reviewed v0.5.0
plan and merged main `0b8263c`. Normal/older cores may omit these methods and
continue running with checkpoint controls disabled. VERSION remains0.4.1 until
release gates are complete. Root coordinates JS/UI/history; native author owns
backend/hooks and actual-WASM tests on an isolated branch.

## Scalar Native API

Export only from the runtime profile using the existing KEEPALIVE conventions:

| C function (JS adds `_`) | Result |
| --- | --- |
| `get_session_checkpoint_support()` | 1 only for a supported loaded profile, otherwise0; pure read |
| `get_session_checkpoint_ready()` | 1 only for a valid same-session slot, otherwise0; pure read |
| `get_session_checkpoint_saved_frame()` | Captured app/core logic frame; use Ready to distinguish frame0 from Empty |
| `save_session_checkpoint()` | Status below; synchronous; no emulator tick |
| `restore_session_checkpoint()` | Status below; synchronous; no emulator tick |
| `discard_session_checkpoint()` | Void; invalidate slot without changing the machine |

Statuses: 0 OK, 1 Unsupported Profile, 2 Unsafe (active fault/pulse/input),
3 Empty, 4 Capture Failed, 5 Restore Failed (machine may have changed),
6 Session/Profile Mismatch (rejected before machine mutation).

Do not accept payload pointers/bytes from JS. No snapshot bytes are exposed.
Native `_start()` invalidates the slot before restarting; successful startup
establishes a new generation. JS also discards before an accepted ROM is copied
into native memory. Rejected staged files or failed allocation before native
mutation preserve the old slot. CPU-only reset preserves the slot.

## Capture and Restore

Restrict to ordinary MD, plain3/6-button pads (including unused ordinary ports),
and validated ordinary SRAM if its complete64KiB backing store is safe; otherwise
reject backup-memory cartridges. Exclude CD/SVP/EEPROM/custom mappers, other
peripherals, unknown contexts and incompatible audio profiles. Hardware eligibility
uses resolved generic core fields, never game-title whitelists. Do not reject a
supported machine merely because its CPU is halted or its memory is corrupted.

Save requires all native fault configurations and armed pulses off, and neutral
native input. The UI also rejects held/momentary contacts and host controls. Poll
current host input before capture without running a frame. Save preserves prior
play/pause state. Use privately owned current/spare storage: validate profile,
bounds and every component before publishing the replacement slot. Failed saves
leave the previous valid slot usable. Prove the stock writer bound for every
eligible state path before calling its pointer-only serializer; a returned-length
check cannot prevent overflow. Keep guards and meaningful refusal tests.

Capture stock core state, omitted audio runtime state, complete eligible pad
protocol state, optional ordinary SRAM, and raw framebuffer/viewport data needed
to display the checkpoint immediately while paused. Retain live allocation
pointers and validate identity/length/profile before loading. Do not restore host
browser sources or app preferences. Preserve counter/history semantics explicitly.

Restore requires native faults/pulses off; the UI pauses, disarms recovery, cancels
held restoration callbacks, releases host controls, flushes queued audio and runs
the existing verified all-domain clear first. Failed clears stop before native
restore. Native validation errors1/2/3/6 precede mutation. Once stock load begins,
a later failure5 invalidates uncertain slot state and leaves the UI paused; do
not promise rollback. On success retain the slot for repeated explicit Restore.
Never tick to paint a saved frame: restore the saved raw framebuffer and draw it.

## UI and Records

Put **Save Checkpoint** and **Restore Checkpoint** with the existing advanced
Logic / Work RAM recovery controls, with a session-only saved-frame status.
All buttons/labels use Title Case. Restore remains paused until explicit Resume.
Hold currently active keyboard/gamepad controls suppressed until release so a
stale press cannot immediately change the restored machine. Muting, volume,
theme and keyboard target remain user preferences.

Keep CPU and all-fault history; add `checkpointEvents` and a segment counter to
experiment exports, never checkpoint bytes. Record Save/Restore attempt, native
status, before/after observed frame, saved frame and segment. A successful Restore
starts a new segment; a possible partial native restore failure also delimits an
uncertain segment. Current logic frame remains observed monotonic bookkeeping,
not a claim that saved game time was restored. Record before/after fault-counter
baselines if they reset during load. Clean Restart/new-ROM initialization clears
slot/history according to existing lifecycle rules.

## Gates

Independent native and JS review; meaningful positive/negative/partial-failure
checks; native sanitizers and actual-WASM round trips; audio/pixel equality,
3/6-button protocol and ordinary SRAM cases; same-cartridge/module/lifecycle
invalidation; immediate restored image; held-input release; defaults off/empty;
legacy fallback; all seven PR and main checks; matching ROM-free package.
No public v0.5.0 release or McRetro.net action is authorized by this contract.
