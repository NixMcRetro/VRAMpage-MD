# Development work queue

Read with [development status](DEVELOPMENT-STATUS.md), [roadmap](../ROADMAP.md)
and [versioning](VERSIONING.md). Status describes evidence, not promised effects.

| Priority | Work | Dependencies and acceptance | Assignment | Status |
|---|---|---|---|---|
| Done | Verify corrected v0.2.4 distribution | Public checksum, exact tag/source/version, JS/WASM, source/notices, executable launcher and actual-core local launch | Basic packaging worker, coordinator | Fresh public download, checksum, package and unmocked launcher/core verification passed |
| Done | Deliver v0.2.6 experiment build identification | Nonblocking metadata, explicit unavailable fallback, unchanged fault models, package identity, three-browser CI, specialist review and public ZIP | Basic implementation/packaging workers; Luna High independent review | PR #20 merged as 6d18f8e after all required CI passed; release workflow 39767990645 passed; fresh public ZIP checksum, exact source/tag, unmocked launcher and actual-core export verified |
| Done | Compact Work RAM diagram and publish v0.2.8 | Smaller laptop viewports, accessible pin targets, unchanged core, three-browser CI, exact release provenance and extracted launcher/core checks | Basic UI worker, independent review and coordinator | PRs #37/#38 merged; main CI39971912690 and release39972454348 passed; public download verified |
| Done | Keep superseded legacy release deleted | Preserve existing source tag and historical evidence; do not restore release entry or assets | Coordinator | User explicitly reaffirmed deletion; no restoration attempted |
| Done | Read-only internal demo/player observer | Source-verified byte lanes/fields, exact ROM/core profiles, repeatable baseline/negative/one-write trials, scalar/hash output and independent specialist review | Luna High implementation and independent Luna High review; coordinator evidence/docs | Protocols 1/2 recorded separately; six trials each repeat exactly; baseline/demo continuation observed; monitored A10/A11 trajectory is one tick delayed |
| Done | Identify the first affected generic RAM write | Inspect/reuse existing hooks; passive address/width/frame diagnostics only if needed; preserve no-fault behaviour, access counts and exact pulse budgets; strict/sanitizer/WASM tests and independent review | Luna High investigation/implementation and independent specialist review | Local verification passed: metadata trace identifies byte $FFF62A to $F22A at tick1801; six traced/untraced trials preserve historical observations. Source and independent six-trial evidence review approved; PR #23 merged as 6c7469f after all PR checks passed |
| Done | Publish and verify v0.2.7 Mac package | Passing fixed main CI, source/tag/version/checksum, source/notices, launcher and extracted actual-core checks | Coordinator after default-worker package/docs preparation | Public release from 1d87fd9; workflow39863608264 passed, 319-entry ZIP and real metadata/core smoke verified |
| Done | Bound the VBlank-flag to sound-track alias investigation | Corrected source layout; distinguish VBlank flag set/clear candidates and compare named state, generated sound and phase-aligned player/demo state under the same one-write pulse, no new audio model | Luna High investigation and independent review | Eight fresh-core trials and independent specialist review passed; player/demo lag -1 repeats, no audio hash matches at offsets -2 through +2; exact store and causality remain unproven; see RAM-ALIAS-AUDIO-PHASE.md |
| Done | Identify the executed VBlank store | Bounded generic instruction/write-value metadata if required; same pulse, no game-variable edits, no-fault equivalence and independent review | Luna High implementation and independent review | Separate diagnostic captured repeated zero-write at instruction PC $B46, byte FFF62A to F22A; nine actual-WASM synthetic CPU groups and all eight fresh-core trial gates passed; production API and public v0.2.7 unchanged |
| Done | Verify the delayed wait/release sequence | Identified zero-write; bounded read-only instruction/flag progression, exact public-core equivalence, no game-variable edits or recovery, independent review | Luna High experiment design and independent review | Verified: matched Rev00 source build, tick1801 failed clear and continued poll, tick1802 normal clear/return/caller/setup; all nine-core experiment gates pass, public-core equivalence and independent specialist review; see VBLANK-WAIT-SEQUENCE.md |
| Done | Evaluate one A12/A13 object-memory alias | Matched source, predefined one-write budget and trajectory threshold, fresh-core repeat/equivalence, independent review | Luna High implementation and independent review | Valid negative: D022 status-byte write aliases C022, demo continues, all 596 monitored frame/demo/player pairs match baseline; see RAM-GAMEPLAY-CANDIDATE.md |
| Done | Establish bounded attract-mode gameplay divergence | Previous item; source-backed scene/playback observation, equivalent reset/input, phase alignment and player-state or private visual evidence, repeated bounded candidate and no silent recovery | Luna High experiment design; basic runner/documentation support | Verified for the pinned ROM/public v0.2.7 core: A12/A13 eight-write pulse, all 596 demo tuples match at phase 0 while position differs by at least one pixel for 594 ticks, longest run 432; six-core independent rerun byte-identical. See RAM-STATUS-FOLLOWUP.md. Physical/native Mac fidelity remains unclaimed |
| Done | Plan transaction-level VRAM integration | Bounded RAM criterion verified; map VDP access paths, multiplexed addressing and cache/timing/recovery acceptance before implementation | Luna High architecture and independent review | Source-backed architecture and test gates recorded in TRANSACTION-VRAM-PLAN.md; developer-only access implementation is recorded below |
| Done | Resolve transaction-model semantics | Reviewed architecture/test plan; decide supported modes, byte lanes, cache alias dependencies, SAT policy, API/counters and legacy compatibility before runtime edits | Luna High design and independent review | Reviewed protocol in TRANSACTION-VRAM-SEMANTICS.md; developer-only access hooks follow this protocol |
| Done | Isolated native transaction helper | Reviewed semantics; exhaustive mapping, byte/word lanes, aliases, bounded cache dependencies, atomic settings and strict/sanitizer tests | Luna High implementation and independent review | Native byte/dependency primitives and focused strict/sanitizer tests passed independent review; no emulator or public API integration at that stage |
| Done | Integrate VDP port and DMA accessors | Reviewed semantics and native helper; exact pinned patch anchors, idempotence/source-drift checks, no-fault equivalence and actual synthetic-WASM CPU/Z80/DMA coverage before renderer migration | Luna High implementation and independent review | Developer-only hooks and actual-WASM synthetic checks passed independent review; see VRAM-ACCESS-DIAGNOSTIC.md. Renderer and public model selection remain gated |
| Done (implementation) | Integrate diagnostic renderer and cache reads | Reviewed Mode 5/interlace/alternate routing, literal pixels, name/scroll/SAT fields, alias recovery, whole-state equivalence and fixed performance gate | Luna High implementation and independent review | 91 full local tests, fresh four-core WASM and actual-core Chromium pass. The first failed measurement is preserved; the reviewed guard correction passes the unchanged complete five-pair gate and independent audit. [PR #40](https://github.com/NixMcRetro/VRAMpage-MD/pull/40) records required CI and integration; public milestone remains below |
| Done (implementation) | Safe public VRAM model API groundwork | Separate optional runtime from diagnostic bridges; atomic model selection, JS/C type validation, scalar state and last-frame counts, legacy compatibility, runtime export inspection and real-WASM profile tests | Luna High implementation and independent Luna High review; coordinator docs/integration | Safe JS/C validation, read-only model/support metadata and completed-frame counts implemented in a harness-built runtime profile. Independent review, 91 full tests with normal leak checking, five-profile WASM, normal Chromium and real packaging pass locally; PR #41 merged as 46dcc80 after all required checks passed and main CI40041499264 passed. Normal app/release remains v0.2.8 and frame-scoped |
| Done (implementation) | Reproducible optional runtime build | Keep normal output unchanged; isolate runtime artifacts and flags; actual production-builder checks, corresponding source, negative inputs and independent review | Luna High implementation and independent review; coordinator integration/docs | [Build verification](VRAM-RUNTIME-BUILD.md): 94 full local tests, actual builder switching, independent source rebuild/API review and normal Chromium pass; PR #42 merged as d074bdf with all PR and main CI40043483063 checks passing. No application controls, release or version change in this stage |
| Done | Usable browser transaction controls and exports | Reuse merged runtime; ship actual core, frame fallback, safe RAM/VRAM handoff, legs/bridges, separate metadata/counts, actual browser tests and independent review | Luna High implementation and review; coordinator integration | Delivered in PR #43, merged4cfb983; all seven PR/main CI checks pass, including packaged Firefox/WebKit. Fixed runtime performance gate passes independent audit. Public v0.3.0 package verified. |
| Done | Public transaction-level VRAM milestone | Approved semantics and bounded architecture/test plan; VDP read/write/cache/timing coverage, normal-output regression, independent specialist review | Luna High | v0.3.0 publication40063210310 passes; public tag/source/version/checksum, 626-file complete ZIP, downloaded real core/browser and launcher checks pass. Earlier artifacts unchanged. |
| Done B | Hardware-informed audio bending | PSG/FM delivered; complete milestone package/CI gates for verified Z80 paths, preserve clean audio, native/WASM/browser tests and independent review before v0.4.0 | Luna High implementation and independent review | PSG/FM and acceptance PRs #44/#45/#46 merged; all PR/main CI and publication40069946647 pass. Public v0.4.0 ZIP provenance, checksum, launcher and downloaded actual-core tests verified |
| Done B1 | FM input-data bridge | Shared YM2612/YM3438 write boundary, port/cycle/busy preservation, atomic settings, exact counters, UI/export/reset, no-fault equivalence and focused actual-WASM tests | Luna High author; independent Luna High reviewer | Implemented and independently reviewed through 204e611; matched-backend WASM and actual Chromium pass; 107-test full local suite, fresh WASM and Chromium pass; post-reset mailbox proof reviewed; PR #45 merged2cb6e85 after all seven CI checks passed |
| Done B2 | Actual Z80-to-PSG route | Original bootstrap under BUSREQ/RESET, no 68K PSG writes, normal/off equal, active mapping/tone change, reset baseline, independent review | Luna High test author; FM author independent review | Implemented with encoded bootstrap-store validation; independent review and actual FM-enabled runtime pass: exactly three Z80 writes, two changed bytes; included with FM integration |

| Done B3 | Complete audio acceptance | Actual Z80-to-FM and simultaneous FM/PSG traffic; repeated-active determinism, bounded queue/pause behavior and concise audio model overview | Luna High implementation/review; coordinator docs | Implemented and independently reviewed; both FM backend mixed/deterministic tests and Chromium scheduling pass locally; all seven PR/main checks, complete public package and downloaded-core verification passed |
| Active C | Essential workbench configurations | Versioned save/restore settings with validation, reproducible presets, combined recovery and useful experiment comparison; preserve existing defaults | Luna High architecture/implementation and independent review; basic UI/docs support | Configuration save/preview/apply implemented, including exception-safe pause, unknown-state reporting and normalized pair comparisons. Independent review, full 107-test native/SDK suite, 40 browser logic cases and four actual-core cases pass. GitHub CI is required before merge. Do not add Z80 RAM faults or speculative features first |

Configuration slice verified: PR #47 merged `ccc80e12`; PR CI40083076183 and
main CI40083371467 pass all seven checks. Do not rebuild this completed feature.

## Current user priority: compact chip workbench

Show VRAM, Work RAM, FM and PSG together in the existing sidebar as compact
conceptual chip diagrams. Connections stay within each individual chip, as
explicitly confirmed by the user. Keep signal labels inside bodies, short legs,
keyboard access, visible selected/connected states and crosses for grounded
signals. Target all four diagrams in an ordinary 1366 by 768 browser viewport.
Retain advanced controls and existing presets rather than duplicating state.

The native PSG/FM models currently bridge pairs only. Add runtime-only 8-bit
stuck-low masks at their existing write-input boundaries, mutually exclusive
with each chip's pair. Preserve timestamps, synthesis, exact counters, reset
semantics, normal binary output and legacy pair APIs. Missing mask APIs disable
only audio cut mode. No Z80 fault model, Work RAM data-cut model, physical pinout
claim or cross-chip wiring is included.

Implemented with Luna High core author and independent UI/configuration author in
isolated worktrees, with reciprocal specialist review. Acceptance includes
native/sanitizer and actual-WASM mask/bridge/reset tests, real browser control
and viewport tests, chip-local selection isolation, truthful legacy fallback,
experiment metadata and configuration-file migration without rewriting v1 files
or recorded experiments. Keep the existing public v0.4.0 artifact unchanged.

Configuration save/preview/apply is already complete in PR #47. Do not rebuild
it; extend its strict format only as needed for audio masks, retaining v1 import.
Local verification passes: 107 native/SDK tests, 45 browser logic cases, four
actual-core cases, three transaction cases and six display cases. Both source
reviews approve. Required GitHub checks and same-commit package verification
remain the delivery gate. PR #48 is now merged as `e579c57` after all seven
PR checks passed in run40088693320. Verify main CI40089045294, then publish and
freshly verify v0.4.1 from that exact source before starting new work. The
continuation branch `experiment/chip-workbench-delivery-checkpoint` records
post-merge evidence; bundle it with the next implementation.

After this user priority, resume coordinated fault-disconnect/recovery using
existing setters and pulse protections, then experiment comparison.

## Feature-first continuation

A: complete usable transaction VRAM, current-runtime performance and v0.3.0
acceptance. B: hardware-informed YM2612/PSG/Z80 audio, then v0.4.0 acceptance.
C: essential configurations/presets, coordinated faults, recovery and experiment
comparison. D: feature freeze, comprehensive bug fixing, compatibility,
performance and usability refinement. Fundamental correctness remains mandatory
during every phase; full verification belongs at integration boundaries.
No minor cosmetic/documentation releases or repeated completed research.

## Continuation procedure

1. Fetch main and open PR/release/CI state; read the linked status and AGENTS.md.
2. Finish any pending P0 verification/publication before new emulator changes.
3. Select the highest-priority unblocked implementation item. Inspect existing experiment runners before
   adding instrumentation. Use a bounded Luna High assignment and independent
   review for changes to emulator internals.
4. If no private legal cartridge is available, prepare ROM-free diagnostic tests
   and record the precise remaining actual-game blocker. Never download a
   commercial ROM or claim synthetic tests satisfy the attract-mode milestone.
5. Record exact tested commits, evidence and limitations. Preserve earlier results.
