# Demo Cart v0.3.8: Original Brass-Led Ska-Punk Score

**Experimental owner review only. Stacked on v0.3.7. Not an approved built-in cartridge.**

The user chose a lively ska-punk direction, with the bouncing offbeats, melodic
bass and instrumental brass call-and-response common to the genre. A band and
song were mentioned as a mood reference; **this is an independent composition**,
not an arrangement, remake, transcription or imitation of that copyrighted song.

## Original Musical Arrangement

- Keep the established 180-second NTSC/PAL six-scene show and 150 BPM tempo.
- Use 900 sixteen-byte tracker events at five eighth-note events per second.
- Six native YM2612 FM voices: lead horn, answering horn, walking bass,
  clipped offbeat organ/guitar, chord accents, and horn fills.
- Correct YM2612 bank-zero and bank-one port writes for all six channels,
  including the special key-on channel codes 0, 1, 2, 4, 5, and 6.
- Original melodies, scene-specific brass rhythms, chord changes, rising fills,
  and a recurring original hook connecting the introduction and finale.
- Native PSG noise percussion provides interleaved kick, snare, hi-hat and
  transition fills, respecting the fact that the noise channel is monophonic.
- The final 25 seconds feature a fuller six-voice musical climax.
- Retain existing Z80/YM2612 reset-line correction, regional VBlank timing,
  approved portrait and metallic logo, controller input and all native VDP effects.

The score is authored as hardware register events in the ROM. It is neither
browser audio nor a recording of a commercial song. No commercial ROM assets
are bundled. The music is intentionally original, but still requires human
listening and timbre balancing before it can be called finished.

## Owner Review and Download

The experimental native test records fourteen seconds from every scene in
NTSC and PAL, twelve WAV excerpts from the actual Genesis Plus GX FM/PSG
buffers. The CI run also packages a separate ROM-only artifact containing
`VRAMpage-MD-Demo-Cart-v0.3.8-Show.bin`. GitHub serves Actions
artifacts as ZIP archives, with fourteen-day retention.

The new ROM remains experimental. Source tests, actual NTSC/PAL Genesis Plus
GX playback, relevant browser checks and a human listening comparison are
needed. In particular, test the FM bank-one tones and the dynamic changes,
rather than assuming that successful note-table generation proves audible
music. Physical Mega Drive testing is not yet claimed.

## Approval Boundary

PR v0.3.8 is stacked on the v0.3.7 draft. It must not be merged until the
dependency and review sequence is deliberately resolved and explicitly
approved. `site/cartridges.json` remains pinned to the approved
v0.3.5 Demo Cart, and application `VERSION` remains 0.5.0.
No public release, GitHub Pages or McRetro.net deployment is authorised.
