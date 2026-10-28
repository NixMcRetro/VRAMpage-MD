# Sega Manual and MiSTer Evidence Review

Reviewed 28 October 2026 (Sydney), following the user's supplied
[developer manuals](https://drive.google.com/drive/folders/1-XWN7PGSdV5H35pLC5LPiCSL_io_RxOL)
and [service manuals](https://drive.google.com/drive/folders/1jikMIvCjwZz3_FjufmXA6ea_Xr9TJ50z).
This adds source evidence and a regression test, not a new physical fault model.
The app, native binaries, VERSION, released downloads and McRetro.net are unchanged.

## Results That Can Be Used Now

1. Sega's later technical bulletins correct several older manual statements.
   Use those corrections when constructing tests; an old example is not an
   independent oracle without its errata.
2. The service material identifies a PAL VA6.5 Work RAM population and topology,
   plus Model 2 memory consolidation and encoder alternatives. Keep each sheet's
   revision and designators with its facts. None verifies the requested NTSC VA6.
3. MiSTer's pinned HDL cross-checks counters, queues and logical byte ordering.
   It does not provide physical RAM pin routing or analogue short-circuit results.
4. The existing region WASM test now checks Sega's ASCII hexadecimal header
   masks against effective timing and a version-register read by original code.
   No new emulator behavior was necessary.

## Developer Manual Corrections

The HTML index identifies the scanned Software and Sound manuals and their
technical bulletins. Relevant scans were visually checked after OCR navigation;
OCR errors were not treated as source facts. The following links point to the
owner's Drive originals; access depends on their permissions. Scans and HDL are
not copied into this repository.

| Source | Verified Fact | Consequence for This Project |
| --- | --- | --- |
| [Software Manual p. 1](https://drive.google.com/file/d/1N8WJLiy0vJRsWk4iRvuHzpJErLh2ctUl/view), pp. 6, 8 | Work RAM occupies the top 64 KiB; VRAM is a separate VDP-controlled memory domain. | Preserve separate logical faults and telemetry; this is not a package pin map. |
| [Software Manual p. 19](https://drive.google.com/file/d/1IElkJV8xymYqVXatL6-0glcmL2Eo-RBL/view), pp. 20–21 | VRAM word addressing uses A15–A1; odd A0 changes the word's byte ordering rather than spanning the next word. | Cross-check the existing literal byte-lane tests and MiSTer queue behavior; do not equate logical A0 with one external multiplexed address pin. |
| [Bulletin #11, 9 Sep 1991](https://drive.google.com/file/d/1WUATdV6N39JLDk62Yd7PTUfMFeiUHIfp/view) | YM2612 busy-status access is specified at A1/A0 = 0/0; another port can give an invalid not-busy interpretation. | Useful for sound-driver fixtures; it does not establish a universal hardware result for a corrupted or unsupported port read. |
| [Bulletin #12, 9 Sep 1991](https://drive.google.com/file/d/1Mazgex4cofCxcA8ODwYHfWfgjZTpsD0G/view) | CPU reset does not reset the VDP; DMA can continue, making immediate VDP access ineffective. | Supports the existing CPU Reset/Clean Restart distinction. A CPU reset is not evidence of clean video state or a guaranteed lockup cure. |
| [Bulletin #13, 9 Sep 1991](https://drive.google.com/file/d/1aP9iMVAUUrBIhOChwgKNnINKHVR6is1m/view) | Corrects v1.0's byte-access guidance for VRAM/CRAM/VSRAM to supported word/long accesses, and requires Z80 bank switching from the Z80. | Do not turn the superseded examples into recommended software. The emulator's observed handling of an unsupported byte transaction remains a separate question; this bulletin alone does not justify deleting its bus implementation. |
| [Bulletin #29, 10 Mar 1994](https://drive.google.com/file/d/1XwiFAm7L3PbAL3dur9kevLr5xM-zZVsP/view) | Corrects Sound Manual p. 2: word register $A11100 uses bit 8, with 0 meaning the Z80 is inactive and the 68000 can access; 1 means active. | Use mask $0100 and the corrected polarity. The pinned core's word BUSACK path already follows this; never copy the older bit-0 example. |
| [Bulletin #31, 22 Nov 1994](https://drive.google.com/file/d/1EpG0NDdZhBVVklsB9CqhYpeuF_C05LsR/view) | Defines an ASCII hexadecimal hardware-enable mask at ROM $1F0, spaces through $1FF, and hardware identity at $A10001 bits 7/6. | Supplies an independent basis for new Auto/header regression cases below. A compatibility mask does not prescribe an emulator's preferred region. |

### Header Cases Added to the Existing WASM Test

The [original generated fixture](../tests/test_region_profile_wasm.cjs) uses
space-padded region bytes, stages Auto, boots, and reads $A10001 into Work RAM.
Assertions use literal expected region bits, PAL/NTSC timing, master clock and
line count. The native RAM inspection accounts for the core's swapped byte lanes.

| ASCII Header | Enabled Hardware in Bulletin #31 | Expected Auto Selection in This Core |
| --- | --- | --- |
| `1` | Japan NTSC | Region bits $00; NTSC, 262 lines |
| `2` | Japan PAL | Region bits $40; PAL, 313 lines |
| `4` | Overseas NTSC | Region bits $80; NTSC, 262 lines |
| `8` | Overseas PAL | Region bits $C0; PAL, 313 lines |
| `F` | All four | NTSC-U by the core's existing priority |

The pinned [loadrom.c](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/loadrom.c#L1038-L1078)
chooses USA, then Japan NTSC, Europe, then Japan PAL when multiple bits are set.
That preference is not Sega hardware behavior. Auto selection also does not
guarantee that a cartridge's own region lockout accepts the selected machine.

## Service Manual Findings

PDF references below use the **supplied file's one-based page number**, because
the split scans contain gaps, foldouts and different printed page numbers.
Manual revision letters and Model 2 “Version 1” are not automatically Model 1
VA revision identifiers.

| Supplied Source | Pages Visually Checked for the Following Claims | Finding and Boundary |
| --- | --- | --- |
| [PAL-G Rev. A, Part 1](https://drive.google.com/file/d/1CluZkVqGT673OUYd5jQCiQrT5NsbkpQe/view) | 1, 3, 65 | Cover: August 1992, PAL-G, Rev. A. Includes NEC µPD42832C/C-L pseudo-static RAM specification and a 28-pin package diagram. A component appendix is not a universal fitted-parts list. |
| [PAL-G Rev. A, Part 2](https://drive.google.com/file/d/10kh7fZK_VlZ1o6NrbMJiaiBGD920MTcm/view) | 1, 4–5, 11, 18 | Contains multiple board revisions: p. 4 is marked VA4, pp. 5/11 VA6.5. The VA6.5 CPU/RAM sheet identifies the map below. P. 5 labels NTSC/PAL oscillator values 53.693175/53.203424 MHz. P. 18 identifies a CXA1145P/M block/pin diagram. These are labeled reference circuits, not identification of the user's NTSC VA6. |
| [Genesis II / Mega Drive II Supplement A4](https://drive.google.com/file/d/18o7RYj8G_CCdcCA3n743p8aObYb53o4K/view) | 1 | No. 001-1, August 1993: an IC1 specification correction for Model 2. It is not a Model 1 VA0 schematic despite neighboring filenames. |
| [Genesis II / Mega Drive II Version 1 Supplement, A4](https://drive.google.com/file/d/1SW43Co2b1hE5NRE7TmkFQHUqZXlKidS4/view) | 1–4 | No. 001-2, December 1993. P. 2 contrasts two 8-bit Work RAM devices with one 16-bit device, and two four-bit VRAM devices with one eight-bit device. P. 3 lists regional oscillator differences; p. 4 lists CXA1145M, MB3514PF and KA2195D circuit variants. Physical contact profiles therefore need more than a region name and a shared 64 KiB size. |
| `mega1.gif`, `mega2.gif`, `mega3.gif` in the service folder | All three images | CPU/RAM, VDP/encoder and block diagrams are readable, but no matching VA6 board identifier or source cover was established. They are comparison leads, not the missing target-board proof. Do not import their oscillator annotation into the verified region constants. |

### Verified PAL VA6.5 Reference Topology

The supplied PAL-G **Part 2 p. 11**, marked “PC BD M5 PAL VA6.5 -G Version,”
labels IC2/IC3 as µPD42832C-15. Together with **Part 1 p. 65**, it supplies
this qualified reference map:

| Signal | IC2 | IC3 |
| --- | --- | --- |
| Logical data lane | VD0–VD7 | VD8–VD15 |
| Address relationship | CPU VA1–VA15 → device A0–A14 | Same |
| Chip enable, pin 20 | `/RAS0` | `/RAS0` |
| Output enable, pin 22 | `/NOE` | `/NOE` |
| Write enable, pin 27 | `/LWR` | `/UWR` |

Device A10/A11 are package pins 21/23, corresponding to the app's logical
CPU A11/A12 in this topology. Package pin numbers are not the app's address-line
numbers. The NEC specification also names pin 22's refresh role (`/OE(/RFSH)`);
the existing digital address-fault model does not simulate pseudo-static refresh.
This does not identify the part, lane or wiring on an NTSC Model 1 VA6. Keep
[#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73) open and the UI conceptual.

The Model 2 change is a concrete reason to retain a board evidence matrix
before adding a VA selector: one device with separate byte write enables is
not physically the same contact layout as two separate byte-wide devices.
No new selector or per-package fault behavior is introduced here.

## MiSTer Cross-Checks and Their Limits

Independent specialist review fetched the exact
[`Genesis_MiSTer@adc0c42`](https://github.com/MiSTer-devel/Genesis_MiSTer/tree/adc0c42cfb1fa5d484cc8566767f7d68982bc44a)
sources again. Cached contents match after CRLF/final-newline normalization.
Upstream attribution and redistribution terms remain with those files;
no HDL is copied here. See the existing [timing report](VRAM-TIMING-RESEARCH.md)
for the main architecture comparison.

| Pinned HDL | Useful Check | Limit |
| --- | --- | --- |
| [vdp_common.vhd:102–103](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp_common.vhd#L102-L103), [vdp.vhd:2280–2282](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L2280-L2282) | 262/313-line totals and PAL/NTSC selection. | Counter units do not establish an absolute oscillator in Hz; the service circuits supply that separate evidence. |
| [vdp.vhd:2473–2488](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L2473-L2488), [3055–3120](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L3055-L3120) | Raster/refresh-dependent FIFO service and odd-address word-byte swapping. | FPGA ordering and grouped writes are not external DRAM RAS/CAS/serial-clock measurements. |
| [system.sv:346–402](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/system.sv#L346-L402) | Four byte-wide RAM banks, logical lane selection and registered acknowledgement. | These are FPGA storage banks, not proof of a real board's package count or pin permutation. |
| [vdp.vhd:3522–3544](https://github.com/MiSTer-devel/Genesis_MiSTer/blob/adc0c42cfb1fa5d484cc8566767f7d68982bc44a/rtl/vdp.vhd#L3522-L3544) | VBUS DMA feeds the FIFO; fill/copy use distinct states. | No HDL simulation or measured hardware trace was performed. Fast FIFO/turbo settings must be recorded in a future comparison. |

## Limits and Next Bounded Work

Three PDFs were inventoried but could not be locally inspected:
`Sega Mega Drive VA0 1 of 2 A4.pdf` (45,189,030 bytes), its A3 Part 2
(53,639,842 bytes), and `Sega Gen2 & MD2 Supp VA1 2 of 2 A3.pdf`
(51,204,289 bytes). The attachment materializer has a 32 MiB limit; the
connector's text extraction was empty and the cloud proxy refused its streamed
download host (403). Do not claim their contents or a VA0 identity from filenames.
The available smaller PDFs and GIF pages above were inspected successfully.

No new production defect was established. Preserve existing transaction/byte-lane,
Z80 ownership, recovery and region behavior. The new mask cases extend the existing
actual-WASM gate; no renderer rewrite or speculative electrical model is needed.
If raster work follows a concrete discrepancy, reuse the existing proposed
FIFO/store/render trace with distinguishable values and H32/H40 active/blanking
boundaries. A separate SAM/physical model still needs transfer/tap and board
evidence, not constants copied from an FPGA core.

Source-file SHA-256 values for the four locally inspected PDFs (selected-page
inspection, not an exhaustive validation of every page):

```text
PAL-G Part 1: c05602429d198a03d3e507736b78dbf5800b9fbe0dc2d7822945546c13b411f9
PAL-G Part 2: a3faf2a360fb34ce2dfd45eb8612db539374663ad686551740e6b4d4c900b026
II 001-1:    962e1c4c0a959d25a1e34ee95998065a833a5873272b60d9a0ccea5c8ee2f693
II 001-2:    a07a1e13611a0671cc8ed230bc4dfaf7e040e8d7ff395ebbda73e787a7b228c3
```
