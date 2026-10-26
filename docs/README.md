# VRAMpage MD documentation

VRAMpage MD is a browser-based NTSC Mega Drive/Genesis experiment. It runs a locally selected cartridge through a modified Genesis Plus GX core and explores hardware-*informed* circuit faults. The browser offers **frame projection** and **logical-byte transaction** VRAM models. Neither establishes electrical or cycle accuracy.

## Start here

VRAMpage MD runs in modern browsers on **Windows, macOS and Linux**. Start with
[the browser package and launch guide](RUNNING-LOCALLY.md), or read the
[v0.5.0 release notes](RELEASE-NOTES-v0.5.0.md). [Download VRAMpage-MD-v0.5.0-browser.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip) · [SHA256SUMS.txt](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt).

The historical **[v0.4.1 complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip)**
remains unchanged. Python 3 is needed only to run a local server; a hosted browser
build has no Python or macOS requirement. The Work RAM controls are implemented
and experimental; older standalone-model descriptions are historical records.


| Document | Purpose |
| --- | --- |
| [Release history](RELEASE-HISTORY.md) | Canonical historical versions and current runnable downloads |
| [Release presentation](RELEASE-CURATION.md) | Manage release titles and notes without changing tags or binaries |
| [Changelog](../CHANGELOG.md) | Versioned changes and verification limits |
| [Versioning](VERSIONING.md) | Current source version and historical identifier mapping |
| [Run locally](RUNNING-LOCALLY.md) | Windows, macOS and Linux browser-package launch instructions |
| [v0.5.0 release notes](RELEASE-NOTES-v0.5.0.md) | Release changes, distribution and verification limits |
| [Project overview](../README.md) | Current features, limitations, building and repository policy |
| [Session checkpoints](SESSION-CHECKPOINT-API.md) | Explicit session-only checkpoint semantics, supported profiles and validation gates |
| [Product roadmap](../ROADMAP.md) | Versions and video, logic and sound milestones |
| [Documentation roadmap](DOCUMENTATION-ROADMAP.md) | Which Markdown documents to write, in what order, and acceptance criteria |
| [Testing guide](TESTING.md) | Automated and manual test matrix, commands and release gates |
| [Video output](VIDEO-OUTPUT.md) | 640-pixel source stride, native pixels, missing-line recovery and raw output |
| [Logic bending](LOGIC-BENDING.md) | v0.2 work-RAM model, runtime scope and known limits |
| [Byte transactions](WORK-RAM-BYTES.md) | Standalone byte-lane rules and regression coverage |
| [Renderer diagnostic](VRAM-RENDER-DIAGNOSTIC.md) | Mode 5 read inventory, visible/cache acceptance and performance gates |
| [VDP access diagnostic](VRAM-ACCESS-DIAGNOSTIC.md) | Developer-only CPU/Z80/DMA hooks, actual-WASM checks and remaining renderer gates |
| [VRAM transaction semantics](TRANSACTION-VRAM-SEMANTICS.md) | Selected byte, cache, sprite-table, model/API and recovery rules for staged integration |
| [Transaction-level VRAM plan](TRANSACTION-VRAM-PLAN.md) | Pinned access-path inventory, compatibility decisions, staged test gates and current progress |
| [VRAM leg switches](VRAM-LEG-SWITCHES.md) | v0.2.6 AD0-AD7 toggles, crosses and bridge selection |
| [Address-line chip](ADDRESS-LINE-CHIP.md) | v0.2.6 crossed-wire controls, stuck-low assumptions and logical bus mapping |
| [Affected-write pulses](ACCESS-LIMITED-PULSES.md) | v0.2.3 transaction cutoffs, longword fix and corrected-core comparisons |
| [Pulse survey](PULSE-EXPERIMENTS.md) | Repeated actual-core survey of all adjacent address write pairs |
| [RAM pulses](RAM-PULSES.md) | Short contacts, quick address write pairs, frame timing and cancellation |
| [Native Checkpoint Replay Proof](CHECKPOINT-REPLAY-PROOF.md) | Developer-only capacity, audio continuity and synthetic replay evidence |
| [v0.5.0 recovery/checkpoint plan](RECOVERY-CHECKPOINT-PLAN.md) | Ordered recovery, one-session checkpoint and acceptance gates |
| [CPU recovery](CPU-RECOVERY.md) | v0.2.1 force-resume/reset semantics, metadata and limits |
| [Experiments](EXPERIMENTS.md) | Read-only saved-export comparison and repeatable zero-fault/RAM-fault procedure |
| [Build and deployment](DEPLOYMENT.md) | Versioned local downloads and separately authorised website deployment |
| [Source import](IMPORTING.md) | How the original v0.1 working prototype entered GitHub |
| [Prototype notes](PROTOTYPE-V0.1-NOTES.md) | Historical first-stage implementation and technical assumptions |

The v0.4.1 workbench extends optional, independent
[PSG input-data](PSG-INPUT-DATA-SEMANTICS.md) and
[FM write-input](FM-DATA-BRIDGE.md) bridges. Previous releases remain unchanged.

- [Audio bending](AUDIO-BENDING.md): signal paths, bus ownership, controls, recovery, browser scheduling and evidence limits.

- [Circuit configuration files](CIRCUIT-CONFIGURATIONS.md): development save/preview/apply format, capability checks and failure semantics.

- [Compact chip workbench](CHIP-WORKBENCH.md): chip-local leg controls, audio masks, layout and model limits.

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

## Development coordination

- [Agent instructions](../AGENTS.md): worker selection, review and publishing rules.
- [Work queue](WORK-QUEUE.md): priorities, dependencies and acceptance criteria.
- [Development status](DEVELOPMENT-STATUS.md): verified evidence, limits and continuation.

- [Attract-mode observations](ATTRACT-MODE-OBSERVATIONS.md): read-only demo markers, repeated trials and acceptance limits.

- [First affected RAM write trace](RAM-WRITE-TRACE.md): optional generic diagnostic and bounded private comparison.

v0.2.7 includes an optional, default-disabled metadata-only RAM write trace for developer experiments. See [trace documentation](RAM-WRITE-TRACE.md).

- [VBlank/RAM alias and audio phase protocol](RAM-ALIAS-AUDIO-PHASE.md): read-only developer experiment with corrected source interpretation.

- [VBlank store origin](VBLANK-STORE-ORIGIN.md): isolated diagnostic build, CPU provenance tests and bounded write classification.
- [VBlank wait/release sequence](VBLANK-WAIT-SEQUENCE.md): bounded actual-bus flag and instruction observations following the one-write alias.
- [Object-memory alias candidate](RAM-GAMEPLAY-CANDIDATE.md): predefined phase-aligned gameplay experiment, outcomes and limits.
- [Eight-write status follow-up](RAM-STATUS-FOLLOWUP.md): separately predefined object-memory trial using the same core, timing and success criteria.

- [Safe VRAM model API groundwork](VRAM-PUBLIC-MODEL-API.md): optional runtime and diagnostic export separation, validation and acceptance.

- [Optional runtime core build](VRAM-RUNTIME-BUILD.md): isolated production command, corresponding source, profile switching and remaining application gates.
