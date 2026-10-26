# 🎛️ VRAMpage MD

A browser workbench for circuit-bending a Sega Mega Drive / Genesis. Experiment
with video memory, Work RAM and FM/PSG sound through a modified emulator.

**[Open VRAMpage MD](https://mcretro.net/homepages/vrampage-md/)** ·
**[Download v0.5.0](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip)** ·
[Checksums](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt)

## 🎮 Try It

Open the live app, choose **Load ROM**, then **Enable Sound**. Cartridge files
stay in your browser and are not uploaded. Use your own legally usable ROM, or
start with the free original test program:

> [!TIP]
> **[Download the Colour-Test ROM](https://mcretro.net/assets/downloads/2026/10/vrampage-md/VRAMpage-MD-Colour-Test.bin)** ·
> [ROM and Python Source ZIP](https://mcretro.net/assets/downloads/2026/10/vrampage-md/VRAMpage-MD-Colour-Test.zip) ·
> [About the Project](https://mcretro.net/vrampage-md-bending-bits/)
>
> The 64 KiB test ROM uses original code and graphics. It is silent, so use another
> cartridge for FM/PSG experiments. Commercial games are not included in this
> repository or the browser package.

## ⚡ What Can You Bend?

| Chip | Experiments |
| --- | --- |
| **VRAM** | Cut modelled video-memory address lines or bridge a pair. |
| **SRAM (Work RAM)** | Alter address lines; hold A11–A15 write contacts or apply eight-frame pulses. |
| **FM / PSG** | Alter each chip's input writes independently, or use its **Randomiser** button. |

Save configurations, compare exported experiments, use a session checkpoint,
or try **Force Resume**, **CPU Reset** and **Clean Restart**.

These are experimental digital models, not electrically accurate motherboard
simulations. A fault can stop a game or leave corrupted memory/sound state after
it is removed. **CPU Reset** preserves RAM and sound-chip state, although
restarted game code can overwrite RAM. **Clean Restart** fully reboots.
See the [controls and recovery guide](docs/RUNNING-LOCALLY.md).

Development source also includes an optional
[Z80 RAM Write Bridge](docs/Z80-RAM-WRITE-BRIDGE.md) for sound-driver memory.
It is off by default and is not included in the published v0.5.0 download.

## 💻 Run Locally

Download and extract the complete **v0.5.0 browser ZIP** above. From its
**VRAMpage-MD** folder, run:

| System | Command |
| --- | --- |
| Windows | `py -3 scripts/serve.py` |
| macOS / Linux | `python3 scripts/serve.py` |

Keep the terminal open while using the app; press **Ctrl+C** to stop the server.
On macOS, **START.command** is an optional shortcut. Hosted use needs only a
browser; local use also needs Python 3. No emulator compilation is needed for
the complete package. GitHub's **Code → Download ZIP** is source-only.
[Launch help and troubleshooting](docs/RUNNING-LOCALLY.md).

## 🧩 Source and Credits

- **VRAMpage MD:** Nix McRetro, with Codex assistance for the workbench, fault
  models, recovery and testing.
- **Genesis Plus GX:** [Eke-Eke](https://github.com/ekeeke/Genesis-Plus-GX),
  building on the original Genesis Plus by Charles Mac Donald.
- **WebAssembly port:** [h1romas4/wasm-genplus](https://github.com/h1romas4/wasm-genplus),
  pinned at `6090aff9e9b2f578cd28882bd4571d2e35b1d674`.
- **Core components:** Nuked OPN2 by Alexey Khokholov (Nuke.YKT), Musashi by
  Karl Stenerud, and the Z80 emulator by Juergen Buchmueller. Further component
  credits and full terms are in [Third-Party Notices](THIRD-PARTY-NOTICES.md).

The emulator's upstream terms include **non-commercial distribution** and
**complete corresponding-source requirements**. Runnable packages include the
modified emulator source and notices. Those terms do not grant rights to games.

## 📚 Further Reading

[Build from Source](docs/DEPLOYMENT.md) · [Documentation](docs/README.md) ·
[Testing](docs/TESTING.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md)

For historical downloads, including the preserved
[v0.4.1 package](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip),
see [Release History](docs/RELEASE-HISTORY.md). Development here does not
automatically deploy to McRetro.net; website releases are managed separately.
