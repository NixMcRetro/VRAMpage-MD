# VRAMpage MD releases and source history

**[Download the current ready-to-run Mac package: v0.2.6](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.6/VRAMpage-MD-v0.2.6-macos.zip)**

For ordinary use, download the complete ZIP, extract it, open **START.command** and load your own legally usable cartridge. Python 3 is required; you do not need Git or WebAssembly build tools. See [Mac launch help](RUNNING-LOCALLY.md).

**Note:** Source development on `main` is labelled v0.2.7; that does not mean a v0.2.7 runnable release has been published. The latest published package listed here remains v0.2.6.

There are **two kinds of GitHub release** here. The complete Mac downloads include the compiled emulator; older *source-history milestones* do not. GitHub's automatically generated **Source code (zip)** is not a playable Mac application.

## Complete runnable Mac downloads

| Version | What changed | Download |
| --- | --- | --- |
| **[v0.2.6](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.6)** (current) | Build identification in experiment exports; existing VRAM/RAM patchbay | [Complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.6/VRAMpage-MD-v0.2.6-macos.zip) |
| [v0.2.5](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.5) | Independent VRAM leg switches | [Complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.5/VRAMpage-MD-v0.2.5-macos.zip) |
| [v0.2.4](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.4) | Consolidated workbench, RAM controls and core display fixes | [Complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.4/VRAMpage-MD-v0.2.4-macos.zip) |

Each runnable release has its own `SHA256SUMS.txt`, release-specific source commit, original compiled core and corresponding modified emulator source. Previous packages remain available for reproducibility; use v0.2.6 for new installations.

## Earlier milestones: source history only

These releases were created retrospectively from their **actual development commits**, to preserve an understandable timeline. They do **not** include compiled Mac ZIPs and have not been freshly validated as standalone releases.

| Version | Original commit | Development milestone |
| --- | --- | --- |
| [v0.1.0](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.1.0) | [a391c4a](https://github.com/NixMcRetro/VRAMpage-MD/commit/a391c4a715b11c810b07aee5ba8d1d032f3aa223) | Original browser prototype |
| [v0.1.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.1.1) | [d9b95bc](https://github.com/NixMcRetro/VRAMpage-MD/commit/d9b95bcbd723841773c12dd8ed168e51130a6095) | Workbench and fullscreen improvements |
| [v0.1.2](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.1.2) | [16f7b44](https://github.com/NixMcRetro/VRAMpage-MD/commit/16f7b44dbd82aaad5bba30ea6cf6603d839b9437) | Compact UI and clean restart |
| [v0.1.3](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.1.3) | [6b4b88c](https://github.com/NixMcRetro/VRAMpage-MD/commit/6b4b88c9d64bc8b7ffe11255ffc1f74b7c9934b4) | System appearance and video recovery |
| [v0.1.4](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.1.4) | [b3a6bd2](https://github.com/NixMcRetro/VRAMpage-MD/commit/b3a6bd2374d35a5513c88ac919512ce1d00f83cf) | Native framebuffer and window sizing |
| [v0.2.0](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.0) | [46d0638](https://github.com/NixMcRetro/VRAMpage-MD/commit/46d0638e8d7b40b277dcbff57ab205172540f32d) | Work-RAM integration |
| [v0.2.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.1) | [80dd553](https://github.com/NixMcRetro/VRAMpage-MD/commit/80dd55359cb0a4a80fb7308d96438b1b75bd3486) | CPU recovery |
| [v0.2.2](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.2) | [f26501f](https://github.com/NixMcRetro/VRAMpage-MD/commit/f26501fbd0477d1c76bf71f944e017f4567196a5) | Short fault pulses and surveys |
| [v0.2.3](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.3) | [fa464ab](https://github.com/NixMcRetro/VRAMpage-MD/commit/fa464ab67a29062a57a11a2c8f259fb2b72c3eca) | Affected-write limits and longword repair |

The misnumbered v2.4.0 **release entry was removed previously**. Its original source-history Git tag remains, and the canonical runnable release is [v0.2.4](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.4). Earlier provisional references to v2.1–v2.4 correspond to canonical v0.2.1–v0.2.4; historical commits and experiment records are not rewritten.

For the technical detail behind each step, see the [changelog](../CHANGELOG.md), [versioning policy](VERSIONING.md) and [testing record](TESTING.md).

For an audit trail of the public release descriptions **before** they were simplified,
see the [original-release-note archive](archive/original-release-notes/README.md).
