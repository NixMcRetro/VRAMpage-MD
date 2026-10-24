# Optional runtime build integration

## Objective and scope

Build the reviewed transaction-model runtime through a reproducible opt-in
production build path. Reuse the [safe model API](VRAM-PUBLIC-MODEL-API.md),
reviewed helper and renderer integration. Preserve the default normal JS/WASM binaries,
static hosting and immutable v0.2.8 download. The original build-only stage did not add application controls or publish a
release. The browser integration now uses this reviewed path as described below.

Integration base: `46dcc80a8d561cde4b79453300a2a1bdee3e847c`, merged
[PR #41](https://github.com/NixMcRetro/VRAMpage-MD/pull/41).
[Main CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40041499264)
passed all five source, browser and real-core/package jobs.

## Acceptance criteria

- Keep the existing default invocation and normal JS/WASM binaries unchanged.
  The corresponding-source bundle also includes the new helper and API shim.
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

## Application integration

The application now selects frame or transaction mode through the production
runtime, with validated RAM/VRAM handoff and separate export metadata/counters.
The current runtime passes the fixed five-pair performance gate after independent
review. Final browser CI, packaging and publication remain milestone gates;
see [development status](DEVELOPMENT-STATUS.md). Native Mac, audible output and
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
`source/wasm-genplus`, `source/scripts`, `THIRD-PARTY-NOTICES.md` and
`BUILDING.txt`.
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

## Verification checkpoint

Independent Luna High implementation and review approved author commit
`1d8b3f0` after fixing path validation and making the builder fixture ignore an
inherited output override. The integrated full suite passed 94 Python tests
without skips, including the actual production command and fresh five-profile
WASM integration, six nested pinned-renderer checks, existing JavaScript/native
suites, strict warnings and ASan/UBSan with normal LeakSanitizer settings.

Tests reject empty/unknown/extra arguments, unsafe and normalized `..` output
paths, symlinks, missing vendor input and invalid job counts. Pure path tests
also cover a safe default, custom output and configured external vendor.
The normal/runtime/normal sequence retains the exact normal binaries and leaves
the configured vendor unchanged during the runtime step. Actual generated
module checks select transaction mode using an original synthetic cartridge,
observe counts, reject coercible input and verify legacy frame controls and
absence of diagnostic memory/handler bridges.

The source bundle was rebuilt using the exact `BUILDING.txt` commands.
Independent review reran the API checks on both emitted and source-rebuilt
factories. Their binaries match byte for byte:

| Profile | JS SHA-256 | WASM SHA-256 |
|---|---|---|
| Normal, unchanged from main PR #41 | `3b984104bf92fd9e7a47fa5f081ed18d020e61dee6cd87df7580c147a3edc3bd` | `0bb55f946e5bb20ba0efc24e81776305ba8e1d9a82e0a3dcdca9e6218fbbe6d9` |
| Optional runtime and rebuilt source | `d5576f9c6943608de4f748c100f27b725601f9014ab99c8b80d6fe71c330b0e3` | `d37132fa4dca82cdcefee0758031d3767b6b982f6826d9c8880cd680e76ec951` |

The normal production build and actual-core Chromium smoke passed locally using
cached tools and the installed browser. The normal corresponding-source bundle
adds the helper and shim; only the normal JS/WASM hashes are unchanged.
Required GitHub checks remain the merge gate. These results do not establish
runtime performance, native Mac behavior, audible output or physical fidelity.


## Browser site profile

`bash scripts/build-core.sh site-runtime` builds the isolated runtime and installs
its JS/WASM in `site/core`. Matching runtime source, shim, notices and rebuild
instructions are retained in the marked `site/source/runtime-profile` tree.
The site then offers frame or transaction selection with the existing chip
controls. Explicit `normal` remains the fallback production build; it does not
expose the new runtime selector API. The website/release workflow verifies normal
baseline hashes and tests both that fallback and the installed runtime in the
browser before packaging. Diagnostic bridges remain excluded.
