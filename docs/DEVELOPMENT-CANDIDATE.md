# Development Candidate

The owner approved the full Demo Cart v0.3.8 and publication of **v0.5.2** on
30 October 2026. Require final source CI, complete-package and exact
corresponding-source rebuild verification for the release commit. Use
[development status](DEVELOPMENT-STATUS.md) and
[PR #117](https://github.com/NixMcRetro/VRAMpage-MD/pull/117) for exact source, checks
and Actions downloads; BUILD-INFO.json identifies the packaged commit. Earlier
published assets remain unchanged. Website deployment requires separate approval.

## Changes Since Public v0.5.1

- **Full Demo Cart:** the approved normal 180-second v0.3.8 show from PR #106
  becomes the manifest default. The 20-second hook audition stays separate.
  Keep the original Colour Test, v0.1 source kit, portrait and logo unchanged.
- **FM Output Model:** stage Discrete (default) or Integrated, then apply it with
  Clean Restart or a new cartridge. CPU Reset and Restore retain the active model;
  pending/rejected choices preserve current sound and the checkpoint.
- **File Actions:** use the direct Load Your Own ROM… action accepted by the
  owner in Safari. Configuration/export pickers retain visible click/Enter/Space
  controls without invisible duplicate tab stops.
- **Input and Audio Recovery:** release held keyboard/RAM contacts when hidden,
  retain latched faults and recovery preferences, handle blocked gamepad access,
  complete standard A/D-pad mapping, and resume interrupted/suspended audio from
  Enable Sound with muted retry on failure.

See [v0.5.2 release notes](RELEASE-NOTES-v0.5.2.md) for exact cartridge/package
identities. The retained features below shipped in
[v0.5.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.5.1).

## Retained v0.5.1 Features

- **Work RAM Data Lines:** runtime D0–D15 cuts cover both byte lanes in the
  existing Address/Data chip view. Masks replace address faults or byte-local
  bridges and retain existing recovery rules. [Reference, API and limits](WORK-RAM-DATA.md).
- **Z80 RAM Write:** an off-by-default write-address bridge in the sound CPU's
  8 KiB RAM. It changes future eligible stores without changing native bus
  ownership or read/fetch decoding. Corrupted RAM or instructions can persist
  after removal. [Controls, counters and limits](Z80-RAM-WRITE-BRIDGE.md).
- **RGB Encoder:** off-by-default cuts and one joined RGB pair affect copied
  display pixels independently of memory/audio faults. Raw Emulator Output
  bypasses the effect. This uses explicit black-termination/equal-impedance
  assumptions with byte-code voltage proxies. [Model and lifecycle](RGB-ENCODER-INPUTS.md).
- **Saved Settings and Observations:** configuration v5 includes data masks and both
  newer domains, and imports v1–v4 with missing contacts off. Six-domain disconnect,
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
The [128-cycle mixed-fault workload](TESTING.md#mixed-fault-endurance-checks),
NTSC/PAL approved-cartridge playback, exact source-to-JS/WASM rebuild and
three-browser package CI are release acceptance gates. Retained local results
identify their exact test source; final release verification is recorded
separately and must not be inferred from owner approval.
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

For the approved v0.5.2 release, align VERSION, labels, notes, tag and filenames.
After all required checks pass, prepare the draft using the exact
reviewed main commit with all [manifest-approved original/homebrew cartridges](BUILT-IN-CARTRIDGES.md),
checksums, complete corresponding emulator source and notices. Commercial ROMs
are not included. Verify downloaded assets against their source/tag/metadata;
preserve existing public releases. Website deployment requires separate approval.

Composite/sync/mono encoder faults and physical VRAM timing are deferred models.
[NTSC VA6 device mapping](VA6-RAM-VALIDATION.md) still needs matching board evidence;
the chip diagram remains conceptual and that exact-board work is optional.
Development-source [Work RAM data cuts](WORK-RAM-DATA.md) now use the documented
PAL two-byte reference, with the same digital/electrical limits.
