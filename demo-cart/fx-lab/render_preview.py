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
PALETTES={'title':B.CRAM}
PALETTES.update({n:B.FX_PALETTES[n][:128] for n in ('vortex','aurora')})
PATTERNS=B.PATTERNS+b'\0'*32+b'\x00\x0F'*16+B.FX_PATTERNS
MAPS={'title':B.full_map(B.title_cells),'vortex':struct.pack('>2048H',*B.VORTEX_MAP),'aurora':struct.pack('>2048H',*B.AURORA_MAP)}

def rgb(c):
    return (((c>>1)&7)*36,((c>>5)&7)*36,((c>>9)&7)*36)

def palette(kind,frame):
    content=B.CRAM if kind=='title' else B.fx_palette(kind,frame)
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
    if kind=='title':return pix.crop((0,0,320,224))
    scroll=struct.unpack('>30H',B.fx_scroll(kind,frame))
    out=Image.new('RGB',(320,224))
    outpix=out.load()
    for y in range(224):
        k=scroll[y//8]
        if k>=512:k-=1024
        vy=(y+frame)%256
        for x in range(320):
            # Positive VDP scroll shifts fetched source in opposing direction.
            sx=(x-k)%512
            outpix[x,y]=px[sx,vy]
    return out

def make():
    for name in ('title','vortex','aurora'):
        im=render(name,0)
        im.save(OUT/f'{name}_320x224.png')
        im.resize((1280,896),Image.Resampling.NEAREST).save(OUT/f'{name}_4x_nearest.png')
    images=[]
    for kind in ('vortex','aurora'):
        for frame in range(0,B.PHASES,4):
            images.append(render(kind,frame).resize((640,448),Image.Resampling.NEAREST))
    images[0].save(OUT/'FX_Lab_Storyboard.gif',save_all=True,append_images=images[1:],duration=90,loop=0,optimize=False)
    print('Wrote previews to',OUT)
if __name__=='__main__':make()
