# Development status

Updated 31 October 2026 (Sydney). **Update these current sections in place; do not
prepend historical checkpoint logs.** Priorities, dependencies and approval
boundaries are in the [work queue](WORK-QUEUE.md); root [AGENTS.md](../AGENTS.md)
retains the feature freeze and default Ponytail Full Mode instructions.

## Latest source and integration checks

The active isolated branch is `release/v0.5.2-demo-v0.3.8`, based on verified main
`3e5a204f0617e2c753bdfe813421991e06404249` (concise handoff PR #116). Its seven
[main source/browser/package checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41036531603)
and four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41036531138)
passed. Earlier integration evidence remains below and in the immutable history.

The owner approved the full Demo Cart v0.3.8 and a new VRAMpage MD v0.5.2 release
on 30 October 2026. The source is PR #106 head
`1a68c0d2c2f999af294e15364c8f06ed92db6b3a`; the separate short audition is excluded.
The exact full ROM reproduces at 167,720 bytes, SHA-256
`1baf324f8f997029513cea9855856148589df91882e7ae5d0c2a3b8906da5ffc`.
Its specialist source audit, five structural/preservation tests, 16 manifest/
static/release-asset tests and actual Genesis Plus GX NTSC/PAL checks pass locally.
The native checks include every scene's PCM, full show/menu/restart, A/B/C/START
and byte-exact VDP clean recovery. Both approved cartridges also pass generic
native execution in both regions. Original source-kit and portrait/logo bytes
are retained; no generated ROM is committed.

Independent specialist review approved the initial candidate
`46183ca2001829b22cf460a76723c505b6f5f5cf`, and its CodeQL passed. The complete
local source suite, 18 Chromium cartridge cases, actual-core startup and packaged
17-file static site passed. Its source ZIP independently rebuilt to byte-identical
JS/WASM with Emscripten 4.0.23; core hashes remain those recorded in the FM proof.

Initial [PR #117 CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/41066926096)
exposed stale v0.5.1 expectations in browser export/provenance tests. Those tests
now read the authoritative VERSION file while retaining exact metadata and
rejection assertions. Isolated historical fixtures remain unchanged. The failed
run is retained as evidence; its duplicate builds were cancelled after diagnosis.
Final integration review and protected PR/main CI, CodeQL and release checks
must pass on the final head. Follow [PR #117](https://github.com/NixMcRetro/VRAMpage-MD/pull/117)
for check results and the v0.5.2 release for exact commit/artifact identities.
Do not infer those results from owner approval. McRetro.net deployment remains
outside this task.

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

The owner approved the full v0.3.8 cartridge; the separate short Music Lab
audition remains experimental. Synthetic PCM/core checks do not independently
establish musical quality. Optional NTSC VA6 issue
#73 needs matching board evidence and does not block source integration.

Repository Dependabot/code-scanning alert-list API reads returned HTTP 403.
Public PyPI responses reported no advisories for the tested Playwright **1.64.1**,
pyee **13.0.1** and greenlet **3.5.5**. This does not establish that repository
alert lists are empty or that all dependencies are clear.

## Published and approved identities

[VRAMpage MD v0.5.1](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.5.1)
and [website PR #12](https://github.com/NixMcRetro/mcretro.net/pull/12) were
published/deployed under their completed approval, including the complete
same-origin source ZIP and matching GitHub mirror. The active v0.5.2 task authorizes a new release, without deploying the website.
Current version/cartridge identities and future
approval boundaries are recorded in the [queue](WORK-QUEUE.md).

## Complete historical status

The [complete status at merged PR #115](https://github.com/NixMcRetro/VRAMpage-MD/blob/a15fce5ac0352b4486486d6b9db43d7cc075f0f6/docs/DEVELOPMENT-STATUS.md)
retains every earlier commit, CI run, checksum, failed run and evidence limit
byte for byte, with original relative navigation. Its old continuation directives
are historical. The current queue/status govern new work. Recover it locally:

```sh
git show a15fce5ac0352b4486486d6b9db43d7cc075f0f6:docs/DEVELOPMENT-STATUS.md
```
