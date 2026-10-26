# VRAMpage MD v0.5.0

Candidate release notes. This version is being verified; these notes do not
announce a published release. The immutable public v0.4.1 tag and assets remain
unchanged.

## Cross-Platform Browser Package

The complete **VRAMpage-MD-v0.5.0-browser.zip** contains the HTML/CSS/JavaScript
app, compiled WebAssembly emulator, matching modified core source and notices.
Run it in a modern browser on Windows, macOS or Linux. Use the included Python 3
local server, or serve the built site from static HTTP/HTTPS hosting. macOS users
can keep using the optional START.command launcher. No ROMs are included.

See [launch instructions](RUNNING-LOCALLY.md). Before publication, candidate
packages are available as expiring GitHub Actions review artifacts. Verify the
package's BUILD-INFO.json source commit against the reviewed run. A final release
must provide the matching ZIP, SHA-256 checksum and tag; no v0.5.0 public download
is claimed here.

## Changes Since v0.4.1

- Independent **PSG**, **FM** and **VRAM** Randomiser buttons select chip-local
  cuts or bridges. Coordinated fault removal reports partial failures honestly.
- Ten **RAM Write** A11–A15 pair buttons support default **Hold While Pressed**
  and explicit eight-frame contacts. Releasing a contact does not repair prior
  corruption. RAM Write leaves Randomiser button appearance unchanged.
- **0** cycles the keyboard fault target; **1–9** selects its presets. Active
  faults use pale green chip fills/outlines. Chip headings identify **SRAM (Work
  RAM)** and **VRAM (Video RAM)** while chip bodies retain their short names.
- **Force Resume** and **CPU Recovery** are independent switches near Randomiser,
  both initially On. Two eligible HALT frames permit one Force Resume; eight
  further consecutive HALT frames permit one CPU-only reset. Clearing HALT
  cancels escalation. A bounded sequence prevents automatic reset loops; both
  switches Off selects unassisted operation.
- **Save Checkpoint** and **Restore Checkpoint** provide one explicit, private
  in-memory slot for the current cartridge session. Restore clears faults and
  returns paused. CPU Reset retains the slot; Clean Restart, a new cartridge or
  page reload discards it. No automatic rewind or checkpoint-file import is added.
- Read-only comparison of saved experiment exports distinguishes identity,
  settings and recorded results without applying settings or replaying games.
- Audio queue cleanup, modifier-key isolation and staged cartridge replacement
  avoid stale host audio/input and preserve accepted cartridge identity when a
  replacement file is rejected.

## Known Limits and Release Evidence

Recovery responds to reported HALT; it cannot detect software loops or a browser
blocked inside a frame. CPU-only recovery preserves RAM and sound-chip state,
but resumed game code may overwrite them. Neither recovery nor checkpoints
promise playable results for every glitch.

Checkpoint support is limited to validated ordinary Mega Drive cartridge,
three-/six-button pad and SRAM profiles; unsupported mappings/peripherals are
refused. The checkpoint stays in memory and may itself contain a broken game.
Faults remain hardware-informed digital approximations, not cycle-level or
physical electrical validation.

Chromium, Firefox and WebKit automation uses Linux and original synthetic
cartridges. The user reports Mac Safari controls, audio and recovery working;
this does not establish native Windows/Linux desktop launch, native macOS
Firefox, physical-gamepad or universal cartridge coverage. Exact candidate CI,
package identity and checksums belong in the final delivery record before
publication. See [the testing guide](TESTING.md).

Upstream non-commercial and corresponding-source terms continue to apply.
This candidate does not deploy or modify McRetro.net.
