# VRAMpage MD development instructions

Work only in `NixMcRetro/VRAMpage-MD`. Do not modify, merge or deploy
`NixMcRetro/mcretro.net` without separate explicit approval.

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

## Future Built-In Demo Cart Releases

The user's 29 October 2026 approval applies to **integrating the original
Demo Cart v0.3.5 into this repository's main and future releases**, not to
replacing an existing public release. For all future browser release builds,
run `python3 scripts/build-demo-cart.py` and include the generated
`site/demo/VRAMpage-MD-Demo-Cart-v0.3.5.bin` (150,564 bytes; SHA-256
`89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f`). `site/app.js` autoloads this
original verified cartridge. The previous v0.1 binary remains tracked for
historical compatibility. Never check in newly generated ROMs or relax the
approved-cartridge allowlists; the generator must fail if the pinned output
differs. Keep the original portrait and logo source assets unchanged. Run
the source, actual Genesis Plus GX, all browser and packaged-release tests,
and obtain normal approval before publishing new releases or deploying the
McRetro.net website. Do not change the already public v0.5.0 artifacts.
The three-minute music-led show is still a future milestone.

## Versions, releases and evidence

`VERSION` and `docs/VERSIONING.md` are authoritative. Use 0.2.x for incremental
RAM-stage work, 0.3.0 for transaction-level VRAM and 0.4.0 for hardware-informed
audio. Do not advance to 1.x or 2.x without an explicit release decision. Keep
labels, new exports, tests, release tags, filenames and download links aligned.
Preserve old commits, attribution, release artifacts and recorded experiment
JSON. Do not silently rebuild or replace an existing public artifact.

Release titles must be exactly `VRAMpage MD v0.x.x`, without subtitles. Publish
meaningful usable milestones only; preserve historical releases unchanged.

Provide complete ROM-free Mac packages with built JS/WASM, matching source,
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

The following rules are from [DietrichGebert/ponytail's `AGENTS.md`](https://github.com/DietrichGebert/ponytail/blob/main/AGENTS.md) (MIT license). They supplement, rather than replace, the project instructions above.

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

## Ponytail mode selection for Codex Cloud

These are task-level instruction modes when using the repository in Codex Cloud, not installed slash commands or lifecycle hooks. Default to **full** when no mode is specified.

- **lite**: Implement the requested change, briefly identifying a simpler option when useful. Preserve required checks and safety.
- **full** (default): Follow all Ponytail principles; implement the smallest complete solution, reuse existing code, and test non-trivial logic.
- **ultra**: Apply full and also question unnecessary complexity or scope before implementation. Do not override a clear user requirement or block an otherwise authorised task.
- **off**: Set aside Ponytail-specific preferences for that task while keeping all project instructions and essential safety requirements.

A task can choose a mode by saying `Use Ponytail lite`, `Use Ponytail full`, `Use Ponytail ultra`, or `Use Ponytail off`. This selection applies to that task only. It does not change the repository default or activate Ponytail's CLI plugin commands.

Project-specific instructions above take priority over Ponytail preferences if they conflict. Never remove validation, security, accessibility, data-loss prevention, required reviews or tests merely to reduce code or tokens.
