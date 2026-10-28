#!/usr/bin/env python3
"""Strict instruction-subset execution and static layout tests.

This is NOT a real hardware or Genesis Plus GX runtime test. It deliberately
fails if the builder adds an opcode without a corresponding simulator rule.
"""
from pathlib import Path
import hashlib,struct,sys,unittest,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_fx
R=build_fx
ROM=(R.OUT/'VRAMpage-MD-FX-Lab-v0.3.1-Fixed.bin').read_bytes()

class CPU:
    def __init__(self,pal=False,start_at=None,inputs=None):
        self.d=[0]*8;self.a=[0]*8;self.z=False;self.n=False
        self.pc=int.from_bytes(ROM[4:8],'big');self.a[7]=int.from_bytes(ROM[0:4],'big')
        self.stack=[];self.commands=[];self.psg=[];self.region=0xC1 if pal else 0x81
        self.pad_th=0x40;self.ready_start=start_at;self.inputs=sorted(inputs or []);self.frames=0;self.frame_scenes={};self.scene='boot';self.cursor_choices=[];self.enters=[]
        self.vram=bytearray(65536);self.cram=bytearray(128);self.vsram=bytearray(80)
        self.port='vram';self.addr=0;self.in_vblank=False;self.autoinc=2;self.hscroll_mode=0
        self.tmss=0;self.display=False;self.stepcount=0;self.scroll_addresses={}
        self.scene_targets={R.asm.labels['load_'+name]:name for name in ('title','vortex','aurora','sprites','colour','audio')}
    def rw(self,pos):return struct.unpack_from('>H',ROM,pos)[0]
    def rl(self,pos):return struct.unpack_from('>I',ROM,pos)[0]
    def w(self):v=self.rw(self.pc);self.pc+=2;return v
    def l(self):v=self.rl(self.pc);self.pc+=4;return v
    def signed(self,v):return v-65536 if v&0x8000 else v
    def memread(self,addr,size):
        if addr==0xA10001:return self.region
        if addr==0xA10003:
            mask=0
            if self.ready_start is not None and self.frames>=self.ready_start:mask|=0x80
            for frame,buttons in self.inputs:
                if self.frames>=frame:mask=buttons
            return 0xFF ^ ((mask&0x3f) if self.pad_th else ((mask>>2)&0x30))
        if addr==0xC00004:
            self.in_vblank=not self.in_vblank
            return 8 if self.in_vblank else 0
        raise AssertionError(f'Unrecognised read 0x{addr:08X}')
    def memwrite(self,addr,size,val):
        if addr==0xA14000:
            self.tmss=val;return
        if addr==0xA10003:
            self.pad_th=val;return
        if addr==0xA10009:return
        if addr==0xC00011:
            self.psg.append(val&255);return
        if addr==0xC00004:
            if size==2:
                if not val&0x8000:raise AssertionError('Expected VDP register write')
                reg=(val>>8)&31
                if reg==1:self.display=bool(val&0x40)
                if reg==11:self.hscroll_mode=val&3
                if reg==15:self.autoinc=val&255
                return
            first=val>>16;low=val&0xffff
            code=((first>>14)&3)|((low>>2)&0x3c)
            self.addr=(first&0x3fff)|((low&3)<<14)
            self.port={1:'vram',3:'cram',5:'vsram'}.get(code)
            if not self.port:raise AssertionError(f'VDP command {val:08X} code={code}')
            self.commands.append((self.scene,self.port,self.addr))
            return
        if addr==0xC00000:
            buf={'vram':self.vram,'cram':self.cram,'vsram':self.vsram}[self.port]
            if self.addr+1>=len(buf):raise AssertionError(f'bad {self.port} index {self.addr}')
            if self.port=='vram' and self.autoinc==32:
                entries=self.scroll_addresses.setdefault(self.scene,[])
                if len(entries)<120:entries.append(self.addr)
            buf[self.addr:self.addr+2]=struct.pack('>H',val&65535)
            self.addr+=self.autoinc
            return
        raise AssertionError(f'Unrecognised write {size} to 0x{addr:08X}')
    def step(self):
        op_pc=self.pc;op=self.w();self.stepcount+=1
        if op_pc in self.scene_targets:
            self.scene=self.scene_targets[op_pc]
            self.enters.append((self.scene,self.frames))
        if op_pc==R.asm.labels['draw_cursor']:
            self.cursor_choices.append((self.frames,self.d[7]))
        if op==0x46FC:self.w();return
        if op==0x4E75:
            self.pc=self.stack.pop();return
        if op&0xF1FF==0x207C:
            self.a[(op>>9)&7]=self.l();return
        if op&0xF100==0x7000:
            reg=(op>>9)&7;v=op&255;self.d[reg]=v-256 if v>=128 else v;return
        if op&0xFF00 in (0x6000,0x6100,0x6600,0x6700,0x6A00) and (op&0xff)==0:
            disp_pos=self.pc;ofs=self.signed(self.w());target=disp_pos+ofs
            if op&0xFF00==0x6100:self.stack.append(self.pc)
            if op&0xFF00 in (0x6000,0x6100) or (op&0xFF00==0x6600 and not self.z) or (op&0xFF00==0x6700 and self.z) or (op&0xFF00==0x6A00 and not self.n):self.pc=target
            return
        if op&0xFFF8==0x51C8:
            reg=op&7;disp_pos=self.pc;ofs=self.signed(self.w())
            self.d[reg]=(self.d[reg]&0xFFFF0000)|((self.d[reg]-1)&0xFFFF)
            if (self.d[reg]&65535)!=65535:self.pc=disp_pos+ofs
            return
        if op&0xF1FF==0x303C:
            self.d[(op>>9)&7]=self.w();return
        if op&0xF1FF in (0x30BC,0x20BC,0x10BC):
            reg=(op>>9)&7;size={0x30BC:2,0x20BC:4,0x10BC:1}[op&0xF1FF]
            val=self.l() if size==4 else self.w()
            self.memwrite(self.a[reg],size,val);return
        if op&0xF1F8 in (0x1010,0x3010):
            reg=(op>>9)&7;ar=op&7;size=1 if (op&0xF1F8)==0x1010 else 2
            val=self.memread(self.a[ar],size)
            self.d[reg]=(self.d[reg]&(-1<<(size*8)))|val
            self.z=(val==0);return
        if op&0xF1F8 in (0x1080,0x3080):
            ar=(op>>9)&7;src=op&7;size=1 if op&0xF1F8==0x1080 else 2
            self.memwrite(self.a[ar],size,self.d[src]);return
        if op&0xF1F8==0x3000:
            dest=(op>>9)&7;src=op&7
            self.d[dest]=(self.d[dest]&0xFFFF0000)|(self.d[src]&65535);return
        if op in (0x329A,0x329E):
            source=op&7;p=self.a[source];v=self.rw(p);self.a[source]+=2
            self.memwrite(self.a[1],2,v);return
        if op&0xFFF8 in (0x0240,0x0200,0x0640):
            r=op&7;imm=self.w()
            if (op&0xFFF8)==0x0640:self.d[r]=(self.d[r]+imm)&65535;self.z=(self.d[r]==0)
            elif (op&0xFFF8)==0x0240:self.d[r]&=imm;self.z=(self.d[r]&65535)==0
            else:self.d[r]&=(imm|0xFFFFFF00);self.z=(self.d[r]&255)==0
            return
        if op&0xFFF8==0x0C40:
            r=op&7;value=self.w();self.z=(self.d[r]&65535)==value;return
        if op&0xFFF8==0x0A00:
            r=op&7;val=self.w();self.d[r]=(self.d[r]&~255)|((self.d[r]^val)&255);self.z=(self.d[r]&255)==0;return
        if op&0xFFF8==0x4A40:
            r=op&7;self.z=(self.d[r]&65535)==0;self.n=bool(self.d[r]&0x8000);return
        if op&0xFFF8==0x4A00:
            self.z=(self.d[op&7]&255)==0;return
        if op&0xF1F8==0xD040:
            dest=(op>>9)&7;src=op&7
            self.d[dest]=(self.d[dest]&0xFFFF0000)|((self.d[dest]+self.d[src])&65535);return
        if op&0xF1F8 in (0x8000,0xB100,0xC000):
            dest=(op>>9)&7 if (op&0xF1F8)!=0xB100 else op&7
            src=op&7 if (op&0xF1F8)!=0xB100 else (op>>9)&7
            if (op&0xF1F8)==0x8000:out=(self.d[dest]|self.d[src])&255
            elif (op&0xF1F8)==0xB100:out=(self.d[dest]^self.d[src])&255
            else:out=(self.d[dest]&self.d[src])&255
            self.d[dest]=(self.d[dest]&~255)|out;self.z=(out==0);return
        if op&0xF1F8==0xE148:
            r=op&7;count=(op>>9)&7 or 8
            self.d[r]=(self.d[r]&~65535)|((self.d[r]<<count)&65535)
            self.z=(self.d[r]&65535)==0;return
        if op&0xF1F8==0x5140:
            r=op&7;count=(op>>9)&7 or 8
            self.d[r]=(self.d[r]&0xFFFF0000)|((self.d[r]-count)&65535);return
        if op&0xF1F8==0x5040:
            r=op&7;count=(op>>9)&7 or 8
            self.d[r]=(self.d[r]+count)&65535;return
        raise AssertionError(f'Unsupported instruction {op:04X} at {op_pc:06X} after {self.stepcount} steps')
    def run_until(self,predicate,max_steps=5000000):
        while self.stepcount<max_steps:
            if predicate(self):return
            if self.pc==R.asm.labels['wait_vblank']:
                self.frames+=1
                self.frame_scenes[self.scene]=self.frame_scenes.get(self.scene,0)+1
            self.step()
        raise AssertionError('Predicate did not become true in execution budget')

    def run(self,max_steps=5000000):
        while self.stepcount<max_steps:
            if self.pc==R.asm.labels['wait_vblank']:
                self.frames+=1
                self.frame_scenes[self.scene]=self.frame_scenes.get(self.scene,0)+1
            if self.scene=='audio' and self.pc==R.asm.labels['whole_demo']:
                return
            self.step()
        raise AssertionError('Execution did not return to opening title within step budget')

class TestROM(unittest.TestCase):
 def test_header_checksum_and_vectors(self):
    self.assertEqual(ROM[0x100:0x104],b'SEGA')
    self.assertEqual(struct.unpack_from('>I',ROM,4)[0],0x200)
    self.assertEqual(struct.unpack_from('>I',ROM,0)[0],0xFFFF00)
    self.assertEqual(struct.unpack_from('>I',ROM,0x1A4)[0],len(ROM)-1)
    self.assertEqual(sum(struct.unpack_from('>H',ROM,i)[0] for i in range(0x200,len(ROM),2))&65535,struct.unpack_from('>H',ROM,0x18E)[0])
    self.assertEqual(len(ROM)%2,0)
 def test_vdp_assets(self):
    self.assertLess((R.ARROW_ID+1)*32,0xC000)
    self.assertEqual(len(R.CRAM),4*16*2)
    for name in ('title','vortex','aurora','sprites','colour','audio'):
     p=R.asm.labels['map_'+name]
     self.assertEqual(len(ROM[p:p+4096]),4096)
 def test_ntsc_main_sequence(self):
    c=CPU();c.run()
    self.assertEqual(c.tmss,0x53454741)
    self.assertEqual(c.frame_scenes['title'],600)
    self.assertEqual(c.frame_scenes['vortex'],719)
    self.assertEqual(c.frame_scenes['aurora'],719)
    self.assertEqual(c.frame_scenes['sprites'],479)
    self.assertEqual(c.frame_scenes['colour'],479)
    self.assertEqual(c.frame_scenes['audio'],479)
    self.assertTrue(c.display)
    self.assertIn(0x9F,c.psg)
    self.assertTrue(any(scene=='sprites' and addr==0xF400 for scene,kind,addr in c.commands))
    self.assertTrue(any(scene=='vortex' and kind=='vsram' for scene,kind,addr in c.commands))
    self.assertTrue(any(scene=='aurora' and kind=='cram' for scene,kind,addr in c.commands))
    self.assertTrue(any(scene=='vortex' and kind=='vram' and addr==0xF800 for scene,kind,addr in c.commands))
    self.assertEqual(c.autoinc,2)
    self.assertEqual(c.hscroll_mode,0)
 def test_fx_scroll_writes_are_cell_aligned_and_bounded(self):
    c=CPU();c.run()
    expected=[0xF800+i*32 for i in range(30)]
    for name in ('vortex','aurora'):
        self.assertEqual(c.scroll_addresses[name][:30],expected)
        self.assertEqual(c.scroll_addresses[name][30:60],expected)
        self.assertTrue(all(0xF800 <= addr <= 0xFBA0 for addr in c.scroll_addresses[name]))
    self.assertEqual(c.autoinc,2)
    self.assertEqual(c.hscroll_mode,0)
 def test_fx_rom_tables_and_palettes_obey_vdp_constraints(self):
    self.assertEqual(R.PHASES,96)
    self.assertLess((R.ARROW_ID+1)*32,0xC000)
    self.assertLess(0xF800+30*32,0xFC00)
    for name in ('vortex','aurora'):
        self.assertEqual(len(R.FX_PALETTES[name]),R.PHASES*128)
        self.assertEqual(len(R.FX_SCROLLS[name]),R.PHASES*60)
        for phase in range(R.PHASES):
            for offset in range(0,128,2):
                value=struct.unpack_from('>H',R.fx_palette(name,phase),offset)[0]
                self.assertEqual(value&0x111,0)
            for offset in range(0,60,2):
                value=struct.unpack_from('>H',R.fx_scroll(name,phase),offset)[0]
                self.assertLess(value,1024)
        # Loop seam: last-frame CRAM channels remain close to the next frame.
        first=struct.unpack('>64H',R.fx_palette(name,0))
        last=struct.unpack('>64H',R.fx_palette(name,R.PHASES-1))
        for a,b in zip(first,last):
            for shift in (1,5,9):
                self.assertLessEqual(abs(((a>>shift)&7)-((b>>shift)&7)),2)
 def test_startup_copies_all_approved_and_effect_patterns_to_actual_vram(self):
    # This regression fails against v0.3: its startup only uploaded the old
    # title tiles and left the selector/FX patterns uninitialised in VRAM.
    c=CPU()
    c.run_until(lambda c:c.pc==R.asm.labels['whole_demo'])
    self.assertEqual(c.vram[:len(R.ALL_PATTERNS)], R.ALL_PATTERNS)
    self.assertEqual(c.vram[R.ARROW_ID*32:(R.ARROW_ID+1)*32],R.UI_PATTERNS[-32:])
    self.assertGreater(len(R.ALL_PATTERNS),len(R.PATTERNS)+64)
    self.assertTrue(any(c.vram[R.FX_BASE*32:(R.FX_BASE+R.FX_TILE_COUNT)*32]))

 def test_demonstration_maps_never_reuse_portrait_or_logo_tiles(self):
    # All non-title stages use original FX patterns and no image tile IDs.
    for name,cell in [('sprites',R.sprite_cells),('colour',R.colour_cells),('audio',R.audio_cells)]:
        with self.subTest(scene=name):
            self.assertTrue(all(R.FX_BASE <= (word&0x7ff) < R.FX_BASE+R.FX_TILE_COUNT for word in cell))
            self.assertGreater(len(set(cell)),100)

 def test_static_effect_palettes_are_loaded_at_scene_start(self):
    c=CPU()
    c.run_until(lambda c:c.scene=='sprites' and c.pc==R.asm.labels['run_sprites']+4)
    self.assertEqual(c.cram,R.FX_PALETTES['aurora'][:128])

 def test_approved_portrait_tiles_are_byte_identical(self):
    self.assertEqual(ROM[R.asm.labels['patterns']:R.asm.labels['patterns']+len(R.PATTERNS)],R.PATTERNS)
    for idx,original in enumerate(R.BASE_TITLE_CELLS):
        tx,ty=idx%40,idx//40
        if not any(x0<=tx*8<x1 and y0<=ty*8<y1 for x0,y0,x1,y1 in R.UI_BLOCKS):
            self.assertEqual(R.title_cells[idx],original)
    self.assertEqual(ROM[R.asm.labels['patterns']+len(R.PATTERNS):R.asm.labels['patterns']+len(R.PATTERNS)+32],bytes(32))
    self.assertEqual(ROM[R.asm.labels['map_title']:R.asm.labels['map_title']+4096],R.full_map(R.title_cells))
 def test_pal_main_sequence(self):
    c=CPU(pal=True);c.run()
    self.assertEqual(c.frame_scenes['title'],500)
    self.assertEqual(c.frame_scenes['vortex'],600)
    self.assertEqual(c.frame_scenes['aurora'],600)
 def test_start_skips_intro(self):
    c=CPU(inputs=[(5,0x80),(8,0)]);c.run_until(lambda c:len(c.enters)>1)
    self.assertEqual(c.frame_scenes['title'],5)
    self.assertEqual(c.enters[1][0],'vortex')

 def test_dpad_navigation_and_abcs_launch(self):
     # Highlight next with Down, next again with Right, then A opens sprite scene.
     c=CPU(inputs=[(2,0x02),(4,0),(6,0x08),(8,0),(10,0x40),(12,0)])
     c.run_until(lambda c:len(c.enters)>1)
     self.assertIn((2,1),c.cursor_choices)
     self.assertIn((6,2),c.cursor_choices)
     self.assertEqual(c.enters[1][0],'sprites')
     self.assertLess(c.enters[1][1],40)
     self.assertEqual(c.frame_scenes.get('sprites',0),0)

 def test_buttons_and_wrap_no_repeat(self):
     # UP wraps from item 0 to item 4, hold for several frames must not repeat.
     c=CPU(inputs=[(3,0x01),(9,0),(12,0x10),(14,0)])
     c.run_until(lambda c:len(c.enters)>1)
     self.assertEqual(c.cursor_choices[:2],[(0,0),(3,4)])
     self.assertEqual(c.enters[1][0],'audio')

 def test_B_and_C_launch_selections(self):
     for button in (0x10,0x20):
         with self.subTest(button=button):
             c=CPU(inputs=[(5,button),(8,0)])
             c.run_until(lambda c:len(c.enters)>1)
             self.assertEqual(c.enters[1][0],'vortex')
             self.assertLess(c.enters[1][1],20)

 def test_start_returns_to_menu_without_relaunching_when_held(self):
     c=CPU(inputs=[(3,0x80),(6,0),(20,0x80),(31,0)])
     c.run_until(lambda c:len(c.cursor_choices)>1)
     self.assertGreaterEqual(len(c.cursor_choices),2)
     self.assertEqual(c.enters[1][0],'vortex')
     self.assertTrue(any(kind=='title' and at>=20 for kind,at in c.enters))

if __name__=='__main__': unittest.main(verbosity=2)
