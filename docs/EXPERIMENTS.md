# Work RAM experiment procedure

This is an initial protocol for comparing an attract-mode baseline with one
modeled work-RAM fault. It records observations without assuming a desired
glitch. A game crash or stopped CPU is a result to record, not something the
emulator should hide or repair.

## Record the setup

Use a legally obtained local cartridge through **Load ROM**. Keep the ROM outside
the repository and record only its title, region and SHA-256 fingerprint. Do not
copy ROM bytes or RAM contents into the experiment record. Record:

- Date, browser/OS, VRAMpage model version and pinned emulator-core revision.
- ROM title/region and SHA-256; do not include the ROM or copyrighted screenshots.
- The reset/restart method and the point at which the attract demo begins.
- Fault domain (RAM), fault kind (address or data), selected pair, direction
  (read, write or both), activation frame, and the run length.
- Exported CPU STOP/HALT state, fault counters, visible behavior, and any crash,
  reset, audio or input changes. Preserve the exported metadata with the notes.

The built-in export includes the ROM hash, model version, core revision, fault
configuration, activation frame and reset state. If its hash is `null`, calculate
it locally and record it separately. Check the export before sharing it; it must
not contain ROM bytes, RAM bytes or local file contents.

## Baseline and fault run

1. Load the cartridge and start from a clean reset. Leave all fault domains open.
   Do not provide controller input during the attract demo. If a title requires
   an input before it begins, record that input and apply it at the same point in
   every run.
2. Let the game reach the attract demo. Choose a reproducible point using the
   panel's **Current frame** counter and a run duration. Record the frame range
   and observe a zero-fault baseline for that interval, including the displayed
   scene and CPU state. Download the baseline metadata too.
3. Clean-restart and repeat the same setup. Confirm the VRAM domain is inactive.
   Select one RAM address or data pair and choose read, write or both. Keep the
   controller input schedule unchanged.
4. At the same attract-demo point and displayed frame N, press **Apply RAM fault**.
   Record the activation frame shown in the panel/export. Continue for the same
   interval or until the game stops/crashes. Record the observed behavior and
   CPU monitor state. Do not edit game variables or choose another fault mid-run.
5. Disconnect the fault and note whether changed RAM effects remain. Disconnect
   does not roll back writes made while the fault was active; the panel retains
   the last experiment's counters until a new fault or clean restart.
6. Download the metadata and save it with the notes outside the repository before
   starting another experiment. Record the clean-restart state separately.
7. If a screenshot or video is useful, keep it private and outside the repository;
   never commit copyrighted game imagery.

Repeat the baseline and fault run from the same reset state if the result is
unclear. Report both runs, including no visible change. Do not generalize one
cartridge's result to other games or board revisions.

## Explicit recovery trials

For v2.1, treat force resume and CPU-only reset as separate interventions,
not part of the uninterrupted fault baseline. Exported `cpuInterventions` records
the action/frame and before/after flags. Download records before clean restart.
See [CPU recovery](CPU-RECOVERY.md); record failures as well as apparent recovery.

## Run record template

| Field | Value |
| --- | --- |
| Date / browser / OS | |
| ROM title / region / SHA-256 | |
| Core revision / model version | |
| Reset method / attract start frame | |
| Baseline interval / observation | |
| Fault kind / pair / direction | |
| Activation frame N / run interval | |
| CPU STOP/HALT / counters / observed result | |
| Disconnect persistence / clean-restart result | |
| Export reviewed for ROM/RAM bytes | |

## Initial actual-cartridge results — 22 October 2026

The supplied 512 KiB Sonic backup, SHA-256
`46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`,
was run in the actual Emscripten 4.0.23 core under Node, with all external
controller inputs zero, sound consumed each tick, and no variable edits. This
is deterministic frame stepping, not browser timing or physical-hardware testing.

Reproduce privately from the repository root after building:

```sh
node scripts/run-ram-experiment.cjs /private/path/cartridge.md > /tmp/results.json
```

The runner executes a baseline and three generic configurations twice each,
activates immediately after tick 1800, and samples ticks 1800, 2400 and 3000.
It exports only SHA-256 digests, counters and flags. The
[recorded results](experiments/2026-10-22-work-ram.json) contain no game bytes.
All four cases reproduced identical sampled results on their second run.

| Configuration | Affected accesses at tick 3000 | CPU flags | Observation |
| --- | ---: | ---: | --- |
| No fault | 0 | 0 | Baseline frame/RAM hashes changed over time |
| A1/A2 read (WA0/WA1) | 327 reads | 2 (HALT) | Frame/RAM hashes stopped changing by tick 2400 |
| D0/D1 read | 955877 reads | 0 | Different frame/RAM hashes; both static from 2400 to 3000 |
| D0/D1 write | 956592 writes | 0 | Different frame/RAM hashes; both static from 2400 to 3000 |

The data cases show why a zero STOP/HALT flag is not a reliable healthy-game
indicator: affected accesses continued despite static sampled output. These
runs establish repeatable corruption and one halted CPU, **not** successful
attract-mode desynchronisation. The scene at activation and continued internal
demo-controller playback were not instrumented or verified. Those remain the
next experiment; do not infer them from zero external input or advancing ticks.

Separately, a disabled-fault comparison against the preceding display core ran
3000 ticks. Full framebuffer and left-channel audio hashes at ticks 1, 600,
1200, 1800, 2400 and 3000 matched exactly. This is sampled regression evidence,
not exhaustive equivalence or audible-playback verification.
