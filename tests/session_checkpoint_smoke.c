/* Exercise backend publication/failure boundaries without exposing test APIs. */
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define STATE_SIZE 512
#define STATE_VERSION "TEST-STATE-00000"
#define MAX_DEVICES 8
#define SYSTEM_MD 128
#define SYSTEM_GAMEPAD 1
#define NO_SYSTEM 0
#define NO_DEVICE 255
#define DEVICE_PAD3B 0
#define DEVICE_PAD6B 1
#define WORK_RAM_FAULT_APPLY_READ 1
#define WORK_RAM_FAULT_APPLY_WRITE 2
#define WORK_RAM_PULSE_ARMED 1

typedef struct { int value; } blip_t;
typedef struct { uint8_t *base; } cpu_memory_map;
struct _zbank_memory_map { uint8_t *base; } zbank_memory_map[256];
struct { cpu_memory_map memory_map[256]; int cycles, int_level, stopped; } m68k;
struct { uint8_t *rom; uint32_t romsize, special; struct { uint8_t regs[4]; } hw; } cart;
struct { uint8_t *sram; uint32_t start,end,crc; int on,detected,custom; } sram;
struct { int ym3438; } config;
struct { int system[2],dev[MAX_DEVICES],pad[MAX_DEVICES],analog[MAX_DEVICES][2]; } input;
struct { blip_t *blips[3]; } snd;
struct { uint8_t *data; int width,height,pitch; struct { int x,y,w,h,ow,oh,changed; } viewport; } bitmap;
uint8_t work_ram[64],zram[16],io_reg[16];
int zstate,zbank;
typedef struct { int value; } Z80_Regs;
int system_hw = SYSTEM_MD;
void *svp;
uint32_t *frame_buffer;
uint32_t rom_size=0x10000;
static uint32_t frame_number;
static int faults,held_pulse,plain_cart=1,bound_extra,save_failure,load_failure,audio_failure,pad_failure,save_calls,load_calls;
static int z80_faults;
static int work_ram_logic_applies(int operation) { (void)operation; return faults; }
uint32_t get_logic_frame(void) { return frame_number; }
uint32_t get_logic_pulse_state(void) { return held_pulse; }
uint32_t get_logic_address_mask(void) { return faults; }
int get_psg_data_bridge_enabled(void) { return faults; }
int get_psg_data_mask(void) { return faults; }
int get_fm_data_bridge_enabled(void) { return faults; }
int get_fm_data_mask(void) { return faults; }
int get_z80_ram_bridge_enabled(void) { return z80_faults; }
int get_vram_fault_model_effective(void) { return faults; }
unsigned get_vram_address_mask(void) { return faults; }
int get_vram_short_a(void) { return -1; }
int get_vram_short_b(void) { return -1; }
int checkpoint_audio_size(void) { return 20; }
int checkpoint_audio_save(uint8_t *p,unsigned cap) { if(audio_failure || cap<20) return -1; memset(p,0,20); return 20; }
int checkpoint_audio_validate(const uint8_t *p,unsigned n) { return p && n==20; }
int checkpoint_audio_load(const uint8_t *p,unsigned n) { return audio_failure ? -1 : (checkpoint_audio_validate(p,n)?20:-1); }
unsigned checkpoint_pad_size(void) { return 8; }
int checkpoint_pad_save(uint8_t *p,unsigned cap) { if(pad_failure || cap<8) return -1; memset(p,0,8); return 8; }
int checkpoint_pad_validate(const uint8_t *p,unsigned n) { return p && n==8; }
int checkpoint_pad_load(const uint8_t *p,unsigned n) { return pad_failure ? -1 : (checkpoint_pad_validate(p,n)?8:-1); }
unsigned checkpoint_stock_sound_bound(void) { return 24; }
unsigned checkpoint_vdp_context_bound(void) { return 24+bound_extra; }
int checkpoint_plain_md_cart(void) { return plain_cart; }
static unsigned session_checkpoint_stock_state_bound(void);
int state_save(uint8_t *p) { ++save_calls; if(save_failure) return -1; memcpy(p,STATE_VERSION,16); p[16]=work_ram[0]; return (int)session_checkpoint_stock_state_bound(); }
int state_load(uint8_t *p) { ++load_calls; work_ram[0]=p[16]; return load_failure ? -1 : (int)session_checkpoint_stock_state_bound(); }
#include "../scripts/session_checkpoint_runtime.c"

int main(void) {
 blip_t blip={0}; snd.blips[0]=&blip;
 frame_buffer=calloc(640u*480u,4); cart.rom=calloc(0x810000u,1);
 assert(frame_buffer && cart.rom); cart.romsize=0x400000;
 sram.sram=cart.rom+0x800000; sram.on=1; sram.start=0x200000; sram.end=0x20ffff;
 input.system[0]=input.system[1]=SYSTEM_GAMEPAD;
 for(unsigned i=0;i<MAX_DEVICES;i++) input.dev[i]=NO_DEVICE;
 input.dev[0]=DEVICE_PAD3B; input.dev[4]=DEVICE_PAD6B;
 session_checkpoint_runtime_start();
 assert(get_session_checkpoint_support()==1 && !get_session_checkpoint_ready());
 assert(restore_session_checkpoint()==SESSION_CHECKPOINT_EMPTY && !load_calls);
 frame_number=UINT32_MAX; work_ram[0]=17; frame_buffer[0]=23; sram.sram[0]=29;
 m68k.memory_map[0].base=cart.rom+42; zbank_memory_map[0].base=cart.rom+43;
 assert(save_session_checkpoint()==0 && get_session_checkpoint_saved_frame()==UINT32_MAX);
 {
  int saved=save_calls,loaded=load_calls;
  z80_faults=1;
  assert(save_session_checkpoint()==SESSION_CHECKPOINT_UNSAFE && save_calls==saved);
  assert(restore_session_checkpoint()==SESSION_CHECKPOINT_UNSAFE && load_calls==loaded);
  assert(z80_faults && get_session_checkpoint_ready() && work_ram[0]==17);
  z80_faults=0;
 }
 assert(frame_number==UINT32_MAX && get_session_checkpoint_ready());
 /* Refused or incomplete replacement never publishes the spare slot. */
 faults=1; assert(get_session_checkpoint_support()==1 && get_session_checkpoint_ready());
 assert(save_session_checkpoint()==2 && restore_session_checkpoint()==2 && !load_calls); faults=0;
 input.pad[0]=1; assert(save_session_checkpoint()==2 && get_session_checkpoint_support()==1); input.pad[0]=0;
 held_pulse=1; assert(save_session_checkpoint()==2); held_pulse=0;
 int before=save_calls; bound_extra=STATE_SIZE; assert(save_session_checkpoint()==1 && save_calls==before); bound_extra=0;
 save_failure=1; assert(save_session_checkpoint()==4 && get_session_checkpoint_ready()); save_failure=0;
 audio_failure=1; assert(save_session_checkpoint()==4 && get_session_checkpoint_ready()); audio_failure=0;
 pad_failure=1; assert(save_session_checkpoint()==4 && get_session_checkpoint_ready()); pad_failure=0;
 work_ram[0]=1; frame_buffer[0]=2; sram.sram[0]=3; m68k.memory_map[0].base=NULL; zbank_memory_map[0].base=NULL;
 assert(restore_session_checkpoint()==0 && work_ram[0]==17 && frame_buffer[0]==23 && sram.sram[0]==29);
 assert(m68k.memory_map[0].base==cart.rom+42 && zbank_memory_map[0].base==cart.rom+43);
 assert(restore_session_checkpoint()==0 && get_session_checkpoint_ready());
 /* Structural mismatch refuses before even the stock loader is called. */
 before=load_calls; cart.romsize--; assert(restore_session_checkpoint()==6 && load_calls==before); cart.romsize++;
 session_checkpoint_slot *slot=&session_checkpoint_slots[session_checkpoint_current];
 slot->state_after[0]=0; assert(restore_session_checkpoint()==6 && load_calls==before); slot->state_after[0]=0xa5;
 slot->state[0]^=1; assert(restore_session_checkpoint()==6 && load_calls==before); slot->state[0]^=1;
 slot->audio_after[0]=0; assert(restore_session_checkpoint()==6 && load_calls==before); slot->audio_after[0]=0xa5;
 slot->pad_after[0]=0; assert(restore_session_checkpoint()==6 && load_calls==before); slot->pad_after[0]=0xa5;
 snd.blips[1]=&blip; assert(get_session_checkpoint_support()==0 && restore_session_checkpoint()==1); snd.blips[1]=NULL;
 sram.custom=1; assert(get_session_checkpoint_support()==0); sram.custom=0;
 input.dev[1]=DEVICE_PAD3B; assert(get_session_checkpoint_support()==0); input.dev[1]=NO_DEVICE;
 plain_cart=0; assert(get_session_checkpoint_support()==0 && restore_session_checkpoint()==1); plain_cart=1;
 load_failure=1; assert(restore_session_checkpoint()==5 && !get_session_checkpoint_ready()); load_failure=0;
 assert(save_session_checkpoint()==0); audio_failure=1; assert(restore_session_checkpoint()==5 && !get_session_checkpoint_ready()); audio_failure=0;
 assert(save_session_checkpoint()==0); discard_session_checkpoint(); assert(!get_session_checkpoint_ready() && restore_session_checkpoint()==3);
 assert(save_session_checkpoint()==0); session_checkpoint_runtime_start(); assert(!get_session_checkpoint_ready());
 assert(save_session_checkpoint()==0); config.ym3438=1; before=load_calls; assert(restore_session_checkpoint()==1 && load_calls==before);
 free(frame_buffer);free(cart.rom);
 return 0;
}
