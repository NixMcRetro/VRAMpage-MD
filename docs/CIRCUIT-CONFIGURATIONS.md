# Circuit configuration files

The v0.4.1 workbench saves and restores stable circuit settings. This feature
is not in the original v0.4.0 ZIP.

Open **Circuit configuration**, choose **Download configuration**, and keep the JSON
file. To restore it, choose the file, review its preview and click **Apply staged configuration**.
Choosing a file only stages a preview. It does not activate faults or change the
existing controls. Cancel discards the preview. Invalid replacement files leave
the previous valid preview visible and report that the replacement was rejected.

The development-source version 3 format saves the selected VRAM model and either its disconnected
lines or bridge pair, one stable Work RAM fault, independent PSG/FM settings, and a separate optional
Z80 RAM write-address pair. Published v0.5.0 retains its original version 2 format.
It excludes ROM identity/content, memory contents, counters, timing, pulses and
experiment history. These are reusable settings, not emulator save states or a
promise to reproduce the same gameplay from a different starting point. Use
experiment exports separately to record execution metadata.

All domains are present in a file. A null RAM entry means disconnected; audio entries contain a nullable pair
and a dataMask from 0 through 255. A sound chip cannot use both at once.
The `z80Ram` object has a nullable pair of distinct local address bits 0–12;
it is independent of the other fault domains.
RAM and active VRAM faults cannot coexist. Bridge endpoints are unordered: a
reversed pair represents the same connection and must not reset live counters.
Unknown fields, incompatible versions, invalid values and cross-byte RAM data
pairs are rejected. Files are limited to 32 KB.

Apply checks the current core's capabilities before changing settings. It does
not silently replace an unsupported transaction model with the frame model.
An active RAM pulse or momentary VRAM contact must finish or be released first.
Unchanged settings skip setters so counters are retained. Changing a setting can
reset its counters. Existing memory-domain handoff rules remain in force, while
PSG, FM and the independent Z80 RAM write bridge can coexist with either
existing memory domain.

If a later core operation rejects or throws after earlier operations succeeded,
emulation pauses and the preview remains available. The status reports observed
or tracked state and explicitly identifies unavailable state. This is not an
atomic rollback: earlier changes and counter resets can remain. Removing a fault
does not undo memory writes or restore chip registers. Clean restart remains the
full reset path.

Tests cover strict schema validation, inert staging, supported and unsupported
cores, pulses, unchanged/reversed connections, memory handoffs, failed and
throwing setters, and round-trips through the actual compiled runtime.

Version 1 files with nullable audio pairs and version 2 files with audio masks
remain importable and are normalized without modifying the original file.
Both import with Z80 RAM off. New development-source downloads use version 3.
Older applications reject the newer schema rather than silently losing its settings.

For example, this version 3 file selects a frame-model VRAM bridge, two
independent audio settings and a Z80 RAM write bridge:

```json
{
  "format": "vrampage-md-circuit-config",
  "schemaVersion": 3,
  "configuration": {
    "vram": {"modelId": 1, "mask": 0, "pair": [0, 1]},
    "ram": null,
    "psg": {"pair": [0, 7], "dataMask": 0},
    "fm": {"pair": null, "dataMask": 2},
    "z80Ram": {"pair": [0, 12]}
  }
}
```
