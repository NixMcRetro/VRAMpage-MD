# Run VRAMpage MD on your Mac

## Download once, then launch

1. [Download VRAMpage-MD-v0.4.1-macos.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip).
2. Double-click the ZIP in Finder to extract it. Open the **VRAMpage-MD** folder.
3. Double-click **START.command**. It starts a local server and opens your default browser.
4. Click **Load ROM** and select your own legally usable Mega Drive cartridge.
5. Click **Enable Sound**. Use the on-screen keyboard guide to play.

This is one complete ZIP, with the emulator already compiled. No cloning,
GitHub login, Emscripten or manual compilation is needed. **Code → Download ZIP**
on GitHub is a different, source-only download and cannot run without building.

Python 3 is the only local prerequisite. If the launcher reports that it is
missing, install it using the [official macOS installer](https://www.python.org/downloads/macos/),
then double-click **START.command** again. You do not need a desktop development app.

To use Firefox, make it your default browser before launching, or copy the local
address printed in the launcher's Terminal window into Firefox's address bar.
Keep that window open while playing. Press **Control+C** there to stop the server.
ROM files are read locally by your browser; they are not uploaded.

### Development-source cartridge loading safeguards

Later review builds stage new cartridge files before replacing the current game.
A rejected size/header, unreadable file or refused input buffer leaves the last
accepted cartridge and restart data intact. While a game is active, rejection is
reported in the event log without covering its screen or changing play/pause.
Only the latest chosen file may activate; Clean restart cancels earlier pending
reads. Experiment export cancels if cartridge identity changes during hashing,
rather than saving a mismatched name and SHA-256.

If the emulator has begun activation and then fails, the app stops and reports
uncertainty. Clean restart can explicitly retry the retained accepted cartridge;
this is not automatic rollback or game recovery. These development changes do
not replace the immutable public v0.4.1 ZIP.


## If macOS blocks START.command

First try right-clicking **START.command**, choosing **Open**, and confirming
**Open** if macOS offers it. If it still refuses to run:

1. Open **Terminal** (Applications → Utilities → Terminal).
2. Type `bash `, including the space.
3. Drag **START.command** from Finder into the Terminal window.
4. Press **Return**. No path or other command needs to be typed.

The script finds its own folder, even if its name contains spaces.

## Common problems

- **Missing emulator files:** re-download the complete release ZIP and extract
  the whole folder. Do not move START.command away from its accompanying files.
- **Port already in use:** the launcher normally chooses a free port automatically.
  Close a previous launcher window if you no longer need it; do not stop unrelated apps.
- **Browser does not open:** copy the local address printed in the Terminal window
  into Firefox. The server can still be running successfully.
- **No sound:** click Enable Sound after loading a cartridge, check Firefox's
  audio permissions, the tab's mute setting and your Mac's volume.
- **Game stops after a fault:** reconnect lines first. CPU recovery preserves
  corrupted RAM and may not restore play. **Clean restart** reboots the cartridge.
- **Untrusted file warning:** this launcher is an unsigned shell script. Obtain
  the archive from this repository's release page and read it before running.

## Disconnect a VRAM leg

Leave **Leg action** on **Disconnect / reconnect**. After loading a cartridge,
click an AD0–AD7 leg: a **×** marks that address signal forced low. Click the
same leg again to reconnect it, or choose **Reconnect all [0]**. Several legs
may be crossed at once. Choose **Bridge two nets** to retain the earlier paired
short interaction; presets and keyboard contacts still work.

This is a deterministic address-signal approximation, not removal of the entire
VRAM chip. Written corruption can persist; **Clean restart** reboots the cartridge.
See [VRAM leg switches](VRAM-LEG-SWITCHES.md) for details.

## What the complete ZIP contains

HTML/CSS/JavaScript, the compiled JS/WASM emulator, its complete corresponding
modified source and third-party notices, the Python local server and Mac launcher.
The launcher listens only on `127.0.0.1`; it does not require an internet server.
The package contains no commercial ROM. See [Testing](TESTING.md) for the short
manual Firefox checklist and the limits of cloud validation.

Maintainers can still use GitHub Actions artifacts for temporary review. They
expire, and GitHub may wrap the package in another ZIP; the versioned release
asset above is the normal user download.

v0.2.7 includes an optional, default-disabled metadata-only RAM write trace for
developer experiments. Normal play needs no trace setup. See [trace documentation](RAM-WRITE-TRACE.md).

Development builds after the public v0.4.1 ZIP use **0** to cycle keyboard chip
targets and **1–9** for that target's presets; reconnect using the named buttons.
See [workbench shortcuts](CHIP-WORKBENCH.md#development-source-keyboard-chip-target).
