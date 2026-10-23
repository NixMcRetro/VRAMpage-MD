# Safe VRAM model API groundwork

## Scope

This bounded stage prepares the reviewed transaction model for future application
integration. It does not enable a new public UI or publish v0.3.0. The normal
build and immutable v0.2.8 Mac download retain frame-projection controls. The
[semantics protocol](TRANSACTION-VRAM-SEMANTICS.md#api-migration-state-and-exports)
defines IDs, errors and model behavior; the
[renderer record](VRAM-RENDER-DIAGNOSTIC.md) contains prior verification.

An optional runtime build will expose model selection and read-only scalar state
and last-frame counters, without diagnostic memory accessors, handler invocation
bridges, cache setters or renderer probes. A diagnostic profile adds those
test-only exports; the default profile exposes neither new runtime API nor test
bridges. Shared CPU/DMA/renderer implementation remains the reviewed engine.

## Acceptance before merge

- Reject wrong argument counts, non-number JavaScript inputs, fractional and
  nonfinite values before WebAssembly coercion. Validate numeric arguments again
  in C before narrowing to integer types. Errors leave settings, memory, counters
  and cache state unchanged.
- Preserve the normal modularized factory lifecycle, including asynchronous and
  custom synchronous instantiation and existing callback function/array forms.
  Test the generated module rather than only a mocked wrapper.
- Cover OFF, frame projection and transaction selection, defaults, identity,
  invalid masks/pairs/model IDs, unsupported modes, mode suspension/reentry,
  reconnect, legacy setter compatibility and clean restart.
- Keep legacy frame-difference counters distinct from transaction byte-lane
  counters. State reports the configured model and whether it is effective;
  inactive/suspended identity counts stay zero.
- Inspect actual WebAssembly exports in default, runtime and diagnostic profiles.
  Test bridges must be absent from runtime, not merely hidden in the frontend.
- Preserve application-owned RAM/VRAM exclusion and failed-disconnect behavior.
  The raw core VRAM selector changes only VRAM settings; it must not silently
  reset, disconnect or take over RAM. A future UI adapter must validate a request
  before orchestrating domain changes. This stage adds no UI takeover policy.
- Run focused native/strict/sanitizer and actual-WASM profile checks, independent
  specialist review, the applicable full regression and required CI. Preserve
  prior experiment records, release assets and normal core behavior.

## Continuation

After core API acceptance, connect explicit model selection and separate
transaction metadata/counters to application experiment exports. Then complete
browser compatibility and milestone packaging before declaring v0.3.0. Full-field
interlace timing, electrical fidelity, native Mac and audible acceptance are
separate evidence limits. Audio bending remains the later v0.4.0 milestone.

## Implemented developer interface

The actual-WASM harness builds five isolated profiles: normal, runtime-only,
diagnostic, alternate-renderer diagnostic and original-renderer reference.
Runtime-only defines `VRAM_TX_RUNTIME`. Diagnostic builds enable the same runtime
plus `VRAM_TX_DIAGNOSTIC`; existing diagnostic-only guards remain compatible.
There is currently no production runtime-profile builder or application selector.
The ordinary `scripts/build-core.sh` remains the normal profile.

The generated runtime factory installs these JavaScript-facing methods:

- `_set_vram_fault_model(modelId, mask, bridgeA, bridgeB)`: four integer arguments;
  returns 0 for success, 1 for invalid arguments or 2 for an unsupported mode.
- `_get_vram_fault_model_state()`: current configuration, semantics identifier,
  effectiveness/reason, support mask and completed-frame transaction counts.
- `_get_vram_supported_model_mask()`: a read-only capability probe; bit 0 is OFF,
  bit 1 is frame projection, and bit 2 is the transaction model. The mask is 3
  outside supported MD Mode 5 and 7 within it. Querying never selects a model.

| Numeric model | `modelVersion` identifier | Meaning |
|---|---|---|
| 0 | `off` | No VRAM fault; reason `off` |
| 1 | `frame-projection-v1` | Existing frame model; reason `none` or `no-fault` |
| 2 | `logical-byte-transaction-v1` | Transaction model; reason `none`, `no-fault` or `unsupported-mode` |

The state object also contains `modelId`, `mask`, `bridgeA`, `bridgeB`,
`effective`, `reason`, `supportedModelsMask` and `lastFrameCounts`. The latter
contains `logicalByteReads`, `logicalByteWrites`, `redirectedByteReads`,
`redirectedByteWrites` and `changedPhysicalByteWrites`, as nonnegative JavaScript
integer counts. These are completed-tick software byte-lane counts, not physical
bus cycles. Scalar C getters also exist; use the JavaScript state facade to
decode the C semantics-string pointer. Existing frame-difference getters retain
their previous meanings. The application's experiment JSON is not changed yet.

The build-owned `scripts/vram_transaction_api.js` is linked with `--pre-js`, so
registration precedes even custom synchronous instantiation. Its installer runs
before user post-run callbacks and preserves prior function/array callbacks.
Use the public methods after the modularized factory resolves. The shim captures
and removes the coercive `_set_vram_fault_model_c` property from Module; the
low-level numeric WASM implementation is not the public JavaScript interface.
The safe setter checks argument count and JavaScript types before crossing that
ABI; C independently checks finite integral ranges before narrowing.

The normal module lacks the new API and diagnostic bridges. Runtime-only lacks
handler invocation, memory/cache accessors and renderer test probes. This is
verified on actual generated module objects and audited compile guards, rather
than a vacuous name search in minified WASM exports.

## Reproduce the optional developer build

Activate the pinned SDK and prepare the vendor checkout as in
[deployment](DEPLOYMENT.md). From the repository root, choose an empty persistent
output directory and run:

```sh
VRAMPAGE_WASM_GENPLUS="$PWD/vendor/wasm-genplus" \
VRAM_TX_WASM_BUILD_ROOT="/absolute/path/to/empty-build-directory" \
python3 -m unittest tests.test_vram_transaction_wasm -v
```

The runtime factory and binary are emitted under
`runtime/src/main/js/genplus.js` and `genplus.wasm` in that output directory.
Normal, diagnostic, alternate and reference artifacts are retained alongside
them. These are developer/test outputs, not the Mac download or a new release.
Source-only runs that skip missing SDK/vendor prerequisites are not acceptance.

## Verified checkpoint

Independent specialist review approved author commit
`d8e566242e5058b4bb99bd264139e38d9c41c254` and independently reran its actual-WASM
API matrix. The integrated full suite passed all 91 Python tests without skips,
six required pinned-source patch checks, fresh five-profile WASM builds and
existing JavaScript/native suites. The coordinator ran ASan/UBSan and normal
LeakSanitizer outside the restricted executor with no suppression. A worker's
restricted LSan run failed under ptrace; its local workaround is not the final
verification or a checked-in harness change.

Tests cover per-argument coercion inputs, active-state invalid/unsupported
atomicity and physical-byte stability, model/reason/capability transitions, RAM
state preservation, legacy setters, nonzero counts and next-frame replacement.
All five facade counts match the diagnostic live-counter oracle after a tick;
a diagnostic read between ticks changes live counts but leaves the completed
public snapshot unchanged. Callback function/array order and synchronous and
asynchronous module instantiation are exercised on real generated factories.

An independently reconstructed checkout patched by exact previous-main scripts
(`9649c592d5a08a23826ad0f0878a69b50d9b91da`) upgraded successfully with the new
patcher, and a second pass was byte-identical. Partial/unknown guard layouts fail
closed. The normal production build, actual-core Chromium and a real 384-file
review ZIP also passed locally. Normal JS/WASM hashes match the PR #40 main
baseline exactly. These checks do not certify a production transaction build,
new runtime performance, native Mac behavior or physical fidelity. Required CI
still precedes merge.
