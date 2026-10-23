# Optional runtime build integration

## Objective and scope

Build the reviewed transaction-model runtime through a reproducible opt-in
production build path. Reuse the [safe model API](VRAM-PUBLIC-MODEL-API.md),
reviewed helper and renderer integration. Preserve the default normal build,
static hosting and immutable v0.2.8 download. This stage does not add application
controls, change experiment exports, publish a release or declare v0.3.0.

Integration base: `46dcc80a8d561cde4b79453300a2a1bdee3e847c`, merged
[PR #41](https://github.com/NixMcRetro/VRAMpage-MD/pull/41).
[Main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40041499264)
passed all five source, browser and real-core/package jobs.

## Acceptance criteria

- Keep the existing default invocation and normal output unchanged.
- Make the transaction runtime an explicit opt-in with separate output; never
  silently replace `site/core` or attach diagnostic bridges to the runtime.
- Reject invalid options before mutating vendor source or output directories.
- Isolate compile/link flags and build products across repeated normal, runtime,
  normal builds. Preserve pinned-source validation and fail-closed patching.
- Include the JavaScript API shim, complete modified source, build instructions
  and licence notices with runtime output.
- Test the production build command, actual module API presence and diagnostic
  bridge absence, negative input paths and profile switching. Preserve normal
  JS/WASM hashes relative to the integration base.
- Require independent specialist source/test review, the full applicable suite,
  actual-WASM and browser checks and passing GitHub Actions before merge.

## Next stage

After this build path is accepted, integrate application model selection and
separate transaction metadata/counters in experiment exports. Prevalidate
selection before RAM/VRAM handoff. Current-runtime performance, browser and
milestone acceptance remain gates before v0.3.0. Native Mac, audible output and
physical hardware fidelity require separate evidence.
