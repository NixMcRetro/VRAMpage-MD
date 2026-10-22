/* Original synthetic test fixture. No emulator or cartridge code/data. */
window.Module = async () => {
  const memory = new ArrayBuffer(8 * 1024 * 1024);
  const bytes = new Uint8Array(memory);
  const floats = new Float32Array(memory);
  const input = 2 * 1024 * 1024;
  window.mockCore = {starts: 0, ticks: 0, short: [-1, -1], inputs: []};
  // Native 640-pixel pitch, coloured even rows, missing odd rows.
  for (let y = 0; y < 224; y++) {
    for (let x = 0; x < 320; x++) {
      const i = (y * 640 + x) * 4;
      bytes[i] = y % 2 ? 0 : 64 + x % 128;
      bytes[i + 1] = y % 2 ? 0 : 64 + y % 128;
      bytes[i + 2] = y % 2 ? 0 : 192;
      bytes[i + 3] = 255;
    }
  }
  return {
    HEAPU8: bytes, HEAPF32: floats,
    _init() {},
    _get_rom_buffer_ref: () => 3 * 1024 * 1024,
    _get_frame_buffer_ref: () => 0,
    _get_input_buffer_ref: () => input,
    _get_web_audio_l_ref: () => input + 1024,
    _get_web_audio_r_ref: () => input + 16384,
    _start() { window.mockCore.starts++; },
    _tick() { window.mockCore.ticks++; },
    _sound: () => 0,
    _wasm_input_update() {
      window.mockCore.inputs = Array.from(new Float32Array(memory, input, 32));
    },
    _set_vram_short(a, b) { window.mockCore.short = [a, b]; },
    _get_vram_changed_reads: () => 0,
    _get_vram_changed_writes: () => 0,
  };
};
