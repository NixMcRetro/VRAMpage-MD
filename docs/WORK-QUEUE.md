## Safari Local-ROM Picker — Integration Checkpoint, 30 October 2026 (Sydney)

The owner reports that the live page's **Load Your Own ROM…** choice opens no
file dialog in Safari, while Firefox works. The native cartridge menu itself
opens. Before this correction, published and development builds triggered the
hidden file input from a native select's change handler. Linux WPE WebKit and Chromium open a dialog
with trusted keyboard selection; this does not reproduce macOS Safari's native
pointer-menu path. The old `select_option` test supplies activation while sending
untrusted change events, so it does not verify that platform interaction.

Keep one compact Choose Cartridge disclosure with the same manifest-approved
built-ins and local-ROM choice. Direct buttons open the local picker in their
click handler; preserve existing approval, validation, recovery, session/default
and cancellation rules. Use native summary/buttons, outside/Escape closing and
keyboard/focus handling without a framework or browser detection. Require
trusted click/keyboard picker coverage and the original race/rejection/layout
assertions, independent review, protected CI/CodeQL and verified main. Native
macOS Safari remains a manual confirmation; do not claim it passed in Linux.

Local verification passes: 18 cartridge cases in Chromium and WPE WebKit, the
seven original display/input cases in each engine, and final changed picker/
visibility cases rechecked after the automation-listener correction. Direct
click/Enter/Space each produce a chooser; cancellation/reopening, visible/hidden
state, focus, key isolation and desktop/mobile/844 × 390 bounds are asserted.
The full source/JS/native suite passes (23 cartridge and 148 general tests; two
unchanged vendor/SDK-dependent classes skipped). Independent review approved
after rerunning all three new picker/key/layout cases in WPE WebKit. Full
protected browser/package/CodeQL gates remain required before source merge.

[FM selector PR #108](https://github.com/NixMcRetro/VRAMpage-MD/pull/108) is
complete at `7d2dda1332989733a3fe5e84b0e8b9c3f8697cf3`, identical to its reviewed
tree. All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40890156450)
and four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40890155904)
passed; downloaded main browser/source artifacts match the independently rebuilt
runtime and approved cartridges. VERSION, published assets, approved Demo Cart
v0.3.5 and McRetro.net stay unchanged. The completed v0.5.1 publication approval
does not authorize publishing or deploying this later source correction.

## FM Output Model Selector — Integration Checkpoint, 29 October 2026

The compact Discrete/Integrated selector is implemented beside Region, using
[the bounded feature contract](FM-OUTPUT-MODEL.md). Discrete remains default;
changes stage until Clean Restart/new cartridge. Pending/rejected choices,
CPU Reset and checkpoint restore retain active sound/model and the saved slot.
Versioned `machine.fmOutputModel` observations/comparison distinguish pending,
effective and backend identity independently from Region; legacy/inconsistent
data stays Unknown. Grouped controls preserve active/pending labels on phones.

Independent Luna High specialist review approved after rerunning production
actual-WASM output/DAC/status/fault routing, all 13 checkpoint groups (two models
by NTSC/PAL), strict native/API and comparison checks, four focused mock browser
cases and a real-core FM/PAL/checkpoint browser case. Full source/ASan/UBSan checks
pass locally; both environment-dependent classes skipped in that command pass
separately with the pinned vendor/SDK (renderer patch and diagnostic-WASM). Retained-source rebuilding is
byte-exact with all 267 inventory hashes and Musashi notice validated.

Final runtime JS SHA-256 is
`dd69d2de684ff898b5dc69f01ac76a121a91c0bf5fe7c659122394c15063fac2`;
WASM is `04c3108a1359e364da25e1570e5789dd20d1f3a250e2ea97d62868967183f844`.
Only the runtime gate changes; normal gates stay fixed. Require all seven
protected checks and CodeQL before merge, then verify main. VERSION, approved
cartridges, releases and McRetro.net remain unchanged. Audibility and physical
hardware accuracy are not established. Experimental Demo Cart listening/gameplay
acceptance remains owner work; optional NTSC VA6 issue #73 does not block source.

## Completed FM Output Model Proof — 29 October 2026

[PR #107](https://github.com/NixMcRetro/VRAMpage-MD/pull/107) merged as
`4723457f4f80e94250e8f272bbedc04c4596fcb2`; its tree matches reviewed
`1395350c0026ebdf028e29af519952e0ce4ad525`. All seven
[main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40854623252)
and four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40854621660)
passed, following green PR checks and independent Luna High specialist review.
The [proof](FM-MODEL-PROOF.md) establishes native PCM/DAC/status behavior,
CPU/banked-Z80 cuts/bridges with exact counters and PSG isolation, and each
model's checkpoint/reset/restore/restart replay. Retained source rebuilt exactly
with all 266 inventory hashes/notices verified. No production control, default,
release, approved cartridge or website changed in that proof slice.

Experimental Demo Cart drafts still need owner acceptance; v0.3.5 remains the
manifest-approved default. Optional NTSC VA6 issue #73 does not block this work.
No new release or website deployment is authorized.

## Completed v0.5.1 Release and Website — 29 October 2026

[Source PR #102](https://github.com/NixMcRetro/VRAMpage-MD/pull/102) merged as
`bc7369c943f1f7cda5167632077235b7630ad41b`. All seven PR/main checks and four
CodeQL analyses passed. [v0.5.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.5.1)
was published after release workflow 40841450977 attempt 2 and exact rebuilding
of the downloaded source archive. Its source SHA-256 is
`47d93c3b5c97892bd8ffe8c278dca431d82acdf4779cec60b0c9b9111208e8bf`.

[Website PR #12](https://github.com/NixMcRetro/mcretro.net/pull/12) merged as
`c3ead06c63ca2a2e967c85524b7c28f27b3349c5`. Main deployment 40846544059 verified
all 17 live files and WASM MIME at https://mcretro.net/homepages/vrampage-md/.
The package is 17 files / 3,152,701 bytes (~3.01MiB), including one complete source
ZIP. Same-origin source remains mandatory; the matching GitHub release is a
mirror. Non-commercial hosting was explicitly confirmed. All 18 older releases
and their asset identities/digests remain unchanged. This release/deployment
authorization is completed, not standing permission for another publication.

## Built-In Cartridge Selector — Integration Checkpoint, 29 October 2026 (UTC)

Authorized task starts from main `c73ac2777e65640bfed14ec159804c9d563361f5`
([PR #99](https://github.com/NixMcRetro/VRAMpage-MD/pull/99), all seven main
checks and four CodeQL analyses passing). The new
[cartridge guide](BUILT-IN-CARTRIDGES.md) and `AGENTS.md` define the permanent
manifest/approval/release policy. `site/cartridges.json` owns current identities;
only explicitly approved originals are built and bundled. No generated ROM is
newly tracked. Application `VERSION`, public releases, original v0.1/source-kit
assets, captain portrait/logo and McRetro.net are preserved.

Choose Cartridge offers the approved Demo Cart, original Colour Test and the
local file picker. The existing activation/recovery path is reused; explicit
choices and Clean Restart cancel older manifest/fetch/hash/file/core waits.
Local file contents remain private. Built-in size and SHA-256 are verified even
on static HTTP hosts without Web Crypto. Complete ZIP/static packages require
all approved bytes and source/notices; unknown images, secret metadata,
symlinked source/destination paths and incomplete static runtimes fail closed.

Local evidence: exact source rebuilds; both cartridges execute 180 actual
Genesis Plus GX frames under NTSC-U and PAL, with nonuniform original pixels,
Work RAM progress and bounded finite PCM. The detailed v0.3.5 A/B/C native
regression passes with 28 frame captures. All 169 original-plus-selector
Chromium interface cases pass, with 15 focused cartridge cases (including three
additional recovery cases) also passing. The 12-case actual-core suite passes;
its strengthened default test passes again with local-only GET requests and
subdirectory hosting. Layout7 passes without weakening existing height bounds.
The 26-case manifest/package/static group passes, including rebuilding extracted
cartridge source. Full source/sanitizer checks passed before the final bounded
static-completeness test; final source CI remains required. Local LeakSanitizer
is disabled for container ptrace; ASan/UBSan and CI sanitizer settings remain.

Independent Luna High review approved the implementation and final static
completeness/toolbar/test delta. Findings on symlinks, metadata and validator
parity were fixed and retested. Require every protected-main check and CodeQL
on the final PR head before merge, then verify main CI and package source/tree.
No release, VERSION bump or website deployment is authorized by this task.

## Demo Cart v0.3.5 Source Integration, 29 October 2026

The user approved integration of the experimentally verified original
v0.3.5 cartridge into VRAMpage MD main, plus **future** release packaging.
Use `scripts/build-demo-cart.py` and
`demo-cart/fx-lab/build_fx.py`. The generated 150,564-byte cartridge
must have SHA-256 `89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f`. The source
is tracked but the generated .bin is ignored; the browser default URL,
release package allowlist and local staging must select the v0.3.5 ROM.
Verify in the real Genesis Plus GX with NTSC-U/PAL controls and
frame-identical B recovery. Do not publish, deploy or alter the historical
v0.5.0 browser asset. Complete the full 7-check main ruleset and CodeQL
before merging. YM2612 soundtrack, three-minute sequencing and finale
remain future work; the v0.3.5 cartridge is only an interactive proof.

# Development work queue

## Work RAM Write Inhibit — Integration Checkpoint, 28 October 2026 (UTC)

Authorized bounded follow-up to the reviewed [write-enable research](WORK-RAM-WRITE-ENABLE-RESEARCH.md).
Start from verified main `9b29a5b9380ed4fe760f41015d15c51c53674e1e`
([main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40773753902),
[CodeQL](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40773753398)).
The [implementation guide](WORK-RAM-WRITE-INHIBIT.md) defines runtime/API, UI,
configuration/export, lifecycle and measurable acceptance. Lower/Upper inactive-high
write enables retain old bytes and replace existing RAM faults; there is no new
motherboard selector or pulse engine. FM selection remains research only.

Native/API changes and literal CPU/banked-Z80 actual-WASM tests are integrated.
Independent Luna High review approved source/test deltas through `a6cdb30`.
Root caught unguarded normal-profile references before CI, fixed them in
`7d93422`, and added normal/runtime strict compilation to the shared regression;
the independent reviewer freshly compiled and ran both profiles successfully.

Local source/sanitizer/Node/C checks pass (115 Python tests reported, two
build-dependent classes skipped there). The rebuilt runtime passes 33 actual-WASM
CPU/Z80 cases and the production factory/API assertions. Chromium interface
159/159 plus one new focused orphan-state case, actual-core 12/12 (including
128 mixed-fault cycles), transaction 3/3 and layout 7/7 pass. LeakSanitizer is
disabled locally for container ptrace; ASan/UBSan and normal CI settings remain.

Rebuilt runtime JS SHA-256 is
`e8da1c28303fd3900f35c032ce01802c76d1d041dc8a0d6cd57bdc97ee3af4d0`;
WASM is `8fa2fa0fe6a47890c948ed39a7f095980d9ffde7d4405a88ce07a5f34b8814b7`.
Fresh normal-WASM hash checks and all required PR checks/CodeQL, then verified
main CI, remain integration gates. Cached prior normal hashes are not presented
as a new build verification. VERSION/public v0.5.0, all releases, Demo Cart assets
and McRetro.net remain unchanged. Carry the already reviewed RAM/FM research and
standalone FM characterization probe with this implementation; no FM selector
or other runtime feature is added. Next bounded task after delivery is the
separate staged-MAME-model/replay proof, not another motherboard catalogue.

## Next Fault Research — 28 October 2026 (UTC)

Research branch `research/ram-enables-fm-variants` starts from verified main
`9b29a5b9380ed4fe760f41015d15c51c53674e1e` ([PR #96](https://github.com/NixMcRetro/VRAMpage-MD/pull/96),
[seven main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40773753902),
[four main CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40773753398)).
It carries research reports and a standalone native characterization probe;
application/native runtime behavior and existing interfaces are unchanged.

1. [Work RAM Write Enables](WORK-RAM-WRITE-ENABLE-RESEARCH.md): use the accepted
   PAL two-byte reference. Inhibit means holding active-low `/WE` high; a floating
   cut or forcing low is not the same contract. Keep old upper/lower bytes on
   selected stores, reuse existing hooks and clear/recovery rules, and validate
   literal bytes/counters/checkpoints before any implementation.
2. [FM Models and Engines](FM-VARIANTS-RESEARCH.md): distinguish MAME/Nuked backend
   selection from digital output models and board filters. Native mode-2/3 DAC
   probes show real differences in core outputs, without proving final sound.
   Nuked lacks checkpoint support; MAME model choice is also absent from the
   snapshot. A staged Discrete/Integrated choice needs immutable active-model
   lifetime plus actual-WASM replay proof before exposure.

The standalone FM probe passes strict C11 and ASan/UBSan with identical summaries
(SHA-256 `98bd338cec8355256efd054ab3d507a4d4f69cb7fa2be897f8a5c3eb307c77ef`).
It verifies accepted register/pan programming and literal midpoint outputs.
LeakSanitizer is disabled locally for the known ptrace limitation. This research
is not a new WASM or browser test run; main's previous verified evidence is reused.
Independent Luna High review of reports/probe through `8ce5350` found no blockers;
the coordinator separately inspected the pinned source and reran the strengthened
native probe. A second specialist verified source citations, observed outputs and
checkpoint invariants. Relative documentation links and whitespace checks pass.
No PR was opened or main changed for this research-only checkpoint.

Next bounded implementation candidate: write-only RAM inhibit controls, without
another board catalogue. FM model staging/replay is second. Composite burst/sync
and physical VRAM timing retain the specific receiver/ordering evidence gaps
already documented; do not repeat those broad inventories. Exact NTSC #73 remains
optional. No release, deployment, Demo Cart work or new runtime feature is part of
this research checkpoint. Keep the reports on the research branch for the next
implementation slice instead of opening a trivial documentation-only PR.

## Work RAM Data Lines — Integration Checkpoint, 29 October 2026 (Sydney)

Development source adds runtime-only D0–D15 cut masks, independently
selectable across both byte lanes, using the documented PAL Model 1 VA6.5
two-device circuit as its reference. The existing Work RAM panel switches
between Address and Data;  same-byte bridges reuse the existing
engine. Address masks, data masks and bridge pairs replace one another.
See [scope and acceptance](WORK-RAM-DATA.md).

Exact NTSC VA6 population/routing in [#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73)
is now optional follow-up, not a development gate. User-supplied PAL/USA board
photos support two-device populations but do not establish every trace or
part pinout. Add a physical model selector only when another evidenced model
has meaningful implemented differences; region selection remains separate.

Started from verified main `8733a5594a243a48c5fd9cd6d80760106ee99dad`
([seven required jobs](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40697665333),
[four CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40697664612)).
Implementation through `987b9a0` passed independent Luna High review, including
native byte-lane semantics, strict API validation, lifecycle, packaging and
schema-5 imports of versions 1–4. Local source/sanitizer/Node/C checks pass
(115 Python tests reported; two build-dependent classes skipped in that command).
The actual-WASM production profile test separately passes CPU byte/word/longword,
DMA/mirror/recovery cases and exact normal-core hash checks. Chromium interface
153/153, actual-core 12/12 (including 128 mixed-fault cycles), transaction 3/3
and layout 7/7 pass. LeakSanitizer is disabled locally because it aborts under
container ptrace; ASan/UBSan remain enabled and CI retains its normal settings.

Integration still requires all required PR checks and CodeQL, then verified main
CI; consult the PR and final delivery checkpoint for those results. Runtime JS
hash is `8443dbcda84eec872b6f262d14deb4dc54c768bbd0cf38d6f2277399b3339450`;
WASM is `a7f7175ad6511082e882ce53beb6a430918f12b526c65514ac91444775bc0682`.
Normal/fallback hashes remain unchanged. No VERSION bump, public release or
website deployment. Preserve all releases and original Demo Cart assets;
PRs #93/#94 are separate work. Next: use concrete cartridge feedback for the
candidate, and add physical-model choices only when another evidenced model
has meaningful implemented differences. Exact NTSC mapping remains optional.

## Demo Cart Merged; Hardware Follow-Up — 28 October 2026 (Sydney)

[PR #90](https://github.com/NixMcRetro/VRAMpage-MD/pull/90) merged as
`a8ba05f2133097fea80a689d38e7c74dff3640ce`, tree
`33ef378ac8e0e30bbd348e69f3ebb33f74a18a3d`, exactly matching tested head
`8c5539586347b2d4cebfd5072deedf9b63cc0a73`. All seven required
[PR jobs](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40692733654) and
[main jobs](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40693866935)
passed on the first attempt; all four CodeQL analyses passed on both
[PR](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40692727011) and
[main](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40693866567).
Independent Luna High review approved the complete integration at `8c55395`.
The staging path correction passed the source/sanitizer suite and an isolated
local fixture showing the staged destination in the review list, without commits.

The user explicitly superseded the earlier merge hold and deferred full Demo
Cart art/audio/PAL/NTSC scene/fault acceptance until around v0.6.0. No new scenes,
version bump, release replacement or McRetro.net deployment was performed.
[Verified main browser download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40693866935/artifacts/12819097164).

The [manual/ConsoleMods follow-up](SEGA-MANUAL-EVIDENCE.md) resolves the PDF access
blocker, qualifies Model II VA0/VA1 mappings and records source inconsistencies.
Keep #73 open: target NTSC Model 1 VA6 RAM markings and matching routing remain
unverified. Research changes are documentation only; independent review and
required PR/main checks remain gates for that bounded follow-up. Revisit release
candidate work afterward; do not repeat completed region/RAM/recovery work.

## Draft PR #90 CI Repair — 28 October 2026 (Sydney)

The user requested correction of actual-core tests that assumed an empty
console before the built-in Demo Cart existed. Start from PR head `97019c6`,
merge verified main `32970b1` without rewriting history, and fix the shared
manual-cartridge fixture. Preserve the genuine default auto-load test, race and
missing-demo cases, disabled-control assertions and original asset hashes.

The bounded fixture change uses the existing session preference before navigation,
with accepted-ROM identity waits for affected loads. Production app/core, artwork,
original ROM/source kit, VERSION, releases and McRetro.net remain unchanged.
Local Chromium actual-core 12/12, transaction 3/3, source/sanitizer/Node/C checks
and local packaging pass. Independent Luna High review of `f19c27f` found no
blockers. All required fresh PR CI/CodeQL remain the completion gates. Keep PR #90 draft: its
[design guardrail](DEMO-CART-DESIGN.md#development-order-and-release-guardrails)
requires explicit user approval before merge or website deployment. This request
repairs CI and does not remove that hold or add demonstration scenes.

## Supplied Manual Evidence — 28 October 2026 (Sydney)

The user authorized working with the supplied Sega developer/service manuals
and MiSTer HDL. The [evidence review](SEGA-MANUAL-EVIDENCE.md) records visually
checked errata, a qualified NEC PAL VA6.5 RAM map, Model 2 memory/encoder
variations and fresh pinned HDL cross-checks. Three oversized PDFs
remain uninspected because the materializer limit and proxy block their downloads;
the report names these files without inferring their content from filenames.

Commit `dea1685` adds literal actual-WASM Auto/header-mask checks from Sega
Bulletin #31; these pass using the unchanged verified runtime and normal core.
Production code, native artifacts, VERSION, releases and McRetro.net are unchanged.
Independent review and the required PR/main CI/CodeQL remain integration gates.

Keep #73 open: the supplied PAL VA6.5 reference does not prove the selected
NTSC Model 1 VA6's fitted devices or routing. Do not implement a cosmetic VA
selector or repeat completed region/recovery/RAM work. Next: complete this bounded
review/integration and retain exact source/page and GitHub evidence.

## Region Selection Verified — 28 October 2026 (Sydney)

[PR #89](https://github.com/NixMcRetro/VRAMpage-MD/pull/89) merged as
`ef88ae17067c256da9c9e4fc61c2592e1e53135d`; its tree
`76ba18d15ef81eb5036b997114f9224de597a891` exactly matches tested head
`1eb3091ea73b4a2695a0c13173e974d4feba892f`. All seven required
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40654392270)
and [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40657588413)
passed, including Chromium/Firefox/WebKit interface and packaged actual-core
coverage. All four CodeQL analyses passed on both the
[PR](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40654387164) and
[main](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40657588967).
The active main ruleset was satisfied without bypass. No PR remains open.

Development source now stages Auto/NTSC-U/NTSC-J/PAL Europe/Japan PAL choices,
with NTSC-U unchanged by default. Load ROM/Clean Restart applies the request;
CPU Reset retains the active region and checkpoint. Native cadence and viewport
drive display and requested/effective machine identity in exports/comparison.
Circuit files remain fault-only. The normal core has no region API and retains
its exact existing JS/WASM hashes. See [the region guide](REGION-PROFILES-PLAN.md).

Luna High authored the native runtime; independent Luna High reviews through
`e176a4b` found no blockers. Local source/sanitizer checks pass (114 Python tests
reported; two build-dependent classes handled separately), fresh actual-WASM
build/profile tests2/2, Chromium interface145/145, actual-core11/11,
transaction3/3 and layout7/7. Original cartridges exercise software-visible
region bits, nonzero video/PCM/RAM, native clock/geometry/audio bounds, default
parity, held-input release, checkpoints and exact eight-native-frame pulses.
The existing 128-cycle mixed-fault workload also passes unchanged.

[Download the development browser build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40657588413/artifacts/12803320191)
(artifact12803320191; expires 27 November 2026). It includes matching source and
build information for the verified main commit. No VERSION change or public
release replacement; all18 release records and asset identities are unchanged.
McRetro.net was not modified or deployed. Physical VA profiles, #73's matching
board map, commercial-game compatibility and audible acceptance remain unverified.

Next: review the development build with available cartridges and concrete
compatibility feedback. Do not repeat completed security/Actions/RAM/recovery
work or infer physical profiles from a region choice. This final delivery
checkpoint is on `maintenance/region-delivery`, avoiding another trivial
source CI cycle; the implementation and all tests are already on verified main.

## Actions Upgrades Verified — 28 October 2026 (Sydney)

The five requested major Actions updates are merged individually. Each branch
was tested with current main; all seven required PR checks and all seven
post-merge main checks passed for each upgrade. Each merged tree matched its
tested head. Final main is `b4b3f90ddc4acef5d40147244df3071fb0cd6300`.

| PR | Upgrade | Tested Head | PR CI | Main CI |
| --- | --- | --- | --- | --- |
| [#84](https://github.com/NixMcRetro/VRAMpage-MD/pull/84) | setup-node 4 → 7 | `bacadfbf6566460c587246a3661b38beda5c283e` | [40635690666](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40635690666) | [40636320206](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40636320206) |
| [#85](https://github.com/NixMcRetro/VRAMpage-MD/pull/85) | download-artifact 4 → 8 | `9c33b628f75f26bd8bf9c5ad676751efc7832bcf` | [40637060996](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40637060996) | [40637794655](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40637794655) |
| [#86](https://github.com/NixMcRetro/VRAMpage-MD/pull/86) | checkout 4 → 7 | `87f0795f8373b46173c222e9f5b1c4bd02c01c38` | [40638008106](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40638008106) | [40638693076](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40638693076) |
| [#87](https://github.com/NixMcRetro/VRAMpage-MD/pull/87) | upload-artifact 4 → 7 | `cdb357023d1804f187a92a82d7704404076ff9a6` | [40639413882](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40639413882) | [40640071248](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40640071248) |
| [#88](https://github.com/NixMcRetro/VRAMpage-MD/pull/88) | setup-python 5 → 7 | `4f91c22a4130229ad0d9cbe3faa01bab924dbe1c` | [40640721423](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40640721423) | [40641311776](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40641311776) |

Independent GPT-6 Luna High review inspected exact diffs, release/migration
notes and upstream action metadata. No compatibility or permission blocker was
found. Explicit Node 22, Python 3.12, Ubuntu 24.04, artifact names/paths/retention
and archived-upload semantics remain unchanged. The final snapshot changes only
four workflow files; application code, emulator pins and VERSION are unchanged.

All 18 release records and attached asset identities match the preserved
post-curation snapshot. Release-writing workflows were reviewed but not run.
McRetro.net was not accessed or modified during this VRAMpage-only task. No PRs
remain open at this checkpoint. #73 still needs matching board evidence.

Two automatic approval reviews used stale pending-package evidence and blocked
an attempted continuation/merge. Fresh explicit API evidence showed all seven
jobs complete successfully; the authorised retries then proceeded. No check was
bypassed or weakened. The final CLI watcher lost annotation access (401), while
CI continued; connected GitHub API monitoring verified final success. Logs,
merge identities and release comparison are under `/workspace/scratch/actions-upgrades/`.

Next: concrete stability feedback or the development candidate/release decision;
do not repeat finished experiments or create another infrastructure-only sequence.
This final checkpoint is on `maintenance/actions-delivery` without another
trivial documentation-only CI cycle.


## Dependency Maintenance Scope — 28 October 2026 (Sydney)

The user authorised useful fixes while GitHub security-alert access is being
resolved. This slice adds scheduled Dependabot updates for the declared Python
browser-test requirement and GitHub Actions only. Weekly checks group compatible
Action updates; major updates remain separate. Repository security toggles and
GitHub App permissions remain administrator settings, outside this file.

Acceptance: validate the configuration against the published schema and actual
manifest paths, obtain independent review, pass local source checks and all seven
PR/main jobs, then verify the merged tree. Do not change emulator code, dependency
pins, VERSION, releases, archived evidence or McRetro.net from this repository.
The separately authorised website maintenance branch is tracked outside this
repository. Preserve the verified mixed-fault evidence below.

Configuration schema and manifest-path checks passed. Independent GPT-6 Luna
High review found no configuration/workflow blocker; the website wording was
clarified to avoid claiming unverified security enablement. Local
`bash scripts/test.sh` passed: 114 Python tests reported, two unchanged
build-dependent classes skipped, plus native sanitizer/Node/C suites. Runtime
source, pins, VERSION and release assets remain unchanged. GitHub PR checks,
exact-tree merge and all seven main checks are the remaining integration gates.

## Mixed-Fault Stability Pass Verified — 27 October 2026

[PR #81](https://github.com/NixMcRetro/VRAMpage-MD/pull/81) merged as
`90eb7ff95f9793da68819f5e836ce504d93ed848`; its tree exactly matches checked
head `b34631f03686d3920c935a257d1a587885e02dd2`. All seven
[fixed PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40483003512)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40483950982)
passed, including Chromium/Firefox/WebKit logic/layout, fresh native/WASM tests
and extracted-package runtime/fallback/audio/control checks.

The actual-core workload completes two full warm-ups, 128 measured cycles,
eight measured lifecycle boundaries and exactly 1,159 native frames/ticks.
Original generated code performs eligible Work RAM/Z80/PSG/FM writes with nonzero
baseline pixels/PCM. It combines independent faults, exact eight-frame release,
paused CPU Reset RAM/PCM preservation, held-input/contact cleanup, changed-image
checkpoint replay, rejected-file retention and restart/replacement invalidation.
Both automatic recovery preferences are Off in the test; faults are not silently
rescued. No production emulation defect was reproduced.

Local and packaged PR Firefox/WebKit metrics matched: 33,554,432-byte warmed
WASM heap, one module and AudioContext, 1,160 real audio sources created, peak 12
connected (limit 16), final 0, finite PCM. Main repeats the same acceptance gates.
[Initial evidence](experiments/mixed-fault-endurance-2026-10-27.json) and
[strengthened frame/count evidence](experiments/mixed-fault-endurance-v2-2026-10-27.json)
retain exact historical test-source hashes; both core hashes match merged builds.
A heap plateau does not prove absence of JS/allocator-internal leaks. Events are
synthetic, not OS tab/background or physical-controller acceptance.

Independent GPT-6 Luna High review reproduced the strengthened run and found no
blockers. The first [PR run](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40481597734)
failed both packaged jobs before this workload: default Playwright RAF polling
waited on the test's controlled RAF queue. Timer polling corrected both startup
waits without timeout/assertion/workload changes; independent review confirmed it.
The fresh full run above passed. Local WebKit attempts stopped at missing host
dependencies/browser launch; genuine packaged WebKit passes on provisioned CI.

Local validation: source/native sanitizer/Node/C suites passed (114 Python tests
reported, two unchanged build-dependent classes skipped), ten actual-core cases
passed and changed assertions/readiness were rechecked in focused runs. Seven
layout cases plus eight new-control keyboard/theme/viewport cases passed; active
RGB text contrast measured 9.55:1. All 331 pre-merge relative Markdown paths resolved.
The only production change removes the obsolete [0] from Reconnect All; 0 still
cycles chip targets. [Draft candidate notes](DEVELOPMENT-CANDIDATE.md) collect
post-v0.5.0 features and a short review/publication checklist without selecting
or publishing a release.

The [verified development browser download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40483950982/artifacts/12724098229)
identifies the exact merge above; all 261 tracked files match. Checksum, root/site
metadata, corresponding source/notices, executable launcher and ROM-free contents
passed inspection. ZIP SHA256:
`eca2e3b6550afa59952f065c10e1ee4b9f5a41835a14b323fba86559f609d1c7`
(3,610,901 bytes; 758 entries). Runtime and normal fallback JS/WASM hashes remain
unchanged. All 18 public release records/asset identities match the starting
snapshot; VERSION and McRetro.net were not changed or deployed.

A bounded GitHub search found a PAL recreation, not matching NTSC VA6 evidence;
#73 stays open. This was not an exhaustive web or physical investigation. No
new audible, real-game, native desktop or physical electrical acceptance is
claimed. Logs/probes are under `/workspace/scratch/mixed-soak/`.
Next: address concrete development-build regressions and retain #73's board
boundary. Do not repeat completed experiments or start another hardware model
without a bounded oracle. This final record is preserved on
`experiment/mixed-soak-delivery` without a trivial documentation-only CI cycle.

## VRAM Export Availability Verified — 27 October 2026

[PR #80](https://github.com/NixMcRetro/VRAMpage-MD/pull/80) merged as
`528cc2778e33499fe4b2d35cbae39606ca9ba949`; its tree exactly matches checked
head `687d07a4e466d8968157639ac4d360036d7f79a1`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40462545301)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40463216175)
passed, including three-browser logic/layout, fresh native/WASM tests and
extracted-package runtime/fallback/audio/control checks.

The bounded stability audit reproduced a false export observation: transaction
model 2 with AD2↔AD5 stayed active, but a null/throwing optional getter produced
an available frame-model-1 record via the UI compatibility fallback. The
six-line exporter fix reads runtime observations directly; unavailable metadata
now compares Unknown while tracked contacts and the UI/recovery fallback remain
unchanged. No native, renderer, schema, version or hardware-model change.

Independent GPT-6 Luna High review of `1ab067d` found no blockers and separately
passed the focused Chromium regression and Node comparison tests. Final head
adds checkpoint documentation only. The regression failed before the fix on
null/throw and now passes healthy/null/throw/absent cases, including unchanged
native settings/ticks/recovery/starts and paused state. Full local source/native
sanitizer/Node/C suites passed (114 Python tests reported, two unchanged
build-dependent classes skipped locally), as did all 139 Chromium logic cases.
All 316 relative documentation links resolved before delivery. Logs/probes:
`/workspace/scratch/fault-stability/`.

The independent lifecycle audit found no confirmed cartridge/control defect.
Its suspected stale Z80 controls were disproved by the existing transitive
refresh and a Chromium post-mutation-start-failure probe. A forced canvas draw
exception was synthetic; no normal-use failure was established and no speculative
handling was added. Existing native/RGB performance evidence remains unchanged.

The [verified development browser download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40463216175/artifacts/12715258729)
contains exact merge `528cc2778e33499fe4b2d35cbae39606ca9ba949`; all 258 tracked
files match. Checksum, root/site metadata, corresponding source/notices,
executable launcher and ROM-free contents passed inspection. ZIP SHA256:
`49967ad23fb0b5911100f6aef24f48fda764162390f5c2dd90bb2270bc6ccff4`
(3,598,698 bytes; 755 entries). Both runtime and normal fallback JS/WASM hashes
match the preceding verified build. This Actions package includes current Z80
RAM/RGB work and the reporting fix; public release assets were not replaced.

All 18 release records/asset identities match the starting snapshot. VERSION and
McRetro.net were not changed or deployed. No new physical, audible or native
desktop validation is claimed. No other confirmed software blocker emerged.
Next: investigate concrete regressions from the development build; #73 still
requires matching NTSC VA6 board evidence. Do not repeat completed research or
add another hardware model without a bounded oracle. This final checkpoint is
preserved on `experiment/fault-stability-delivery` without another
trivial documentation-only integration cycle.

## RGB Encoder Inputs Verified — 27 October 2026 (Sydney)

[PR #79](https://github.com/NixMcRetro/VRAMpage-MD/pull/79) merged as
`5e90aacd15b85254a4de39ba006ffd179e91e963`; its tree exactly matches checked
head `711c15989d972bfef5c408532484963039e55bbb`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40459211948)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40459878011)
passed, including fresh native/WASM builds, Chromium/Firefox/WebKit logic/layout
and extracted-package runtime/fallback/audio/control checks.

The [off-by-default RGB contacts](RGB-ENCODER-INPUTS.md) operate only on copied
canvas pixels: independent cuts, one joined pair, explicit black termination and
equal source impedances using normalized byte-code voltage proxies. Raw Output
bypasses them; CPU Reset retains them; Clean Restart clears them. Configuration
v4 imports v1/v2/v3 with RGB off; exports/comparison, sixth-domain disconnect and
checkpoint handling are included. Native CPU/RAM/audio code is unchanged.

Independent GPT-6 Luna High review of implementation/test head `18d0586` found
no concrete blockers; the final head adds checkpoint documentation only. Local
source/native sanitizer/Node/C suites passed (114 Python tests reported, two
unchanged build-dependent classes skipped locally), as did 138 Chromium logic,
seven layout, nine actual-core and three transaction/handoff cases. Literal
palette colours and byte-identical native frame, Work RAM, available Z80 RAM and
stereo PCM prove paused output isolation on runtime/fallback profiles. The first
full core run's two stale expected schema/domain lists were corrected to assert
the complete contract; its full repeat passed without weakened assertions.

The [fixed five-pair display record](experiments/rgb-encoder-display-performance-v1.json)
passes inactive median/p95 ratios 1.0/1.0 (limit 1.05) and active p95 0.318 ms per
320×224 frame (limit 1 ms). All recorded input hashes still match merged source.
All 311 relative Markdown links resolve. Logs and original synthetic UI inspection
are under `/workspace/scratch/rgb-encoder/`.

The [development browser download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40459878011/artifacts/12713773822)
contains the exact merged commit above: all 258 tracked files match. Its checksum,
root/site metadata, corresponding source, notices, executable launcher and
ROM-free contents were verified. ZIP SHA256:
`ac5e91d68bb6a0aa6d6b025d5f290a1c66cb48fd9fc304fa6af749d209aa3628`
(3,595,611 bytes; 755 entries). Runtime and normal fallback JS/WASM hashes remain
identical to the preceding verified build. This Actions download is development
source, not a replacement public release; it includes both Z80 RAM and RGB work.

All 18 release records/asset identities match the starting snapshot. VERSION and
McRetro.net were not changed or redeployed. No measured physical encoder match,
audible result or native desktop acceptance is inferred from synthetic Linux
checks. Composite, sync and mono faults remain outside this model.

Next: use this development build for concrete browser feedback and fix reproduced
regressions. #73 still needs matching NTSC VA6 board evidence; do not repeat
completed RAM/encoder research or add another analogue model without a bounded
oracle. No software delivery blocker remains. This final record is preserved on
`experiment/rgb-encoder-delivery` without another documentation-only CI cycle.

## Video Encoder Research Verified — 27 October 2026 (Sydney)

[PR #78](https://github.com/NixMcRetro/VRAMpage-MD/pull/78) merged as
`fbfe46a1007abd77141226c34421329a74f46592`; its tree exactly matches reviewed
head `136127d467f5f94859a544a5831d8ca48e42e261`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40421292278)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40422107154)
passed. The diff contains six Markdown files only, including the preceding
verified Z80 delivery checkpoint. Application code and VERSION are unchanged;
all 18 release records/asset identities match the starting snapshot. McRetro.net
was not modified or deployed.

The [CXA1145 report](VIDEO-ENCODER-RESEARCH.md) records Sony manufacturer signal
text, CXA1645 differences, Sega-listed Model 2 alternatives and the current
32-bit RGBA output boundary. Analogue RGB contacts are the smallest candidate;
composite subcarrier/sync require timing and receiver assumptions. A distinct
mono-buffer path is documented. This is research, not an implemented feature,
feature-freeze exception or physical NTSC VA6 validation.

Independent GPT-6 Luna High review found no major blocker; its exact BFOUT/YCLPC
pin-function correction is applied. Source checks passed (114 reported tests,
two unchanged build-dependent classes skipped locally), and all 302 relative
Markdown paths resolve. Initial default-sandbox loopback/LSan failures are
retained; the network-enabled runner passed without weakened checks. Logs:
`/workspace/scratch/video-encoder-research/`.

No board, waveform, listening or proposed encoder-model experiment was performed.
Primary text was inspected; PDF screenshot markers did not supply inspectable
images, so independent visual validation is not claimed. Future model tests are
specified, not reported as passing.

Next: await the user's Z80 RAM build review and address concrete stability reports.
Encoder implementation needs a separate bounded decision; do not automatically
add RGB/composite/mono faults. #73 still needs matching NTSC VA6 board evidence.
This final queue/status record is preserved on `experiment/video-encoder-delivery`
without another documentation-only integration cycle. No research-delivery blocker
remains; physical/model calibration remains outstanding.

## Z80 RAM Write Verified — 27 October 2026 (Sydney)

[PR #77](https://github.com/NixMcRetro/VRAMpage-MD/pull/77) merged as
`1b464a90daa1b8ba8d9ff321475ccb4dc8ff865c`; its tree exactly matches reviewed
head `a94e87c80d3a40873318f47960ccc624d7ceeb63`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40418074759)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40418745966)
passed, including Chromium/Firefox/WebKit logic/layout, compiled-WASM variants,
normal-core hash checks and packaged Firefox/WebKit audio/control/fallback tests.

The [off-by-default Z80 RAM write bridge](Z80-RAM-WRITE-BRIDGE.md) is integrated
with compact controls, exact owner counters, configuration v3 (v1/v2 imports),
comparison, verified disconnect/recovery and checkpoints. Native ownership,
read/fetch paths and sound-chip reset wiring are unchanged. Independent GPT-6
Luna High specialist review found no remaining blocker; actual BigInt ABI and
unsigned-boundary coverage closed its test request. Native ASan/UBSan/LSan passed
without disabling leak detection. Original generated cartridges verify stores,
ownership, sound-driver input/finite PCM, instruction corruption and lifecycle.

[Inactive-store evidence](experiments/z80-ram-inactive-performance-v1-summary.json)
passed the fixed five-pair gate: median ratio 1.00618 and p95 ratio 1.03573,
limit 1.05. The main package's runtime hashes match those measured binaries.
The normal fallback hashes remain unchanged. This is one synthetic workload.

The [development browser download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40418745966/artifacts/12697036290)
contains built runtime/fallback cores and corresponding source. Its embedded
commit is the merge above; all 252 tracked files match that source. ZIP SHA256:
`628181bbca355fe89a5d164bcad4582a4a47ef4865169588c2f53fead561f63d`.
The package is ROM-free. All 18 release records/assets match the starting snapshot,
including protected v0.4.1/v0.5.0. VERSION, published artifacts and McRetro.net
were not changed or redeployed; this feature is development source only.

CI caught an existing Firefox test race: counting sources before asynchronous
suspension completed. The reviewed test-only fix starts counting after suspension,
asserts suspended state at both endpoints and retains the original buffer bound.
A delayed-suspension probe reproduced the old failure and passed with the fix on
follow-up. Its earlier unrelated startup-lead failure, failed CI and original
performance samples remain retained; no assertion or sanitizer was weakened.
Evidence and package verification: `/workspace/scratch/z80-ram-write/`.

Next: return to concrete stability/compatibility reports under the feature freeze.
Do not repeat completed research or add arbitration/physical VRAM timing without
a separately scoped oracle and decision. #73 still needs matching NTSC VA6 board
evidence. No implementation blocker remains. Physical-board, commercial-gameplay,
audible listening and native macOS/Windows checks were not performed.
This final record is committed on `experiment/z80-ram-delivery` to preserve the
verified main commit and avoid an unrelated documentation-only integration cycle.

## Hardware Research Verified — 27 October 2026 (Sydney)

[PR #76](https://github.com/NixMcRetro/VRAMpage-MD/pull/76) merged as
`44627eba37b410c05437731335ce5e38b43a2417`; its tree exactly matches reviewed
head `85077a3f90054de8016e5686fc7dfcaacffc4459`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40397822846)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40398771476)
passed. Local source111 passed (two unchanged build-dependent classes skipped),
existing actual-WASM Z80 PSG/FM scripts passed, and 125 relative links resolved.
Independent GPT-6 Luna High source/table review found no remaining blocker;
primary PDF visual checks were performed by the coordinator, not independently
repeated by the reviewer. Proposed-model fixtures were specified, not implemented.

- [#75](https://github.com/NixMcRetro/VRAMpage-MD/issues/75) closed as research
  completed: [access/reset map and bounded write-only Z80 RAM proposal](Z80-RAM-RESEARCH.md).
  Arbitration injection remains deferred.
- [#74](https://github.com/NixMcRetro/VRAMpage-MD/issues/74) closed as research
  completed: [physical component / pinned HDL / emulator comparison](VRAM-TIMING-RESEARCH.md).
  Physical/raster implementation awaits a separate timing oracle and scope.
- [#73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73) stays open:
  [candidate HM65256B pins and PAL reference](VA6-RAM-VALIDATION.md) are recorded;
  matching NTSC VA6 device, lane and net evidence remains unverified.

GitHub readback confirms all three issue bodies/states and research evidence
links. All 18 release records and asset identities/digests/timestamps match the
starting snapshot, including protected v0.4.1. No runtime, version, release,
ROM or McRetro.net changes. Evidence: `/workspace/scratch/hardware-research/`.
Next: concrete compatibility reports, or a separately scoped implementation of
the documented Z80 RAM candidate. Do not repeat the completed research or claim
physical validation; #73 needs matching board evidence, not more gameplay tests.

## Hardware Research Checkpoint — 27 October 2026 (Sydney)

The user authorized independent work on #73–#75, starting with the easier
bounded Z80 scope. Research is based on unchanged main
`1dc30d654d156653e5fae49cb1f667355e440131`, the existing pinned core and
primary manufacturer/Sega scans. Historical issue-housekeeping checkpoints
are carried forward without repeating delivered RAM/VRAM/audio experiments.

- [Z80 RAM research](Z80-RAM-RESEARCH.md): ownership/access/fetch/reset map,
  bounded write-only address-alias proposal, counters/lifecycle and future
  acceptance tests. Defer arbitration injection; no runtime feature added.
- [VRAM timing research](VRAM-TIMING-RESEARCH.md): HM53461 component evidence,
  MiSTer `adc0c42cfb1fa5d484cc8566767f7d68982bc44a` comparison, identified
  FIFO/render/serial gaps and fixtures. No physical timing implementation.
- [VA6 validation](VA6-RAM-VALIDATION.md): candidate HM65256B device pins
  and PAL VA6.5 topology; requested NTSC VA6 still unverified. Keep #73 open.

Existing actual-core Z80 PSG/FM tests passed; proposed-model tests are specified,
not executed against a new model. Independent Luna High research review found
no blocker in Z80/VRAM reports; its DMA function/citation correction is applied.
VA6 table/qualification review also found no blocker; primary PDF visual checks
were performed by the coordinator, not independently repeated by the reviewer.
Final source checks, document link audit and PR/main CI are pending at this
committed checkpoint. Evidence: `/workspace/scratch/hardware-research/`.
Preserve all public releases and McRetro.net. After integration, close #74/#75
as research completed with evidence links, leaving implementation a separate
feature decision and #73 awaiting matching board evidence.

## Milestone Issue Housekeeping Completed — 27 October 2026 (Sydney)

After the user approved the audit recommendation, the remaining work was split
into three focused GitHub follow-ups before the old trackers were closed:

| Delivered Milestone | Remaining Work |
| --- | --- |
| [#1 Work RAM](https://github.com/NixMcRetro/VRAMpage-MD/issues/1), closed | [#73 Verify Model 1 VA6 Work RAM Devices and Pin Mapping](https://github.com/NixMcRetro/VRAMpage-MD/issues/73) |
| [#2 Transaction VRAM](https://github.com/NixMcRetro/VRAMpage-MD/issues/2), closed | [#74 Research VRAM Serial Access and Scanline Timing](https://github.com/NixMcRetro/VRAMpage-MD/issues/74) |
| [#3 FM/PSG Audio](https://github.com/NixMcRetro/VRAMpage-MD/issues/3), closed | [#75 Research Z80 Sound RAM and Bus Arbitration Faults](https://github.com/NixMcRetro/VRAMpage-MD/issues/75) |

Each original title/body is preserved, with an appended resolution linking the
delivered implementation, test/evidence records and its follow-up. Closures mark
the delivered software milestones; physical mapping, precise timing and the
separate Z80 RAM/arbitration fault models are not represented as completed.
The new issues have explicit scope, sources and acceptance criteria, with no
implementation, release-version or priority commitment beyond the current plan.

GitHub readback verified all six bodies/titles/states and the three new open
issues. No comments were posted. Source behavior and releases were unchanged;
physical experiments were not rerun. The prior source/main CI evidence remains valid. Drafts and
before/after metadata are retained in `/workspace/scratch/issue-housekeeping/`.
Next: use #73–#75 for the remaining optional research; do not repeat the delivered
RAM/VRAM/FM/PSG milestones or displace stabilization without a new scoped decision.

## README Polish and Issue Audit Verified — 27 October 2026 (Sydney)

[PR #72](https://github.com/NixMcRetro/VRAMpage-MD/pull/72) merged as
`1dc30d654d156653e5fae49cb1f667355e440131`; its tree exactly matches reviewed
head `0df478b2626e14b9c3bb663b9cc7f34c131d4243`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40382903048)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40383854322)
passed. GitHub's Markdown renderer accepted the heading icons, native test-ROM
Tip and chip table. All existing links, credits and terms are retained; the
26 focused documentation/versioning/curation checks and independent review passed.
No app, version, release, asset, curator or website changes were made.
The CLI watcher hit a credential error on an annotations lookup; the connected
GitHub app independently confirmed the completed main run and all seven jobs.

The user then requested a read-only audit of the three open milestone issues:

- [#1](https://github.com/NixMcRetro/VRAMpage-MD/issues/1): Work RAM access faults,
  controls/diagnostics and the bounded attract-mode divergence criterion are
  delivered. [Recorded proof](RAM-STATUS-FOLLOWUP.md) preserves matching demo input
  phase with sustained player-trajectory differences. Verified VA6 physical
  SRAM-device/pin mapping remains unfulfilled; no guaranteed visual wall-sticking
  or electrical equivalence is established.
- [#2](https://github.com/NixMcRetro/VRAMpage-MD/issues/2): Logical per-access VRAM
  transactions, CPU/Z80/DMA coverage and cache coherence shipped in v0.3.0 via
  [PR #43](https://github.com/NixMcRetro/VRAMpage-MD/pull/43). Frame mode is an
  intentional retained fallback/default. Physical serial-access waveforms and
  cycle/beam timing remain outside the documented model.
- [#3](https://github.com/NixMcRetro/VRAMpage-MD/issues/3): FM/PSG pre-synthesis
  input faults and both CPU write routes shipped in v0.4.0 via
  [PR #46](https://github.com/NixMcRetro/VRAMpage-MD/pull/46). Actual Z80 audio-write
  tests remain in current CI. Z80 sound-driver RAM/arbitration fault models remain
  explicitly deferred; physical/cycle fidelity and universal recovery are unproven.

Recommendation: retire the delivered software-milestone wording and track any
remaining VA6 validation, serial/timing research or Z80 extensions as focused
follow-ups. Do not reimplement the shipped RAM/VRAM/FM/PSG work. No issue was
commented on, edited or closed. The audit reused pinned evidence/current code and
passing CI; it did not repeat commercial-cartridge or physical experiments.
Evidence/logs: `/workspace/scratch/readme-visual-polish/`.

## Repository Cleanup Verified — 27 October 2026 (Sydney)

[PR #71](https://github.com/NixMcRetro/VRAMpage-MD/pull/71) merged as
`1cba1f7e1fd56ea06290e3785d1b0bb5da8ea9e7`; its tree exactly matches reviewed
head `65405e89a39795da5643b691fdd46ce49f94a9cc`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40376224647)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40377355038)
passed. The [metadata-only curation](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40377354871)
also passed after complete remote preflight.

The README is reduced from 1,444 to 464 words and leads with the live app,
current v0.5.0 download, free original colour-test ROM/source and upstream credits.
Detailed instructions remain linked. No ROM, generated core, application change
or new release was introduced; McRetro.net was not modified by this cleanup.

The user chose to keep all 18 releases and correct historical latest links.
Post-curation comparison confirms every release/tag, asset ID/hash/size/timestamp
and original publication date is unchanged. Fourteen historical bodies match the
approved notes. Protected v0.3.0/v0.4.0/v0.4.1/v0.5.0 titles, bodies and metadata
update timestamps are unchanged; v0.5.0 remains Latest without an extra write.
Original note archives and experiment-pinned v0.2.6/v0.2.7 packages are preserved.

Local checks passed all 111 Python tests (two unchanged SDK/vendor classes
skipped), existing JavaScript/native/sanitizer checks and relative-link validation.
Independent README/credit review and coordinator curator review found no blocker.
Snapshots and logs: `/workspace/scratch/repository-cleanup/`.
GitHub's integration rejected the optional repository About-sidebar edit with 403;
its description/homepage settings remain unchanged. No extra permission is needed
for the completed README, PR or release-note work. Next: handle concrete
compatibility reports, preserving public artifacts and avoiding minor doc releases.

## v0.5.0 Published — 26 October 2026 (Sydney)

[VRAMpage MD v0.5.0](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.5.0)
is public with exact title, immutable tag/source commit
`e9f366fb3985f11430d353c3b2589f076ff93128` and two assets:
[Browser ZIP](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip)
and [SHA256SUMS.txt](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt).
All four [release workflow checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40302794303)
passed after all seven candidate PR/main checks. Downloaded release ZIP has 716
unique paths, exact tagged source/version/UI, runtime/fallback/source/notices and
no ROMs. Manifest and public asset digests match: ZIP
`6024ad1701d1cb58dc5da16ce4ae51db4fd03de7e9e1a6e26b3e6aff27ef0aad`;
checksum asset `5d632ba923c05a94182975bd3bd06cfe6ebd491f7a11b7e0aa115651f2bd856d`.

Public notes replace candidate wording while preserving the exact tagged package;
the package's candidate-stage docs remain provenance. Post-publication docs now
link permanent downloads, label historical releases correctly and retain all
native-platform coverage limits. Independent GPT-6 review found no publication
blocker; its wording/table cleanup requests were applied. Source106 passed
12.431s (two unchanged SDK/vendor classes skipped); publication-docs PR/main CI
remain the final repository integration gate.

The draft-tag API endpoint returned404 during a redundant final metadata lookup;
the shell continued to publication. Tag/source/downloaded manifest had already
passed; public metadata and both remote digests were immediately checked against
the downloaded files and match. Future dependent shell actions must stop on error.
No release asset was replaced or retagged. Public v0.4.1 name, target, timestamp
and both digests remain unchanged; McRetro.net was not modified or deployed.
Evidence: `/workspace/scratch/v050-release`.

Next: finish publication-docs integration; then respond to concrete compatibility
reports without repeating completed proof work or publishing minor intermediates.
Native Windows/macOS launch, physical pads and universal gameplay are not claimed.

## PR #68 Verified Delivery — 26 October 2026 (Sydney)

[PR #68](https://github.com/NixMcRetro/VRAMpage-MD/pull/68) merged as
`32b7096beaef48cc3f155a0f3a8606ee211bbd79`; tree exactly matches reviewed/tested
head `b514cc264f7ff96cc16cb2f9cad995edf0ab4b7c`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40288935242)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40289738383)
passed. [Runnable build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40289738383/artifacts/12635426870).

Chip bodies read SRAM and VRAM; headings read SRAM (Work RAM) and VRAM (Video RAM).
Only two HTML labels changed. Identifiers, memory/recovery logic and release
inputs are unchanged. Independent GPT-6 review found no blocker. Local source106
passed (two unchanged SDK/vendor classes skipped), Chromium display7 passed.
Canonical runnable checkout refreshed; local ZIP has 714 unique paths, exact main
source/version/UI/core identity and SHA256
`5efab7107728fd329b5b6c3b814b7bf9c97b27f06ff3fe61481d7ebb9815b69f`.
Evidence: `/workspace/scratch/chip-memory-labels`. Preserve public v0.4.1 and
McRetro.net. Next remains version-aligned v0.5.0 release-candidate preparation;
no repeated emulator research or native manual coverage claims.

## PR #67 Verified Delivery — 26 October 2026 (Sydney)

[PR #67](https://github.com/NixMcRetro/VRAMpage-MD/pull/67) merged as
`380e517eb85af7a344c1fb723b981fb41a452729`; source tree exactly matches tested
head `1ac07a0553b7c55fb18f9d8fe625dd791fe0a256`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40285842745)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40286496702)
passed. [Runnable build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40286496702/artifacts/12634666300).

Chip heading/body, accessible names and advanced-panel heading now read
SRAM (Work RAM); README navigation matches. WRAM schema identifiers, native
faults, recovery behavior and cartridge save SRAM are unchanged. Independent
GPT-6 read-only review found no blocker. Local source106 passed (two unchanged
SDK/vendor classes skipped), Chromium display7 passed, and the longer chip name
was contained at all nine existing desktop/mobile viewport sizes.

User reports PR #66 recovery seems OK and cannot practically test further;
record acceptance without inventing native Firefox/physical-gamepad coverage.
Corrected stale checkpoint-proof and pre-merge blockers already completed in
PR #63/#66. Next bounded release-candidate task is version alignment across
VERSION, site/index.html, site/app.js, build-website.yml, publish-local-release.yml,
version/browser/comparison fixtures and current release documentation. Then test
and verify a matching new-version package/tag/checksum. Do not dispatch the
publisher still fixed to v0.4.1 or replace the immutable public release.

Canonical runnable checkout refreshed. Main ZIP has 714 unique paths and exact
main source/version/UI/core identity; SHA256
`6d171380cae152e104a97eadf8d4886119333bce7b769528eb2fe7ecd26330f0`.
Public v0.4.1 release name, target, timestamp and asset digests verified unchanged.
No McRetro.net changes. Evidence: `/workspace/scratch/sram-label`.

## PR #66 Verified Delivery — 26 October 2026 (Sydney)

PR #66 merged as `c65ba5c0a6634526f385fca04928e9551b7f6f0e`, with an exact
source-tree match to reviewed/tested head `5210d4b487e1bfa7efdb6e355b9d01c3708e62d2`.
All seven [PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40279123549)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40279717162)
passed. [Runnable review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40279717162/artifacts/12632206278).
[PR #66](https://github.com/NixMcRetro/VRAMpage-MD/pull/66).

Force Resume and CPU Recovery are independent persistent On/Off switches near
Randomiser, both initially On. Two eligible HALT frames attempt Force Resume once;
eight more consecutive eligible HALT frames attempt one CPU Reset if enabled.
HALT clearing cancels escalation. Both Off selects unassisted operation. Held RAM
contacts defer observation, and Randomiser appearance remains unchanged.

Local Chromium125, WebKit recovery15, source106 (two unchanged SDK/vendor classes
skipped), actual-core8 and transaction3 passed. Extracted package core8 and
transaction3 passed. Independent GPT-6 review completed; requested Luna High was
not confirmed available. The native fixture clears HALT after Force Resume;
exact eight-frame escalation uses controlled telemetry, not a native re-HALT claim.

Canonical runnable checkout refreshed. Main ZIP has 714 unique paths with exact
main source/version/UI/core identity; SHA256
`3b3c3014b477c38774601b97ca9c60f0895c9940d43bf7994fcb4b4e6061fc89`.
Public v0.4.1 name, target, timestamp and both asset digests remain unchanged.
No McRetro.net changes. Evidence: `/workspace/scratch/ordered-recovery`.

Next: native Mac/cartridge acceptance of default-On recovery and compact controls;
continue concrete stabilisation reports. No automatic rewind, software-loop or
browser-blocked-frame detection, guaranteed gameplay recovery or physical claim.
No release/version bump.

## PR #65 Verified Delivery — 26 October 2026 (Sydney)

[PR #65](https://github.com/NixMcRetro/VRAMpage-MD/pull/65) merged as
`88cb73ebffecfe6c233b647ec979785c9c05b377`; tree exactly matches reviewed head
`45a2ac4943d7fcccccdda04f19336eec809c8a6e`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40261666973)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40262214621)
pass. [Updated runnable review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40262214621/artifacts/12624119703).

The final requirement is no dimming of ANY Randomiser button during RAM Write,
including VRAM text. The native VRAM safety interlock stays in place; its RAM-blocked
visual state now matches its ordinary enabled appearance. Genuine ROM/profile
unavailability keeps ordinary unavailable styling. No emulator or routing change.
Regression `test_ram_write_keeps_all_randomiser_button_styles_unchanged` compares
PSG/FM/VRAM text and text-fill colour, opacity, fill, border and appearance before,
during and after both hold/eight-frame modes in light/dark themes. Blocked clicks,
unchanged VRAM calls and post-contact availability are retained. Independent review
approved; focused Chromium/WebKit and all full CI browser suites pass.

Canonical runnable checkout refreshed. Local main ZIP has 714 unique paths, exact
source/version/app/style identity and unchanged core bytes; SHA256
`f2462a2e6cdba004c033a61fb50852b88f433393e254e22223aaa7f1825ba9bf`.
Evidence: `/workspace/scratch/randomiser-ram-appearance`. Public v0.4.1 release
name, target, timestamp and both asset digests rechecked unchanged. No McRetro.net
changes or release publication. PDF remains solely page-length feedback.

Next: user confirms native Mac Safari now leaves all three Randomiser buttons
fully unchanged during RAM Write. Do not reintroduce a RAM-dependent dimmed label.


## Randomiser Appearance During RAM Write — 26 October 2026 (Sydney)

User clarifies that RAM Write must not dim any Randomiser button, including the
VRAM label. PR #64's muted-label treatment did not meet that requirement.
The fix keeps the native VRAM interlock and existing preflight guards while using
normal text colour specifically when a Work RAM fault/contact/pulse blocks VRAM.
Missing-ROM/profile failures keep the ordinary unavailable styling.

Acceptance compares PSG, FM and VRAM computed text/text-fill colour, opacity,
background, border and appearance before, during and after both held and eight-frame
RAM Write contacts, in light/dark themes. It also verifies native disabled state,
blocked clicks and unchanged VRAM calls. No emulator or fault-routing change.
The PDF remains page-length feedback only; no layout changes are included.
Focused Chromium6.097s and WebKit12.829s pass all four mode/theme comparisons.
Source106 PASS15.186s (two unchanged SDK/vendor classes skipped). Independent
review approved2178e7c with no blockers. Required seven PR/main checks remain.
Preserve v0.4.1 and McRetro.net.


## PR #64 Verified Delivery — 26 October 2026 (Sydney)

[PR #64](https://github.com/NixMcRetro/VRAMpage-MD/pull/64) merged as
`ecf4592b7dff3a4d2b8d675d426270c615b0beb5`; tree matches tested head
`2851804a3bc2726cc4e75886090ff553bb1d7ad0`. All seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40259049136)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40259602894)
pass. [Complete updated review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40259602894/artifacts/12624246220).

RAM Write still disables VRAM randomisation for domain safety. Randomiser-row
buttons now keep their neutral fill/border while unavailable, mute only the label
and suppress native button paint. No app/emulator behavior changed; app JS and
both core binaries are byte-identical to PR #63. Light/dark regression verifies
no pressed state, blocked clicks, unchanged VRAM calls and availability on release.
Independent review approved the implementation; local Chromium/WebKit focused,
seven layout cases and source checks pass. Local source checks skipped the two
unchanged SDK/vendor-dependent classes; CI rebuilt/tested the complete package.

Canonical runnable checkout refreshed. Local main ZIP has 714 unique paths and
verified source/version/style/core identity; SHA256
`d356b42b347cd821a1a3ddea8bfbe67f0cb34b425965fb88144c9b7a49773398`.
Logs/packages: `/workspace/scratch/ram-write-button-state`.
Public v0.4.1 tag, timestamp and both asset digests rechecked unchanged.
McRetro.net untouched. User checkpoint/reset acceptance is recorded below.

Next: user confirms the new disabled-button appearance in native Mac Safari.
The PDF is ONLY page-length feedback, not button-bug evidence. Page-length feedback
is retained separately; no layout changes were made in this fix. No new release.


## Mac Acceptance and RAM Write Button Feedback — 26 October 2026 (Sydney)

User confirms checkpoint steps1–3: baseline save, deliberate chip faults, restored
picture/gameplay/sound and resume checks. Repeated restores work; saving with held contacts/controls or
active faults correctly reports the release/disconnect requirement. CPU Reset
retains the checkpoint and preserves sound-chip state. Clean Restart reboots and
discards it. Held-input suppression after Restore was not separately described.
These are user-reported Mac acceptance results, not new physical-hardware evidence.

The supplied Safari PDF is page-length feedback only. It is not evidence for the
separate reported VRAM Randomiser appearance during RAM Write. No PDF/game capture
is committed. The page-length feedback is retained; no layout redesign is included.

Reviewed fix: the VRAM Randomiser remains disabled during Work RAM contacts,
as required by fault-domain exclusion. Whole-button45% opacity made it look pressed;
keep its normal fill/border, mute only disabled text and remove native button paint
for the Randomiser row. No emulator, randomisation or cross-domain logic changes.
Regression checks in light/dark themes assert identical idle/disabled fills,
non-pressed state, blocked clicks, unchanged VRAM calls and restored availability
on release. Focused Chromium4.724s/WebKit9.616s (both themes) and source106 tests
PASS13.794s, with unchanged SDK/vendor-dependent classes skipped2. Independent
review approved796a796 with no blockers; native Mac Safari visual confirmation
is still needed. All seven PR/main checks remain required. Preserve v0.4.1 and
McRetro.net.


## PR #63 Verified Delivery — 26 October 2026 (Sydney)

[PR #63](https://github.com/NixMcRetro/VRAMpage-MD/pull/63) merged as
`c5d4e1249c43441c48b36ce66db230eb1e0e29ea`; its tree exactly matches reviewed
head `37e42bb67b693af455fe1c0bea59dec8ad5da69b`. All seven
[final PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40254986283)
and all seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40255469625)
pass. [Download the complete main review app](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40255469625/artifacts/12622163573).
The initial PR run's Firefox mock-image alpha failure was corrected without
changing product code or weakening the exact pixel assertion; the final full
Chromium/Firefox/WebKit suites each include117 logic cases. No blind rerun.

Explicit Save Checkpoint / Restore Checkpoint are complete in the advanced
Logic / Work RAM panel. One private session slot; capture never ticks, failed
capture retains the slot, verified fault clearing precedes restore, the saved
image displays immediately and emulation stays paused. Held controls wait for
release. CPU Reset retains the slot; Clean Restart/new cartridge invalidates it.
Metadata-only exports retain event/counter baselines and experiment segments.
Ordinary MD, 3/6-button pads and validated ordinary SRAM/write protection are
supported; unsupported mapper/peripheral/audio profiles are refused.

Independent native/JS review approved3fa33ff and reran nine actual-WASM groups.
Root local full SDK/source116 passes with fatal native sanitizers; production
actual-core8, extracted core8/transaction3, display7 and WebKit checkpoint14 pass.
Normal core binaries remain byte-identical and omit checkpoint APIs. Canonical
site/core and corresponding site/source were refreshed to the verified build.
The local main package has714 unique paths with exact c5d4e12/version/UI/core
identity; SHA256 `b5c1704b6731274e5bc300668038c16e25716bcc5be9e7aa7683736f4909727f`.
Logs/packages: `/workspace/scratch/session-checkpoint-ui`. The connector downloaded
the main review artifact; its producer and extracted-package CI checks pass.

Public v0.4.1 tag remains `e579c571f14b3549a5befa33d9e62ba3f3c9d45b`;
ZIP/SHA256SUMS digests remain36133552…ec6fd /961ff2e5…b1bc, release timestamp
unchanged. No v0.5.0 release was published. McRetro.net is untouched.

Next bounded gate: manual Mac/cartridge checkpoint acceptance (save a clean
running/paused point, apply chip faults, restore image/sound, release held inputs,
repeat restore, verify CPU Reset retention and Clean Restart invalidation).
Native Mac audible output, universal cartridge compatibility and physical fidelity
are unverified. Keep features frozen for concrete reported defects; do not repeat
completed native replay research or publish a release before its remaining gates.


## Session Checkpoint Integration Candidate — 26 October 2026 (Sydney)

Resumed from verified main `0b8263c`; all seven existing main checks were rechecked.
Explicit **Save Checkpoint / Restore Checkpoint** now use one privately owned,
same-cartridge/module slot. Save verifies clear faults and neutral controls without
ticking; failed captures retain the prior slot. Restore pauses, cancels transients,
releases held inputs, verifies all-domain clearing, restores the saved image without
ticking and stays paused. CPU Reset retains the slot; Clean Restart/new cartridge
invalidates it. JSON records metadata-only events/counter baselines/segments.
Ordinary MD, 3/6-button pads and validated ordinary SRAM/maps are supported;
other profiles are refused. [API/scope](SESSION-CHECKPOINT-API.md).

Native author checkpoint163d2ff is integrated as3fa33ff. Independent specialist
review approved native/JS source at3fa33ff and reran all nine actual-WASM groups.
The requested Luna High was unavailable; both specialist workers reported actual
GPT-6-based Codex. Root review caught normal-profile exposure and displaced Start
reset hooks before PR; corrections restore unchanged normal binary hashes and
explicit active-fault Start regression coverage. No assertion was weakened.

Local evidence: full SDK/source116 PASS209.065s with normal fatal sanitizers and
fresh builds; native checkpoint9 actual-WASM groups and existing logic25 pass.
Chromium mock logic116 PASS258.309s plus new unsigned-frame boundary/telemetry
cases2 PASS4.513s; display7 PASS17.384s. WebKit checkpoint14 PASS112.188s.
Production actual-core browser8 PASS99.739s, including immediate raw/canvas image,
no extra tick, paused restore and restart invalidation. Extracted package core8
PASS44.051s and transaction3 PASS10.227s on code-identical bf547d6; 714 unique
paths and source/version/UI/core identity verified. Required PR/main CI remain.
Evidence logs stay under
`/workspace/scratch/session-checkpoint-ui`; candidate source, runtime and normal
builds are retained in the isolated worktrees. No integrated release is claimed.

Initial [PR #63 CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40254368579)
passed six of seven checks. Firefox's sole failure was the new mock-image oracle:
the fixture filled alpha with80 as well as RGB80, so Firefox composited translucent
pixels to26. Production pixels are opaque. The fixture now sets alpha255 while
keeping the exact RGB80 assertion; isolated Chromium/WebKit rechecks pass. Product
source/core and thresholds are unchanged. A new complete CI run is required.

Public v0.4.1 tag/assets remain unchanged; no version bump or McRetro.net action.
Next: finish PR #63 CI, require all seven PR
checks before merge, verify all seven main checks, and record exact delivery links.
Native Mac audible/physical and universal mapper compatibility remain unverified.

## PR #62 verified delivery — 26 October 2026 (Sydney)

[PR #62](https://github.com/NixMcRetro/VRAMpage-MD/pull/62) merged as
`0b8263c1eb3f731f808c2cc6555ecde79b8a396a` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40224455470)
passed on `ebce69a94389694dceafe5e12bfaeaf2721f4907`; merged source tree matches.
All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40224889344)
pass on the latest main, attempt2. Initial build attempt had one real-time browser
scheduling start20.317ms late against the unchanged5ms limit. The other six core
cases passed. Logs were inspected/retained, isolated local recheck passed3.742s,
then only failed/dependent jobs were retried once without any source/threshold change.
[Ready-to-run main review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40224889344/artifacts/12610843393).

Private replay proof and defined Blip arithmetic are complete. No product checkpoint
API/controls exist. Native fatal ASan/UBSan and five actual-WASM replay cases pass;
all prior recorded PCM/pixel hashes remain unchanged. Full SDK/source115 passes
(145.167s); fresh production core7/handoff3 and extracted core7/handoff3 pass.
Twelve focused staging/source checks pass. Both production profiles have no proof
exports. Package704 unique files matches exact source/version/UI/core; SHA256
`85535807920bbdbfb044975299d285b286f5dd64544705a5cab5817bed622d22`.
Independent specialist review approved the corrections through158715e. Cached
canonical `site/core`/`site/source` now use the verified production builds; canonical
vendor was upgraded by the supported idempotent patcher. No private hooks installed.

Public v0.4.1 title/tag/assets are unchanged; original tag
`e579c571f14b3549a5befa33d9e62ba3f3c9d45b`, ZIP digest
`36133552de9c7dafb9502dea957b6a4934fe4b503d19e311fb898834162ec6fd`,
SHA256SUMS digest `961ff2e54e34e511355e736f0106fcd8cda71777977f1e29663683e08ed7b1bc`.
McRetro.net untouched. No new native Mac audible/physical claim.

User authorizes continued work. Next bounded gate is default six-button controller
state and warmed mid-session SRAM replay in scratch (worker `v050_state_audit`).
Initial3-button input-consuming and plain64KiB SRAM experiments pass with a bounded
SRAM copyback. Stock state omits SRAM; bytes/hashes after stock load prove the gap.
Root reran full input/SRAM build with normal default leak/address/UB sanitizers
(`env -u ASAN_OPTIONS -u LSAN_OPTIONS`, tool additional network permission); all
pass. Earlier worker disabled leak detection after sandbox ptrace failure; that
limitation is superseded by the root default-sanitizer rerun, not hidden.
Evidence: `/workspace/scratch/checkpoint-input-sram/root-default-sanitizers.log`.
No tracked input/SRAM implementation or production checkpoint wrapper yet. Keep
EEPROM/SVP/custom mappings/peripherals gated; capture/restore remains explicit,
one in-memory same-session slot, default unassisted faults, Title Case controls.


## Private checkpoint proof and defined Blip arithmetic integration

Developer-only code in `scripts/checkpoint-proof` archives the exact upstream pin,
builds in a marked isolated directory, and validates five original synthetic cases:
PSG LPF, FM+PSG LPF/EQ and changing-CRAM LPF/EQ. Stock state144398 bytes alone
fails PCM replay; a35960-byte audio supplement restores six-frame pixel/sample-count/
stereo hashes exactly. All five outputs also match recorded pre-correction goldens.
No normal/runtime checkpoint exports or UI are added. Input-consuming gameplay,
SRAM/EEPROM/SVP/mappers and fault/diagnostic restoration remain gates.

Native AddressSanitizer/UndefinedBehaviorSanitizer found old signed negative shifts
in pinned Blip filtering. The shared patch replaces four high-pass expressions
with defined multiplication, using the existing clamped16-bit sample and factor64.
Intended output is unchanged. The native smoke now runs with fatal sanitizers,
capacity/null refusal, guards, live pointers, PCM replay and three-buffer mixing.
Independent specialist review approves through158715e; twelve focused source/path
checks pass. Final SDK/source115 passes; fresh production profiles have no experimental
checkpoint exports; compiled-core7 and runtime/normal handoff3 pass. Portable
proof/native sanitizers and all five pre-correction pixel/PCM goldens pass.
Package provenance and required PR/main CI remain integration gates.

Builder refuses missing/drifted source, symlink output/ancestors, source paths,
unmarked output and dirty tracked source before cleanup. Committed source identity
and source-file hashes accompany the proof outputs. Focused Blip sanitizers do not
establish full-core/WASM memory safety or a production checkpoint format. Public
v0.4.1/McRetro.net remain untouched. Preserve Title Case and unassisted defaults.


## PR #61 verified delivery — 26 October 2026 (Sydney)

[PR #61](https://github.com/NixMcRetro/VRAMpage-MD/pull/61) merged as
`436a8e0f8fd815bc527a3be0fd675b3d90c7c41d` after all seven checks passed on
`ea699a55a9508069aa24b35325eeb64ceaa7c8e9` ([PR CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40221361461)).
Merged tree equals reviewed/tested source. All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40221890031)
passed on the latest main. [Ready-to-run review download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40221890031/artifacts/12609931295).

Title Case controls/labels and the off-by-default one-attempt HALT recovery are
complete. CPU Reset preserves FM/PSG; Clean Restart remains a full reset. Final
Chromium logic103 passed in 217.138s; core7/display7, focused WebKit logic7 +
actual HALT/STOP1, direct WASM25, docs6 and source/native97 (two SDK/vendor classes
skipped locally) passed. CI rebuilt fresh native/WASM and tested all browser/package
routes. Local ROM-free package683 matched exact source/version/UI/core; extracted
core7 and final HALT/STOP case passed. Final ZIP SHA256:
`37814dce927cbe9a1d385c3cbf8cad78ee298217acd2a23047bd959ab2985a78`.
Independent source review approved fixes; first failed CI layout records remain.

Public v0.4.1 title/tag/assets are unchanged: tag commit
`e579c571f14b3549a5befa33d9e62ba3f3c9d45b`; ZIP digest
`36133552de9c7dafb9502dea957b6a4934fe4b503d19e311fb898834162ec6fd`;
SHA256SUMS digest `961ff2e54e34e511355e736f0106fcd8cda71777977f1e29663683e08ed7b1bc`.
McRetro.net untouched. Native Safari and audible/physical behavior were not newly
verified; the policy cannot rescue every software/browser hang.

The user authorizes continued improvements during the active session. Next work
is the private checkpoint replay proof on `experiment/checkpoint-replay-proof`
(initial author09e7008; reviewed staging-guard fixes1055f42). Stock native state
144398 bytes restores serialized fields/pixels but changes PCM. An isolated35960-byte
audio supplement replays five original synthetic cases exactly, including dynamic
CRAM, PSG/FM and LPF/EQ. No product checkpoint API exists. A newly added native
sanitizer smoke check reports old negative-left-shift UB in pinned Blip filtering;
investigate/fix with sample-equivalence evidence before accepting sanitizer status.
Proof/source safety fixes are unmerged and require final review/checks/CI. Preserve
unassisted defaults, source pin, Title Case, v0.4.1 and McRetro.net. This checkpoint
is a continuation branch, not a separate documentation-only PR.


## Bounded CPU recovery integration — 26 October 2026 (Sydney)

Development source implements plan step 1: **Arm CPU Recovery Once**, off by
default, observes HALT on two consecutive eligible completed frames and consumes
one CPU-only reset attempt. It ignores STOP-only and deliberate transient contacts;
failed telemetry/clears/recovery pause without retry. Lifecycle operations disarm;
ordinary fault edits reset the streak while retaining arming. FM/PSG are preserved
by the existing CPU-only reset path. Intervention metadata records armed triggers
and aborts. The frame catch-up loop now stops immediately on a failure pause.

Buttons and labels use Title Case, including **Work RAM**, **CPU Reset**,
**Clean Restart** and **Hold While Pressed**. Preserve this style in future work.
No native model, VERSION, public release or McRetro.net change. Checkpoint
save/restore remains gated by serializer capacity and complete state/replay proof.
Independent review approves through c6930dc. Source/native smoke97 (two SDK/vendor
classes skipped), Chromium core7/display7, WebKit focused7/actual-HALT1 and direct
WASM25 pass. Final-source Chromium103 passes. Initial CI found native-control viewport
differences in Firefox/WebKit; desktop-only sizing fixes both locally reproduced
WebKit cases without changing the strict assertions. Required seven PR/main
checks and updated package provenance remain integration gates.


## v0.5.0 design checkpoint

Resume from verified main `5d0425a64acb0f883789c67e8c6ec41e5d2c0c02` (PR #60,
all seven PR/main checks passed). No new open PR or main changes were found.
[Recovery/checkpoint plan](RECOVERY-CHECKPOINT-PLAN.md) now defines the next
implementation: one explicitly armed HALT-triggered CPU reset attempt; then one
manual in-memory same-session checkpoint after native round-trip/capacity proof.
Unassisted operation remains default, audio remains outside CPU reset, and no
static-image heuristic, repeated rescue or automatic rewind is planned.

This is a design-only continuation checkpoint. No runtime/build/package change,
version bump, release replacement or McRetro.net action. Previous CI evidence
is reused; new runtime tests are acceptance gates, not executed claims. Independent
Luna High source audit covered existing serializer and CPU recovery paths;
full design review approved with no blocking findings. Six documentation tests,
changed Markdown local-link validation and `git diff --check` passed. Design saved
on `experiment/v050-recovery-design`; no documentation-only integration PR.
Native serialization bounds/complete replay and manual Mac acceptance remain
implementation gates. First implementation scope is plan step 1, with focused
positive/negative/failure tests and all required CI before merging.


## PR #60 verified delivery checkpoint — 26 October 2026 (Sydney)

[PR #60](https://github.com/NixMcRetro/VRAMpage-MD/pull/60) merged as
`5d0425a64acb0f883789c67e8c6ec41e5d2c0c02` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40206196863)
passed on `6d2a461d8ae4b6890cf05ce045e64dd50517f7c4`. Merged tree equals
reviewed source. All seven [main checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40206671753)
passed on the latest main; no blocker remains.

VRAM-only dotted disabled styling is removed; standard disabled appearance and
safety guards remain. Active fill and default Hold are user accepted. CPU reset
preserves FM/PSG directly; Clean restart resets sound. Resumed cartridge code can
still reprogram sound. Independent specialist review found no blocking issue.
Chromium: compact 6, display 7, logic 96, actual-core 6 passed. Targeted WebKit
appearance and CPU/restart cases passed, as did 48 visual states and 25 actual-WASM
CPU checks. Local ROM-free package: 682 unique files, exact source/version/UI/core
identity and extracted actual-core 6 passed. Unchanged native SDK evidence reused.
Fresh CI builds and packaged-browser checks passed separately.

[Ready-to-run main review download](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40206671753/artifacts/12603749446).
Public v0.4.1 metadata, asset digests and tag `e579c571f14b3549a5befa33d9e62ba3f3c9d45b`
are unchanged. McRetro.net untouched. Native Safari and physical electrical
accuracy were not newly tested; synthetic checks do not establish audible game sound.

Next bounded task: design the v0.5.0 opt-in bounded CPU recovery and explicit
save/restore checkpoints, with default unassisted faults and compatibility/state
validation. Reuse completed stabilisation evidence. Do not bump VERSION, replace
public assets, silently rescue faults or repeat finished RAM research. This
checkpoint is a continuation branch, not another documentation-only PR.


## Completed scope: consistent disabled controls and CPU/audio confirmation

The user accepts the active fill and Hold behaviour, and requests removal of the
VRAM-only dotted unavailable styling. Remove that one CSS override so all chip
Randomiser buttons share the normal disabled appearance. Preserve disable/title
behaviour both before ROM loading and during RAM contacts; no VRAM action should
be triggered. Native fault models, Hold defaults and audio behaviour are unchanged.

Independent source review confirms CPU reset reaches only work-RAM fault clearing
and `m68k_pulse_reset()`, with no VDP/Z80/FM/PSG/sound-reset call. Clean restart's
full `system_reset()` reaches `sound_reset()` and FM/PSG reset. Cartridge code can
later write sound registers once CPU execution resumes. New paused actual-core
coverage compares FM/PSG configuration snapshots around the CPU reset and verifies
that both Clean restart buttons clear them. Counters can be zero in this fixture;
nonzero counter/register preservation rests on the reviewed native call graph,
not an unsupported claim about that snapshot test. Existing actual-WASM CPU/RAM
checks pass (25 original synthetic 68000 checks).

Next after this bounded cleanup: v0.5.0 design for optional bounded CPU recovery
and explicit save/restore checkpoints, preserving unassisted glitch outcomes by
default. No v0.5.0 implementation/version bump is included here. Preserve public
v0.4.1, historical artifacts and McRetro.net; require seven PR/main CI checks.

## PR #59 integration checkpoint — 26 October 2026 (Sydney)

[PR #59](https://github.com/NixMcRetro/VRAMpage-MD/pull/59) merged as
`00be32ff8c9c705c60b1aafe4dd264d799c22fa2` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40202191064)
passed on `c8c40816d528b8548c2a2b959f480cfe8b30afdc`.
The merged tree exactly matches the independently reviewed head.
All seven main checks pass; no integration blocker remains.
Main verification: [run 40202700942](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40202700942).

RAM WRITE starts on **Hold while pressed** on a fresh page. Eight-frame pulse
remains an explicit option with unchanged exact timing and release semantics.
Active fault chips receive pale green fill plus their existing green outline;
idle chips and keyboard target changes stay neutral. Body, plain-pin, applied-pin
and hovered-pin labels remain readable in both themes. The dotted VRAM Randomiser
continues to mean unavailable, including before a ROM loads and during RAM
contacts; its safety guard is unchanged.

Independent review approves the selected default, explicit pulse regression
coverage and final palette/contrast guards through `26c8c09`. Local source/native/
SDK107, Chromium logic96/display7/compiled-core6, focused WebKit5 and its real-core
default-Hold case pass. Forty-eight visual states pass. The 682-file ROM-free
package matches exact source/version0.4.1 and UI/runtime bytes. An initial
unchanged-audio scheduling start was 11.61 ms late against the strict 5 ms test
limit; the original log is retained. Isolated audio and serial full extracted-core6
rechecks pass without modifying the assertion or audio code. Final package/core6
passes in 18.239 s. Evidence: `/workspace/scratch/hold-default`.

[Ready-to-run ROM-free review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40202700942/artifacts/12602597340).

Public v0.4.1 metadata, tag and both original asset digests were verified unchanged
after merge. McRetro.net was not modified or deployed. No JavaScript, native fault,
recovery or timing code changed. Native Safari retest/physical validation remain
separate from automated Chromium/WebKit checks; deliberate faults can still lock
games. Next: new UI/default acceptance and concrete compatibility reports, then
the separately planned v0.5.0 optional recovery/checkpoint design. Preserve old
models/evidence; do not publish an intermediate release or repeat completed research.

## Completed source slice: RAM WRITE Hold default and active chip fills

The user requests **Hold while pressed** as the RAM WRITE default. On a fresh
page the selector now starts on Hold; the existing **8-frame pulse** option remains
available by explicit choice. No input handler, native fault model, timing,
recovery or public version changes are required. Pulse-specific regression
cases select Pulse explicitly; cold-start mock and actual-core tests check the
new default and release semantics rather than overriding the selector first.

Active faults also give their chips pale green fill while retaining the green
outline. Idle chips and keyboard target changes remain neutral; body text and
plain/applied/hovered pin labels retain readable contrast in both themes. The
dotted VRAM Randomiser border means unavailable, both before a ROM is loaded
and during RAM contacts; it remains a safety-disabled command, not a press.

Implementation `bd254b4` changes only the initial HTML selection to Hold;
reviewed CSS/test follow-ups through `26c8c09` add the active pale fill with
readable body, plain-pin, applied-pin and hover colours. No JavaScript, native
fault, timing or recovery code changed. Independent review approves the default
and final palette/contrast guards. Explicit pulse cases retain their exact
8-frame, write-count, cancellation, rejection and legacy assertions.

Local full source/native/SDK107 passes with normal sanitizers/fresh WASM
(337.785 s); native code is unchanged after the CSS-only refinement. Final
Chromium logic96/96, display7/7 and compiled-core6/6 pass. Focused WebKit5/5 and
its real compiled-core default-Hold case pass. Forty-eight light/dark desktop/
mobile visual states verify default Hold, explicit Pulse, active fill/outline,
neutral idle chips and the existing unavailable VRAM style. Logs and images:
`/workspace/scratch/hold-default`. Package provenance and PR/main integration evidence are recorded above;
preserve public v0.4.1 and McRetro.net.

## PR #58 integration checkpoint — 26 October 2026 (Sydney)

[PR #58](https://github.com/NixMcRetro/VRAMpage-MD/pull/58) merged as
`d3b8d7eec4a2dd16c99734eecbce73d345bb8c26` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40197239190)
passed on `00aa262f351feeb7f16687ce472fb45e42dd01f4`.
The merged tree exactly matches the independently reviewed head.
All seven main checks pass; no integration blocker remains.
Main verification: [run 40197674169](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40197674169).

Green outlines now follow active chip faults, with neutral fills and normal
text/pin colours. Keyboard selection remains a separate text label. Indicators
clear with pulses, contact release, disconnection and restart; audio outlines
require confirmed support. The VRAM Randomiser's apparent press during RAM
contacts was its disabled state, with zero clicks or VRAM setters. It now has
a distinct muted dashed disabled appearance while retaining the safety guard.
A separate genuine keyboard handoff bug is fixed: focused RAM pair controls
cannot route fault digits to global VRAM, while Space release, 0 cycling and
explicit independent audio shortcuts continue to work.

Independent Luna High review approves the correction. Source/native/SDK107,
Chromium logic96/display7/compiled-core6, extracted-package6 and focused WebKit6
plus its genuine compiled-core case pass. Forty-eight light/dark desktop/mobile
states verify active outlines, neutral bodies, target independence, pulse/Hold
cleanup and disabled appearance. The 682-file ROM-free package identifies the
exact source/version0.4.1 and matches UI/runtime bytes. Original before/fixed
native evidence, logs and images: `/workspace/scratch/active-outline`.

[Ready-to-run ROM-free review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40197674169/artifacts/12599784087).

Public v0.4.1 metadata, tag and both original asset digests were verified unchanged
after merge. McRetro.net was not modified or deployed. Native models, timing and
recovery policy are unchanged. New UI corrections have automated Chromium/WebKit
coverage; native Mac Safari retest and physical-chip validation remain distinct.
Next: concrete compatibility reports/new UI acceptance, then the separately
planned v0.5.0 optional recovery/checkpoint design after stabilisation. Do not
repeat completed research or publish an intermediate release.

## Completed source slice: active-chip outlines and focused WRAM shortcuts

User clarification after PR #57: green should mark the chip outline when its
fault is active, not fill the selected keyboard target. Keep neutral chip bodies
and ordinary text/pin colours; the separate keyboard-target label still follows
0 cycling. Outline VRAM, WRAM, FM and PSG from their actual configured fault
state, including masks, bridges and temporary contacts; remove the outline when
the fault clears, without implying earlier corruption has been repaired.

A before-fix compiled-core probe reproduces a cross-domain bug: with an A11/A12
Work RAM button focused, Space starts its held write contact, but Digit1 reaches
the still-selected VRAM shortcut and applies AD0/AD1 while disconnecting RAM.
Block conflicting VRAM fault digits on the focused native RAM control, preserve Space/Enter
release and ordinary global shortcuts elsewhere, and retain safe 0 target cycling.
Raw original-cartridge-only proof: `/workspace/scratch/active-outline/baseline-core.json`.

The user further identifies the VRAM Randomiser's apparent pressed appearance.
A pointer-contact probe confirms it is disabled by the RAM safety guard, not
active: zero click events and no VRAM setter changes, with `:active=false` and
no pressed attribute. Make that disabled state visually distinct with a muted
dashed border while retaining the safety guard and explanatory title.

Acceptance: no green idle/default VRAM; active chip outline only, neutral infill,
correct light/dark contrast, multiple independent audio outlines, exact eight-frame
and pointer/key contact cleanup, no VRAM change or RAM disconnect from focused
WRAM digits, and no hidden CPU recovery. Preserve v0.4.1, McRetro.net, all native
fault models and previous verified evidence. Use independent review and required
seven PR/main checks at integration; do not repeat completed RAM research.

Source `fc49c19` and independent Luna High review `250adbf` implement the
correction. Audio outlines require confirmed runtime support and configuration;
unknown support does not produce a green active indication. The configured
fault state drives chip-body outlines, independently of the text-only keyboard
target. The VRAM Randomiser remains guarded and distinctly unavailable during
RAM contacts, with no click or VRAM setter activation from the mouse path.

The original compiled-core focus probe fails before the fix and passes after:
Space-held WRAM survives Digit1 with unchanged VRAM state/setters, 0 still cycles,
and Space release clears only RAM. Local full source/native/SDK107 passes with
normal sanitizers/fresh WASM (168.034 s); native code is unchanged after the JS-only
review support guard. Final syntax/compact UI6, Chromium logic96/96 and display7/7,
compiled-core6/6, focused WebKit6/6 and its genuine compiled-core controls case
pass. Forty-eight light/dark desktop/mobile visual states verify neutral fills,
active outlines, target independence, pulse/hold cleanup and disabled appearance.
Logs and original before-fix evidence: `/workspace/scratch/active-outline`.
Package provenance and PR/main integration evidence are recorded above.

## PR #57 integration checkpoint — 25 October 2026 (Sydney)

[PR #57](https://github.com/NixMcRetro/VRAMpage-MD/pull/57) merged as
`5a63331ddf2b100f1f5fd1d9cf73a557a875c536` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40184481041)
passed on `db46608478f9245627c389b75dadf43cf83d253e`.
The merged tree exactly matches the independently reviewed head.
All seven main checks pass; no integration blocker remains.
Main verification: [run 40184871084](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40184871084).

Clean restart is duplicated immediately right of CPU reset with shared handler
and error/availability behaviour. RAM WRITE defaults to eight frames; **Hold while
pressed** releases with pointer/key up, cancellation or focus loss, without CPU
recovery. Keys 1–9 target the selected chip; 0 cycles VRAM → WRAM → FM → PSG
without changing faults. A pale green chip body and visible label identify that
target. WRAM's tenth pair remains available by button. Rejected/uncertain release
pauses and reports; newer faults and restarts cannot be overwritten by stale
release callbacks. Native models, timing and intentional glitch outcomes remain.

Independent Luna High review approves implementation and follow-ups. Local
source/native/SDK107, Chromium logic93 and display7, actual compiled-core6 and
extracted-package6 pass, alongside focused WebKit contact/recovery/layout and
compiled-core checks. Sixteen light/dark desktop/mobile visual states pass. The
682-file ROM-free review package matches exact source, version0.4.1 and UI/runtime
bytes. Raw logs, images and original failure records: `/workspace/scratch/shortcut-modes`.

[Ready-to-run ROM-free review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40184871084/artifacts/12595786841).

Public v0.4.1 metadata, tag and both original asset digests were verified unchanged
after merge. McRetro.net was not modified or deployed. The user's earlier Mac
Safari acceptance is recorded below; new controls have automated Chromium/WebKit
coverage and still need user-side Mac acceptance. Deliberate faults can still
halt/corrupt a game. Next: concrete compatibility reports and the new-control
manual check; optional recovery/checkpoints remain planned for v0.5.0 after
stabilisation. Do not repeat completed research or publish an intermediate release.

## Completed source slice: compact recovery, held RAM and chip shortcuts

Resume verified main `c8753f5` / checkpoint `53b653e`; preserve public v0.4.1,
existing hardware models and McRetro.net. The user explicitly requested this
bounded workbench refinement after manual acceptance: duplicate Clean restart
immediately right of CPU reset, a sustained option for RAM WRITE pair buttons,
and 1–9 fault shortcuts with 0 cycling VRAM → WRAM → FM → PSG. Mark the selected
keyboard chip pale green with a readable target label. Reuse shared restart,
fault application/removal, capability checks, state/history and pulse handling;
no native model, automatic recovery or version bump is required.

Acceptance: both restart buttons have identical enabled/error/reset behaviour;
eight-frame default remains exact; sustained writes affect only the chosen
A11–A15 pair and releases with the mouse/key (including pointer cancel or focus loss)
without CPU recovery; keyboard target changes
never apply/remove faults; shortcuts target one chip with correct held-action
release, focus/modifier/repeat guards and truthful unsupported/failure state.
Keep all ten RAM pair buttons; digits address the first nine. Verify ninth preset,
all four modes, chip highlight in light/dark, keyboard/pointer and compact/mobile
layout. Independent specialist review, focused actual-core proof, full applicable
regressions and seven PR/main CI checks remain required before completion.

Implementation `593d4f5` / `c6d8c31` and independent Luna High review fixes
`a602394` implement press-duration Hold with pointer capture and release/cancel/
blur cleanup. Default eight-frame pulses remain unchanged. Held state cannot
restore over newer faults; release rejection/uncertainty pauses with explicit
status, without CPU recovery. Compact and toolbar restart share one handler,
including retained-cartridge availability after an uncertain native start.
Review approves final source and markup/test/style follow-ups through `79690f5`.
The chip target indicator sits above the grid so short landscape windows retain
the player budget, and the recovery buttons stay together when rows wrap.

Local source/native/SDK107 passes with normal sanitizers/fresh WASM (176.933 s);
unchanged native evidence is reused after the JS-only review fixes. Final syntax
and compact UI6, Chromium display7 and actual compiled-core6 pass. Compiled-core
proof covers all four keyboard targets, ninth pairs, keyboard/pointer contacts
beyond eight frames, changed writes, release without recovery and both restarts.
Sixteen visual states (four targets × light/dark × desktop/mobile) pass tint,
contrast, overflow and adjacent-restart checks. Full Chromium logic93/93 passes (221.230 s). Focused WebKit covers twelve
contact/recovery cases across runs, three compact-layout cases and the new
compiled-core controls case; all pass. Package provenance and PR/main integration evidence are recorded above. Raw logs,
screenshots and retained first failures: `/workspace/scratch/shortcut-modes`.

## User-reported Mac Safari acceptance — 25 October 2026 (Sydney)

The user confirms audible playback, mute/re-enable, randomisers, eight-frame RAM
buttons, CPU reset and Clean restart work. Switching tabs in the same Safari
browser pauses emulation and returning resumes it. Switching apps leaves it
running, with no stuck keys or notes observed. Record this as user-reported Mac
Safari acceptance; it is not automated native macOS Firefox or physical-chip
validation. Do not repeat these checks as an unfulfilled prerequisite.

## PR #56 integration checkpoint — 25 October 2026

[PR #56](https://github.com/NixMcRetro/VRAMpage-MD/pull/56) merged as
`c8753f5ad8c677873587f91a1f49a7e4b7be7b34` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40178948293)
passed on `5fc7b814b09abb044e326cab2e6d8021750947bc`.
The merged tree exactly matches the independently reviewed head.
All seven main checks pass; no integration blocker remains.
Main verification: [run 40179292731](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40179292731).

The shared keyboard handler ignores Control/Command/Alt keydowns so browser
shortcuts cannot pause, patch or press controller buttons. Plain controls, Shift
momentary contacts and modified keyup cleanup remain covered. Independent Luna
High review approves the one-line implementation and final regression. Local
source/native/SDK107, Chromium display7/7 and logic80/80, actual compiled-core5/5,
focused WebKit3/3 and tightened shortcut cases in both browsers pass. The 682-file
ROM-free package matches source/version/UI/runtime bytes; the extracted genuine
core repeats the fixed shortcut probe. Raw before/after evidence and logs:
`/workspace/scratch/input-stability`.

[Ready-to-run ROM-free review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40179292731/artifacts/12593530865).

Public v0.4.1 metadata, tag and both asset digests were verified unchanged after
merge. McRetro.net was not modified or deployed. No native model, timing, fault
outcome or recovery policy changed. Phase D continues with remaining manual
native Mac audible/OS-background acceptance and any concrete compatibility
reports; this Linux DOM-event probe does not establish those results. Do not
repeat completed automated gates or add speculative features. Optional bounded
recovery/manual checkpoints remain planned for v0.5.0 after stabilisation.

## Completed Phase D slice: browser shortcut isolation

Source `feb9277` adds one modifier guard to shared keyboard handling after a
compiled-core reproduction: Ctrl+P prevented browser default and changed Pause
to Resume; Meta+C pressed emulated A. The fixed original-cartridge probe leaves
Pause unchanged, browser default available and A released, without page errors.
This uses synthetic DOM modifier events with a genuine compiled core; it does
not establish native Mac shortcut or OS-background behaviour. Raw before/after
reports and logs: `/workspace/scratch/input-stability`.

Control/Command/Alt keydowns no longer invoke game/preset/pause actions. Ordinary
controls and Shift momentary contacts remain supported; keyup cleanup remains
unconditional. Focused Chromium negative and existing controller/patchbay tests
pass. Independent Luna High review approves `feb9277` and final test follow-up
`ac44e96`; the new test waits for a fresh tick and verifies modified keyup release.
Full source/SDK107, Chromium display7/7 and logic80/80, actual compiled-core5/5
and focused WebKit3/3 pass; the final tightened shortcut case passes again in
Chromium and WebKit. Required PR/main integration evidence is recorded above. Preserve
v0.4.1, all intentional fault outcomes and McRetro.net; no native model, timing,
recovery or release change is included. Native Mac/audible/OS-background manual
acceptance remains open after this bounded compatibility fix.

## PR #55 integration checkpoint — 25 October 2026

[PR #55](https://github.com/NixMcRetro/VRAMpage-MD/pull/55) merged as
`ed62981a62a3a32477308cec85bee2b62a7583ba` after all seven
[PR checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40174231430)
passed on `18c692a33fa9e2ba0fd75bafa5174c3a7f7d2fd9`.
The merged tree exactly matches the independently reviewed head.
All seven main checks pass; no integration blocker remains.
Main verification: [run 40174600830](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40174600830).

Safe replacement retains accepted restart bytes/name/hash on rejected files;
latest selection wins, Clean restart invalidates stale reads, and asynchronous
export cannot mix cartridge identities. Native-start failure stops with explicit
uncertainty and manual restart, without automatic recovery or fake rollback.
Independent Luna High review approves the source. Final source/SDK107,
Chromium80/80, actual compiled-core5/5, extracted-package5/5 and focused WebKit6/6
pass. The ROM-free 682-file package matches exact source/version/runtime bytes.
[Ready-to-run ROM-free review build](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40174600830/artifacts/12591218799).
Raw before/after evidence and logs: `/workspace/scratch/rom-stability`.

Public v0.4.1 title/tag and both original asset digests are verified unchanged;
McRetro.net was not modified or deployed. Phase D remains active. Next bounded
work is remaining compatibility/manual acceptance, especially native Mac audible
output and OS background transitions; do not repeat completed automated gates or
implement speculative recovery. v0.5.0 remains planned after stabilisation.
Intentional faults can still halt or corrupt a game; no automatic rescue was added.

## Source checkpoint: safe cartridge replacement

Implementation `5b378f9` stages file reads and accepted ROM identity, rejects
known size limits before reading and ignores stale selections/errors. Explicit
Clean restart invalidates pending reads and uses retained accepted bytes. Export
cancels rather than mixing identities after asynchronous hashing. Preflight
rejection preserves the running/paused game, faults, audio, pulse and history.
An activation attempt that may mutate the core stops/reports uncertainty on
failure; there is no hidden rollback or automatic CPU rescue.

Independent Luna High review/fixes `f85ac61` mark mutation before native start,
retain pre-start audio drain and pulse cancellation only after acceptance, and
refuse pending export if the core becomes uncertain. New-mode rejection coverage
`141bdd9` and reset contract `522c13e` retain exact pulse timing and real native
restart behaviour. Focused ROM/failure/race/export/pulse checks pass. The old
source-only reset regex demanded premature disconnect calls; it was updated to
assert real native restart plus read invalidation instead, with behavioural
reset/cleanup evidence retained. The failed first source log is preserved.

Independent compiled-core before/after proof: the old build exported the rejected
file's hash under the accepted filename and failed to restart; the fixed build
retains the accepted hash/name and performs native Clean restart. Raw evidence:
`/workspace/scratch/rom-stability`. Final source/SDK107, Chromium80/80, actual compiled-core5/5 and focused
WebKit ROM6/6 pass. Package provenance and PR/main integration evidence are
recorded above. Preserve public v0.4.1 and
McRetro.net; this is Phase D failure handling, not the v0.5.0 recovery milestone.

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
