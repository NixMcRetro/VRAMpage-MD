# Circuit configuration files

The v0.4.1 workbench saves and restores stable circuit settings. This feature
is not in the original v0.4.0 ZIP.

Open **Circuit configuration**, choose **Download configuration**, and keep the JSON
file. To restore it, choose the file, review its preview and click **Apply staged configuration**.
Choosing a file only stages a preview. It does not activate faults or change the
existing controls. Cancel discards the preview. Invalid replacement files leave
the previous valid preview visible and report that the replacement was rejected.

The development-source version 6 format saves the selected VRAM model and either its disconnected
lines or bridge pair, one stable Work RAM address/data mask, bridge pair or write-inhibit mask, independent PSG/FM settings, and a separate optional
Z80 RAM write-address pair and RGB encoder input contacts. Published v0.5.0 retains its original version 2 format.
It excludes ROM identity/content, memory contents, counters, timing, pulses and
experiment history. These are reusable settings, not emulator save states or a
promise to reproduce the same gameplay from a different starting point. Use
experiment exports separately to record execution metadata.

All domains are present in a file. A null RAM entry means disconnected; audio entries contain a nullable pair
and a dataMask from 0 through 255. A sound chip cannot use both at once.
The `z80Ram` object has a nullable pair of distinct local address bits 0–12;
it is independent of the other fault domains.
The `rgbEncoder` object contains a cut mask 0–7 and nullable pair of distinct
channel indexes 0–2. See [RGB assumptions and bypass rules](RGB-ENCODER-INPUTS.md).
A Work RAM `data-mask` uses a mask from 1–65535 and access 1 (Read),
2 (Write) or 3 (Read + Write); bit N selects CPU data line DN. It replaces
address masks or pairs and requires the updated runtime core. A zero mask is
saved as null. See [data-line semantics](WORK-RAM-DATA.md).
A `write-inhibit` RAM entry contains only `type` and `mask` (1–3): bit 0 inhibits
lower-byte writes, bit 1 upper-byte writes. It has no Access field. Earlier
schemas reject this new type; imported old settings leave it off. See
[write-inhibit semantics](WORK-RAM-WRITE-INHIBIT.md).
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

Version 1 files with nullable audio pairs, version 2 files with audio masks
and version 3 files with a Z80 RAM pair
remain importable and are normalized without modifying the original file.
Versions 1/2 import with Z80 RAM off; versions 1–3 import with RGB
off. Version 4 files retain their RGB settings. All four older versions remain
importable; none can encode a data mask. Version 5 data-mask files also import unchanged; new downloads use version 6.
Older applications reject the newer schema rather than silently losing its settings.

For example, this version 6 file selects a frame-model VRAM bridge, two
independent audio settings and a Z80 RAM write bridge with RGB contacts off:

```json
{
  "format": "vrampage-md-circuit-config",
  "schemaVersion": 6,
  "configuration": {
    "vram": {"modelId": 1, "mask": 0, "pair": [0, 1]},
    "ram": null,
    "psg": {"pair": [0, 7], "dataMask": 0},
    "fm": {"pair": null, "dataMask": 2},
    "z80Ram": {"pair": [0, 12]},
    "rgbEncoder": {"cutMask": 0, "pair": null}
  }
}
```
