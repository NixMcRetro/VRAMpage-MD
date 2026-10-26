# VA6 Work RAM Device Validation

**Status: partial desk research, target NTSC VA6 mapping unverified.**
Follow-up to [#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73),
27 October 2026 (Sydney). Keep the public chip diagram conceptual. The bounded
RAM experiment and its evidence remain complete and unchanged.

## Evidence Found

- Hitachi, *HM65256B Series*,
  [manufacturer datasheet scan, pages 1–2](https://datasheet.octopart.com/HM65256BLFP-12-Hitachi-datasheet-180018748.pdf#page=1).
  Visually checked ordering/package and top-view pin diagrams. This family is
  32K × 8 **pseudo-static RAM**, with internal refresh and an SRAM-compatible
  interface. It supplies a candidate device pinout, not evidence that a
  particular console contains that part. P/SP/FP package and suffix matter.
- Sega, [Mega Drive PAL-G VA6.5 schematic, first sheet](https://retrosix.wiki/uploads/Mega%20Drive%20Schematic%20%28VA6.5%29-1.pdf#page=1).
  Visually checked IC2/IC3 and the title/revision: two 32K × 8 devices form the
  main RAM, with address A1–A15 and separate upper/lower data lanes. This is
  **PAL VA6.5**, not primary proof of an NTSC VA6 population or trace map.
  The component labels are compatible with the candidate interface below;
  no cross-revision continuity is assumed.

Community inventories suggest several fitted vendors and revisions, but they
are leads to locate identifiable board evidence. They do not establish one
universal bill of materials. In particular, do not silently substitute a
generic HM62256 SRAM datasheet for HM65256B pseudo-static RAM, or treat a
Model 1 VA7 / Model 2 schematic as a VA6 schematic.

## Candidate Pin Map, Conditional on the Matching Device

The following **device pins** come from the HM65256B P/SP/FP top-view diagram.
The CPU-column correspondence is the word-address relationship shown on the
inspected PAL VA6.5 sheet. It remains a candidate for the requested NTSC VA6.
Read package orientation from its notch/pin-1 mark, not the page's screen
orientation; never transfer this table to an unidentified part/package.

| Device Address | Package Pin | Corresponding CPU Address in the Reference Topology |
| --- | --- | --- |
| A0 | 10 | A1 |
| A1 | 9 | A2 |
| A2 | 8 | A3 |
| A3 | 7 | A4 |
| A4 | 6 | A5 |
| A5 | 5 | A6 |
| A6 | 4 | A7 |
| A7 | 3 | A8 |
| A8 | 25 | A9 |
| A9 | 24 | A10 |
| A10 | 21 | A11 |
| A11 | 23 | A12 |
| A12 | 2 | A13 |
| A13 | 26 | A14 |
| A14 | 1 | A15 |

| Other Device Signal | Package Pin(s) | Evidence Boundary |
| --- | --- | --- |
| I/O0, I/O1, I/O2 | 11, 12, 13 | Local 8-bit data numbering, not CPU D0–D15 by itself. |
| I/O3, I/O4, I/O5, I/O6, I/O7 | 15, 16, 17, 18, 19 | The two devices provide distinct CPU byte lanes; target-board lane-to-designator assignment still needs confirmation. |
| `/CS`, `/OE`, `/WE` | 20, 22, 27 | Device control names; actual VA6 enable/write net routing is not verified here. |
| VSS, VCC | 14, 28 | Device supply pins, not a board wiring instruction. |

This explains a naming trap: UI **A11 ↔ A12** means CPU logical address lines,
which would correspond to device A10/A11 and pins 21/23 in this candidate
topology. It does not mean package pins 11 and 12. An 8-bit device's A0 is
also different from the 68000's byte-selection convention. The current model
retains its documented lane rules; this table does not change their scope.

The user-facing **SRAM (Work RAM)** name describes the main working-memory
role/static interface. If the fitted part proves to be pseudo-static, record
that distinction in hardware documentation without inferring dynamic refresh
faults from the existing digital model. Z80 sound RAM and cartridge save RAM
are separate domains, regardless of similarly named memory technologies.

## What Still Establishes Completion of #73

1. Identify an NTSC Model 1 VA6 board by readable silkscreen/board number and
   region evidence; record both RAM designators, full part markings and package
   orientation. A case label alone cannot identify a swapped motherboard.
2. Pair those exact markings with original manufacturer diagrams. If a second
   vendor or package is fitted, verify that device rather than importing this
   candidate table on resemblance.
3. Trace or obtain a revision-matched original schematic establishing each
   device's CPU byte lane and address/control nets. Record source, sheet,
   revision and any bodge/jumper differences explicitly.
4. Reconcile that map with the conceptual UI/model and document remaining
   electrical limits. Do not rewrite immutable experiment results or imply
   that a digital bridge predicts short-circuit voltages or refresh behavior.

No target-board photographs, continuity measurements or verified NTSC VA6
schematic were supplied or obtained in this research. This issue remains open.
The component and PAL-reference work above can be reused when matching primary
board evidence becomes available; no further user testing is needed for the
completed Z80/VRAM research reports.
