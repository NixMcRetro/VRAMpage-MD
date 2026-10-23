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
