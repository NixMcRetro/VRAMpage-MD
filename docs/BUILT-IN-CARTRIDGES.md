# Built-In Cartridges

The **Choose Cartridge** menu offers the approved Demo Cart, original Colour
Test and **Load Your Own ROM…**. The latest approved Demo Cart starts by default.
Explicit selections always outrank older downloads, hashes and file reads.
Selecting the file picker cancels an outstanding load even if dismissed.

Choices are remembered only in this tab's session. A built-in can start again
after refresh; local ROM contents are never uploaded or stored. Selecting local
loading leaves the console waiting for a file after refresh. Rejected images
leave the accepted cartridge, faults and checkpoint untouched unless native
activation has already begun; that case uses the existing uncertain-activation
message and Clean Restart recovery. Loading an accepted new cartridge discards
the prior checkpoint, as before. Audio remains gesture-enabled; region changes
still take effect when a cartridge starts or on Clean Restart.

## One Approval Record

[`site/cartridges.json`](../site/cartridges.json) is the only current version,
display name, path, source/build method, byte length, SHA-256 and licensing
authority. `defaultCartridge` identifies the approved Demo Cart. Entries must
be explicitly approved; unfinished experiments are not selected by scanning
directories, branch names, tags or version numbers. Historical assets remain
listed separately for exact preservation. The browser version in `VERSION`
does not change when a cartridge changes.

Both current built-ins are original project homebrew. The Colour Test source
reproduces the existing blog download byte for byte and contains original
program instructions and tile graphics, with no commercial game/SDK data.
Owner approval authorizes its inclusion. Preserve the factual
[cartridge notices](../demo-cart/CARTRIDGE-NOTICES.md) and original README;
no third-party or blanket SPDX licence is inferred. Emulator licences and
corresponding-source requirements continue to apply independently.

## Build and Package

```sh
python3 scripts/build-demo-cart.py
python3 scripts/cartridges.py verify-site
python3 scripts/package-review.py --output /workspace/VRAMpage-MD-review.zip
python3 scripts/cartridges.py stage-site /workspace/VRAMpage-MD-static
```

The compatibility-named build command generates **all** approved built-ins from
their manifest sources using Python 3. No network or assembler is needed.
New generated ROM binaries remain ignored by Git. The Demo Cart v0.1 binary,
source kit, captain portrait and logo stay unchanged.

ZIP and static staging require every approved cartridge with exact size/hash,
and reject unknown/altered ROMs. They include matching cartridge source and
notices. Keep relative paths intact for static subdirectory hosting. Run through
HTTP(S), including an offline loopback server; `file://` launching is unsupported.
The browser verifies each built-in before activation, with a tested SHA-256
fallback on HTTP hosts that lack Web Crypto. Checksums establish correspondence
to the shipped manifest, not protection against an attacker replacing the
whole application and manifest together. Local user ROMs use the existing
format/header validation and are not restricted to the built-in allowlist.

## Approving a New Demo Cart

1. Obtain explicit owner approval for the intended source and artwork. Preserve
   all prior published assets and the original v0.1 source kit.
2. Reproduce the candidate from source and verify actual Genesis Plus GX
   execution under NTSC/PAL, its controller behavior and recovery. Record
   source-specific evidence before declaring the new output approved.
3. Update the Demo Cart entry in the manifest with its version, source/build
   output, size, digest and applicable licence/notice. Keep its stable `demo`
   identity and default. No app/workflow/package version constants need edits.
4. Run source checks, generic manifest-driven actual-WASM tests, retained
   version-specific regressions, browser races/rejections and extracted complete
   ZIP/static checks. Never weaken an assertion to accommodate a new image.
5. Require independent review, every protected-main check and CodeQL before
   merge; verify main CI. Every subsequent release then selects the approved
   manifest default automatically.

The manifest policy does not authorize publication, modifying existing public
downloads, bumping `VERSION` or deploying McRetro.net. Those require separate
explicit approval.
