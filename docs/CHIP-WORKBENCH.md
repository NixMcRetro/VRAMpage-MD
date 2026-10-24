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
