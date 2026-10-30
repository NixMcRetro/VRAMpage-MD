# Development work queue

Updated 30 October 2026 (Sydney). This is the current queue. **Update these sections
in place; do not prepend historical checkpoint logs.** Exact commits, CI,
downloads and verification limits belong in [development status](DEVELOPMENT-STATUS.md).
The root [development instructions](../AGENTS.md) remain authoritative.

## Current scope

Phase D feature freeze and stabilisation are active. Transaction-level VRAM,
hardware-informed audio, essential configurations/presets, recovery and experiment
comparison are integrated. Continue bounded browser/audio, input, crash/failure
safety and usability corrections supported by concrete evidence.

Ponytail Full Mode is the default for subsequent tasks and new sessions, with
project instructions taking precedence. Reuse completed native/WASM, performance,
RAM research and soak evidence when the relevant source is unchanged.

## Priorities and dependencies

| Work | Dependency | Acceptance |
| --- | --- | --- |
| Concrete stabilisation regression | Reproducible failure or owner report; inspect the existing implementation and tests first | Bounded correction, regression evidence, review proportional to risk, applicable checks and verified integration |
| Experimental Demo Cart music | Owner listening/gameplay review of the experimental drafts; latest audition is PR #106 | Explicit owner approval before any cartridge promotion; digital output checks alone do not supply that approval |
| Optional NTSC Model 1 VA6 mapping, issue #73 | Matching board markings and routing evidence | Record physical evidence honestly; this is not a source integration blocker |

No implementation item is currently recorded as unfinished. Select the next
bounded correction from a concrete failure or owner feedback, then record its
scope and measurable acceptance here before editing. Do not invent a feature,
repeat completed experiments or create pipeline-only work to fill the queue.

The five experimental music PRs [#101](https://github.com/NixMcRetro/VRAMpage-MD/pull/101),
[#103](https://github.com/NixMcRetro/VRAMpage-MD/pull/103),
[#104](https://github.com/NixMcRetro/VRAMpage-MD/pull/104),
[#105](https://github.com/NixMcRetro/VRAMpage-MD/pull/105) and
[#106](https://github.com/NixMcRetro/VRAMpage-MD/pull/106) await owner listening
approval. Use the latest audition rather than restarting the music work.
[Issue #73](https://github.com/NixMcRetro/VRAMpage-MD/issues/73) remains optional;
the accepted PAL reference and implemented controls do not establish that NTSC map.

## Continue a bounded task

1. Read the current [status](DEVELOPMENT-STATUS.md), inspect main/open PRs and
   changes since the recorded evidence, and preserve local work.
2. Define the reproduction, affected files, dependencies and acceptance. Use
   existing helpers; follow AGENTS for worker choice and independent review.
3. Fix the concrete issue while preserving intentional glitch/HALT outcomes,
   recovery semantics and existing assertions. Run focused checks during edits
   and the required applicable gates at integration; reuse valid unchanged evidence.
4. Record the reviewed/merged commits, actual check results, blockers and next
   bounded task in the current sections. Distinguish pending checks from passes.

## Approval and preservation boundaries

VERSION remains **0.5.1**. Its release and website approval are complete; future
publishing, asset replacement, version bumps or McRetro.net deployment require
separate explicit approval. Preserve all existing public artifacts and unrelated
website content.

[site/cartridges.json](../site/cartridges.json) owns approved identities: default
Demo Cart **v0.3.5** and original Colour Test **v1**. Experimental music is separate.
Every future complete browser/static bundle includes all manifest-approved
cartridges, matching source and notices under the
[cartridge maintenance policy](BUILT-IN-CARTRIDGES.md). Preserve original Demo Cart
v0.1 assets, portrait/logo, attribution and recorded experiment JSON.

## Complete historical queue

The [complete queue at merged PR #115](https://github.com/NixMcRetro/VRAMpage-MD/blob/a15fce5ac0352b4486486d6b9db43d7cc075f0f6/docs/WORK-QUEUE.md)
preserves every earlier checkpoint, source identity and evidence link byte for
byte, with original relative navigation. Its old next-task directives are
historical; the current sections above govern continuation. Recover it locally:

```sh
git show a15fce5ac0352b4486486d6b9db43d7cc075f0f6:docs/WORK-QUEUE.md
```
