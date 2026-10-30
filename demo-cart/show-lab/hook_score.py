"""Original owner-review ska-punk *phrase* for Mega Drive YM2612.

Exactly 100 eighth-note events at 150 BPM: 20 seconds, twelve 4/4 bars
plus a half-bar final A-major chord. A deliberately authored short passage,
NOT a procedural song-generation algorithm. The preview ROM retains the
180-second graphical show; after this 20-second audition the music stops.
No commercial song, sample, instrument preset or sound recording is used.
"""

# Concert-pitch melody. Each bar has eight 200 ms grid positions.
# "=" means genuinely sustain an FM key; "-" means key off.
# The first two bars state the rhythm, bars 3-6 introduce the hook,
# bars 7-10 answer it, bars 11-12 build, and the half-bar resolves.
CHORDS=("A","D","E","A","F#m","D","E","E","A","D","E","E","A")
LEAD=(
 "A4 = C#5 E5 = C#5 A4 -",
 "- B4 C#5 = E5 F#5 E5 -",
 "E5 = - C#5 E5 F#5 = -",
 "F#5 = A5 G#5 F#5 E5 = -",
 "- E5 F#5 G#5 = E5 C#5 -",
 "E5 = C#5 B4 A4 = - -",
 "C#5 = E5 F#5 = - E5 -",
 "F#5 E5 D5 C#5 B4 = - -",
 "- A4 C#5 E5 = C#5 A4 -",
 "B4 C#5 E5 = F#5 = E5 -",
 "F#5 = A5 = G#5 F#5 E5 -",
 "E5 F#5 G#5 A5 = F#5 E5 -",
 "A5 = = =",
)
RESPONSE=(
 "- - - - - - E4 -",
 "- - - A4 = - F#4 -",
 "- - A4 = - - C#5 -",
 "- - D5 = - C#5 - -",
 "- - B4 = - - E5 -",
 "- - A4 = - F#4 - -",
 "- - B4 = - - E5 -",
 "- - G#4 B4 = E5 = -",
 "- - A4 = - - E5 -",
 "- - F#4 A4 = - D5 -",
 "- - B4 = - - E5 -",
 "- - G#4 B4 = - E5 -",
 "C#5 = = =",
)
# One independent bass performance, including anticipations and rests.
BASS=(
 "A2 = E3 - A2 = C#3 E3",
 "D3 = A2 - D3 = F#3 C#3",
 "E3 = B2 E3 = G#3 E3 D#3",
 "A2 = E3 - A3 E3 C#3 -",
 "F#2 = C#3 - F#3 E3 C#3 E3",
 "D3 = A2 D3 = F#3 A2 C#3",
 "E3 = B2 - E3 = G#3 D#3",
 "E3 = B2 E3 = D#3 E3 G#3",
 "A2 = E3 - A2 C#3 E3 G#3",
 "D3 = A2 D3 = F#3 E3 C#3",
 "E3 = B2 E3 = G#3 B2 D#3",
 "E3 = B2 E3 G#3 B3 G#3 E3",
 "A2 = = =",
)
HORN_STABS=(
 "- - - - - - A4 -",
 "- - - - - - D5 -",
 "- - - - - - B4 -",
 "- - - - E5 = - -",
 "- - - - - - C#5 -",
 "- - - - - - A4 -",
 "- - - - - - B4 -",
 "- - - - - G#5 - -",
 "- - - - - - C#5 -",
 "- - - - - - D5 -",
 "- - - - - - E5 -",
 "- - G#5 = - - B4 -",
 "E5 = = =",
)

def _assert_notation():
    assert len(CHORDS)==len(LEAD)==len(RESPONSE)==len(BASS)==len(HORN_STABS)==13
    for part in (LEAD,RESPONSE,BASS,HORN_STABS):
        for index,row in enumerate(part):
            count=4 if index==12 else 8
            assert len(row.split())==count,(index,row,count)
    assert CHORDS[-1]=="A"
_assert_notation()

def make_hook_preview(score_pitch,show_pitch,chord_lookup):
    """Return native, interleaved six-FM-voice + PSG events for 20 seconds."""
    out=[]
    for bar,chord in enumerate(CHORDS):
        root,third,fifth=chord_lookup[chord]
        limit=4 if bar==12 else 8
        for beat in range(limit):
            lead=score_pitch(LEAD[bar].split()[beat])
            response=score_pitch(RESPONSE[bar].split()[beat])
            bass=score_pitch(BASS[bar].split()[beat])
            fill=score_pitch(HORN_STABS[bar].split()[beat])
            # Two voice chord stab on the *offbeat*, with a short
            # release on the following downbeat. The melody is
            # never derived from these chord positions.
            on=(beat%2==1 and bar!=12)
            skank=show_pitch(root+12+third) if on else (0,0)
            upper=show_pitch(root+12+fifth) if on else (0,0)
            # Opening is sparse; drums enter with full groove in bar 2.
            if bar==0:
                drum=1 if beat in (0,4) else 2 if beat==6 else 0
            elif bar==12:
                drum=1 if beat==0 else 0
            elif bar in (5,11) and beat==7:
                drum=4
            else:
                drum=1 if beat in (0,4) else 2 if beat in (2,6) else 3
            event=bytes((*lead,*response,*bass,*skank,*upper,*fill,
                        drum,int(beat==0),0,0))
            assert len(event)==16
            out.append(event)
    assert len(out)==100
    assert sum(any(row[ch] not in (0,255) for ch in (0,2,4,6,8,10))
               for row in out)>85
    return b''.join(out)
