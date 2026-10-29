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

## v0.3.8 Audio Balance Refinement

The user reported PSG drums overwhelming the six-voice YM2612 score. This
experimental cartridge now attenuates the PSG kick, snare, hat and fill to
8, 9, 12 and 8 respectively, on the genuine SN76489-compatible
0 (loudest) through 15 (silent) volume scale. A 68000 routine advances
noise attenuation each VBlank, fading every hit to silence within three
to eight frames. This applies to both NTSC and PAL.

The six original FM instrument patches each reduce carrier total level by
five register steps for greater brass, bass and offbeat keyboard presence.
The melody, song timing, VDP effects, original logo and portrait, and
controller inputs are unchanged. PSG decay state is explicitly reset at
boot, at show start, and at show stop.

This fix is **entirely inside the Demo Cart ROM**. Neither Genesis Plus GX's
audio mix nor the website, other cartridges, approved v0.3.5 ROM, or
v0.5.1 website package is modified. Human listening remains necessary
to decide whether this first balance adjustment is satisfactory.

## Six-Voice Timbre Refinement

The owner accepted the improved PSG balance and requested more distinctive
instrument sounds. This experimental v0.3.8 pass preserves the 180-second
song, all 900 score events, the per-VBlank PSG drum fade, visual effects,
portrait, logo and controller behaviour. Only the six FM patch definitions
and their native YM2612 register programming change.

| FM voice | Original sound design | Algorithm |
| --- | --- | --- |
| Brass lead | Brighter two-stack attack and warm dual carriers | 4 |
| Brass answer | Softer, nasal answering three-carrier horn | 5 |
| Walking bass | Strong low fundamentals with subtle harmonics | 7 |
| Offbeat ska chop | Quick, plucked, fast-decaying two-stack tone | 4 |
| Organ accents | Sustained additive organ drawbar-style tone | 7 |
| Horn fills | Bright three-carrier staccato counterphrase | 5 |

All four operators on each FM voice have independent TL, attack, initial
decay, secondary decay, and sustain/release settings. The ROM writes those
registers to the real YM2612 address ports. This does not alter the shared
emulator audio mixer, the website, or the approved v0.3.5 cartridge. Objective
native playback tests and owner's listening assessment remain essential.
