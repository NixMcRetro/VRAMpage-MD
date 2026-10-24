# VRAMpage MD

**Play Sega Mega Drive / Genesis games in your browser and experiment with simulated hardware faults.** VRAMpage MD is an experimental, hardware-informed circuit-bending workbench built from a modified Genesis Plus GX emulator. Supply your own legally usable game cartridge file. No game ROMs are included or uploaded.

> **New here? Start with the Mac download below.** You do not need to know Git, install a developer application or compile an emulator.

## Download and play on your Mac

**[Download VRAMpage MD v0.3.0 - complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.3.0/VRAMpage-MD-v0.3.0-macos.zip)**

1. Download the ZIP and double-click it in Finder to extract it.
2. Open the **VRAMpage-MD** folder and double-click **START.command**.
3. When the browser opens, choose **Load ROM** and select your own legally usable `.md`, `.bin` or `.gen` game.
4. Click **Enable Sound** for audio. Keep the launcher Terminal window open while playing.

**Needs:** macOS and **Python 3**. The included launcher runs a small server on your own computer. There is no account, cloud backend or Emscripten setup. It is a *local browser app*, not a native Mac `.app`.

If your Mac blocks `START.command`, right-click it and choose **Open**, or follow the short [Mac launch and troubleshooting guide](docs/RUNNING-LOCALLY.md). To use Firefox, make Firefox your default browser or open the local address printed by the launcher in Firefox.

**Important:** GitHub's green **Code → Download ZIP** gives you a *source-only* archive, not the ready-to-run application. Use the **complete Mac ZIP** above.

[Previous v0.2.8 Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.8/VRAMpage-MD-v0.2.8-macos.zip) remains available for reproducing earlier experiments.

[Latest release and checksum](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.3.0) · [Other runnable versions and historical source releases](docs/RELEASE-HISTORY.md)

**v0.3.0:** choose **Frame projection** or **Transaction** in the VRAM patchbay, then use the same legs and bridges. Transaction mode maps actual emulator VRAM accesses and exports separate model metadata and counters. Frame projection remains the default fallback. Both are digital approximations.

**RAM research:** a [reproducible bounded experiment](docs/RAM-STATUS-FOLLOWUP.md) now shows player-trajectory divergence while recorded demo inputs continue at the same phase. This uses the existing public core and does not establish physical electrical accuracy.

## What can it do?

- **Play:** Load a cartridge from your computer, use keyboard/gamepad controls, enable sound, pause, reset or go fullscreen.
- **Bend video memory:** Click the VRAM AD0–AD7 chip legs to simulate disconnected address lines, or bridge two signals. Watch how the game's video memory responds.
- **Bend game logic:** Experiment with 68000 work-RAM address/data faults, short pulses and affected-write limits. Check CPU STOP/HALT indicators and try explicit recovery.
- **Compare experiments:** Record fault settings and export JSON containing reproducibility metadata, including a build identifier when available.

The interface fits different window sizes, follows your system Light/Dark preference and offers both corrected video output and raw diagnostic output. Some faults can freeze a game or leave persistent RAM corruption until a **Clean restart**.

**Experimental limitations:** VRAM offers frame projection and logical-byte transaction models; neither VRAM nor RAM faults reproduce every physical electrical effect. The circuit diagrams are conceptual, not verified motherboard pinouts. Rendering remains line-batched rather than cycle-accurate. Hardware-informed audio bending is the next major milestone. Automated Linux browser/core tests are not the same as native Mac Firefox or physical-hardware validation.

## For developers, researchers and maintainers

| Topic | Where to start |
| --- | --- |
| Source code and contributor build | [Developer build instructions](docs/DEPLOYMENT.md) |
| Transaction VRAM development | [Browser controls and handoff behavior](docs/LOGIC-BENDING.md#browser-transaction-vram-integration), [runtime build](docs/VRAM-RUNTIME-BUILD.md) and [model API](docs/VRAM-PUBLIC-MODEL-API.md) |
| Technical architecture and fault assumptions | [Logic bending](docs/LOGIC-BENDING.md) · [Video output](docs/VIDEO-OUTPUT.md) |
| Current verified state and experiments | [Development status](docs/DEVELOPMENT-STATUS.md) · [Experiment records](docs/EXPERIMENTS.md) · [RAM trace](docs/RAM-WRITE-TRACE.md) |
| Roadmap and next work | [ROADMAP.md](ROADMAP.md) · [Work queue](docs/WORK-QUEUE.md) |
| Automated and manual validation | [Testing guide](docs/TESTING.md) |
| Release versions and provenance | [Release history](docs/RELEASE-HISTORY.md) · [Versioning policy](docs/VERSIONING.md) |
| All technical documents | [Documentation index](docs/README.md) |
| Agent/development rules | [AGENTS.md](AGENTS.md) |

### Build from source

Contributors need Git, Python 3, Make, CMake and Emscripten 4.0.23. From the repository root:

```sh
source ~/emsdk/emsdk_env.sh
bash scripts/test.sh
bash scripts/build-core.sh normal
bash scripts/build-core.sh site-runtime
node tests/test_wasm_logic.cjs site/core/genplus.js
python3 scripts/serve.py --no-browser
```

The emulator uses `h1romas4/wasm-genplus` pinned at `6090aff9e9b2f578cd28882bd4571d2e35b1d674`, with modified Genesis Plus GX. See the [third-party notices](THIRD-PARTY-NOTICES.md): the upstream restrictions include **non-commercial distribution** and corresponding-source requirements. Runnable releases include the modified emulator source, notices, launcher and checksums; no Sega ROMs or commercial game assets.

**Repository separation:** Development and releases belong to `NixMcRetro/VRAMpage-MD`. Nothing in this repository automatically deploys to [McRetro.net](https://mcretro.net/); website publication needs separate explicit approval.
