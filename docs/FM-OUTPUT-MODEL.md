# FM Output Model

Development source feature after [proof PR #107](https://github.com/NixMcRetro/VRAMpage-MD/pull/107),
based on `4723457f4f80e94250e8f272bbedc04c4596fcb2`. The bounded
[actual-WASM proof](FM-MODEL-PROOF.md) establishes digital output and lifecycle.
It does not establish audible quality or measured physical motherboard behavior.

## Scope and Behavior

Add one compact **FM Output Model** selector beside the existing Region control.
Offer **Discrete** and **Integrated**, using the current MAME backend. Discrete
remains the default. Do not add Enhanced output, a Nuked engine selector, board
revision choices or analogue claims. Use the current visual style, Title Case
labels and existing accessibility/status patterns; avoid another panel.

Reuse Region's staged-machine lifecycle. A valid choice updates only the pending
request. Apply it after startup defaults and before native sound initialization.
Only successful cartridge start reports an effective model. CPU Reset, Force
Resume and checkpoint save/restore retain the active model and checkpoint; a
pending choice cannot alter current sound or faults. Clean Restart/new cartridge
invalidates the old slot before applying the pending model. Invalid requests are
atomic rejections. Preserve private local cartridge loading and all existing
controller, region, sound, fault and recovery behavior.

Normal/legacy cores without the API expose the selector as unavailable and do
not invent an observed model. The native/API state must distinguish requested
from effective identity and uninitialized/unsupported states. Strict validation
belongs at the JS facade and native boundary. Do not expose unchecked setters.

## Exports and Comparison

Include versioned requested/effective model and backend identity in machine
observations and experiment exports. Pending and effective models must remain
distinguishable. Compare observed active identity so a Discrete/Integrated pair
cannot silently look equivalent. Treat missing, invalid or unavailable legacy
observations as Unknown. Avoid changing circuit-fault configuration schemas for
this machine setting unless an existing contract requires it.

## Acceptance

- Reuse the complete proof's default parity, native PCM/DAC/status, CPU/banked-Z80
  masks/bridges/isolation and exact checkpoint replay cases against the production
  runtime API. Retire test-only model mutation once the production lifecycle
  replaces it, preserving every behavioral assertion and source-notice check.
- Test valid/boundary/invalid requests and missing/malformed APIs. Verify that
  staging does not change live output, faults or checkpoint readiness; CPU Reset
  and Restore do not activate pending choices; restart/new cartridge does.
- Browser tests cover selection, pending/active status, startup/restart/reset,
  old-core fallback and exported/comparison identity. Preserve layout bounds,
  keyboard/controller input and all existing assertions.
- Production default Discrete behavior must match the normal core. Normal
  JS/WASM hashes stay unchanged. Runtime API exports intentionally change its
  binary hash; update that gate only from a freshly built, independently reviewed
  runtime with retained exact source/notices and reproducible output.
- Run meaningful focused native/API/actual-WASM/browser tests, the full applicable
  suite, independent Luna High specialist review, all seven protected checks and
  CodeQL before merge; verify main afterwards. Never weaken a test to hide a
  regression. Keep exact commands, commits and checks in the continuation record.

Keep VERSION, the manifest-approved Demo Cart v0.3.5 and Colour Test, experimental
cartridge branches, published releases and McRetro.net unchanged. No release,
publication or deployment is authorized by this development feature.
