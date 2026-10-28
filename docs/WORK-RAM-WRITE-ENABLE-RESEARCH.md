# Work RAM Write-Enable Research

Original research checkpoint, 28 October 2026 (UTC). Based on verified main
`9b29a5b9380ed4fe760f41015d15c51c53674e1e`; no application, native API,
configuration version, release or website changes accompany this report.

## Recommendation

A write-only **Lower Byte / Upper Byte Write Inhibit** is the smallest useful
next RAM experiment. Suppress the selected byte's future stores while retaining
its previous contents. Reuse the current Work RAM transaction hooks, fault
replacement and recovery rules. A second motherboard profile is unnecessary
for this bounded digital contract.

This is different from the delivered D0–D15 cuts: those force selected incoming
bits low; write inhibition can leave arbitrary old bits behind. Stale variables,
instructions or stack bytes can still stop a game. No reduced-lockup claim follows.

## Evidence and the Polarity Trap

- Sega's supplied [PAL-G Part 2, PDF p. 11](https://drive.google.com/file/d/10kh7fZK_VlZ1o6NrbMJiaiBGD920MTcm/view)
  is explicitly PAL Model 1 VA6.5. IC2 carries VD0–VD7 with `/LWR` at pin 27;
  IC3 carries VD8–VD15 with `/UWR` at pin 27. Both use `/RAS0` and `/NOE`.
  The [matching NEC appendix, Part 1 p. 65](https://drive.google.com/file/d/1CluZkVqGT673OUYd5jQCiQrT5NsbkpQe/view)
  labels pin 27 active-low `/WE` and pin 22 `/OE(/RFSH)`. The cached original
  sheet and appendix were visually inspected again for this question.
- Hitachi's [H8/3003 Interface Application Note, hosted by Renesas](https://www.renesas.com/en/document/apn/microcomputer-h83003-interface-application-note#page=111),
  section 5.4, printed p. 97 / PDF p. 111, specifies that HM65256B writes require
  overlapping low chip-enable and write-enable signals. Section 3.5 separately
  documents a two-byte-wide-device interface and refresh requirements. This is
  corroborating component/interface evidence, not a Sega schematic or proof of
  identical NEC timing. Text was inspected; the web screenshot connector did
  not deliver inspectable PDF image blocks, so no fresh visual check is claimed.

**Inhibit means holding the active-low write input inactive/high.** Forcing it
low would assert write enable. A physically cut wire can float and cannot be
assumed high. Use explicit write-inhibit terminology and a stated inactive-level
assumption; do not silently reuse the data-cut rule. Leave reads, chip selection,
refresh and CPU bus acknowledgements under the existing emulator's control.

This reference is enough for a bounded digital contract. It does not resolve
the optional exact NTSC VA6 mapping in [#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73),
predict physical contention or justify grounding a real control pin.

## Literal Proposed Results

For an aligned big-endian word containing `$AABB`, a CPU word store of `$1122`
would have these results under the proposed model:

| Write Inhibit | Word Afterwards | Explanation |
| --- | --- | --- |
| Off | `$1122` | Both byte stores accepted |
| Lower (`/LWR`) | `$11BB` | D0–D7 retain the old lower byte |
| Upper (`/UWR`) | `$AA22` | D8–D15 retain the old upper byte |
| Both | `$AABB` | Neither byte store accepted |

By comparison, the existing write data mask `$00FF` produces `$1100`, and
`$FF00` produces `$0022`. These were derived acceptance examples at the research checkpoint. The later
[development implementation](WORK-RAM-WRITE-INHIBIT.md) executes their native
and actual-WASM acceptance probes.

An even byte store uses the upper lane; an odd byte store uses the lower lane.
A longword remains two sequential word transactions, each applying the mask
then active. Reconnecting permits later stores; it does not reconstruct skipped
writes or rewind execution. This is a stable control fault, not a new pulse engine.

## Smallest Integration Boundary

The current [runtime write hooks](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/scripts/work_ram_runtime.c#L195)
already centralize byte/word storage. The
[pinned-core patch](https://github.com/NixMcRetro/VRAMpage-MD/blob/9b29a5b9380ed4fe760f41015d15c51c53674e1e/scripts/patch_core.py#L95)
routes CPU byte/word/longword writes and banked Z80 Work RAM writes through
those hooks. Add the optional runtime behavior there, preserving big-endian
bus lanes and native host-storage layout. Do not replace the memory map or
rewrite CPU execution. VDP DMA reads from Work RAM remain ordinary reads;
the separate 8 KiB Z80 Sound RAM is outside this control.

If implemented later:

- Use two write-only inhibit bits, independently selectable together. A strict
  integer API/getter must validate before mutation. Zero clears. Keep new code
  under the optional runtime guard so normal/fallback hashes stay unchanged.
- Replace address masks, data masks or pairs when this mode activates, and clear
  the inhibit mask through the same accepted setters. Preserve VRAM exclusion
  and independent FM/PSG/Z80 RAM/RGB behavior. Do not add combination rules.
- Reuse the existing chip signal view or advanced controls. Identify Lower and
  Upper bytes and write-only scope. Preserve keyboard access, chip highlighting
  and the existing desktop/mobile height budget; no extra chip panel is needed.
- Extend stable circuit configuration/export/comparison with explicit capability
  and mask observations; older files import off and missing observations remain
  Unknown. Do not change schemas during research. Unknown native outcomes must
  pause and remain clearable, following the delivered data-mask handling.
- Force Resume/CPU Reset remove the control but retain RAM and sound state under
  their existing contracts. CPU Reset retains the checkpoint; Clean Restart
  clears controls and discards it. The native checkpoint guard must reject active
  inhibits for save/restore. Preserve the UI's Restore behavior: first clear and
  verify all faults, including this control, then call the native restore.
  Temporary address contacts must restore a prior inhibit configuration only
  where the existing ownership rules already restore the previous fault.

Count an affected write once per byte/word hook call when the retained bytes
differ from what the CPU attempted to store. A longword traverses two 16-bit bus
subtransactions and can count 0–2 affected writes. An inhibited store of the
already-stored value emits no affected-write trace/count or budget consumption.
Add an explicit control-inhibit trace reason rather than claiming the CPU's
data-bus value changed; document completion as handler completion even when no
RAM store occurs. Reuse frame timing and tracing, without building a new subsystem.

## Acceptance Before Integration

| Check | Required Result |
| --- | --- |
| Word table above | Literal `$1122/$11BB/$AA22/$AABB` results |
| Even/odd byte stores | Only the selected lane is suppressed; adjacent byte unchanged |
| Longwords and E0–FF mirrors | Both sequential words and aliases obey the same lane contract |
| Banked Z80 stores | Work RAM suppression without changing bus ownership or local sound RAM |
| Reads and DMA reads | Existing stored bytes returned without read projections or extra read counts |
| Counters/trace | One affected transaction, unchanged-value no-op, explicit control reason |
| Validation/replacement | Invalid calls preserve live state; accepted replacement clears old modes |
| Lifecycle and holds | Clear/recovery/checkpoint/restart and temporary-contact ownership stay correct |
| Compatibility | Optional API absence degrades clearly; off path and normal-core hashes unchanged |

Use literal native/sanitized tests, original synthetic actual-WASM cartridge probes, configuration
round-trips and the existing three-browser/package CI gates. Require independent
specialist review before merge. Do not use commercial-game recovery or physical
electrical accuracy as inferred acceptance results.

## Decision

The user subsequently authorized the [bounded implementation](WORK-RAM-WRITE-INHIBIT.md).
The proposal below records its original research decision.

**Ready for a bounded implementation proposal; no further motherboard catalogue
or user measurement is needed for the stated digital contract.** Physical open
inputs, write-enable shorts, refresh failure and phase-level waveform modeling
remain outside it. Proceed before FM engine selection if the next feature is
chosen: it preserves the current sound/checkpoint backend and reuses the delivered
RAM lifecycle. The [FM follow-up](FM-VARIANTS-RESEARCH.md) has separate constraints.
