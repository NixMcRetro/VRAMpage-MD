#!/usr/bin/env python3
"""Experimental original Mega Drive FX expansion using a deliberately small 68000 encoder.

No proprietary ROM, external assembler or network dependency. Reviewed asset input
is mandatory; run only with matching approved asset files.
"""
from __future__ import annotations
from pathlib import Path
import json, hashlib, struct, zipfile, math, colorsys

ROOT = Path(__file__).resolve().parent
BASE_KIT = ROOT.parent / 'VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip'
APPROVED_KIT_SHA256 = 'fb073ee201ce73072c83a569742a644c2f8c7816e102ffd55ce723154bd67403'
assert hashlib.sha256(BASE_KIT.read_bytes()).hexdigest() == APPROVED_KIT_SHA256, 'Base ROM source kit changed'
OUT = ROOT / 'build'
OUT.mkdir(exist_ok=True)
with zipfile.ZipFile(BASE_KIT) as archive:
    PATTERNS = archive.read('demo-cart/assets/title_patterns.bin')
    TILEMAP = archive.read('demo-cart/assets/title_tilemap_viewport.bin')
    CRAM = archive.read('demo-cart/assets/title_cram.bin')
assert len(PATTERNS) % 32 == 0 and len(TILEMAP) == 40*28*2 and len(CRAM) == 128
pattern_count = len(PATTERNS)//32
assert all((int.from_bytes(TILEMAP[i:i+2],'big') & 0x7ff) < pattern_count for i in range(0,len(TILEMAP),2))

class A68:
    def __init__(self):
        self.data=bytearray(0x200)
        self.labels={};self.fixups=[]
    def here(self): return len(self.data)
    def w(self,x): self.data+=struct.pack('>H',x & 0xFFFF)
    def l(self,x): self.data+=struct.pack('>I',x & 0xFFFFFFFF)
    def label(self,n):
        if n in self.labels: raise ValueError(n)
        self.labels[n]=self.here()
    def branch(self,op,n):
        self.w(op); pos=self.here();self.w(0);self.fixups.append((pos,n,2))
    def absref(self,n):
        p=self.here();self.l(0);self.fixups.append((p,n,4))
    def movea(self,reg,addr):self.w(0x207C+(reg<<9));self.l(addr)
    def movea_ref(self,reg,n):self.w(0x207C+(reg<<9));self.absref(n)
    def movew_imm_d(self,reg,value):self.w(0x303C+(reg<<9));self.w(value)
    def movew_imm_ai(self,reg,value):self.w(0x30BC+(reg<<9));self.w(value)
    def movel_imm_ai(self,reg,value):self.w(0x20BC+(reg<<9));self.l(value)
    def moveb_imm_ai(self,reg,value):self.w(0x10BC+(reg<<9));self.w(value)
    def moveb_d_ai(self,dr,ar):self.w(0x1080+(ar<<9)+dr)
    def movew_d_d(self,src,dest):self.w(0x3000+(dest<<9)+src)
    def addiw(self,reg,imm):self.w(0x0640+reg);self.w(imm)
    def movew_d_ai(self,dr,ar):self.w(0x3080+(ar<<9)+dr)
    def movew_a_post_ai(self,source,dest):self.w(0x3000+(dest<<9)+(2<<6)+(3<<3)+source)
    def moveb_ai_d(self,ar,dr):self.w(0x1000+(dr<<9)+(2<<3)+ar)
    def movew_ai_d(self,ar,dr):self.w(0x3000+(dr<<9)+(2<<3)+ar)
    def addq(self,reg,n=1):self.w(0x5040+(n<<9)+reg)
    def subq(self,reg,n=1):self.w(0x5140+(n<<9)+reg)
    def andiw(self,reg,imm):self.w(0x0240+reg);self.w(imm)
    def andib(self,reg,imm):self.w(0x0200+reg);self.w(imm)
    def moveq(self,reg,v): self.w(0x7000+(reg<<9)+(v & 255))
    def dbra(self,reg,label):self.branch(0x51C8+reg,label)
    def bsr(self,label):self.branch(0x6100,label)
    def bra(self,label):self.branch(0x6000,label)
    def beq(self,label):self.branch(0x6700,label)
    def bne(self,label):self.branch(0x6600,label)
    def tstb(self,reg):self.w(0x4A00+reg)
    def rts(self):self.w(0x4E75)
    def append(self,n,blob):
        if len(self.data)%2:self.data+=b'\0'
        self.label(n);self.data+=blob
    def final(self):
        for pos,n,kind in self.fixups:
            target=self.labels[n]
            if kind==2:
                disp=target-pos
                if not -32768 <= disp <= 32767:raise ValueError(f'branch out of range {n} {disp}')
                self.data[pos:pos+2]=struct.pack('>h',disp)
            else:self.data[pos:pos+4]=struct.pack('>I',target)
        return self.data

# Procedural original graphics. These never alter the user's portrait or logo.
PHASES=96
FX_TILE_COUNT=256
FX_BASE=pattern_count+2

def genesis_colour(red,green,blue):
    return ((round(red*7)&7)<<1)|((round(green*7)&7)<<5)|((round(blue*7)&7)<<9)

def fx_patterns():
    # 16 orientations x 16 phases, using coherent tile-local diagonal ribbons.
    out=bytearray()
    for angle in range(16):
        theta=angle*math.tau/16
        dx,dy=math.cos(theta),math.sin(theta)
        for phase in range(16):
            pixels=[]
            for y in range(8):
                for x in range(8):
                    u=(x-3.5)*dx+(y-3.5)*dy
                    # Intentional 0..15 phase bands, with a thin bright accent.
                    position=(phase*0.95+u*1.28) % 15
                    colour=1+(int(position)%15)
                    pixels.append(colour)
            for i in range(0,64,2):out.append(pixels[i]<<4|pixels[i+1])
    assert len(out)==FX_TILE_COUNT*32
    return bytes(out)

FX_PATTERNS=fx_patterns()
assert (FX_BASE+FX_TILE_COUNT)*32 < 0xC000, 'Tile patterns overlap Plane A at $C000'

def fx_map(kind):
    words=[]
    for y in range(32):
        for x in range(64):
            dx,dy=(x-19.5)/1.05,(y-13.5)/1.05
            radius=math.hypot(dx,dy)
            theta=math.atan2(dy,dx)
            if kind=='vortex':
                angle=int((theta/math.tau+0.5)*16)&15
                phase=int(radius*2.8-theta*3.2)&15
                bank=(int(radius//5)+int((theta+math.pi)*2))&3
            else:
                displacement=math.sin(x/6.0+y/4.0)
                angle=(int(4+3.4*math.sin((x+y)*0.18))+int(y/6))&15
                phase=int(x*0.58+y*2.3+displacement*4)&15
                bank=(y//7+int(x//13))&3
            index=FX_BASE+angle*16+phase
            words.append((bank<<13)|index)
    assert len(words)==2048
    return words

VORTEX_MAP=fx_map('vortex')
AURORA_MAP=fx_map('aurora')

def fx_palette(kind, frame):
    entries=[]
    for bank in range(4):
        entries.append(0)
        for shade in range(1,16):
            rad=frame*math.tau/PHASES
            if kind=='vortex':
                hue=(bank/4 + (shade/15)*0.18 +0.10*math.sin(rad))%1
                sat=0.84
                value=(0.20+0.78*shade/15)*(0.93+0.07*math.sin(shade*0.56+rad))
            else:
                hue=(0.52+bank*0.10 + (shade/15)*0.08 +0.06*math.sin(rad))%1
                sat=0.69
                value=(0.18+0.78*shade/15)*(0.94+0.06*math.sin(shade*.7-rad))
            entries.append(genesis_colour(*colorsys.hsv_to_rgb(hue,sat,min(1.0,max(0.0,value)))))
    assert len(entries)==64 and all(0 <= c <= 0xEEE and c&0x111==0 for c in entries)
    return b''.join(struct.pack('>H',x) for x in entries)

def fx_scroll(kind,frame):
    values=[]
    for row in range(30):
        rad=frame*math.tau/PHASES
        if kind=='vortex':
            scroll=round(15*math.sin(row*.34+rad)+7*math.sin(row*.87-rad*2.0))
        else:
            scroll=round(10*math.sin(row*.19-rad)+11*math.sin(row*.49+rad*1.0))
        values.append(scroll&0x3FF) # Signed scroll (10-bit effective VDP offset)
    return b''.join(struct.pack('>H',x) for x in values)

FX_PALETTES={name:b''.join(fx_palette(name,frame) for frame in range(PHASES)) for name in ('vortex','aurora')}
FX_SCROLLS={name:b''.join(fx_scroll(name,frame) for frame in range(PHASES)) for name in ('vortex','aurora')}
assert all(len(x)==PHASES*128 for x in FX_PALETTES.values())
assert all(len(x)==PHASES*60 for x in FX_SCROLLS.values())

# Exact 64-column plane layout. Index 892 is reserved as a completely transparent tile.
blank_id=pattern_count
assert len(PATTERNS)+64+len(FX_PATTERNS) < 0xC000

def full_map(viewport):
    rows=[]
    for y in range(32):
        for x in range(64):
            if x < 40 and y < 28:rows.append(viewport[y*40+x])
            else:rows.append(blank_id)
    return b''.join(struct.pack('>H',v) for v in rows)

title_cells=[int.from_bytes(TILEMAP[i:i+2],'big') for i in range(0,len(TILEMAP),2)]
# Reusing the original title patterns makes VRAM bending conspicuous.
# Alternate scenes are intentionally original tile-index compositions, not static copies.
tile_cells=[];colour_cells=[];sprite_cells=[];audio_cells=[]
for y in range(28):
    for x in range(40):
        shape=((x//2+y//2)*17+(x^y)*5)%pattern_count
        tile_cells.append(((x//10)%4<<13)|shape)
        colour_cells.append(((x//5+y//5)%4<<13)|((x*7+y*23)%pattern_count))
        sprite_cells.append((((x+y)//12)%4<<13)|((x*3+y*11)%pattern_count))
        audio_cells.append((((x+y)//9)%4<<13)|((x*13+y*3)%pattern_count))

asm=A68()
# Mega Drive vectors: stack and reset PC, all unused exception vectors stop safely.
for i in range(64):asm.data[i*4:i*4+4]=struct.pack('>I',0x200)
asm.data[0:4]=struct.pack('>I',0x00FFFF00)
asm.data[4:8]=struct.pack('>I',0x00000200)

# Helper instructions: e.g. MOVE.W #$2700,SR and MOVE.W #$xxxx,(A0).
asm.label('start');asm.w(0x46FC);asm.w(0x2700) # interrupts masked, polling-only implementation
asm.movea(0,0xC00004) # VDP control/status
asm.movea(1,0xC00000) # VDP data
asm.movea(3,0xA10003) # pad 1 data
asm.movea(4,0xA10009) # pad 1 direction
asm.movea(5,0xC00011) # PSG write
asm.moveb_imm_ai(4,0x40);asm.moveb_imm_ai(3,0x40)
asm.movea(2,0xA10001)
asm.moveb_ai_d(2,0);asm.andib(0,0x0F)
asm.beq('tmss_done')
asm.movea(2,0xA14000)
asm.movel_imm_ai(2,0x53454741)
asm.label('tmss_done')
asm.bsr('setup_vdp')
asm.bsr('load_pattern')
asm.bsr('load_palettes')
asm.bsr('clear_plane_b')
asm.bsr('clear_sprites')
asm.bsr('clear_hscroll')
asm.label('whole_demo')
for n,duration,mode in [('title',10,0),('vortex',12,5),('aurora',12,6),('sprites',8,2),('colour',8,3),('audio',8,4)]:
    asm.bsr('load_'+n)
    if n=='audio':asm.bsr('sound_on')
    # Detect PAL from version register bit 6: 0 => NTSC; 1 => PAL.
    asm.movea(2,0xA10001)
    asm.moveb_ai_d(2,0)
    asm.andib(0,0x40)
    asm.bne('pal_'+n)
    asm.movew_imm_d(6,round(duration*59.92)-1)
    asm.bra('start_'+n)
    asm.label('pal_'+n)
    asm.movew_imm_d(6,duration*50-2 if n=='title' else duration*50-1)
    asm.label('start_'+n)
    if n in ('vortex','aurora'):
        asm.movea_ref(2,'scroll_'+n)
        asm.movea_ref(6,'palframes_'+n)
        asm.movew_imm_d(4,PHASES-1)
    asm.moveq(5,0)
    asm.label('tick_'+n)
    asm.bsr('wait_vblank')
    if mode==0:
        # Low-cost metallic-cyan logo shimmer: swap just one legal CRAM entry.
        asm.movel_imm_ai(0,0xC0340000) # CRAM palette 1, entry 10
        asm.movew_d_d(5,2)
        asm.andiw(2,0x0010)
        asm.beq('title_bright')
        asm.movew_imm_ai(1,0x02CE)
        asm.bra('title_shimmer_done')
        asm.label('title_bright')
        asm.movew_imm_ai(1,0x04EE)
        asm.label('title_shimmer_done')
    elif mode in (5,6):
        # 30 cell-scroll registers. Horizontal scroll mode=per 8-pixel strip.
        # Register 15 autoincrement 32 writes A at F800+row*32, B remains 0.
        # This is <300 bytes of CRAM/VRAM writes per VBlank, not 896-byte
        # per-line table upload and not an impossible pixel-scaling effect.
        asm.movew_imm_ai(0,0x8F20)
        asm.movel_imm_ai(0,0x78000003) # VRAM write $F800
        asm.movew_imm_d(0,29)
        asm.bsr('copy_words')
        asm.movew_imm_ai(0,0x8F02)
        # Cycle all 4 legal 16-colour CRAM palette banks coherently.
        asm.movel_imm_ai(0,0xC0000000)
        asm.movew_imm_d(0,63)
        asm.bsr('copy_words_a6')
        # One-screen vertical scroll complements the tile-row horizontal waves.
        asm.movel_imm_ai(0,0x40000010)
        asm.movew_d_ai(5,1)
        asm.dbra(4,'phase_ok_'+n)
        asm.movea_ref(2,'scroll_'+n)
        asm.movea_ref(6,'palframes_'+n)
        asm.movew_imm_d(4,PHASES-1)
        asm.label('phase_ok_'+n)
    elif mode==2:
        # SAT sprite 0 bounces horizontally. Y=160 +128, size=8x8, tile 893.
        asm.movel_imm_ai(0,0x74000003) # VRAM write $F400
        asm.movew_imm_ai(1,288)
        asm.movew_imm_ai(1,0) # 1x1 sprite, end of link chain
        asm.movew_imm_ai(1,(3<<13)|(blank_id+1))
        asm.movew_d_d(5,2)
        asm.andiw(2,0x00FF)
        asm.addiw(2,128)
        asm.movew_d_ai(2,1) # X includes 128-pixel hardware bias
    elif mode==3:
        # CRAM entry index 1: cycling low red bits through legal CRAM values.
        asm.movel_imm_ai(0,0xC0020000)
        asm.movew_d_d(5,2)
        asm.andiw(2,0x000E)
        asm.movew_d_ai(2,1)
    elif mode==4:
        # Alter one PSG tone as the display animates; a browser gesture still governs sound.
        asm.moveb_imm_ai(5,0x80) # PSG ch0 tone latch, low nibble 0
        asm.movew_d_d(5,2)
        asm.andib(2,0x3F)
        asm.moveb_d_ai(2,5)
    asm.addq(5,1)
    asm.bsr('poll_start')
    asm.beq('end_'+n)
    asm.dbra(6,'tick_'+n)
    asm.label('end_'+n)
    if n=='audio':asm.bsr('sound_off')
    if n=='sprites':asm.bsr('clear_sprites')
# Return to title when the cycle ends.
asm.bra('whole_demo')

asm.label('wait_vblank')
asm.label('wait_leave')
asm.movew_ai_d(0,1);asm.andiw(1,8);asm.bne('wait_leave')
asm.label('wait_enter')
asm.movew_ai_d(0,1);asm.andiw(1,8);asm.beq('wait_enter')
asm.rts()

asm.label('poll_start')
asm.moveb_imm_ai(3,0) # TH low exposes active-low START at bit 5
asm.moveb_ai_d(3,2);asm.andib(2,0x20)
asm.moveb_imm_ai(3,0x40) # restore TH high
asm.tstb(2)
asm.rts()

asm.label('setup_vdp')
for reg,val in [(0,0x04),(1,0x04),(2,0x30),(3,0x3C),(4,0x07),(5,0x7A),
                (6,0),(7,0),(10,0),(11,0),(12,0x81),(13,0x3E),(15,2),(16,1),
                (17,0),(18,0)]:
    asm.movew_imm_ai(0,0x8000|(reg<<8)|val)
asm.rts()

asm.label('enable_display');asm.movew_imm_ai(0,0x8144);asm.rts()
asm.label('disable_display');asm.movew_imm_ai(0,0x8104);asm.rts()
asm.label('load_pattern')
asm.movel_imm_ai(0,0x40000000)
asm.movea_ref(2,'patterns')
asm.movew_imm_d(0,(len(PATTERNS)+64)//2-1)
asm.bsr('copy_words');asm.rts()
asm.label('load_palettes')
asm.movel_imm_ai(0,0xC0000000)
asm.movea_ref(2,'cram')
asm.movew_imm_d(0,63);asm.bsr('copy_words');asm.rts()
asm.label('clear_plane_b')
asm.movel_imm_ai(0,0x60000003) # VRAM $E000 write
asm.movew_imm_d(0,2047)
asm.label('clear_b_loop');asm.movew_imm_ai(1,blank_id);asm.dbra(0,'clear_b_loop');asm.rts()
asm.label('clear_hscroll')
asm.movew_imm_ai(0,0x8F02)
asm.movel_imm_ai(0,0x78000003)  # $F800
asm.movew_imm_d(0,511)
asm.label('clear_hscroll_loop');asm.movew_imm_ai(1,0);asm.dbra(0,'clear_hscroll_loop');asm.rts()
asm.label('clear_sprites')
asm.movel_imm_ai(0,0x74000003) # VRAM $F400
asm.movew_imm_d(0,319)
asm.label('clear_sprites_loop');asm.movew_imm_ai(1,0);asm.dbra(0,'clear_sprites_loop');asm.rts()

for name in ('title','vortex','aurora','sprites','colour','audio'):
    asm.label('load_'+name)
    asm.bsr('disable_display')
    asm.movel_imm_ai(0,0x40000003) # VRAM $C000
    asm.movea_ref(2,'map_'+name)
    asm.movew_imm_d(0,2047);asm.bsr('copy_words')
    # Use full-width scroll for non-FX scenes; 1-cell horizontal bands in FX scenes.
    asm.movew_imm_ai(0,0x8B02 if name in ('vortex','aurora') else 0x8B00)
    if name not in ('vortex','aurora'):
        asm.bsr('load_palettes')
        asm.movel_imm_ai(0,0x78000003)
        asm.movew_imm_ai(1,0)
        asm.movew_imm_ai(1,0)
    asm.movel_imm_ai(0,0x40000010);asm.movew_imm_ai(1,0)
    asm.bsr('enable_display');asm.rts()

asm.label('copy_words')
asm.label('copy_loop')
asm.movew_a_post_ai(2,1)
asm.dbra(0,'copy_loop');asm.rts()

asm.label('copy_words_a6')
asm.label('copy_a6_loop')
asm.movew_a_post_ai(6,1)
asm.dbra(0,'copy_a6_loop');asm.rts()

asm.label('sound_on')
# Original PSG tone, volume low. FM is intentionally not claimed in this first version.
asm.moveb_imm_ai(5,0x8A);asm.moveb_imm_ai(5,0x14)
asm.moveb_imm_ai(5,0x94);asm.rts()
asm.label('sound_off');asm.moveb_imm_ai(5,0x9F);asm.rts()

asm.append('patterns',PATTERNS+b'\0'*32+b'\x00\x0F'*16+FX_PATTERNS) # 893 is an original single-8x8 sprite motif
asm.append('cram',CRAM)
for name,cell in [('title',title_cells),('vortex',VORTEX_MAP),('aurora',AURORA_MAP),('sprites',sprite_cells),('colour',colour_cells),('audio',audio_cells)]:
    asm.append('map_'+name, b''.join(struct.pack('>H',v) for v in cell)
               if name in ('vortex','aurora') else full_map(cell))
for name in ('vortex','aurora'):
    asm.append('scroll_'+name,FX_SCROLLS[name])
    asm.append('palframes_'+name,FX_PALETTES[name])

rom=asm.final()
# Header is installed only after byte offsets/branches are fixed.
def put(start,stop,text):
    b=text.encode('ascii');assert len(b)<=stop-start
    rom[start:stop]=b.ljust(stop-start,b' ')
put(0x100,0x110,'SEGA MEGA DRIVE')
put(0x110,0x120,'(C) MCRETRO 2026')
put(0x120,0x150,'VRAMPAGE MD FX LAB V0.2')
put(0x150,0x180,'VRAMPAGE MD FX LAB V0.2')
put(0x180,0x18E,'GM 00000000-00')
put(0x190,0x1A0,'J               ')
rom[0x1A0:0x1A8]=struct.pack('>II',0,len(rom)-1)
rom[0x1A8:0x1B0]=struct.pack('>II',0xFF0000,0xFFFFFF)
put(0x1F0,0x200,'JUE')
if len(rom)%2:rom+=b'\x00'
rom[0x1A4:0x1A8]=struct.pack('>I',len(rom)-1)
checksum=sum(struct.unpack_from('>H',rom,i)[0] for i in range(0x200,len(rom),2))&0xFFFF
rom[0x18E:0x190]=struct.pack('>H',checksum)
(OUT/'VRAMpage-MD-FX-Lab-v0.2.bin').write_bytes(rom)
report={
 'romSize':len(rom),'checksum':f'{checksum:04X}',
 'sha256':hashlib.sha256(rom).hexdigest(), 'baseKitSHA256':APPROVED_KIT_SHA256,
 'patternTiles':FX_BASE+FX_TILE_COUNT,'patternBytes':(FX_BASE+FX_TILE_COUNT)*32,
 'planeA':0xC000,'planeB':0xE000,'spriteTable':0xF400,'hscrollTable':0xF800,
 'phases':PHASES,'hscrollEntriesPerFrame':30,'hscrollAutoincrement':32,
 'paletteWordsPerFrame':64,'tileMaps':['title','vortex','aurora','sprites','colour','audio'],
 'titleSecondsNTSC':round(10*59.92),'titleSecondsPAL':500,
 'loopScenes':['title','vortex','aurora','sprites','colour','audio'],
 'assetSHA256':{'title_patterns.bin':hashlib.sha256(PATTERNS).hexdigest(),
                'title_tilemap_viewport.bin':hashlib.sha256(TILEMAP).hexdigest(),
                'title_cram.bin':hashlib.sha256(CRAM).hexdigest()},
 'labelOffsets':{n:hex(addr) for n,addr in asm.labels.items() if n in
                 ['start','whole_demo','patterns','cram','map_title','scroll_vortex','scroll_aurora']},
 'restrictions':['Rom build and source-based previews are not proof of emulator boot',
                 'Intended hardware scrolling and CRAM writes require Genesis Plus GX validation',
                 'No public release or browser auto-load substitution',
                 'FM and Z80 not included in this prototype']}
(OUT/'rom_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['romSize','checksum','sha256','patternTiles','loopScenes']},indent=2))
