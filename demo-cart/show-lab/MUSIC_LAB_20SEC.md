# Music Lab: Original 20-second Ska-Punk Hook

This is an **experimental audio-only composition review**, not a release or
replacement of the approved v0.3.5 Demo Cart or the earlier v0.3.8 draft.

The original FM instrument programming wrote S1,S3,S2,S4 slots as though they
were S1,S2,S3,S4. The correct hardware offset sequence for naturally ordered
operators is 0,8,4,12. The original F-number frequency equation was also
off by a factor of two. The pitch formula now uses a note-relative block
and `2^(21-block)`, matching YM2612 note tables and concert pitch.

A separate environment flag `VRAMPAGE_HOOK_PREVIEW=1` builds a preview ROM
with **100 hand-authored 150-BPM eighth-note events (20 seconds)**. It has
twelve complete bars and a half-bar ending with original brass call/response,
specifically written bass notes, restrained two-voice offbeat chords, a short
break and final cadence. The rest of the 180-second graphical show remains,
but the audition intentionally contains no further score events after 20
seconds. The original complete 180-second score remains the normal build.

The native CI test captures **20 seconds of actual Genesis Plus GX stereo
PCM** in NTSC and PAL and records time-binned RMS and peak levels.
It proves audible output and timing only, not musical quality.

Never modify the global Genesis Plus GX mixer or ship this as the default
cartridge. No merge, public release or website deployment without owner approval.
