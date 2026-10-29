# Demo Cart v0.3.6: First Music-Led Rough Cut

**Experimental development only, not approved as a built-in cartridge.**

The base v0.3.5 menu, captain portrait, original logo, sprite and palette
effects, and the A/B/C Chroma Reactor interaction are retained. The
automatically launched original show starts after the existing 10-second
idle menu and then runs for 180 seconds.

| Segment | Duration |
|---|---:|
| Captain Intro | 20 seconds |
| Chromatic Vortex | 30 seconds |
| Neon Aurora | 30 seconds |
| Sprite Storm | 35 seconds |
| Chroma Reactor | 40 seconds |
| Finale (Original Portrait and Logo Reprise) | 25 seconds |

An original 720-event 120-BPM score provides three YM2612 voices and PSG
percussion, driven by 68000 writes at the real VBlank boundary. PAL and NTSC
advance four events per second with fractional timing handled in the PAL
accumulator. START exits the performance. Standalone menu scenes preserve
their earlier shorter durations.

This is a **musical and structural rough cut**, not a final soundtrack or a
completed spectacle. The finale deliberately reuses the unchanged original
artwork. A professional music mix, musical section transitions, richer effect
animation, physical console timing and a human audio/video review are still
required.

## Build and verify

```sh
python3 demo-cart/show-lab/build_show.py
python3 -m unittest discover -s demo-cart/show-lab/tests -v
node tests/test_demo_cart_v036_wasm.cjs site/core/genplus.js
```

Do not change `site/cartridges.json` or publish this candidate until owner
approval. No current VRAMpage MD release or McRetro.net deployment is changed.
