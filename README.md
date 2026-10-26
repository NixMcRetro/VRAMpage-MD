# VRAMpage MD

**Play Sega Mega Drive / Genesis games in your browser and experiment with simulated hardware faults.** VRAMpage MD is an experimental, hardware-informed circuit-bending workbench built from a modified Genesis Plus GX emulator. Supply your own legally usable game cartridge file. No game ROMs are included or uploaded.

## Run in your browser

VRAMpage MD is a **cross-platform HTML/CSS/JavaScript/WebAssembly app** for modern
browsers on Windows, macOS and Linux. A hosted build needs only a browser; a local
copy needs **Python 3** to serve its files. macOS is not an app requirement.

[Download VRAMpage-MD-v0.5.0-browser.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip) · [SHA256SUMS.txt](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt).

The complete package includes the built emulator and matching source. See the
[release notes](docs/RELEASE-NOTES-v0.5.0.md).

1. Extract the complete package and open the **VRAMpage-MD** folder in a terminal.
2. Start the included local server:

   | Operating System | Command |
   | --- | --- |
   | Windows | `py -3 scripts/serve.py` |
   | macOS or Linux | `python3 scripts/serve.py` |

3. The server opens your default browser, or prints a local address you can open
   in another browser. Choose **Load ROM** and select your own legally usable
   `.md`, `.bin` or `.gen` game, then click **Enable Sound**.
4. Keep the terminal open while playing; press **Ctrl+C** there to stop the server.

On macOS, double-clicking **START.command** remains a convenient alternative.
See [cross-platform launch instructions and troubleshooting](docs/RUNNING-LOCALLY.md).
No Git, Emscripten or emulator compilation is needed for the complete package.
GitHub's **Code → Download ZIP** is a source-only archive, not this runnable build.
Open the app through HTTP rather than double-clicking site/index.html.

The existing public **[v0.4.1 complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip)**
and its [release/checksum](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.4.1)
remain unchanged. Its filename reflects the historical Mac launcher packaging;
it does not include the v0.5.0 controls. [Other runnable versions and historical source releases](docs/RELEASE-HISTORY.md)
remain available for reproducing earlier experiments.

**v0.3.0:** choose **Frame projection** or **Transaction** in the VRAM patchbay, then use the same legs and bridges. Transaction mode maps actual emulator VRAM accesses and exports separate model metadata and counters. Frame projection remains the default fallback. Both are digital approximations.

**v0.4.0:** [audio input bridges](docs/AUDIO-BENDING.md) add independent PSG and FM D0-D7 pair controls, exact counters and experiment metadata. They change future chip-input writes before synthesis. Both the 68000 and Z80 routes are covered by synthetic tests; Z80 RAM/arbitration faults and physical electrical fidelity remain outside this model. Enable sound, choose a pair and apply it. Removing a bridge does not repair prior chip state; use clean restart when needed.

**v0.4.1:** [four compact chip diagrams](docs/CHIP-WORKBENCH.md) keep VRAM, Work RAM, FM and PSG visible together. Click legs to disconnect supported lines or join a pair within that chip. Audio cuts use a new stuck-low input model. [Configuration files](docs/CIRCUIT-CONFIGURATIONS.md) save masks and bridges; loading previews settings before explicit Apply. Older configuration files remain importable.

**v0.5.0 candidate:** coordinated fault removal clears every modeled domain while preserving play/pause after a confirmed complete clear. Failed or unverified clears pause for inspection. CPU recovery still clears RAM/VRAM faults and preserves audio faults. These candidate controls are not in the historical v0.4.1 ZIP above; see [recovery semantics](docs/CPU-RECOVERY.md).

v0.5.0 offers **Force Resume: On/Off** and **CPU Recovery: On/Off** beside Randomiser. Both start **On**, as requested. Two consecutive eligible HALT frames permit one Force Resume; if HALT persists for eight more completed frames (~0.13 s), CPU Recovery permits one CPU-only reset. A cleared HALT flag cancels escalation. Each fault experiment gets one sequence; a new fault action, toggle change or explicit Resume permits another. Switch both **Off** for unassisted experiments. Neither static pictures nor ordinary STOP trigger recovery. See [recovery semantics](docs/CPU-RECOVERY.md#development-source-ordered-recovery).

The v0.5.0 candidate adds **Save Checkpoint** and **Restore Checkpoint** in the advanced **Logic / SRAM (Work RAM)** panel. Save with all faults off and controller inputs released. The single checkpoint stays in this tab's current cartridge session; it is never written to a file or included in experiment JSON. Restore clears all fault domains, returns to the saved machine state and image without advancing a frame, and stays paused until **Resume**. CPU Reset keeps the slot; Clean Restart, a new cartridge or reloading the page discards it. Supported scope is ordinary Mega Drive cartridges, three- or six-button pads and validated ordinary SRAM; other mapper/peripheral/audio profiles are refused. A checkpoint can itself contain a broken game.


The v0.5.0 candidate also adds a [read-only comparison of two saved experiment exports](docs/EXPERIMENTS.md#compare-saved-exports-development-source). Inspect identities, settings and recorded results locally; loading an export never applies its settings or replays a run. Missing metadata remains unknown.

The candidate [Randomiser](docs/CHIP-WORKBENCH.md#development-source-randomiser) has separate **PSG**, **FM** and **VRAM** buttons. Each selects cuts or a joined pair within that chip, leaving the other chips unchanged. Save the resulting configuration to keep a useful setup. The public v0.4.1 ZIP is preserved.

The same area includes **CPU Reset**, a copy of **Clean Restart** immediately to its right, and ten **RAM WRITE** pair buttons covering every combination within A11–A15. The default **Hold while pressed** keeps a write-only pair active only while its mouse button or shortcut key is held down; releasing it disconnects the pair. Choose **8-frame pulse** for a contact that disconnects after eight emulated frames. Contact expiry itself issues no CPU recovery; the automatic HALT policy may act on later frames if enabled. Neither mode has an affected-write cap. Removing a fault does not repair earlier corruption.

Candidate fault shortcuts **1–9** target the chip selected by **0**: **VRAM → WRAM → FM → PSG**. The text label identifies the keyboard target. An active fault gives its chip a pale green fill and outline; idle chips keep their normal theme colours. Shift holds a temporary contact until release. WRAM digits cover the first nine displayed A11–A15 pairs; the tenth remains available by button. Reconnect/disconnect buttons remain available; **0 now changes target**. Browser Control/Command/Alt shortcuts keep their normal behaviour.

The candidate also stages cartridge replacements: rejected files keep the
current game and its identity intact, older asynchronous reads cannot replace a
newer selection, and Clean Restart uses the last accepted cartridge. If core
activation becomes uncertain, emulation stops explicitly; it does not pretend
the previous machine state was restored.

**RAM research:** a [reproducible bounded experiment](docs/RAM-STATUS-FOLLOWUP.md) now shows player-trajectory divergence while recorded demo inputs continue at the same phase. This uses the existing public core and does not establish physical electrical accuracy.

## What can it do?

- **Play:** Load a cartridge from your computer, use keyboard/gamepad controls, enable sound, pause, reset or go fullscreen.
- **Bend video memory:** Click the VRAM AD0–AD7 chip legs to simulate disconnected address lines, or bridge two signals. Watch how the game's video memory responds.
- **Bend game logic:** Experiment with 68000 work-RAM address/data faults, short pulses and affected-write limits. Check CPU STOP/HALT indicators and try explicit recovery.
- **Bend audio inputs:** Apply separate FM or PSG write-input bridges, inspect counters and remove them independently. Start at low volume.
- **Compare experiments:** Record fault settings and export JSON containing reproducibility metadata, including a build identifier when available.

The interface fits different window sizes, follows your system Light/Dark preference and offers both corrected video output and raw diagnostic output. Some faults can freeze a game or leave persistent RAM corruption until a **Clean Restart**.

**Experimental limitations:** VRAM offers frame projection and logical-byte transaction models; neither VRAM nor RAM faults reproduce every physical electrical effect. The circuit diagrams are conceptual, not verified motherboard pinouts. Rendering remains line-batched rather than cycle-accurate. Automated Linux browser/core tests are not the same as native Mac Firefox or physical-hardware validation.

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
