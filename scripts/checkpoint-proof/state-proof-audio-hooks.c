/* Scratch-only omitted-audio-state proof hooks. */
extern unsigned system_audio_proof_size(void);
extern int system_audio_proof_save(unsigned char*, unsigned);
extern int system_audio_proof_load(const unsigned char*, unsigned);
int EMSCRIPTEN_KEEPALIVE state_proof_set_filter(int mode) {
    if(mode<0 || mode>3) return -1;
    config.filter=(uint8)mode;
    audio_set_equalizer();
    return 0;
}
#define STATE_PROOF_AUDIO_GUARD 64u
static struct {
    uint8_t pre[STATE_PROOF_AUDIO_GUARD];
    uint8_t payload[0x80000];
    uint8_t post[STATE_PROOF_AUDIO_GUARD];
} state_proof_audio_storage;
static int state_proof_audio_length;
int EMSCRIPTEN_KEEPALIVE state_proof_audio_save(void) {
    memset(&state_proof_audio_storage,0xA5,sizeof(state_proof_audio_storage));
    state_proof_audio_length=(int)system_audio_proof_size();
    if(state_proof_audio_length<=0 || state_proof_audio_length>(int)sizeof(state_proof_audio_storage.payload)) return -1;
    return system_audio_proof_save(state_proof_audio_storage.payload,(unsigned)sizeof(state_proof_audio_storage.payload));
}
int EMSCRIPTEN_KEEPALIVE state_proof_audio_load(void) {
    if(state_proof_audio_length<=0 || state_proof_audio_length>(int)sizeof(state_proof_audio_storage.payload)) return -1;
    return system_audio_proof_load(state_proof_audio_storage.payload,(unsigned)state_proof_audio_length);
}
uint8 EMSCRIPTEN_KEEPALIVE state_proof_audio_guard_ok(void) {
    for(unsigned i=0;i<STATE_PROOF_AUDIO_GUARD;i++)
        if(state_proof_audio_storage.pre[i]!=0xA5 || state_proof_audio_storage.post[i]!=0xA5) return 0;
    for(unsigned i=(unsigned)state_proof_audio_length;i<sizeof(state_proof_audio_storage.payload);i++)
        if(state_proof_audio_storage.payload[i]!=0xA5) return 0;
    return state_proof_audio_length>0 && state_proof_audio_length<=(int)sizeof(state_proof_audio_storage.payload);
}
extern int system_audio_proof_reject_profile(const unsigned char*, unsigned);
extern uintptr_t system_audio_proof_pointer_fingerprint(void);
int EMSCRIPTEN_KEEPALIVE state_proof_audio_small_capacity_refused(void) {
    uint8_t probe[64];
    memset(probe, 0xA5, sizeof(probe));
    int result = system_audio_proof_save(probe, 0);
    if (result != -1) return 0;
    for (unsigned i = 0; i < sizeof(probe); ++i) if (probe[i] != 0xA5) return 0;
    return 1;
}
int EMSCRIPTEN_KEEPALIVE state_proof_audio_profile_refused(void) {
    return state_proof_audio_length > 0 && system_audio_proof_reject_profile(
        state_proof_audio_storage.payload, (unsigned)state_proof_audio_length);
}
uintptr_t EMSCRIPTEN_KEEPALIVE state_proof_audio_pointer_fingerprint(void) {
    return system_audio_proof_pointer_fingerprint();
}
