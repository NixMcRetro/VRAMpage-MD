# Run VRAMpage MD in Your Browser

VRAMpage MD is a cross-platform HTML/CSS/JavaScript/WebAssembly app. Use a modern
browser on Windows, macOS or Linux. The complete package includes the compiled
emulator; no Git, Emscripten or build tools are needed. A hosted build needs only
a browser. Running a local copy requires Python 3 for its small HTTP server.

## Get the Complete Browser Package

The **v0.5.0 browser release candidate** is being verified before publication.
The package is named **VRAMpage-MD-v0.5.0-browser.zip**. For candidate review, open
the matching successful [source-checks run](https://github.com/NixMcRetro/VRAMpage-MD/actions/workflows/source-checks.yml)
and download **VRAMpage-MD-local-review** under Artifacts. GitHub may require
sign-in and wrap the package in another ZIP. Extract the outer artifact and the
browser ZIP, then open the **VRAMpage-MD** folder. BUILD-INFO.json identifies the
source commit; artifacts expire. See the [candidate notes](RELEASE-NOTES-v0.5.0.md).

The historical [VRAMpage-MD-v0.4.1-macos.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip)
remains a public download with its original assets. It predates the candidate's
new controls. **Code → Download ZIP** on GitHub is a different, source-only
archive and cannot run without building the emulator first.

## Start a Local Copy

Install [Python 3](https://www.python.org/downloads/) if it is not already present.
Open a terminal in the extracted **VRAMpage-MD** folder and use the command for
your operating system:

| Operating System | Command |
| --- | --- |
| Windows (PowerShell or Command Prompt) | `py -3 scripts/serve.py` |
| macOS or Linux | `python3 scripts/serve.py` |

On Windows, `python scripts/serve.py` is an alternative if your Python 3 installer
provides `python` rather than `py`. On macOS, you can also double-click
**START.command** in Finder. That optional launcher uses the same local server.

The server chooses an available port, listens only on **127.0.0.1**, and opens
your default browser. If it does not open, copy the printed `http://127.0.0.1:…/`
address into a browser. Keep the terminal open while playing; press **Ctrl+C**
there to stop the server. No online account is needed to run an extracted copy.

Choose **Load ROM**, select your own legally usable Mega Drive cartridge, then
click **Enable Sound**. ROM files are read locally by your browser and are not
uploaded. Use the on-screen keyboard guide to play. To use another browser, open
the same printed local address there.

Serve the files over HTTP; opening site/index.html directly as a `file://` URL can
prevent the WASM emulator from loading. To choose a port, append `--port 8000`.
To serve without automatically opening a browser, append `--no-browser`.

## Static Hosting

The built **site/** directory can also be served by an ordinary static HTTP/HTTPS
host. Keep its relative asset paths, compiled **core/** files, corresponding
**source/** and notices together; serve `.wasm` as `application/wasm`. Visitors
then need only a browser, with no Python installation or OS-specific launcher.
See [build and deployment](DEPLOYMENT.md) for maintainer instructions and licence
requirements. Preparing this package does not publish a website or authorise
changes to McRetro.net.

## Common Problems

- **Missing emulator files:** extract the whole complete package. A source-only
  checkout requires a core build. Keep scripts/serve.py and START.command with
  their accompanying folders.
- **Python command missing:** install Python 3, reopen the terminal, and use the
  command for your operating system above.
- **Port already in use:** the default chooses a free port. If you selected a
  fixed port, try `--port 0`; do not stop unrelated applications.
- **Browser does not open:** copy the printed local address into your browser.
- **No sound:** click **Enable Sound** after loading a cartridge; check browser
  audio permissions, the tab's mute setting and your computer's volume.
- **Game stops after a fault:** disconnect faults first. **Force Resume** and
  **CPU Reset** preserve corrupted memory and may not restore play. **Clean
  Restart** reboots the cartridge. Automatic recovery handles reported HALT only,
  not software loops or a browser blocked inside a frame.
- **macOS blocks START.command:** right-click it and choose **Open**, or run
  `bash START.command` in Terminal from the extracted folder. The launcher is an
  unsigned shell script; obtain it from this repository and inspect it as needed.

## Controls and Cartridge Replacement

The compact chip headings read **VRAM (Video RAM)** and **SRAM (Work RAM)**.
Choose **Cut / Reconnect** to toggle modeled legs, or **Bridge Pair** to join a
pair within a chip. These are deterministic digital approximations, not removal
of the entire chip or verified physical pinouts. Corruption can persist after
fault removal. See [VRAM leg switches](VRAM-LEG-SWITCHES.md).

**0** cycles keyboard chip targets and **1–9** selects that target's presets;
reconnect using the named buttons. RAM Write defaults to **Hold While Pressed**;
release the control to disconnect, or choose an eight-frame pulse. See
[workbench shortcuts](CHIP-WORKBENCH.md#development-source-keyboard-chip-target).

Cartridge files are staged before replacing the current game. Rejected files
leave the accepted cartridge and restart data intact, and stale asynchronous
reads cannot replace a newer selection. If native activation becomes uncertain,
emulation stops explicitly. **Clean Restart** can retry the retained accepted
cartridge; it is not automatic rollback.

## Package Contents and Verification Limits

The complete ZIP contains HTML/CSS/JavaScript, compiled JS/WASM, matching modified
emulator source, third-party notices, the Python local server and optional Mac
launcher. It contains no game ROMs. Follow the upstream non-commercial and
corresponding-source terms in the included notices.

Automated Chromium, Firefox and WebKit checks run on Linux. Reported Mac Safari
checks cover the tested controls and recovery, not every cartridge or browser.
Native Windows/Linux desktop launch, native macOS Firefox and physical-gamepad
coverage must not be inferred from browser automation. See [Testing](TESTING.md)
for exact evidence and remaining limits.
