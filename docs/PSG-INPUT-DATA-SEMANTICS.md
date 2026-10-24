# PSG input data bridge

The optional runtime profile exposes a low-dominant bridge between two SN76489-compatible PSG
software data inputs D0 through D7. The bridge is applied at the synchronized
`psg_write` input, before the byte is decoded as a latch or data write. If both
selected input bits are high, both remain high. If either is low, both are
forced low. Other bits are unchanged.

The safe JavaScript API is `_set_psg_data_bridge(enabled, inputA, inputB)`.
Arguments must be JavaScript numbers that are integers. Enable with
`(1, a, b)`, where `a` and `b` are distinct values from 0 through 7. Disable
with `(0, -1, -1)`. The setter returns 0 on success, 1 for invalid arguments,
and 2 when an enabled bridge is unsupported by the current system profile.
Rejected calls do not change configuration or counters. Support is limited to
the Genesis `SYSTEM_MD` profile. The normal core does not expose this API.

`_get_psg_data_bridge_state()` reports `modelVersion`, `supported`,
`configured`, `effective`, `reason`, `bridgeA`, `bridgeB`, `inputWrites`, and
`changedWrites`. The two counters are decimal strings for exact integer
representation. They aggregate calls reaching the supported PSG sink while the bridge is enabled, and do not
attribute writes to the 68000 or Z80. They reset when configuration changes or
`psg_reset` runs. In particular, a full system reset that resets the PSG clears
the bridge and counters. A CPU-only reset is not documented to reset the PSG.

Removing the bridge changes future writes only. It does not repair the PSG
latch, registers, current audio output, or any other chip state already changed
by prior writes. The feature models a deterministic digital input condition;
it does not model analog contention or establish physical electrical behavior.
Original synthetic cartridges exercise both the 68000 PSG route and Z80
`$7F11` writes under the native BUSREQ/RESET sequence. A mixed Z80 fixture
verifies simultaneous FM/PSG counters and repeated fresh-core output for both
FM backends. These are software route tests, not commercial-game or physical
hardware evidence.
