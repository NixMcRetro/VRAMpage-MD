# Demo Cart v0.3.8

The owner approved the full three-minute cartridge on 30 October 2026 for
VRAMpage MD v0.5.2 and future bundles. The approved source is the default
full-show build from [PR #106](https://github.com/NixMcRetro/VRAMpage-MD/pull/106),
head `1a68c0d2c2f999af294e15364c8f06ed92db6b3a`, with its YM2612 pitch and
operator-order corrections. The separate 20-second Music Lab audition remains
experimental and is not an approved bundled cartridge.

## Build and Identity

`site/cartridges.json` is authoritative for the approved source, build output,
byte length, SHA-256, region metadata and redistribution notice. From the root:

```sh
python3 scripts/build-demo-cart.py
python3 scripts/cartridges.py verify-site
python3 -m unittest discover -s demo-cart/show-lab/tests -v
node tests/test_demo_cart_v038_wasm.cjs site/core/genplus.js
```

Generate ROMs from source; do not commit the outputs. Preserve all previously
published cartridges and the checksum-pinned v0.1 source kit. The approved
portrait, logo, title pattern data, tilemap and palette inputs remain unchanged.
Read [cartridge notices](../CARTRIDGE-NOTICES.md) and the
[permanent packaging policy](../../docs/BUILT-IN-CARTRIDGES.md).

## Full Show and Original Soundtrack

Six scenes run for 180 seconds under native NTSC/PAL VBlank timing: Captain
Intro, Chromatic Vortex, Neon Aurora, Sprite Storm, Chroma Reactor and Finale.
The original 150 BPM score contains 900 sixteen-byte tracker events, six YM2612
voices and quiet PSG percussion with bounded VBlank decay. Ten written musical
sections use independent brass lead/response, walking bass, offbeat chops,
organ accents, rests, held notes, transitions and a final cadence.

FM writes use both native banks and key-on channel codes 0, 1, 2, 4, 5, 6.
Logical operators S1/S2/S3/S4 map to register offsets 0/8/4/12. Pitch uses the
OPN2 `Hz * 144 * 2^(21-BLOCK) / clock` F-number relation. A high byte of `0xFF`
holds a note without a key-off; zero rests. Sound is synthesized inside the
cartridge through native chip registers. No commercial recording, transcribed
song, external synthesizer or emulator-mixer modification is used.

A cycles Chroma Reactor bend strength, B restores clean graphics, C selects
maximum distortion and START returns to the menu. Attract mode returns to the
original menu and starts another full show after its idle period.

## Verification and Limits

The source suite verifies structure, checksum/header, manifest approval and
byte-exact original portrait/logo patterns. Actual Genesis Plus GX checks run
both regions, record six fourteen-second PCM excerpts per region, test a complete
show loop and compare A/B/C recovery against an unmodified VDP reference.
Historical v0.3.5 tests remain intact. Browser, package and corresponding-source
checks are separate required gates; no test is replaced by a soundtrack claim.
Technical output does not establish physical console performance or subjective
music quality. Website deployment requires separate approval.
