#!/usr/bin/env python3
"""Optional, software-only static/animated tile preview, NOT an emulator capture.

Requires Pillow. Reads the *same* tilemaps, patterns and CRAM tables packed into
build_fx.py; colour quantisation and layout are deterministic, but emulated
VDP timing and startup are not verified by this script.
"""
from pathlib import Path
import struct
from PIL import Image,ImageDraw,ImageFont
import build_fx as B

OUT=Path(__file__).resolve().parent/'build'
PALETTES={'title':B.CRAM,'sprites':B.SPRITE_PALETTES[:128], 'colour':B.COLOUR_PALETTES[:128], 'audio':B.FX_PALETTES['aurora'][:128]}
PALETTES.update({n:B.FX_PALETTES[n][:128] for n in ('vortex','aurora')})
PATTERNS=B.ALL_PATTERNS
MAPS={'title':B.full_map(B.title_cells),'vortex':struct.pack('>2048H',*B.VORTEX_MAP),'aurora':struct.pack('>2048H',*B.AURORA_MAP),
      'sprites':B.full_map(B.sprite_cells),'colour':B.full_map(B.colour_cells),'audio':B.full_map(B.audio_cells)}

def rgb(c):
    return (((c>>1)&7)*36,((c>>5)&7)*36,((c>>9)&7)*36)

def palette(kind,frame):
    content=(B.CRAM if kind=='title' else B.sprite_palette(frame) if kind=='sprites' else B.colour_palette(frame) if kind=='colour' else B.fx_palette(kind if kind in ('vortex','aurora') else 'aurora',frame))
    return [rgb(struct.unpack_from('>H',content,i)[0]) for i in range(0,128,2)]

def render(kind,frame=0):
    pix=Image.new('RGB',(512,256))
    px=pix.load();data=MAPS[kind];pal=palette(kind,frame)
    for row in range(32):
        for col in range(64):
            word=struct.unpack_from('>H',data,(row*64+col)*2)[0]
            index=word&0x7FF;bank=(word>>13)&3
            assert 0 <= index*32 <= len(PATTERNS)-32
            tile=PATTERNS[index*32:index*32+32]
            for ty in range(8):
                for tx in range(8):
                    byte=tile[ty*4+tx//2]
                    p=(byte>>4) if tx%2==0 else byte&0x0F
                    px[col*8+tx,row*8+ty]=pal[bank*16+p]
    if kind=='title':
        result=pix.crop((0,0,320,224))
        # The ROM itself positions this original sprite through the SAT.
        # The following reproduces only its static default-selected location.
        pat=PATTERNS[B.ARROW_ID*32:(B.ARROW_ID+1)*32]
        colours=palette('title',0)
        for row in range(8):
            for col in range(8):
                byte=pat[row*4+col//2]
                v=byte>>4 if col%2==0 else byte&15
                if v:result.putpixel((11+col,69+row),colours[16+v])
        return result
    scroll=struct.unpack('>30H',B.colour_scroll(frame) if kind=='colour' else B.fx_scroll(kind,frame)) if kind in ('vortex','aurora','colour') else (0,)*30
    out=Image.new('RGB',(320,224))
    outpix=out.load()
    for y in range(224):
        k=scroll[y//8]
        if k>=512:k-=1024
        vy=(y+frame)%256 if kind in ('vortex','aurora') else y
        for x in range(320):
            # Positive VDP scroll shifts fetched source in opposing direction.
            sx=(x-k)%512
            outpix[x,y]=px[sx,vy]
    if kind=='sprites':
        # Render authentic 2x2 SAT pattern ordering and transparent pixel zero.
        sprite_data=B.sprite_sat(frame)
        colours=palette(kind,frame)
        for i in range(B.SPRITE_COUNT):
            sy,size_link,attr,sx=struct.unpack_from('>4H',sprite_data,i*8)
            sy-=128;sx-=128
            assert size_link>>8 == 5
            tile_index=attr&0x7ff;bank=(attr>>13)&3
            for col in range(2):
                for row in range(2):
                    tile=PATTERNS[(tile_index+col*2+row)*32:(tile_index+col*2+row+1)*32]
                    for dy in range(8):
                        for dx in range(8):
                            byte=tile[dy*4+dx//2]
                            val=byte>>4 if dx%2==0 else byte&15
                            x=sx+col*8+dx;y=sy+row*8+dy
                            if val and 0<=x<320 and 0<=y<224:
                                out.putpixel((x,y),colours[bank*16+val])
    return out

def make():
    for name in ('title','vortex','aurora','sprites','colour','audio'):
        im=render(name,0)
        im.save(OUT/f'{name}_320x224.png')
        im.resize((1280,896),Image.Resampling.NEAREST).save(OUT/f'{name}_4x_nearest.png')
    images=[]
    for kind in ('vortex','aurora','sprites','colour'):
        for frame in range(0,B.PHASES,4):
            images.append(render(kind,frame).resize((640,448),Image.Resampling.NEAREST))
    images[0].save(OUT/'FX_Lab_Storyboard_v0.3.2.gif',save_all=True,append_images=images[1:],duration=90,loop=0,optimize=False)
    print('Wrote previews to',OUT)
if __name__=='__main__':make()
