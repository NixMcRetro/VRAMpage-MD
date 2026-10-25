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
  const psg = {configured:false,bridgeA:-1,bridgeB:-1,dataMask:0,supported:true,inputWrites:'0',changedWrites:'0',calls:[],maskCalls:[]};
  const fm = {configured:false,bridgeA:-1,bridgeB:-1,dataMask:0,supported:true,inputWrites:'0',changedWrites:'0',calls:[],maskCalls:[]};
  const vramModel = {modelId:1,mask:0,bridgeA:-1,bridgeB:-1,supportedModelsMask:7,calls:[]};
  window.mockCore = {starts: 0, ticks: 0, lastStartTick: 0, short: [-1, -1], vramAddressMask:0,
    vramMaskCalls:[], inputs: [], logic, psg, fm, vramModel};

  function setLogicFault(kind, access, a, b) {
    logic.setterCalls.push([kind, access, a, b]);
    if (kind === 0) {
      if(window.mockCore.throwLogicClearAfter) {
        logic.pulseState = 0;logic.budget=0;logic.addressMask=0;logic.active=false;
        logic.config={kind:0,access:0,a:0,b:0};logic.reads=0;logic.writes=0;logic.activationFrame=0;
        throw new Error('synthetic RAM clear trap after mutation');
      }
      if(window.mockCore.rejectLogicClear)return 5;
      if (logic.pulseState === 1 && !window.mockCore.leavePulseArmedAfterClear) logic.pulseState = 4;
      logic.addressMask=0;
      logic.active = false;
      logic.config = {kind: 0, access: 0, a: 0, b: 0};
      logic.reads = 0;
      logic.writes = 0;
      logic.activationFrame = 0;
      return 0;
    }
    if (window.mockCore.throwLogicFaultAfter) {
      logic.active=true;logic.config={kind,access,a,b};logic.reads=0;logic.writes=0;
      logic.activationFrame=logic.frame;
      throw new Error('synthetic RAM setter trap after mutation');
    }
    if (window.mockCore.rejectLogicFault) return 5;
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
    _get_rom_buffer_ref: () => window.mockCore.rejectRomAllocation ? 0 : 3 * 1024 * 1024,
    _get_frame_buffer_ref: () => 0,
    _get_input_buffer_ref: () => input,
    _get_web_audio_l_ref: () => input + 1024,
    _get_web_audio_r_ref: () => input + 16384,
    _start() {
      window.mockCore.starts++;
      resetLogic();window.mockCore.short=[-1,-1];window.mockCore.vramAddressMask=0;
      Object.assign(vramModel,{modelId:1,mask:0,bridgeA:-1,bridgeB:-1});
      for (const state of [psg,fm]) Object.assign(state,{configured:false,bridgeA:-1,bridgeB:-1,dataMask:0,inputWrites:'0',changedWrites:'0'});
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
  if (window.__circuitConfigCore) {
    Object.assign(core, {
      _set_vram_fault_model(modelId,mask,a,b) {
        vramModel.calls.push([modelId,mask,a,b]);
        if (window.mockCore.rejectVramModel) return 9;
        if (window.mockCore.throwVramModel) throw new Error('synthetic VRAM selector trap');
        if (![1,2].includes(modelId) || !(vramModel.supportedModelsMask & (1<<modelId)) ||
            !Number.isInteger(mask) || mask<0 || mask>255 ||
            (mask && (a!==-1 || b!==-1)) ||
            !((a===-1&&b===-1)||(a>=0&&a<=7&&b>=0&&b<=7&&a!==b))) return 2;
        if (window.mockCore.leaveVramModelConfiguredAfterSet) return 0;
        Object.assign(vramModel,{modelId,mask,bridgeA:a,bridgeB:b});
        window.mockCore.vramAddressMask=mask;
        window.mockCore.short=a<0?[-1,-1]:[a,b];
        if (window.mockCore.throwVramModelAfter) throw new Error('synthetic VRAM selector trap after mutation');
        if (window.mockCore.rejectVramModelAfterMutation) return 9;
        return 0;
      },
      _get_vram_fault_model_state:()=>window.mockCore.nullVramState?null:(window.mockCore.vramStateOverride||{modelId:vramModel.modelId,modelVersion:vramModel.modelId===2
        ?'logical-byte-transaction-v1':'frame-projection-v1',mask:vramModel.mask,
        bridgeA:vramModel.bridgeA,bridgeB:vramModel.bridgeB,supportedModelsMask:vramModel.supportedModelsMask,
        effective:!!(vramModel.mask||vramModel.bridgeA>=0),reason:vramModel.mask||vramModel.bridgeA>=0?'active':'no-fault',
        lastFrameCounts:{logicalByteReads:0,logicalByteWrites:0,redirectedByteReads:0,
          redirectedByteWrites:0,changedPhysicalByteWrites:0}}),
      _get_vram_supported_model_mask:()=>{
        if(window.mockCore.throwVramSupport) throw new Error('synthetic VRAM support metadata trap');
        return vramModel.supportedModelsMask;
      }
    });
  }
  if (window.__circuitConfigCore && !window.__legacyPsgDataCore) {
    Object.assign(core, {
      _set_psg_data_bridge(enabled,a,b) {
        psg.calls.push([enabled,a,b]);
        if (window.mockCore.throwPsgBridge) {
          window.mockCore.throwPsgState=true;
          throw new Error('synthetic PSG setter trap');
        }
        if (window.mockCore.rejectPsgBridge) return 1;
        if (enabled && (!psg.supported || a<0 || b<0 || a>7 || b>7 || a===b)) return 2;
        Object.assign(psg,{configured:!!enabled,bridgeA:enabled?a:-1,bridgeB:enabled?b:-1,dataMask:0,
          inputWrites:'0',changedWrites:'0'});
        return 0;
      },
      _get_psg_data_bridge_state:()=>{
        if(window.mockCore.throwPsgState) throw new Error('synthetic PSG state trap');
        return {...psg,modelVersion:'psg-data-bridge-test-v2'};
      }
    });
    if (!window.__legacyPsgMaskCore) core._set_psg_data_mask=mask=>{
      psg.maskCalls.push(mask);
      if (!Number.isInteger(mask)||mask<0||mask>255) return 1;
      if (mask&&!psg.supported) return 2;
      Object.assign(psg,{configured:!!mask,bridgeA:-1,bridgeB:-1,dataMask:mask,inputWrites:'0',changedWrites:'0'});
      if (window.mockCore.rejectPsgMaskAfterMutation) return 1;
      return 0;
    };
  }
  if (window.__circuitConfigCore && !window.__legacyFmDataCore) {
    Object.assign(core, {
      _set_fm_data_bridge(enabled,a,b) {
        fm.calls.push([enabled,a,b]);
        if (window.mockCore.rejectFmBridge) return 1;
        if (enabled && (!fm.supported || a<0 || b<0 || a>7 || b>7 || a===b)) return 2;
        Object.assign(fm,{configured:!!enabled,bridgeA:enabled?a:-1,bridgeB:enabled?b:-1,dataMask:0,
          inputWrites:'0',changedWrites:'0'});
        return 0;
      },
      _get_fm_data_bridge_state:()=>{
        if(window.mockCore.throwFmState) throw new Error('synthetic FM state trap');
        return {...fm,modelVersion:'fm-data-bridge-test-v2'};
      }
    });
    if (!window.__legacyFmMaskCore) core._set_fm_data_mask=mask=>{
      fm.maskCalls.push(mask);
      if (!Number.isInteger(mask)||mask<0||mask>255) return 1;
      if (mask&&!fm.supported) return 2;
      Object.assign(fm,{configured:!!mask,bridgeA:-1,bridgeB:-1,dataMask:mask,inputWrites:'0',changedWrites:'0'});
      return 0;
    };
  }
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
        if (window.mockCore.rejectPulseArm) return 5;
        const status=setLogicFault(kind,2,a,b);
        if (status!==0) return status;
        logic.pulseState=1;logic.budget=limit;
        if (window.mockCore.throwPulseArmAfter) throw new Error('synthetic pulse arm trap after mutation');
        return 0;
      },
      _get_logic_pulse_state:()=>logic.pulseState,
      _set_logic_fault: setLogicFault,
      _get_logic_reads: () => logic.reads,
      _get_logic_writes: () => logic.writes,
      _get_logic_frame: () => {
        if(window.mockCore.throwFrameOnce) {window.mockCore.throwFrameOnce=false;throw new Error('synthetic frame telemetry trap');}
        return logic.frame;
      },
      _get_logic_activation_frame: () => logic.activationFrame,
      _get_logic_cpu_flags: () => {
        if (window.mockCore.throwCpuFlags) throw new Error('synthetic CPU flag telemetry trap');
        if (Object.prototype.hasOwnProperty.call(window.mockCore,'invalidCpuFlags')) return window.mockCore.invalidCpuFlags;
        return window.mockCore.cpuFlagsByFrame?.[logic.frame] ?? logic.cpuFlags;
      },
    });
  }
  if (window.__legacyRecoveryCore) delete core._recover_logic_cpu;
  if (window.__legacyWritePulseCore) {
    delete core._arm_logic_write_pulse;delete core._get_logic_pulse_state;
  }
  if (window.__legacyChipCore) {delete core._set_logic_address_mask;delete core._get_logic_address_mask;}
  if(window.__legacyVramChipCore) {delete core._set_vram_address_mask;delete core._get_vram_address_mask;}
  window.mockCore.core=core;
  return core;
};
