# VRAMpage MD v0.5.0

The cross-platform browser release. The immutable public v0.4.1 tag and assets remain unchanged.

## Cross-Platform Browser Package

The complete **VRAMpage-MD-v0.5.0-browser.zip** contains the HTML/CSS/JavaScript
app, compiled WebAssembly emulator, matching modified core source and notices.
Run it in a modern browser on Windows, macOS or Linux. Use the included Python 3
local server, or serve the built site from static HTTP/HTTPS hosting. macOS users
can keep using the optional START.command launcher. No ROMs are included.

[Download the complete browser ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip) · [SHA256SUMS.txt](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt).

Extract the ZIP and open its VRAMpage-MD folder in a terminal. Windows: `py -3 scripts/serve.py`; macOS/Linux: `python3 scripts/serve.py`. Python 3.8 or later is required for local serving; hosted use needs only a browser. The optional Mac START.command launcher is also included. GitHub's automatic source archives do not contain the built emulator.

See [launch instructions](https://github.com/NixMcRetro/VRAMpage-MD/blob/v0.5.0/docs/RUNNING-LOCALLY.md). BUILD-INFO.json identifies the exact source commit. The tagged package retains its candidate-stage documentation as provenance; use the direct downloads above for the published release.

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
Firefox, physical-gamepad or universal cartridge coverage. All seven candidate PR checks and all seven main checks passed; the release
workflow also rebuilt and verified the packaged runtime before publication. See [the testing guide](https://github.com/NixMcRetro/VRAMpage-MD/blob/main/docs/TESTING.md).

Upstream non-commercial and corresponding-source terms continue to apply.
This release does not deploy or modify McRetro.net.

Source commit: `e9f366fb3985f11430d353c3b2589f076ff93128`.
Candidate validation: https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40297233926
Release validation: https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40302794303
