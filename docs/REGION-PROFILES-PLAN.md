# Region Selection and Hardware Profiles

Status: implemented in development source, 28 October 2026 (Sydney).
Integration requires the verification gates below. Existing releases and the
hosted app are unchanged; physical VA profiles remain research.

## Runtime Region Selection

The runtime-core Region selector keeps the current NTSC-U default.
Choices: NTSC-U, NTSC-J, PAL (Europe), Auto, and Japan PAL (a core-supported
mode, not a verified motherboard profile). Keep country identity, video standard
and clock coherent. Record requested and effective settings separately.

Choosing a region stages it. Apply it on Load ROM or the existing Clean Restart,
with a visible pending-change message; selecting an option alone must not erase
a checkpoint or restart a running cartridge. CPU Reset retains the active region
and checkpoint. Applying a region through Clean Restart clears faults, drains
audio and discards the checkpoint through the existing lifecycle.

VA-specific profiles remain an evidence table until their mappings are verified.
The region selector must not claim a physical VA revision or solve issue #73.

## Source Basis and Integration

- Upstream pin `6090aff9e9b2f578cd28882bd4571d2e35b1d674`,
  `src/main/c/core/loadrom.c`: region_detect 1/2/3/4 selects USA, Europe,
  Japan NTSC and Japan PAL; 0 retains region detection. Separate VDP and
  master-clock overrides can otherwise create inconsistent combinations.
- Upstream `src/main/c/wasm/wasm.c:start()` resets defaults before loading the
  cartridge, then initializes audio and the system. A pre-start config setter
  alone would be overwritten. Store the requested choice separately and consume
  it after defaults, before load_rom; validate unsupported values atomically.
- The [patcher](../scripts/patch_core.py) preserves the normal core's USA/NTSC
  overrides. Runtime-only [region state](../scripts/region_profile_runtime.c)
  consumes the staged request after defaults and publishes observations after
  successful startup. Its [API shim](../scripts/region_profile_api.js) accepts
  exact integer IDs 0–4 and distinguishes unloaded state from observations.
- The [frontend](../site/app.js) uses observed cadence and viewport; the
  [framebuffer adapter](../site/framebuffer.js) validates variable geometry while
  preserving default missing-line recovery. PAL does not imply 240 visible
  lines; the VDP's active mode controls the viewport. Interlace is reported with
  native rendered height; double-resolution output remains disabled in this core.
- Native PAL/NTSC use 313/262 lines. Derive cadence from native timing rather
  than hardcoding 50/60. Verify returned audio sample counts and full buffer
  bounds at 44.1 kHz; the wrapper's 2048-sample allocation needs explicit checks.

## Smallest Complete Integration

1. Add requested/effective region APIs only under VRAM_TX_RUNTIME, using the
   existing runtime API shim/build-manifest pattern. Preserve the normal/fallback
   profile's fixed NTSC-U behavior and binary hashes. Detect API absence and
   disable/refuse unavailable changes explicitly.
2. Expose effective region, clock, frame timing and viewport; distinguish
   unloaded/unavailable state from an observed setting. Preserve the selected
   request across starts; ROM load and Clean Restart apply it before native init.
3. Use native cadence, viewport and returned audio counts in scheduling, display,
   RGB output and status. Preserve existing raw-output and display-recovery
   semantics; define and test interlace/geometry handling before claiming support.
4. Include machine-region identity in experiment exports and comparison. Legacy
   exports without it compare Unknown. Existing circuit files remain fault-only:
   preview/apply does not silently switch machine region or restart a cartridge.
5. Reuse lifecycle cleanup for pending loads, held inputs, audio, fault pulses,
   automatic CPU recovery and checkpoints. Eight-frame operations remain eight
   native frames, so their wall-clock duration differs between standards.

## Acceptance Before Integration

- Original synthetic cartridges verify software-visible region, native effective
  timing/clock, 262/313 lines, viewport boundaries and bounded finite audio.
- Default NTSC-U frames, PCM, memory and fault behavior match the existing runtime
  under equivalent inputs. New runtime binary hashes will change; record new
  provenance, while normal/fallback hashes and historical artifacts stay intact.
- Cover every supported selection, Auto/header cases, invalid values, staging,
  repeated restarts, rejected/stale loads and unavailable legacy API behavior.
- Verify checkpoint retention on CPU Reset and invalidation on region application,
  eight-frame contacts/recovery semantics, audio cleanup and export comparisons.
- Require native sanitizers, actual-WASM checks, independent specialist review,
  three-browser/package CI, CodeQL and the active main ruleset. Inspect actual
  required checks rather than assuming that the older seven-job list is complete.

## Evidence Boundary for VA Profiles

[VA6 validation](VA6-RAM-VALIDATION.md) currently supplies a candidate HM65256B
pinout and PAL VA6.5 reference. NTSC VA6 part/package markings, byte lanes and
address/control routing remain unverified. Other boards and the pinned MiSTer
HDL in [VRAM research](VRAM-TIMING-RESEARCH.md) can support comparisons without
establishing an original PCB trace map. Do not infer a VA revision from a ROM's
region or expose unverified profiles as physically accurate simulations.

Independent Luna High feasibility and implementation reviews checked startup,
region overrides, timing and runtime guards. Actual-WASM and browser cartridges
exercise software-visible regions, nonzero pixels/PCM/RAM and default parity;
see [Testing](TESTING.md#region-selection-development-checks). The queue/status
checkpoint records final CI and integration evidence. This does not establish
gameplay compatibility or analogue/electrical accuracy.
