# Development status and continuation checkpoint

Verified on 24 October 2026. Read [work queue](WORK-QUEUE.md),
[versioning](VERSIONING.md), [testing](TESTING.md) and [roadmap](../ROADMAP.md).

## Current checkpoint

Verified integration base: `46dcc80a8d561cde4b79453300a2a1bdee3e847c` (PR #41).
[Main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40041499264)
passed source, Chromium, Firefox, WebKit and actual-core/package checks.
The immutable [v0.2.8 Mac package](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.2.8/VRAMpage-MD-v0.2.8-macos.zip)
was published by [workflow 39972454348](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39972454348)
from `f1aad11f331e772e6ec786be020d54b36905c7ba`. Its tag, manifests and checksum agree.
PR #39 subsequently aligned the release catalog and editorial links without
rebuilding or replacing the public package; the release curator passed. The downloaded
ZIP passed actual-core Chromium and unmocked local launcher checks, including
clean Ctrl+C shutdown. No new native macOS validation is claimed.
Playwright caches remain enabled. Browser OS dependencies use official Ubuntu
mirrors with bounded retries; no tests or pinned browser versions were removed.
The public app retains the existing frame-scoped VRAM model.
The first affected write is identified at PC `$B46`; bounded actual-bus evidence
now shows wait/caller release one tick later. The eight-write follow-up now meets the bounded same-input-phase trajectory
criterion. The [transaction-level VRAM plan](TRANSACTION-VRAM-PLAN.md) maps
CPU/Z80 ports, DMA, renderer/cache and sprite-table paths. The developer-only
[access diagnostic](VRAM-ACCESS-DIAGNOSTIC.md) now connects CPU/Z80 ports and DMA
to the helper in a separately compiled test variant. The [semantics protocol](TRANSACTION-VRAM-SEMANTICS.md) now fixes
byte/lane ordering, cache dependencies, supported modes, sprite-table policy and
explicit model compatibility. An isolated native helper implements those byte-access and dependency
primitives. Diagnostic core hooks preserve the normal access path by default;
renderer/cache reads are now implemented and locally verified in the separately
compiled diagnostic. [PR #40](https://github.com/NixMcRetro/VRAMpage-MD/pull/40)
merged after all required CI passed, and merged-main CI passed too. The [safe core model API](VRAM-PUBLIC-MODEL-API.md) is now implemented in a
harness-built runtime profile with separate diagnostic exports. Independent
review and the integrated 91-test suite, normal leak checking, five real-WASM
profiles, normal Chromium and real packaging passed locally.
[PR #41](https://github.com/NixMcRetro/VRAMpage-MD/pull/41) merged after all
required checks passed, and merged-main CI passed too. The normal app/release remains v0.2.8; the [isolated runtime builder](VRAM-RUNTIME-BUILD.md) now passes independent
review, normal/runtime/normal actual build checks, source-bundle reproduction and
the full 94-test suite locally. Normal core hashes and actual-core Chromium are
unchanged. Required CI precedes merge; UI selection,
experiment exports and milestone acceptance follow. Read the first unfinished
[work-queue](WORK-QUEUE.md) item and relevant protocol before older history.
Reuse unchanged passing evidence; new diagnostic code needs focused tests,
independent specialist review, final regression and CI before merge.

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
