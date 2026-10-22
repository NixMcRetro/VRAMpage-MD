/* Original synthetic test fixture. No emulator or cartridge code/data. */
window.Module = async () => {
  const memory = new ArrayBuffer(8 * 1024 * 1024);
  const bytes = new Uint8Array(memory);
  const floats = new Float32Array(memory);
  const input = 2 * 1024 * 1024;
  const logic = {
    active: false, config: {kind: 0, access: 0, a: 0, b: 0},
    reads: 0, writes: 0, frame: 0, activationFrame: 0, cpuFlags: 0,
    setterCalls: [], storedWrites: 0, recoveries: [], pulseState: 0, budget: 0, writesPerTick: 1, addressMask:0,
  };
  window.mockCore = {starts: 0, ticks: 0, lastStartTick: 0, short: [-1, -1], vramAddressMask:0, vramMaskCalls:[], inputs: [], logic};

  function setLogicFault(kind, access, a, b) {
    logic.setterCalls.push([kind, access, a, b]);
    if (kind === 0) {
      if(window.mockCore.rejectLogicClear)return 5;
      if (logic.pulseState === 1) logic.pulseState = 4;
      logic.addressMask=0;
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
    logic.pulseState = 0; logic.budget = 0;logic.addressMask=0;
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
    logic.storedWrites = 0;logic.addressMask=0;
    logic.pulseState = 0; logic.budget = 0;
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
      resetLogic();window.mockCore.short=[-1,-1];window.mockCore.vramAddressMask=0;
      window.mockCore.lastStartTick = window.mockCore.ticks;
    },
    _tick() {
      window.mockCore.ticks++;
      logic.frame++;
      if (!logic.active) return;
      if (logic.config.access === 1 || logic.config.access === 3) logic.reads++;
      if (logic.config.access === 2 || logic.config.access === 3) {
        for (let i=0; i<logic.writesPerTick && logic.active; i++) {
          logic.writes++; logic.storedWrites++;
          if (logic.pulseState === 1 && --logic.budget === 0) {
            logic.active = false; logic.pulseState = 2;
          }
        }
      }
      if (logic.pulseState === 1) {logic.active=false;logic.pulseState=3;}
    },
    _sound: () => 0,
    _wasm_input_update() {
      window.mockCore.inputs = Array.from(new Float32Array(memory, input, 32));
    },
    _set_vram_short(a, b) { window.mockCore.short = [a, b];window.mockCore.vramAddressMask=0; },
    _set_vram_address_mask(mask) {
      window.mockCore.vramMaskCalls.push(mask);
      if(window.mockCore.rejectVramMask || !Number.isInteger(mask)||mask<0||mask>255)return 1;
      window.mockCore.vramAddressMask=mask;window.mockCore.short=[-1,-1];return 0;
    },
    _get_vram_address_mask:()=>window.mockCore.vramAddressMask,
    _get_vram_changed_reads: () => 0,
    _get_vram_changed_writes: () => 0,
  };
  if (!window.__legacyLogicCore) {
    // Expose the same setter on the instrumentation object so tests can
    // verify the core-level guard independently of UI validation.
    window.mockCore._set_logic_fault = setLogicFault;
    Object.assign(core, {
      _recover_logic_cpu(mode) {
        if (![1,2].includes(mode)) return 5;
        logic.recoveries.push(mode);
        logic.active = false; logic.cpuFlags = 0;
        return 0;
      },
      _set_logic_address_mask(mask,access) {
        if (!Number.isInteger(mask)||mask<0||mask>0x7fff||![1,2,3].includes(access)) return 5;
        setLogicFault(0,0,0,0);logic.addressMask=mask;
        if(mask) {logic.active=true;logic.config={kind:3,access,a:0,b:0};logic.activationFrame=logic.frame;}
        return 0;
      },
      _get_logic_address_mask:()=>logic.addressMask,
      _arm_logic_write_pulse(kind,a,b,limit) {
        if (!Number.isInteger(limit) || limit<1 || limit>1024) return 5;
        const status=setLogicFault(kind,2,a,b);
        if (status!==0) return status;
        logic.pulseState=1;logic.budget=limit;return 0;
      },
      _get_logic_pulse_state:()=>logic.pulseState,
      _set_logic_fault: setLogicFault,
      _get_logic_reads: () => logic.reads,
      _get_logic_writes: () => logic.writes,
      _get_logic_frame: () => logic.frame,
      _get_logic_activation_frame: () => logic.activationFrame,
      _get_logic_cpu_flags: () => logic.cpuFlags,
    });
  }
  if (window.__legacyRecoveryCore) delete core._recover_logic_cpu;
  if (window.__legacyWritePulseCore) {
    delete core._arm_logic_write_pulse;delete core._get_logic_pulse_state;
  }
  if (window.__legacyChipCore) {delete core._set_logic_address_mask;delete core._get_logic_address_mask;}
  if(window.__legacyVramChipCore) {delete core._set_vram_address_mask;delete core._get_vram_address_mask;}
  return core;
};
