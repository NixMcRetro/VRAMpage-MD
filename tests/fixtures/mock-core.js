/* Original synthetic test fixture. No emulator or cartridge code/data. */
window.Module = async () => {
  const memory = new ArrayBuffer(8 * 1024 * 1024);
  const bytes = new Uint8Array(memory);
  const floats = new Float32Array(memory);
  const input = 2 * 1024 * 1024;
  const logic = {
    active: false, config: {kind: 0, access: 0, a: 0, b: 0},
    reads: 0, writes: 0, frame: 0, activationFrame: 0, cpuFlags: 0,
    setterCalls: [], storedWrites: 0,
  };
  window.mockCore = {starts: 0, ticks: 0, lastStartTick: 0, short: [-1, -1], inputs: [], logic};

  function setLogicFault(kind, access, a, b) {
    logic.setterCalls.push([kind, access, a, b]);
    if (kind === 0) {
      logic.active = false;
      logic.config = {kind: 0, access: 0, a: 0, b: 0};
      logic.reads = 0;
      logic.writes = 0;
      logic.activationFrame = 0;
      return 0;
    }
    const lineLimit = kind === 1 ? 15 : kind === 2 ? 16 : 0;
    if (!lineLimit || ![1, 2, 3].includes(access) || a < 0 || b < 0 ||
        a >= lineLimit || b >= lineLimit || a === b)
      return 5;
    if (kind === 2 && Math.floor(a / 8) !== Math.floor(b / 8)) return 6;
    logic.active = true;
    logic.config = {kind, access, a, b};
    logic.reads = 0;
    logic.writes = 0;
    logic.activationFrame = logic.frame;
    return 0;
  }

  function resetLogic() {
    logic.active = false;
    logic.config = {kind: 0, access: 0, a: 0, b: 0};
    logic.reads = 0;
    logic.writes = 0;
    logic.frame = 0;
    logic.activationFrame = 0;
    logic.cpuFlags = 0;
    logic.storedWrites = 0;
  }
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
  const core = {
    HEAPU8: bytes, HEAPF32: floats,
    _init() {},
    _get_rom_buffer_ref: () => 3 * 1024 * 1024,
    _get_frame_buffer_ref: () => 0,
    _get_input_buffer_ref: () => input,
    _get_web_audio_l_ref: () => input + 1024,
    _get_web_audio_r_ref: () => input + 16384,
    _start() {
      window.mockCore.starts++;
      resetLogic();
      window.mockCore.lastStartTick = window.mockCore.ticks;
    },
    _tick() {
      window.mockCore.ticks++;
      logic.frame++;
      if (!logic.active) return;
      if (logic.config.access === 1 || logic.config.access === 3) logic.reads++;
      if (logic.config.access === 2 || logic.config.access === 3) {
        logic.writes++;
        logic.storedWrites++;
      }
    },
    _sound: () => 0,
    _wasm_input_update() {
      window.mockCore.inputs = Array.from(new Float32Array(memory, input, 32));
    },
    _set_vram_short(a, b) { window.mockCore.short = [a, b]; },
    _get_vram_changed_reads: () => 0,
    _get_vram_changed_writes: () => 0,
  };
  if (!window.__legacyLogicCore) {
    // Expose the same setter on the instrumentation object so tests can
    // verify the core-level guard independently of UI validation.
    window.mockCore._set_logic_fault = setLogicFault;
    Object.assign(core, {
      _set_logic_fault: setLogicFault,
      _get_logic_reads: () => logic.reads,
      _get_logic_writes: () => logic.writes,
      _get_logic_frame: () => logic.frame,
      _get_logic_activation_frame: () => logic.activationFrame,
      _get_logic_cpu_flags: () => logic.cpuFlags,
    });
  }
  return core;
};
