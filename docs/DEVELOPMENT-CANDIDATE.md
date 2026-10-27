# Development Candidate

These draft notes describe merged development work after public v0.5.0. They do
not select a release version or tag. The live McRetro.net page and published
release downloads retain their existing builds. Use the latest verified
[development checkpoint](WORK-QUEUE.md) for the current source, CI and Actions
download; its BUILD-INFO.json identifies the exact commit.

## Changes Since Public v0.5.0

- **Z80 RAM Write:** an off-by-default write-address bridge in the sound CPU's
  8 KiB RAM. It changes future eligible stores without changing native bus
  ownership or read/fetch decoding. Corrupted RAM or instructions can persist
  after removal. [Controls, counters and limits](Z80-RAM-WRITE-BRIDGE.md).
- **RGB Encoder:** off-by-default cuts and one joined RGB pair affect copied
  display pixels independently of memory/audio faults. Raw Emulator Output
  bypasses the effect. This uses explicit black-termination/equal-impedance
  assumptions with byte-code voltage proxies. [Model and lifecycle](RGB-ENCODER-INPUTS.md).
- **Saved Settings and Observations:** configuration v4 includes both domains
  and imports v1/v2/v3 with missing newer contacts off. Six-domain disconnect,
  checkpoints and comparison include them. Missing VRAM runtime metadata now
  compares Unknown rather than reporting a display fallback as observed data.
- **Usability:** the VRAM Reconnect All label no longer advertises the obsolete
  0 shortcut; 0 continues to cycle keyboard chip targets.

CPU Reset clears the memory-fault controls while preserving RAM and sound-chip
state at the intervention; subsequent cartridge code can overwrite them. It
retains RGB contacts and the current session checkpoint. Clean Restart fully
reboots, removes all contacts and discards the checkpoint. Restore Checkpoint
clears all six domains, restores the saved machine/image and stays paused.

## Candidate Acceptance

Automated acceptance uses original generated cartridges and separate source,
native sanitizer, compiled-WASM and three-browser/package checks. The current
[checkpoint](WORK-QUEUE.md) records completed evidence and remaining blockers.
The mixed-fault endurance workload is an additional acceptance gate in progress;
its results must be recorded before presenting this draft as a tested candidate.
Browser-software checks do not establish physical electrical accuracy, listening
quality, every cartridge's recovery or native desktop acceptance on every OS.

For native-browser review of the new features, use a legally usable cartridge:

1. Try RGB cuts/joins, enable Raw Emulator Output, then reconnect RGB. Check that
   the bypass preserves the selected contacts and reconnect returns the ordinary
   picture without a CPU reset.
2. Try a Z80 RAM pair while the game's sound driver runs. Counters depend on the
   cartridge's eligible writes; silence or a stopped driver can be a fault result.
   Removal stops future aliasing and does not repair earlier corruption.
3. Save a fault-free checkpoint, apply contacts, then restore. Check that the
   controls clear and the saved image returns paused. CPU Reset retains the slot;
   Clean Restart discards it.
4. Save/stage a circuit file, inspect the preview, then apply it. Older files
   explicitly leave newer contacts off. Selecting a file alone must not activate
   it or upload cartridge data.

## Publication Handoff

Choose a meaningful version and align VERSION, labels, release notes, tag and
filenames only after a release decision. Publish the exact reviewed main commit
with its ROM-free browser ZIP, checksum, complete corresponding emulator source
and notices. Verify the downloaded asset against its source/tag/metadata. Preserve
existing public releases. Website deployment is a separate repository/action.

Composite/sync/mono encoder faults and physical VRAM timing are deferred models.
[NTSC VA6 device mapping](VA6-RAM-VALIDATION.md) still needs matching board evidence;
the chip diagram remains conceptual. No new hardware-fault model is implied by
this candidate.
