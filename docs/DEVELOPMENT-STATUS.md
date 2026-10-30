# Development status

Updated 30 October 2026 (Sydney). **Update these current sections in place; do not
prepend historical checkpoint logs.** Priorities, dependencies and approval
boundaries are in the [work queue](WORK-QUEUE.md); root [AGENTS.md](../AGENTS.md)
retains the feature freeze and default Ponytail Full Mode instructions.

## Latest source and integration checks

[Interrupted audio PR #115](https://github.com/NixMcRetro/VRAMpage-MD/pull/115)
merged as `a15fce5ac0352b4486486d6b9db43d7cc075f0f6`, with a tree identical to
reviewed `74ca75b7d0920353cec713407a1c99512fa78b5e`. All seven protected
[PR source/browser/package checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41031588513),
four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41031583947)
and the aggregate check passed before merge.

**PR #115 main source/browser/package verification is running at this checkpoint:**
[remaining source/browser/package checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41032790675).
All four [main CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41032790630)
passed. Record the remaining actual results before claiming main fully verified.

The previous fully verified main is [controller PR #114](https://github.com/NixMcRetro/VRAMpage-MD/pull/114),
`291de22d9219d73a783206f3c2648f42f8c2c1f1`: all seven
[main source/browser/package checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41030368789)
and four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41030368313)
passed. Actions run pages provide review downloads; `BUILD-INFO.json` identifies
the exact packaged source. Follow [local running instructions](RUNNING-LOCALLY.md).

## Reviewed behaviour and retained evidence

Enable Sound resumes both interrupted and suspended contexts and requires the
context to reach running before enabling output. Rejected or ineffective resumes
stay muted and permit retry with the existing context. Permission errors use
browser-neutral wording.

PR #115's regression fails before the correction and passes Chromium/WebKit:
trusted gestures, suspended/running states, failure, retry and context reuse are
covered. Genuine AudioContext/production-core queue checks pass both engines;
31 focused documentation checks passed. These are recorded source-checkpoint
results, not new physical interruption or listening acceptance.

PR #114 guards policy-blocked gamepad reads, preserves keyboard/frame progress
and checkpoint suppression, and completes standard A/D-pad mapping with short
button-array safety. Its protected integration checks above are complete.

Reuse the completed [testing evidence](TESTING.md),
[FM model proof](FM-MODEL-PROOF.md) and
[FM selector contract](FM-OUTPUT-MODEL.md) for unchanged native/WASM, checkpoint,
region, fault and performance behaviour. Historical failures, negative results
and bounded RAM trajectory acceptance remain preserved in the snapshot below.

## Manual and security limits

The owner accepted the Safari local-ROM picker correction in
[PR #109](https://github.com/NixMcRetro/VRAMpage-MD/pull/109). This is acceptance
of that reported interaction. Linux WebKit automation does not establish native
Safari/iOS interruption behaviour, broad native macOS/Windows compatibility,
physical gamepad mapping, human listening quality or physical electrical fidelity.
Specific earlier owner feedback retains its recorded scope.

Music drafts still await the owner review listed in the [queue](WORK-QUEUE.md).
Synthetic PCM/core checks do not approve a soundtrack. Optional NTSC VA6 issue
#73 needs matching board evidence and does not block source integration.

Repository Dependabot/code-scanning alert-list API reads returned HTTP 403.
Public PyPI responses reported no advisories for the tested Playwright **1.64.1**,
pyee **13.0.1** and greenlet **3.5.5**. This does not establish that repository
alert lists are empty or that all dependencies are clear.

## Published and approved identities

[VRAMpage MD v0.5.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.5.1)
and [website PR #12](https://github.com/NixMcRetro/mcretro.net/pull/12) were
published/deployed under their completed approval, including the complete
same-origin source ZIP and matching GitHub mirror. These later source PRs did not
publish a release or deploy the website. Current version/cartridge identities and future
approval boundaries are recorded in the [queue](WORK-QUEUE.md).

## Complete historical status

The [complete status at merged PR #115](https://github.com/NixMcRetro/VRAMpage-MD/blob/a15fce5ac0352b4486486d6b9db43d7cc075f0f6/docs/DEVELOPMENT-STATUS.md)
retains every earlier commit, CI run, checksum, failed run and evidence limit
byte for byte, with original relative navigation. Its old continuation directives
are historical. The current queue/status govern new work. Recover it locally:

```sh
git show a15fce5ac0352b4486486d6b9db43d7cc075f0f6:docs/DEVELOPMENT-STATUS.md
```
