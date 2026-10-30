# VRAMpage MD v0.5.2

The approved full **Demo Cart v0.3.8** is now the default built-in cartridge.
Its 180-second show combines six visual scenes with original native FM/PSG
music. Let the menu idle to start the show, or select a scene with directions
and launch it with A/B/C/START. Chroma Reactor retains A to cycle bend strength,
B to recover graphics, C for maximum distortion and START to return to the menu.
The original Colour Test, v0.1 source kit, captain portrait and logo are unchanged.

Changes since v0.5.1:

- **FM Output Model:** choose Discrete (default) or Integrated and apply it with
  Clean Restart or a new cartridge. CPU Reset and Restore Checkpoint retain the
  active model. Pending/rejected choices preserve current sound and the checkpoint.
- **File Pickers:** Load Your Own ROM… opens directly from its button, including
  the owner-accepted Safari interaction. Configuration/export actions support
  click, Enter and Space without invisible duplicate tab stops. ROMs stay local.
- **Input Recovery:** hidden tabs release held keyboard inputs and momentary
  RAM contacts while retaining latched faults and recovery preferences. Gamepad
  access failures preserve keyboard input; standard A/D-pad mapping is complete.
- **Audio Recovery:** Enable Sound resumes interrupted or suspended contexts.
  Failed resumes stay muted and allow retry with the existing context.

Disconnecting a fault stops future interference; earlier corruption can remain.
CPU Reset preserves RAM and sound-chip state at the intervention. Clean Restart
fully reboots and discards the session checkpoint. Restore Checkpoint clears
faults, restores the saved machine/image and remains paused.

The approved Demo Cart is the normal `VRAMpage-MD-Demo-Cart-v0.3.8-Show.bin`
from [PR #106](https://github.com/NixMcRetro/VRAMpage-MD/pull/106), candidate
`1a68c0d2c2f999af294e15364c8f06ed92db6b3a`: **167,720 bytes**, SHA-256
`1baf324f8f997029513cea9855856148589df91882e7ae5d0c2a3b8906da5ffc`.
The [approved manifest](../site/cartridges.json) selects
`demo-cart/show-lab/build_show.py`; the 20-second hook audition is not the
approved bundled cartridge. Cartridge and application versions are independent.

Distribution requires `VRAMpage-MD-v0.5.2-browser.zip`,
`VRAMpage-MD-v0.5.2-corresponding-source.zip` and `SHA256SUMS.txt`. The complete
browser ZIP includes every manifest-approved cartridge, matching cartridge and
modified emulator source, compiled JS/WASM, notices, Python server,
START.command and instructions. Check `BUILD-INFO.json`, source metadata and
the v0.5.2 tag against the exact release commit. GitHub's automatic source
snapshot does not replace the complete corresponding-source ZIP.

Publication requires protected PR/main checks, CodeQL, NTSC/PAL native cartridge
verification, browser/package checks, checksums and an exact source-to-JS/WASM
rebuild with the pinned toolchain. [Development status](DEVELOPMENT-STATUS.md)
records final evidence; owner approval alone does not establish these results.
Linux browser automation does not establish physical-console accuracy or native
desktop/controller coverage beyond recorded acceptance. Existing source/licence
obligations remain unchanged.

Earlier public releases remain unchanged. The hosted app remains at v0.5.1;
McRetro.net deployment requires separate approval.
