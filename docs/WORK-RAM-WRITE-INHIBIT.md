# Work RAM Write Inhibit

Development source adds two write-only controls in the existing **SRAM (Work RAM)**
panel. Choose **Writes**, then toggle `/LWR` (Lower Byte) and `/UWR` (Upper Byte).
Either or both can be inhibited. Access is fixed to Write in this view;
**Restore All Writes** permits future stores again. Switching signal views does
not change the active fault. The two-device PAL Model 1 VA6.5 circuit is the
[documented reference](WORK-RAM-WRITE-ENABLE-RESEARCH.md).

For a big-endian word containing `$AABB`, a store of `$1122` produces:

| Inhibit | Stored Word |
| --- | --- |
| Off | `$1122` |
| Lower | `$11BB` |
| Upper | `$AA22` |
| Both | `$AABB` |

An even byte store uses the upper lane; an odd byte store uses the lower lane.
Longwords are two sequential word transactions. CPU and banked Z80 Work RAM
writes share the existing hooks. Reads, VDP DMA reads and the separate local
Z80 Sound RAM retain their existing behavior. Releasing inhibition does not
replay skipped stores or restore program state. Stale RAM can still stop a game.

Address masks, data masks, byte-local bridges and write inhibition replace one
another. VRAM exclusion and independent audio/Z80 RAM/RGB rules are unchanged.
CPU Reset/Force Resume clear inhibition while retaining RAM and sound state;
CPU Reset keeps the checkpoint. Restore Checkpoint first clears and verifies all
faults, then restores the saved machine while paused. Native save/restore refuses
active inhibition. Clean Restart clears controls and discards the checkpoint.
Existing temporary address-shortcut ownership rules restore a prior inhibit mask.

## Runtime and Recorded State

The optional runtime API is `_set_logic_write_inhibit(mask)` and
`_get_logic_write_inhibit()`. Bit 0 selects the lower byte, bit 1 the upper;
mask 0 clears and masks 1–3 inhibit. The setter accepts exactly one integer,
validates before mutation, and replaces the current RAM fault. Accepted existing
RAM setters, startup and recovery clear the mask. Invalid calls preserve state.
The unchanged normal/fallback core has no inhibit API; its existing RAM controls
remain usable and the Writes pins show the unavailable capability.

An affected write is counted once per byte/word hook when the retained result
differs from the attempted value. A longword can therefore count 0–2. An inhibited
store of the already-stored value is a no-op for affected counters/budgets.
Trace reason `4` identifies a control inhibit; completion means the bus handler
finished, including when the effective data was retained. It does not claim that
the CPU's data-bus value changed or that an electrical write strobe occurred.

Circuit schema 6 saves `{ "type": "write-inhibit", "mask": 1 }` as its RAM entry,
with no Access field because this is write-only. Schemas 1–5 remain importable;
newer controls are not accepted in an older schema. Experiment logic metadata
version 3 records the observed mask and capability. Missing/unreadable observations
compare Unknown. Unverified setters or clears pause rather than claiming success;
configuration save/apply refuses inconsistent mask state.

## Verification and Limits

Literal native and actual-WASM probes cover word/byte retention, sequential
longwords, mirrors, counters/CONTROL traces, validation, replacement and clearing.
A banked Z80 baseline writes `$5566`; masks 1/2/3 produce `$55BB/$AA66/$AABB`,
while a separate `$77` marker in local Z80 RAM remains unchanged. Browser checks
cover controls, keyboard access, schema round-trips, optional legacy capability,
uncertain outcomes, temporary contacts and checkpoint/reset/sound behavior.
Normal and runtime C profiles are compiled separately. Integration requires
independent specialist review, fresh normal hash checks and required PR/main CI.

The model holds selected active-low write enables **inactive/high**. It does not
equate a physically cut input with high, or force the write enable low. Floating
inputs, contention, refresh failure and physical timing are not simulated.
No application VERSION change, public release or McRetro.net deployment is part
of this development slice.
