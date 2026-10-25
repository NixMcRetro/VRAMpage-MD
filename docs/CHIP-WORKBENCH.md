# Compact chip workbench

The v0.4.1 workbench brings the existing VRAM and Work
RAM diagrams together with FM and PSG controls in one compact sidebar. These
are conceptual signal diagrams, not physical chip pinouts. The PSG is a logical
function inside the Mega Drive VDP.

Connections stay within each chip. A selected leg on one chip cannot be joined
to a leg on another. Use each chip's action selector to choose a bridge or the
supported line-disconnect model. Signal labels remain inside the bodies and
external legs stay short. Buttons support keyboard activation and show their
selection, connection or crossed state.

VRAM retains its existing AD0-AD7 address mask and pair models, including frame
projection and transaction mode. Work RAM retains A1-A15 address disconnections
and existing address/data pair controls. Work RAM data-line disconnections and
Z80 fault models are not added. Existing memory-domain handoff rules still
permit only one active RAM or VRAM fault domain; audio controls are independent.

The new FM/PSG cut mode uses an 8-bit stuck-low mask at the existing chip-write
input boundary. Each selected D0-D7 bit is forced low on future writes and has a
visible cross. This is the same deterministic approximation used by the other
line controls, not a simulation of a floating open wire. A chip can use a mask
or one bridge pair, not both at once. Changing modes replaces the previous
fault only when the corresponding setting is applied.

Removing a fault affects future accesses. It does not undo corrupted memory or
restore sound-chip registers. Clean restart clears all runtime fault settings;
CPU-only recovery retains its separately documented limits. If the loaded core
has the older bridge API but lacks audio masks, bridge controls remain usable
and audio cut mode is unavailable.

Configuration save/preview/apply must preserve the selected masks as well as
pairs. Older version 1 configuration files remain importable. Experiment
exports identify the active audio model and mask without rewriting historical
records. The original v0.4.0 download remains unchanged; new packages are identified by their version and source commit.

## Development-source coordinated removal

**Disconnect all faults** attempts every modeled domain without forcing a pause
on a confirmed complete clear. It preserves an existing pause; partial or
unverified failure pauses for inspection. This includes audio masks and pair
bridges. It abandons pending leg selections and
held/momentary restore actions so they cannot reinstate a connection afterward.
The result reports partial failure rather than claiming every chip is clear.
This does not reset the CPU or repair earlier corruption. See
[CPU recovery](CPU-RECOVERY.md) for the distinct actions and pulse limitations.
The public v0.4.1 download remains unchanged until a later workbench release.

## Development-source randomiser

The **Randomiser** row has separate **PSG**, **FM** and **VRAM** buttons. Each
press chooses cuts or a joined pair within that chip's eight supported lines.
It replaces only that chip's fault configuration; it cannot join different
chips. The diagram shows the resulting crosses or bridge. The current VRAM
model is retained, and the existing sound enable/mute and play/pause controls
remain separate.

Work RAM is excluded. VRAM randomisation refuses while a RAM fault/pulse or
held VRAM bridge would be disturbed. Audio chips remain independent of those
memory controls. Unsupported chips are unavailable; an older bridge-only API
can choose bridges without pretending to support cuts. Core rejections or
unavailable state are reported instead of claiming success. A trapped or
uncertain change pauses emulation for inspection rather than restarting it.

Use **Download configuration** to save the resulting settings and experiment
JSON to retain the recorded state and counters. Randomisation does not consume
a staged configuration preview or add a new file format. Removing a fault
changes future accesses, without repairing prior corruption. These remain
digital approximations, not physical open-wire or electrical fault simulation.

## Development-source compact recovery and RAM burst

**CPU reset** beside the Randomiser buttons invokes the existing CPU-only reset:
RAM/VRAM faults clear while PSG/FM faults and the app's pause state are preserved.
It does not reload the cartridge. The nearby **RAM pulse** chooses one write-only
address bridge within A11–A15 for up to eight affected writes, capped at one
emulated frame. It disconnects without automatic CPU recovery. Existing memory
faults/pulses and held contacts block this shortcut instead of being overwritten;
audio faults can coexist. See [pulse timing and records](RAM-PULSES.md).
