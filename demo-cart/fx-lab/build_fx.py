#!/usr/bin/env python3
"""Experimental original Mega Drive FX expansion using a deliberately small 68000 encoder.

No proprietary ROM, external assembler or network dependency. Reviewed asset input
is mandatory; run only with matching approved asset files.
"""
from __future__ import annotations
from pathlib import Path
import json, hashlib, struct, zipfile, math, colorsys, ast

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
    TITLE_FONT_SOURCE = archive.read('demo-cart/polish_title.py').decode('utf-8')
assert len(PATTERNS) % 32 == 0 and len(TILEMAP) == 40*28*2 and len(CRAM) == 128
# Extract only font literals from the reviewed source without executing that script.
def decode_font_literal(node):
    if isinstance(node,ast.Constant) and isinstance(node.value,(str,int)):
        return node.value
    if isinstance(node,ast.List):
        return [decode_font_literal(item) for item in node.elts]
    if isinstance(node,ast.Dict):
        return {decode_font_literal(key):decode_font_literal(value)
                for key,value in zip(node.keys,node.values)}
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult):
        left=decode_font_literal(node.left);right=decode_font_literal(node.right)
        if isinstance(left,list) and isinstance(right,int) and 0<=right<=8:
            return left*right
    raise ValueError('Unsupported glyph literal in the pinned source kit')
font_ast=ast.parse(TITLE_FONT_SOURCE)
FONT=next(decode_font_literal(stmt.value) for stmt in font_ast.body if isinstance(stmt,ast.Assign) and
          any(isinstance(t,ast.Name) and t.id=='FONT' for t in stmt.targets))
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
    def bpl(self,label):self.branch(0x6A00,label)
    def bne(self,label):self.branch(0x6600,label)
    def tstb(self,reg):self.w(0x4A00+reg)
    def tstw(self,reg):self.w(0x4A40+reg)
    def cmpiw(self,reg,imm):self.w(0x0C40+reg);self.w(imm)
    def eorib(self,reg,imm):self.w(0x0A00+reg);self.w(imm)
    def lslw(self,reg,count):self.w(0xE148+(count<<9)+reg)
    def orb(self,src,dst):self.w(0x8000+(dst<<9)+src)
    def eorb(self,src,dst):self.w(0xB100+(src<<9)+dst)
    def andb(self,src,dst):self.w(0xC000+(dst<<9)+src)
    def addw(self,src,dst):self.w(0xD040+(dst<<9)+src)
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

# Controller selector: redraw ONLY the left-side text panel and lower instruction
# strip at native tile resolution. Portrait/logo source tiles remain untouched.
# Uses the approved title's existing bank 1: black (0), white (4), electric blue (8).
PANEL_X0,PANEL_X1=16,144
PANEL_Y0,PANEL_Y1=64,168
CHOICES=('CHROMATIC VORTEX','NEON AURORA','SPRITE STORM','CHROMA REACTOR','PSG SOUND')
LABEL_YS=(69,81,93,105,117)
BASE_TITLE_CELLS=[int.from_bytes(TILEMAP[i:i+2],'big') for i in range(0,len(TILEMAP),2)]
selector_pixels={}
def label_pixels(text,x,y,colour=4):
    for ch in text:
        for dy,row in enumerate(FONT[ch]):
            for dx,bit in enumerate(row):
                if bit=='1':selector_pixels[(x+dx,y+dy)]=colour
        x+=6

for i,(name,y) in enumerate(zip(CHOICES,LABEL_YS),1):
    text=f'{i:02d} {name}'
    assert 20+6*len(text)<=PANEL_X1
    label_pixels(text,20,y)
label_pixels('ARROWS: SELECT',20,139,8)
label_pixels('A/B/C/START: RUN',20,152,4)
label_pixels('IDLE: AUTO LOOP',100,196,4)
label_pixels('START: RETURN',100,205,4)

# Each UI tile is newly generated only inside approved text regions. The untouched
# viewport elsewhere retains its original pattern IDs, palette bank and flips.
UI_BLOCKS=((PANEL_X0,PANEL_Y0,PANEL_X1,PANEL_Y1),(88,192,256,216))
extra_patterns=[];new_tile_ids={}
def get_ui_tile(tx,ty):
    pixels=[]
    for py in range(8):
        for px in range(8):
            pixels.append(selector_pixels.get((tx*8+px,ty*8+py),0))
    pat=bytes(((pixels[i]<<4)|pixels[i+1]) for i in range(0,64,2))
    if pat not in new_tile_ids:
        new_tile_ids[pat]=FX_BASE+FX_TILE_COUNT+len(extra_patterns)
        extra_patterns.append(pat)
    return (1<<13)|new_tile_ids[pat]

title_cells=BASE_TITLE_CELLS[:]
for ty in range(28):
    for tx in range(40):
        if any(x0<=tx*8<x1 and y0<=ty*8<y1 for x0,y0,x1,y1 in UI_BLOCKS):
            title_cells[ty*40+tx]=get_ui_tile(tx,ty)
# One 8x8 right-pointing cursor sprite, with cyan fill, drawn over the left margin.
arrow_rows=('10000000','11000000','11100000','11110000',
            '11100000','11000000','10000000','00000000')
# Explicit nibble encoding from boolean pixels, rather than binary bit-pairs.
arrow=bytes((8 if row[x]=='1' else 0)<<4 | (8 if row[x+1]=='1' else 0)
            for row in arrow_rows for x in range(0,8,2))
ARROW_ID=FX_BASE+FX_TILE_COUNT+len(extra_patterns)
extra_patterns.append(arrow)
UI_PATTERNS=b''.join(extra_patterns)
assert (ARROW_ID+1)*32 < 0xC000,'UI graphic patterns overlap Plane A'
assert all(title_cells[i]==BASE_TITLE_CELLS[i] for i in range(40*28)
           if not any(x0<=(i%40)*8<x1 and y0<=(i//40)*8<y1 for x0,y0,x1,y1 in UI_BLOCKS))


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

# v0.3.2 original demoscene effects. These are 68000-owned VDP sprites and
# complete CRAM cycles, not simulated browser overlays or staged corruption.
SPRITE_COUNT=20
SPRITE_VARIANTS=4
SPRITE_PHASES=96
SPRITE_TILE_COUNT=SPRITE_VARIANTS*4 # 16x16 hardware sprites require four tiles each

def make_sprite_patterns():
    result=bytearray()
    # Mega Drive sprite tile order is column-major (top then bottom).
    for kind in range(SPRITE_VARIANTS):
        canvas=[]
        for y in range(16):
            row=[]
            for x in range(16):
                dx=x-7.5;dy=y-7.5;dist=math.hypot(dx,dy)
                if kind==0: # glass jewel
                    v=0 if dist>7.3 else (15 if dist<2.8 else 10 if dist<5.4 else 5)
                    if dx<-2 and dy<-2 and dist<6:v=15
                elif kind==1: # piercing four-point star
                    tip=max(abs(dx),abs(dy)); width=min(abs(dx),abs(dy))
                    v=0 if not (tip<7.4 and width<max(0.6,3.5-tip*0.44)) else (15 if tip<2.5 else 11 if tip<5 else 6)
                elif kind==2: # pulsing torus
                    v=0 if dist>7.2 or dist<2.8 else (15 if 4.5<=dist<=5.7 else 8)
                else: # faceted diamond
                    k=abs(dx)+abs(dy)
                    v=0 if k>10.4 else (15 if k<3 else 11 if k<6.6 else 5)
                row.append(v)
            canvas.append(row)
        for tx in (0,8):
            for ty in (0,8):
                for y in range(ty,ty+8):
                    for x in range(tx,tx+8,2):
                        result.append((canvas[y][x]<<4)|canvas[y][x+1])
    assert len(result)==SPRITE_TILE_COUNT*32
    return bytes(result)

def sprite_palette(frame):
    entries=[]
    phase=frame*math.tau/SPRITE_PHASES
    for bank in range(4):
        entries.append(0)
        for shade in range(1,16):
            if bank < 2: # lower-energy blue-violet backdrop, no sudden flashes
                hue=(0.56+0.10*bank+0.02*math.sin(phase))%1
                val=(0.06+0.43*shade/15)
                sat=0.68
            else: # warm and cyan foreground jewels in independent banks
                hue=(0.08 if bank==2 else 0.50)+0.04*math.sin(phase+(bank-2)*2)
                val=min(1,0.12+0.86*shade/15)*(0.93+0.07*math.cos(phase))
                sat=0.84
            entries.append(genesis_colour(*colorsys.hsv_to_rgb(hue,sat,val)))
    return struct.pack('>64H',*entries)

def colour_palette(frame):
    phase=frame*math.tau/PHASES
    entries=[]
    for bank in range(4):
        entries.append(0)
        for shade in range(1,16):
            hue=(bank*0.25+shade*0.026+frame/PHASES)%1
            hue=(hue+0.025*math.sin(phase+bank))%1
            sat=0.84
            val=min(1,0.22+0.76*shade/15)
            entries.append(genesis_colour(*colorsys.hsv_to_rgb(hue,sat,val)))
    return struct.pack('>64H',*entries)

def colour_scroll(frame):
    angle=frame*math.tau/PHASES
    words=[]
    for row in range(30):
        offset=round(18*math.sin(row*0.35+angle)+9*math.sin(row*0.74-angle*2))
        words.append(offset & 0x3FF)
    return struct.pack('>30H',*words)

SPRITE_PATTERNS=make_sprite_patterns()
SPRITE_PALETTES=b''.join(sprite_palette(frame) for frame in range(SPRITE_PHASES))
COLOUR_PALETTES=b''.join(colour_palette(frame) for frame in range(PHASES))
COLOUR_SCROLLS=b''.join(colour_scroll(frame) for frame in range(PHASES))

# Exact 64-column plane layout. Index 892 is reserved as a completely transparent tile.
blank_id=pattern_count
assert len(PATTERNS)+64+len(FX_PATTERNS) < 0xC000

def full_map(viewport, fill_edges=False):
    rows=[]
    for y in range(32):
        for x in range(64):
            if y < 28 and (x < 40 or fill_edges):rows.append(viewport[y*40+(x%40)])
            else:rows.append(blank_id)
    return b''.join(struct.pack('>H',v) for v in rows)

# Do not scatter title/portrait glyphs through the effects! Scene maps only
# reference ORIGINAL procedural FX tiles; no approved portrait/logo tiles are used.
# These maps are independent of any circuit bending, which remains user-controlled.
tile_cells=[];colour_cells=[];sprite_cells=[];audio_cells=[]
for y in range(28):
    for x in range(40):
        # Alternating interlocking ribbons with warm/cool regions.
        a=((x//4)+2*(y//4)) & 15
        phase=(3*x+2*y+(x//3)) & 15
        tile_cells.append((((x//10)+(y//7))%4<<13)|(FX_BASE+a*16+phase))
        # Large, legible colour regions reveal deliberate palette mutations.
        colour_cells.append(((((x//8)+(y//5))%4)<<13)|(FX_BASE+((x+y)//5%16)*16+((x//2+y//2)&15)))
        # Calm stage backdrop, with a moving 1x1 hardware sprite on top.
        sprite_cells.append(((((y//8)+(x//12))%4)<<13)|(FX_BASE+((y//3)&15)*16+((x//4)&15)))
        # A muted oscilloscope-style diagonal backdrop for the PSG stage.
        audio_cells.append(((((x//12)+(y//8))%4)<<13)|(FX_BASE+((x+2*y)//5%16)*16+((x+y*3)&15)))

# The ROM must actually upload every tile referenced by the maps AND cursor.
# The previous version included those pixels in its ROM but uploaded only the
# old title patterns, leaving all selector and FX tile IDs uninitialised in VRAM.
SPRITE_TILE_BASE=ARROW_ID+1
ALL_PATTERNS=PATTERNS+b'\0'*32+b'\x00\x0F'*16+FX_PATTERNS+UI_PATTERNS+SPRITE_PATTERNS
assert len(ALL_PATTERNS)==(SPRITE_TILE_BASE+SPRITE_TILE_COUNT)*32
assert SPRITE_TILE_BASE+SPRITE_TILE_COUNT < 2048

def sprite_sat(frame):
    records=[]
    theta=frame*math.tau/SPRITE_PHASES
    for i in range(SPRITE_COUNT):
        # Two counter-rotating rings with a gentle 2:3 phase relationship.
        ring=i//10;slot=i%10
        t=theta*(1 if ring==0 else -1.5)+slot*math.tau/10+ring*0.24
        rx=78 if ring==0 else 133
        ry=50 if ring==0 else 82
        px=round(152+rx*math.cos(t))
        py=round(106+ry*math.sin(t)+7*math.sin(theta*2+slot*0.8))
        assert 0<=px<=304 and 0<=py<=208
        # Size 2x2 in bits 8-11 and explicit linked SAT chain.
        size_link=0x0500 | (i+1 if i<SPRITE_COUNT-1 else 0)
        attr=0x8000|((2+i%2)<<13)|(SPRITE_TILE_BASE+(i%SPRITE_VARIANTS)*4)
        records.extend((128+py,size_link,attr,128+px))
    assert len(records)==SPRITE_COUNT*4
    return struct.pack('>'+str(len(records))+'H',*records)

SPRITE_SAT_FRAMES=b''.join(sprite_sat(frame) for frame in range(SPRITE_PHASES))
assert len(SPRITE_SAT_FRAMES)==SPRITE_PHASES*SPRITE_COUNT*8
assert len(ALL_PATTERNS)<0xC000, 'Tile upload must not overlap Plane A'
assert all((word&0x7FF)>=FX_BASE for scene in (tile_cells,colour_cells,sprite_cells,audio_cells) for word in scene)

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
# D7: menu selection 0..4. D3: previous 8-bit button state, for edge detection.
# Button bits: UP=1 DOWN=2 LEFT=4 RIGHT=8 B=16 C=32 A=64 START=128.
asm.moveq(7,0);asm.moveq(3,0)
asm.label('whole_demo')
asm.bsr('load_title')
asm.bsr('draw_cursor')
asm.bsr('reset_idle')
asm.moveq(5,0)
asm.label('menu_tick')
asm.bsr('wait_vblank')
# Metallic chrome shimmer within the original logo's palette bank.
asm.movel_imm_ai(0,0xC0340000)
asm.movew_d_d(5,2);asm.andiw(2,0x0010)
asm.beq('menu_bright')
asm.movew_imm_ai(1,0x02CE)
asm.bra('menu_shimmer_done')
asm.label('menu_bright');asm.movew_imm_ai(1,0x04EE)
asm.label('menu_shimmer_done')
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.movew_d_d(2,1);asm.andiw(1,0x00F0)
asm.bne('manual_launch')
asm.movew_d_d(2,1);asm.andiw(1,0x0005)
asm.bne('select_previous')
asm.movew_d_d(2,1);asm.andiw(1,0x000A)
asm.bne('select_next')
asm.dbra(6,'menu_tick')
asm.label('auto_cycle')
for n in ('vortex','aurora','sprites','colour','audio'):
    asm.bsr('run_'+n)
asm.bra('whole_demo')
asm.label('select_previous')
asm.subq(7)
asm.tstw(7);asm.bpl('nav_updated')
asm.moveq(7,4);asm.bra('nav_updated')
asm.label('select_next')
asm.addq(7);asm.cmpiw(7,5);asm.bne('nav_updated')
asm.moveq(7,0)
asm.label('nav_updated')
asm.bsr('draw_cursor')
asm.bsr('reset_idle')
asm.bra('menu_tick')
asm.label('manual_launch')
for i,name in enumerate(('vortex','aurora','sprites','colour')):
    asm.cmpiw(7,i);asm.beq('manual_'+name)
asm.bsr('run_audio');asm.bra('whole_demo')
for n in ('vortex','aurora','sprites','colour'):
    asm.label('manual_'+n)
    asm.bsr('run_'+n)
    asm.bra('whole_demo')

asm.label('reset_idle')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('reset_pal')
asm.movew_imm_d(6,598);asm.rts()
asm.label('reset_pal');asm.movew_imm_d(6,498);asm.rts()

asm.label('draw_cursor')
# Y = 128 + 69 + selected * 12; X = 128 + 11. Uses the real SAT.
asm.movew_d_d(7,2)
asm.addw(7,2);asm.addw(7,2) # D2 = 3 * selected
asm.addw(2,2);asm.addw(2,2) # D2 = 12 * selected
asm.addiw(2,197)
asm.movel_imm_ai(0,0x74000003) # SAT $F400
asm.movew_d_ai(2,1) # Y
asm.movew_imm_ai(1,0) # 1x1 sprite, last link
asm.movew_imm_ai(1,(1<<13)|ARROW_ID)
asm.movew_imm_ai(1,139) # X = 128 + 11
asm.rts()

# Full native Mega Drive three-button protocol. Poll high TH for U/D/L/R/B/C,
# low TH for A/START; compare to previous state so holding cannot repeat a menu
# action every frame. The emulator's existing keyboard/gamepad mapping is used.
asm.label('poll_buttons')
asm.moveb_imm_ai(3,0x40)
asm.moveb_ai_d(3,2);asm.eorib(2,0x3F);asm.andib(2,0x3F)
asm.moveb_imm_ai(3,0)
asm.moveb_ai_d(3,1);asm.eorib(1,0x30);asm.andib(1,0x30)
asm.lslw(1,2);asm.orb(1,2)
asm.moveb_imm_ai(3,0x40)
asm.movew_d_d(2,1) # current state
asm.eorb(3,2);asm.andb(1,2) # rising edges only
asm.movew_d_d(1,3)
asm.rts()

asm.label('run_vortex')
asm.bsr('load_vortex')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('pal_vortex')
asm.movew_imm_d(6,718)
asm.bra('start_vortex')
asm.label('pal_vortex')
asm.movew_imm_d(6,599)
asm.label('start_vortex')
asm.movea_ref(2,'scroll_vortex')
asm.movea_ref(6,'palframes_vortex')
asm.movew_imm_d(4,PHASES-1)
asm.moveq(5,0)
asm.label('tick_vortex')
asm.bsr('wait_vblank')
asm.movew_imm_ai(0,0x8F20)
asm.movel_imm_ai(0,0x78000003)
asm.movew_imm_d(0,29)
asm.bsr('copy_words')
asm.movew_imm_ai(0,0x8F02)
asm.movel_imm_ai(0,0xC0000000)
asm.movew_imm_d(0,63)
asm.bsr('copy_words_a6')
asm.movel_imm_ai(0,0x40000010)
asm.movew_d_ai(5,1)
asm.dbra(4,'phase_ok_vortex')
asm.movea_ref(2,'scroll_vortex')
asm.movea_ref(6,'palframes_vortex')
asm.movew_imm_d(4,PHASES-1)
asm.label('phase_ok_vortex')
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.andiw(2,0x0080)
asm.bne('scene_end_vortex')
asm.dbra(6,'tick_vortex')
asm.label('scene_end_vortex')
asm.rts()

asm.label('run_aurora')
asm.bsr('load_aurora')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('pal_aurora')
asm.movew_imm_d(6,718)
asm.bra('start_aurora')
asm.label('pal_aurora')
asm.movew_imm_d(6,599)
asm.label('start_aurora')
asm.movea_ref(2,'scroll_aurora')
asm.movea_ref(6,'palframes_aurora')
asm.movew_imm_d(4,PHASES-1)
asm.moveq(5,0)
asm.label('tick_aurora')
asm.bsr('wait_vblank')
asm.movew_imm_ai(0,0x8F20)
asm.movel_imm_ai(0,0x78000003)
asm.movew_imm_d(0,29)
asm.bsr('copy_words')
asm.movew_imm_ai(0,0x8F02)
asm.movel_imm_ai(0,0xC0000000)
asm.movew_imm_d(0,63)
asm.bsr('copy_words_a6')
asm.movel_imm_ai(0,0x40000010)
asm.movew_d_ai(5,1)
asm.dbra(4,'phase_ok_aurora')
asm.movea_ref(2,'scroll_aurora')
asm.movea_ref(6,'palframes_aurora')
asm.movew_imm_d(4,PHASES-1)
asm.label('phase_ok_aurora')
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.andiw(2,0x0080)
asm.bne('scene_end_aurora')
asm.dbra(6,'tick_aurora')
asm.label('scene_end_aurora')
asm.rts()

asm.label('run_sprites')
asm.bsr('load_sprites')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('pal_sprites')
asm.movew_imm_d(6,478)
asm.bra('start_sprites')
asm.label('pal_sprites');asm.movew_imm_d(6,399)
asm.label('start_sprites')
asm.movea_ref(2,'satframes_sprites')
asm.movea_ref(6,'palframes_sprites')
asm.movew_imm_d(4,SPRITE_PHASES-1)
asm.moveq(5,0)
asm.label('tick_sprites')
asm.bsr('wait_vblank')
# Twenty 16x16 hardware sprites, with authentic linked SAT entries.
asm.movel_imm_ai(0,0x74000003)
asm.movew_imm_d(0,SPRITE_COUNT*4-1)
asm.bsr('copy_words')
# Cycle all 64 palette entries for the background and two foreground banks.
asm.movel_imm_ai(0,0xC0000000)
asm.movew_imm_d(0,63)
asm.bsr('copy_words_a6')
asm.dbra(4,'sprite_phase_done')
asm.movea_ref(2,'satframes_sprites')
asm.movea_ref(6,'palframes_sprites')
asm.movew_imm_d(4,SPRITE_PHASES-1)
asm.label('sprite_phase_done')
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.andiw(2,0x0080)
asm.bne('scene_end_sprites')
asm.dbra(6,'tick_sprites')
asm.label('scene_end_sprites')
asm.bsr('clear_sprites')
asm.rts()

asm.label('run_colour')
asm.bsr('load_colour')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('pal_colour')
asm.movew_imm_d(6,478)
asm.bra('start_colour')
asm.label('pal_colour');asm.movew_imm_d(6,399)
asm.label('start_colour')
asm.movea_ref(2,'scroll_colour')
asm.movea_ref(6,'palframes_colour')
asm.movew_imm_d(4,PHASES-1)
asm.moveq(5,0)
asm.label('tick_colour')
asm.bsr('wait_vblank')
# Horizontal one-cell scrolling uses HScroll table with 32-byte autoincrement.
asm.movew_imm_ai(0,0x8F20)
asm.movel_imm_ai(0,0x78000003)
asm.movew_imm_d(0,29)
asm.bsr('copy_words')
asm.movew_imm_ai(0,0x8F02)
# Full four-bank CRAM rotation, not the previous single-word flicker.
asm.movel_imm_ai(0,0xC0000000)
asm.movew_imm_d(0,63)
asm.bsr('copy_words_a6')
asm.dbra(4,'colour_phase_done')
asm.movea_ref(2,'scroll_colour')
asm.movea_ref(6,'palframes_colour')
asm.movew_imm_d(4,PHASES-1)
asm.label('colour_phase_done')
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.andiw(2,0x0080)
asm.bne('scene_end_colour')
asm.dbra(6,'tick_colour')
asm.label('scene_end_colour')
asm.rts()

asm.label('run_audio')
asm.bsr('load_audio')
asm.bsr('sound_on')
asm.movea(2,0xA10001);asm.moveb_ai_d(2,0);asm.andib(0,0x40)
asm.bne('pal_audio')
asm.movew_imm_d(6,478)
asm.bra('start_audio')
asm.label('pal_audio')
asm.movew_imm_d(6,399)
asm.label('start_audio')
asm.moveq(5,0)
asm.label('tick_audio')
asm.bsr('wait_vblank')
asm.moveb_imm_ai(5,0x80)
asm.movew_d_d(5,2)
asm.andib(2,0x3F)
asm.moveb_d_ai(2,5)
asm.addq(5,1)
asm.bsr('poll_buttons')
asm.andiw(2,0x0080)
asm.bne('scene_end_audio')
asm.dbra(6,'tick_audio')
asm.label('scene_end_audio')
asm.bsr('sound_off')
asm.rts()

asm.label('wait_vblank')
asm.label('wait_leave')
asm.movew_ai_d(0,1);asm.andiw(1,8);asm.bne('wait_leave')
asm.label('wait_enter')
asm.movew_ai_d(0,1);asm.andiw(1,8);asm.beq('wait_enter')
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
# Copy all contiguous pattern data, including FX and the native menu text.
asm.movew_imm_d(0,len(ALL_PATTERNS)//2-1)
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
    asm.bsr('clear_sprites')
    asm.movel_imm_ai(0,0x40000003) # VRAM $C000
    asm.movea_ref(2,'map_'+name)
    asm.movew_imm_d(0,2047);asm.bsr('copy_words')
    # Use full-width scroll for non-FX scenes; 1-cell horizontal bands in FX scenes.
    asm.movew_imm_ai(0,0x8B02 if name in ('vortex','aurora','colour') else 0x8B00)
    if name not in ('vortex','aurora'):
        if name=='title':
            asm.bsr('load_palettes')  # Preserve approved captain and logo colours.
        else:
            # Procedural scenes need the corresponding procedural palette,
            # not the portrait's original colour banks.
            asm.movel_imm_ai(0,0xC0000000)
            asm.movea_ref(2,'palette_static_colour' if name=='colour' else 'palette_static_sprites' if name=='sprites' else 'palette_static_cool')
            asm.movew_imm_d(0,63)
            asm.bsr('copy_words')
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

asm.append('patterns',ALL_PATTERNS) # Keep approved title tiles; append menu and arrow tiles
asm.append('cram',CRAM)
asm.append('palette_static_colour',COLOUR_PALETTES[:128])
asm.append('palette_static_sprites',SPRITE_PALETTES[:128])
asm.append('palette_static_cool',FX_PALETTES['aurora'][:128])
for name,cell in [('title',title_cells),('vortex',VORTEX_MAP),('aurora',AURORA_MAP),('sprites',sprite_cells),('colour',colour_cells),('audio',audio_cells)]:
    asm.append('map_'+name, b''.join(struct.pack('>H',v) for v in cell)
               if name in ('vortex','aurora') else full_map(cell, fill_edges=name=='colour'))
for name in ('vortex','aurora'):
    asm.append('scroll_'+name,FX_SCROLLS[name])
    asm.append('palframes_'+name,FX_PALETTES[name])
asm.append('satframes_sprites',SPRITE_SAT_FRAMES)
asm.append('palframes_sprites',SPRITE_PALETTES)
asm.append('scroll_colour',COLOUR_SCROLLS)
asm.append('palframes_colour',COLOUR_PALETTES)

rom=asm.final()
# Header is installed only after byte offsets/branches are fixed.
def put(start,stop,text):
    b=text.encode('ascii');assert len(b)<=stop-start
    rom[start:stop]=b.ljust(stop-start,b' ')
put(0x100,0x110,'SEGA MEGA DRIVE')
put(0x110,0x120,'(C) MCRETRO 2026')
put(0x120,0x150,'VRAMPAGE MD FX LAB V0.3.3 DEMOSCENE')
put(0x150,0x180,'VRAMPAGE MD FX LAB V0.3.3 DEMOSCENE')
put(0x180,0x18E,'GM 00000000-00')
put(0x190,0x1A0,'J               ')
rom[0x1A0:0x1A8]=struct.pack('>II',0,len(rom)-1)
rom[0x1A8:0x1B0]=struct.pack('>II',0xFF0000,0xFFFFFF)
put(0x1F0,0x200,'JUE')
if len(rom)%2:rom+=b'\x00'
rom[0x1A4:0x1A8]=struct.pack('>I',len(rom)-1)
checksum=sum(struct.unpack_from('>H',rom,i)[0] for i in range(0x200,len(rom),2))&0xFFFF
rom[0x18E:0x190]=struct.pack('>H',checksum)
(OUT/'VRAMpage-MD-FX-Lab-v0.3.3-Demoscene.bin').write_bytes(rom)
report={
 'romSize':len(rom),'checksum':f'{checksum:04X}',
 'sha256':hashlib.sha256(rom).hexdigest(), 'baseKitSHA256':APPROVED_KIT_SHA256,
 'patternTiles':SPRITE_TILE_BASE+SPRITE_TILE_COUNT,'patternBytes':len(ALL_PATTERNS),
 'spriteCount':SPRITE_COUNT,'spriteTileBase':SPRITE_TILE_BASE,'spritePhases':SPRITE_PHASES,
 'spriteSatBytes':len(SPRITE_SAT_FRAMES),'spritePaletteBytes':len(SPRITE_PALETTES),
 'colourPaletteBytes':len(COLOUR_PALETTES),'colourScrollBytes':len(COLOUR_SCROLLS),
 'planeA':0xC000,'planeB':0xE000,'spriteTable':0xF400,'hscrollTable':0xF800,
 'phases':PHASES,'hscrollEntriesPerFrame':30,'hscrollAutoincrement':32,
 'paletteWordsPerFrame':64,'tileMaps':['title','vortex','aurora','sprites','colour','audio'],
 'titleSecondsNTSC':round(10*59.92),'titleSecondsPAL':500,
 'loopScenes':['title','vortex','aurora','sprites','colour','audio'],
 'menuChoices':list(CHOICES),'input':{'up':'previous','left':'previous','down':'next','right':'next','start':'launch or return','A':'launch','B':'launch','C':'launch'},
 'autoAttractIdleNTSCFrames':600,'autoAttractIdlePALFrames':500,
 'cursorTile':ARROW_ID,'uiPatternTiles':len(extra_patterns),
 'assetSHA256':{'title_patterns.bin':hashlib.sha256(PATTERNS).hexdigest(),
                'title_tilemap_viewport.bin':hashlib.sha256(TILEMAP).hexdigest(),
                'title_cram.bin':hashlib.sha256(CRAM).hexdigest()},
 'labelOffsets':{n:hex(addr) for n,addr in asm.labels.items() if n in
                 ['start','whole_demo','poll_buttons','run_vortex','run_aurora','patterns','cram','map_title','scroll_vortex','scroll_aurora']},
 'restrictions':['Rom build and source-based previews are not proof of emulator boot',
                 'Intended hardware scrolling and CRAM writes require Genesis Plus GX validation',
                 'No public release or browser auto-load substitution',
                 'FM and Z80 not included in this prototype']}
(OUT/'rom_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['romSize','checksum','sha256','patternTiles','loopScenes']},indent=2))
