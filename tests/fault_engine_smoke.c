#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
/* minimal stubs for standalone C smoke-test */
#define EMSCRIPTEN_KEEPALIVE
#define uint8 uint8_t
#define uint16 uint16_t
uint8 vram[0x10000];
uint8 bg_name_dirty[0x800];
uint16 bg_name_list[0x800];
uint16 bg_list_index;
#include "../scripts/vram_fault_patch.c"

#define CHECK(x) do { if(!(x)) {fprintf(stderr,"failed line %d: %s\n",__LINE__,#x);exit(1);} } while(0)
int main(void) {
    vram[0]=0x22;
    vram[4]=0x11;
    vram[1]=0x33;
    set_vram_short(0,1);
    CHECK(get_vram_short_a()==0);
    CHECK(get_vram_short_b()==1);
    bend_before_frame();
    CHECK(vram[4]==0x22); /* row A2/A3 & col A0/A1 are low-dominant */
    CHECK(bg_list_index==0x800);
    CHECK(get_vram_changed_reads()>=1);
    /* Simulate a logical VDP write during the faulted frame. */
    vram[4]=0xCC;
    bend_after_frame();
    CHECK(vram[0]==0xCC); /* mapped to physical address zero */
    CHECK(vram[4]==0x11); /* original physical byte preserved */
    CHECK(get_vram_changed_writes()>=1);
    set_vram_short(-1,-1);
    bend_before_frame();
    CHECK(get_vram_short_a()==-1);
    CHECK(vram[4]==0x11);
    puts("C fault-engine smoke test passed");
    return 0;
}