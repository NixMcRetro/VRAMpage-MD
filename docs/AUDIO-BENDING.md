# Audio bending

The v0.4.0 runtime models digital write-input bridges for the Mega Drive
PSG and FM chips. These controls are experimental, off by default, and absent
from earlier public packages. They alter chip inputs before synthesis, never
apply distortion to mixed samples, and do not establish electrical accuracy.

## Signal paths and ownership

The 68000 can access FM through the Z80 window at `$A04000` and `$A04001` when
bus ownership permits. Z80 code accesses the corresponding FM ports at `$4000`
and `$4001`; additional bank/port selection stays with the native emulator.
The Z80 has its own sound-driver RAM. The 68000 requests its bus through
`$A11100` and controls Z80 reset through `$A11200`. Original synthetic fixtures
exercise this ownership sequence. These bridges do not corrupt Z80 RAM or
change arbitration. Those would be separate models requiring verified mapping.

PSG writes reach the synchronized `psg_write` input, including the Z80 `$7F11`
route. FM writes pass through the shared YM2612/YM3438 handler with the original
port and cycle timestamp. A selected pair D0-D7 is low dominant: if either bit
is low both become low; if both are high both remain high. FM address-latch
bytes and data bytes are both affected, so corrupted input can select another
register as well as change a parameter. See [PSG semantics](PSG-INPUT-DATA-SEMANTICS.md)
and [FM semantics](FM-DATA-BRIDGE.md) for API and counter details. Counters
aggregate chip-input writes, without attributing them to a processor.

## Controls and recovery

Choose two distinct inputs and apply each bridge independently. Removing a
bridge affects future writes and does not repair earlier chip state. Clean
restart/new-ROM initialization clears both bridges and counters. A Z80-only
partial FM reset preserves the FM bridge and aggregate counters, while native
chip registers follow their ordinary reset behavior. CPU recovery is not a
guarantee of restored audio or game state. Both existing CPU recovery actions
clear memory faults but leave audio fault configurations unchanged. The separate
development-source **Disconnect all faults** action attempts every domain,
preserving play/pause on confirmed complete clears and pausing failed or
unverified clears for inspection. It does not reset the CPU or repair registers; inspect its
per-domain status and explicitly resume when ready. Export experiments to retain the
separate settings, exact decimal counters and source identification. As with
the existing per-chip removal controls, clearing an active audio configuration
resets its counters; export first if those measurements need to be retained.

Click **Enable Sound** after loading a cartridge. Browsers require a user
gesture; if audio remains blocked, check site permissions and retry. **Mute
Sound** stops submitting new output buffers without changing fault settings.
Start at low volume: corrupted register writes may produce loud tones or stuck
notes. Muting and clean restart are useful recovery options.

The browser schedules stereo 44.1 kHz buffers, with a 200 ms future-start limit
and a 25 ms resynchronization offset when scheduling falls behind. In the public
v0.4.1 build, pause/visibility reset that cursor while already submitted short
buffers can finish. Development-source stabilisation now stops and disconnects
queued buffers on pause, mute, visibility changes and validated cartridge
replacement/clean restart; ended sources release their connections. Invalid ROM
headers/sizes and failed buffer allocation leave the current audio untouched.

A non-running browser AudioContext cannot consume scheduled buffers. Emulation
continues to produce its normal sound output, but the frontend discards that
unplayable output instead of allocating an accumulating queue. After context
resume it schedules fresh buffers near current time. This does not resume a
halted CPU, clear fault settings, reset sound-chip registers or smooth the PCM
samples during normal playback. An underrun can still cause a gap. Automation
observes native audio routing and generated samples, not sound heard through
speakers or actual macOS background throttling.

## Acceptance

Require normal/runtime disabled equivalence, finite stereo samples, active
changes at documented chip writes, deterministic repetitions, preserved native
busy/status timing, independent bridge traffic and explicit reset/removal
semantics. Actual Z80 routes, browser gesture/mute and bounded scheduling need
their own evidence. No commercial cartridge, physical hardware or audible
validation is implied by synthetic tests. Publish v0.4.0 only after these gates,
three-browser CI and complete package/provenance verification pass.
