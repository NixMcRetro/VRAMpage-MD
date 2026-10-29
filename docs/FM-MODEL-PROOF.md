# FM Output Model Proof

Development proof, based on verified main/release
`bc7369c943f1f7cda5167632077235b7630ad41b` (v0.5.1). The owner authorized the
next independent FM investigation after release/deployment completion.

## Scope

Use the existing Genesis Plus GX MAME backend to compare its Discrete and
Integrated output models. Reuse the staged-machine lifecycle, runtime builder,
original sound cartridges and real checkpoint implementation. Do not repeat the
completed Nuked mode characterization or add a motherboard catalogue.

The bounded proof must establish native PCM/DAC/status behavior, FM-fault input
routing and checkpoint replay before exposing any public selector. It uses an
isolated test build/adapter; the production app, runtime defaults, normal/runtime
binary hashes, VERSION, cartridge manifest, published releases and live site
remain unchanged. An adapter's test API is not a shipped application capability.

The [source research](FM-VARIANTS-RESEARCH.md) distinguishes engine, digital
output model and board circuit. This proof keeps MAME active and tests only the
first two MAME model IDs. Enhanced output and the Nuked backend are outside this
slice. Emulator output differences do not establish measured physical Yamaha
silicon behavior or a specific VA board's filters/loading.

## Lifetime Contract

The current checkpoint serializer does not save `config.ym2612` or the MAME
core's static model globals. Model identity therefore stays immutable during a
checkpoint's lifetime. A requested choice is staged independently from the
active native configuration.

| Event | Required Result |
| --- | --- |
| Module created | Default request is Discrete; no effective model is claimed before cartridge start |
| Valid request | Update only pending choice; preserve active sound, faults and any saved slot |
| Invalid/unsupported request | Reject without changing pending/active state or the slot |
| Cartridge start | Apply the pending choice after startup defaults and before native sound initialization |
| Save | Use the real safe-boundary/profile/fault/input guards and preserve the active model |
| CPU Reset | Preserve active model, sound-chip state and saved checkpoint; do not apply pending choice |
| Restore | Replay the saved native machine under its unchanged active model; do not apply pending choice |
| Clean Restart/new cartridge | Invalidate the old checkpoint before activating pending model; preserve existing restart semantics |

Prove model activation from real output and native behavior. A configuration
getter echo or a new adapter's own bookkeeping is not sufficient evidence.

## Acceptance Evidence

1. **Default parity:** compare production and proof builds under the same
   original cartridge/input sequence. Default PCM, pixels, memory progress and
   visible native state must agree; extra proof exports must not change the
   default executed behavior. Existing production hash gates remain intact.
2. **Actual model output:** run both models through native emulation, retain
   finite/nonzero PCM assertions and compare deterministic repeated captures.
   Establish native DAC/status cases from the pinned implementation; report
   any output that is equal rather than inventing a required difference.
3. **Fault routing:** exercise real CPU and banked-Z80 FM writes with existing
   cuts/bridges, literal delivered-byte/counter assertions and appropriate PSG
   isolation/control observations under each model. Removing a fault must not
   be described as repairing prior chip state.
4. **Checkpoint replay:** for each active model, save then replay identical
   instructions/input and compare PCM, framebuffer and relevant native state.
   Include save → CPU Reset → restore, a valid pending change and rejected
   choices. The pending request must not silently change the restored model.
5. **Restart boundaries:** show Clean Restart/new-cartridge activation discards
   the prior slot and applies the pending native model at initialization.
   Retain the existing supported/unsupported cartridge and backend gates.
6. **Independent verification:** inspect actual diffs, source provenance and
   test design; run applicable native/sanitizer, actual-WASM and protected CI
   checks plus CodeQL. Never remove an assertion to turn a failing proof green.

Use synthetic original cartridges only. Logs may contain hashes, counts and
model observations, not user ROMs, private RAM or checkpoint dumps. If any proof
core binaries are distributed as review artifacts, include their exact complete
modified source, build inputs and notices. Summary-only CI artifacts avoid an
unnecessary binary distribution.

## Following Integration

A later public control must reuse the proven lifecycle, expose requested and
effective identity in exports/comparison, preserve legacy/fallback behavior and
use Title Case labels. The proof alone does not add that menu, authorize a new
release or replace the approved Demo Cart. Experimental Demo Cart drafts require
their own explicit listening/gameplay acceptance.
