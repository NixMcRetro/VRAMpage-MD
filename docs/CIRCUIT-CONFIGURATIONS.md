# Circuit configuration files

Development source after the public v0.4.0 release can save and restore stable
circuit settings. This feature is not in the original v0.4.0 ZIP.

Open **Circuit configuration**, choose **Save configuration**, and keep the JSON
file. To restore it, choose the file, review its preview and click **Apply**.
Choosing a file only stages a preview. It does not activate faults or change the
existing controls. Cancel discards the preview. Invalid replacement files leave
the previous valid preview visible and report that the replacement was rejected.

The version 1 format saves the selected VRAM model and either its disconnected
lines or bridge pair, one stable RAM fault, and independent PSG/FM bridge pairs.
It excludes ROM identity/content, memory contents, counters, timing, pulses and
experiment history. These are reusable settings, not emulator save states or a
promise to reproduce the same gameplay from a different starting point. Use
experiment exports separately to record execution metadata.

All domains are present in a file. A null RAM or audio entry means disconnected.
RAM and active VRAM faults cannot coexist. Bridge endpoints are unordered: a
reversed pair represents the same connection and must not reset live counters.
Unknown fields, incompatible versions, invalid values and cross-byte RAM data
pairs are rejected. Files are limited to 32 KB.

Apply checks the current core's capabilities before changing settings. It does
not silently replace an unsupported transaction model with the frame model.
An active RAM pulse or momentary VRAM contact must finish or be released first.
Unchanged settings skip setters so counters are retained. Changing a setting can
reset its counters. Existing memory-domain handoff rules remain in force, while
PSG and FM can coexist with either memory domain.

If a later core operation rejects or throws after earlier operations succeeded,
emulation pauses and the preview remains available. The status reports observed
or tracked state and explicitly identifies unavailable state. This is not an
atomic rollback: earlier changes and counter resets can remain. Removing a fault
does not undo memory writes or restore chip registers. Clean restart remains the
full reset path.

Tests cover strict schema validation, inert staging, supported and unsupported
cores, pulses, unchanged/reversed connections, memory handoffs, failed and
throwing setters, and round-trips through the actual compiled runtime.

For example, this version 1 file selects a frame-model VRAM bridge and two
independent audio bridges:

```json
{
  "format": "vrampage-md-circuit-config",
  "schemaVersion": 1,
  "configuration": {
    "vram": {"modelId": 1, "mask": 0, "pair": [0, 1]},
    "ram": null,
    "psg": [0, 7],
    "fm": [1, 6]
  }
}
```
