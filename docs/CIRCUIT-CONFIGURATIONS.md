# Circuit configuration files

Circuit configuration JSON saves fault settings only. It never includes a ROM,
RAM or VRAM contents, counters, frame numbers, pulse budgets, or event history.
The existing experiment metadata download remains separate.

Version 1 uses the format name `vrampage-md-circuit-config` and contains all
four stable domains: `vram`, `ram`, `psg`, and `fm`. The VRAM entry has a model
ID, an 8-bit stuck-low mask, and either a two-line bridge pair or `null`. The
RAM entry is `null` or an address-mask setting or a persistent address/data
line-pair setting. PSG and FM entries are `null` or two distinct D0-D7 inputs.
RAM and VRAM faults cannot both be enabled. PSG and FM settings are independent
of each other and of the memory fault domain.

Files must include every domain. Unknown versions, fields, invalid ranges,
cross-byte-lane RAM data pairs, and conflicting RAM/VRAM settings are rejected.
The importer does not merge partial files or downgrade unsupported models.
An unsupported enabled setting makes the whole staged configuration
unavailable to Apply. Disabled optional PSG/FM settings remain usable with a
core that lacks those APIs.

Loading a file only displays a preview. The user must choose **Apply staged
configuration** to change the running circuit. Apply checks current system
support, core APIs, and active RAM pulses before calling any setter. Existing
VRAM and RAM handoff functions preserve their mutual exclusion. Unchanged
targets skip setters so their counters remain intact. If a setter fails after
another domain has changed, the app pauses, keeps the staged file, and reports
the tracked resulting settings. It does not claim that counters or prior chip
state were restored.

For example:

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

This file describes settings only. It does not store chip registers, RAM
contents, or game execution state, and applying a configuration does not repair
state changed by earlier writes.
