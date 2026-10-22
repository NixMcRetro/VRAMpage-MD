# Work-RAM byte transaction model

The standalone model in `scripts/work_ram_fault.c` supports byte and aligned
word operations on a 64 KiB big-endian byte array. Even addresses select D8–D15;
odd addresses select D0–D7. Address-pair projection uses A1–A15 (WA0–WA14),
preserving A0 and therefore the byte lane.

A data pair wholly within the other byte lane leaves a byte transaction unchanged.
A cross-lane pair returns `WORK_RAM_FAULT_UNSUPPORTED_LANE` for applicable byte
operations without modifying output or memory. Word transactions support all
120 pairs. This is an explicit digital-model limitation, not a statement about
physical shorts. Runtime integration rejects cross-lane configurations globally.

Read projections do not modify stored bytes. Write projections can alias a
location or store changed data; removing a fault does not undo these writes.
The projection helpers share the same rules with the emulator's native storage
adapter, avoiding a second implementation of the model.

`tests/work_ram_fault_smoke.c` and `tests/test_work_ram_properties.py` check every
address/data pair, lane selection, direction, invalid configurations, bounds,
identity and persistent writes against an independent reference calculation.
See [Logic bending](LOGIC-BENDING.md) for upstream references, runtime coverage
and electrical-model limitations.
