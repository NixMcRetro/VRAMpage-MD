# VRAMpage MD

VRAMpage MD is a browser-based NTSC Sega Mega Drive / Genesis Model 1 emulator
experiment. Play your own locally supplied cartridge while exploring deterministic,
hardware-informed VRAM and 68000 work-RAM faults. **v2.4 is experimental:** the
chip diagrams are conceptual and the models are not electrically accurate.

## Download and run on a Mac

**[Download the complete v2.4.0 Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v2.4.0/VRAMpage-MD-v2.4.0-macos.zip)**
([release notes](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v2.4.0)).

1. Download that ZIP and extract it in Finder.
2. Open the extracted **VRAMpage-MD** folder and double-click **START.command**.
3. The app opens in your default browser. Click **Load ROM** and choose your own
   legally usable `.md`, `.bin` or `.gen` cartridge.
4. Click **Enable Sound** for audio. Leave the launcher's Terminal window open.

The complete download includes the compiled WebAssembly core, modified source,
licence notices and launcher. You do not need Git, Emscripten or a developer app.
**Python 3 is required**; the launcher explains how to install it if missing.
GitHub's **Code → Download ZIP** is source-only, so use the download above.
If macOS blocks the launcher, follow the simple drag-and-drop Terminal fallback
in [Run locally](docs/RUNNING-LOCALLY.md). Firefox users can make Firefox their
default browser or open the address printed by the launcher in Firefox.

## What works

- Local cartridge picker, keyboard three-button controls, pause, sound toggle,
  fullscreen and clean restart. ROM data stays on your computer.
- Native framebuffer correction, responsive window sizing and automatic system
  Light/Dark appearance; legacy-core row recovery and raw-output option remain.
- VRAM AD0–AD7 paired bridges, presets, momentary and latched contacts.
- Experimental work-RAM address/data faults with read/write direction, affected
  access counters and CPU STOP/HALT monitoring.
- Explicit CPU resume/reset, short frame pulses and affected-write limits.
- Compact chips with internal labels and short legs; independent A1–A15 stuck-low
  switches show crosses on disabled lines.
- Local experiment logging and JSON metadata export, without ROM or RAM bytes.

Only one fault domain is active at a time. Faulted writes can persist after
reconnection; recovery does not guarantee healthy gameplay. Keyboard mappings
are shown in the app. Standard gamepad axes and buttons are mapped; physical
USB/Bluetooth controller acceptance remains a manual check.

## Limits and unfinished experiments

VRAM faults are frame-scoped approximations. Work-RAM faults model transactions,
not analogue floating pins. Physical pin mappings, continued attract-mode play
after faults, actual Z80 execution coverage, cartridge-bus faults and audio
bending remain incomplete. Normal FM/PSG audio is supported. Native macOS Firefox
and audible playback acceptance must be checked on your Mac; cloud browser and
actual-core checks are recorded in [Testing](docs/TESTING.md).

## Contributor build

Trying the app requires only the complete download above. To modify the core,
install Git, Python 3, Make, CMake and Emscripten **4.0.23**, then from this
repository root run:

```sh
source ~/emsdk/emsdk_env.sh
bash scripts/test.sh
bash scripts/build-core.sh
node tests/test_wasm_logic.cjs site/core/genplus.js
python3 scripts/serve.py --no-browser
```

CMake 4.1.3 is verified; the build supplies the upstream compatibility policy.
Build outputs under `vendor/`, `site/core/` and `site/source/` stay out of Git.
See [release instructions](docs/DEPLOYMENT.md) for producing a complete ZIP.

## Source, rights and project history

The core is `h1romas4/wasm-genplus` pinned at
`6090aff9e9b2f578cd28882bd4571d2e35b1d674`, with modified Genesis Plus GX.
**Non-commercial redistribution only**, with complete corresponding modified
source and upstream notices. See [third-party notices](THIRD-PARTY-NOTICES.md).
No Sega games, logos or commercial ROMs are included.

The integrated history preserves development from the source import through
v2.4. Historical prototype and experiment records remain in the
[documentation index](docs/README.md). See [changelog](CHANGELOG.md) and
[roadmap](ROADMAP.md). Releases belong to this independent repository;
**McRetro.net is not modified or deployed by this workflow**.
