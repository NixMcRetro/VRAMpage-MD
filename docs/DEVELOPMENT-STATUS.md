# Development status and continuation checkpoint

Verified on 22 October 2026. Read [work queue](WORK-QUEUE.md),
[versioning](VERSIONING.md), [testing](TESTING.md) and [roadmap](../ROADMAP.md).

## Verified baseline

- Main contains the complete stacked development history and canonical v0.2.4,
  followed by v0.2.5 independent VRAM leg switches. Earlier work was not rebuilt
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

## Implemented functionality and evidence limits

The application includes the native framebuffer fix, legacy missing-line
recovery, raw output, responsive/fullscreen display, system Light/Dark appearance,
keyboard/gamepad controls, sound controls, VRAM patchbay/leg switches, work-RAM
faults, CPU recovery, frame/write-limited pulses, restart, logging and exports.
Tests cover original synthetic cartridges and actual compiled emulator execution.
See TESTING.md for the distinct historical real-game observations.

VRAM faults remain frame-scoped. Digital low-dominant and stuck-low approximations
are not measured electrical models or verified physical package pin mappings.
Per-access VDP faults and hardware-informed audio bending remain unimplemented.
No new native Mac, audible, commercial-game or physical-hardware test is claimed.

## Active integration

PR [#20](https://github.com/NixMcRetro/VRAMpage-MD/pull/20) adds v0.2.6 experiment
build identification without changing core/fault models. Reviewed head:
`8f71dfbcb936238f1c14d402809e1b156ac439e7`.

Local checks passed: 63 Python tests, both framebuffer suites, nine pulse protocol
groups, both native C smoke programs, 28 Chromium logic cases, six display cases,
23 actual-WASM original-cartridge checks and actual-core browser smoke. An
extracted package launched and exported its actual source commit using the real
manifest. Basic implementation/packaging workers and coordinator reviewed it;
independent Luna High source/test-design review found no concrete regression.
That specialist review executed no additional checks.

CI and publication status must be refreshed from GitHub before continuation.
Do not treat a pending PR or locally built ZIP as a published release.

## Highest-priority unfinished experiment

Current actual-cartridge records show repeatable corruption, including halted or
static-output cases and some divergent-output candidates. They do not establish
that internal Sonic attract-mode demo playback continues after a fault. Zero
external input, advancing ticks, clear CPU flags or changing hashes are insufficient.
Do not claim the RAM-stage acceptance is complete.

Next assignment: Luna High should inspect the existing runners and determine the
smallest read-only diagnostic/observation protocol that proves internal demo
playback and activation scene, preserving unmodified game code. A private legally
usable cartridge is needed for actual Sonic evidence; no cartridge was found in
the inspected project/session test locations. Do not fetch a commercial ROM.
Synthetic tests can verify diagnostic behaviour but cannot satisfy gameplay
acceptance. Require an independent specialist review for emulator instrumentation.

Record exact source/core/ROM hash, reset/input schedule, activation and release
frames, scene observation, playback evidence, fault settings, CPU state and repeated
baseline/fault outcomes. Export no protected bytes or captures. Report failures
without implicit recovery. See WORK-QUEUE.md for dependencies and acceptance.

## Restart instructions

Fetch main and open PRs/releases/CI. Read AGENTS.md and the queue, preserve local
changes and existing artifacts, finish pending release checks, then continue the
first unblocked RAM-stage item. Use pinned tools and existing scripts. No work is
authorised in McRetro.net. There is no unattended background-execution promise.
