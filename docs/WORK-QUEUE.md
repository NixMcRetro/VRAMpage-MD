# Development work queue

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
checks pass. Full SDK/source113 passed before two final guard cases were added;
fresh production cores/browser checks and required PR/main CI are integration gates.

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
