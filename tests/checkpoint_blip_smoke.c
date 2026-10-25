/* Exercise the actual proof-only Blip snapshot helpers with native sanitizers. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "blip_buf.h"

extern uintptr_t blip_proof_pointer_fingerprint(const blip_t *);

int main(void)
{
    blip_t *buffer=blip_new(4410);
    assert(buffer);
    blip_set_rates(buffer,1000000,44100);
    blip_add_delta(buffer,3,2000,-1000);
    blip_end_frame(buffer,1000);
    int count=blip_samples_avail(buffer);
    assert(count>0 && count<128);
    unsigned size=blip_proof_size(buffer);
    unsigned char *storage=malloc((size_t)size+32);
    assert(storage && size>0);
    memset(storage,0xA5,(size_t)size+32);
    assert(blip_proof_save(NULL,storage+16,size)==-1);
    assert(blip_proof_save(buffer,NULL,size)==-1);
    assert(blip_proof_save(buffer,storage+16,size-1)==-1);
    for (unsigned i=0;i<size+32;++i) assert(storage[i]==0xA5);
    assert(blip_proof_save(buffer,storage+16,size)==(int)size);
    for (unsigned i=0;i<16;++i) assert(storage[i]==0xA5 && storage[size+16+i]==0xA5);
    uintptr_t pointers=blip_proof_pointer_fingerprint(buffer);
    short expected[256]={0},actual[256]={0};
    assert(blip_read_samples(buffer,expected,count)==count);
    blip_add_delta(buffer,2,-500,200);
    blip_end_frame(buffer,1000);
    assert(blip_proof_load(buffer,storage+16,size-1)==-1);
    assert(blip_proof_load(NULL,storage+16,size)==-1);
    assert(blip_proof_load(buffer,NULL,size)==-1);
    assert(blip_proof_load(buffer,storage+16,size)==(int)size);
    assert(blip_proof_pointer_fingerprint(buffer)==pointers);
    assert(blip_samples_avail(buffer)==count);
    assert(blip_read_samples(buffer,actual,count)==count);
    assert(memcmp(expected,actual,(size_t)count*2*sizeof(short))==0);
    free(storage);
    blip_delete(buffer);
    blip_t *mixed[3];
    for (int i=0;i<3;++i) {
        mixed[i]=blip_new(4410);assert(mixed[i]);
        blip_set_rates(mixed[i],1000000,44100);
        blip_add_delta(mixed[i],3,1000*(i+1),-500*(i+1));
        blip_end_frame(mixed[i],1000);
    }
    assert(blip_mix_samples(mixed[0],mixed[1],mixed[2],actual,count)==count);
    for (int i=0;i<3;++i) blip_delete(mixed[i]);
    puts("Private Blip proof: capacity, refusal, guards, pointers and PCM replay passed");
    return 0;
}
