# Development status and continuation checkpoint

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
