# Development status and continuation checkpoint

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

## Completed user priority — compact RAM pulse and recovery

The user requested CPU reset beside Randomiser, a temporary Work RAM write
randomiser confined to A11–A15, and no forced pause during all-domain clearing.
Implementation is isolated on `experiment/workbench-ram-pulse` from checkpoint
`ffb330f`. The new burst uses the existing eight-affected-write/one-frame limit
without CPU recovery; the existing advanced forced-resume pulses remain intact.
Confirmed complete disconnection preserves prior play/pause, while partial or
unknown outcomes pause for inspection. Reuse existing native code/evidence,
preserve v0.4.1 and keep McRetro.net untouched. Integrated by PR #52; see the current checkpoint above.

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


## Earlier Randomiser implementation checkpoint

The user requested **Randomiser** followed by independent **PSG**, **FM** and
**VRAM** buttons. Implementation is isolated on `experiment/random-chip-faults`
from checkpoint `d44c063`, with documentation in a separate worktree. Reuse the
verified models and apply paths; preserve Work RAM and every unselected chip.
This user request precedes the combined workbench acceptance task below. No
native model, version bump, public release or McRetro.net deployment is planned.
Implementation `5be6d9e` and independent Luna High review/fixes `2cc4914` are
complete. The full 107-test native/SDK suite with normal sanitizers and fresh
WASM profiles and source script pass; core implementation is unchanged.
Final Chromium interfaces66/66 and focused WebKit Randomiser5/5 pass. The
compiled-core5/5, transaction3/3 and display6/6 checks pass, including actual
native Randomiser settings and configuration export. Visual checks put the
Randomiser row below all four chips within 1366 by 768, with no horizontal page
overflow at 1366, 768 or 390 pixels. A nondeterministic new test was corrected
to force the expected mode; the failed log is retained. Required PR/main CI and matching review-package verification passed;
see the final integration checkpoint above.

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


Verified on 24 October 2026. Read [work queue](WORK-QUEUE.md),
[versioning](VERSIONING.md), [testing](TESTING.md) and [roadmap](../ROADMAP.md).

## Earlier implementation checkpoint

The next source slice adds read-only comparison of two saved experiment exports.
Implementation is on `experiment/experiment-comparison`, based on merged PR #49
and its checkpoint `ec5756e`. It reuses exported metadata rather than introducing
a new emulator model. Export schema versions remain unchanged; the additive
`logic.available` flag identifies unavailable counter fallbacks. Comparison separates
ROM/core/build/model identity, recorded settings, active state and results, with
missing legacy metadata explicitly unknown. No public release or version bump
is planned. See [comparison usage](EXPERIMENTS.md#compare-saved-exports-development-source).
Independent Luna High review approves source checkpoint `64ae7a3`. The full
107-test native/SDK suite with normal sanitizers and fresh WASM profiles passes,
as do the source script's JavaScript/native checks. The unchanged native/core
evidence is reused after the final input-validation and presentation fixes.
The initial full Chromium interface suite passes 59/59; compiled-core4/4,
transaction3/3 and display6/6 pass. Final focused WebKit comparison tests pass
2/2, including actual exporter mask/data-pair records, stale reads, no mutator
calls and 390-pixel layout. Final Chromium regression and required PR/main CI
remain integration gates until the final verification record is added below.
The final Chromium suite passes 60/60 before the focused keyboard fix.
Independent review approves `2d29d0a`: results-region arrow scrolling and blocked
game hotkeys pass all three focused comparison cases in Chromium and WebKit.
Native/core evidence is unchanged; required CI must pass on the final head.
The next bounded task after that gate
is combined workbench acceptance before the Phase D feature freeze.

Coordinated all-domain removal is implemented in development source after the
public v0.4.1 baseline below. It pauses, cancels held/momentary restores and
pulse callbacks, independently clears available domains and records truthful
per-domain outcomes in `faultDisconnects`. CPU recovery keeps its existing
RAM/VRAM clearing and explicitly preserves audio fault configurations. No new
native model or core implementation is introduced.

Independent Luna High review approves integrated implementation `96f4abd`.
The 107-test native/SDK suite with normal sanitizers and fresh WASM profiles
passes. Compiled-core Chromium4/4, transaction3/3 and display6/6 pass. WebKit55
plus the final three boundary cases and final Chromium interface checks are
recorded in the current task logs. Required PR/main CI and the same-commit
review package remain before source integration. No public release is planned
for this intermediate slice; retain v0.4.1 and its original artifact unchanged.
Next after verified integration: experiment comparison, then the remaining
workbench acceptance and stabilisation queue.


PR #48 is merged as `e579c571f14b3549a5befa33d9e62ba3f3c9d45b`.
[PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40088693320)
and [main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40089045294)
passed all seven checks. The merged source tree is identical to independently
reviewed head `1878816`. [Publication40089373232](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40089373232)
passed all four jobs and published **VRAMpage MD v0.4.1** from that exact merge.

The [public complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.1/VRAMpage-MD-v0.4.1-macos.zip)
was freshly downloaded. Its 681 unique entries, executable launcher, source,
notices, tag, version and matching root/site build manifests are verified.
SHA-256: `36133552de9c7dafb9502dea957b6a4934fe4b503d19e311fb898834162ec6fd`.
Runtime JS/WASM hashes match the reviewed candidate. Downloaded production API,
PSG/FM mask/pair tone and reset tests pass; extracted Chromium actual-core4/4
and transaction3/3 pass. The launcher serves complete required asset bodies with
HTTP200 and exits cleanly on Ctrl+C. No ROM or secret paths/signatures found.
Local WebKit also passes all six display and 45 logic tests after independent
probes isolated native Work RAM select overflow. Shorter action labels fix it
without replacing the control or weakening the overflow checks.

There are no outstanding delivery gates for this feature. Next: coordinated
fault-disconnect/recovery using existing setters and pulse protections, then
experiment comparison. Bundle this checkpoint branch with that next implementation;
do not repeat completed configuration, chip, VRAM or audio work.

Continuation environment notes are `/workspace/scratch/VRAMPAGE-ENVIRONMENT.md`.
Reuse `/usr/bin/chromium`, the pinned SDK and cached WebKit under
`/workspace/.cloud-tools/playwright`; do not reinstall them. The local WebKit
wrapper needs the documented workspace library setup. CI uses its normal system
libraries. No native Mac, audible or physical testing is claimed.


Public v0.4.1 delivers a compact 2 by 2 chip workbench: VRAM, Work RAM, FM
and PSG/VDP. Pin selections and connections stay within each chip. Existing
VRAM/Work RAM behavior is reused; runtime FM/PSG data masks add stuck-low cuts
at the existing write boundaries. Work RAM data bridges remain in advanced
settings and their active state is reported on the compact card.

Reciprocal Luna High review approved the native core and UI/config changes.
The full 107-test native/SDK suite passes with normal sanitizer settings, fresh
WASM profiles and both FM backends. Chromium passes 45 logic tests, four
actual-core tests, three transaction tests and six display/fullscreen tests.
The actual-core cases exercise both audio chips' masks and import legacy pairs
back over them. All four chip bodies fit within the 1366 by 768 viewport.
Configuration schema 2 saves masks and imports schema 1; new audio experiment
subsections are schema 2 with native model v2. Historical files are unchanged.
Final package, PR/main CI, publication and fresh public-download checks pass above.


Configuration save/preview/apply is merged in [PR #47](https://github.com/NixMcRetro/VRAMpage-MD/pull/47)
as `ccc80e12db4a58ca54d5056bcd0e9d5cc188f013`.
[PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40083076183)
and [merged-main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40083371467)
pass all seven checks, including three-browser interfaces and extracted
actual-core Firefox/WebKit. The merged tree matches reviewed head `2207fa3`.
Independent Luna High review, full 107-test native/SDK suite, schema/native/JS
checks, 40 Chromium logic cases and four actual runtime/normal-core cases pass.
The 679-entry extracted review package also passes three transaction cases.
A transient GitHub API HTTP 503 affected status polling only and recovered;
no failed workflow was hidden or rerun to bypass a failure.

Public v0.4.0 remains unchanged at its original tag/source below. The new
configuration and chip workbench features are delivered together in public
v0.4.1 through [PR #48](https://github.com/NixMcRetro/VRAMpage-MD/pull/48). No external
repository was modified or deployed.

The compact four-chip workbench and native PSG/FM line masks are implemented.
Resume the work queue's coordinated fault-disconnect/recovery task after the
completed chip workbench. All delivery gates pass above.
Use existing setters and pulse protections, distinguish memory-only CPU recovery
from all-domain disconnection and clean restart, and require truthful partial
failure status. Do not repeat configuration, VRAM or audio implementation.

Audio-input milestone **v0.4.0** is merged and publicly verified.
[PR #46](https://github.com/NixMcRetro/VRAMpage-MD/pull/46) merged as
`8c1d5329477d8702e1fb0d294abfbc233d50d80d`.
[PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40069242003)
and [merged-main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40069602921)
passed all seven checks. [Publication](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40069946647)
also passed, including extracted actual-core Firefox and WebKit tests.
The [complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.4.0/VRAMpage-MD-v0.4.0-macos.zip)
has SHA-256 `161ce8a914aa0ed42079c30b2a0dc705d95cdc57a4ec4a0e91bb9d8fed5f572c`.
A fresh public download has 676 unique entries, matching version/tag/source
manifests, executable launcher and runtime binaries identical to the tested
candidate. Node API and both-chip/Z80 tests pass on the downloaded core, as do
two actual Chromium audio/control and three transaction tests. The launcher
serves all required assets and shuts down cleanly. Earlier releases are unchanged.

The bounded audio milestone covers chip write-input bridges, not Z80 RAM faults
or arbitration changes. Native audio probes observe stereo 44.1 kHz finite
buffers, bounded start lead, pause/resume and a synthetic visibility event under
normal test load. They do not establish audible quality, actual OS background
throttling or physical fidelity. See [audio model](AUDIO-BENDING.md).

Active Phase C: strict circuit-configuration save/preview/apply, implemented on
`experiment/circuit-config` from this release. Import is inert; explicit apply
must preflight capabilities and preserve counter state for unchanged settings.
Thrown-setter pause, unavailable-state reporting and undirected-pair
normalization are implemented, including reversed live audio selections.
Actual-runtime configuration staging, RAM/VRAM handoff and export tests pass;
independent specialist review and the full 107-test native/SDK regression
suite pass. Browser logic passes 40 tests; actual runtime and normal-core
configuration, audio and control tests pass all four cases. Async selection
tokens prevent stale reads or canceled files from replacing the preview.
Integration is tracked in [PR #47](https://github.com/NixMcRetro/VRAMpage-MD/pull/47).
GitHub checks remain the merge gate; no new public release is planned. Read the work queue before older checkpoints.

Transaction VRAM v0.3.0 is merged and publicly verified. [PR #43](https://github.com/NixMcRetro/VRAMpage-MD/pull/43)
merged as `4cfb983f3003449c0632375576f6a674e660d778`.
[PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40062636637)
and [merged-main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40062903294)
passed all seven checks, including packaged actual-core Firefox and WebKit.
[Publication](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40063210310)
passed. The public [complete Mac ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.3.0/VRAMpage-MD-v0.3.0-macos.zip)
has SHA-256 `b1570d4b9524ba3c87bbeacb2672d5be4883f4a24e8ac90092fd828d6924aef6`.
The tag, both build manifests, version and source commit agree. All 626 entries,
executable launcher, source and notices were checked. Fresh downloaded-core API
and three actual-browser tests passed, as did launcher asset serving and Ctrl+C
shutdown. Runtime binaries match the independently audited timing record.
Native macOS, audible output and physical electrical accuracy are not claimed.
Previous public artifacts remain unchanged.

Implemented: explicit frame/transaction selector, VRAM legs and bridges,
capability/effectiveness reporting, five completed-frame transaction counters,
separate experiment metadata, and validated RAM/VRAM handoff with rollback and
fail-closed pause. Active RAM pulses reject takeover without losing their budget.
The production site bundles the runtime plus corresponding source; the normal
core remains a supported fallback with unchanged binary hashes.

Independent Luna High implementation/review covered the app and core changes.
The final core/source checkpoint passed 99 Python tests without skips, normal
LeakSanitizer, strict/native and JavaScript suites, five fresh actual-WASM
profiles, production normal/runtime builds and actual-core Chromium. Version
changes passed six focused checks and repeated actual-core browser tests.
The first runtime timing failed and is preserved; the reviewed inactive path
passes the unchanged fixed five-pair gate with independent raw-data audit.
See [both retained records](experiments/vram-runtime-performance-2026-10-24-v2-summary.json).
These synthetic timings do not establish game-wide performance.

The first PSG input-data bridge is merged in development source through
[PR #44](https://github.com/NixMcRetro/VRAMpage-MD/pull/44), as
`c26c19f7272eb16ee711b48d997ecc19fde79e89`.
[Final PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40066559119)
and [merged-main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40066918601)
pass all seven checks, including extracted actual-core audio/controls in Firefox
and WebKit. The immutable public v0.3.0 ZIP is unchanged and does not include PSG.

PSG defaults off, reports exact unsigned decimal counters, handles unavailable
APIs, preserves editable pair drafts, and exports separate metadata. Clearing
changes future writes; full PSG reset clears its configuration/counters, while
CPU-only reset does not promise chip repair. Independent specialist review,
normal sanitizers, fresh WASM, normal/runtime/normal builds and actual browser
checks pass. A diagnostic builder dependency omission was repaired and fresh
store-origin/VBlank WASM suites pass. Native Firefox was suspended at time zero
on the headless runner; an explicit 44.1 kHz PulseAudio virtual output resolves
it with unchanged enable/mute assertions and a stronger advancing-clock check.
This validates software routing, not audible output or native macOS.

FM implementation and independent specialist review are complete through
`204e611`, integrated on `integration/audio-fm`. The optional bridge transforms
FM address/data input bytes at the shared YM2612/YM3438 boundary and preserves
native timestamps, ports and busy handling. Matching normal/runtime tests cover
both backends, finite generated samples, disabled equivalence, active changes,
full reset and partial Z80 reset semantics. Browser controls and separate export
state preserve PSG independence and legacy fallback.

The original Z80-to-PSG fixture has also passed independent review and actual
runtime checks: three writes, two changed bytes. Its encoded bootstrap proves
that the 68K only controls BUSREQ/RESET and loads Z80 RAM, rather than writing the
PSG directly. Final local regression passes: 107 Python tests with normal native sanitizer
checks, JavaScript suites, fresh production/diagnostic profiles and both FM
backends. The reset fixture now proves execution with a post-reset mailbox; its
old DBRA loop incorrectly never reached reset. Both backend tests pass after
that correction. Actual Chromium audio/controls and transaction tests pass.
GitHub CI and merge remain pending. Do not declare
v0.4.0 complete or publish before full audio acceptance. Read the work queue
before older historical records below.

## Compact Work RAM interface

The v0.2.8 cosmetic update reduces the diagram from 300 by 256 to 260 by 192
CSS pixels with at least 24-pixel pin targets. Local full source/WASM and
Chromium layout, logic and actual-core checks passed; see [testing](TESTING.md).
Normal emulator binaries are unchanged. No native Mac check is claimed.
Renderer integration remains a separate developer task with its own gates.

## Renderer continuation recovery

On resumption, the temporary renderer worktree and its uncommitted source were
missing. Its branch and Git index still identified the PR #36 base; no renderer
source checkpoint was recoverable. The committed scope document remains, but
previous temporary renderer test observations cannot certify rebuilt code.
At that recovery checkpoint, no reconstructed renderer change had been merged
or released.

Reconstruct the reviewed design in a persistent `/workspace` worktree, commit
bounded source/test checkpoints, and repeat focused and final acceptance on
those commits. First checkpoint: renderer byte-read helper, cached lifecycle
gate, literal endian/wrap oracles and strict/sanitizer checks. Then route the
pinned renderer and restore the full visible/cache/SAT/performance matrix.
The first helper checkpoint is now committed on
`experiment/vram-render-cache-resume` through
`1b2fd0d71de0dc2d0a2ab90af130325518e43472` and incorporated into the local
integration branch. Six focused helper tests passed with normal leak detection:
strict and ASan/UBSan builds, both host-layout branches, literal packing oracles,
ordered mapped reads, wrap and inactive direct loads. Independent specialist
source review approved progression to renderer routing. Its separate restricted
sanitizer run required a local ptrace workaround; the coordinator's verification
used normal LeakSanitizer without suppression. The full local regression suite also passed 83 Python tests with no skips,
fresh normal/diagnostic WASM builds, existing JavaScript/native suites and normal
LeakSanitizer enabled. This verifies existing CPU/DMA behavior, not renderer
routing. The next routing checkpoints `d74b930` and `1bbdd1a` now cover the pinned Mode 5 inventory and reject missing/unrouted reads. Independent source review approved progression to visible fixtures; the integrated routing checkpoint passed 89 full Python tests, normal/diagnostic/alternate WASM builds and existing native/JavaScript checks. Later committed four-core fixtures now cover visible output, cache aliases, lifecycle transitions and mixed SAT behavior. Independent review approved the source and literal pixel oracles. The VS/interlace active checks cover line zero, not full-field timing. Fixed-tick DMA preflight passed independently; final integrated correctness and actual-core Chromium now pass. The fixed five-pair gate failed diagnostic-off p95 (1.069346) and identity median (1.126256) against 1.05. Independent review confirmed all measurements and provenance. A reviewed inactive-guard correction now passes the 91-test full suite and fresh actual-core Chromium; the fresh fixed-protocol second run now passes all three no-fault median/p95 gates. Both full raw records are preserved; independent audit passed and required CI remains the merge gate. This diagnostic checkpoint is tracked by PR #40; it does not complete public
transaction-model or v0.3.0 acceptance.

## Verified baseline

- Main contains the complete stacked development history through v0.2.7,
  including v0.2.5 VRAM leg switches and v0.2.6 build identification. Earlier work was not rebuilt
  from the initial main or blindly cherry-picked.
- Corrected v0.2.4 remains public with its original tag and assets. A fresh public
  download matched SHA-256
  `4f9a60a70e5b1ecf64537196bc2c365b96c4824e2b3c1683a26191d2bbaa2e5b`;
  root manifest version `0.2.4` identifies
  `e2d974fb57bcb9c95ec5f950ec2ee20d8c5b03fc`. The 274-file ZIP has the compiled
  JS/WASM, corresponding source, notices, executable launcher and no bundled ROM.
  Extracted actual-core and unmocked local-launch/cartridge/export checks passed.
- The earlier v2.4.0 release entry/assets remain deleted, as explicitly reaffirmed
  by the user. Its original Git tag remains. Do not restore the release.
- v0.2.5 remains an immutable public release. The user says it appears to work on
  their Mac, as far as they can tell. This is qualified feedback, not complete
  native macOS Firefox or audible-output acceptance.

## User-reported native acceptance

The user confirms sound, USB keyboard input, resize and fullscreen in Mac
Firefox. Fault removal works while responsive. Exceptions and hard crashes need
CPU restart or clean restart; removal alone does not recover them. Both restart
actions reportedly clear the observed condition. The package version was not
identified with this feedback. The user has no physical gamepad, so physical
controller acceptance remains untested. See [Testing](TESTING.md) for scope.

## Implemented functionality and evidence limits

The application includes the native framebuffer fix, legacy missing-line
recovery, raw output, responsive/fullscreen display, system Light/Dark appearance,
keyboard/gamepad controls, sound controls, VRAM patchbay/leg switches, work-RAM
faults, CPU recovery, frame/write-limited pulses, restart, logging and exports.
Tests cover original synthetic cartridges and actual compiled emulator execution.
See TESTING.md for the distinct historical real-game observations.

VRAM faults remain frame-scoped. Digital low-dominant and stuck-low approximations
are not measured electrical models or verified physical package pin mappings.
A partial transaction access diagnostic exists, but complete per-access
VDP/render faults and hardware-informed audio bending remain unfinished.
No new native Mac, audible, commercial-game or physical-hardware test is claimed.

## Historical v0.2.6 integration and release

PR [#20](https://github.com/NixMcRetro/VRAMpage-MD/pull/20) merged v0.2.6 experiment
build identification without changing core/fault models. Reviewed head:
`8f71dfbcb936238f1c14d402809e1b156ac439e7`. Merge commit:
`6d18f8e80191f1d60e5aa7b5899d3524c6dcbc07`.
All required [PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39762699685)
passed, including Chromium, Firefox, WebKit and a fresh core/package build.

Local checks passed: 63 Python tests, both framebuffer suites, nine pulse protocol
groups, both native C smoke programs, 28 Chromium logic cases, six display cases,
23 actual-WASM original-cartridge checks and actual-core browser smoke. An
extracted package launched and exported its actual source commit using the real
manifest. Basic implementation/packaging workers and coordinator reviewed it;
independent Luna High source/test-design review found no concrete regression.
That specialist review executed no additional checks.

The [v0.2.6 release](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.6)
is public. Its [release workflow](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39767990645)
passed and built the exact merge commit above. Download
[VRAMpage-MD-v0.2.6-macos.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.6/VRAMpage-MD-v0.2.6-macos.zip).
The asset SHA-256 is
`8f2c1fd895ee28d59b486ecb520be04b77aacbc6c2b1c29c06349e44e87886fc`.
A fresh public download matched its attached checksum. Root/site manifests were
byte-identical and matched the source/tag/version. The 277-entry ZIP passed
runtime/source/notices, executable launcher and ROM/secret checks. Unmocked
extracted launcher and actual-core browser checks loaded the original synthetic
cartridge and exported the exact release SHA without page errors. The actual-core
check covered native video rows, generated audio samples, keyboard/gamepad adapter,
VRAM/RAM faults, recovery, restart and exports. No native Mac/audible/gameplay claim
is implied. Previous v0.2.4/v0.2.5 ZIP digests and historical JSON remain unchanged.

Refresh CI/release state from GitHub before continuation; documentation-only
commits after this release do not replace the tested package or retag it.

## Read-only observer checkpoint

The observer uses the immutable v0.2.6 application/core profile. The separate developer
observer adds no core, game-code, direct game-variable or hardware-model edits.
Permanent instructions/status/queue were merged in
[PR #21](https://github.com/NixMcRetro/VRAMpage-MD/pull/21), main commit
`8fbbbce9d935cf550a7f2c1a91b2610a2c7a9e88`; its
[post-merge CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39772128971)
passed all browser/source/package jobs. An earlier main WebKit installation
exceeded its job limit before tests began; a fresh rerun of that job passed.

Observer protocol 1 and 2 have separate immutable six-trial JSON records in
[Attract-mode observations](ATTRACT-MODE-OBSERVATIONS.md). Protocol 2 tool source
is `fff7c95e9cd3c6bf0eb7c3f18357972bcdc672eb`, file SHA-256
`2dd2c8e46a622248a05b7aac161c6de0248a89059e547bf5701f7f207971a0f0`.
Its record identifies the published package/core separately from the tool.
Independent Luna High review checked actual code, field mappings and tests and
ran the six actual private-cartridge trials. Baseline Sonic object ID 1 was
observed through all 602 timeline ticks. Source checks cover 63 Python tests,
framebuffer suites, nine pulse groups, nine observer groups and both C smokes.

## v0.2.7 integration and release verification

PR [#23](https://github.com/NixMcRetro/VRAMpage-MD/pull/23) merged the diagnostic as
`6c7469fefe8d004c0e61b360e08579dc9b100a9d` after all
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39784517150)
passed. The first post-merge run [39784898869](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39784898869)
exceeded the Firefox installation limit. A targeted fresh-runner retry reached
all tests and exposed a separate-read counter race, not a runtime reset defect.
[PR #26](https://github.com/NixMcRetro/VRAMpage-MD/pull/26) preserves the exact
invariant in one synchronous snapshot. Its full
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39790523455)
passed; merge `1d87fd9a921194a557fc5320e54be48295c62b1f` exactly matches the
tested merge tree and preserves concurrent release-presentation PRs #24/#25.
The [fixed main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39863314204)
passed all source/browser/core/package jobs.

The public [v0.2.7 release](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.2.7)
was built by [39863608264](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39863608264)
from exact source/tag `1d87fd9a921194a557fc5320e54be48295c62b1f`.
The fresh public ZIP is 1,344,568 bytes, 319 unique entries, SHA-256
`2e1beee265041a42f5544262291284be937fa1d23958f21ac553b79f8f46a1ae`.
Its checksum, root/site manifests, version, tag, executable launcher, source,
notices and ROM/secret checks passed. From an unrelated directory, START.command
served eight assets successfully and stopped cleanly with Ctrl+C. The extracted
public core passed 25 actual-WASM original-cartridge checks and the full actual-core
Chromium smoke using real package metadata, including video/audio generation,
controls, faults, recovery, restart and export. No native Mac or audible acceptance
is claimed for this new build. Older release binaries and experiment records remain
unchanged. Catalog/download presentation updates do not rebuild this public ZIP.

The optional default-disabled first-affected-write diagnostic passed local verification.
The API records logical address metadata, bus width, completed frame and reason,
never memory values. The separate runner compares tracing off/on/repeated and
checks historical v0.2.6 observations. See [RAM write trace](RAM-WRITE-TRACE.md).
Strict native/sanitizer, 25 actual-WASM checks, 28 Chromium logic cases, six
display cases and actual-core browser smoke passed. Independent Luna High source
and test review approved the implementation. The review ZIP from f0cc664 has
288 unique entries; an independent default worker verified manifests, source/notices, executable launcher, ROM/secret
exclusion, eight served assets and browser startup without errors.

Independent specialist review reran all six trials and obtained byte-identical
output. The previous sprite-table label was incorrect. Corrected source allocation
identifies `$F62A` as `v_vblank_routine`; `$F22A` remains the `AMSFMSPan`
field of the first sound-effects FM track. The VBlank flag set/clear and wait
paths provide a timing hypothesis, not an exact-PC or audible-effect observation.

The six-trial [trace record](RAM-WRITE-TRACE.md#recorded-first-write-result)
identified a byte write at `$FFF62A` mapped to logical `$F22A` during tick 1801.
Traced/untraced and enabled repeats matched exactly. Baseline and one-write
observations matched the preserved v0.2.6 protocol-2 output. This localizes the
access and verifies bounded diagnostic noninterference; sustained gameplay
divergence remains unproven.

## Highest-priority unfinished experiment

The user supplied the private 512 KiB cartridge matching the historical
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`
fingerprint. It stays outside the repository and packages. Source-backed
internal demo playback is now observed in baseline and A10/A11 one-write trials.
The sustained D0/D1 read control stops the demo despite clear CPU flags.

For A10/A11, all 596 monitored demo/player tuples match baseline one tick earlier.
Exactly one affected write is recorded, with no CPU recovery. This establishes
a continuation candidate consistent with a phase delay, not sustained gameplay
trajectory divergence. Thirty-five raw-frame hash differences remain after that
alignment; they do not establish changed gameplay. Visual scene identity,
whole-game equivalence, native Mac/Firefox, audible output, other revisions and
physical hardware are not validated. The RAM-stage acceptance remains open.

The first affected generic write is now identified; its causal effect remains
partially localized. The named-state/audio comparison and instruction-origin
result are now recorded below. Next assignment: Luna High should verify the
bounded wait/release sequence using existing diagnostic hooks first. If
additional passive instruction/state metadata is needed, define a
bounded implementation in the generic RAM access layer, with no game-specific
writes, no silent recovery and no ROM/RAM byte output. Require independent
specialist review and strict native/sanitizer, actual-WASM, no-fault and exact
budget/counter regression tests. Record only diagnostic metadata. Any runtime
API change uses the next 0.2.x version and keeps the v0.2.6 profile/artifacts intact.

Use the identified access and source-backed scene/playback observation to choose
a bounded next trial. Repeat baseline and fault from equivalent resets, examine
phase alignment and player state, and record failures honestly. Do not run an
undirected large sweep or advance to transaction-level VRAM on hash differences.

## Restart instructions

Fetch main and open PRs/releases/CI. Read AGENTS.md and the queue, preserve local
changes and existing artifacts, finish pending release checks, then continue the
first unblocked RAM-stage item. Use pinned tools and existing scripts. No work is
authorised in McRetro.net. There is no unattended background-execution promise.

## Bounded audio/state follow-up

The [RAM alias/audio phase protocol](RAM-ALIAS-AUDIO-PHASE.md) records eight
fresh-core trials against the unchanged public v0.2.7 package. Repeats,
prefault and observational noninterference passed. Demo/player observations
match lag -1 for 596/596 pairs; audio hashes match none of five tested lags.
The corrected source mapping identifies the VBlank routine flag, not a sprite
buffer. The diagnostic below now identifies the instruction and zero-write class.
Intermediate flag progression, audible effect and genuine sustained trajectory
divergence remain unproven.
No runtime version or published package changes are required for this tooling.

## PR #28 integration verified

[PR #28](https://github.com/NixMcRetro/VRAMpage-MD/pull/28) merged as
`eaf7c271ff6f054642e637098429d1173bee3c82`. The merged tree matches the reviewed
branch. [PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39867309696)
and [main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39868043581)
passed source, Chromium, Firefox, WebKit and actual-core/package checks. The
post-merge WebKit installation delay completed successfully without a retry.
The public application remains the unchanged v0.2.7 download.

## VBlank store origin localized

The [isolated diagnostic](VBLANK-STORE-ORIGIN.md) records a repeated zero-write
at instruction-start PC `$B46` for byte address `$FFF62A` remapped to `$F22A`
during tick 1801. Six custom-core and two public-core trials pass all acceptance
gates; nine synthetic actual-WASM CPU groups validate PC/classification and
lifecycle. The public runtime, app version and download are unchanged. The
result identifies the clear candidate; the complete delayed wait/release
sequence is the next bounded question. No sustained gameplay divergence or
new audible/native Mac/physical acceptance is claimed.

## PR #29 integration verified

[PR #29](https://github.com/NixMcRetro/VRAMpage-MD/pull/29) merged as
`640a22e5da8e13c58bac4f2df3a1433e554f642d`; its tree exactly matches reviewed
head `c96f256`. [PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39874114777)
and [main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39876027287)
passed all source, three-browser and actual-core/package checks, including the
new isolated diagnostic CPU tests. Independent specialist review reproduced
the private eight-core evidence byte for byte. The normal v0.2.7 application,
public download, runtime API and historical evidence remain unchanged. Continue
with the bounded wait/release sequence in the work queue.


## Bounded VBlank wait/release verified

The [wait-sequence protocol](VBLANK-WAIT-SEQUENCE.md) records a matched Revision 0
source build and nine fresh-core trials including the baseline scout. A10/A11
redirects the tick-1801 zero-write at `$B46`, leaving the native flag nonzero.
Polling continues until the ordinary tick-1802 clear; the wait return, caller
successor and next setup then execute. Baseline reaches those milestones at
1801. All origin, repeat, prefault, exact-budget, zero-host-input and public-core
equivalence gates passed. Earlier JSON and public v0.2.7 are unchanged.

Local checks passed: 76 Python tests with strict native/sanitizer coverage,
existing JavaScript/native suites, 27 wait-runner groups, 18 new wait actual-WASM
and nine existing origin CPU groups on one clean staged compilation. Independent
Luna High source/profile and evidence review approved the final changes and
record, including the distinction between listing context and observed milestones.
This result explains a bounded one-tick wait delay, not sustained gameplay
divergence. Next: choose a source-backed bounded RAM experiment using the
existing demo/player observer, with no game-specific edits or silent recovery.


## A12/A13 object-alias candidate evaluated

The [bounded candidate](RAM-GAMEPLAY-CANDIDATE.md) produced a valid negative.
Six public v0.2.7 fresh-core trials passed protocol, repeats, prefault,
noninterference, zero-input and exact one-write release checks. The first affected
byte write was `$FFD022` to `$C022`, the player object's status field rather than
its position or velocity. Demo progression and the recorded CPU/player safety
checks passed. All 596 frame/demo/player pairs match baseline at the unique
zero-tick offset; no qualifying position difference was observed.

The normal app, public download, runtime API and version remain unchanged.
The shared observer preserves the old default scenarios and API guards; actual
baseline and A10/A11 observations match their previous immutable public-core
records exactly. Local source, native/sanitizer and JavaScript suites passed,
including nine new candidate groups. Independent specialist source review
approved the helper, trace invariants and positive/negative report assembly.
Genuine trajectory divergence remains unproven. Next: a separately defined
source-backed follow-up using the observed status-write location, with no
post-hoc changes to this experiment or silent CPU recovery.


## Bounded RAM trajectory criterion verified

The [eight-write follow-up](RAM-STATUS-FOLLOWUP.md) passes the predefined criterion
on the exact public v0.2.7 core and supported ROM. All 596 demo-state/input tuples
match baseline at the unique zero-tick offset, while player position differs by
at least one pixel on 594 ticks, with a longest consecutive run of 432. The pulse
released after exactly eight writes at tick 1801; all prefault, repeat,
noninterference, host-input and recorded CPU/demo/player safety gates passed.
An independent specialist repeated all six fresh-core trials and reproduced the
JSON byte for byte. The baseline matches the prior immutable public observation.

The first trace is still the status-byte alias D022 to C022; later seven addresses
and exact downstream causality are not recorded. No game code/variables were
edited directly and no CPU recovery was applied. Physical, audible, native Mac
and visual-scene interpretation are not established. All prior negative and
phase-delay records remain unchanged. App/runtime/API/version/download remain
v0.2.7. Local full source/native/sanitizer/JavaScript tests passed, including six
new wrapper groups and independent clean-archive verification. Next: a bounded
transaction-level VRAM architecture/test plan, before any v0.3 implementation.
