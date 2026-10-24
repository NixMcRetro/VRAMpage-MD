# FM register-data input bridge

The optional runtime profile can force two selected input bits low on each
byte delivered to the FM register interface. It is disabled by default and
accepts distinct D0-D7 inputs. The bridge sits at the shared FM write handler
boundary, before the chip receives the register address or data byte. It
preserves the original handler, port address, and cycle timestamp, so both
YM2612 and YM3438 write paths use the same transformation.

The counters aggregate FM-interface byte writes and changed bytes. They do not
attribute a write to the 68K or Z80. Removing the bridge affects future writes
only. It does not restore prior register values or otherwise repair current
chip state.

A full sound reset clears the bridge selection and both counters. This includes
the sound reset performed for a new cartridge. The Genesis Z80-only reset path
calls the chip's partial `fm_reset` routine without calling the full sound
reset, so the bridge selection and counters remain in place across that event.
This keeps the configured input behavior connected when the Z80 is restarted;
it does not claim that FM chip registers survive the chip's own partial reset.

The API reports whether the current system profile supports the bridge. A
configuration request on an unsupported profile is rejected without changing
the current configuration or counters. This input bridge is independent of
the PSG and RAM/VRAM fault controls.
