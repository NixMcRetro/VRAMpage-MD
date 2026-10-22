# v2.4 work-RAM address-line switches

The work-RAM panel includes a chip-shaped address-bus diagram. Each A1–A15 wire
is a button: click it to show a **×** and force that modeled address input low;
click again to reconnect it. Several wires may be crossed simultaneously.
**Reconnect all address lines**, Disconnect RAM, CPU recovery and Clean restart
also remove the mask. Projected writes remain in RAM after reconnection.

Use Tab and Enter/Space as well as the mouse. Pressed state and accessible labels
report which lines are forced low, without relying on color. The diagram follows
system appearance and fits the tested laptop and mobile widths. Older cores
without the mask API disable these switches while keeping existing controls usable.

## The chip drawing is conceptual

This is a logical view of the 64 KiB work-RAM address bus, **not a verified chip
package or motherboard pinout**. A1–A15 are CPU signal names, not physical pin
numbers. Their positions around the rectangle are an interface arrangement.
We have not selected/verified a particular Model 1 board revision, SRAM part or
schematic mapping; this view does not claim a single physical 64 KiB package.

“Disabled” is an explicit **stuck-low approximation**. Removing a real wire can
leave a floating input whose voltage depends on the circuit. The emulator does
not model that analogue behavior, noise or pull resistors. A crossed wire always
means deterministic zero here. This differs from the existing low-dominant pair
bridge: forcing one line low also changes addresses where that line alone is high.

The map follows the pinned core's [work_ram backing and Genesis map](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c).
See [Logic bending](LOGIC-BENDING.md) for the byte-lane convention, mirrors and
upstream references. No physical-pin fidelity is claimed.

## Application and memory behavior

Clicking a wire applies immediately, using the **Access** direction selected
above. Changing the selectors alone does not alter an existing fault; the next
wire click or explicit Apply action uses the new selection. The chip mask stays
latched until reconnected or replaced. Pair Apply and pair pulse controls replace
the mask; they do not pulse the entire chip mask. A chip click cancels a pending
pair pulse. VRAM and work-RAM faults remain mutually exclusive.

For mask `M`, bit 0 represents CPU A1 and bit 14 represents A15. The native
storage adapter maps a word address as `word & ~M`. Byte-address mapping clears
`M << 1`, preserving CPU A0 and therefore the selected byte lane. Reads return
the aliased location without modifying RAM. Writes can alias into another
location; removing the mask does not undo those writes. Read/write isolation is
an experimental control, not a claim that a real disconnected pin distinguishes
transaction direction. No game variables or graphical filters are used.

A reconnect does not clear CPU STOP/HALT or guarantee recovered gameplay. Use
explicit recovery if needed; Clean restart remains a full reboot.

## API and experiment records

`set_logic_address_mask(mask, access)` accepts 0–32767 and read/write/both access
values 1/2/3. Zero clears the RAM fault. Invalid arguments preserve the current
configuration. Nonzero masks replace paired faults and access budgets, reset
fault counters and set the activation frame; normal fault setters clear masks.
`get_logic_address_mask()` returns the active mask. Both use the same runtime
adapter as CPU, DMA-read and Z80-bank hooks; actual Z80 execution is not covered.

v2.4 JSON labels the fault `address-stuck-low`, lists its lines and `addressMask`,
and records `addressLineChanges`: frame, previous/new mask, access, reason and
read/write counts before each transition. Reconnection, paired replacement,
recovery and VRAM takeover record mask removal. Each nonzero change starts new
counters; the transition record preserves the previous counts. Loading a cartridge
or Clean restart clears history. No ROM/RAM bytes are exported.

## Verification and manual reproduction

Native tests enumerate every word address for all 15 single-line masks and
alternating multi-line masks, check source integrity after reads, all-lines-low,
byte-lane preservation, persistent writes, read/write direction, bounds/invalid
settings, replacement, timeout cancellation and reset. Actual-WASM original
cartridges test read aliasing, both faulted longword halves, byte writes and
recovery/restart clearing. Browser tests cover mouse/keyboard, visible crosses,
multiple lines, export, invalid paired replacement, recovery, legacy fallback,
and expanded layout at 1366×768, 390×844 and 844×390.

To reproduce with a private cartridge: open Logic / work RAM, choose Write,
click A1 and A15, and verify both wires have crosses. Export the record before
reconnecting. Reconnect A1 and confirm A15 remains crossed; reconnect all and
confirm the mask is gone. Stored changes or a halted CPU may persist. Repeat
from clean reset for comparisons, and do not infer hardware accuracy or healthy
gameplay from the appearance of the diagram. See [Testing](TESTING.md) for results.
