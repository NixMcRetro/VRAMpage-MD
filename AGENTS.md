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
telemetry, frameworks and rewrites.

Use an isolated feature branch and focused PR. Required GitHub Actions checks
must pass before merging. Completed verified work is authorised for merge into
this repository's main; do not force-push. Verify merged source and CI, and
record the final state in the queue/status. Never claim an unexecuted check.

## Versions, releases and evidence

`VERSION` and `docs/VERSIONING.md` are authoritative. Use 0.2.x for incremental
RAM-stage work, 0.3.0 for transaction-level VRAM and 0.4.0 for hardware-informed
audio. Do not advance to 1.x or 2.x without an explicit release decision. Keep
labels, new exports, tests, release tags, filenames and download links aligned.
Preserve old commits, attribution, release artifacts and recorded experiment
JSON. Do not silently rebuild or replace an existing public artifact.

Provide complete ROM-free Mac packages with built JS/WASM, matching source,
notices, START.command, instructions and checksum. Verify package source commit,
version and tag. Respect upstream non-commercial/corresponding-source terms.

Never commit ROMs, protected RAM dumps, private game captures or credentials.
Synthetic cartridge tests do not establish Sonic gameplay, audible sound, native
macOS Firefox or physical electrical accuracy. Distinguish deterministic digital
approximations from physical evidence. Do not use game-specific variable edits
or post-mix distortion to fabricate hardware-fault outcomes.

## Continue and checkpoint

Follow the authoritative roadmap: finish the RAM attract-mode acceptance before
major VRAM/audio work. A stopped or static game is a result, not a reason to
silently rescue it. Continued internal demo input needs direct evidence.

Keep `docs/WORK-QUEUE.md`, `docs/DEVELOPMENT-STATUS.md` and `CHANGELOG.md` current.
At a checkpoint record completed work, exact GitHub state, passing checks,
blockers and next worker/continuation instructions. Continue eligible work during
the active session; do not promise indefinite background execution. Report
outcomes concisely with PR, commit, CI and download links and honest limitations.
