# RGB Encoder Input Contacts

**Development Source — Experimental.** These controls follow the
[CXA1145 research](VIDEO-ENCODER-RESEARCH.md). They are off by default and are
not included in the published v0.5.0 download or hosted page. No new release or
website deployment is part of this change.

After loading a cartridge, use **Cut R**, **Cut G**, **Cut B** or one of the
**Join** buttons below the memory controls. Cuts toggle independently; selecting
a different joined pair replaces the previous pair. **Reconnect RGB** removes
all encoder contacts. The pressed state shows the configured contacts.

## Model and Limits

This is an RGB input approximation, not a complete CXA1145 circuit. The core
already supplies RGBA byte codes. Each source code divided by 255 stands for a
normalized input voltage; it is neither a calibrated voltage nor a conversion
to linear-light sRGB. The pinned core's CRAM-to-palette path supplies no measured
analogue transfer function.

For each pixel, disconnected sources are first replaced by zero. A cut means
black termination with the same normalized source impedance as a connected
source. It does **not** predict a floating open input. One ideal, zero-resistance
pair join then produces the arithmetic mean of those two source voltages,
assuming equal source impedances. The third channel stays independent. Output
codes round half up: joining 255 and 0 gives 128; joining 5 and 0 gives 3.
Alpha is preserved. A cut R joined to an uncut G can therefore receive G's
signal through the join; the cut is on the source side of that junction.

All eight cut masks can coexist with any one of the three joined pairs. Multiple
simultaneous pair joins, unequal impedances, leakage, loading of the VDP,
composite encoding, subcarrier, sync, receiver timing and mono audio are outside
this model. This output fault cannot rescue a stopped game or establish what a
physical motherboard short would do.

## Output and Lifecycle

The transform operates on the copied 320×224 canvas buffer after the existing
legacy missing-row recovery. It does not write the native framebuffer, CPU,
RAM, VRAM, audio registers or generated PCM, and it does not advance emulation.
It is independent of all memory/audio faults and works with the normal fallback
core as well as the runtime core.

**Raw Emulator Output** bypasses both display adaptations without removing
configured encoder contacts. Status and exported metadata distinguish configured
from effective contacts. Direct RGB edits and RGB-only configuration changes do
not arm or cancel automatic CPU recovery. **CPU Reset** and **Force Resume**
retain RGB contacts. **Clean Restart** or a successful new cartridge load removes
them. Rejecting a staged cartridge preserves the running configuration.

**Disconnect All Faults** includes RGB contacts as a sixth domain. A successful
clear preserves play/pause. **Save Checkpoint** refuses configured RGB contacts,
including bypassed contacts; **Restore Checkpoint** clears them through the
all-domain action before restoring, and remains paused.

## Files and Verification

Configuration schema v4 adds `rgbEncoder: {"cutMask": 0, "pair": null}`. Mask bits
0/1/2 select R/G/B, and pair indexes are distinct values 0–2. Imports from v1,
v2 and v3 explicitly turn RGB off. Experiment exports retain root schema 1 and
add `rgbEncoderFault`, including model `rgb-input-code-voltage-v1`, configuration,
effective state and bypass reason. Comparison marks absent older fields Unknown.

`tests/test_rgb_encoder.cjs` contains literal RGBA oracles, all cut masks, grey
ramps and exhaustive joined-channel code pairs. Browser logic tests cover
configuration, lifecycle and independence. The actual-core browser case checks
literal canvas colours plus byte-identical native frame, full Work RAM, available
Z80 RAM and generated stereo PCM under paused RGB edits on runtime and fallback
profiles. These synthetic checks do not establish physical or audible accuracy.
