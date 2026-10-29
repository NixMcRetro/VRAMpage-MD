# VRAMpage MD v0.5.1 compiled-core licence audit

**Scope and evidence.** This is a source-level inventory of the actual browser runtime shipped by main commit `996d353` (not a generic inventory of every file in the vendor tree). The release profile records JS SHA-256 `e8da1c28303fd3900f35c032ce01802c76d1d041dc8a0d6cd57bdc97ee3af4d0`, WASM SHA-256 `8fa2fa0fe6a47890c948ed39a7f095980d9ffde7d4405a88ce07a5f34b8814b7`, and pinned `h1romas4/wasm-genplus` source commit `6090aff9e9b2f578cd28882bd4571d2e35b1d674` ([verified complete main bundle](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40809766464/artifacts/12870445297), entry `site/source/runtime-profile/BUILDING.txt`). The modified corresponding tree is under `site/source/runtime-profile/source/wasm-genplus`; the adjacent `scripts/` and site `source/` files contain VRAMpage changes. The build record describes this source and the repeatable Emscripten/CMake/Make commands ([pinned builder](https://github.com/NixMcRetro/VRAMpage-MD/blob/996d35310e03d1fc67a8e4c1681e090c6edff227/scripts/build-core-runtime.py#L233)).

The pinned upstream CMake file explicitly enumerates translation units in lines 8–63, sets `HAVE_YM3438_CORE` at line 81, and the project builder adds the runtime flags and API shims to the generated CMake file ([immutable CMake source](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/CMakeLists.txt#L8-L83)). It compiles `z80.c`, Musashi `m68kcpu.c` and `s68kcpu.c`, Genesis Plus GX core, YM2413, YM2612, Nuked OPN2/YM3438, `blip_buf.c`, `eq.c`, both NTSC implementations, and the listed cartridge, CD and WebAssembly support files. It does **not** list Tremor or FAME translation units. Their presence in the complete source archive does not establish their inclusion in this binary. The CMake list includes `scrc32.c` (at `src/main/c/wasm/scrc32.c`), not a `core/wasm` path.

## Approved Hosting and Follow-Up

On 29 October 2026 the owner approved proceeding with the release/website
workflow and confirmed **“Non-commercial hobby site; no monetization.”** Public
free hosting is not prohibited by the quoted terms. The standalone app has no
advertising, payment or sponsorship integration. Reassess the non-commercial
condition if that context changes; this is a recorded owner fact, not a finding
about an unknown monetized service.

The upstream [project-wide licence at immutable commit
9bb64c47](https://github.com/ekeeke/Genesis-Plus-GX/blob/9bb64c47f969dffe44c4bafe1f2651b88652ab36/LICENSE.txt#L2-L38)
expressly says “Unless otherwise explicitly stated, all code in Genesis Plus GX
is released under the following license”. Its non-commercial/source terms match
the pinned core's terms. The pinned YM2612/YM2413 headers attribute their authors
and origin without an alternative grant or exception. This supports applying the
GX default licence, while preserving those headers; MAME ancestry alone is not
evidence of a missing grant or modern MAME's different licence.

Musashi's exact 836-byte licensing/copyright comment is embedded unaltered as a
named `license.Musashi` WebAssembly custom section. Deterministic build tooling
retains the source notice, checks its bytes and reproduces the packaged module.
The [WebAssembly specification](https://webassembly.github.io/spec/versions/core/WebAssembly-2.0.pdf)
defines custom sections as metadata ignored by execution semantics. Removing
only this added section recovers the previous binary byte for byte; actual
module validation, browser execution and independent source rebuild remain
required. The historical raw hashes above identify the original executable
sections; the release build record identifies the notice-bearing binary hash.

The same-origin source ZIP remains the chosen accompaniment, with the exact
served binaries included in that ZIP. This avoids relying on a GitHub-only
interpretation. A matching release artifact is an additional mirror. These
concrete source/notice measures and the confirmed non-commercial context support
proceeding with this distribution; no licence itself requires an external legal
opinion as a prerequisite. This is a reasoned packaging assessment, not a legal
guarantee for every possible future hosting arrangement.

## Licence and attribution inventory

| Compiled component | Evidence and material terms | Distribution implication |
|---|---|---|
| Genesis Plus GX, including the `wasm-genplus` wrapper/core build | `genesis.c` calls for non-commercial distribution and says modified-source redistributions “must include the complete source code, including the source code for all components used by a binary built from the modified sources” ([source, lines 10–26](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/genesis.c#L10-L26)). The wrapper README calls this a Genesis-Plus-GX WebAssembly port, gives build steps, and points to the Genesis Plus GX licence ([README, lines 104–106](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/README.md#L104-L106)). | Treat the full staged, modified source and notices as required for the binary. Preserve the exact upstream notices and VRAMpage modification marks. Do not infer additional rights from the wrapper README. |
| Nuked OPN2 / YM3438 | `ym3438.c` is compiled and its source is enabled by `HAVE_YM3438_CORE`; its notice independently repeats non-commercial and complete-corresponding-source conditions ([source, lines 1–21](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym3438.c#L1-L21)). | Preserve source/header notices and ship the source actually used. |
| Musashi 680x0 CPUs | Both CPU implementation files are in CMake. `m68k.h` requires the copyright notice to remain unaltered “in the source code and any binary files containing this code in compiled form” and limits the stated permission to non-commercial use ([header, lines 7–23](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/m68k/m68k.h#L7-L23)). | Make the notice accessible with the distributed binary; do not remove it from compiled-source copies. Include complete relevant Musashi sources. |
| Z80 | Compiled `z80.c` says freeware for non-commercial purposes; redistribution requires credit, modified source files need modification notices, and the full notice must remain in source ([source, lines 1–18](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/z80/z80.c#L1-L18)). | Retain its entire header, list the author in credits, and mark modified files. |
| YM2612 and YM2413 FM implementations | Both `.c` files are compiled. YM2612 attributes original code to MAME's `fm.c`, Jarek Burczynski and Tatsuyuki Satoh ([source, lines 1–18](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2612.c#L1-L18)); YM2413 attributes copyright to Jarek Burczynski ([source, lines 1–8](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/ym2413.c#L1-L8)). | Retain full source/header notices and do not call the YM2612 implementation a separate FAME core. Build inventory shows these files, not FAME. |
| blip_buf | Compiled source offers LGPL 2.1-or-later ([source, lines 19–28](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/blip_buf.c#L19-L28)). | Include the full LGPL text and component source; analyze linked-WASM relinking requirements separately below. |
| MD NTSC and SMS NTSC | Both implementations are compiled. Their notices identify Shay Green and LGPL 2.1-or-later ([MD source, lines 8–17](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/ntsc/md_ntsc.c#L8-L17); [SMS source, lines 8–17](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/ntsc/sms_ntsc.c#L8-L17)). | Include `core/ntsc/license.txt`, headers, implementation files and other corresponding NTSC sources. |
| EQ | Compiled `eq.c` says it is public domain for all purposes, including commercial applications ([source, lines 7–16](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/sound/eq.c#L7-L16)). | Preserve provenance; this notice is not the source of the emulator's non-commercial restriction. |
| CRC32 and other core/support files | CMake compiles `scrc32.c` and many core/platform units. `scrc32.c` contains its own attribution and redistribution conditions ([source, lines 1–26](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/wasm/scrc32.c#L1-L26)). | Include the complete source tree and retain per-file notices; do not limit the archive to the headline emulator files. |

The upstream non-commercial and corresponding-source wording is repeated in more than Genesis Plus GX (for example YM3438), so omitting a compiled component's source is not cured by retaining only the main core. Conversely, this inventory does not assert that every file in the vendor tree is linked into the runtime.

## Source delivery recommendation and limits

For the v0.5.1 browser package, the conservative delivery is one version-matched ZIP on the same McRetro origin containing the exact `genplus.js` and `genplus.wasm`, the **complete modified corresponding source** used to build those files, the build scripts/configuration and frontend/launcher source, and a notices/licenses document with full upstream headers/text. Include the pinned vendor source tree, VRAMpage patch/build scripts and API shims; retain unmodified component notices and mark every changed file as required by its applicable notice. The existing build record identifies the source location and build invocation, and the existing third-party notices record the terms and named components ([pinned builder](https://github.com/NixMcRetro/VRAMpage-MD/blob/996d35310e03d1fc67a8e4c1681e090c6edff227/scripts/build-core-runtime.py#L233); [tracked notices](../THIRD-PARTY-NOTICES.md)). Link the archive prominently from the package instructions and keep it available with the binary version. A checksum and pinned commit/build identifiers make the source-binary match reviewable.

A complete, version-matched source ZIP attached to the corresponding GitHub release would provide a useful durable mirror. If GitHub is the only source location, whether linking or “accompanying” the runtime satisfies the core's literal requirement to “include” source is an interpretation question; the text does not specify a hosting protocol. A same-origin package including both removes that avoidable ambiguity. This is a conservative distribution recommendation, not a legal conclusion.

The LGPL components add separate obligations. LGPL 2.1 section 6(a) expressly permits accompanying an executable with the complete machine-readable library source **and** the complete machine-readable source and data/utility programs for the “work that uses the Library,” so the user can modify the library and relink the executable ([licence, lines 278–325](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/ntsc/license.txt#L278-L325)). On this build, a complete app source package plus modified library sources, exact compile/link flags, scripts and reproducible Emscripten/CMake build is a plausible §6(a) route; the candidate archive extracted from `7a28b7a` was independently rebuilt with Emscripten 4.0.23 and both output hashes match exactly (see the [rebuild and footprint record](LIGHTWEIGHT-DEPLOYMENT-v0.5.1.md)). This is technical evidence for the complete-source/relink route, not resolution of every licence interpretation. Section 6 also requires prominent notice that the Library is used, a copy of the LGPL, and preserves reverse-engineering permission for debugging modifications ([same licence, lines 275–284](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/ntsc/license.txt#L275-L284)). Do not describe object files as categorically mandatory where the complete-source §6(a) route is used; ensure the package actually contains every required source, input and utility needed to modify and relink the final executable. The package builder should preserve the complete LGPL text already present at `src/main/c/core/ntsc/license.txt` and all component notices.

The core's non-commercial condition warrants an owner decision on the proposed host/activity. Whether ordinary site advertising, analytics, sponsorship or other monetization makes this distribution a “commercial product or activity” is not resolved by the source wording or this audit. This report makes no finding that McRetro.net violates that condition. The installed Emscripten 4.0.23 `LICENSE` describes the tool as dual MIT / University of Illinois-NCSA licensed and says third-party compiler subdirectory code is not used by default; this audit makes no blanket GPL-exception claim; the actual link trace and retained standard-runtime notices below supplement that compiler-level notice. Retain applicable Emscripten/runtime notices with the package after checking the actual generated JS. ROM and trademark rights are outside these component licences, and no third-party game ROM is part of this audit.

**Limit.** This is a factual source/build inventory and conservative packaging recommendation, not legal advice. The owner has confirmed the non-commercial context, and complete source plus byte-exact rebuilding supplies the technical basis for the LGPL source/relink route. Seek qualified clarification if the hosting context changes or a different source-delivery arrangement is proposed.

## Questions That Packaging Alone Does Not Settle

- **GitHub-only delivery:** the custom Genesis Plus GX/Nuked conditions do not
  say that an external link satisfies “include”. Keep the complete same-origin
  archive as the default. Qualified advice or rights-holder clarification is
  needed before removing it; LGPL guidance cannot answer that separate clause.
- **Musashi binary wording:** the notice-bearing build puts the exact source
  notice inside the WASM itself, addressing the literal binary-notice condition
  without changing executable sections. Keep the metadata and its verification
  in future builds; a separate web page alone was not the chosen solution.
- **Legacy FM provenance:** the project-wide default grant and absence of a
  file-specific alternative provide the permission basis described above.
  Preserve author/MAME attributions; do not relabel this code as modern MAME GPL.
- **Non-commercial activity:** source availability does not remove these terms.
  The owner confirmed this distribution is an unmonetized hobby activity. Revisit
  the grant before introducing advertising, paid access or commercial use.

The owner has now approved the release/deployment workflow, subject to its
technical review and CI gates. The same-origin ZIP must remain available with
the corresponding runtime; GitHub-only delivery remains outside this decision.
The pinned Emscripten licence text is
preserved in `licences/EMSCRIPTEN-LICENSE.txt`; the compiler/system-component
exception is not used to omit the emulator or application source.

## Actual Standard-Library Link Trace

The same approved object files and link flags were relinked with `-Wl,--trace`
into a separate scratch directory. Both output hashes stayed identical. The
linker selected members of `libc.a`, `libc_optz.a`, `libstubs.a`, `libdlmalloc.a`
and `libcompiler_rt.a`. This confirms standard runtime code is in the binary,
even though compiler source itself need not be bundled under the core's system
component exception. Notice-retention duties are separate from that exception.

The package therefore also preserves musl's complete COPYRIGHT/MIT file, the
LLVM compiler-rt Apache2/LLVM-exception licence, original leading notices from
the selected musl math sources (including Sun/Arm terms), and dlmalloc's public
domain attribution. The complete source ZIP and HTML notices page both carry
these texts. This does not retroactively apply LGPL/GPL or commercial permission
to the separately licensed emulator. The installed source corresponds to
Emscripten4.0.23; canonical source examples are
[`musl/COPYRIGHT`](https://github.com/emscripten-core/emscripten/blob/4.0.23/system/lib/libc/musl/COPYRIGHT),
[`compiler-rt/LICENSE.TXT`](https://github.com/emscripten-core/emscripten/blob/4.0.23/system/lib/compiler-rt/LICENSE.TXT)
and [`dlmalloc.c`](https://github.com/emscripten-core/emscripten/blob/4.0.23/system/lib/dlmalloc.c).
The trace and selected-notice inventory are retained with local verification
evidence under `/workspace/scratch/lightweight-v051/toolchain-link-audit`.
