# Development work queue

## PR #54 integration checkpoint — 25 October 2026

[PR #54](https://github.com/NixMcRetro/VRAMpage-MD/pull/54) merged as
`841239996c11446ec11a94fe757cd9991f6ca7b4` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40163855382)
passed on `f9ae124e097ad3ee9623183610997259e262a84b`.
The merged tree exactly matches the reviewed head.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40164254321)
pass. No integration blocker remains.

This Phase D slice fixes host audio queues: no buffer allocation while the
browser context cannot run; queued playback stops/disconnects on pause, mute,
visibility and accepted ROM restart; ended/start-error paths release tracking.
Core sound still runs and normal PCM copying, fault models/settings, CPU/chip
state and game-recovery behaviour are unchanged. No smoothing or automatic
rescue was added. Independent Luna High review approves source `23ec56b`.

Full source/SDK107 with normal sanitizers/fresh WASM, Chromium72/72, extracted
compiled-core5/5 and genuine WebKit lifecycle1/1 pass. The 682-file ROM-free
review ZIP matches `f9ae124`, version0.4.1 and UI/runtime bytes. A 1,500-cycle
actual-core mixed run completed in 411.73 seconds without page errors or queue
violations: zero allocations during controlled context suspension, 15 peak
active sources, all 15,767 sources ended and fixed 32 MiB WASM. Post-GC JS heap
measured 2.83–3.29 MiB, including browser/JIT/automation state; this does not
establish universal leak freedom. Raw logs/reports: `/workspace/scratch/stability`.

[Ready-to-run audio-stability review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40164254321/artifacts/12587573637)
contains merged source and matching runtime, separate from public v0.4.1.

Public v0.4.1 tag, metadata and original asset digests were verified unchanged
after merge. McRetro.net was not modified or deployed. Phase D stabilisation
continues; no additional reproducible source blocker remains from this slice.
Next: targeted compatibility/failure/performance and native Mac/audible/OS
background acceptance. These Linux synthetic checks do not establish the latter.
The optional recovery/checkpoint v0.5.0 milestone remains planned only, after
stabilisation. Preserve completed models/evidence; no speculative features,
RAM research, intermediate release or standalone documentation PR is needed.

## Completed Phase D slice: audio lifecycle stability

Resume checkpoint `426c4fc` atop main `2736d59`; preserve all completed feature
and hardware-model evidence. Source `23ec56b` fixes host-side queued audio only:
stop/disconnect old sources at pause, mute, visibility and accepted cartridge
replacement/restart boundaries, release ended nodes, and avoid buffer allocation
while the AudioContext cannot run. Keep calling the core sound path, normal PCM
copying, fault settings, CPU/chip state and manual recovery semantics unchanged.
Independent Luna High review approves this exact source; no source blocker remains.

A genuine-context/compiled-core probe reproduced 120 new queued sources across
120 emulated frames while context time was suspended. The fixed probe creates
zero. The 150-cycle mixed fault/pulse/reset/audio/visibility run reports no stale
queue violations, a peak of four active sources and fixed 32 MiB WASM memory.
The 1,500-cycle run passes after 411.73 seconds: no queue violations/page
errors, zero allocations during suspension, 15 peak active sources, all 15,767
sources ended and constant 32 MiB WASM memory. Post-GC JS heap measured about
2.83–3.29 MiB; this includes warm-up/browser/automation state, not a universal
no-leak proof. Full source/SDK107, Chromium72/72, actual-core5/5 and focused
WebKit audio1/1 pass. Package provenance and PR/main CI are recorded in the checkpoint above;
no audible/native Mac validation is claimed. Scratch evidence: `/workspace/scratch/stability`.

The proposed v0.5.0 auto-resume/checkpoint milestone is deferred until after
stabilisation; no new recovery feature, version bump or public release change is
part of this slice. Preserve v0.4.1 and McRetro.net. A stopped/corrupted game is
still a valid fault outcome; host audio cleanup must not silently rescue it.

## PR #53 integration checkpoint — 25 October 2026

[PR #53](https://github.com/NixMcRetro/VRAMpage-MD/pull/53) merged as
`2736d596435e050f0c779351535a2e40f73d6097` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40159956069)
passed on `5b7afb4bfac4bf5a00b76addce9130d02ca905ec`.
The merged tree exactly matches the reviewed head.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40160355074)
pass. No integration blocker remains.

All ten A11–A15 WRITE pairs now have individual buttons. Each bridge runs for
exactly eight emulated frames without an affected-write cap, then disconnects
without CPU recovery. Advanced selected-limit/forced-resume pulses are unchanged.
Both rows stay visible at 1366×768, including with long status messages. Explicit
cancel/reset/restart/load/replacement cannot clear a later RAM fault.

Independent Luna High review approved `21a80e7` (review `772f749`). Full source/
SDK107, normal sanitizers/fresh WASM, final Chromium72/72, extracted compiled-core
5/5, display6/6, focused WebKit5/5 and independent focused Chromium7/7 pass. The
682-file ROM-free ZIP matches `5b7afb4`, version0.4.1 and its UI/runtime bytes.
Logs, package and acceptance plan: `/workspace/scratch/eight-frame-ram-pairs`.

[Ready-to-run eight-frame review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40160355074/artifacts/12586885523)
contains the merged controls and matching source, separate from public v0.4.1.

Combined configuration/preset/randomisation/pulse/removal/recovery/restart/export/
comparison acceptance is complete. Phase C is accepted; Phase D feature freeze
and stabilisation are active. Reuse valid unchanged native/performance evidence;
fix concrete failures and usability gaps rather than add models or infrastructure.
The public v0.4.1 tag, metadata and original asset digests were verified unchanged
after merge. McRetro.net was not modified or deployed. Native macOS, audible and
physical validation remain unclaimed; faults can stop games or persist in RAM.
Bundle this checkpoint with the next concrete stabilisation change; no standalone
documentation PR or intermediate release is needed.

## Source checkpoint: eight-frame pairs and combined acceptance

Implementation `2465987` and layout fix `ddaebad` replace the random RAM shortcut
with all ten individual A11–A15 WRITE pairs. Each runs for eight emulated frames
without an affected-write cap, then disconnects without CPU recovery. Independent
Luna High review approved cancellation/keyboard acceptance fix `21a80e7`
(cherry-picked from `772f749`). No source review blocker remains.

Focused tests cover all ten pairs (160 affected writes each, zero reads, exactly
eight frames and no CPU intervention), keyboard/no-write/paused timing, active
and malformed-state refusal, failed setters/releases, all cancellation paths,
legacy optional APIs and actual normal/runtime cores. Full source/SDK107 with
normal sanitizers and fresh WASM, display6/6 and focused WebKit5/5 pass. The
independent final focused Chromium7/7 run passes. Final full interfaces and package provenance pass; PR/main CI evidence is
recorded in the integration checkpoint above. Logs and the plan
are under `/workspace/scratch/eight-frame-ram-pairs`.

The combined workbench flow passes: save/preview/apply, presets, independent chip
randomisation, pulse save/apply guards, explicit CPU-only reset preserving audio,
running/paused all-domain removal, experiment/configuration exports, read-only
comparison and clean restart. Existing individual-domain negative and actual-core
evidence is reused. Phase C automated acceptance is complete in source.

## Active Phase D: feature freeze and stabilisation

Freeze the implemented feature set. Continue compatibility, crash/failure safety,
audio/visibility scheduling, performance and usability checks; fix concrete gaps
rather than add models or infrastructure. Current CI repeats all three browser
interfaces and extracted Firefox/WebKit packages. Reuse existing native and
performance evidence when source is unchanged. Native macOS Firefox, audible
output and physical validation remain explicitly unverified, not integration
claims. Preserve public v0.4.1, historical evidence and McRetro.net. No speculative
Z80 RAM faults, intermediate public release or documentation-only PR is needed.

## PR #52 integration checkpoint — 25 October 2026

[PR #52](https://github.com/NixMcRetro/VRAMpage-MD/pull/52) merged as
`b4424e0d6a68ed12a36b8dc8fff70a502ca16a02` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40153718149)
passed on `a1a142eb612fee260c9adc3479079f279549c933`.
The merged tree exactly matches the reviewed head.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40154014908)
pass. No integration blocker remains.

CPU reset now sits beside Randomiser. The separate Work RAM WRITE pulse chooses
a distinct A11–A15 pair, stops after eight affected writes or one emulated frame,
and disconnects without CPU recovery. Active or unknown memory/held/pulse state
is refused before mutation. Existing advanced forced-resume pulses are unchanged.
Successful Disconnect all preserves the prior running/paused state; partial or
unverified outcomes pause before another tick. Held player input is preserved.
Independent Luna High review approved source `72f67ad`, including malformed-state
hardening `53c710b` and normal-core legacy-getter acceptance.

Local verification passes: full source/native/SDK107 with normal sanitizers and
fresh WASM profiles; final Chromium71/71; WebKit focused7/7; display6/6; extracted
compiled-core5/5. The 682-file review ZIP matches `a1a142e`, version0.4.1 and the
built assets. Initial sandbox restrictions and stale test expectations were
corrected without weakening assertions; logs remain under
`/workspace/scratch/workbench-ram-pulse`. Native/core model code is unchanged.

[Ready-to-run review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40154014908/artifacts/12584305775)
contains the merged controls and matching source, separately from the public release.

The public v0.4.1 tag, release metadata and original asset digests are unchanged.
McRetro.net was not modified or deployed. No native macOS, audible or physical
evidence is claimed. A pulse can still stop a game; recovery remains explicit.
Next: combined configuration/randomisation/removal/recovery/
comparison acceptance, then Phase D feature freeze. Preserve the completed
models, existing release and evidence; do not reopen RAM research or publish an
intermediate release. Bundle this checkpoint with the next implementation task;
no documentation-only PR is needed.

## Completed user priority: compact CPU reset, RAM burst and running disconnect

Reuse PR #51's verified workbench and checkpoint `ffb330f`. Add **CPU reset**
next to the Randomiser buttons using the existing memory-clearing/audio-preserving
CPU-only recovery. Add a separate random **write-only A11–A15 joined pair**,
limited to eight affected writes with a one-frame maximum. It clears without
CPU recovery. Refuse existing memory faults/pulses/held contacts rather than
overwriting them; preserve audio, staged files, pause state and existing advanced
pulse behavior. Record the chosen pair, limits and explicit no-recovery outcome
in the existing pulse history. No new native model or claim of lockup-free use.

Remove the upfront pause from **Disconnect all faults**. A confirmed complete
clear preserves prior play/pause; unsafe partial, failed or unknown state pauses
before another tick. Keep callback cancellation, successful clears, per-domain
outcomes and no automatic CPU intervention. Test original advanced pulses and
recovery alongside these changes, not just new controls. Preserve the compact
viewport, optional legacy APIs, v0.4.1 release and McRetro.net boundary. Independent
review, full applicable regression, actual-core checks and PR/main CI remain gates.

Implementation `c0e79a0`, hardening `2dbd1f4`, review fixes `53c710b` and
normal-core acceptance `72f67ad` are complete. Independent Luna High review
approves the final source. The full source/SDK107 suite and normal sanitizers
pass, as do display6/6, focused WebKit7/7 and independent actual-core running/
paused and normal-fallback pulse cases. Review tightened malformed VRAM-state
refusal before any mutation. Final browser and PR/main results are recorded in the checkpoint above; no
public release or external-site changes are authorised.

## PR #51 integration checkpoint — 25 October 2026

[PR #51](https://github.com/NixMcRetro/VRAMpage-MD/pull/51) merged as
`53d8de70e37fe67301a4b3841b49b45a57adffe0` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40111996963)
passed on `63856ab494c8055320c95559adfcfb4e0cf77173`.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40112535488)
pass; the merged tree exactly matches the reviewed head. Independent Luna High
review approved source `2cc4914`.

**Randomiser — PSG · FM · VRAM** is complete in source. Each button chooses
cuts or a joined pair only within its selected chip, preserving the other chip
settings and Work RAM. VRAM retains its model and refuses active RAM/pulse/held
handoffs. Failure status distinguishes unchanged, observed partial and unknown
state. Existing configuration/experiment formats capture the selected settings.
Native/core code is unchanged. Local verification: native/SDK107 and source
script, final Chromium66/66, focused WebKit5/5, actual-core5/5, transaction3/3,
display6/6 and an exact-source 682-entry review ZIP. Final CI repeats full
interfaces in all three browsers and tests the extracted runtime in Firefox/WebKit.

[Ready-to-run review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40112535488/artifacts/12567700494)
contains the merged source changes. This is separate from the public v0.4.1
release: its original tag, metadata and asset digests remain unchanged.
McRetro.net was not modified or deployed. No integration blocker remains.
Next: combined configuration/randomisation/removal/recovery/comparison acceptance,
then Phase D feature freeze. Bundle this checkpoint with that task; no
intermediate public release or documentation-only PR. Reuse environment notes
and evidence in `/workspace/scratch/VRAMPAGE-ENVIRONMENT.md` and
`/workspace/scratch/randomise`. No native macOS, audible or physical evidence
is claimed.


## Completed user priority: chip-local Randomiser

Add a compact **Randomiser** label followed by **PSG**, **FM**, **VRAM** buttons,
as explicitly requested. Each button selects cuts or a distinct joined pair
within its own chip using the existing models. Preserve the other chips, Work
RAM, selected VRAM model, staged configuration and ordinary play/pause state.
Do not add cross-chip links, another fault model, intensity controls or a new
export format. Existing configurations/exports must capture the chosen state.

Acceptance: deterministic tests cover both modes, valid endpoints/nonzero masks,
chip isolation, RAM/pulse/held-contact guards, bridge-only and unavailable APIs,
rejected/trapped setters, truthful state, configuration/export round trips,
keyboard operation and the compact viewport. Reuse unchanged native/core
evidence and run applicable full regression and actual-core checks. Independent
specialist review and passing PR/main CI remain required. Preserve v0.4.1 and
McRetro.net; return to combined workbench acceptance after this requested slice.

Implemented `5be6d9e`, independently reviewed/fixed `2cc4914`. The full native/SDK107
and source script pass. Final Chromium66/66, WebKit focused5/5, compiled-core5/5,
transaction3/3 and display6/6 pass. All seven PR and main checks passed; see the final integration checkpoint above.
Keep the corrected deterministic selection test and held-key restoration test;
do not weaken assertions to accommodate unforced random outcomes.

## PR #50 integration checkpoint — 25 October 2026

[PR #50](https://github.com/NixMcRetro/VRAMpage-MD/pull/50) merged as
`f59f2122a277cca7b12300863e893d42520412f1` after all seven
[final PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40108624863)
passed on `7fb89d76c02f16c25a86e358fcd3196c4f7a7ad9`.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40109011904)
pass. The merged tree exactly matches the reviewed head. Independent Luna High
review approved comparison `64ae7a3` and keyboard fix `2d29d0a`.

Saved-export comparison is complete in source: bounded local imports, explicit
unknown metadata, recorded settings/results, text-only rendering, canceled-read
protection and keyboard scrolling without game hotkeys. Schema versions remain
unchanged with additive `logic.available` metadata. Local evidence: native/SDK107,
Chromium60 before the final keyboard fix, final comparison3/3 in Chromium and
WebKit, display6/6, actual-core4/4 and transaction3/3. Final CI runs the complete
61-case interfaces in all three browsers and extracted Firefox/WebKit packages.
The 683-entry local review package matches source `7fb89d7` and its manifests.
The public v0.4.1 release, original tag and asset digests remain unchanged;
McRetro.net was not modified or deployed. No integration blocker remains.

Next bounded task: combined workbench acceptance using existing configuration,
fault-removal, recovery and comparison flows, then Phase D feature freeze.
Do not rebuild completed models or publish an intermediate release. Bundle this
checkpoint with that task rather than opening a documentation-only PR.
Environment and evidence: `/workspace/scratch/VRAMPAGE-ENVIRONMENT.md` and
`/workspace/scratch/comparison`; reuse the SDK, core and browser caches.
No new native macOS, audible, physical-gamepad or electrical evidence is claimed.


## PR #49 integration checkpoint — 25 October 2026

[PR #49](https://github.com/NixMcRetro/VRAMpage-MD/pull/49) merged as
`1bb92a5d6055f78b8d002c45f6d3b9102adac5c7` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40094544657)
passed on reviewed head `a6a3f34a3cb69dde813d04ec711b346f01386236`.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40104216774)
passed, including source, three-browser interfaces, compiled-core/package and
packaged Firefox/WebKit. The merge tree exactly matches the reviewed head.
The original v0.4.1 release metadata, tag and asset digests remain unchanged;
McRetro.net was not modified or deployed. No integration blocker remains.
Next bounded task: experiment comparison. Preserve this checkpoint with the
next implementation rather than opening a documentation-only PR.
Shell Git fetch was unavailable because the executor proxy could not connect;
latest remote main/PR/CI were fetched through the connected GitHub API.
No additional local/native Mac, audible or physical checks were run.


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
| Done C | Combined workbench acceptance | Versioned save/restore settings with validation, reproducible presets, combined recovery and useful experiment comparison; preserve existing defaults | Luna High architecture/implementation and independent review; basic UI/docs support | Essential flows and the new eight-frame controls pass combined source acceptance; feature freeze is active. Preserve the implemented models and release; do not add Z80 RAM faults or speculative features |
| Active D | Feature freeze and stabilisation | Accepted essential flows; full browser/audio/visibility, failure safety, usability and existing performance/package gates before a meaningful release | Coordinator; bounded basic checks and Luna High review for risky fixes | Freeze features; fix concrete regressions only. Current automated gates continue; native macOS, audible and physical validation remain unclaimed. Preserve v0.4.1 and McRetro.net |

Configuration slice verified: PR #47 merged `ccc80e12`; PR CI40083076183 and
main CI40083371467 pass all seven checks. Do not rebuild this completed feature.

## Completed user priority: compact chip workbench

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
passed. PR #48 is merged as `e579c57`; PR40088693320 and main40089045294
pass all seven checks. Publication40089373232 passes all four jobs. Fresh public
v0.4.1 ZIP provenance, SHA-256, 681-entry source/notices, launcher, downloaded
API/audio and extracted actual-core4/4 plus transaction3/3 checks pass. The
continuation branch `experiment/chip-workbench-delivery-checkpoint` records
post-merge evidence; bundle it with the next implementation. No delivery blocker.
Reuse cached Chromium, WebKit and SDK; see the environment notes linked in status.

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

## Completed bounded task: coordinated removal and recovery

Build on verified public v0.4.1/source `e579c57`. Reuse existing setters and
native fault semantics; no emulator-core rewrite or new hardware model.
Luna High implements app controls and focused tests; an independent Luna High
reviewer checks cancellation, partial failures, state reporting and actual-core
coverage. Coordinator handles docs, integration and required GitHub gates.

Acceptance: one action pauses and best-effort clears each configured domain;
no late pulse or key release restores a fault or triggers CPU recovery; failures
retain successful clears and remain paused; optional legacy APIs are reported
truthfully; CPU-only controls retain RAM/VRAM clearing and audio preservation;
exported metadata does not confuse fault removal with a CPU intervention.
Preserve the small-screen chip budget and existing strict configuration import.
Run full applicable regression and compiled-core browser checks before merge.
No public release or version bump for this intermediate workbench slice.

PR #49 and its merged-main run passed all seven checks; the integration
checkpoint above records the exact source and evidence. Do not repeat that
implementation.

## Completed bounded task: saved experiment comparison

Build on merged `1bb92a5` and include checkpoint `ec5756e`. Compare two saved
browser experiment exports without applying settings or calling emulator APIs.
Distinguish recorded ROM/core/build/model matches, mismatches and unknown
metadata; keep settings, active state and recorded counters/outcomes separate.
Preserve legacy exports and identify missing fields rather than inferring them.
Matching metadata does not establish replay, gameplay or causal equivalence.

Acceptance: bounded JSON input; text-only rendering; inert local file handling;
stale-read/cancel protection; clear identity and settings comparisons; no live
fault, pulse, CPU, cartridge or counter changes. Cover valid current/legacy
exports, mismatches, unavailable metadata, invalid input, hostile strings and
responsive display with focused tests and independent Luna High review.
Require full applicable source/browser/compiled-package CI before merging.
Preserve public v0.4.1, its original tag/assets and all recorded evidence. No
version bump or intermediate release; no McRetro.net work. After verified
integration, review combined workbench acceptance before the Phase D freeze.

Implemented and independently reviewed through `64ae7a3`. The full 107-test
native/SDK suite and source script pass; unchanged core evidence is reused.
Chromium interface59/59, compiled-core4/4, transaction3/3 and display6/6 pass;
final focused WebKit comparison2/2 passes. Final Chromium and required GitHub
PR/main checks remain before integration. The implementation includes bounded
input validation, explicit unavailable values, a readable scrollable table and
the additive logic-availability export flag while retaining schema versions.
Final Chromium60/60 and extracted package core4/4 plus transaction3/3 pass.
Independent review approves final keyboard fix `2d29d0a`; focused comparison3/3
passes in both Chromium and WebKit. All seven final-head PR and main checks pass; see the integration checkpoint above.

## Completed source acceptance: combined workbench

Acceptance criteria covered by the eight-frame integration and existing original
synthetic cartridge tests: configuration save/preview/apply, presets, chip-local
randomisation, fault removal, memory-only
CPU recovery, clean restart, export and comparison as a combined workflow on
runtime and normal fallback cores. Check active state and retained history,
truthful partial/unavailable results and keyboard/pulse boundaries without
adding another fault model or repeating completed RAM research. Reuse valid
individual-domain and core evidence. Record any concrete acceptance gaps;
essential flows now pass in source, so Phase D feature freeze is active.
