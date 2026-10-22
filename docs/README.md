# VRAMpage MD documentation

VRAMpage MD is a browser-based NTSC Mega Drive/Genesis experiment. It runs a locally selected cartridge through a modified Genesis Plus GX core and explores hardware-*informed* circuit faults. The current VRAM model is **frame-scoped**, not electrically or cycle-accurate.

## Start here

| Document | Purpose |
| --- | --- |
| [Changelog](../CHANGELOG.md) | Versioned changes and verification limits |
| [Run locally](RUNNING-LOCALLY.md) | Start a ready-built review bundle without building WebAssembly |
| [Project overview](../README.md) | Current features, limitations, building and repository policy |
| [Product roadmap](../ROADMAP.md) | Versions and video, logic and sound milestones |
| [Documentation roadmap](DOCUMENTATION-ROADMAP.md) | Which Markdown documents to write, in what order, and acceptance criteria |
| [Testing guide](TESTING.md) | Automated and manual test matrix, commands and release gates |
| [Video output](VIDEO-OUTPUT.md) | 640-pixel source stride, native pixels, missing-line recovery and raw output |
| [Logic bending](LOGIC-BENDING.md) | v0.2 work-RAM model, runtime scope and known limits |
| [Byte transactions](WORK-RAM-BYTES.md) | Standalone byte-lane rules and regression coverage |
| [Experiments](EXPERIMENTS.md) | Repeatable zero-fault and RAM-fault attract-mode procedure |
| [Build and deployment](DEPLOYMENT.md) | Manual publishing to McRetro.net, never direct from feature work |
| [Source import](IMPORTING.md) | How the original v0.1 working prototype entered GitHub |
| [Prototype notes](PROTOTYPE-V0.1-NOTES.md) | Historical first-stage implementation and technical assumptions |

## Documentation conventions

- **Describe what works today separately from what is planned.** Mark features as Implemented, Experimental, Planned or Unverified. Label the v0.2 work-RAM model Experimental until genuine-game checks are recorded; do not imply a verified Sonic outcome or sound bending.
- Record the tested build/ref, hardware revision, game region and display mode where relevant. An NTSC target does not make every game or clone board identical.
- Separate physical facts (with a source), emulator behaviour (with a code location), and digital approximations (with an explicit assumption).
- Keep instructions executable from the **repository root**; where a user must start elsewhere, give the full `cd` command.
- Never add ROM images, game-derived screenshots or secret credentials to the repository. Test games must be original, redistributable homebrew with recorded licensing and provenance.
- Keep screenshots optional for comprehension; provide alt text, keyboard instructions and Markdown descriptions.
- Update the appropriate docs and regression tests in the same pull request as a behaviour change.

## Maintainer release rule

VRAMpage-MD development does not automatically publish to `mcretro.net`. Deploy only a reviewed, approved static build to `/homepages/vrampage/` through a **separate branch** of the website repository. That merge triggers a full Jekyll/Pagefind rebuild.
