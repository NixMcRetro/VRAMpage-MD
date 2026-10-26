# Z80 Sound RAM and Bus Fault Research

The research record below predates the separately authorized
[development-source write bridge](Z80-RAM-WRITE-BRIDGE.md). Its physical limits
and deferred arbitration decision still apply; published releases are unchanged.

**Status: research/design, not implemented.** Follow-up to
[#75](https://github.com/NixMcRetro/VRAMpage-MD/issues/75), inspected
27 October 2026 (Sydney). The first useful candidate is a write-only address
bridge inside Z80 RAM. Keep bus arbitration unchanged. This does not add a
control, change v0.5.0, or commit a release.

## Sources and Evidence Boundary

- Sega, *Genesis Sound Software Manual*, 21 February 1992, printed pages 1–3
  ([scan, PDF pages 105–107](https://manuals.plus/m/92e49f67ea8b99e0a693b6d44936e78281efbddee702652b65752883719e3c03.pdf#page=105)).
  It identifies 8 KiB sound SRAM, banked 68000 access, byte-oriented uploads,
  BUSREQ/start-up sequencing and the FM reset connection. The scan was visually
  checked; ambiguous OCR timing units are not used as a timing specification.
- Zilog, *Z80 CPU User Manual*, UM008011-0816, printed pages 5–11
  ([PDF](https://www.zilog.com/docs/z80/um0080.pdf#page=19)). BUSREQ/BUSACK
  transfer bus control at machine-cycle boundaries. RESET initializes CPU
  control state; it is not a RAM erase operation. This CPU manual alone does
  not specify Sega's glue logic or sound-chip wiring.
- Inspected emulator: `h1romas4/wasm-genplus`
  [`6090aff9e9b2f578cd28882bd4571d2e35b1d674`](https://github.com/h1romas4/wasm-genplus/tree/6090aff9e9b2f578cd28882bd4571d2e35b1d674),
  the project's existing pin. File links below use this immutable revision.
  These establish implementation behavior, not electrical equivalence.

## Access Map

| Route in the Pinned Core | Behavior and Injection Boundary |
| --- | --- |
| Z80 data `$0000–$3FFF` | `z80_memory_r/w` use `zram[address & 0x1FFF]`: 8 KiB with an upper mirror. |
| Z80 instruction/opcode operands | `cpu_readop` and `cpu_readop_arg` index `z80_readmap` directly, bypassing data-read handlers. |
| Granted 68000 `$A00000–$A0FFFF` window | `z80_read_byte/write_byte` decode `(address >> 13) & 3`; native RAM branches mask to 13 bits. Upper-window aliases are emulator behavior, not a recommendation for software. |
| 68000 word access to that window | Native read duplicates one byte; native write stores the high byte once. Preserve these quirks and the write latency; Sega recommends byte access. |
| Z80 `$4000–$5FFF` | FM handler and original port decode; excluded from RAM injection. |
| Z80 `$6000–$60FF` writes | Serial bank latch. Nine LSB-first writes select the bank; no RAM injection. |
| Z80 `$7Fxx` / `$8000–$FFFF` | VDP route / 32 KiB banked 68000 route, respectively; neither is local Z80 RAM. Existing Work RAM faults may affect the banked main-RAM destination. |
| VDP DMA from the Z80 window | `vdp_dma_68k_io` returns its existing Work RAM/open-bus substitute, not `zram`. Do not add a fictitious Z80-RAM DMA route. |

Source locations:
[`memz80.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/memz80.c#L95-L204),
[`mem68k.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/mem68k.c#L141-L220),
[`z80.c` fetch macros](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/z80/z80.c#L141-L142),
[`genesis.c` fetch map](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L142-L152),
[`vdp_dma_68k_io`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_ctrl.c#L3042-L3060).

The fetch map even aliases RAM above `$3FFF`; upstream explicitly assumes the
PC should not execute there. That shortcut must not be presented as real
hardware execution from FM, VDP or banked ROM. A future read bridge needs an
explicit fetch-path design; changing only `z80_memory_r` would be incomplete.

## Ownership and Reset

The transition code in
[`gen_zbusreq_w` / `gen_zreset_w`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L460-L561)
gives the following states. Use these transitions, rather than the misleading
bit-description comment beside the `zstate` declaration:

| `zstate` | Reset Released | BUSREQ Asserted | Native Result |
| --- | --- | --- | --- |
| 0 | No | No | Z80 stopped; 68000 window unavailable. |
| 1 | Yes | No | Z80 runs; 68000 window unavailable. |
| 2 | No | Yes | Z80 stopped; 68000 window unavailable. |
| 3 | Yes | Yes | Z80 stopped; 68000 RAM/FM window granted. |

Word writes use D8 at `$A11100` (1 requests bus) and `$A11200` (1 releases
reset). Byte writes at these same even register addresses use D0. BUSACK reads report the grant with
bit 0 clear for a byte, bit 8 clear for a word; unrelated bits retain native
bus behavior. Synchronization runs the Z80 to the requesting 68000 timestamp
and rounds resume time to 15 master-clock units. This is an emulator schedule,
not a simulation of each BUSREQ/BUSACK edge. See
[`mem68k.c` control handlers](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/mem68k.c#L309-L339).

Native Z80 reset calls `fm_reset` and leaves `zram` intact; it can therefore
restart a still-corrupted sound driver and reset FM state. This is distinct
from the app's **CPU Reset**, which calls only `m68k_pulse_reset` after memory
fault removal and preserves Z80 RAM/sound-chip state synchronously. Subsequent
cartridge code may request a Z80 reset or reload its driver. **Clean Restart**
boots through native hard initialization and clears RAM. These distinctions
must survive any extension; see [CPU recovery](CPU-RECOVERY.md).

## Smallest Initial Model

Proposed identifier: `z80-ram-write-address-pair-v1`. Off by default, runtime
profile only, ordinary standalone Mega Drive/Genesis cartridge mode
(`system_hw == SYSTEM_MD`). Exclude SMS/compatibility mode, CD, Pico and other
profiles until separately validated. FM-chip implementation selection does not
change the address rule; retain both existing YM2612/YM3438 test profiles.

Select two distinct local byte-address bits A0–A12. For an already-decoded,
permitted RAM store, take `a = address & 0x1FFF` and
`mask = (1 << p) | (1 << q)`. If `(a & mask) != mask`, store at `a & ~mask`;
otherwise store at `a`. Store the original byte once. With A0/A1 bridged,
offsets 0, 1, 2, 3 map to 0, 0, 0, 3. Four stores of 11, 22, 33, 44 hex leave
33 at offset 0 and 44 at offset 3; untouched offsets retain their prior bytes.

Apply this to both local Z80 stores and the 68000's granted RAM-store branches,
after native ownership/region decoding. Do not remap addresses before decoding,
grant denied stores, transform FM/PSG/bank registers, or change timing. Reads
and instruction fetches see the resulting stored bytes normally, so corrupted
code is possible without claiming a read fault. Removing the pair cannot undo
earlier writes. Write-only low dominance is a deterministic experimental rule,
not a literal continuously shorted address net.

Reuse the existing pair-projection rule and export conventions. The Work RAM
byte-address API preserves a 16-bit bus lane and assumes 64 KiB, so it cannot
be called unchanged for this 8-bit/8-KiB device. Share only a small pure
projection helper if that is simpler than the few-line operation; keep domain
state and counters independent. No generalized bus framework is needed.

Proposed counters are unsigned 64-bit `ramWrites` (eligible stores while
configured), `changedAddresses`, and per-owner store totals. Count one native
store once, including same-address/value repeats; denied/I/O/disabled stores
do not count. Export decimal strings, selected lines, effective/support reason,
activation frame and source/model identity using existing conventions. Reject
duplicate/out-of-range lines and unsupported activation without mutation.

Disconnect and **CPU Reset** clear this new memory-fault configuration/counters,
preserve backing RAM and retain existing audio-chip settings. **Clean Restart**
and cartridge replacement clear configuration/counters through initialization.
Native Z80 reset alone retains the selected contact/counters and RAM. Checkpoint
save refuses an active contact; restore removes it and restores saved RAM using
the existing supported-profile policy. All-domain disconnect, export/config
validation and failure reporting must include the domain before public UI work.

## Acceptance Before Implementation

| Fixture / Gate | Required Oracle |
| --- | --- |
| Clean normal vs runtime | Existing original Z80 PSG/FM cartridges: exact PCM, sample counts and finite output with the new model off, for both FM implementations. |
| Literal RAM mapping | Original 68000 bootstrap and separate Z80 writer: initialize four bytes, exercise the A0/A1 example above and inspect literal expected destinations. Cover `$1FFF`, `$2000` mirror, `$3FFF`, all selected-bit combinations and exact counters. |
| Ownership | Exercise all four states above, request/release/reset transitions, byte and native word accesses. Denied stores and FM/bank/VDP writes must not count or change Z80 RAM. Preserve BUSACK and latency. |
| Sound-driver data | Original Z80 program reads a deliberately aliased parameter and writes PSG/FM. Assert the literal emitted input bytes, independent existing bridge effects, finite PCM and a measured active difference. Never infer the RAM cause from PCM alone. |
| Stored instruction / stack | Deliberately alias a code or stack store with an independently enumerated byte oracle; confirm fetch observes stored corruption. Document native fetch-map limits and bound execution with a host timeout. |
| Repetition and removal | Fresh-instance repeats with the same frame/store sequence give equal memory, counters and PCM. Disconnect stops future aliasing, retains damaged RAM, and does not promise restored music. |
| Recovery / lifecycle | Synchronous CPU Reset preserves RAM/audio before game instructions; native Z80 reset preserves RAM while resetting FM; Clean Restart matches a fresh baseline. Exercise checkpoint refusal/restore, invalid profiles, partial disconnect failure and domain isolation. |
| Integration | Native ASan/UBSan, meaningful actual-WASM checks, three-browser controls/export and ROM-free package checks before any merge. Compare inactive performance against the same pinned core. |

These are future test requirements, not results from an implemented fault.
During this research the existing `test_z80_psg_runtime.cjs` and
`test_fm_data_runtime.cjs` passed against the unchanged local normal/runtime
builds: clean PCM equality, changed active input writes, independent audio
bridges and native partial reset. They do not validate the proposed RAM model.

## Arbitration Decision and Remaining Limits

Defer BUSREQ/BUSACK/WAIT/reset fault injection. The pinned core's state/map
switching does not expose a contention waveform, and forcing a convenient
grant could merely hide a deadlock or permit impossible simultaneous owners.
A later arbitration proposal needs trace-backed edge timing and explicit
bounded failure tests before selecting a model. Nothing here guarantees more
glitches, audible quality, fewer game locks or physical VA6 pin equivalence.

The research criteria in #75 are satisfied by this map, bounded proposal and
test plan. Implementation remains a separate feature decision under the
stabilization freeze. No commercial cartridge or physical board was tested.
