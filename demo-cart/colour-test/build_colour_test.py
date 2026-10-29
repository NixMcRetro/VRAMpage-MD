#!/usr/bin/env python3
"""Build the original VRAMpage MD colour-pattern cartridge using Python 3 only.

Original program and graphics created for the VRAMpage MD blog illustration.
No commercial game code, graphics, audio, libraries or ROM data are included.
It configures the VDP, fills original tiles/name data, then increments Work RAM
at $FF1000 forever. It does not read the controller or program FM/PSG sound.
Intended for emulator experiments; this is not a hardware diagnostic suite.
"""
import struct
from pathlib import Path

def diagnostic():
 rom=bytearray(65536)
 for o in range(0,256,4):struct.pack_into('>I',rom,o,0x300)
 struct.pack_into('>II',rom,0,0xffff00,0x400)
 rom[0x100:0x110]=b'SEGA MEGA DRIVE '
 rom[0x120:0x140]=b'VRAMPAGE ORIGINAL COLOUR TEST'.ljust(32, b' ')
 struct.pack_into('>IIII',rom,0x1a0,0,len(rom)-1,0xff0000,0xffffff)
 rom[0x1f0]=ord('U'); words=[]
 def w(a,v):words.extend([0x33fc,v,a>>16,a&0xffff])
 def addr(a,cram=False):
  command=((a&0x3fff)<<16)|(a>>14)| (0xc0000000 if cram else 0x40000000)
  words.extend([0x23fc,command>>16,command&0xffff,0x00c0,0x0004])
 for reg,val in [(0,4),(1,4),(2,0x30),(3,0x3e),(4,7),(5,0x6c),(7,0),(12,0x81),(13,0x3f),(15,2),(16,1),(17,0),(18,0)]:w(0xc00004,0x8000|(reg<<8)|val)
 addr(0,True)
 for col in [0,0xeee,0x00e,0x04e,0x08e,0x0ee,0x0e8,0x0e0,0x8e0,0xee0,0xe80,0xe00,0xe08,0xe0e,0x80e,0x444]:w(0xc00000,col)
 addr(0)
 for tile in range(17):
  for y in range(8):
   pixels=[0 if tile==0 else 1+(tile%14) for x in range(8)]
   for x in [0,4]:w(0xc00000,sum(pixels[x+i]<<(12-4*i) for i in range(4)))
 addr(0xc000)
 for y in range(32):
  for x in range(64):w(0xc00000,1+((x//2+y//2)*3)%14)
 w(0xc00004,0x8144)
 words.extend([0x5279,0x00ff,0x1000,0x60f8])
 assert 0x400+2*len(words)<65536
 for i,v in enumerate(words):struct.pack_into('>H',rom,0x400+2*i,v)
 for i,v in enumerate([0x4e72,0x2700,0x60fe]):struct.pack_into('>H',rom,0x300+2*i,v)
 checksum=sum(struct.unpack_from(">H",rom,i)[0] for i in range(0x200,len(rom),2)) & 0xffff
 struct.pack_into(">H",rom,0x18e,checksum)
 return bytes(rom)

if __name__ == '__main__':
 path=Path(__file__).with_name('VRAMpage-MD-Colour-Test.bin')
 path.write_bytes(diagnostic())
 print(f'Wrote {path.name}: {path.stat().st_size} bytes')
