'use strict';
// Standalone (no bundler) frontend for wasm-genplus with a custom C fault API.
// No third-party JS, fonts, CDN, telemetry, or ROM downloads.
(() => {
  const $ = id => document.getElementById(id);
  // WASM stores a 320x224 Sonic picture inside a 640x480 framebuffer.
  // Use native pixels with no scanline or smoothing effects.
  const SCREEN_WIDTH = 640, SCREEN_HEIGHT = 480;
  const GAME_WIDTH = 320, GAME_HEIGHT = 224;
  const NTSC_FPS = 59.92274;
  const FRAME_MS = 1000 / NTSC_FPS;
  const AUDIO_RATE = 44100;
  const PRESETS = [[0,1], [0,2], [1,3], [2,4], [3,5], [4,6], [5,7], [6,7]];
  const QUICK_RAM_PAIRS = Array.from({length:5},(_,i)=>Array.from({length:4-i},(_,j)=>[i+10,i+11+j])).flat();
  const SHORTCUT_PAIRS = [...PRESETS,[0,7]];
  const KEYBOARD_TARGETS = ['VRAM','WRAM','FM','PSG'];
  const canvas = $('screen');
  const displayViewport = $('displayViewport');
  const ctx = canvas.getContext('2d', {alpha: false});
  ctx.imageSmoothingEnabled = false;
  const imageData = ctx.createImageData(GAME_WIDTH, GAME_HEIGHT);
  const frameAdapter = window.VRAMpageFrame;
  if (!frameAdapter) throw new Error("Missing framebuffer.js: display adapter could not load");
  let previousVideoStatus = "";
  const pressed = new Set();
  const pinButtons = [];
  const psgPinButtons = [], fmPinButtons = [];
  let ramSelectedPin=null, psgSelectedPin=null, fmSelectedPin=null;
  let keyboardTarget='VRAM', keyboardHeld=null, ownedAddressHold=null, keyboardMutation=false;
  const logEl = $('experimentLog');
  let emulator = null, started = false, paused = false;
  let loadedName = '', latched = null, momentary = null, momentaryRestorePair = null, momentaryRestoreMask=0, selectedPin = null;
  let audioCtx = null, audioOn = false, nextAudioTime = 0;
  const activeAudioSources = new Set();
  let romBytes = null, frameView = null, inputView = null, leftAudio = null, rightAudio = null;
  let lastFrame = 0, accumulated = 0, frames = 0, measuredAt = 0;
  let focusReleased = false;
  let lastContact = '';
  let vramAddressMask=0, vramAddressLineChanges=[];
  let vramModelId=1, vramModelTransitions=[];
  let lastVramSelectorStatus=0;
  let vramModelStatusMessage='';
  let possibleVramResidue = false;
  let displayRefreshQueued = false;
  let logicApiAvailable = false, logicActive = false, logicStatsRetained = false;
  let logicStatusMessage = 'Checking core support…';
  let lastLogicExperiment = null;
  let cpuInterventions = [];
  let cpuRecoveryArmed = false, cpuRecoveryHaltFrames = [];
  let lastCpuRecoveryAttempt = null;
  let faultDisconnectActions = [];
  let faultPulses = [], pendingPulse = null;
  let activeRamConfiguration = null, stagedCircuitConfiguration = null;
  let circuitConfigLoadGeneration=0, circuitConfigLoading=false;
  let logicAddressMask = 0, addressLineChanges = [];
  let logicResetState = 'No cartridge loaded';
  let romLoadGeneration = 0;
  let romIdentity = null;
  const CORE_PIN = '6090aff9e9b2f578cd28882bd4571d2e35b1d674';
  const APPLICATION_VERSION = '0.4.1';
  let buildInfo = {status:'unavailable',applicationVersion:APPLICATION_VERSION,sourceCommit:null};
  loadBuildInfo().then(info=>{buildInfo=info;});

  async function loadBuildInfo() {
    const unavailable = {status:'unavailable',applicationVersion:APPLICATION_VERSION,sourceCommit:null};
    let timer;
    try {
      const controller = new AbortController();
      const request = fetch('./build-info.json', {
        signal:controller.signal,cache:'no-store',credentials:'omit'
      }).then(async response => {
        if (!response.ok) return unavailable;
        const info = await response.json();
        if (!info || typeof info!=='object' || Array.isArray(info) ||
            info.application!=='VRAMpage MD' || info.application_version!==APPLICATION_VERSION ||
            info.package_format!==1 || typeof info.source_commit!=='string' ||
            !/^[a-f0-9]{40}$/.test(info.source_commit)) return unavailable;
        // Copy only the public, validated identity fields into experiment records.
        return {status:'available',applicationVersion:APPLICATION_VERSION,sourceCommit:info.source_commit};
      });
      const timeout = new Promise(resolve => {
        timer=setTimeout(()=>{resolve(unavailable);controller.abort();},1500);
      });
      return await Promise.race([request,timeout]);
    } catch (_) {
      return unavailable;
    } finally {
      clearTimeout(timer);
    }
  }

  const LOGIC_API = ['_set_logic_fault','_get_logic_reads','_get_logic_writes',
    '_get_logic_frame','_get_logic_activation_frame','_get_logic_cpu_flags'];

  function stamp(message) {
    const li = document.createElement('li');
    li.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logEl.prepend(li);
    while (logEl.children.length > 38) logEl.lastChild.remove();
  }

  function message(title, body) {
    $('placeholderTitle').textContent = title;
    $('placeholderMessage').textContent = body;
    $('screenPlaceholder').hidden = false;
  }

  function setRunning(running) {
    const randomiserStatus=$('randomiserStatus');
    if (running && randomiserStatus.textContent==='Load a ROM to randomise a chip.')
      randomiserStatus.textContent='Choose PSG, FM, or VRAM to randomise a chip.';
    else if (!running && emulator && randomiserStatus.textContent==='Choose PSG, FM, or VRAM to randomise a chip.')
      randomiserStatus.textContent='Load a ROM to randomise a chip.';
    $('powerLed').classList.toggle('on', running);
    $('powerLabel').textContent = running ? 'CONSOLE ON' : (emulator ? 'WAITING FOR ROM' : 'CORE NOT READY');
    $('resetBtn').disabled = !running;
    $('compactResetBtn').disabled = !running;
    $('disconnectAllFaultsBtn').disabled = !running;
    $('pauseBtn').disabled = !running;
    $('soundBtn').disabled = !running;
    updateLogicControls();
    refreshVramControls();
    refreshPsgDataControls();
    refreshFmDataControls();
    refreshRandomiserControls();
    refreshCircuitConfigControls();
  }

  function samePair(a,b) { return !!(a && b) && a[0] === b[0] && a[1] === b[1]; }
  function canonical(pair) { return pair ? [...pair].sort((a,b) => a-b) : null; }
  function actualPair() { return momentary || latched; }
  function describe(pair) { return pair ? `AD${pair[0]} ↔ AD${pair[1]}` : 'NONE — NORMAL ADDRESSING'; }

  function vramModelApiReady(core=emulator) {
    return typeof core?._set_vram_fault_model==='function' &&
      typeof core?._get_vram_fault_model_state==='function' &&
      typeof core?._get_vram_supported_model_mask==='function';
  }

  function vramMaskApiReady() {
    return typeof emulator?._set_vram_address_mask==='function' &&
      typeof emulator?._get_vram_address_mask==='function';
  }

  function psgDataApiReady(core=emulator) {
    return typeof core?._set_psg_data_bridge==='function' &&
      typeof core?._get_psg_data_bridge_state==='function';
  }

  function fmDataApiReady(core=emulator) {
    return typeof core?._set_fm_data_bridge==='function' &&
      typeof core?._get_fm_data_bridge_state==='function';
  }

  function psgDataMaskApiReady(core=emulator) { return typeof core?._set_psg_data_mask==='function'; }
  function fmDataMaskApiReady(core=emulator) { return typeof core?._set_fm_data_mask==='function'; }

  function currentPsgDataState() {
    if (!psgDataApiReady()) return null;
    try { return emulator._get_psg_data_bridge_state(); }
    catch (_) { return null; }
  }

  function currentFmDataState() {
    if (!fmDataApiReady()) return null;
    try { return emulator._get_fm_data_bridge_state(); }
    catch (_) { return null; }
  }

  function refreshPsgDataControls() {
    const available=psgDataApiReady();
    const state=currentPsgDataState();
    const supported=!!state?.supported;
    $('psgBridgeApply').disabled=!started || !available || !supported;
    $('psgBridgeRemove').disabled=!started || !available || !state?.configured;
    $('psgBridgeA').disabled=!started || !available || !supported;
    $('psgBridgeB').disabled=!started || !available || !supported;
    $('psgLegMode').querySelector('[data-audio-mask]').disabled=!psgDataMaskApiReady();
    $('psgInputWrites').textContent=state?.inputWrites ?? '0';
    $('psgChangedWrites').textContent=state?.changedWrites ?? '0';
    $('psgBridgeStatus').textContent=!available
      ? 'This core does not provide the optional PSG runtime API.'
      : !state
        ? 'PSG runtime state is unavailable; controls are disabled.'
        : !supported
        ? (state.configured ? 'Configured, but inactive in this system profile.' : 'PSG bridge is unavailable in this system profile.')
        : state.configured
          ? (Number(state.dataMask||0)
            ? `Active: ${maskLineNames(Number(state.dataMask))} forced low on future writes.`
            : `Active: D${state.bridgeA} ↔ D${state.bridgeB}; future PSG writes only.`)
          : 'No PSG data bridge is active.';
    updateAudioChip('psg',state);
    document.querySelector('[data-keyboard-chip="PSG"]').classList.toggle('fault-active',
      started && !!state?.supported && !!state?.configured &&
      (!!Number(state.dataMask||0) || (state.bridgeA>=0 && state.bridgeB>=0)));
    refreshRandomiserControls();
  }

  function setPsgDataBridge(enabled, pairOverride=undefined) {
    resetCpuRecoveryObservation();
    if (!psgDataApiReady()) {
      $('psgBridgeStatus').textContent='This core does not provide the optional PSG runtime API.';
      return false;
    }
    const state=currentPsgDataState();
    if (enabled && !state?.supported) {
      $('psgBridgeStatus').textContent='PSG bridge request rejected: unsupported system profile.';
      return false;
    }
    const a=enabled ? Number(pairOverride===undefined ? $('psgBridgeA').value : pairOverride[0]) : -1;
    const b=enabled ? Number(pairOverride===undefined ? $('psgBridgeB').value : pairOverride[1]) : -1;
    if (enabled && (!Number.isInteger(a) || !Number.isInteger(b) || a<0 || a>7 || b<0 || b>7 || a===b)) {
      $('psgBridgeStatus').textContent='Choose two distinct PSG data inputs from D0 to D7.';
      return false;
    }
    const status=emulator._set_psg_data_bridge(enabled?1:0,a,b);
    if (status!==0) {
      $('psgBridgeStatus').textContent=status===2
        ? 'PSG bridge request rejected: unsupported system profile.'
        : 'PSG bridge request rejected: invalid settings.';
      stamp(`PSG bridge request rejected (status ${status})`);
      refreshPsgDataControls();
      return false;
    }
    abandonKeyboardHold('PSG');
    if (enabled && pairOverride!==undefined) {
      $('psgBridgeA').value=String(a); $('psgBridgeB').value=String(b);
    }
    refreshPsgDataControls();
    stamp(enabled
      ? `PSG data bridge applied: D${a} ↔ D${b}; existing chip state was not repaired.`
      : 'PSG data bridge removed; existing chip state was not repaired.');
    return true;
  }

  function setPsgDataMask(mask) {
    resetCpuRecoveryObservation();
    if (!psgDataMaskApiReady() || !Number.isInteger(mask) || mask<0 || mask>255) return false;
    const state=currentPsgDataState();
    if (!state || (mask && !state.supported)) return false;
    const status=emulator._set_psg_data_mask(mask);
    if (status!==0) {
      $('psgBridgeStatus').textContent=status===2?'PSG mask request rejected: unsupported system profile.':'PSG mask request rejected: invalid settings.';
      refreshPsgDataControls(); return false;
    }
    abandonKeyboardHold('PSG');
    refreshPsgDataControls();
    stamp(mask?`PSG data inputs ${maskLineNames(mask)} forced low for future writes.`:'PSG data fault removed; existing chip state was not repaired.');
    return true;
  }

  function refreshFmDataControls() {
    const available=fmDataApiReady();
    const state=currentFmDataState();
    const supported=!!state?.supported;
    $('fmBridgeApply').disabled=!started || !available || !supported;
    $('fmBridgeRemove').disabled=!started || !available || !state?.configured;
    $('fmBridgeA').disabled=!started || !available || !supported;
    $('fmBridgeB').disabled=!started || !available || !supported;
    $('fmLegMode').querySelector('[data-audio-mask]').disabled=!fmDataMaskApiReady();
    $('fmInputWrites').textContent=state?.inputWrites ?? '0';
    $('fmChangedWrites').textContent=state?.changedWrites ?? '0';
    $('fmBridgeStatus').textContent=!available
      ? 'This core does not provide the optional FM runtime API.'
      : !state
        ? 'FM runtime state is unavailable; controls are disabled.'
      : !supported
        ? (state.configured ? 'Configured, but inactive in this system profile.' : 'FM bridge is unavailable in this system profile.')
        : state.configured
          ? (Number(state.dataMask||0)
            ? `Active: ${maskLineNames(Number(state.dataMask))} forced low before register decode.`
            : `Active: D${state.bridgeA} ↔ D${state.bridgeB}; future FM register writes only.`)
          : 'No FM data bridge is active.';
    updateAudioChip('fm',state);
    document.querySelector('[data-keyboard-chip="FM"]').classList.toggle('fault-active',
      started && !!state?.supported && !!state?.configured &&
      (!!Number(state.dataMask||0) || (state.bridgeA>=0 && state.bridgeB>=0)));
    refreshRandomiserControls();
  }

  function setFmDataBridge(enabled, pairOverride=undefined) {
    resetCpuRecoveryObservation();
    if (!fmDataApiReady()) {
      $('fmBridgeStatus').textContent='This core does not provide the optional FM runtime API.';
      return false;
    }
    const state=currentFmDataState();
    if (enabled && !state?.supported) {
      $('fmBridgeStatus').textContent='FM bridge request rejected: unsupported system profile.';
      return false;
    }
    const a=enabled ? Number(pairOverride===undefined ? $('fmBridgeA').value : pairOverride[0]) : -1;
    const b=enabled ? Number(pairOverride===undefined ? $('fmBridgeB').value : pairOverride[1]) : -1;
    if (enabled && (!Number.isInteger(a) || !Number.isInteger(b) || a<0 || a>7 || b<0 || b>7 || a===b)) {
      $('fmBridgeStatus').textContent='Choose two distinct FM data inputs from D0 to D7.';
      return false;
    }
    const status=emulator._set_fm_data_bridge(enabled?1:0,a,b);
    if (status!==0) {
      $('fmBridgeStatus').textContent=status===2
        ? 'FM bridge request rejected: unsupported system profile.'
        : 'FM bridge request rejected: invalid settings.';
      stamp(`FM bridge request rejected (status ${status})`);
      refreshFmDataControls();
      return false;
    }
    abandonKeyboardHold('FM');
    if (enabled && pairOverride!==undefined) {
      $('fmBridgeA').value=String(a); $('fmBridgeB').value=String(b);
    }
    refreshFmDataControls();
    stamp(enabled
      ? `FM data bridge applied: D${a} ↔ D${b}; existing chip state was not repaired.`
      : 'FM data bridge removed; existing chip state was not repaired.');
    return true;
  }

  function setFmDataMask(mask) {
    resetCpuRecoveryObservation();
    if (!fmDataMaskApiReady() || !Number.isInteger(mask) || mask<0 || mask>255) return false;
    const state=currentFmDataState();
    if (!state || (mask && !state.supported)) return false;
    const status=emulator._set_fm_data_mask(mask);
    if (status!==0) {
      $('fmBridgeStatus').textContent=status===2?'FM mask request rejected: unsupported system profile.':'FM mask request rejected: invalid settings.';
      refreshFmDataControls(); return false;
    }
    abandonKeyboardHold('FM');
    refreshFmDataControls();
    stamp(mask?`FM data inputs ${maskLineNames(mask)} forced low before register decode.`:'FM data fault removed; existing chip state was not repaired.');
    return true;
  }

  function maskLineNames(mask) {
    return Array.from({length:8},(_,bit)=>bit).filter(bit=>mask&(1<<bit)).map(bit=>`D${bit}`).join(', ');
  }

  function randomPair() {
    const a=Math.floor(Math.random()*8), slot=Math.floor(Math.random()*7);
    return canonical([a,slot>=a?slot+1:slot]);
  }

  function randomCutMask() { return 1+Math.floor(Math.random()*255); }

  function refreshRandomiserControls() {
    let psg=null, fm=null, psgReady=false, fmReady=false, vramReady=false;
    try { psgReady=psgDataApiReady(); psg=currentPsgDataState(); psgReady=psgReady&&!!psg?.supported; } catch (_) { psgReady=false; }
    try { fmReady=fmDataApiReady(); fm=currentFmDataState(); fmReady=fmReady&&!!fm?.supported; } catch (_) { fmReady=false; }
    try { vramReady=!!emulator && (vramModelApiReady() || vramMaskApiReady() || typeof emulator._set_vram_short==='function'); } catch (_) { vramReady=false; }
    let ramSafe=!!emulator && !logicActive && !pendingPulse && !momentary;
    let pulse=null, pulseReadable=true;
    if (emulator && typeof emulator._get_logic_pulse_state==='function') {
      try {
        pulse=emulator._get_logic_pulse_state();
        ramSafe=ramSafe && Number.isInteger(pulse) && [0,2,3,4].includes(pulse);
      }
      catch (_) { ramSafe=false; pulseReadable=false; }
    }
    if (vramReady) {
      try {
        if (!vramModelApiReady()) {
          if (vramModelId!==1) vramReady=false;
        } else {
        const supported=Number(emulator._get_vram_supported_model_mask());
        const state=emulator._get_vram_fault_model_state();
        vramReady=!!state && Number.isInteger(supported) && (supported&(1<<vramModelId))!==0;
        }
      } catch (_) { vramReady=false; }
    }
    $('randomPsgBtn').disabled=!started || !psgReady;
    $('randomFmBtn').disabled=!started || !fmReady;
    $('randomVramBtn').disabled=!started || !vramReady || !ramSafe;
    const vramReason=!started?'Load a ROM first.':!vramReady?'The selected VRAM model or runtime API is unavailable.'
      :logicActive?'Disconnect the active Work RAM fault first.':pendingPulse?'Wait for or clear the active RAM pulse first.'
      :momentary?'Release the held VRAM bridge first.':!pulseReadable?'RAM pulse state is unavailable.'
      :pulse!==null&&![0,2,3,4].includes(pulse)?'An active RAM pulse prevents VRAM randomisation.':'';
    $('randomVramBtn').title=vramReason||'Randomise VRAM cuts or one bridge pair.';
  }

  function randomiseAudio(kind) {
    const isPsg=kind==='psg';
    const status=$(isPsg?'psgBridgeStatus':'fmBridgeStatus');
    let setterAttempted=false;
    try {
      const state=isPsg?currentPsgDataState():currentFmDataState();
      if (!started || !state?.supported) {
        $('randomiserStatus').textContent=`${kind.toUpperCase()} randomisation unavailable: runtime state or profile support could not be read.`;
        return false;
      }
      let ok, result, mode;
      const maskReady=isPsg?psgDataMaskApiReady():fmDataMaskApiReady();
      const bridgeReady=isPsg?psgDataApiReady():fmDataApiReady();
      if (!maskReady && !bridgeReady) throw new Error('Chip fault APIs are unavailable.');
      mode=maskReady && bridgeReady ? (Math.random()<0.5?'cut':'bridge') : maskReady?'cut':'bridge';
      const currentPair=state.configured && state.bridgeA>=0 && state.bridgeB>=0
        ? canonical([state.bridgeA,state.bridgeB]) : null;
      if (mode==='cut') {
        result=randomCutMask();
        ok=Number(state.dataMask)===result;
        if (!ok) {
          setterAttempted=true;
          ok=isPsg?setPsgDataMask(result):setFmDataMask(result);
        }
      } else {
        result=randomPair();
        ok=Number(state.dataMask||0)===0 && samePair(currentPair,result);
        if (!ok) {
          setterAttempted=true;
          ok=isPsg?setPsgDataBridge(true,result):setFmDataBridge(true,result);
        }
      }
      if (!ok) {
        let after=null;
        try { after=isPsg?currentPsgDataState():currentFmDataState(); } catch (_) { /* State is unknown below. */ }
        const changed=after && (after.dataMask!==state.dataMask || after.configured!==state.configured ||
          after.bridgeA!==state.bridgeA || after.bridgeB!==state.bridgeB);
        const unknown=setterAttempted&&!after;
        if (changed && !paused) pauseToggle();
        if (unknown && !paused) pauseToggle();
        status.textContent=`Randomiser did not apply ${kind.toUpperCase()} settings${after?'; observed state refreshed':'; resulting state is unavailable'}.`;
        $('randomiserStatus').textContent=`${kind.toUpperCase()} randomisation was rejected${changed?'; partial state observed and emulation paused':unknown?'; resulting state is unknown and emulation paused':'; runtime state is unchanged'}.`;
        return false;
      }
      const observed=isPsg?currentPsgDataState():currentFmDataState();
      if (!observed || (Array.isArray(result) ? !observed.configured || !samePair(canonical([observed.bridgeA,observed.bridgeB]),result)
          : Number(observed.dataMask)!==result)) {
        if (setterAttempted && !paused) pauseToggle();
        isPsg?refreshPsgDataControls():refreshFmDataControls();
        status.textContent=`${kind.toUpperCase()} randomisation could not be confirmed; runtime state is unavailable or differs from the requested setting.`;
        $('randomiserStatus').textContent=`${kind.toUpperCase()} randomisation could not be confirmed${setterAttempted?'; emulation paused for inspection':''}; runtime state is unavailable or differs from the requested setting.`;
        return false;
      }
      $(isPsg?'psgLegMode':'fmLegMode').value=mode==='cut'?'ground':'bridge';
      const selectedState=Array.isArray(result)?`D${result[0]} ↔ D${result[1]} bridge`:`${maskLineNames(result)} forced low`;
      $('randomiserStatus').textContent=`${kind.toUpperCase()}: ${selectedState}${setterAttempted?' applied':' already selected'}.`;
      return true;
    } catch (_) {
      if (setterAttempted && !paused) pauseToggle();
      try { isPsg?refreshPsgDataControls():refreshFmDataControls(); } catch (_) { /* Keep the failure report available. */ }
      status.textContent=setterAttempted
        ? `${kind.toUpperCase()} randomisation failed during the setter; emulation paused. Observed state refreshed where available.`
        : `${kind.toUpperCase()} randomisation refused because runtime state could not be read.`;
      $('randomiserStatus').textContent=setterAttempted
        ? `${kind.toUpperCase()} randomisation failed during the setter; emulation paused and observed state refreshed where available.`
        : `${kind.toUpperCase()} randomisation refused because runtime state could not be read.`;
      return false;
    } finally { refreshRandomiserControls(); }
  }

  function randomiseVram() {
    let setterAttempted=false;
    const refreshObserved=()=>{
      if (!vramModelApiReady()) return null;
      try {
        const actual=emulator._get_vram_fault_model_state();
        if (!actual || ![1,2].includes(actual.modelId) || !Number.isInteger(actual.mask) ||
            actual.mask<0 || actual.mask>255 || !Number.isInteger(actual.bridgeA) || !Number.isInteger(actual.bridgeB) ||
            !((actual.bridgeA===-1&&actual.bridgeB===-1) ||
              (actual.bridgeA>=0&&actual.bridgeA<=7&&actual.bridgeB>=0&&actual.bridgeB<=7&&actual.bridgeA!==actual.bridgeB)) ||
            (actual.mask&&(actual.bridgeA!==-1||actual.bridgeB!==-1))) throw new Error('VRAM state unavailable');
        vramModelId=actual.modelId;
        recordVramMask(actual.mask,'Randomiser observed runtime state');
        latched=actual.bridgeA>=0&&actual.bridgeB>=0?canonical([actual.bridgeA,actual.bridgeB]):null;
        momentary=null; momentaryRestorePair=null; selectedPin=null;
        $('vramMode').value=latched?'bridge':'disconnect';
        updateFaultUI();
        return actual;
      } catch (_) { return null; }
    };
    try {
      // Check every handoff hazard before choosing or applying anything.
      if (!started || logicActive || pendingPulse || momentary) throw new Error('RAM fault, pulse, or momentary VRAM bridge is active.');
      if (typeof emulator?._get_logic_pulse_state==='function') {
        const pulse=emulator._get_logic_pulse_state();
        if (![0,2,3,4].includes(pulse)) throw new Error('RAM pulse state is active or unavailable.');
      }
      let state=currentVramModelState();
      if (vramModelApiReady()) {
        const supported=Number(emulator._get_vram_supported_model_mask());
        state=emulator._get_vram_fault_model_state();
        if (!state || !Number.isInteger(supported) || (supported&(1<<vramModelId))===0)
          throw new Error('The selected VRAM model is unavailable.');
      } else if (vramModelId!==1) throw new Error('The selected VRAM model is unavailable.');
      const maskReady=vramMaskApiReady();
      const bridgeReady=vramModelApiReady() || typeof emulator?._set_vram_short==='function';
      if (!maskReady && !bridgeReady) throw new Error('This core has no supported VRAM fault setter.');
      const mode=maskReady && bridgeReady ? (Math.random()<0.5?'cut':'bridge') : maskReady?'cut':'bridge';
      const mask=mode==='cut'?randomCutMask():0, pair=mode==='bridge'?randomPair():null;
      if (!validateVramModel(vramModelId,mask,pair).ok) throw new Error('The selected VRAM setting is unsupported.');
      const previousPair=canonical(actualPair());
      const sameSelectedPair=(!previousPair&&!pair) || samePair(previousPair,pair);
      const unchanged=vramAddressMask===mask && sameSelectedPair;
      setterAttempted=!unchanged;
      if (!unchanged && !applyVramModel(vramModelId,mask,pair,'Randomiser')) {
        const actual=refreshObserved();
        const partial=!!actual && (actual.modelId!==state.modelId || actual.mask!==state.mask ||
          actual.bridgeA!==state.bridgeA || actual.bridgeB!==state.bridgeB);
        const unknown=!actual;
        if ((partial||unknown) && !paused) pauseToggle();
        $('randomiserStatus').textContent=`VRAM randomisation was rejected; ${partial?'partial runtime state observed and emulation paused':unknown?'runtime state is unknown and emulation paused': 'runtime state is unchanged'}.`;
        return false;
      }
      const observed=vramModelApiReady()?emulator._get_vram_fault_model_state():null;
      const mismatch=observed && (observed.modelId!==vramModelId || observed.mask!==mask ||
        (pair && (observed.bridgeA!==pair[0] || observed.bridgeB!==pair[1])));
      if ((vramModelApiReady()&&!observed) || mismatch) throw new Error('VRAM settings could not be confirmed.');
      $('vramMode').value=pair?'bridge':'disconnect';
      $('randomiserStatus').textContent=pair
        ? `VRAM: AD${pair[0]} ↔ AD${pair[1]} bridge${vramModelApiReady()?'':' (legacy core)'}${unchanged?' already selected':' applied'}.`
        : `VRAM: ${vramLines(mask).join(', ')} forced low${unchanged?' already selected':' applied'}.`;
      return true;
    } catch (error) {
      if (setterAttempted && !paused) pauseToggle();
      $('randomiserStatus').textContent=`VRAM randomisation unavailable: ${error?.message||'runtime state could not be read'}`;
      if (setterAttempted) {
        try {
          const observed=refreshObserved();
          $('randomiserStatus').textContent+=observed
            ? '; observed VRAM state refreshed.' : '; runtime state is unknown.';
        } catch (_) { /* Keep the refusal visible. */ }
      }
      return false;
    } finally { refreshRandomiserControls(); }
  }

  function updateAudioChip(kind,state) {
    const isPsg=kind==='psg', buttons=isPsg?psgPinButtons:fmPinButtons;
    const mode=$(isPsg?'psgLegMode':'fmLegMode').value;
    const selected=isPsg?psgSelectedPin:fmSelectedPin;
    const ready=isPsg?psgDataApiReady():fmDataApiReady();
    const maskReady=isPsg?psgDataMaskApiReady():fmDataMaskApiReady();
    const mask=Number.isInteger(state?.dataMask)?state.dataMask:0;
    const pair=state?.configured && state.bridgeA>=0 && state.bridgeB>=0?[state.bridgeA,state.bridgeB]:null;
    buttons.forEach((button,bit)=>{
      const grounded=!!(mask&(1<<bit)), bridged=!!(pair&&pair.includes(bit)), pending=selected===bit;
      button.disabled=!started || !ready || !state?.supported || (mode==='ground'&&!maskReady);
      button.classList.toggle('cut',grounded);
      button.classList.toggle('bridged',bridged);
      button.classList.toggle('selected',pending);
      button.querySelector('.chip-cut').textContent=grounded?'×':bridged?'↔':'×';
      button.setAttribute('aria-pressed',String(grounded||bridged||pending));
      button.setAttribute('aria-label',`${kind.toUpperCase()} D${bit}${grounded?', forced low':bridged?', bridged':pending?', selected for bridge':''}`);
    });
    const stateText=$(isPsg?'psgChipState':'fmChipState');
    if (stateText) stateText.textContent=mask
      ? `× ${maskLineNames(mask)} low`
      : pair?`D${pair[0]} ↔ D${pair[1]} bridge`:'No data fault';
  }

  function setupAudioChip(kind) {
    const isPsg=kind==='psg', id=isPsg?'psgChip':'fmChip';
    const buttons=isPsg?psgPinButtons:fmPinButtons;
    const state=()=>isPsg?currentPsgDataState():currentFmDataState();
    const mode=()=>$(isPsg?'psgLegMode':'fmLegMode').value;
    const refresh=()=>isPsg?refreshPsgDataControls():refreshFmDataControls();
    const selectPair=pair=>isPsg?setPsgDataBridge(true,pair):setFmDataBridge(true,pair);
    const setMask=mask=>isPsg?setPsgDataMask(mask):setFmDataMask(mask);
    for (let bit=0;bit<8;bit++) {
      const button=document.createElement('button');
      button.type='button';button.className='pin';
      button.style.gridColumn=bit<4?'1':'3';button.style.gridRow=String(bit<4?bit+1:bit-3);
      const label=document.createElement('span');label.className='chip-signal';label.textContent=`D${bit}`;
      const wire=document.createElement('span');wire.className='chip-wire';wire.setAttribute('aria-hidden','true');
      const cut=document.createElement('span');cut.className='chip-cut';cut.textContent='×';wire.append(cut);
      button.append(...(bit<4?[wire,label]:[label,wire]));
      button.title=`${kind.toUpperCase()} D${bit}; select two bits to bridge, or force the line low.`;
      button.setAttribute('aria-pressed','false');
      button.addEventListener('click',()=>{
        const live=state();
        if (!live?.supported) return;
        if (mode()==='ground') {
          if (! (isPsg?psgDataMaskApiReady():fmDataMaskApiReady())) return;
          const current=Number.isInteger(live.dataMask)?live.dataMask:0;
          if (isPsg) psgSelectedPin=null; else fmSelectedPin=null;
          setMask(current^(1<<bit));
          return;
        }
        const current=isPsg?psgSelectedPin:fmSelectedPin;
        if (current===null) {
          if (isPsg) psgSelectedPin=bit; else fmSelectedPin=bit;
        } else if (current===bit) {
          if (isPsg) psgSelectedPin=null; else fmSelectedPin=null;
        } else {
          if (isPsg) psgSelectedPin=null; else fmSelectedPin=null;
          selectPair([current,bit]);
        }
        refresh();
      });
      $(id).append(button);buttons.push(button);
    }
    const middle=document.createElement('div');middle.className='chip-middle';
    const title=document.createElement('strong');title.textContent=isPsg?'PSG / VDP':'YM2612';
    const subtitle=document.createElement('span');subtitle.textContent='D0–D7';
    middle.append(title,subtitle);$(id).append(middle);
    $(isPsg?'psgLegMode':'fmLegMode').addEventListener('change',()=>{
      if (isPsg) psgSelectedPin=null; else fmSelectedPin=null;
      refresh();
    });
    refresh();
  }

  function currentVramModelState() {
    if (vramModelApiReady()) {
      try {
        const state=emulator._get_vram_fault_model_state();
        if (state) return state;
      }
      catch (_) { /* The legacy view below remains usable if optional metadata fails. */ }
    }
    return {
      modelId:1,modelVersion:'frame-projection-v1',
      supportedModelsMask:3,effective:vramFaultActive(),
      reason:vramFaultActive()?'none':'no-fault',
      mask:vramAddressMask,bridgeA:actualPair()?.[0] ?? -1,
      bridgeB:actualPair()?.[1] ?? -1,
      lastFrameCounts:null
    };
  }

  function vramConfigArgs(modelId,mask,pair) {
    if (!Number.isInteger(modelId) || (modelId!==1 && modelId!==2) ||
        !Number.isInteger(mask) || mask<0 || mask>255) return null;
    if (mask && pair) return null;
    if (pair && (!Number.isInteger(pair[0]) || !Number.isInteger(pair[1]) ||
        pair[0]<0 || pair[0]>7 || pair[1]<0 || pair[1]>7 || pair[0]===pair[1])) return null;
    return pair ? [modelId,0,pair[0],pair[1]] : [modelId,mask,-1,-1];
  }

  function validateVramModel(modelId,mask,pair) {
    const args=vramConfigArgs(modelId,mask,pair);
    if (!args) return {ok:false,status:1,message:'Invalid VRAM model settings.'};
    if (modelId===2 && !vramModelApiReady())
      return {ok:false,status:2,message:'Transaction model needs a runtime-enabled core.'};
    if (vramModelApiReady()) {
      const supported=emulator._get_vram_supported_model_mask();
      if ((supported & (1<<modelId))===0)
        return {ok:false,status:2,message:'Transaction model is unsupported in the current VDP mode.'};
    } else if (modelId!==1 || (mask && !vramMaskApiReady()) ||
               (pair && typeof emulator?._set_vram_short!=='function')) {
      return {ok:false,status:1,message:'The current core does not support this VRAM setting.'};
    }
    return {ok:true,status:0,args};
  }

  function vramDisconnectModel() {
    const state=currentVramModelState();
    return vramModelId===2 && (state.supportedModelsMask&4)===0 ? 1 : vramModelId;
  }

  function prepareVramForRamFault(reason) {
    if (!vramFaultActive()) return {ok:true,snapshot:null};
    const snapshot={modelId:vramModelId,mask:vramAddressMask,pair:canonical(actualPair())};
    const targetModel=vramDisconnectModel();
    const preflight=validateVramModel(targetModel,0,null);
    if (!preflight.ok) {
      setLogicStatus(`RAM fault was not applied: VRAM reconnect preflight failed. ${preflight.message}`);
      stamp(`RAM handoff rejected before mutation: ${preflight.message}`);
      return {ok:false,snapshot};
    }
    if (!applyVramModel(targetModel,0,null,reason))
      return {ok:false,snapshot};
    return {ok:true,snapshot};
  }

  function restoreVramAfterRamReject(snapshot,reason) {
    if (!snapshot) return {ok:true,status:0};
    const ok=applyVramModel(snapshot.modelId,snapshot.mask,snapshot.pair,reason);
    const state=currentVramModelState();
    if (!ok) vramModelTransitions.push({frame:logicApiReady()?Number(emulator._get_logic_frame()):null,
      from:vramModelId,to:snapshot.modelId,fromMask:vramAddressMask,toMask:snapshot.mask,
      fromPair:canonical(actualPair()),toPair:snapshot.pair,reason,result:'restore-rejected',
      selectorStatus:lastVramSelectorStatus,actualModelId:state.modelId,actualMask:state.mask,
      actualBridgeA:state.bridgeA,actualBridgeB:state.bridgeB});
    return {ok,status:ok?0:lastVramSelectorStatus};
  }

  function recordRamHandoffRejection(snapshot,reason,status,rollback) {
    const actual=currentVramModelState();
    vramModelTransitions.push({frame:logicApiReady()?Number(emulator._get_logic_frame()):null,
      from:snapshot?.modelId??vramModelId,to:actual.modelId,
      fromMask:snapshot?.mask??vramAddressMask,toMask:actual.mask,
      fromPair:snapshot?.pair??canonical(actualPair()),
      toPair:actual.bridgeA>=0&&actual.bridgeB>=0?[actual.bridgeA,actual.bridgeB]:null,
      reason,result:'ram-fault-rejected',ramSetterStatus:status,
      vramRestoreStatus:rollback.status,actualModelId:actual.modelId,actualMask:actual.mask,
      actualBridgeA:actual.bridgeA,actualBridgeB:actual.bridgeB,
      transactionCountersReset:!!vramModelApiReady()&&!!snapshot,
      transactionCacheInvalidated:!!vramModelApiReady()&&!!snapshot&&snapshot.modelId===2});
  }

  function callVramModel(modelId,mask,pair) {
    const validation=validateVramModel(modelId,mask,pair);
    if (!validation.ok) return lastVramSelectorStatus=validation.status;
    if (vramModelApiReady())
      return lastVramSelectorStatus=emulator._set_vram_fault_model(...validation.args);
    // The legacy setters are retained for older cores and always mean frame projection.
    const maskSetter=typeof emulator?._set_vram_address_mask==='function';
    const bridgeSetter=typeof emulator?._set_vram_short==='function';
    if (pair) {
      const status=bridgeSetter?emulator._set_vram_short(pair[0],pair[1]):1;
      if (status!==0 && status!==undefined) return lastVramSelectorStatus=status;
    } else if (mask) {
      if (!maskSetter) return lastVramSelectorStatus=1;
      if (actualPair() && bridgeSetter) {
        const clearStatus=emulator._set_vram_short(-1,-1);
        if (clearStatus!==0 && clearStatus!==undefined) return lastVramSelectorStatus=clearStatus;
      }
      const status=emulator._set_vram_address_mask(mask);
      if (status!==0 && status!==undefined) return lastVramSelectorStatus=status;
    } else {
      if (bridgeSetter) {
        const clearStatus=emulator._set_vram_short(-1,-1);
        if (clearStatus!==0 && clearStatus!==undefined) return lastVramSelectorStatus=clearStatus;
      }
      if (maskSetter) {
        const status=emulator._set_vram_address_mask(0);
        if (status!==0 && status!==undefined) return lastVramSelectorStatus=status;
      }
    }
    return lastVramSelectorStatus=0;
  }

  function vramFaultActive() { return !!(vramAddressMask || actualPair()); }
  function vramLines(mask) {
    return Array.from({length:8},(_,i)=>i).filter(i=>mask & (1<<i)).map(i=>`AD${i}`);
  }

  function refreshVramTelemetry() {
    const modelState=currentVramModelState();
    const txSupported=vramModelApiReady() && (modelState.supportedModelsMask & 4)!==0;
    const modelSelect=$('vramModel');
    modelSelect.querySelector('[value="2"]').disabled=!vramModelApiReady() ||
      (!txSupported && vramModelId!==2);
    modelSelect.disabled=!started;
    if (modelSelect.value!==String(vramModelId)) modelSelect.value=String(vramModelId);
    const modelStatus=$('vramModelStatus');
    if (vramModelStatusMessage) {
      modelStatus.textContent=vramModelStatusMessage;
    } else if (!vramModelApiReady()) {
      modelStatus.textContent='This core uses frame projection. Rebuild with the runtime profile to enable transaction mode.';
    } else if (!started) {
      modelStatus.textContent='Load a cartridge to select a VRAM model.';
    } else if (modelState.modelId===2 && modelState.reason==='unsupported-mode') {
      modelStatus.textContent='Transaction mode is suspended outside supported VDP Mode 5; its configuration is retained.';
    } else if (vramModelId===2 && !txSupported) {
      modelStatus.textContent='Transaction mode is unsupported in the current VDP mode.';
    } else {
      modelStatus.textContent=vramModelId===2
        ? 'Logical-byte transaction model is selected; counters describe the last completed tick.'
        : 'Frame-projection model is selected; legacy difference counters retain their meaning.';
    }
    $('transactionMetrics').hidden=!vramModelApiReady();
    if (modelState.lastFrameCounts) {
      $('transactionReads').textContent=modelState.lastFrameCounts.logicalByteReads.toLocaleString();
      $('transactionWrites').textContent=modelState.lastFrameCounts.logicalByteWrites.toLocaleString();
      $('redirectedReads').textContent=modelState.lastFrameCounts.redirectedByteReads.toLocaleString();
      $('redirectedWrites').textContent=modelState.lastFrameCounts.redirectedByteWrites.toLocaleString();
      $('physicalWrites').textContent=modelState.lastFrameCounts.changedPhysicalByteWrites.toLocaleString();
    }
  }

  function refreshVramControls() {
    const supported=vramMaskApiReady();
    refreshVramTelemetry();
    $('vramMode').querySelector('[value="disconnect"]').disabled=!!emulator && !supported;
    $('vramModeHint').textContent=emulator && !supported
      ? 'This older core supports bridges only. Rebuild or download the current release for leg switches.'
      : 'Disconnected legs use a stuck-low approximation, not floating-wire physics. Click a crossed leg to reconnect.';
    const switching=$('vramMode').value==='disconnect';
    pinButtons.forEach((button,index)=>{
      const cut=!!(vramAddressMask & (1<<index));
      button.disabled=switching && (!started || !supported);
      button.setAttribute('aria-label', switching
        ? `AD${index}: ${cut?'forced low; reconnect':'enabled; force low'}`
        : `AD${index}: ${cut?'forced low; select to replace with bridge':'select net to bridge'}`);
      button.title=button.getAttribute('aria-label');
    });
  }

  function vramTransitionSnapshot() {
    return {
      frame:logicApiReady()?Number(emulator._get_logic_frame()):null,
      previousMask:vramAddressMask,
      projectedDifferencesBefore:Number(emulator?._get_vram_changed_reads?.() || 0),
      changedBytesBefore:Number(emulator?._get_vram_changed_writes?.() || 0)
    };
  }

  function recordVramMask(mask,reason,before=vramTransitionSnapshot()) {
    if(mask!==vramAddressMask) vramAddressLineChanges.push({...before,mask,reason});
    vramAddressMask=mask;
  }

  function applyVramModel(modelId,mask,pair,reason='VRAM model changed') {
    resetCpuRecoveryObservation();
    const targetPair=pair?canonical(pair):null;
    const validation=validateVramModel(modelId,mask,targetPair);
    if (!validation.ok) {
      vramModelStatusMessage=validation.message;
      $('vramModelStatus').textContent=vramModelStatusMessage;
      stamp(`VRAM request rejected: ${validation.message}`);
      return false;
    }
    const changesFault=!!(mask || targetPair);
    const removedLogic=changesFault && logicActive;
    if (removedLogic && pendingPulse) {
      setLogicStatus('Disconnect the active RAM pulse before applying a VRAM fault; its remaining budget is preserved.');
      stamp('VRAM handoff rejected while a RAM pulse is active; pulse budget preserved.');
      return false;
    }
    if (removedLogic && !logicApiReady()) {
      setLogicStatus('RAM fault cannot be disconnected; VRAM settings were not changed.');
      stamp('VRAM handoff rejected because RAM disconnect is unavailable.');
      return false;
    }

    const oldModel=vramModelId, oldMask=vramAddressMask, oldPair=canonical(actualPair());
    const oldFrame=logicApiReady()?Number(emulator._get_logic_frame()):null;
    const before=vramTransitionSnapshot();
    const status=callVramModel(modelId,mask,targetPair);
    if (status!==0) {
      vramModelStatusMessage=`VRAM model rejected (status ${status}); RAM settings were not changed.`;
      $('vramModelStatus').textContent=vramModelStatusMessage;
      stamp(`VRAM model rejected (status ${status}); RAM fault remains unchanged.`);
      return false;
    }
    abandonKeyboardHold('VRAM');
    if (removedLogic && !disconnectLogic({silent:true})) {
      let rollbackStatus=callVramModel(oldModel,oldMask,oldPair);
      let safeFallbackStatus=null;
      if (rollbackStatus!==0) {
        safeFallbackStatus=callVramModel(1,0,null);
        if (safeFallbackStatus===0) {
          vramModelId=1;
          recordVramMask(0,'VRAM rollback used frame-projection identity');
          latched=null; momentary=null; momentaryRestorePair=null; selectedPin=null;
          rollbackStatus=0;
        }
      }
      if (rollbackStatus!==0 && vramModelApiReady()) {
        const actual=currentVramModelState();
        vramModelId=actual.modelId;
        vramAddressMask=actual.mask;
        latched=actual.bridgeA>=0&&actual.bridgeB>=0
          ? canonical([actual.bridgeA,actual.bridgeB]) : null;
        momentary=null;momentaryRestorePair=null;selectedPin=null;
      }
      vramModelTransitions.push({frame:oldFrame,from:oldModel,to:modelId,reason,
        result:'ram-disconnect-rejected',rollbackStatus,safeFallbackStatus,
        attemptedModelCountersReset:vramModelApiReady()?modelId:null,
        rollbackModelCountersReset:vramModelApiReady()&&rollbackStatus===0?oldModel:null,
        transactionCacheInvalidated:!!vramModelApiReady()&&(modelId===2||oldModel===2),
        actualModelId:currentVramModelState().modelId,actualMask:currentVramModelState().mask,
        actualBridgeA:currentVramModelState().bridgeA,actualBridgeB:currentVramModelState().bridgeB,
        ramFaultStillActive:logicActive});
      vramModelStatusMessage=rollbackStatus===0
        ? safeFallbackStatus===0
          ? 'RAM disconnect failed. VRAM faults were cleared in frame mode; selector rollback reset model counters.'
          : 'RAM disconnect failed. VRAM settings were restored; selector rollback reset model counters.'
        : 'RAM disconnect failed and VRAM rollback was rejected. Stop emulation and reload the cartridge.';
      $('vramModelStatus').textContent=vramModelStatusMessage;
      stamp(rollbackStatus===0
        ? safeFallbackStatus===0
          ? 'RAM disconnect failed; VRAM faults cleared in frame mode. Selector rollback reset model counters.'
          : 'RAM disconnect failed; VRAM configuration restored. Selector rollback reset model counters.'
        : `RAM disconnect failed; VRAM rollback also failed (status ${rollbackStatus}).`);
      updateFaultUI();
      if (rollbackStatus!==0) {
        if (!paused) pauseToggle();
        vramModelStatusMessage='RAM disconnect failed and VRAM rollback was rejected. Both fault states are retained; emulation was paused.';
        $('vramModelStatus').textContent=vramModelStatusMessage;
        stamp('Unsafe dual-domain rollback failure; emulation paused before another tick.');
      }
      return false;
    }
    vramModelStatusMessage='';
    vramModelId=modelId;
    recordVramMask(mask,reason,before);
    latched=targetPair; momentary=null; selectedPin=null;
    if (removedLogic) {
      logicResetState='Logic fault disconnected because VRAM fault was activated';
      logicStatusMessage='VRAM patch active; logic/Work RAM fault disconnected.';
      $('logicStatus').textContent=logicStatusMessage;
      stamp('Logic/Work RAM fault disconnected because the VRAM patch was activated');
    }
    if (oldModel!==modelId || oldMask!==mask || !samePair(oldPair,targetPair)) {
      vramModelTransitions.push({frame:oldFrame,from:oldModel,to:modelId,
        fromMask:oldMask,toMask:mask,fromPair:oldPair,toPair:targetPair,reason,result:'applied'});
    }
    if (oldModel!==modelId) {
      stamp(`VRAM model changed from ${oldModel===2?'transaction':'frame projection'} to ${modelId===2?'transaction':'frame projection'}`);
    }
    updateFaultUI();
    return true;
  }

  function applyVramAddressMask(mask) {
    if(!started || !Number.isInteger(mask) || mask<0 || mask>255) return false;
    return applyVramModel(vramModelId,mask,null,'VRAM leg toggled');
  }

  function logicApiReady(core=emulator) {
    return !!core && LOGIC_API.every(name => typeof core[name] === 'function');
  }

  function writePulseApiReady() {
    return typeof emulator?._arm_logic_write_pulse === 'function' &&
      typeof emulator?._get_logic_pulse_state === 'function';
  }

  function addressMaskApiReady() {
    return typeof emulator?._set_logic_address_mask === 'function' &&
      typeof emulator?._get_logic_address_mask === 'function';
  }

  function refreshChipControls() {
    const ready=started && addressMaskApiReady();
    for (const button of document.querySelectorAll('[data-chip-line]')) {
      const line=Number(button.dataset.chipLine), forced=!!(logicAddressMask & (1<<line));
      const bridged=logicActive && activeRamConfiguration?.type==='line-pair' && activeRamConfiguration.kind===1 &&
        [activeRamConfiguration.a,activeRamConfiguration.b].includes(line);
      const pending=ramSelectedPin===line;
      button.disabled=!ready;
      button.classList.toggle('cut',forced);
      button.classList.toggle('bridged',bridged);
      button.classList.toggle('selected',pending);
      button.querySelector('.chip-cut').textContent=forced?'×':bridged?'↔':'×';
      button.setAttribute('aria-pressed',String(forced||bridged||pending));
      button.setAttribute('aria-label',`A${line+1}: ${forced?'forced low; reconnect':bridged?'bridged; select another leg action to change':'connected'}`);
    }
    $('chipRestoreBtn').disabled=!ready || (logicAddressMask===0 && !(logicActive && activeRamConfiguration?.type==='line-pair' && activeRamConfiguration.kind===1));
    $('ramLegAction').disabled=!started || !logicApiReady();
    $('ramChipState').textContent=logicAddressMask
      ? `${Array.from({length:15},(_,i)=>i).filter(i=>logicAddressMask&(1<<i)).map(i=>`A${i+1}`).join(', ')} forced low`
      : logicActive && activeRamConfiguration?.type==='line-pair' && activeRamConfiguration.kind===1
        ? `A${activeRamConfiguration.a+1} ↔ A${activeRamConfiguration.b+1} bridge`
        : logicActive && activeRamConfiguration?.type==='line-pair' && activeRamConfiguration.kind===2
          ? `Data bridge D${activeRamConfiguration.a} ↔ D${activeRamConfiguration.b} active; see RAM settings.`
          : 'Address lines are connected.';
  }

  function chipTransitionSnapshot() {
    return {frame:Number(emulator._get_logic_frame()),previousMask:logicAddressMask,
      readCountBefore:Number(emulator._get_logic_reads()),writeCountBefore:Number(emulator._get_logic_writes())};
  }

  function recordAddressMask(mask,access,reason,before) {
    if (mask!==logicAddressMask) addressLineChanges.push({...before,mask,access,reason});
    logicAddressMask=mask;
  }

  function applyAddressMask(mask, accessOverride=undefined) {
    resetCpuRecoveryObservation();
    if (!started || !addressMaskApiReady()) return false;
    const access=Number(accessOverride===undefined ? $('logicAccess').value : accessOverride);
    if (!Number.isInteger(mask) || mask<0 || mask>0x7fff ||
        !Number.isInteger(access) || access<1 || access>3) {
      setLogicStatus('Invalid RAM address mask; no fault was applied.');
      return false;
    }
    const event=chipTransitionSnapshot();
    if (mask===0) {
      if (!disconnectLogic()) return false;
      return true;
    }
    const handoff=prepareVramForRamFault('VRAM fault cleared before RAM fault activation');
    if (!handoff.ok) return false;
    const status=emulator._set_logic_address_mask(mask,access);
    if (status!==0) {
      const rollback=restoreVramAfterRamReject(handoff.snapshot,'restored after RAM address-line rejection');
      recordRamHandoffRejection(handoff.snapshot,'RAM address-line setter rejected after VRAM clear',status,rollback);
      setLogicStatus(rollback.ok
        ? `Address-line setting rejected (status ${status}); previous VRAM configuration restored.`
        : `Address-line setting rejected (status ${status}); VRAM configuration restore failed.`);
      stamp(rollback.ok
        ? `RAM address-line request rejected (status ${status}); previous VRAM configuration restored.`
        : `RAM address-line request rejected (status ${status}); VRAM restore also failed.`);
      return false;
    }
    abandonKeyboardHold('WRAM');
    ownedAddressHold=null;
    cancelPulse('replaced by address-line switches');
    recordAddressMask(mask,access,'address line toggled',event); logicActive=true; logicStatsRetained=false;
    activeRamConfiguration={type:'address-mask',mask,access};
    const lines=Array.from({length:15},(_,i)=>i).filter(i=>mask & (1<<i)).map(i=>`A${i+1}`);
    const accessLabel=['','read','write','read + write'][access];
    lastLogicExperiment={kind:'address-stuck-low',access:accessLabel,lines,addressMask:mask,
      activationFrame:Number(emulator._get_logic_activation_frame()),resetState:logicResetState,
      currentFrame:event.frame,readCount:0,writeCount:0,cpuFlags:Number(emulator._get_logic_cpu_flags())};
    setLogicStatus(`${lines.join(', ')} forced low on ${accessLabel}. Click crossed wires to reconnect; stored writes persist.`);
    stamp(`Address lines forced low: ${lines.join(', ')} (${accessLabel})`);
    return true;
  }

  function setupAddressChip() {
    for (let line=0;line<15;line++) {
      const button=document.createElement('button');
      button.type='button';button.className='chip-pin';button.dataset.chipLine=String(line);
      button.style.gridColumn=line<8?'1':'3';button.style.gridRow=String(line<8?line+1:line-7);
      const label=document.createElement('span');label.className='chip-signal';label.textContent=`A${line+1}`;
      const wire=document.createElement('span');wire.className='chip-wire';wire.setAttribute('aria-hidden','true');
      const cut=document.createElement('span');cut.className='chip-cut';cut.textContent='×';wire.append(cut);
      button.append(...(line<8?[wire,label]:[label,wire]));
      button.addEventListener('click',()=>{
        if ($('ramLegAction').value==='cut') {
          ramSelectedPin=null;
          applyAddressMask(logicAddressMask ^ (1<<line));
          refreshChipControls();
          return;
        }
        if (ramSelectedPin===null) ramSelectedPin=line;
        else if (ramSelectedPin===line) ramSelectedPin=null;
        else {
          const first=ramSelectedPin;ramSelectedPin=null;
          $('logicKind').value='1';configureLogicLines();
          $('logicLineA').value=String(first);$('logicLineB').value=String(line);
          applyLogicFault(null,{kind:1,access:Number($('logicAccess').value),a:first,b:line});
        }
        refreshChipControls();
      });
      $('ramChip').append(button);
    }
    $('chipRestoreBtn').addEventListener('click',()=>{
      ramSelectedPin=null;
      if (logicAddressMask) applyAddressMask(0);
      else if (logicActive && activeRamConfiguration?.type==='line-pair' && activeRamConfiguration.kind===1) disconnectLogic();
      refreshChipControls();
    });
    $('ramLegAction').addEventListener('change',()=>{ramSelectedPin=null;refreshChipControls();});
  }

  function updateLogicControls() {
    logicApiAvailable = logicApiReady();
    const canUse = started && logicApiAvailable;
    for (const id of ['logicKind','logicAccess','logicLineA','logicLineB','logicApplyBtn'])
      $(id).disabled = !canUse;
    $('logicDisconnectBtn').disabled = !canUse;
    updateCpuRecoveryControls(canUse);
    for (const id of ['logicResumeBtn','logicCpuResetBtn'])
      $(id).disabled = !canUse || typeof emulator._recover_logic_cpu !== 'function';
    for (const control of document.querySelectorAll('[data-ram-frame-pair]'))
      control.disabled = !canUse;
    $('ramWriteMode').disabled=!canUse;
    for (const control of document.querySelectorAll('[data-ram-frame-pair]')) {
      const owned=ownedAddressHold?.key===control.dataset.ramFramePair;
      control.setAttribute('aria-pressed',String(owned));
      control.classList.toggle('active',owned);
      control.setAttribute('aria-label',`${owned?'Held':'Write-only bridge'} A${Number(control.dataset.ramFramePair.split(',')[0])+1} and A${Number(control.dataset.ramFramePair.split(',')[1])+1}${$('ramWriteMode').value==='hold'?' while pressed':' for eight emulated frames'}`);
    }
    for (const control of document.querySelectorAll('[data-ram-pulse], #logicPulseBtn, #logicPulseFrames'))
      control.disabled = !canUse || typeof emulator._recover_logic_cpu !== 'function';
    for (const option of $('logicPulseFrames').querySelectorAll('[data-write-limit]'))
      option.disabled = !writePulseApiReady();
    $('logicExperimentBtn').disabled = !started || !romBytes;
    if (!logicApiAvailable) logicStatusMessage = 'Rebuild core for logic faults';
    else if (!started && ['Checking core support…','Rebuild core for logic faults'].includes(logicStatusMessage))
      logicStatusMessage = 'Load a ROM to enable logic faults.';
    $('logicStatus').textContent = logicStatusMessage;
    document.querySelector('[data-keyboard-chip="WRAM"]').classList.toggle('fault-active',started && logicActive);
    refreshLogicMetrics();
    refreshChipControls();
    refreshRandomiserControls();
  }

  function updateCpuRecoveryControls(canUse=started && logicApiReady()) {
    const recoveryReady=canUse && !paused && typeof emulator?._recover_logic_cpu==='function' &&
      typeof emulator?._get_logic_cpu_flags==='function';
    $('armCpuRecoveryBtn').disabled=!recoveryReady || (!cpuRecoveryArmed && recoveryTransientActive());
    $('armCpuRecoveryBtn').setAttribute('aria-pressed',String(cpuRecoveryArmed));
    $('armCpuRecoveryBtn').textContent=cpuRecoveryArmed?'Disarm CPU Recovery':'Arm CPU Recovery Once';
    $('cpuRecoveryStatus').textContent=cpuRecoveryArmed
      ? `ARMED${cpuRecoveryHaltFrames.length?` · HALT ${cpuRecoveryHaltFrames.length}/2`:''}` : 'OFF';
  }

  function recoveryTransientActive() {
    return !!(momentary || keyboardHeld || ownedAddressHold || pendingPulse);
  }

  function resetCpuRecoveryObservation() {
    const hadObservation=cpuRecoveryHaltFrames.length>0;
    cpuRecoveryHaltFrames=[];
    if (hadObservation) updateCpuRecoveryControls();
  }

  function disarmCpuRecovery() {
    cpuRecoveryArmed=false;
    resetCpuRecoveryObservation();
    updateCpuRecoveryControls();
  }

  function abortAutomaticCpuRecovery(reason, frame=null, flags=null, observedFrames=[]) {
    cpuRecoveryArmed=false;
    resetCpuRecoveryObservation();
    cpuInterventions.push({action:'automatic-recovery-aborted',trigger:'armed-halt-streak',
      frame,observedFlags:flags,observedFrames:[...observedFrames],attempted:false,
      outcome:'aborted',reason});
    if (!paused) pauseToggle();
    setLogicStatus(`Automatic CPU recovery stopped: ${reason}. Emulation paused for inspection; no retry will occur.`);
    stamp(`Automatic CPU recovery aborted: ${reason}; emulation paused; no retry`);
    updateLogicControls();
  }

  function observeAutomaticCpuRecovery() {
    if (!cpuRecoveryArmed || paused || !started) return;
    if (recoveryTransientActive()) { resetCpuRecoveryObservation(); return; }
    let flags, frame;
    try {
      flags=emulator._get_logic_cpu_flags();
      frame=emulator._get_logic_frame();
      if (typeof flags!=='number' || !Number.isInteger(flags) || flags<0 || flags>3 ||
          typeof frame!=='number' || !Number.isSafeInteger(frame) || frame<0)
        throw new Error('CPU flag or frame telemetry is invalid');
    } catch (error) {
      abortAutomaticCpuRecovery(`CPU telemetry unavailable (${error.message})`,null,null,cpuRecoveryHaltFrames);
      return;
    }
    if (!(flags&2)) { resetCpuRecoveryObservation(); return; }
    cpuRecoveryHaltFrames.push(frame);
    if (cpuRecoveryHaltFrames.length<2) { updateLogicControls(); return; }
    const observedFrames=[...cpuRecoveryHaltFrames];
    cpuRecoveryArmed=false; // Consume before clears or native recovery can fail.
    resetCpuRecoveryObservation();
    const interventionStart=cpuInterventions.length;
    let succeeded=false, reason='CPU recovery failed';
    try { succeeded=recoverLogicCPU(2)===true; }
    catch (error) { reason=`CPU recovery threw (${error.message})`; }
    const latest=cpuInterventions.at(-1);
    if (succeeded && latest && cpuInterventions.length>interventionStart) {
      Object.assign(latest,{trigger:'armed-halt-streak',observedFlags:flags,
        observedFrames,attempted:true,outcome:'issued'});
      if (latest.telemetryError) {
        if (!paused) pauseToggle();
        setLogicStatus(`CPU-only reset issued; post-reset telemetry unavailable (${latest.telemetryError}). Emulation paused for inspection; no retry will occur.`);
      }
    } else {
      reason=lastCpuRecoveryAttempt?.reason || reason;
      if (latest && cpuInterventions.length>interventionStart && latest.action==='recovery-aborted') {
        Object.assign(latest,{trigger:'armed-halt-streak',observedFlags:flags,
          observedFrames,attempted:false,outcome:'aborted'});
      } else if (latest && cpuInterventions.length>interventionStart &&
          ['cpu-only-reset','force-resume','cpu-recovery-rejected'].includes(latest.action)) {
        Object.assign(latest,{trigger:'armed-halt-streak',observedFlags:flags,observedFrames,
          attempted:true,outcome:latest.action==='cpu-recovery-rejected'?'rejected':'aborted',reason});
      } else cpuInterventions.push({action:'automatic-recovery-aborted',trigger:'armed-halt-streak',
        frame,observedFlags:flags,observedFrames,attempted:!!lastCpuRecoveryAttempt?.nativeCalled,
        outcome:'aborted',reason});
      if (!paused) pauseToggle();
      setLogicStatus(`Automatic CPU recovery stopped: ${reason}. Emulation paused for inspection; no retry will occur.`);
      stamp(`Automatic CPU recovery aborted: ${reason}; emulation paused; no retry`);
    }
    updateLogicControls();
  }

  function refreshLogicMetrics() {
    const core=emulator;
    if (logicApiReady(core)) {
      const metric=(getter,fallback=null)=>{
        try { const value=Number(getter.call(core)); return Number.isFinite(value)?value:fallback; }
        catch (_) { return fallback; }
      };
      const reads=metric(core._get_logic_reads,0);
      const writes=metric(core._get_logic_writes,0);
      const frame=metric(core._get_logic_frame);
      const activation=metric(core._get_logic_activation_frame);
      let flags=null;
      try { flags=Number(core._get_logic_cpu_flags()); if (!Number.isFinite(flags)) flags=null; }
      catch (_) { flags=null; }
      const shownReads=!logicActive && logicStatsRetained && lastLogicExperiment
        ? lastLogicExperiment.readCount : reads;
      const shownWrites=!logicActive && logicStatsRetained && lastLogicExperiment
        ? lastLogicExperiment.writeCount : writes;
      $('logicReadCount').textContent=shownReads.toLocaleString();
      $('logicWriteCount').textContent=shownWrites.toLocaleString();
      $('logicFrame').textContent=frame===null?'—':frame.toLocaleString();
      const shownActivation=logicActive && Number.isFinite(activation) && activation>=0
        ? activation : lastLogicExperiment?.activationFrame;
      $('logicActivationFrame').textContent=shownActivation===undefined ? '—' : Number(shownActivation).toLocaleString();
      const cpu=[];
      if (flags===null) $('logicCpuStatus').textContent='CPU status unavailable';
      else {
        if (flags & 1) cpu.push('STOP');
        if (flags & 2) cpu.push('HALT');
        $('logicCpuStatus').textContent=cpu.length ? cpu.join(' + ') : 'No STOP/HALT flag';
      }
      if (lastLogicExperiment && logicActive) {
        lastLogicExperiment.currentFrame=frame;
        lastLogicExperiment.readCount=reads;
        lastLogicExperiment.writeCount=writes;
        lastLogicExperiment.cpuFlags=flags;
      }
    }
    $('logicStatus').textContent=logicStatusMessage;
  }

  function configureLogicLines() {
    const kind=Number($('logicKind').value);
    const priorA=$('logicLineA').value, priorB=$('logicLineB').value;
    const indexA=priorA==='' ? 0 : Number(priorA);
    const indexB=priorB==='' ? 1 : Number(priorB);
    const count=kind===1 ? 15 : 16;
    const label=kind===1 ? index => `A${index+1}` : index => `D${index}`;
    for (const [select,prior] of [[$('logicLineA'),indexA],[$('logicLineB'),indexB]]) {
      select.replaceChildren();
      for (let i=0;i<count;i++) {
        const option=document.createElement('option');
        option.value=String(i); option.textContent=label(i); select.append(option);
      }
      select.value=prior<count ? String(prior) : '0';
    }
  }

  function setLogicStatus(message) {
    logicStatusMessage=message;
    updateLogicControls();
  }

  function setAddressFramePulseStatus(message) {
    setLogicStatus(message);
    $('randomiserStatus').textContent=message;
  }

  function logicConfigFromControls() {
    return {
      kind:Number($('logicKind').value),
      access:Number($('logicAccess').value),
      a:Number($('logicLineA').value),
      b:Number($('logicLineB').value)
    };
  }

  function logicLineName(kind,line) { return kind===1 ? `A${line+1}` : `D${line}`; }

  function applyLogicFault(writeLimit=null, configOverride=null) {
    resetCpuRecoveryObservation();
    if (!started || !logicApiReady()) return false;
    const config=configOverride || logicConfigFromControls();
    const lineCount=config.kind===1?15:config.kind===2?16:0;
    if (!lineCount || !Number.isInteger(config.access) || config.access<1 || config.access>3 ||
        !Number.isInteger(config.a) || !Number.isInteger(config.b) ||
        config.a<0 || config.b<0 || config.a>=lineCount || config.b>=lineCount) {
      setLogicStatus('Invalid RAM fault configuration. No fault was applied.');
      return false;
    }
    if (config.a===config.b) {
      setLogicStatus('Choose two different lines. No fault was applied.');
      return false;
    }
    if (config.kind===2 && Math.floor(config.a/8)!==Math.floor(config.b/8)) {
      setLogicStatus('Data pairs must stay within D0–D7 or D8–D15. No fault was applied.');
      return false;
    }
    if (writeLimit!==null && (!Number.isInteger(writeLimit) || ![1,2,4,8].includes(writeLimit) ||
        !writePulseApiReady() || config.access!==2)) {
      setLogicStatus('Affected-write pulses require Access: Write and a rebuilt core.');
      return false;
    }
    const handoff=prepareVramForRamFault('VRAM fault cleared before RAM fault activation');
    if (!handoff.ok) return false;
    const chipBefore=chipTransitionSnapshot();
    const status=writeLimit===null
      ? emulator._set_logic_fault(config.kind,config.access,config.a,config.b)
      : emulator._arm_logic_write_pulse(config.kind,config.a,config.b,writeLimit);
    if (status!==0) {
      const rollback=restoreVramAfterRamReject(handoff.snapshot,'restored after RAM fault rejection');
      recordRamHandoffRejection(handoff.snapshot,'RAM fault setter rejected after VRAM clear',status,rollback);
      setLogicStatus(rollback.ok
        ? `Core rejected this logic fault (status ${status}); previous VRAM configuration restored.`
        : `Core rejected this logic fault (status ${status}); VRAM configuration restore failed.`);
      stamp(rollback.ok
        ? `Logic fault rejected: core status ${status}; previous VRAM configuration restored.`
        : `Logic fault rejected: core status ${status}; VRAM restore also failed.`);
      return false;
    }
    abandonKeyboardHold('WRAM');
    ownedAddressHold=null;
    cancelPulse('replaced by another fault');
    recordAddressMask(0,0,'replaced by paired fault',chipBefore);
    logicActive=true;
    activeRamConfiguration={type:'line-pair',kind:config.kind,access:config.access,
      a:Math.min(config.a,config.b),b:Math.max(config.a,config.b)};
    logicStatsRetained=false;
    const activation=Number(emulator._get_logic_activation_frame());
    const kindLabel=config.kind===1 ? 'address' : 'data';
    const accessLabel=['','read','write','read + write'][config.access] || 'unknown access';
    const lineA=logicLineName(config.kind,config.a), lineB=logicLineName(config.kind,config.b);
    lastLogicExperiment={
      kind:kindLabel, access:accessLabel, lines:[lineA,lineB],
      activationFrame:Number.isFinite(activation) && activation>=0 ? activation : Number(emulator._get_logic_frame()) || 0,
      resetState:logicResetState,
      currentFrame:Number(emulator._get_logic_frame()) || 0,
      readCount:Number(emulator._get_logic_reads()) || 0,
      writeCount:Number(emulator._get_logic_writes()) || 0,
      cpuFlags:Number(emulator._get_logic_cpu_flags()) || 0
    };
    setLogicStatus(`Applied ${kindLabel} ${lineA} ↔ ${lineB} on ${accessLabel}.`);
    stamp(`LOGIC / Work RAM FAULT: ${kindLabel} ${lineA} ↔ ${lineB}, ${accessLabel}`);
    return true;
  }

  function disconnectLogic({silent=false,pulseReason='fault disconnected'}={}) {
    resetCpuRecoveryObservation();
    if (!logicActive) {
      cancelPulse(pulseReason);
      if (!silent) setLogicStatus('No logic fault is active.');
      return true;
    }
    if (!logicApiReady()) return false;
    const finalReads=Number(emulator._get_logic_reads()) || 0;
    const finalWrites=Number(emulator._get_logic_writes()) || 0;
    const finalFrame=Number(emulator._get_logic_frame()) || 0;
    const finalFlags=Number(emulator._get_logic_cpu_flags()) || 0;
    const status=emulator._set_logic_fault(0,0,-1,-1);
    if (status!==0) {
      if (!silent) setLogicStatus(`Core could not disconnect the logic fault (status ${status}).`);
      return false;
    }
    abandonKeyboardHold('WRAM');
    ownedAddressHold=null;
    cancelPulse(pulseReason);
    logicActive=false;
    activeRamConfiguration=null;
    recordAddressMask(0,0,'fault disconnected',{frame:finalFrame,previousMask:logicAddressMask,
      readCountBefore:finalReads,writeCountBefore:finalWrites});
    logicStatsRetained=true;
    if (lastLogicExperiment) {
      lastLogicExperiment.disconnectedAtFrame=finalFrame;
      lastLogicExperiment.readCount=finalReads;
      lastLogicExperiment.writeCount=finalWrites;
      lastLogicExperiment.cpuFlags=finalFlags;
    }
    if (!silent) {
      logicResetState='Logic fault disconnected; RAM writes persist';
      setLogicStatus('Logic fault disconnected. Any projected writes remain in RAM until a clean restart.');
      stamp('Logic/Work RAM fault disconnected; projected RAM writes persist');
    }
    updateLogicControls();
    return true;
  }

  function recoverLogicCPU(mode) {
    lastCpuRecoveryAttempt={nativeCalled:false,status:null};
    disarmCpuRecovery();
    if (!started || typeof emulator?._recover_logic_cpu !== 'function') return false;
    const frame=Number(emulator._get_logic_frame());
    const flagsBefore=Number(emulator._get_logic_cpu_flags());
    const hadRamFault=logicActive;
    if (!disconnectLogic({silent:true,pulseReason:'manual CPU recovery'})) {
      lastCpuRecoveryAttempt.reason='RAM clear rejected or unavailable';
      setLogicStatus('Recovery stopped: could not disconnect RAM fault.');
      return false;
    }
    if (!disconnect('CPU recovery disconnected VRAM fault')) {
      const state=currentVramModelState();
      const partial={action:'recovery-aborted',frame,flagsBefore,
        ramFaultWasActive:hadRamFault,ramFaultDisconnected:hadRamFault&&!logicActive,
        vramFaultDisconnected:false,reason:'VRAM clear rejected',
        actualModelId:state.modelId,actualMask:state.mask,
        actualBridgeA:state.bridgeA,actualBridgeB:state.bridgeB};
      cpuInterventions.push(partial);
      logicResetState='Recovery stopped after RAM fault disconnect; VRAM configuration remains active';
      setLogicStatus('Recovery stopped: VRAM clear was rejected. The RAM fault is disconnected, VRAM configuration remains active, and no CPU intervention was issued.');
      stamp('CPU recovery aborted after RAM disconnect; VRAM configuration remains active and CPU intervention was not issued.');
      return false;
    }
    lastCpuRecoveryAttempt.nativeCalled=true;
    const status=emulator._recover_logic_cpu(mode);
    lastCpuRecoveryAttempt.status=status;
    if (status!==0) {
      lastCpuRecoveryAttempt.reason=`CPU recovery rejected (status ${status})`;
      cpuInterventions.push({action:'cpu-recovery-rejected',frame,flagsBefore,
        status,attempted:true,outcome:'rejected'});
      setLogicStatus(`CPU recovery rejected (status ${status}).`);
      return false;
    }
    const action=mode===1 ? 'force-resume' : 'cpu-only-reset';
    const intervention={action,frame,flagsBefore,flagsAfter:null,attempted:true,outcome:'issued'};
    cpuInterventions.push(intervention);
    try {
      const flags=emulator._get_logic_cpu_flags();
      if (typeof flags!=='number' || !Number.isInteger(flags) || flags<0 || flags>3)
        throw new Error('CPU flag telemetry is invalid');
      intervention.flagsAfter=flags;
    } catch (error) { intervention.telemetryError=error.message; }
    logicResetState=`${action}; RAM/VRAM faults disconnected; audio faults unchanged; RAM preserved`;
    setLogicStatus(`${mode===1 ? 'Forced resume attempted' : 'CPU-only reset issued'}. RAM/VRAM faults disconnected; audio faults unchanged; RAM preserved. Recovery is not guaranteed.`);
    stamp(`CPU intervention: ${action}; RAM/VRAM faults disconnected; audio faults unchanged; RAM preserved`);
    refreshLogicMetrics();
    return true;
  }

  function cancelPulse(reason) {
    if (!pendingPulse) return;
    pendingPulse.status='cancelled';
    pendingPulse.reason=reason;
    try {
      const frame=Number(emulator._get_logic_frame());
      pendingPulse.endFrame=Number.isFinite(frame)&&frame>=0?frame:null;
    } catch (_) { pendingPulse.endFrame=null; }
    if (pendingPulse.mode==='address-frames') {
      $('randomiserStatus').textContent=`Work RAM WRITE pulse cancelled: ${reason}; no CPU recovery was attempted.`;
    }
    pendingPulse=null;
  }

  function disconnectAllFaults() {
    if (!started) return false;
    disarmCpuRecovery();
    cancelPulse('all fault domains disconnected');
    selectedPin=null; ramSelectedPin=null; psgSelectedPin=null; fmSelectedPin=null;
    if (momentary) latched=canonical(momentary);
    momentary=null; momentaryRestorePair=null;

    const results=[];
    const note=(domain,result,actual)=>results.push({domain,result,actual});
    const syncVramState=actual=>{
      if (!actual || (actual.modelId!==1 && actual.modelId!==2) ||
          !Number.isInteger(actual.mask) || actual.mask<0 || actual.mask>255 ||
          !Number.isInteger(actual.bridgeA) || !Number.isInteger(actual.bridgeB)) return false;
      vramModelId=actual.modelId;
      vramAddressMask=actual.mask;
      latched=actual.bridgeA>=0&&actual.bridgeA<=7&&actual.bridgeB>=0&&actual.bridgeB<=7&&actual.bridgeA!==actual.bridgeB
        ? canonical([actual.bridgeA,actual.bridgeB]) : null;
      momentary=null; momentaryRestorePair=null; selectedPin=null;
      return true;
    };
    let vramState=null, vramStateUnknown=false;
    if (vramModelApiReady()) {
      try { vramState=emulator._get_vram_fault_model_state(); vramStateUnknown=!vramState; }
      catch (_) { vramStateUnknown=true; }
    }
    const vramActive=vramState
      ? !!(vramState.mask || (vramState.bridgeA>=0 && vramState.bridgeB>=0))
      : vramFaultActive() || vramStateUnknown;
    if (!vramActive) note('VRAM','already off','no configured VRAM fault');
    else {
      let supportStateUnknown=false;
      if (vramModelApiReady()) {
        try { emulator._get_vram_supported_model_mask(); }
        catch (_) { supportStateUnknown=true; }
      }
      if (supportStateUnknown) {
        try {
          // Model 1 identity is supported in every runtime profile and clears the VRAM fault.
          const selectorStatus=emulator._set_vram_fault_model(1,0,-1,-1);
          let actual=null;
          try { actual=emulator._get_vram_fault_model_state(); } catch (_) { /* Keep the result explicitly unverified. */ }
          if (actual) syncVramState(actual);
          const off=actual && !actual.mask && !(actual.bridgeA>=0&&actual.bridgeB>=0);
          note('VRAM',selectorStatus!==0?`clear rejected (${selectorStatus})`:off?'cleared':actual?'clear accepted; fault remains configured':'clear accepted; runtime state unknown',
            actual?`runtime model ${actual.modelId}, ${off?'no fault configured':'fault remains configured'}`:'runtime state unknown');
        } catch (_) {
          let actual=null;
          try { actual=emulator._get_vram_fault_model_state(); } catch (_) { /* Fall through to tracked state. */ }
          if (actual) syncVramState(actual);
          note('VRAM','clear threw',actual
            ? `runtime model ${actual.modelId}, ${actual.mask||(actual.bridgeA>=0&&actual.bridgeB>=0)?'fault remains configured':'no fault configured'}`
            : vramFaultActive()?'tracked fault remains active; runtime state unknown':'tracked fault off; runtime state unknown');
        }
      } else try {
        const cleared=disconnect('all fault domains disconnected');
        let actual=null;
        try { if (vramModelApiReady()) actual=emulator._get_vram_fault_model_state(); } catch (_) { /* Show tracked state below. */ }
        const actualIsRuntime=!!actual;
        actual=actual || currentVramModelState();
        const stillActive=!!(actual.mask || (actual.bridgeA>=0 && actual.bridgeB>=0));
        const result=cleared&&!stillActive
          ? (actualIsRuntime||!vramModelApiReady()?'cleared':'clear accepted; runtime state unknown')
          : 'clear failed';
        note('VRAM',result,
          `${actualIsRuntime?'runtime':'tracked'} model ${actual.modelId}, mask ${actual.mask}, pair ${actual.bridgeA>=0&&actual.bridgeB>=0?`AD${actual.bridgeA}↔AD${actual.bridgeB}`:'none'}`);
      } catch (_) {
        let actual=null;
        try { if (vramModelApiReady()) actual=emulator._get_vram_fault_model_state(); } catch (_) { /* Fall through to tracked values. */ }
        if (actual) syncVramState(actual);
        note('VRAM','clear threw',actual
          ? `runtime model ${actual.modelId}, ${actual.mask||(actual.bridgeA>=0&&actual.bridgeB>=0)?'fault remains configured':'no fault configured'}`
          : vramFaultActive()?'tracked fault remains active; runtime state unknown':'tracked fault off; runtime state unknown');
      }
    }

    let pulseArmed=false, pulseStateUnknown=false;
    try { pulseArmed=typeof emulator._get_logic_pulse_state==='function' && Number(emulator._get_logic_pulse_state())===1; }
    catch (_) { pulseStateUnknown=true; }
    if (!logicActive && !pendingPulse && !pulseArmed && !pulseStateUnknown) note('RAM','already off','no tracked RAM fault');
    else {
      try {
        let cleared;
        if (logicActive) cleared=disconnectLogic({silent:true,pulseReason:'all fault domains disconnected'});
        else {
          const clearStatus=emulator._set_logic_fault(0,0,-1,-1);
          cleared=clearStatus===0;
          if (cleared) cancelPulse('all fault domains disconnected');
        }
        let pulseAfter=false, pulseAfterKnown=false;
        try {
          if (typeof emulator._get_logic_pulse_state==='function') {
            pulseAfter=Number(emulator._get_logic_pulse_state())===1;
            pulseAfterKnown=true;
          }
        } catch (_) { /* A telemetry failure cannot undo the clear attempt. */ }
        const verifiedClear=cleared&&!logicActive&&pulseAfterKnown&&!pulseAfter;
        const ramResult=verifiedClear?'cleared':cleared
          ? (pulseAfter?'clear accepted; pulse remains armed':'clear accepted; pulse state unknown')
          : 'clear failed';
        note('RAM',ramResult,cleared
          ? `no tracked RAM fault; core clear accepted${pulseAfter?'; core pulse remains armed while paused':!pulseAfterKnown?'; core pulse state unverified':''}`
          : `${logicActive?'tracked RAM fault remains active':'tracked RAM state off; core state unverified'}${pulseAfter?'; core pulse remains armed while paused':''}`);
      } catch (_) { note('RAM','clear threw',`${logicActive?'tracked RAM fault remains active':'tracked RAM state off'}; core setter outcome and pulse state unverified while paused`); }
    }

    const clearAudio=(kind)=>{
      const isPsg=kind==='PSG';
      const ready=isPsg?psgDataApiReady():fmDataApiReady();
      const getter=isPsg?emulator?._get_psg_data_bridge_state:emulator?._get_fm_data_bridge_state;
      const bridgeSetter=isPsg?emulator?._set_psg_data_bridge:emulator?._set_fm_data_bridge;
      const maskSetter=isPsg?emulator?._set_psg_data_mask:emulator?._set_fm_data_mask;
      if (!ready) { note(kind,'unavailable','optional runtime API absent'); return; }
      let state=null;
      try { state=getter.call(emulator); } catch (_) { /* Continue with the clear request and report state as unknown. */ }
      if (state && !state.configured) { note(kind,'already off','runtime state reports no configured fault'); return; }
      const observedAudio=()=>{
        try {
          const after=getter.call(emulator);
          return after ? after.configured?'configured fault remains':'no configured fault' : 'runtime state unknown';
        } catch (_) { return 'runtime state unknown'; }
      };
      try {
        const status=state?.dataMask && typeof maskSetter==='function'
          ? maskSetter.call(emulator,0)
          : bridgeSetter.call(emulator,0,-1,-1);
        if (status!==0) { note(kind,`clear rejected (${status})`,observedAudio()); return; }
        let after=null;
        try { after=getter.call(emulator); } catch (_) { /* Setter success remains known; state is not observable. */ }
        note(kind,after ? after.configured?'clear accepted; still configured':'cleared' : 'clear accepted; runtime state unknown',
          after ? after.configured?'configured fault remains':'no configured fault' : 'runtime state unknown');
      } catch (_) { note(kind,'clear threw',observedAudio()); }
    };
    clearAudio('PSG');
    clearAudio('FM');

    const summary=results.map(item=>`${item.domain}: ${item.result} (${item.actual})`).join('; ');
    const allClear=results.every(item=>item.result==='already off'||item.result==='cleared');
    if (!allClear && !paused) pauseToggle();
    const status=`All-domain disconnect ${allClear?'completed':'was incomplete'}. ${summary}. ${allClear?(paused?'Paused state preserved.':'Running state preserved.'):'Emulation paused before the next frame.'} No CPU recovery or full restart was issued; existing memory and chip state may persist.`;
    $('disconnectAllFaultsStatus').textContent=status;
    stamp(status);
    let frame=null;
    try { if (logicApiReady()) { const value=Number(emulator._get_logic_frame()); if(Number.isFinite(value)&&value>=0)frame=value; } }
    catch (_) { /* Disconnect results must still be retained if telemetry is unavailable. */ }
    faultDisconnectActions.push({action:'all-domain-disconnect',frame,results:results.map(item=>({...item}))});
    updateFaultUI(); updateLogicControls(); refreshPsgDataControls(); refreshFmDataControls();
    return allClear;
  }

  function runDisconnectAllFaults() {
    try { disconnectAllFaults(); }
    catch (error) {
      if (!paused) pauseToggle();
      const status=`All-domain disconnect failed unexpectedly (${error.message}); emulation paused before the next frame. Earlier clears may have succeeded; runtime state is unknown. No CPU recovery or full restart was issued.`;
      $('disconnectAllFaultsStatus').textContent=status;
      stamp(status);
      faultDisconnectActions.push({action:'all-domain-disconnect',frame:null,
        results:[{domain:'UNKNOWN',result:'unexpected clear failure',actual:'partial runtime state unknown'}]});
    }
  }

  function startFaultPulse(pair=null) {
    if (!started || typeof emulator?._recover_logic_cpu !== 'function') return;
    const selection=$('logicPulseFrames').value;
    const writeLimited=selection.startsWith('writes:');
    const amount=Number(writeLimited ? selection.slice(7) : selection);
    if (![1,2,4,8].includes(amount)) return;
    const duration=writeLimited ? 1 : amount;
    if (pair) {
      $('logicKind').value='1'; configureLogicLines();
      $('logicAccess').value='2'; // Quick pairs are explicitly labelled write pulses.
      $('logicLineA').value=String(pair[0]); $('logicLineB').value=String(pair[1]);
    }
    if (!applyLogicFault(writeLimited ? amount : null)) return;
    pendingPulse={...logicConfigFromControls(),mode:writeLimited?'affected-writes':'frames',
      ...(writeLimited ? {requestedWrites:amount} : {}),requestedFrames:duration,
      startFrame:Number(emulator._get_logic_frame()),status:'active'};
    faultPulses.push(pendingPulse);
    const length=writeLimited ? `up to ${amount} affected write${amount===1?'':'s'} (one-frame maximum)` : `${duration} emulated frame${duration===1?'':'s'}`;
    setLogicStatus(`RAM pulse active for ${length}; then disconnect and force resume.${paused?' Paused: press Resume to advance.':''}`);
  }

  function addressFramePairPreflight(pair) {
    let pulseState, pulseStateAvailable, vramState, startFrame;
    try {
      if (!started || !logicApiReady()) throw new Error('Work RAM fault APIs are unavailable');
      if (!Array.isArray(pair) || pair.length!==2 || !pair.every(Number.isInteger) ||
          pair[0]<10 || pair[0]>14 || pair[1]<10 || pair[1]>14 || pair[0]===pair[1])
        throw new Error('choose two distinct A11–A15 lines');
      if (logicActive) throw new Error('Work RAM fault active');
      if (pendingPulse) throw new Error('RAM pulse already active');
      if (momentary) throw new Error('held VRAM bridge active');
      if (vramModelApiReady()) {
        vramState=emulator._get_vram_fault_model_state();
      } else if (vramMaskApiReady() && typeof emulator._get_vram_short_a==='function' &&
                 typeof emulator._get_vram_short_b==='function') {
        vramState={mask:Number(emulator._get_vram_address_mask()),
          bridgeA:Number(emulator._get_vram_short_a()),bridgeB:Number(emulator._get_vram_short_b())};
      } else throw new Error('VRAM runtime state unavailable');
      pulseStateAvailable=typeof emulator._get_logic_pulse_state==='function';
      if (typeof emulator._arm_logic_write_pulse==='function' && !pulseStateAvailable)
        throw new Error('RAM pulse state is unreadable');
      pulseState=pulseStateAvailable ? emulator._get_logic_pulse_state() : 0;
      if (!Number.isInteger(pulseState) || ![0,2,3,4].includes(pulseState)) throw new Error('RAM pulse state active or unreadable');
      if (!vramState || !Number.isInteger(vramState.mask) || !Number.isInteger(vramState.bridgeA) ||
          !Number.isInteger(vramState.bridgeB)) throw new Error('VRAM runtime state unavailable');
      if (vramState.mask<0 || vramState.mask>255) throw new Error('VRAM runtime state unavailable');
      const bridgeOff=vramState.bridgeA===-1 && vramState.bridgeB===-1;
      const bridgeValid=vramState.bridgeA>=0 && vramState.bridgeA<8 &&
        vramState.bridgeB>=0 && vramState.bridgeB<8 && vramState.bridgeA!==vramState.bridgeB;
      if (!bridgeOff && !bridgeValid) throw new Error('VRAM runtime state unavailable');
      if (vramState.mask || bridgeValid) throw new Error('VRAM fault active');
      startFrame=Number(emulator._get_logic_frame());
      if (!Number.isFinite(startFrame) || startFrame<0) throw new Error('RAM frame state unavailable');
      return {ok:true,startFrame};
    } catch (error) { return {ok:false,error}; }
  }

  function startAddressFramePulse(pair) {
    const preflight=addressFramePairPreflight(pair);
    if (!preflight.ok) {
      const error=preflight.error;
      setAddressFramePulseStatus(`Work RAM WRITE pulse refused: ${error.message}. No fault was applied.`);
      return false;
    }
    const startFrame=preflight.startFrame;
    const [a,b]=canonical(pair);
    const pulse={kind:1,access:2,a,b,mode:'address-frames',requestedFrames:8,
      startFrame,status:'active',cpuRecoveryAttempted:false,recoveryAccepted:false};
    try {
      if (!applyLogicFault(null,{kind:1,access:2,a,b})) {
        $('randomiserStatus').textContent=$('logicStatus').textContent;
        return false;
      }
    } catch (error) {
      pulse.status='incomplete'; pulse.releaseReason='unknown';
      pendingPulse=null; faultPulses.push(pulse);
      logicActive=true; activeRamConfiguration={type:'line-pair',kind:1,access:2,a,b};
      if (!paused) pauseToggle();
      setAddressFramePulseStatus(`Work RAM WRITE pulse outcome is unknown (${error.message}); emulation paused. No CPU recovery was attempted.`);
      stamp('Work RAM WRITE pulse outcome unknown; emulation paused; no CPU recovery attempted');
      updateLogicControls();
      return false;
    }
    pendingPulse=pulse;
    faultPulses.push(pendingPulse);
    setAddressFramePulseStatus(`Work RAM WRITE bridge active on A${a+1} ↔ A${b+1} for 8 emulated frames; automatic disconnect, no CPU recovery.`);
    stamp(`Work RAM WRITE bridge: A${a+1} ↔ A${b+1}, 8 emulated frames; no CPU recovery`);
    updateLogicControls();
    return true;
  }

  function finishFaultPulse() {
    if (!pendingPulse) return;
    if (pendingPulse.mode==='address-frames') {
      finishAddressFramePulse();
      return;
    }
    const frame=Number(emulator._get_logic_frame());
    if (frame-pendingPulse.startFrame<pendingPulse.requestedFrames) return;
    const pulse=pendingPulse;
    pendingPulse=null; // Explicit completion must not be marked cancelled by recovery.
    pulse.endFrame=frame;
    pulse.status='completed';
    pulse.releaseReason=pulse.mode==='affected-writes' && emulator._get_logic_pulse_state()===2
      ? 'affected-write-limit' : 'frame-limit';
    if (pulse.mode==='affected-writes') pulse.corePulseState=emulator._get_logic_pulse_state();
    pulse.readCount=Number(emulator._get_logic_reads());
    pulse.writeCount=Number(emulator._get_logic_writes());
    pulse.cpuFlagsAtEnd=Number(emulator._get_logic_cpu_flags());
    const interventionIndex=cpuInterventions.length;
    pulse.recoveryAccepted=recoverLogicCPU(1)===true;
    if (pulse.recoveryAccepted) {
      pulse.interventionIndex=interventionIndex;
      if (pulse.mode==='affected-writes') {
        const ending=pulse.releaseReason==='affected-write-limit' ? 'write limit reached' : 'one-frame cutoff reached';
        setLogicStatus(`Pulse ended: ${pulse.writeCount} affected write${pulse.writeCount===1?'':'s'}; ${ending}. Fault disconnected; force resume attempted.`);
      }
    }
  }

  function finishAddressFramePulse() {
    const pulse=pendingPulse;
    let frame,state,stateAvailable,reads,writes,flags;
    try {
      frame=Number(emulator._get_logic_frame());
      if (!Number.isFinite(frame) || frame<0) throw new Error('RAM frame expiry metadata is unavailable');
      if (frame-pulse.startFrame<pulse.requestedFrames) return;
      stateAvailable=typeof emulator._get_logic_pulse_state==='function';
      state=stateAvailable ? Number(emulator._get_logic_pulse_state()) : null;
      reads=Number(emulator._get_logic_reads());
      writes=Number(emulator._get_logic_writes());
      flags=Number(emulator._get_logic_cpu_flags());
      if ((stateAvailable && ![0,2,3,4].includes(state)) || ![reads,writes,flags].every(Number.isFinite))
        throw new Error('pulse state or counters are unknown');
      const status=emulator._set_logic_fault(0,0,-1,-1);
      const stateAfter=stateAvailable ? Number(emulator._get_logic_pulse_state()) : 0;
      if (status!==0 || (stateAvailable && ![0,2,3,4].includes(stateAfter)))
        throw new Error(`pulse clear unverified (status ${status})`);
    } catch (error) {
      pulse.status='incomplete'; pulse.endFrame=null; pulse.releaseReason='unknown';
      if (stateAvailable) pulse.corePulseState=Number.isInteger(state)?state:null;
      pulse.cpuRecoveryAttempted=false; pulse.recoveryAccepted=false;
      pendingPulse=null;
      logicActive=true; activeRamConfiguration={type:'line-pair',kind:1,access:2,a:pulse.a,b:pulse.b};
      if (!paused) pauseToggle();
      setAddressFramePulseStatus(`Work RAM WRITE pulse release is unknown (${error.message}); emulation paused. No CPU recovery was attempted.`);
      stamp('Work RAM WRITE pulse release unknown; emulation paused; no CPU recovery attempted');
      return;
    }
    pulse.endFrame=frame; pulse.status='completed';
    pulse.releaseReason='frame-limit';
    if (stateAvailable) pulse.corePulseState=state;
    pulse.readCount=reads; pulse.writeCount=writes; pulse.cpuFlagsAtEnd=flags;
    pulse.cpuRecoveryAttempted=false; pulse.recoveryAccepted=false;
    pendingPulse=null; logicActive=false; activeRamConfiguration=null; logicStatsRetained=true;
    if (lastLogicExperiment) {
      lastLogicExperiment.disconnectedAtFrame=frame; lastLogicExperiment.readCount=reads;
      lastLogicExperiment.writeCount=writes; lastLogicExperiment.cpuFlags=flags;
    }
    setAddressFramePulseStatus(`Work RAM WRITE bridge ended after 8 emulated frames and ${writes} affected writes; fault disconnected automatically. No CPU recovery was attempted.`);
    stamp(`Work RAM WRITE bridge ended after 8 emulated frames; ${writes} affected writes; no CPU recovery attempted`);
    updateLogicControls();
  }

  function setupAddressFramePairButtons() {
    const pairs=$('ramFramePairs');
    for (let a=10;a<15;a++) for (let b=a+1;b<15;b++) {
      const button=document.createElement('button');
      button.type='button'; button.disabled=true;
      button.dataset.ramFramePair=`${a},${b}`;
      button.textContent=`A${a+1} ↔ A${b+1}`;
      button.setAttribute('aria-label',`Write-only bridge A${a+1} and A${b+1} for eight emulated frames`);
      let suppressClick=false;
      button.addEventListener('pointerdown',event=>{
        if ($('ramWriteMode').value!=='hold' || event.button!==0) return;
        suppressClick=true;
        if (startAddressFrameHold([a,b],{type:'pointer',pointerId:event.pointerId,button})) {
          try { button.setPointerCapture(event.pointerId); } catch (_) { /* release remains covered by window blur */ }
        }
      });
      const releasePointer=event=>{
        if (event.type!=='pointerup') suppressClick=false;
        if (ownedAddressHold?.type==='pointer' && ownedAddressHold.pointerId===event.pointerId)
          endAddressFrameHold('pointer',event.pointerId);
      };
      button.addEventListener('pointerup',releasePointer);
      button.addEventListener('pointercancel',releasePointer);
      button.addEventListener('lostpointercapture',releasePointer);
      button.addEventListener('keydown',event=>{
        if ($('ramWriteMode').value!=='hold' || !['Space','Enter'].includes(event.code)) return;
        event.preventDefault();
        if (event.repeat || keyboardHeld) return;
        if (startAddressFrameHold([a,b],{type:'keyboard',code:event.code}))
          keyboardHeld={code:event.code,target:'WRAM',pair:[a,b],restore:null};
      });
      button.addEventListener('click',()=>{
        if (suppressClick) { suppressClick=false; return; }
        if ($('ramWriteMode').value==='pulse') startAddressFramePulse([a,b]);
      });
      pairs.append(button);
    }
    $('ramWriteMode').addEventListener('change',()=>{
      if (ownedAddressHold && !endAddressFrameHold(ownedAddressHold.type,ownedAddressHold.pointerId)) {
        $('ramWriteMode').value='hold';
        setAddressFramePulseStatus('Mode change refused because the held RAM fault could not be disconnected.');
      }
    });
  }

  function startAddressFrameHold(pair,source) {
    const [a,b]=canonical(pair), key=`${a},${b}`;
    if (ownedAddressHold) return false;
    const preflight=addressFramePairPreflight(pair);
    if (!preflight.ok) {
      setAddressFramePulseStatus(`Work RAM WRITE Hold refused: ${preflight.error.message}. No fault was applied.`);
      return false;
    }
    try {
      if (!applyLogicFault(null,{kind:1,access:2,a,b})) return false;
      ownedAddressHold={key,...source};
      setAddressFramePulseStatus(`Work RAM WRITE bridge held on A${a+1} ↔ A${b+1}; release the control to disconnect. No CPU recovery will be attempted.`);
      updateLogicControls();
      return true;
    } catch(error) {
      logicActive=true;activeRamConfiguration={type:'line-pair',kind:1,access:2,a,b};
      if (!paused) pauseToggle();
      setAddressFramePulseStatus(`Work RAM WRITE Hold outcome is unknown (${error.message}); emulation paused. No CPU recovery was attempted.`);
      updateLogicControls();
      return false;
    }
  }

  function endAddressFrameHold(type,pointerId=undefined) {
    const held=ownedAddressHold;
    if (!held || held.type!==type || (type==='pointer' && held.pointerId!==pointerId)) return false;
    const config=activeRamConfiguration;
    if (!logicActive || !config || config.type!=='line-pair' || config.kind!==1 || config.access!==2 ||
        `${config.a},${config.b}`!==held.key) { ownedAddressHold=null; return false; }
    let released;
    try { released=disconnectLogic(); }
    catch(error) {
      if (keyboardHeld?.target==='WRAM') keyboardHeld=null;
      reportKeyboardReleaseFailure('WRAM',error.message);
      return false;
    }
    if (released) {
      if (keyboardHeld?.target==='WRAM') keyboardHeld=null;
      if (type==='pointer' && held.button?.hasPointerCapture?.(pointerId)) {
        try { held.button.releasePointerCapture(pointerId); } catch (_) { /* Pointerup may have released capture already. */ }
      }
    }
    else {
      if (!paused) pauseToggle();
      setAddressFramePulseStatus('Work RAM WRITE Hold release was not confirmed; emulation paused. The fault may remain active.');
    }
    return released;
  }

  function setupPulseButtons() {
    for (let a=0;a<14;a++) {
      const button=document.createElement('button');
      button.type='button'; button.disabled=true;
      button.dataset.ramPulse=String(a);
      button.textContent=`A${a+1} ↔ A${a+2}`;
      button.setAttribute('aria-label',`Pulse address A${a+1} and A${a+2} on writes`);
      button.addEventListener('click',()=>startFaultPulse([a,a+1]));
      $('logicPulsePairs').append(button);
    }
  }

  function resetLogicSelection() {
    $('logicKind').value='1'; $('logicAccess').value='1';
    configureLogicLines();
  }

  function circuitPulseIsArmed() {
    if (pendingPulse) return true;
    if (!writePulseApiReady()) return false;
    try { return Number(emulator._get_logic_pulse_state())===1; }
    catch (_) { return true; }
  }

  function currentCircuitConfiguration() {
    const api=window.VRAMpageCircuitConfig;
    if (!api) throw new Error('Circuit configuration support is unavailable.');
    if (momentary) throw new Error('Release the momentary VRAM bridge before saving a configuration.');
    if (circuitPulseIsArmed()) throw new Error('Wait for or cancel the active RAM pulse before saving a configuration.');
    if (logicActive && !activeRamConfiguration)
      throw new Error('The active RAM fault settings are unavailable; no file was created.');
    let psg={pair:null,dataMask:0}, fm={pair:null,dataMask:0};
    if (psgDataApiReady()) {
      const state=currentPsgDataState();
      if (!state) throw new Error('PSG state is unavailable; no file was created.');
      if (state.configured) psg={pair:state.bridgeA>=0&&state.bridgeB>=0?canonical([state.bridgeA,state.bridgeB]):null,
        dataMask:Number.isInteger(state.dataMask)?state.dataMask:0};
    }
    if (fmDataApiReady()) {
      const state=currentFmDataState();
      if (!state) throw new Error('FM state is unavailable; no file was created.');
      if (state.configured) fm={pair:state.bridgeA>=0&&state.bridgeB>=0?canonical([state.bridgeA,state.bridgeB]):null,
        dataMask:Number.isInteger(state.dataMask)?state.dataMask:0};
    }
    let pair=canonical(actualPair());
    if (vramModelApiReady()) {
      let state;
      try { state=emulator._get_vram_fault_model_state(); }
      catch (_) { throw new Error('VRAM selector state is unavailable; no file was created.'); }
      const selectedPair=state&&state.bridgeA>=0&&state.bridgeB>=0
        ? canonical([state.bridgeA,state.bridgeB]) : null;
      if (!state || state.modelId!==vramModelId || state.mask!==vramAddressMask ||
          JSON.stringify(selectedPair)!==JSON.stringify(pair))
        throw new Error('VRAM selector state differs from the app state; no file was created.');
    }
    return api.validate({format:api.format,schemaVersion:api.version,configuration:{
      vram:{modelId:vramModelId,mask:vramAddressMask,pair},
      ram:logicActive?{...activeRamConfiguration}:null,psg,fm
    }});
  }

  function circuitConfigSummary(config) {
    const c=config.configuration;
    const vram=c.vram.pair?`VRAM AD${c.vram.pair[0]}↔AD${c.vram.pair[1]}`
      :c.vram.mask?`VRAM mask 0x${c.vram.mask.toString(16).toUpperCase()}`:'VRAM identity';
    const model=c.vram.modelId===2?'transaction':'frame projection';
    const ram=!c.ram?'RAM off':c.ram.type==='address-mask'
      ?`RAM address mask 0x${c.ram.mask.toString(16).toUpperCase()}, access ${c.ram.access}`
      :`RAM ${c.ram.kind===1?'address':'data'} pair ${c.ram.a}↔${c.ram.b}, access ${c.ram.access}`;
    const audio=(name,target)=>target.pair?`${name} D${target.pair[0]}↔D${target.pair[1]}`
      :target.dataMask?`${name} ${maskLineNames(target.dataMask)} low`:`${name} off`;
    return `${vram} (${model})\n${ram}\n${audio('PSG',c.psg)}\n${audio('FM',c.fm)}`;
  }

  function refreshCircuitConfigControls() {
    $('circuitConfigApply').disabled=!stagedCircuitConfiguration || !started || circuitConfigLoading;
    $('circuitConfigCancel').disabled=!stagedCircuitConfiguration && !circuitConfigLoading;
    const preview=$('circuitConfigPreview');
    preview.hidden=!stagedCircuitConfiguration;
    preview.textContent=stagedCircuitConfiguration?circuitConfigSummary(stagedCircuitConfiguration):'';
  }

  function stageCircuitConfigurationFile(file) {
    if (!file) return;
    const generation=++circuitConfigLoadGeneration;
    circuitConfigLoading=true;
    $('circuitConfigStatus').textContent=stagedCircuitConfiguration
      ? 'Reading selected file. The previous valid preview is retained; Apply is disabled until reading finishes.'
      : 'Reading selected file. Nothing has been applied.';
    refreshCircuitConfigControls();
    Promise.resolve().then(async()=>{
      if (file.size>32768) throw new Error('Circuit configuration must be at most 32 KB.');
      const parsed=window.VRAMpageCircuitConfig.parse(await file.text());
      if (generation!==circuitConfigLoadGeneration) return;
      stagedCircuitConfiguration=parsed;
      $('circuitConfigStatus').textContent='Preview loaded. Nothing has been applied; choose Apply when ready.';
    }).catch(error=>{
      if (generation!==circuitConfigLoadGeneration) return;
      $('circuitConfigStatus').textContent=`Configuration not staged: ${error.message}${stagedCircuitConfiguration?' The previous valid preview is still available.':''}`;
    }).finally(()=>{
      if (generation!==circuitConfigLoadGeneration) return;
      circuitConfigLoading=false;
      refreshCircuitConfigControls();
    });
  }

  function downloadCircuitConfiguration() {
    let config;
    try { config=currentCircuitConfiguration(); }
    catch (error) { $('circuitConfigStatus').textContent=error.message; return; }
    const blob=new Blob([JSON.stringify(config,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url; link.download='vram-page-md-circuit-v2.json';
    document.body.append(link); link.click(); link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('circuitConfigStatus').textContent='Circuit configuration downloaded. ROM and execution history are not included.';
  }

  function sameCircuitRam(a,b) { return JSON.stringify(a)===JSON.stringify(b); }

  function audioTargetActive(target) { return !!(target&&(target.pair||target.dataMask)); }

  function circuitBridgeNeedsChange(target,state,available) {
    if (!available) return audioTargetActive(target);
    if (!state) return true;
    const actualMask=Number.isInteger(state.dataMask)?state.dataMask:0;
    const actualPair=state.configured&&state.bridgeA>=0&&state.bridgeB>=0
      ?canonical([state.bridgeA,state.bridgeB]):null;
    const targetPair=target?.pair||null;
    return actualMask!==(target?.dataMask||0) ||
      !((actualPair===null&&targetPair===null)||samePair(actualPair,targetPair));
  }

  function setPsgCircuitTarget(target) {
    if (target.dataMask) return setPsgDataMask(target.dataMask);
    if (target.pair) return setPsgDataBridge(true,target.pair);
    return setPsgDataBridge(false);
  }

  function setFmCircuitTarget(target) {
    if (target.dataMask) return setFmDataMask(target.dataMask);
    if (target.pair) return setFmDataBridge(true,target.pair);
    return setFmDataBridge(false);
  }

  function preflightCircuitConfiguration(config) {
    if (!started || !emulator) return 'Load a ROM before applying a circuit configuration.';
    if (momentary) return 'Release the momentary VRAM bridge before applying a configuration.';
    if (circuitPulseIsArmed()) return 'Wait for or cancel the active RAM pulse before applying a configuration.';
    if (logicActive && (!activeRamConfiguration || !logicApiReady()))
      return 'The active RAM fault cannot be safely identified or disconnected.';
    if (logicActive && vramFaultActive()) return 'RAM and VRAM faults are both active; no setters were called.';
    const c=config.configuration;
    let vram;
    try { vram=validateVramModel(c.vram.modelId,c.vram.mask,c.vram.pair); }
    catch (_) { return 'VRAM capability state is unavailable; no setters were called.'; }
    if (!vram.ok) return vram.message;
    if (c.ram && !logicApiReady()) return 'This core cannot safely apply and clear the requested RAM model.';
    if (c.ram?.type==='address-mask' && !addressMaskApiReady())
      return 'This core cannot apply the requested RAM address-mask model.';
    for (const [name,target,ready,getState] of [
      ['PSG',c.psg,psgDataApiReady,currentPsgDataState],
      ['FM',c.fm,fmDataApiReady,currentFmDataState]
    ]) {
      const maskReady=name==='PSG'?psgDataMaskApiReady():fmDataMaskApiReady();
      if (!ready()) { if (audioTargetActive(target)) return `This core does not support the requested ${name} bridge.`; continue; }
      const state=getState();
      if (!state) return `${name} runtime state is unavailable; no setters were called.`;
      if (audioTargetActive(target) && !state.supported) return `The requested ${name} bridge is unsupported in this system profile.`;
      if (target?.dataMask && !maskReady) return `This core does not support the requested ${name} input cuts.`;
    }
    return null;
  }

  function circuitTargetsMatch(config) {
    const c=config.configuration;
    if (c.vram.modelId!==vramModelId || c.vram.mask!==vramAddressMask ||
        JSON.stringify(c.vram.pair)!==JSON.stringify(canonical(actualPair()))) return false;
    if (!sameCircuitRam(c.ram,logicActive?activeRamConfiguration:null)) return false;
    return !circuitBridgeNeedsChange(c.psg,psgDataApiReady()?currentPsgDataState():null,psgDataApiReady()) &&
      !circuitBridgeNeedsChange(c.fm,fmDataApiReady()?currentFmDataState():null,fmDataApiReady());
  }

  function syncCircuitSelectors(config) {
    const c=config.configuration;
    $('vramModel').value=String(c.vram.modelId);
    $('vramMode').value=c.vram.pair?'bridge':'disconnect';
    if (c.ram) {
      $('logicKind').value=String(c.ram.type==='address-mask'?1:c.ram.kind);
      $('logicAccess').value=String(c.ram.access); configureLogicLines();
      if (c.ram.type==='line-pair') {
        $('logicLineA').value=String(c.ram.a); $('logicLineB').value=String(c.ram.b);
      }
    }
    if (c.psg.pair) {
      $('psgBridgeA').value=String(c.psg.pair[0]); $('psgBridgeB').value=String(c.psg.pair[1]);$('psgLegMode').value='bridge';
    } else $('psgLegMode').value=c.psg.dataMask?'ground':'bridge';
    if (c.fm.pair) {
      $('fmBridgeA').value=String(c.fm.pair[0]); $('fmBridgeB').value=String(c.fm.pair[1]);$('fmLegMode').value='bridge';
    } else $('fmLegMode').value=c.fm.dataMask?'ground':'bridge';
    updateFaultUI(); updateLogicControls(); refreshPsgDataControls(); refreshFmDataControls();
  }

  function pauseAfterCircuitApplyFailure(domain) {
    if (!paused) pauseToggle();
    const ram=logicActive?JSON.stringify(activeRamConfiguration):'off';
    const psg=psgDataApiReady()?currentPsgDataState():null;
    const fm=fmDataApiReady()?currentFmDataState():null;
    let vram=null;
    if (vramModelApiReady()) {
      try { vram=emulator._get_vram_fault_model_state(); } catch (_) { /* Report tracked state below. */ }
    }
    const vramDescription=vram
      ? `runtime VRAM model ${vram.modelId}, mask ${vram.mask}, pair ${JSON.stringify(vram.bridgeA>=0&&vram.bridgeB>=0?canonical([vram.bridgeA,vram.bridgeB]):null)}`
      : `tracked VRAM model ${vramModelId}, mask ${vramAddressMask}, pair ${JSON.stringify(canonical(actualPair()))}`;
    const bridgeDescription=(state,name)=>state
      ? `${name} ${state.configured?(Number(state.dataMask||0)?`${maskLineNames(Number(state.dataMask))} low`:`D${state.bridgeA}↔D${state.bridgeB}`):'off'}`
      : `${name} state unavailable`;
    const actual=`Observed state: ${vramDescription}; tracked RAM ${ram}; ${bridgeDescription(psg,'PSG')}; ${bridgeDescription(fm,'FM')}.`;
    const message=`Apply stopped at ${domain}; earlier settings may have changed. ${actual} The staged file is retained and emulation is paused.`;
    $('circuitConfigStatus').textContent=message; stamp(message);
    updateFaultUI(); updateLogicControls(); refreshPsgDataControls(); refreshFmDataControls();
  }

  function applyStagedCircuitConfiguration() {
    if (circuitConfigLoading) {
      $('circuitConfigStatus').textContent='Wait for the selected configuration file to finish reading before Apply.';
      return false;
    }
    const config=stagedCircuitConfiguration;
    if (!config) return false;
    disarmCpuRecovery();
    let error;
    try { error=preflightCircuitConfiguration(config); }
    catch (_) { error='Runtime state could not be read; no setters were called.'; }
    if (error) { $('circuitConfigStatus').textContent=`Apply refused before mutation: ${error}`; return false; }
    let alreadyMatches;
    try { alreadyMatches=circuitTargetsMatch(config); }
    catch (_) { $('circuitConfigStatus').textContent='Apply refused before mutation: runtime state could not be read.'; return false; }
    if (alreadyMatches) {
      $('circuitConfigStatus').textContent='Configuration already matches. No setters were called; live counters were preserved.';
      stagedCircuitConfiguration=null; refreshCircuitConfigControls(); return true;
    }
    const c=config.configuration;
    let currentPsg,currentFm;
    try {
      currentPsg=psgDataApiReady()?currentPsgDataState():null;
      currentFm=fmDataApiReady()?currentFmDataState():null;
    } catch (_) {
      $('circuitConfigStatus').textContent='Apply refused before mutation: runtime state could not be read.';
      return false;
    }
    const changePsg=circuitBridgeNeedsChange(c.psg,currentPsg,psgDataApiReady());
    const changeFm=circuitBridgeNeedsChange(c.fm,currentFm,fmDataApiReady());
    const changeRam=!sameCircuitRam(c.ram,logicActive?activeRamConfiguration:null);
    const changeVram=c.vram.modelId!==vramModelId || c.vram.mask!==vramAddressMask ||
      JSON.stringify(c.vram.pair)!==JSON.stringify(canonical(actualPair()));
    const vramActive=!!(c.vram.mask||c.vram.pair);

    const applyRamTarget=()=>{
      if (!changeRam) return true;
      if (!c.ram) return disconnectLogic({silent:true});
      if (c.ram.type==='address-mask') return applyAddressMask(c.ram.mask,c.ram.access);
      return applyLogicFault(null,{kind:c.ram.kind,access:c.ram.access,a:c.ram.a,b:c.ram.b});
    };
    let currentDomain='configuration';
    let mutationStarted=false;
    try {
    if (vramActive) {
      if (changeVram) { currentDomain='VRAM'; mutationStarted=true; }
      if (changeVram && !applyVramModel(c.vram.modelId,c.vram.mask,c.vram.pair,'Circuit configuration applied')) {
        pauseAfterCircuitApplyFailure('VRAM'); return false;
      }
      if (changeRam) { currentDomain='RAM'; mutationStarted=true; }
      if (!applyRamTarget()) { pauseAfterCircuitApplyFailure('RAM disconnect'); return false; }
    } else if (c.ram) {
      // Let the established RAM handoff own VRAM clearing and rollback first.
      if (changeRam) { currentDomain='RAM'; mutationStarted=true; }
      if (!applyRamTarget()) { pauseAfterCircuitApplyFailure('RAM'); return false; }
      const vramStillDiffers=c.vram.modelId!==vramModelId || vramAddressMask!==0 || actualPair()!==null;
      if (vramStillDiffers) { currentDomain='VRAM model'; mutationStarted=true; }
      if (vramStillDiffers && !applyVramModel(c.vram.modelId,0,null,'Circuit configuration applied')) {
        pauseAfterCircuitApplyFailure('VRAM model'); return false;
      }
    } else {
      if (changeVram) { currentDomain='VRAM model'; mutationStarted=true; }
      if (changeVram && !applyVramModel(c.vram.modelId,0,null,'Circuit configuration applied')) {
        pauseAfterCircuitApplyFailure('VRAM model'); return false;
      }
      if (changeRam) { currentDomain='RAM disconnect'; mutationStarted=true; }
      if (!applyRamTarget()) { pauseAfterCircuitApplyFailure('RAM disconnect'); return false; }
    }
    if (changePsg) { currentDomain='PSG'; mutationStarted=true; }
    if (changePsg && !setPsgCircuitTarget(c.psg)) {
      pauseAfterCircuitApplyFailure('PSG'); return false;
    }
    if (changeFm) { currentDomain='FM'; mutationStarted=true; }
    if (changeFm && !setFmCircuitTarget(c.fm)) {
      pauseAfterCircuitApplyFailure('FM'); return false;
    }
    syncCircuitSelectors(config);
    stagedCircuitConfiguration=null;
    $('circuitConfigStatus').textContent='Configuration applied. Disconnecting a bridge does not repair previous chip or memory state.';
    refreshCircuitConfigControls(); stamp('Versioned circuit configuration applied.');
    return true;
    } catch (failure) {
      if (mutationStarted) pauseAfterCircuitApplyFailure(`${currentDomain} setter/runtime error`);
      else $('circuitConfigStatus').textContent=`Apply refused before mutation: ${failure?.message||'runtime state could not be read'}.`;
      return false;
    }
  }

  function setupCircuitConfigurationControls() {
    $('circuitConfigDownload').addEventListener('click',downloadCircuitConfiguration);
    $('circuitConfigFileLabel').addEventListener('keydown',event=>{
      if (event.key==='Enter' || event.key===' ') { event.preventDefault(); $('circuitConfigFile').click(); }
    });
    $('circuitConfigFile').addEventListener('change',event=>{
      stageCircuitConfigurationFile(event.target.files?.[0]); event.target.value='';
    });
    $('circuitConfigApply').addEventListener('click',applyStagedCircuitConfiguration);
    $('circuitConfigCancel').addEventListener('click',()=>{
      ++circuitConfigLoadGeneration;
      circuitConfigLoading=false;
      stagedCircuitConfiguration=null;
      $('circuitConfigStatus').textContent='Staged configuration discarded and pending file read canceled; no core settings changed.';
      refreshCircuitConfigControls();
    });
    refreshCircuitConfigControls();
  }

  function setupExperimentComparison() {
    const slots=[null,null];
    const generations=[0,0];
    const status=$('compareStatus'), output=$('compareOutput');
    for (const [label,input] of [['compareFileALabel','compareFileA'],['compareFileBLabel','compareFileB']])
      $(label).addEventListener('keydown',event=>{
        if(event.key==='Enter'||event.key===' ') { event.preventDefault(); $(input).click(); }
      });
    function render() {
      output.replaceChildren();
      if (!slots[0] || !slots[1]) return;
      const table=document.createElement('table');
      const head=document.createElement('thead'), header=document.createElement('tr');
      for (const label of ['Recorded field','Export A','Export B','Assessment']) {
        const cell=document.createElement('th'); cell.scope='col'; cell.textContent=label; header.append(cell);
      }
      head.append(header); table.append(head);
      const body=document.createElement('tbody');
      for (const row of window.VRAMpageExperimentComparison.compare(slots[0],slots[1])) {
        const tr=document.createElement('tr');
        for (const value of [row.label,row.a,row.b,row.status]) {
          const cell=document.createElement('td'); cell.textContent=value; tr.append(cell);
        }
        body.append(tr);
      }
      table.append(body); output.append(table);
      status.textContent='Both exports loaded. Unknown means a value is absent, invalid, or unavailable. Long values are shortened.';
    }
    for (let i=0;i<2;i++) $(i?'compareFileB':'compareFileA').addEventListener('change',event=>{
      const file=event.target.files?.[0]; event.target.value='';
      const generation=++generations[i];
      if (!file) return;
      slots[i]=null; output.replaceChildren();
      status.textContent=`Reading export ${i?'B':'A'} locally…`;
      Promise.resolve().then(async()=>{
        if (file.size>window.VRAMpageExperimentComparison.MAX_BYTES) throw new Error('Experiment export must be at most 256 KB.');
        const parsed=window.VRAMpageExperimentComparison.parse(await file.text());
        if (generation!==generations[i]) return;
        slots[i]=parsed;
        status.textContent=`Export ${i?'B':'A'} loaded locally.`;
        render();
      }).catch(error=>{
        if (generation!==generations[i]) return;
        slots[i]=null;
        status.textContent=`Export ${i?'B':'A'} was not loaded: ${error.message}`;
      });
    });
    $('compareCancel').addEventListener('click',()=>{
      generations[0]++; generations[1]++; slots[0]=slots[1]=null;
      output.replaceChildren(); status.textContent='Comparison cleared; pending reads canceled.';
    });
  }

  async function sha256Hex(bytes) {
    if (!window.crypto?.subtle) return null;
    const digest=await window.crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,'0')).join('');
  }

  async function downloadExperimentJSON() {
    const exportIdentity=romIdentity;
    let romSha256=null;
    try { romSha256=await (exportIdentity?.hashPromise ?? Promise.resolve(null)); } catch (_) { /* Hashing failure never blocks emulation. */ }
    if (exportIdentity!==romIdentity) throw new Error('ROM changed while preparing export; download canceled.');
    if (!started || !emulator) throw new Error('Cartridge activation is uncertain; restart the last accepted cartridge before exporting.');
    const currentFrame=logicApiReady() ? Number(emulator._get_logic_frame()) || 0 : 0;
    const coreReads=logicApiReady() ? Number(emulator._get_logic_reads()) || 0 : 0;
    const coreWrites=logicApiReady() ? Number(emulator._get_logic_writes()) || 0 : 0;
    const reads=!logicActive && logicStatsRetained && lastLogicExperiment ? lastLogicExperiment.readCount : coreReads;
    const writes=!logicActive && logicStatsRetained && lastLogicExperiment ? lastLogicExperiment.writeCount : coreWrites;
    const runtimeVramState=vramModelApiReady()?currentVramModelState():null;
    const psgState=currentPsgDataState();
    const fmState=currentFmDataState();
    const transactionCounts=runtimeVramState?.lastFrameCounts
      ? {...runtimeVramState.lastFrameCounts} : null;
    const data={
      schemaVersion:1,
      build:{...buildInfo},
      modelVersion:'0.4.1-experimental',
      vramFault:{kind:vramAddressMask?'address-stuck-low':actualPair()?'address-bridge':'none',
        addressMask:vramAddressMask,lines:vramLines(vramAddressMask),bridge:actualPair()?[...actualPair()]:null},
      vramAddressLineChanges:vramAddressLineChanges.map(entry=>({...entry})),
      corePin:CORE_PIN,
      addressLineChanges:addressLineChanges.map(entry=>({...entry})),
      faultPulses:faultPulses.map(entry=>({...entry})),
      cpuInterventions:cpuInterventions.map(entry=>({...entry})),
      faultDisconnects:faultDisconnectActions.map(entry=>({...entry,results:entry.results.map(result=>({...result}))})),
      rom:{name:exportIdentity?.name || null,sha256:romSha256},
      logicFault:lastLogicExperiment ? {...lastLogicExperiment} : null,
      faultActive:logicActive,
      resetState:logicResetState,
      currentFrame,readCount:reads,writeCount:writes,
      cpuFlags:logicApiReady() ? Number(emulator._get_logic_cpu_flags()) || 0 : null,
      logic:{schemaVersion:1,modelVersion:'work-ram-transaction-v1',available:logicApiReady(),active:logicActive,
        fault:lastLogicExperiment ? {...lastLogicExperiment} : null,
        readCount:reads,writeCount:writes,currentFrame,
        cpuFlags:logicApiReady() ? Number(emulator._get_logic_cpu_flags()) || 0 : null},
      vramTransaction:{schemaVersion:1,available:!!runtimeVramState,
        modelId:runtimeVramState?.modelId ?? 1,
        modelVersion:runtimeVramState?.modelVersion ?? 'frame-projection-v1',
        effective:runtimeVramState?.effective ?? vramFaultActive(),
        reason:runtimeVramState?.reason ?? (vramFaultActive()?'none':'no-fault'),
        supportedModelsMask:runtimeVramState?.supportedModelsMask ?? 3,
        mask:runtimeVramState?.mask ?? vramAddressMask,
        bridgeA:runtimeVramState?.bridgeA ?? actualPair()?.[0] ?? -1,
        bridgeB:runtimeVramState?.bridgeB ?? actualPair()?.[1] ?? -1,
        lastFrameCounts:transactionCounts},
      psgInputFault:{schemaVersion:2,available:!!psgState,
        modelVersion:psgState?.modelVersion ?? null,
        supported:psgState?.supported ?? false,
        configured:psgState?.configured ?? false,
        effective:psgState?.effective ?? false,
        reason:psgState?.reason ?? 'api-unavailable',
        bridgeA:psgState?.bridgeA ?? -1,
        bridgeB:psgState?.bridgeB ?? -1,
        dataMask:Number.isInteger(psgState?.dataMask)?psgState.dataMask:0,
        inputWrites:psgState?.inputWrites ?? '0',
        changedWrites:psgState?.changedWrites ?? '0'},
      fmInputFault:{schemaVersion:2,available:!!fmState,
        modelVersion:fmState?.modelVersion ?? null,
        supported:fmState?.supported ?? false,
        configured:fmState?.configured ?? false,
        effective:fmState?.effective ?? false,
        reason:fmState?.reason ?? 'api-unavailable',
        bridgeA:fmState?.bridgeA ?? -1,
        bridgeB:fmState?.bridgeB ?? -1,
        dataMask:Number.isInteger(fmState?.dataMask)?fmState.dataMask:0,
        inputWrites:fmState?.inputWrites ?? '0',
        changedWrites:fmState?.changedWrites ?? '0'},
      vramModelTransitions:vramModelTransitions.map(entry=>({...entry})),
      exportedAt:new Date().toISOString()
    };
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url; link.download='vram-page-md-experiment.json';
    document.body.append(link); link.click(); link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    stamp('Experiment metadata downloaded locally (ROM bytes were not included)');
  }

  function updateFaultUI() {
    const pair = actualPair();
    const actual=currentVramModelState();
    document.querySelector('[data-keyboard-chip="VRAM"]').classList.toggle('fault-active',
      started && !!(actual.mask || (actual.bridgeA>=0 && actual.bridgeB>=0)));
    const contact=vramAddressMask ? `${vramLines(vramAddressMask).join(', ')} FORCED LOW` : describe(pair);
    $('connectionLabel').textContent = contact;
    pinButtons.forEach((button, index) => {
      button.classList.toggle('connected', !!(pair && pair.includes(index)));
      button.classList.toggle('cut', !!(vramAddressMask & (1<<index)));
      button.classList.toggle('selected', selectedPin === index);
      button.setAttribute('aria-pressed', !!((vramAddressMask & (1<<index)) || (pair && pair.includes(index))));
    });
    document.querySelectorAll('.preset').forEach((button, index) => {
      const isActive = samePair(pair, PRESETS[index]);
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-pressed', isActive);
    });
    refreshVramControls();
    const next = contact;
    if ((pair || vramAddressMask) && started) possibleVramResidue = true;
    const faultHint = $('faultHint');
    if (faultHint) faultHint.hidden = !(!vramFaultActive() && possibleVramResidue && started);
    if (next !== lastContact) {
      if (lastContact) stamp(vramAddressMask ? `VRAM lines forced low: ${vramLines(vramAddressMask).join(', ')}` : pair ? `SHORT CONNECTED: ${next}` : 'All VRAM faults removed');
      lastContact = next;
    }
    $('vramModelNotice').innerHTML=vramModelId===2
      ? '<strong>Experimental transaction model.</strong> Counts are software byte-lane operations for the last completed tick, not physical bus cycles or cycle-accurate electrical behavior.'
      : '<strong>Experimental frame model.</strong> Shorts are applied around each emulated frame, not at every real VRAM bus transition. This is not yet a cycle-accurate electrical simulation.';
    refreshRandomiserControls();
  }

  function latch(pair) {
    const sorted = canonical(pair);
    const nextPair=samePair(latched,sorted)?null:sorted;
    applyVramModel(vramModelId,0,nextPair,'VRAM bridge toggled');
  }

  function disconnect(reason='all VRAM contacts reconnected') {
    const targetModel=vramDisconnectModel();
    return applyVramModel(targetModel,0,null,reason);
  }

  function startMomentaryBridge(pair) {
    const sorted=canonical(pair);
    const restorePair=canonical(latched);
    const restoreMask=vramAddressMask;
    if (!applyVramModel(vramModelId,0,sorted,'momentary VRAM bridge activated')) return false;
    momentaryRestorePair=restorePair;
    momentaryRestoreMask=restoreMask;
    latched=null; momentary=sorted;
    updateFaultUI();
    return true;
  }

  function endMomentaryBridge() {
    if (!momentary) return true;
    const state=currentVramModelState();
    const targetModel=vramModelId===2 && (state.supportedModelsMask&4)===0 ? 1 : vramModelId;
    if (applyVramModel(targetModel,momentaryRestoreMask,momentaryRestorePair,'momentary VRAM bridge released')) {
      momentaryRestorePair=null;momentaryRestoreMask=0;
      return true;
    }
    return false;
  }

  function setKeyboardTarget(target) {
    keyboardTarget=target;
    $('keyboardTarget').textContent=`Keyboard Fault Target: ${target}`;
    document.querySelectorAll('[data-keyboard-chip]').forEach(card=>
      card.classList.toggle('keyboard-target',card.dataset.keyboardChip===target));
  }

  function abandonKeyboardHold(target) {
    if (!keyboardMutation && keyboardHeld?.target===target) keyboardHeld=null;
  }

  function applyKeyboardMutation(action) {
    keyboardMutation=true;
    try { return action(); } finally { keyboardMutation=false; }
  }

  function reportKeyboardReleaseFailure(target,reason) {
    if (target==='WRAM') ownedAddressHold=null;
    if (!paused) pauseToggle();
    if (target==='WRAM') {
      try { updateLogicControls(); } catch (_) { /* Runtime state getters may be the failure source. */ }
    }
    const status=target==='VRAM' ? $('vramModelStatus') : target==='WRAM'
      ? $('logicStatus') : $(`${target.toLowerCase()}BridgeStatus`);
    status.textContent=`${target} held fault release/restoration was not confirmed (${reason}); emulation paused. The fault may remain active.`;
  }

  function audioState(target) {
    const state=target==='FM'?currentFmDataState():currentPsgDataState();
    if (!state) return null;
    return {pair:state.configured && state.bridgeA>=0 && state.bridgeB>=0
      ?canonical([state.bridgeA,state.bridgeB]):null,mask:Number(state.dataMask||0)};
  }

  function applyAudioTarget(target,pair,mask=0) {
    return target==='FM'
      ? (mask ? setFmDataMask(mask) : pair ? setFmDataBridge(true,pair) : setFmDataBridge(false))
      : (mask ? setPsgDataMask(mask) : pair ? setPsgDataBridge(true,pair) : setPsgDataBridge(false));
  }

  function toggleKeyboardFault(index,hold=false) {
    if (!started || index<0 || index>8) return false;
    if (hold && keyboardHeld) return false;
    if (keyboardTarget==='VRAM') {
      if (!hold) return latch(SHORTCUT_PAIRS[index]);
      if (!startMomentaryBridge(SHORTCUT_PAIRS[index])) return false;
      keyboardHeld={code:`Digit${index+1}`,target:'VRAM'};
      return true;
    }
    if (keyboardTarget==='WRAM') {
      const [a,b]=QUICK_RAM_PAIRS[index];
      if (hold) {
        if (pendingPulse || momentary || ownedAddressHold || (logicActive && !activeRamConfiguration)) return false;
        const restore=logicActive&&activeRamConfiguration ? {...activeRamConfiguration}:null;
        if (!applyKeyboardMutation(()=>applyLogicFault(null,{kind:1,access:2,a,b}))) return false;
        keyboardHeld={code:`Digit${index+1}`,target:'WRAM',pair:[a,b],restore};
        return true;
      }
      if ($('ramWriteMode').value==='pulse') return startAddressFramePulse([a,b]);
      if (keyboardHeld || ownedAddressHold) return false;
      if (!startAddressFrameHold([a,b],{type:'numeric',code:`Digit${index+1}`})) return false;
      keyboardHeld={code:`Digit${index+1}`,target:'WRAM',pair:[a,b],restore:null};
      return true;
    }
    const before=audioState(keyboardTarget), pair=SHORTCUT_PAIRS[index];
    if (!before) return false;
    const active=before.mask!==0 || before.pair!==null;
    if (hold) {
      const target=keyboardTarget;
      if (!applyKeyboardMutation(()=>applyAudioTarget(target,pair))) return false;
      keyboardHeld={code:`Digit${index+1}`,target,restore:before};
      return true;
    }
    return active && before.pair && samePair(before.pair,pair) && !before.mask
      ? applyAudioTarget(keyboardTarget,null,0) : applyAudioTarget(keyboardTarget,pair,0);
  }

  function endKeyboardHold(code=null) {
    const held=keyboardHeld;
    if (!held || (code && code!==held.code)) return;
    keyboardHeld=null;
    try {
      if (held.target==='VRAM') {
        if (!endMomentaryBridge()) throw new Error('core refused VRAM restoration');
        return;
      }
      if (held.target==='WRAM') {
        const active=activeRamConfiguration;
        if (!logicActive || !active || active.type!=='line-pair' || active.kind!==1 || active.access!==2 || active.a!==held.pair[0] || active.b!==held.pair[1]) return;
        const expectedOwner=held.code.startsWith('Digit')?'numeric':'keyboard';
        if (ownedAddressHold && (ownedAddressHold.type!==expectedOwner || ownedAddressHold.code!==held.code || ownedAddressHold.key!==`${held.pair[0]},${held.pair[1]}`)) return;
        if (!applyKeyboardMutation(()=>disconnectLogic())) throw new Error('core refused RAM disconnect');
        if (held.restore && !applyKeyboardMutation(()=>held.restore.type==='address-mask'
          ? applyAddressMask(held.restore.mask,held.restore.access)
          : applyLogicFault(null,held.restore))) throw new Error('core rejected the prior RAM fault restoration');
        return;
      }
      const current=audioState(held.target);
      if (!current) throw new Error('audio runtime state is unavailable');
      if (!current.pair || !samePair(current.pair,SHORTCUT_PAIRS[Number(held.code.slice(5))-1])) return;
      if (!applyKeyboardMutation(()=>applyAudioTarget(held.target,held.restore.pair,held.restore.mask)))
        throw new Error('core rejected the prior audio fault restoration');
    } catch(error) {
      reportKeyboardReleaseFailure(held.target,error.message);
    }
  }

  function setupPatchbay() {
    for (let i=0;i<8;i++) {
      const b = document.createElement('button');
      b.type='button'; b.className='pin';
      b.style.gridColumn=i<4?'1':'3'; b.style.gridRow=String(i<4?i+1:i-3);
      const label=document.createElement('span'); label.className='chip-signal'; label.textContent=`AD${i}`;
      const wire=document.createElement('span'); wire.className='chip-wire'; wire.setAttribute('aria-hidden','true');
      const cut=document.createElement('span');cut.className='chip-cut';cut.textContent='×';wire.append(cut);
      b.append(...(i<4?[wire,label]:[label,wire]));
      b.title=`External address/data net AD${i}. Select a second net to bridge.`;
      b.setAttribute('aria-label', `Select net AD${i}`);
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => {
        if ($('vramMode').value==='disconnect') {applyVramAddressMask(vramAddressMask ^ (1<<i));return;}
        if (selectedPin === null) selectedPin = i;
        else if (selectedPin === i) selectedPin = null;
        else { latch([selectedPin, i]); selectedPin = null; }
        updateFaultUI();
      });
      $('pinGrid').append(b);
      pinButtons.push(b);
    }
    $('vramMode').addEventListener('change',()=>{selectedPin=null;updateFaultUI();});
    $('vramModel').addEventListener('change',()=>{
      const modelId=Number($('vramModel').value);
      if (!applyVramModel(modelId,vramAddressMask,actualPair(),'VRAM model selected'))
        $('vramModel').value=String(vramModelId);
    });
    PRESETS.forEach((pair,index) => {
      const b=document.createElement('button');
      b.type='button'; b.className='preset'; b.setAttribute('aria-pressed','false');
      const k=document.createElement('kbd'); k.textContent=`[${index+1}]`;
      const lab=document.createElement('span'); lab.textContent=`${pair[0]} ↔ ${pair[1]}`;
      b.append(k,lab);
      b.addEventListener('click',() => latch(pair));
      $('presetGrid').append(b);
    });
    $('disconnectBtn').addEventListener('click',()=>disconnect());
    $('clearLogBtn').addEventListener('click',()=> {logEl.replaceChildren();stamp('Log cleared');});
    updateFaultUI();
  }

  function ensureWasmViews() {
    if (!emulator || !started) return;
    if (!frameView || frameView.buffer !== emulator.HEAPU8.buffer) {
      frameView = new Uint8Array(emulator.HEAPU8.buffer,
        emulator._get_frame_buffer_ref(), SCREEN_WIDTH*SCREEN_HEIGHT*4);
      inputView = new Float32Array(emulator.HEAPF32.buffer, emulator._get_input_buffer_ref(),32);
      leftAudio = new Float32Array(emulator.HEAPF32.buffer, emulator._get_web_audio_l_ref(), 2048);
      rightAudio = new Float32Array(emulator.HEAPF32.buffer, emulator._get_web_audio_r_ref(), 2048);
    }
  }

  function pollControls() {
    inputView.fill(0);
    inputView[6] = Number(pressed.has('ArrowRight')) - Number(pressed.has('ArrowLeft'));
    inputView[7] = Number(pressed.has('ArrowDown')) - Number(pressed.has('ArrowUp'));
    // wasm-genplus GamePad API mapping for the 3-button Genesis controller.
    if (pressed.has('KeyZ') || pressed.has('Space')) inputView[9] = 1;  // C
    if (pressed.has('KeyX')) inputView[11] = 1; // B
    if (pressed.has('KeyC')) inputView[10] = 1; // A
    if (pressed.has('Enter')) inputView[15] = 1; // Start
    const gamepad = navigator.getGamepads?.()[0];
    if (gamepad) {
      const x = gamepad.axes?.[0] || 0, y = gamepad.axes?.[1] || 0;
      if (Math.abs(x) > 0.4) inputView[6] = Math.sign(x);
      if (Math.abs(y) > 0.4) inputView[7] = Math.sign(y);
      if (gamepad.buttons?.[0]?.pressed) inputView[9] = 1;
      if (gamepad.buttons?.[1]?.pressed) inputView[11] = 1;
      if (gamepad.buttons?.[9]?.pressed) inputView[15] = 1;
    }
    emulator._wasm_input_update();
  }

  function audioFrame() {
    const size = emulator._sound(); // Number of stereo float samples
    if (!audioOn || !audioCtx || size <= 0) return;
    if (audioCtx.state !== 'running') {
      if (activeAudioSources.size) clearAudioQueue();
      return;
    }
    const count = Math.min(2048,size);
    const b = audioCtx.createBuffer(2,count,AUDIO_RATE);
    b.copyToChannel(leftAudio.subarray(0,count),0);
    b.copyToChannel(rightAudio.subarray(0,count),1);
    const src=audioCtx.createBufferSource();
    src.buffer=b; src.connect(audioCtx.destination);
    activeAudioSources.add(src);
    src.addEventListener('ended',()=>{
      activeAudioSources.delete(src);
      src.disconnect();
    },{once:true});
    // Limit latency/backlog after a paused tab or slow frame.
    if (nextAudioTime < audioCtx.currentTime || nextAudioTime > audioCtx.currentTime + 0.20)
      nextAudioTime = audioCtx.currentTime + 0.025;
    try { src.start(nextAudioTime); }
    catch (error) {
      activeAudioSources.delete(src);
      src.disconnect();
      throw error;
    }
    nextAudioTime += b.duration;
  }

  function clearAudioQueue() {
    for (const src of activeAudioSources) {
      try { src.stop(); } catch (_) {}
      try { src.disconnect(); } catch (_) {}
    }
    activeAudioSources.clear();
    nextAudioTime=0;
  }

  function resetStats() { frames = 0; measuredAt = performance.now(); }

  function drawActiveVideo() {
    if (!frameView) return;
    // The wasm-genplus output allocation is 640 x 480 with a 640-pixel pitch.
    // Display recovery fills only systematically missing, fully blank source
    // scanlines. It never changes the emulator's memory or signal simulation.
    const raw = $('rawVideoToggle').checked;
    const result = frameAdapter.copyActiveFrame(frameView, imageData.data, {raw});
    ctx.putImageData(imageData, 0, 0);
    const status = raw ? 'Video: raw core pixels' : result.repairedRows
      ? `Video: ${result.repairedRows} missing output lines recovered`
      : 'Video: native pixels';
    if (status !== previousVideoStatus) {
      $('videoStatus').textContent = status;
      previousVideoStatus = status;
    }
  }

  function renderFrame() {
    const transientAtStart=recoveryTransientActive();
    ensureWasmViews();
    pollControls();
    emulator._tick();
    finishFaultPulse();
    drawActiveVideo();
    audioFrame();
    if (transientAtStart || recoveryTransientActive()) resetCpuRecoveryObservation();
    else observeAutomaticCpuRecovery();
    frames++;
    // Statistics describe byte differences under the projection model.
    if (typeof emulator._get_vram_changed_reads === 'function')
      $('readCount').textContent = emulator._get_vram_changed_reads().toLocaleString();
    if (typeof emulator._get_vram_changed_writes === 'function')
      $('writeCount').textContent = emulator._get_vram_changed_writes().toLocaleString();
    refreshVramTelemetry();
    refreshLogicMetrics();
    refreshPsgDataControls();
    refreshFmDataControls();
  }

  function animationFrame(time) {
    requestAnimationFrame(animationFrame);
    if (!started || paused || document.hidden) {
      lastFrame = time;
      return;
    }
    if (!lastFrame) lastFrame = time;
    accumulated += Math.min(100,time-lastFrame);
    lastFrame = time;
    let done=0;
    while (accumulated>=FRAME_MS && done<3 && started && !paused && !document.hidden) {
      renderFrame(); accumulated-=FRAME_MS; done++;
    }
    if (done===3) accumulated=0;
    if (time-measuredAt>=1000) {
      const fps=Math.round(frames*1000/(time-measuredAt));
      $('fpsIndicator').textContent=`${fps} FPS / 59.92 TARGET`;
      resetStats();
    }
  }

  function pauseToggle() {
    if (!started) return;
    if (!paused) disarmCpuRecovery();
    paused=!paused;
    $('pauseBtn').textContent = paused ? 'Resume' : 'Pause';
    if (paused) clearAudioQueue();
    stamp(paused?'Emulation paused':'Emulation resumed');
    updateLogicControls();
  }

  async function soundToggle() {
    if (!started) return;
    const enabling = !audioOn;
    if (enabling) {
      if (!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:AUDIO_RATE});
      if (audioCtx.state==='suspended') await audioCtx.resume();
      if (audioCtx.state !== 'running') throw new Error('Browser audio is not running. Check Firefox audio permissions.');
    }
    clearAudioQueue();
    audioOn=enabling;
    $('soundBtn').textContent=audioOn?'Mute Sound':'Enable Sound';
    $('soundBtn').setAttribute('aria-pressed',String(audioOn));
    refreshPsgDataControls();
    refreshFmDataControls();
    stamp(audioOn?'Audio enabled (FM + PSG output)':'Audio muted');
  }

  async function startCartridge(bytes, name, {cleanRestart=false}={}) {
    if (!emulator) throw new Error('Emulator not ready. Build the modified core first.');
    if (bytes.length<0x200 || bytes.length>4*1024*1024)
      throw new Error('Expected a 512-byte to 4-MB uncompressed Mega Drive ROM.');
    // Ordinary .bin/.md ROMs contain the SEGA ID at offset 0x100.
    const marker = new TextDecoder('ascii').decode(bytes.subarray(0x100,0x104));
    if (marker !== 'SEGA') throw new Error('ROM header missing "SEGA" at offset 0x100. Supply a valid uncompressed .bin/.md file.');
    // Stop the loop while preparing the new ROM. Before _start, failures leave
    // the current cartridge and all of its controls untouched.
    const wasStarted=started; started=false;
    let coreMutated=false;
    try {
      const ptr=emulator._get_rom_buffer_ref(bytes.length);
      if (!ptr) throw new Error('Emulator refused ROM buffer allocation.');
      ensureWasmViews();
      new Uint8Array(emulator.HEAPU8.buffer,ptr,bytes.length).set(bytes);
      // The accepted new image is about to replace core state; drain old audio
      // and cancel app-scheduled pulse work before native activation can throw.
      disarmCpuRecovery();
      clearAudioQueue();
      cancelPulse(cleanRestart ? 'clean restart' : 'cartridge replaced');
      ownedAddressHold=null; keyboardHeld=null;
      momentary=null; momentaryRestorePair=null; momentaryRestoreMask=0;
      coreMutated=true; // _start can mutate native state before it throws.
      emulator._start();
      if (typeof emulator._set_vram_short !== 'function')
        throw new Error('Core missing _set_vram_short. You must build the patched core (not the upstream prebuilt WASM).');
      frameView=null;
      started=true;
      cpuInterventions=[];
      faultPulses=[]; pendingPulse=null;
      ownedAddressHold=null;keyboardHeld=null;
      vramAddressMask=0;vramAddressLineChanges=[];
      latched=null;momentary=null;momentaryRestorePair=null;selectedPin=null;
      vramModelId=1;vramModelTransitions=[];
      vramModelStatusMessage='';
      logicAddressMask=0;addressLineChanges=[];
      logicActive=false; // runtime_start clears the Work RAM fault and counters.
      activeRamConfiguration=null;
      ramSelectedPin=null;psgSelectedPin=null;fmSelectedPin=null;
      logicStatsRetained=false;
      logicResetState=cleanRestart ? 'Clean Restart; Work RAM fault and counters reset' : 'Cartridge loaded; Work RAM fault and counters reset';
      resetLogicSelection();
      logicStatusMessage=logicApiReady() ? 'Load or apply a logic fault when ready.' : 'Rebuild core for logic faults';
      ensureWasmViews();
      const vramStatus=callVramModel(1,0,null);
      if (vramStatus!==0) throw new Error(`Could not restore default frame-projection VRAM model (status ${vramStatus}).`);
      updateFaultUI();
      $('screenPlaceholder').hidden=true;
      setRunning(true);
      paused=false;
      $('pauseBtn').textContent='Pause';
      faultDisconnectActions=[];
      $('disconnectAllFaultsStatus').textContent='No all-domain disconnect has been attempted for this cartridge.';
      accumulated=0;lastFrame=0;resetStats();
      refreshPsgDataControls();
      refreshFmDataControls();
      const hashPromise=cleanRestart && romIdentity?.bytes===bytes
        ? romIdentity.hashPromise
        : sha256Hex(bytes).catch(error=>{
            if (romIdentity?.bytes===bytes) stamp(`ROM SHA-256 unavailable: ${error.message}`);
            return null;
          });
      romBytes=bytes;
      loadedName=name;
      $('romName').textContent=name.toUpperCase().slice(0,60);
      romIdentity={bytes,name,hashPromise};
      updateLogicControls();
      stamp(`Cartridge inserted: ${name} (forced NTSC-U)`);
    } catch (error) {
      if (coreMutated) {
        started=false;
        setRunning(false);
        $('resetBtn').disabled=!romBytes;
        $('compactResetBtn').disabled=!romBytes;
        error.cartridgeActivationUncertain=true;
        message('CARTRIDGE ACTIVATION UNCERTAIN',`${error.message} The core may have changed; use Clean Restart to reload the last accepted cartridge.`);
      } else started=wasStarted;
      throw error;
    }
    // Browser audio is unlocked by a separate Sound button after user gesture.
  }

  async function loadLocalRom(file) {
    if (!file) return;
    const generation=++romLoadGeneration;
    try {
      stamp(`Loading local cartridge: ${file.name}`);
      if (file.size<0x200 || file.size>4*1024*1024)
        throw new Error('Expected a 512-byte to 4-MB uncompressed Mega Drive ROM.');
      const bytes=new Uint8Array(await file.arrayBuffer());
      if (generation!==romLoadGeneration) return;
      await startCartridge(bytes,file.name);
    } catch(e) {
      if (generation!==romLoadGeneration) return;
      stamp(`ERROR: ${e.message}`);
      if (!started && !e.cartridgeActivationUncertain) message('CARTRIDGE COULD NOT START',e.message);
    }
  }

  async function cleanRestart() {
    if (!romBytes) return;
    ++romLoadGeneration;
    try {
      await startCartridge(romBytes,loadedName,{cleanRestart:true});
      possibleVramResidue = false;
      updateFaultUI();
      setLogicStatus(logicApiAvailable ? 'Clean Restart: VRAM/Work RAM faults cleared; counters reset.' : 'Rebuild core for logic faults');
      stamp('Clean Restart: VRAM/Work RAM reset; all fault domains disconnected');
    } catch (error) { stamp(`Restart failed: ${error.message}`); }
  }

  function installKeyboard() {
    setKeyboardTarget(keyboardTarget);
    document.addEventListener('keydown', event => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.target instanceof HTMLInputElement ||
          event.target instanceof HTMLSelectElement ||
          event.target instanceof HTMLTextAreaElement ||
          event.target.isContentEditable) return;
      const comparisonOutput=event.target.closest?.('#compareOutput');
      if (comparisonOutput) {
        const step=40;
        const scroll={
          ArrowUp:[0,-step],ArrowDown:[0,step],ArrowLeft:[-step,0],ArrowRight:[step,0]
        }[event.code];
        if (scroll) {
          event.preventDefault();
          comparisonOutput.scrollBy(scroll[0],scroll[1]);
        }
        return;
      }
      const code=event.code;
      // Let focused UI controls activate normally rather than swallowing their
      // Enter/Space as controller inputs (notably the keyboard patchbay).
      if (['Enter','Space'].includes(code) &&
          event.target.closest('button, a, summary, label')) return;
      // A focused WRAM control should not hand its digit to the still-selected VRAM target.
      if (/^Digit[1-9]$/.test(code) && keyboardTarget==='VRAM' &&
          event.target.closest('[data-ram-frame-pair]')) return;
      if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','Enter'].includes(code))event.preventDefault();
      if (/^Digit[0-9]$/.test(code)) {
        event.preventDefault();
        if (event.repeat) return;
        const n=Number(code.slice(5));
        if (n===0) setKeyboardTarget(KEYBOARD_TARGETS[(KEYBOARD_TARGETS.indexOf(keyboardTarget)+1)%KEYBOARD_TARGETS.length]);
        else toggleKeyboardFault(n-1,event.shiftKey);
      } else if (code==='KeyP' && !event.repeat) {
        event.preventDefault();pauseToggle();
      } else pressed.add(code);
    });
    document.addEventListener('keyup', event=> {
      pressed.delete(event.code);
      if (/^Digit[1-9]$/.test(event.code)) endKeyboardHold(event.code);
      else if (['Space','Enter'].includes(event.code) && keyboardHeld?.target==='WRAM') endKeyboardHold(event.code);
    });
    window.addEventListener('blur',()=>{
      disarmCpuRecovery();
      pressed.clear();
      endKeyboardHold();
      if (ownedAddressHold?.type==='pointer') endAddressFrameHold('pointer',ownedAddressHold.pointerId);
      focusReleased=true;
    });
    window.addEventListener('focus',()=>{if(focusReleased){lastFrame=0;focusReleased=false;}});
    document.addEventListener('visibilitychange',()=>{
      lastFrame=0;clearAudioQueue();
      if (document.hidden) disarmCpuRecovery();
    });
  }

  async function initialiseCore() {
    if (window.__coreMissing || typeof window.Module!=='function') {
      message('MODIFIED CORE NOT FOUND',
        'Emulator files are missing. Download and extract the complete runnable ZIP from the VRAMpage MD release page. Source checkouts need the contributor build described in README.md.');
      stamp('No emulator core. Run scripts/build-core.sh with the Emscripten SDK.');
      return;
    }
    try {
      message('INITIALISING MEGA DRIVE','Loading the local Genesis Plus GX WebAssembly core…');
      emulator=await window.Module({locateFile:name=>`core/${name}`});
      if (!emulator.HEAPU8 || !emulator.HEAPF32)
        throw new Error('Emulator missing HEAPU8/HEAPF32 exports. Rebuild using the updated scripts/build-core.sh, then refresh this page.');
      emulator._init();
      if(typeof emulator._set_vram_short!=='function')
        throw new Error('Unmodified core detected. Run scripts/build-core.sh for VRAM fault support.');
      if (!vramMaskApiReady()) $('vramMode').value='bridge';
      logicApiAvailable=logicApiReady();
      updateFaultUI();
      setRunning(false);
      if (!logicApiAvailable) logicStatusMessage='Rebuild core for logic faults';
      updateLogicControls();
      message('INSERT YOUR CARTRIDGE','Choose a Sonic the Hedgehog ROM stored on your computer. The file is loaded only in this browser.');
      stamp('NTSC-U core loaded; ready for local ROM.');
    } catch(e) {
      emulator=null;
      message('CORE INITIALISATION FAILED',e.message);
      stamp(`Core error: ${e.message}`);
    }
  }

  function updateFullscreenDisplay() {
    const active = document.fullscreenElement === displayViewport;
    if (!active) {
      const section = displayViewport.closest('.screen-section').getBoundingClientRect();
      const frame = displayViewport.getBoundingClientRect();
      // Measure wrapping controls/help instead of guessing a viewport fraction.
      // Use document coordinates so scrolling cannot grow/shrink the picture.
      // Very short windows retain a usable minimum and may scroll vertically.
      const chrome = section.height - frame.height;
      const height = Math.max(96, Math.floor(window.innerHeight -
        (section.top + window.scrollY) - chrome - 12));
      displayViewport.style.setProperty('--window-display-height', `${height}px`);
    }
    $('fullscreenBtn').textContent = active ? 'Exit Fullscreen' : 'Fullscreen';
    $('fullscreenBtn').setAttribute('aria-pressed', String(active));
    // Firefox can retain a stale canvas backing/compositor surface after a
    // fullscreen transition. Reset only the fixed-size canvas and repaint
    // the last emulated frame; emulator state and ROM remain untouched.
    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;
    ctx.imageSmoothingEnabled = false;
    if (started) {
      ensureWasmViews();
      drawActiveVideo();
    }
  }

  function scheduleDisplayRefresh() {
    // Also handles Firefox's browser-level fullscreen (F11) and window resize,
    // neither of which necessarily fires document.fullscreenchange.
    if (displayRefreshQueued) return;
    displayRefreshQueued = true;
    requestAnimationFrame(() => {
      displayRefreshQueued = false;
      updateFullscreenDisplay();
    });
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement === displayViewport) {
        await document.exitFullscreen();
      } else if (!document.fullscreenElement) {
        await displayViewport.requestFullscreen();
      }
    } catch (error) {
      stamp(`Fullscreen unavailable: ${error.message}`);
    }
  }

  function setup() {
    for (const id of ['psgBridgeA','psgBridgeB']) {
      const select=$(id);
      for (let bit=0;bit<8;bit++) {
        const option=document.createElement('option');
        option.value=String(bit);option.textContent=`D${bit}`;select.append(option);
      }
    }
    // These selects are editable drafts. Refreshes report the live core state
    // without overwriting a pair the user is preparing to apply.
    $('psgBridgeA').value='0';
    $('psgBridgeB').value='1';
    for (const id of ['fmBridgeA','fmBridgeB']) {
      const select=$(id);
      select.innerHTML=Array.from({length:8},(_,bit)=>`<option value="${bit}">D${bit}</option>`).join('');
    }
    $('fmBridgeA').value='0';
    $('fmBridgeB').value='1';
    setupAudioChip('fm');setupAudioChip('psg');
    setupPatchbay();installKeyboard();
    configureLogicLines();
    $('logicKind').addEventListener('change',()=>{
      configureLogicLines();
      setLogicStatus('Configuration changed; apply it to activate a fault.');
    });
    for (const id of ['logicAccess','logicLineA','logicLineB'])
      $(id).addEventListener('change',()=>setLogicStatus('Configuration changed; apply it to activate a fault.'));
    setupPulseButtons();
    setupAddressChip();
    $('logicPulseBtn').addEventListener('click',()=>startFaultPulse());
    $('logicApplyBtn').addEventListener('click',()=>applyLogicFault());
    $('logicResumeBtn').addEventListener('click',()=>recoverLogicCPU(1));
    $('logicCpuResetBtn').addEventListener('click',()=>{
      recoverLogicCPU(2);
      $('randomiserStatus').textContent=$('logicStatus').textContent;
    });
    $('armCpuRecoveryBtn').addEventListener('click',()=>{
      if (cpuRecoveryArmed) disarmCpuRecovery();
      else if (started && !paused && typeof emulator?._recover_logic_cpu==='function' &&
          typeof emulator?._get_logic_cpu_flags==='function' && !recoveryTransientActive()) {
        resetCpuRecoveryObservation();cpuRecoveryArmed=true;
        setLogicStatus('One CPU-only recovery is armed after two eligible HALT frames.');
        stamp('One CPU-only recovery armed');updateLogicControls();
      }
    });
    $('logicDisconnectBtn').addEventListener('click',()=>disconnectLogic());
    $('disconnectAllFaultsBtn').addEventListener('click',runDisconnectAllFaults);
    $('logicExperimentBtn').addEventListener('click',()=>downloadExperimentJSON().catch(error=>{
      setLogicStatus(`Could not create experiment metadata: ${error.message}`);
      stamp(`Metadata export failed: ${error.message}`);
    }));
    $('psgBridgeApply').addEventListener('click',()=>setPsgDataBridge(true));
    $('psgBridgeRemove').addEventListener('click',()=>setPsgDataBridge(false));
    $('fmBridgeApply').addEventListener('click',()=>setFmDataBridge(true));
    $('fmBridgeRemove').addEventListener('click',()=>setFmDataBridge(false));
    $('randomPsgBtn').addEventListener('click',()=>randomiseAudio('psg'));
    $('randomFmBtn').addEventListener('click',()=>randomiseAudio('fm'));
    $('randomVramBtn').addEventListener('click',randomiseVram);
    setupAddressFramePairButtons();
    setupCircuitConfigurationControls();
    setupExperimentComparison();
    $('rawVideoToggle').addEventListener('change', () => {
      previousVideoStatus = "";
      drawActiveVideo();
    });
    $('romFile').addEventListener('change',event=>{loadLocalRom(event.target.files?.[0]);event.target.value='';});
    $('resetBtn').addEventListener('click',cleanRestart);
    $('compactResetBtn').addEventListener('click',cleanRestart);
    $('pauseBtn').addEventListener('click',pauseToggle);
    $('soundBtn').addEventListener('click',()=>soundToggle().catch(e=>stamp(`Audio error: ${e.message}`)));
    $('fullscreenBtn').addEventListener('click', toggleFullscreen);
    document.addEventListener('fullscreenchange', scheduleDisplayRefresh);
    window.addEventListener('resize', scheduleDisplayRefresh);
    if (typeof ResizeObserver !== 'undefined') {
      const displayObserver = new ResizeObserver(scheduleDisplayRefresh);
      displayObserver.observe(displayViewport);
      displayObserver.observe(displayViewport.closest('.screen-section'));
      displayObserver.observe(document.querySelector('.masthead'));
    }
    setRunning(false);
    updateLogicControls();
    resetStats();
    requestAnimationFrame(animationFrame);
    initialiseCore();
  }
  setup();
})();
