# Development work queue

Read with [development status](DEVELOPMENT-STATUS.md), [roadmap](../ROADMAP.md)
and [versioning](VERSIONING.md). Status describes evidence, not promised effects.

| Priority | Work | Dependencies and acceptance | Assignment | Status |
|---|---|---|---|---|
| Done | Verify corrected v0.2.4 distribution | Public checksum, exact tag/source/version, JS/WASM, source/notices, executable launcher and actual-core local launch | Basic packaging worker, coordinator | Fresh public download, checksum, package and unmocked launcher/core verification passed |
| Done | Deliver v0.2.6 experiment build identification | Nonblocking metadata, explicit unavailable fallback, unchanged fault models, package identity, three-browser CI, specialist review and public ZIP | Basic implementation/packaging workers; Luna High independent review | PR #20 merged as 6d18f8e after all required CI passed; release workflow 39767990645 passed; fresh public ZIP checksum, exact source/tag, unmocked launcher and actual-core export verified |
| Done | Keep superseded legacy release deleted | Preserve existing source tag and historical evidence; do not restore release entry or assets | Coordinator | User explicitly reaffirmed deletion; no restoration attempted |
| P1 | Establish reproducible attract-mode observation | Privately available legal ROM, confirmed scene and internal demo playback, equivalent reset and external input schedule, read-only diagnostics and evidence without game bytes | Luna High investigation/implementation plus independent specialist review | Private cartridge supplied with matching historical SHA; Luna High read-only investigation underway. Acceptance incomplete; do not infer demo input from ticks, CPU flags or hashes |
| P1 | Repeat baseline and bounded fault candidate | Previous item; exact version/source/core/ROM hash/settings/activation/release frames; repeated baseline and fault run, continued demo input, measured divergence, no silent recovery | Luna High experiment design; basic runner support | Blocked on demonstrated scene/internal playback observation; private cartridge now supplied |
| P2 | Transaction-level VRAM | RAM-stage acceptance and bounded architecture/test plan; VDP read/write/cache/timing coverage, normal-output regression, independent specialist review | Luna High | Not started; reserve v0.3.0 |
| P3 | Hardware-informed audio bending | Earlier milestones, research and clean-audio regression; YM2612/PSG/Z80 bus/register/memory models, no post-mix substitute | Luna High | Not started; reserve v0.4.0 |

## Continuation procedure

1. Fetch main and open PR/release/CI state; read the linked status and AGENTS.md.
2. Finish any pending P0 verification/publication before new emulator changes.
3. Select the first unblocked P1 item. Inspect existing experiment runners before
   adding instrumentation. Use a bounded Luna High assignment and independent
   review for changes to emulator internals.
4. If no private legal cartridge is available, prepare ROM-free diagnostic tests
   and record the precise remaining actual-game blocker. Never download a
   commercial ROM or claim synthetic tests satisfy the attract-mode milestone.
5. Record exact tested commits, evidence and limitations. Preserve earlier results.
