# 🎛️ VRAMpage MD

**Bend the bits. Break the rules. See what happens.**

A browser workbench for experimental circuit-bending of the Sega Mega Drive / Genesis. Poke at video memory, play with Work RAM, and make the FM and PSG chips do wonderfully strange things.

[**🎮 Play on McRetro.net**](https://mcretro.net/homepages/vrampage-md/) | [**📦 Download v0.5.2**](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.2/VRAMpage-MD-v0.5.2-browser.zip) | [**📚 Full guide**](USER-GUIDE.md)

**Download:** v0.5.2. **Hosted version:** v0.5.1. Website updates are approved separately.

## ⚡ What can you bend?

| | |
| --- | --- |
| 🖼️ **VRAM** | Cut or bridge modelled video-memory address lines |
| 🧠 **Work RAM** | Alter address and data lines, inhibit writes, and experiment with pulses |
| 🎶 **FM / PSG** | Bend sound-chip input writes and try the randomisers |
| 🌈 **RGB** | Experiment with optional encoder input contacts |
| 🔁 **Recovery** | Save checkpoints, compare experiments, and restart when things get weird |

These are experimental digital models, not electrically accurate motherboard simulations. Faults can freeze games or leave corrupted state.

## 🎮 Built-in cartridges

- 🎆 **Demo Cart:** An original three-minute show (v0.3.8 in the v0.5.2 download).
- 🌈 **Colour Test:** An original silent colour-pattern cartridge.
- 💾 **Load your own ROM:** Use a legally usable Mega Drive ROM. Your file stays in your browser.

Try the demo, enable sound, and see how far you can bend the bits. No commercial games are bundled.

## 🚀 Try it

[Open the hosted app](https://mcretro.net/homepages/vrampage-md/) in your browser, or download the complete browser ZIP and extract it.

For local use, open a terminal in the extracted VRAMpage-MD folder and run:

| System | Command |
| --- | --- |
| Windows | `py -3 scripts/serve.py` |
| macOS / Linux | `python3 scripts/serve.py` |

Keep the terminal open; Ctrl+C stops the server. macOS users can also use START.command. Python 3 is required for local use, but no emulator compilation is necessary. GitHub's Code / Download ZIP is source-only.

## 📚 Dig a little deeper

- [Full user and technical guide](USER-GUIDE.md) - controls, cartridges, recovery, and credits
- [v0.5.2 release notes](docs/RELEASE-NOTES-v0.5.2.md) - what's new
- [Launch help](docs/RUNNING-LOCALLY.md) - getting started and troubleshooting
- [Documentation](docs/README.md) - technical experiments
- [Build from source](docs/DEPLOYMENT.md) - deployment
- [Testing](docs/TESTING.md) - verification
- [Changelog](CHANGELOG.md) - development history
- [Release history](docs/RELEASE-HISTORY.md) - older packages
- [Roadmap](ROADMAP.md) - what's next

## ❤️ Source and credits

VRAMpage MD by Nix McRetro, with Codex assistance. Built on Genesis Plus GX by Eke-Eke (building on Charles Mac Donald's Genesis Plus), with the WebAssembly port by h1romas4 and contributions from the original emulator component authors. See the [full credits](USER-GUIDE.md#-source-and-credits).

The emulator's upstream terms include non-commercial distribution and complete corresponding-source requirements. Runnable packages include modified emulator source and notices. These terms do not grant rights to games.

[📦 Corresponding source v0.5.2](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.2/VRAMpage-MD-v0.5.2-corresponding-source.zip) | [🔐 Checksums](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.2/SHA256SUMS.txt) | [📜 Third-party notices](THIRD-PARTY-NOTICES.md)

**Happy bending! ⚡**
