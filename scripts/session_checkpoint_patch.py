#!/usr/bin/env python3
"""Add bounded audio/pad omission snapshots to the pinned runtime profile."""
from pathlib import Path
import shutil
import sys

ROOT = Path(sys.argv[1]) / "src/main/c"


def append(rel, marker, body):
    path = ROOT / rel
    source = path.read_text()
    if marker in source:
        return
    path.write_text(source + "\n" + body + "\n")


def insert_before(rel, marker, anchor, body):
    path = ROOT / rel
    source = path.read_text()
    if marker in source:
        return
    if source.count(anchor) != 1:
        raise SystemExit(f"Pinned insertion anchor missing or ambiguous in {rel}")
    path.write_text(source.replace(anchor, body + "\n" + anchor, 1))


blip_header = ROOT / "core/sound/blip_buf.h"
header = blip_header.read_text()
if "checkpoint_blip_size" not in header:
    anchor = "void blip_delete( blip_t* );"
    if header.count(anchor) != 1:
        raise SystemExit("Pinned Blip API anchor missing or ambiguous")
    header = header.replace(anchor, anchor + "\nunsigned checkpoint_blip_size(const blip_t*);\nint checkpoint_blip_save(blip_t*, unsigned char*, unsigned);\nint checkpoint_blip_load(blip_t*, const unsigned char*, unsigned);", 1)
    blip_header.write_text(header)

append("core/sound/blip_buf.c", "unsigned checkpoint_blip_size(", r'''#include <stdint.h>
typedef struct { fixed_t factor, offset; int size, integrator[2]; } checkpoint_blip_header;
unsigned checkpoint_blip_size(const blip_t *m) {
  return m ? (unsigned)(sizeof(checkpoint_blip_header) + 2u * (unsigned)(m->size + buf_extra) * sizeof(buf_t)) : 0;
}
int checkpoint_blip_save(blip_t *m, unsigned char *out, unsigned cap) {
  checkpoint_blip_header h; unsigned need=checkpoint_blip_size(m), p=0, bytes;
  if (!m || !out || cap<need) return -1;
  h.factor=m->factor; h.offset=m->offset; h.size=m->size;
  h.integrator[0]=m->integrator[0]; h.integrator[1]=m->integrator[1];
  memcpy(out+p,&h,sizeof(h)); p+=(unsigned)sizeof(h);
  bytes=(unsigned)(m->size+buf_extra)*sizeof(buf_t);
  memcpy(out+p,m->buffer[0],bytes); p+=bytes;
  memcpy(out+p,m->buffer[1],bytes); p+=bytes;
  return (int)p;
}
int checkpoint_blip_load(blip_t *m, const unsigned char *in, unsigned len) {
  checkpoint_blip_header h; unsigned p=0, bytes, need=checkpoint_blip_size(m);
  if (!m || !in || len!=need) return -1;
  memcpy(&h,in,sizeof(h)); p+=(unsigned)sizeof(h);
  if (h.size!=m->size) return -1;
  bytes=(unsigned)(m->size+buf_extra)*sizeof(buf_t);
  m->factor=h.factor; m->offset=h.offset;
  m->integrator[0]=h.integrator[0]; m->integrator[1]=h.integrator[1];
  memcpy(m->buffer[0],in+p,bytes); p+=bytes;
  memcpy(m->buffer[1],in+p,bytes); p+=bytes;
  return (int)p;
}''')

append("core/sound/psg.c", "unsigned checkpoint_psg_size(", r'''unsigned checkpoint_psg_stock_bound(void) {
  return (unsigned)(sizeof(psg.clocks)+sizeof(psg.latch)+sizeof(psg.noiseShiftValue)+
    sizeof(psg.regs)+sizeof(psg.freqInc)+sizeof(psg.freqCounter)+sizeof(psg.polarity)+sizeof(psg.chanOut));
}
unsigned checkpoint_psg_size(void) { return (unsigned)sizeof(psg); }
int checkpoint_psg_save(unsigned char *out, unsigned cap) {
  if (!out || cap<sizeof(psg)) return -1;
  memcpy(out,&psg,sizeof(psg)); return (int)sizeof(psg);
}
int checkpoint_psg_load(const unsigned char *in, unsigned len) {
  if (!in || len!=sizeof(psg)) return -1;
  memcpy(&psg,in,sizeof(psg)); return (int)sizeof(psg);
}''')

append("core/sound/ym2612.c", "unsigned checkpoint_ym2612_size(", r'''/* Pinned YM serializer advances twice per one-byte DT index (24 slots). */
unsigned checkpoint_ym2612_size(void) { return (unsigned)(sizeof(ym2612) + 48u); }''')

append("core/cart_hw/md_cart.c", "int checkpoint_plain_md_cart(", r'''#include <stdint.h>
int checkpoint_plain_md_cart(void) {
  int i;
  if (cart.special || cart.hw.realtec || cart.hw.bankshift || cart.hw.time_r ||
      (cart.hw.time_w && cart.hw.time_w != default_time_w) || cart.hw.regs_r || cart.hw.regs_w)
    return 0;
  for (i=0; i<4; i++) if (cart.hw.mask[i] || cart.hw.addr[i]) return 0;
  /* Only plain ROM and the core's ordinary SRAM handlers are replayable. */
  for (i=0; i<0x40; i++) {
    cpu_memory_map *m = &m68k.memory_map[i];
    uintptr_t base = (uintptr_t)m->base, rom = (uintptr_t)cart.rom;
    if (m->base == sram.sram) {
      if (!sram.on || m->read8 != sram_read_byte || m->read16 != sram_read_word ||
          zbank_memory_map[i].read != sram_read_byte ||
          (m->write8 != sram_write_byte && m->write8 != m68k_unused_8_w) ||
          (m->write16 != sram_write_word && m->write16 != m68k_unused_16_w) ||
          (zbank_memory_map[i].write != sram_write_byte && zbank_memory_map[i].write != zbank_unused_w)) return 0;
    } else if (base < rom || base - rom >= 0x800000 || ((base - rom) & 0xffff) ||
               m->read8 || m->read16 || zbank_memory_map[i].read ||
               m->write8 != m68k_unused_8_w || m->write16 != m68k_unused_16_w ||
               zbank_memory_map[i].write != zbank_unused_w) return 0;
  }
  return 1;
}''')

insert_before("core/vdp_ctrl.c", "unsigned checkpoint_vdp_context_bound(", "#ifdef VRAM_TX_DIAGNOSTIC\n#include <emscripten/emscripten.h>", r'''unsigned checkpoint_vdp_context_bound(void) {
  return (unsigned)(sizeof(sat)+sizeof(vram)+sizeof(cram)+sizeof(vsram)+sizeof(reg)+
    sizeof(addr)+sizeof(addr_latch)+sizeof(code)+sizeof(pending)+sizeof(status)+
    sizeof(dmafill)+sizeof(fifo_idx)+sizeof(fifo)+sizeof(h_counter)+sizeof(hint_pending)+
    sizeof(vint_pending)+sizeof(dma_length)+sizeof(dma_type)+sizeof(dma_src)+sizeof(cached_write));
}''')

append("core/sound/sound.c", "unsigned checkpoint_sound_size(", r'''extern unsigned checkpoint_psg_size(void);
extern unsigned checkpoint_ym2612_size(void);
extern int checkpoint_psg_save(unsigned char*, unsigned);
extern int checkpoint_psg_load(const unsigned char*, unsigned);
unsigned checkpoint_sound_size(void) {
  return (unsigned)(sizeof(fm_last)+sizeof(fm_cycles_ratio)+sizeof(fm_cycles_start)+sizeof(fm_cycles_count)+sizeof(fm_cycles_busy)+sizeof(ym3438_cycles))+checkpoint_psg_size();
}
int checkpoint_sound_save(unsigned char *out, unsigned cap) {
  unsigned p=0,n=checkpoint_sound_size();
  if (!out || cap<n) return -1;
#define CHECKPOINT_SOUND_SAVE(x) do { memcpy(out+p,&(x),sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  CHECKPOINT_SOUND_SAVE(fm_last); CHECKPOINT_SOUND_SAVE(fm_cycles_ratio); CHECKPOINT_SOUND_SAVE(fm_cycles_start); CHECKPOINT_SOUND_SAVE(fm_cycles_count); CHECKPOINT_SOUND_SAVE(fm_cycles_busy); CHECKPOINT_SOUND_SAVE(ym3438_cycles);
#undef CHECKPOINT_SOUND_SAVE
  int m=checkpoint_psg_save(out+p,cap-p); if(m<0)return -1; p+=(unsigned)m;
  return (int)p;
}
int checkpoint_sound_load(const unsigned char *in, unsigned len) {
  unsigned p=0,n=checkpoint_sound_size();
  if (!in || len!=n) return -1;
#define CHECKPOINT_SOUND_LOAD(x) do { memcpy(&(x),in+p,sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  CHECKPOINT_SOUND_LOAD(fm_last); CHECKPOINT_SOUND_LOAD(fm_cycles_ratio); CHECKPOINT_SOUND_LOAD(fm_cycles_start); CHECKPOINT_SOUND_LOAD(fm_cycles_count); CHECKPOINT_SOUND_LOAD(fm_cycles_busy); CHECKPOINT_SOUND_LOAD(ym3438_cycles);
#undef CHECKPOINT_SOUND_LOAD
  int m=checkpoint_psg_load(in+p,checkpoint_psg_size()); if(m<0)return -1; p+=(unsigned)m;
  fm_ptr=fm_buffer;
  return (int)p;
}''')

append("core/sound/sound.c", "unsigned checkpoint_stock_sound_bound(", r'''extern unsigned checkpoint_ym2612_size(void);
extern unsigned checkpoint_psg_stock_bound(void);
unsigned checkpoint_stock_sound_bound(void) {
  if (config.ym3438 != 0) return 0;
  return (unsigned)(sizeof(config.ym3438) + sizeof(fm_cycles_start)) +
         checkpoint_ym2612_size() + checkpoint_psg_stock_bound();
}''')

append("core/system.c", "int checkpoint_audio_validate(", r'''extern unsigned checkpoint_sound_size(void);
extern int checkpoint_sound_save(unsigned char*, unsigned);
extern int checkpoint_sound_load(const unsigned char*, unsigned);
extern unsigned checkpoint_blip_size(const blip_t*);
extern int checkpoint_blip_save(blip_t*, unsigned char*, unsigned);
extern int checkpoint_blip_load(blip_t*, const unsigned char*, unsigned);
static unsigned checkpoint_audio_measure(void) {
  return (unsigned)(sizeof(mcycles_vdp)+sizeof(eq)+sizeof(llp)+sizeof(rrp)+sizeof(snd.sample_rate)+sizeof(snd.frame_rate)) + checkpoint_sound_size() + checkpoint_blip_size(snd.blips[0]);
}
int checkpoint_audio_validate(const unsigned char *in, unsigned len) {
  int sample_rate; double frame_rate;
  unsigned off=(unsigned)(sizeof(mcycles_vdp)+sizeof(eq)+sizeof(llp)+sizeof(rrp));
  if (!in || !snd.blips[0] || len!=checkpoint_audio_measure()) return 0;
  memcpy(&sample_rate,in+off,sizeof(sample_rate));
  memcpy(&frame_rate,in+off+sizeof(sample_rate),sizeof(frame_rate));
  return sample_rate==snd.sample_rate && frame_rate==snd.frame_rate;
}
int checkpoint_audio_size(void) { return (int)checkpoint_audio_measure(); }
int checkpoint_audio_save(unsigned char *out, unsigned cap) {
  unsigned p=0,n=checkpoint_audio_measure();
  if (!out || !snd.blips[0] || cap<n) return -1;
#define CHECKPOINT_SYSTEM_SAVE(x) do { memcpy(out+p,&(x),sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  CHECKPOINT_SYSTEM_SAVE(mcycles_vdp); CHECKPOINT_SYSTEM_SAVE(eq); CHECKPOINT_SYSTEM_SAVE(llp); CHECKPOINT_SYSTEM_SAVE(rrp); CHECKPOINT_SYSTEM_SAVE(snd.sample_rate); CHECKPOINT_SYSTEM_SAVE(snd.frame_rate);
#undef CHECKPOINT_SYSTEM_SAVE
  int m=checkpoint_sound_save(out+p,cap-p); if(m<0)return -1; p+=(unsigned)m;
  m=checkpoint_blip_save(snd.blips[0],out+p,cap-p); if(m<0)return -1; p+=(unsigned)m;
  return (int)p;
}
int checkpoint_audio_load(const unsigned char *in, unsigned len) {
  unsigned p=0,n=checkpoint_audio_measure();
  if (!checkpoint_audio_validate(in,len)) return -1;
#define CHECKPOINT_SYSTEM_LOAD(x) do { memcpy(&(x),in+p,sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  CHECKPOINT_SYSTEM_LOAD(mcycles_vdp); CHECKPOINT_SYSTEM_LOAD(eq); CHECKPOINT_SYSTEM_LOAD(llp); CHECKPOINT_SYSTEM_LOAD(rrp); CHECKPOINT_SYSTEM_LOAD(snd.sample_rate); CHECKPOINT_SYSTEM_LOAD(snd.frame_rate);
#undef CHECKPOINT_SYSTEM_LOAD
  int m=checkpoint_sound_load(in+p,checkpoint_sound_size()); if(m<0)return -1; p+=(unsigned)m;
  m=checkpoint_blip_load(snd.blips[0],in+p,len-p); if(m<0)return -1; p+=(unsigned)m;
  return (int)p;
}''')

append("core/input_hw/gamepad.c", "unsigned checkpoint_pad_size(", r'''unsigned checkpoint_pad_size(void) { return (unsigned)(sizeof(input)+sizeof(gamepad)+sizeof(flipflop)+sizeof(latch)); }
int checkpoint_pad_validate(const unsigned char *in, unsigned len) {
  t_input saved; unsigned p=0;
  if (!in || len!=checkpoint_pad_size()) return 0;
  memcpy(&saved,in,sizeof(saved));
  if (saved.system[0]!=NO_SYSTEM && saved.system[0]!=SYSTEM_GAMEPAD) return 0;
  if (saved.system[1]!=NO_SYSTEM && saved.system[1]!=SYSTEM_GAMEPAD) return 0;
  for (unsigned i=0;i<MAX_DEVICES;i++) {
    if (i==0 || i==4) { if(saved.dev[i]!=DEVICE_PAD3B && saved.dev[i]!=DEVICE_PAD6B && saved.dev[i]!=NO_DEVICE) return 0; }
    else if(saved.dev[i]!=NO_DEVICE) return 0;
  }
  p=(unsigned)sizeof(saved)+(unsigned)sizeof(gamepad)+(unsigned)sizeof(flipflop)+(unsigned)sizeof(latch);
  return p==len;
}
int checkpoint_pad_save(unsigned char *out, unsigned cap) {
  unsigned p=0,n=checkpoint_pad_size();
  if (!out || cap<n) return -1;
  memcpy(out+p,&input,sizeof(input)); p+=(unsigned)sizeof(input);
  memcpy(out+p,gamepad,sizeof(gamepad)); p+=(unsigned)sizeof(gamepad);
  memcpy(out+p,flipflop,sizeof(flipflop)); p+=(unsigned)sizeof(flipflop);
  memcpy(out+p,&latch,sizeof(latch)); p+=(unsigned)sizeof(latch);
  return (int)p;
}
int checkpoint_pad_load(const unsigned char *in, unsigned len) {
  unsigned p=0;
  if (!checkpoint_pad_validate(in,len)) return -1;
  memcpy(&input,in+p,sizeof(input)); p+=(unsigned)sizeof(input);
  memcpy(gamepad,in+p,sizeof(gamepad)); p+=(unsigned)sizeof(gamepad);
  memcpy(flipflop,in+p,sizeof(flipflop)); p+=(unsigned)sizeof(flipflop);
  memcpy(&latch,in+p,sizeof(latch)); p+=(unsigned)sizeof(latch);
  return (int)p;
}''')

shutil.copyfile(Path(__file__).with_name("session_checkpoint_runtime.c"), ROOT / "wasm/session_checkpoint_runtime.c")
wasm = ROOT / "wasm/wasm.c"
source = wasm.read_text()
marker = '#include "session_checkpoint_runtime.c" /* VRAMpage native session checkpoint */'
if marker not in source:
    anchor = '#if defined(VRAM_TX_RUNTIME)\n#include "fm_data_fault_core.c"\n#include "fm_data_fault_runtime.c"\n#endif'
    if source.count(anchor) != 1:
        raise SystemExit("Pinned runtime include anchor missing or ambiguous")
    source = source.replace(anchor, anchor + "\n" + marker, 1)
if source.count(marker) != 1:
    raise SystemExit("Session checkpoint runtime include is ambiguous")
start_hook = "    session_checkpoint_runtime_start();\n    error_init();"
if start_hook not in source:
    anchor = "    error_init();"
    if source.count(anchor) != 1:
        raise SystemExit("Pinned start lifecycle anchor missing or ambiguous")
    source = source.replace(anchor, start_hook, 1)
elif source.count(start_hook) != 1:
    raise SystemExit("Session checkpoint lifecycle hook is ambiguous")
wasm.write_text(source)
