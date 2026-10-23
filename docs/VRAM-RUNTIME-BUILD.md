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

## Build and reproduce

Use the same supported Emscripten 4.0.23 toolchain as CI, CMake, Make, Python 3
and Git. First prepare the pinned checkout through the normal build. Then run:

```sh
bash scripts/build-core.sh
bash scripts/build-core.sh runtime
node tests/test_runtime_build_profile.cjs build/runtime-profile/core/genplus.js
```

No argument or explicit `normal` builds the ordinary app in `site/core` and
`site/source`. The `runtime` argument writes only to ignored
`build/runtime-profile`: `core/genplus.js`, `core/genplus.wasm`,
`source/wasm-genplus`, `source/scripts` and `BUILDING.txt`.
The runtime factory starts in the existing frame-projection model. There is no
application model selector yet; use the documented core API in developer tools.
Do not manually replace the public app core or treat this output as v0.3.0.

`VRAMPAGE_WASM_GENPLUS` can select an existing pinned checkout for the runtime
build. Its uncommitted files are not build inputs: the builder archives the pinned
Git commit, applies the current project patch helpers in an isolated staging
tree and compiles with runtime flags only. It never adds those flags to the
normal vendor CMake file. `VRAM_RUNTIME_OUTPUT_DIR` selects another output
location; use a dedicated generated directory. Recognised generated contents
are replaced on rebuild, while unmarked directories containing user data are
refused. `VRAM_BUILD_JOBS` is a positive integer, defaulting to 2.

The runtime output includes complete modified source and the pre-JavaScript
shim. Its `BUILDING.txt` explains how to rebuild the adjacent source directly
with Emscripten and CMake, without a Git checkout or source download. Keep the
source, upstream notices and repository third-party notices with any binary
distribution. This stage does not publish a runtime ZIP or replace a release.
