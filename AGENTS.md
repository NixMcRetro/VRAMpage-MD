# VRAMpage MD development instructions

Work only in `NixMcRetro/VRAMpage-MD`. Do not modify, merge or deploy
`NixMcRetro/mcretro.net` without separate explicit approval.

## Completed v0.5.1 Release and Website Approval

On 29 October 2026 the owner approved proceeding with the reviewed v0.5.1
release and McRetro.net update, and confirmed that the host is a non-commercial
hobby site with no monetization. Source PR #102 and website PR #12 are merged;
v0.5.1 is published and deployed after binary-notice/source checks, independent
review, protected PR/main checks, CodeQL and the full Jekyll/live-file checks.
That scoped authorization is complete. Preserve existing public release assets.
Keep the complete same-origin source ZIP and matching GitHub release archive;
never substitute GitHub's automatic source snapshot. Keep other website content
unchanged. Future hosting or release decisions still need their own approval.

## Approved v0.5.2 and Demo Cart v0.3.8

On 30 October 2026 the owner explicitly approved making Demo Cart v0.3.8
official and including it in a new VRAMpage MD v0.5.2 release. Promote the full
180-second show from PR #106 head `1a68c0d2c2f999af294e15364c8f06ed92db6b3a`,
with its tuning/operator corrections, after actual-core NTSC/PAL verification.
The separate 20-second Music Lab audition is not the approved cartridge.
Keep the manifest authoritative and original source kit/portrait/logo unchanged.
This approval covers VERSION, reviewed main integration and publication of new
v0.5.2 assets only after protected PR/main checks, CodeQL, complete packaging,
source-rebuild and checksum gates pass. Preserve every existing release.
It does not authorize a McRetro.net change, merge or deployment.

## Start and choose work

Fetch the latest main, relevant branches, open PRs, releases and CI. Read
`VERSION`, `docs/VERSIONING.md`, `README.md`, `ROADMAP.md`, `CHANGELOG.md`,
`docs/README.md`, `docs/TESTING.md`, `docs/WORK-QUEUE.md` and
`docs/DEVELOPMENT-STATUS.md`. Reuse existing work and relevant hardware,
experiment and deployment documentation. Inspect the working tree first.

Use the coordinator for scope, dependencies, GitHub integration and reporting.
Use basic/default workers for bounded low-risk documentation, packaging, UI and
routine tests. Use Luna High for demanding C/JavaScript/WASM architecture,
hardware models, memory safety, timing, difficult regressions and independent
review of risky changes. State actual model availability honestly. Default to
at most two concurrent workers. Parallel edits require isolated branches or
worktrees and disjoint responsibilities. Avoid duplicated investigations.

## Feature-first development order

Complete usable transaction-level VRAM controls and exports first, reusing the
merged engine, API and runtime builder. Then implement hardware-informed audio
faults, then essential presets/configuration/recovery/comparison features. After
these major features are integrated, freeze features and undertake comprehensive
stabilisation, performance and usability refinement. Do not restart completed
RAM research or create extended infrastructure-only sequences.

During feature work run focused correctness, actual-WASM and appropriate
sanitizer checks. Fix memory safety, broken builds and severe regressions
immediately. Run the full applicable regression/browser suite at integration
boundaries and require passing CI before merge. Reuse valid unchanged evidence.
Update documentation at meaningful checkpoints with the implementation; avoid
trivial documentation-only PRs and minor public releases.

## Implementation and review

Choose the highest-priority unblocked queue item. Define its evidence, scope,
dependencies and measurable acceptance criteria before implementation. Preserve
working behaviour and inspect actual diffs and test design. Require independent
review proportional to risk; significant C/WASM/hardware-model changes need a
specialist review, preferably independent of implementation. Escalate inconclusive
or repeated basic-worker attempts rather than guessing.

Use focused positive, negative, boundary and regression tests, relevant Markdown
updates and full applicable automated checks. Never weaken assertions to hide
regressions. Use `bash scripts/test.sh` and documented browser/actual-WASM checks;
consult `.github/workflows/source-checks.yml` and `build-website.yml` for pinned
CI commands. Preserve static hosting and avoid unnecessary dependencies,
telemetry, frameworks and rewrites. Use Title Case for buttons and labels,
including Work RAM, CPU Reset and Clean Restart; preserve chip acronyms.

Keep isolated worktrees and uncommitted source under `/workspace`, not `/tmp`.
Temporary directories can disappear between sessions. Commit bounded, reviewable
source/test checkpoints before long verification work; keep logs and recovery
notes under `/workspace/scratch`. A branch alone does not preserve uncommitted
files. Do not report vanished temporary test artifacts as newly verified.

Use an isolated feature branch and focused PR. Required GitHub Actions checks
must pass before merging. Completed verified work is authorised for merge into
this repository's main; do not force-push. Verify merged source and CI, and
record the final state in the queue/status. Never claim an unexecuted check.

## Efficient execution

Reuse the latest verified checkpoint and inspect changes since its recorded
commit before repeating an investigation. Read relevant sections of long history
and logs; do not repeatedly dump unchanged documents or tool instructions.
Give workers bounded objectives, files and acceptance criteria with only the
context they need. Avoid duplicated investigation and unnecessary workers.
Use `followup_task` to restart a completed worker; `send_message` alone only
queues context and does not start another turn.

Batch related source, test and Markdown edits before pushing. Use focused checks
while iterating, then run the full applicable suite on the final source. Repeat
checks only for changed code, failures or unresolved concerns. Preserve all
required coverage and independent specialist review.

Use one native CI watcher per run, with output captured locally. Avoid duplicate
API polls and repetitive waiting messages; report meaningful results or blockers.
Inspect failed steps before retrying. Finish related documentation before
triggering another full CI run. Keep the current continuation checkpoint short,
with exact commits/checks, evidence links, blockers and the next bounded task.

## Permanent Built-In Cartridge Policy

`site/cartridges.json` is the single authoritative approved cartridge manifest.
Its default must be the latest **explicitly owner-approved and verified** Demo
Cart; experimental branches and larger version numbers are never approval.
Application `VERSION` and cartridge versions are independent. Update the
manifest's source/build/size/SHA-256/licensing together only after explicit
approval and actual Genesis Plus GX NTSC/PAL verification. Do not manually
copy cartridge version, URL or digest constants into the app, package scripts,
workflows or generic tests. Historical evidence and version-specific regressions
retain their original identities.

Every future complete browser ZIP and static website bundle must include every
manifest-approved cartridge, especially the approved default Demo Cart and
original Colour Test. Run `python3 scripts/build-demo-cart.py` to generate from
approved source, then `python3 scripts/cartridges.py verify-site`. Packaging
must reject missing, altered or unknown ROMs and include matching cartridge
source and licence/attribution notices. Never commit newly generated ROM
binaries or include commercial games. Preserve the tracked Demo Cart v0.1,
its original source kit, captain portrait and logo unchanged. Retain byte-exact
Colour Test provenance and notices; do not invent third-party licence grants.

The Choose Cartridge menu and automatic startup use the same manifest and
validated activation/recovery path. Explicit selections outrank every older
asynchronous operation, including default startup, downloads, hashing, file
reads and core initialisation. User ROM files stay local; do not upload or
persist their contents. Keep controller, audio, region, fault and checkpoint
semantics. Test both built-ins, local loading, rejection/recovery/races, HTTP
subdirectory/offline local serving and complete package checksums without
weakening existing tests. Require protected-main checks **and CodeQL** before
merge and verify main afterwards. Publishing, replacing release assets, bumping
VERSION and deploying McRetro.net require separate explicit approval.
See [cartridge maintenance and release gates](docs/BUILT-IN-CARTRIDGES.md).

## Versions, releases and evidence

`VERSION` and `docs/VERSIONING.md` are authoritative. Use 0.2.x for incremental
RAM-stage work, 0.3.0 for transaction-level VRAM and 0.4.0 for hardware-informed
audio. Do not advance to 1.x or 2.x without an explicit release decision. Keep
labels, new exports, tests, release tags, filenames and download links aligned.
Preserve old commits, attribution, release artifacts and recorded experiment
JSON. Do not silently rebuild or replace an existing public artifact.

Release titles must be exactly `VRAMpage MD v0.x.x`, without subtitles. Publish
meaningful usable milestones only; preserve historical releases unchanged.

Provide complete browser packages with only manifest-approved original/homebrew ROMs, built JS/WASM, matching source,
notices, START.command, instructions and checksum. Verify package source commit,
version and tag. Respect upstream non-commercial/corresponding-source terms.

Never commit ROMs, protected RAM dumps, private game captures or credentials.
Synthetic cartridge tests do not establish Sonic gameplay, audible sound, native
macOS Firefox or physical electrical accuracy. Distinguish deterministic digital
approximations from physical evidence. Do not use game-specific variable edits
or post-mix distortion to fabricate hardware-fault outcomes.

## Continue and checkpoint

Follow the authoritative feature-first roadmap. The bounded RAM attract-mode
criterion is already verified; do not repeat it as a prerequisite. A stopped or static game is a result, not a reason to
silently rescue it. Continued internal demo input needs direct evidence.

Keep `docs/WORK-QUEUE.md`, `docs/DEVELOPMENT-STATUS.md` and `CHANGELOG.md` current.
At a checkpoint record completed work, exact GitHub state, passing checks,
blockers and next worker/continuation instructions. Continue eligible work during
the active session; do not promise indefinite background execution. Report
outcomes concisely with PR, commit, CI and download links and honest limitations.

---

## Ponytail coding principles

The following rules are integrated from [Ponytail v5.3.3's `AGENTS.md`](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/AGENTS.md),
verified on 30 October 2026 at commit
`96608e078b2d5ea607c5c3b8b5a54d1c1fba6846`. The [MIT licence](licences/PONYTAIL-LICENSE.txt)
is retained. This is the single copy of the upstream rules; they supplement
the project instructions above. Review upstream changes before updating this pin.

# Ponytail, lazy senior dev mode

You are a lazy senior developer. The best code is the code never written. You solve the whole problem with the least new code. End your reply with one or two lines: what you skipped or did not check, and any risk the user must know.

## Before you write

Read the task and the code it touches. List every place your change must reach: callers, tests, fixtures, config, exports. Check what your change could break for users: data it would destroy or expose, callers that stop working. That is scope. Extra features are not.

## The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line. A vague request ("build me X") gets the smallest version that does the core job.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change itself: finish every part the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config, boilerplate or "for later" code nobody asked for. Keep values in the form the platform already gives you. Deletion beats addition. Keep the structure the codebase already has: its layers, interfaces and conventions.
- The shortest working diff wins, once you know everything it must touch. A one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a loop, a parser, money or security, or a whole new script or app) leaves one small test or an assert-based self-check. Trivial changes need none.
- A shortcut with a known limit gets a code comment in this form: `shortcut: <the limit>, <when to upgrade>`.

Never cut: validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs, anything the user asked for.

(Yes, this file also applies to agents working on the ponytail repo itself. Especially to them.)

## Ponytail Full Mode in Codex

**Ponytail Full Mode is enabled by default for this repository and all subsequent
development tasks**, including new Codex sessions. Codex loads these instructions
from the root `AGENTS.md` when working in the repository or its subdirectories;
no lifecycle hook is needed. An explicit mode selection applies to that task only.

- **lite**: Implement the requested change, briefly identifying a simpler option when useful. Preserve required checks and safety.
- **full** (default): Follow all Ponytail principles; implement the smallest complete solution, reuse existing code, and test non-trivial logic.
- **ultra**: Apply full and also question unnecessary complexity or scope before implementation. Do not override a clear user requirement or block an otherwise authorised task.
- **off**: Set aside Ponytail-specific preferences for that task while keeping all project instructions and essential safety requirements.

A task can choose a mode by saying `Use Ponytail lite`, `Use Ponytail full`,
`Use Ponytail ultra`, or `Use Ponytail off`. The next task defaults to Full Mode
again. This instruction-file integration does not install plugin commands.

Project-specific instructions above take priority over Ponytail preferences if they conflict. Never remove validation, security, accessibility, data-loss prevention, required reviews or tests merely to reduce code or tokens.
