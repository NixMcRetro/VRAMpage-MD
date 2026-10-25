/* Scratch-only checkpoint proof hooks. Never carry into product builds. */
#define STATE_PROOF_GUARD 64u
static struct {
    uint8_t pre[STATE_PROOF_GUARD];
    uint8_t payload[STATE_SIZE];
    uint8_t post[STATE_PROOF_GUARD];
} state_proof_storage;
static int state_proof_length;

int EMSCRIPTEN_KEEPALIVE state_proof_save(void) {
    memset(&state_proof_storage, 0xA5, sizeof(state_proof_storage));
    state_proof_length = state_save(state_proof_storage.payload);
    return state_proof_length;
}
int EMSCRIPTEN_KEEPALIVE state_proof_load(void) {
    if (state_proof_length <= 0 || state_proof_length > STATE_SIZE) return -1;
    return state_load(state_proof_storage.payload);
}
uint8 EMSCRIPTEN_KEEPALIVE state_proof_guard_ok(void) {
    for (unsigned i = 0; i < STATE_PROOF_GUARD; ++i) {
        if (state_proof_storage.pre[i] != 0xA5 || state_proof_storage.post[i] != 0xA5) return 0;
    }
    if (state_proof_length < 0 || state_proof_length > STATE_SIZE) return 0;
    for (unsigned i = (unsigned)state_proof_length; i < STATE_SIZE; ++i) {
        if (state_proof_storage.payload[i] != 0xA5) return 0;
    }
    return 1;
}
uint8 *EMSCRIPTEN_KEEPALIVE state_proof_payload_ref(void) { return state_proof_storage.payload; }
int EMSCRIPTEN_KEEPALIVE state_proof_reject_empty(void) {
    int saved = state_proof_length;
    state_proof_length = 0;
    int result = state_proof_load();
    state_proof_length = saved;
    return result == -1;
}
