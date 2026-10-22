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
static uint8 original[0x10000];

static uint16_t expected_map(uint16_t address, unsigned int mask) {
    for (unsigned int line = 0; line < 8; line++) {
        if (mask & (1u << line)) {
            address &= (uint16_t)~(1u << (line + 2));
            address &= (uint16_t)~(1u << (line < 2 ? line : line + 8));
        }
    }
    return address;
}

int main(void) {
    /* Exhaust all logical addresses for every possible physical AD mask. */
    for (unsigned int mask = 0; mask <= 255; mask++) {
        CHECK(set_vram_address_mask((int)mask) == 0);
        CHECK(get_vram_address_mask() == mask);
        CHECK(get_vram_short_a() == -1 && get_vram_short_b() == -1);
        for (unsigned int address = 0; address < 0x10000; address++) {
            uint16_t mapped = bend_map((uint16_t)address);
            CHECK(mapped == expected_map((uint16_t)address, mask));
            CHECK((mapped | address) == address);
            CHECK(bend_map(mapped) == mapped);
        }
    }
    CHECK(bend_map(0xffff) == 0); /* All eight nets low clear all 16 bits. */
    CHECK(set_vram_address_mask(-1) == 1);
    CHECK(set_vram_address_mask(256) == 1);
    CHECK(get_vram_address_mask() == 255);
    set_vram_short(0, 1);
    CHECK(get_vram_address_mask() == 0);
    CHECK(set_vram_address_mask(256) == 1);
    CHECK(get_vram_short_a() == 0 && get_vram_short_b() == 1);

    /* Existing low-dominant pair behavior must remain distinct from stuck-low. */
    CHECK(bend_map(0xffff) == 0xffff);
    vram[0]=0x22;
    vram[4]=0x11;
    vram[1]=0x33;
    bend_before_frame();
    CHECK(vram[4]==0x22);
    CHECK(bg_list_index==0x800);
    CHECK(get_vram_changed_reads()>=1);
    vram[4]=0xCC;
    bend_after_frame();
    CHECK(vram[0]==0xCC);
    CHECK(vram[4]==0x11);
    CHECK(get_vram_changed_writes()>=1);
    set_vram_short(-1,-1);
    bend_before_frame();
    CHECK(get_vram_short_a()==-1);
    CHECK(vram[4]==0x11);

    /* Projected reads alone never persistently overwrite physical VRAM. */
    for (unsigned int i=0;i<0x10000;i++) original[i]=(uint8)(i ^ (i >> 8));
    const int masks[] = {1, 2, 4, 8, 16, 32, 64, 128, 0x55, 0xaa, 255};
    for (unsigned int m=0;m<sizeof(masks)/sizeof(masks[0]);m++) {
        memcpy(vram, original, sizeof(original));
        CHECK(set_vram_address_mask(masks[m]) == 0);
        bend_before_frame();
        for (unsigned int i=0;i<0x10000;i++)
            CHECK(vram[i] == original[expected_map((uint16_t)i,(unsigned int)masks[m])]);
        CHECK(bg_list_index == 0x800 && bg_name_dirty[0] == 0xff && bg_name_dirty[0x7ff] == 0xff);
        bend_after_frame();
        CHECK(memcmp(vram, original, sizeof(original)) == 0);
        CHECK(get_vram_changed_writes() == 0);
    }

    /* Changed logical aliases reconcile in ascending address order. */
    memcpy(vram, original, sizeof(original));
    CHECK(set_vram_address_mask(1) == 0); /* AD0 clears row A2 and column A0. */
    bend_before_frame();
    vram[4] = 0xcc;
    vram[5] = 0xdd;
    bend_after_frame();
    CHECK(vram[0] == 0xdd); /* Last changed logical alias wins. */
    CHECK(vram[4] == original[4] && vram[5] == original[5]);
    CHECK(get_vram_changed_writes() == 2);
    CHECK(set_vram_address_mask(0) == 0);
    memset(bg_name_dirty,0,sizeof(bg_name_dirty));bg_list_index=0;
    bend_before_frame();
    CHECK(vram[0] == 0xdd); /* Reconnect never undoes projected writes. */
    CHECK(bg_list_index == 0x800 && bg_name_dirty[0] == 0xff);
    CHECK(get_vram_changed_reads() == 0 && get_vram_changed_writes() == 0);
    bg_list_index=0;bend_before_frame();CHECK(bg_list_index == 0);

    CHECK(set_vram_address_mask(0x81) == 0);
    bend_changed_reads=7;bend_changed_writes=9;
    bend_reset();
    CHECK(get_vram_address_mask() == 0);
    CHECK(get_vram_short_a() == -1 && get_vram_short_b() == -1);
    CHECK(get_vram_changed_reads() == 0 && get_vram_changed_writes() == 0);
    CHECK(bend_restore_cache == 1);
    bend_before_frame();CHECK(bend_restore_cache == 0);
    puts("C fault-engine smoke test passed (all 256 masks x 65536 addresses)");
    return 0;
}
