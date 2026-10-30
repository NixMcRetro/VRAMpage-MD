# Original Built-In Cartridge Notices

These cartridges contain original VRAMpage MD programs and assets. The project
owner authorized their inclusion as built-in cartridges and in future VRAMpage
MD bundles. This records that specific redistribution authorization; it does not
assign an SPDX license or grant a new blanket license to the artwork or sources.
Retain this notice, the original notices, attribution and corresponding source
when distributing the cartridges. No commercial game ROM, BIOS, SDK routine or
third-party game asset is included. The SEGA header identifies the cartridge
format; these are not official Sega products.

The **Demo Cart** is the VRAMpage MD project's original 68000 program and
user-approved portrait/logo artwork. Its reproducible source is
`show-lab/build_show.py`, with the unchanged, checksum-pinned original source kit
`VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip`. The kit retains its original README
and approved source assets. Its internal input checksum is intentionally fixed.
On 30 October 2026 the owner approved the full three-minute v0.3.8 cartridge
for the v0.5.2 release and future bundles. Its original six-voice FM/PSG score
contains no commercial recordings or transcribed commercial music. The separate
20-second Music Lab audition is experimental and is not a bundled cartridge.
The earlier `fx-lab/build_fx.py` remains available for historical regressions.

The **Colour Test** is the VRAMpage MD project's original program and graphics
created for the VRAMpage MD blog illustration. Its source was copied byte for
byte from the original published `build_colour_test.py`; the published ZIP's
README is retained without changes as
[`colour-test/ORIGINAL-README.txt`](colour-test/ORIGINAL-README.txt). That source
and README establish original provenance; they do not name a separate public
license. The project owner's explicit instruction to include this original
cartridge authorizes this integration and future VRAMpage MD bundles.

The Colour Test is silent, has no controller interaction, and increments a
Work RAM word at `$FF1000` without using it to draw the picture. Its header
declares the US region. It is an emulator visual/memory experiment, not a
physical hardware diagnostic. Version `1` identifies these original published
bytes; it does not change the VRAMpage MD application version.

Build all approved cartridges with `python3 scripts/build-demo-cart.py` from
the repository root. `site/cartridges.json` records the approved identities,
sizes, checksums, build inputs, region headers and attribution. Generated ROMs
remain ignored. Complete browser ZIPs carry the source tree; static bundles
carry a rebuildable source snapshot under `source/cartridges/`.

The preserved Colour Test README refers to the original download's
`SHA256SUMS.txt`. In these bundles the authoritative cartridge checksum is
in `site/cartridges.json`; the README is retained as historical provenance.
