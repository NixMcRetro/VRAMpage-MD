# Demo Cart v0.3.7: Upbeat Original Soundtrack

**Experimental stacked on v0.3.6. Not approved for the default ROM or release.**

The owner found the v0.3.6 soundtrack too sad. This version removes its
minor-scale progressions and deliberately moves toward lively, bright
150-BPM arcade/demoscene music. The original six-scene 180-second production,
native Mega Drive rendering, approved captain portrait, chrome logo, and
Chroma Reactor A/B/C controls remain unchanged.

## Original Musical Redesign

- Seven-note major scales throughout; original ascending hooks and answering
  phrases, with a stronger return to the tonic at the finale.
- 900 original eighth-note tracker events, five per second at 150 BPM.
- Scene-local I-V-IV-V chord root progressions, with distinct major keys.
- Three hardware YM2612 FM voices for melody, bass and bright harmony.
- Faster PSG noise drum pattern: kick, snare and hi-hat on separate eighth notes.
- NTSC and PAL share the same 180-second song duration and 150 BPM tempo via
  five events/second on the VBlank-driven 68000 sequencer.

All music is newly authored and stored inside the cartridge. It is not
copyrighted-game music, browser audio, or an injected soundtrack.

## Review Scope

Build: `python3 demo-cart/show-lab/build_show.py`.

The CI workflow generates the standalone ROM, source reproducibility tests,
original native Genesis Plus GX NTSC/PAL screenshots and WAV excerpts.
A structural checksum is not proof of musical quality. Listen to the audio and
review video timing before accepting the soundtrack's new mood.

Source is stacked on the v0.3.6 draft PR. Neither candidate is approved as
the packaged Demo Cart; `site/cartridges.json` remains pinned to v0.3.5.
Do not merge, publish a GitHub release, or deploy McRetro.net without
separate explicit approval.

## Extended Native Listening Review

The experimental CI now captures fourteen seconds from each of the six show
scenes in both NTSC and PAL, using the actual Genesis Plus GX stereo FM/PSG
output. This provides twelve independently playable WAV files. The existing
`ntsc-original-score.wav` and `pal-original-score.wav` filenames are
retained for the introduction, but now contain fourteen seconds rather than
four. The review JSON records each recording's native frame range, peak,
duration and SHA-256 digest.

GitHub Actions uploads three temporary, separate review artifacts: a ROM-only
archive, the scene-audio archive, and the comprehensive show-review archive.
GitHub Actions downloads are ZIP files; the ROM-only archive contains just
the experimental `.bin`. These review artifacts expire after fourteen days
and are not GitHub releases or approved built-in cartridges. No musical notes,
ROM instructions, artwork, or default-cartridge manifest are changed by this
review improvement.
