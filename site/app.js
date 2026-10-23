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
  const logEl = $('experimentLog');
  let emulator = null, started = false, paused = false;
  let loadedName = '', latched = null, momentary = null, selectedPin = null;
  let audioCtx = null, audioOn = false, nextAudioTime = 0;
  let romBytes = null, frameView = null, inputView = null, leftAudio = null, rightAudio = null;
  let lastFrame = 0, accumulated = 0, frames = 0, measuredAt = 0;
  let focusReleased = false;
  let lastContact = '';
  let vramAddressMask=0, vramAddressLineChanges=[];
  let possibleVramResidue = false;
  let displayRefreshQueued = false;
  let logicApiAvailable = false, logicActive = false, logicStatsRetained = false;
  let logicStatusMessage = 'Checking core support…';
  let lastLogicExperiment = null;
  let cpuInterventions = [];
  let faultPulses = [], pendingPulse = null;
  let logicAddressMask = 0, addressLineChanges = [];
  let logicResetState = 'No cartridge loaded';
  let romHashPromise = Promise.resolve(null);
  const CORE_PIN = '6090aff9e9b2f578cd28882bd4571d2e35b1d674';
  const APPLICATION_VERSION = '0.2.8';
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
    $('powerLed').classList.toggle('on', running);
    $('powerLabel').textContent = running ? 'CONSOLE ON' : (emulator ? 'WAITING FOR ROM' : 'CORE NOT READY');
    $('resetBtn').disabled = !running;
    $('pauseBtn').disabled = !running;
    $('soundBtn').disabled = !running;
    updateLogicControls();
    refreshVramControls();
  }

  function samePair(a,b) { return !!(a && b) && a[0] === b[0] && a[1] === b[1]; }
  function canonical(pair) { return pair ? [...pair].sort((a,b) => a-b) : null; }
  function actualPair() { return momentary || latched; }
  function describe(pair) { return pair ? `AD${pair[0]} ↔ AD${pair[1]}` : 'NONE — NORMAL ADDRESSING'; }

  function vramMaskApiReady() {
    return typeof emulator?._set_vram_address_mask==='function' &&
      typeof emulator?._get_vram_address_mask==='function';
  }

  function vramFaultActive() { return !!(vramAddressMask || actualPair()); }
  function vramLines(mask) {
    return Array.from({length:8},(_,i)=>i).filter(i=>mask & (1<<i)).map(i=>`AD${i}`);
  }

  function refreshVramControls() {
    const supported=vramMaskApiReady();
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

  function applyVramAddressMask(mask) {
    if(!started || !vramMaskApiReady()) return;
    const removedLogic=!!(mask && logicActive);
    if(removedLogic && !disconnectLogic({silent:true})) {
      stamp('VRAM leg unchanged: could not disconnect the RAM fault.');return;
    }
    const before=vramTransitionSnapshot();
    const status=emulator._set_vram_address_mask(mask);
    if(status!==0) {
      if(removedLogic) setLogicStatus('RAM fault disconnected; VRAM leg setting rejected.');
      stamp(`VRAM leg setting rejected (status ${status}).`);return;
    }
    recordVramMask(mask,'VRAM leg toggled',before);
    if (removedLogic) setLogicStatus('VRAM patch active; logic/work RAM fault disconnected.');
    latched=null;momentary=null;selectedPin=null;
    updateFaultUI();
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
      const line=Number(button.dataset.chipLine), disabled=!!(logicAddressMask & (1<<line));
      button.disabled=!ready;
      button.setAttribute('aria-pressed',String(disabled));
      button.setAttribute('aria-label',`A${line+1}: ${disabled?'forced low; reconnect':'enabled; force low'}`);
    }
    $('chipRestoreBtn').disabled=!ready || logicAddressMask===0;
  }

  function chipTransitionSnapshot() {
    return {frame:Number(emulator._get_logic_frame()),previousMask:logicAddressMask,
      readCountBefore:Number(emulator._get_logic_reads()),writeCountBefore:Number(emulator._get_logic_writes())};
  }

  function recordAddressMask(mask,access,reason,before) {
    if (mask!==logicAddressMask) addressLineChanges.push({...before,mask,access,reason});
    logicAddressMask=mask;
  }

  function applyAddressMask(mask) {
    if (!started || !addressMaskApiReady()) return;
    const access=Number($('logicAccess').value);
    const event=chipTransitionSnapshot();
    if (mask===0) {
      if (!disconnectLogic()) return;
      return;
    }
    const status=emulator._set_logic_address_mask(mask,access);
    if (status!==0) {setLogicStatus(`Address-line setting rejected (status ${status}).`);return;}
    cancelPulse('replaced by address-line switches');
    if (vramFaultActive()) disconnect();
    recordAddressMask(mask,access,'address line toggled',event); logicActive=true; logicStatsRetained=false;
    const lines=Array.from({length:15},(_,i)=>i).filter(i=>mask & (1<<i)).map(i=>`A${i+1}`);
    const accessLabel=['','read','write','read + write'][access];
    lastLogicExperiment={kind:'address-stuck-low',access:accessLabel,lines,addressMask:mask,
      activationFrame:Number(emulator._get_logic_activation_frame()),resetState:logicResetState,
      currentFrame:event.frame,readCount:0,writeCount:0,cpuFlags:Number(emulator._get_logic_cpu_flags())};
    setLogicStatus(`${lines.join(', ')} forced low on ${accessLabel}. Click crossed wires to reconnect; stored writes persist.`);
    stamp(`Address lines forced low: ${lines.join(', ')} (${accessLabel})`);
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
      button.addEventListener('click',()=>applyAddressMask(logicAddressMask ^ (1<<line)));
      $('ramChip').append(button);
    }
    $('chipRestoreBtn').addEventListener('click',()=>applyAddressMask(0));
  }

  function updateLogicControls() {
    logicApiAvailable = logicApiReady();
    const canUse = started && logicApiAvailable;
    for (const id of ['logicKind','logicAccess','logicLineA','logicLineB','logicApplyBtn'])
      $(id).disabled = !canUse;
    $('logicDisconnectBtn').disabled = !canUse;
    for (const id of ['logicResumeBtn','logicCpuResetBtn'])
      $(id).disabled = !canUse || typeof emulator._recover_logic_cpu !== 'function';
    for (const control of document.querySelectorAll('[data-ram-pulse], #logicPulseBtn, #logicPulseFrames'))
      control.disabled = !canUse || typeof emulator._recover_logic_cpu !== 'function';
    for (const option of $('logicPulseFrames').querySelectorAll('[data-write-limit]'))
      option.disabled = !writePulseApiReady();
    $('logicExperimentBtn').disabled = !started || !romBytes;
    if (!logicApiAvailable) logicStatusMessage = 'Rebuild core for logic faults';
    else if (!started && ['Checking core support…','Rebuild core for logic faults'].includes(logicStatusMessage))
      logicStatusMessage = 'Load a ROM to enable logic faults.';
    $('logicStatus').textContent = logicStatusMessage;
    refreshLogicMetrics();
    refreshChipControls();
  }

  function refreshLogicMetrics() {
    const core=emulator;
    if (logicApiReady(core)) {
      const reads=Number(core._get_logic_reads()) || 0;
      const writes=Number(core._get_logic_writes()) || 0;
      const frame=Number(core._get_logic_frame()) || 0;
      const activation=Number(core._get_logic_activation_frame());
      const flags=Number(core._get_logic_cpu_flags()) || 0;
      const shownReads=!logicActive && logicStatsRetained && lastLogicExperiment
        ? lastLogicExperiment.readCount : reads;
      const shownWrites=!logicActive && logicStatsRetained && lastLogicExperiment
        ? lastLogicExperiment.writeCount : writes;
      $('logicReadCount').textContent=shownReads.toLocaleString();
      $('logicWriteCount').textContent=shownWrites.toLocaleString();
      $('logicFrame').textContent=frame.toLocaleString();
      const shownActivation=logicActive && Number.isFinite(activation) && activation>=0
        ? activation : lastLogicExperiment?.activationFrame;
      $('logicActivationFrame').textContent=shownActivation===undefined ? '—' : Number(shownActivation).toLocaleString();
      const cpu=[];
      if (flags & 1) cpu.push('STOP');
      if (flags & 2) cpu.push('HALT');
      $('logicCpuStatus').textContent=cpu.length ? cpu.join(' + ') : 'No STOP/HALT flag';
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

  function logicConfigFromControls() {
    return {
      kind:Number($('logicKind').value),
      access:Number($('logicAccess').value),
      a:Number($('logicLineA').value),
      b:Number($('logicLineB').value)
    };
  }

  function logicLineName(kind,line) { return kind===1 ? `A${line+1}` : `D${line}`; }

  function applyLogicFault(writeLimit=null) {
    if (!started || !logicApiReady()) return false;
    const config=logicConfigFromControls();
    if (config.a===config.b) {
      setLogicStatus('Choose two different lines. No fault was applied.');
      return false;
    }
    if (config.kind===2 && Math.floor(config.a/8)!==Math.floor(config.b/8)) {
      setLogicStatus('Data pairs must stay within D0–D7 or D8–D15. No fault was applied.');
      return false;
    }
    if (writeLimit!==null && (!writePulseApiReady() || config.access!==2)) {
      setLogicStatus('Affected-write pulses require Access: Write and a rebuilt core.');
      return false;
    }
    const chipBefore=chipTransitionSnapshot();
    const status=writeLimit===null
      ? emulator._set_logic_fault(config.kind,config.access,config.a,config.b)
      : emulator._arm_logic_write_pulse(config.kind,config.a,config.b,writeLimit);
    if (status!==0) {
      setLogicStatus(`Core rejected this logic fault (status ${status}).`);
      stamp(`Logic fault rejected: core status ${status}`);
      return false;
    }
    if (vramFaultActive()) disconnect('RAM fault activated');
    cancelPulse('replaced by another fault');
    recordAddressMask(0,0,'replaced by paired fault',chipBefore);
    logicActive=true;
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
    stamp(`LOGIC / WORK RAM FAULT: ${kindLabel} ${lineA} ↔ ${lineB}, ${accessLabel}`);
    return true;
  }

  function disconnectLogic({silent=false,pulseReason='fault disconnected'}={}) {
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
    cancelPulse(pulseReason);
    logicActive=false;
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
      stamp('Logic/work RAM fault disconnected; projected RAM writes persist');
    }
    updateLogicControls();
    return true;
  }

  function recoverLogicCPU(mode) {
    if (!started || typeof emulator?._recover_logic_cpu !== 'function') return;
    const frame=Number(emulator._get_logic_frame());
    const flagsBefore=Number(emulator._get_logic_cpu_flags());
    if (!disconnectLogic({silent:true,pulseReason:'manual CPU recovery'})) {
      setLogicStatus('Recovery stopped: could not disconnect RAM fault.');
      return;
    }
    disconnect();
    const status=emulator._recover_logic_cpu(mode);
    if (status!==0) {
      setLogicStatus(`CPU recovery rejected (status ${status}).`);
      return;
    }
    const action=mode===1 ? 'force-resume' : 'cpu-only-reset';
    cpuInterventions.push({action,frame,flagsBefore,
      flagsAfter:Number(emulator._get_logic_cpu_flags())});
    logicResetState=`${action}; faults disconnected, RAM preserved`;
    setLogicStatus(`${mode===1 ? 'Forced resume attempted' : 'CPU-only reset issued'}. Faults disconnected; RAM preserved. Recovery is not guaranteed.`);
    stamp(`CPU intervention: ${action}; RAM preserved, faults disconnected`);
    refreshLogicMetrics();
    return true;
  }

  function cancelPulse(reason) {
    if (!pendingPulse) return;
    pendingPulse.status='cancelled';
    pendingPulse.reason=reason;
    pendingPulse.endFrame=Number(emulator._get_logic_frame());
    pendingPulse=null;
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

  function finishFaultPulse() {
    if (!pendingPulse) return;
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

  async function sha256Hex(bytes) {
    if (!window.crypto?.subtle) return null;
    const digest=await window.crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,'0')).join('');
  }

  async function downloadExperimentJSON() {
    let romSha256=null;
    try { romSha256=await romHashPromise; } catch (_) { /* Hashing failure never blocks emulation. */ }
    const currentFrame=logicApiReady() ? Number(emulator._get_logic_frame()) || 0 : 0;
    const coreReads=logicApiReady() ? Number(emulator._get_logic_reads()) || 0 : 0;
    const coreWrites=logicApiReady() ? Number(emulator._get_logic_writes()) || 0 : 0;
    const reads=!logicActive && logicStatsRetained && lastLogicExperiment ? lastLogicExperiment.readCount : coreReads;
    const writes=!logicActive && logicStatsRetained && lastLogicExperiment ? lastLogicExperiment.writeCount : coreWrites;
    const data={
      schemaVersion:1,
      build:{...buildInfo},
      modelVersion:'0.2.8-experimental',
      vramFault:{kind:vramAddressMask?'address-stuck-low':actualPair()?'address-bridge':'none',
        addressMask:vramAddressMask,lines:vramLines(vramAddressMask),bridge:actualPair()?[...actualPair()]:null},
      vramAddressLineChanges:vramAddressLineChanges.map(entry=>({...entry})),
      corePin:CORE_PIN,
      addressLineChanges:addressLineChanges.map(entry=>({...entry})),
      faultPulses:faultPulses.map(entry=>({...entry})),
      cpuInterventions:cpuInterventions.map(entry=>({...entry})),
      rom:{name:loadedName || null,sha256:romSha256},
      logicFault:lastLogicExperiment ? {...lastLogicExperiment} : null,
      faultActive:logicActive,
      resetState:logicResetState,
      currentFrame,readCount:reads,writeCount:writes,
      cpuFlags:logicApiReady() ? Number(emulator._get_logic_cpu_flags()) || 0 : null,
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
      const removedLogic=!!(pair && started && logicActive);
      if (removedLogic && !disconnectLogic({silent:true})) {
        // Keep the domains exclusive if the core refuses to clear work RAM.
        latched=null; momentary=null; selectedPin=null;
        updateFaultUI();
        setLogicStatus('Could not disconnect the logic fault; VRAM fault was not applied.');
        return;
      }
      if (!vramAddressMask && emulator && typeof emulator._set_vram_short === 'function')
        emulator._set_vram_short(pair ? pair[0] : -1, pair ? pair[1] : -1);
      if (removedLogic) {
        logicResetState='Logic fault disconnected because VRAM fault was activated';
        logicStatusMessage='VRAM patch active; logic/work RAM fault disconnected.';
        $('logicStatus').textContent=logicStatusMessage;
        stamp('Logic/work RAM fault disconnected because the VRAM patch was activated');
      }
      if (lastContact) stamp(vramAddressMask ? `VRAM lines forced low: ${vramLines(vramAddressMask).join(', ')}` : pair ? `SHORT CONNECTED: ${next}` : 'All VRAM faults removed');
      lastContact = next;
    }
  }

  function latch(pair) {
    recordVramMask(0,'replaced by VRAM bridge');
    const sorted = canonical(pair);
    latched = samePair(latched, sorted) ? null : sorted;
    selectedPin = null;
    updateFaultUI();
  }

  function disconnect(reason='all VRAM contacts reconnected') {
    recordVramMask(0,reason);
    latched = null;
    momentary = null;
    selectedPin = null;
    updateFaultUI();
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
    const count = Math.min(2048,size);
    const b = audioCtx.createBuffer(2,count,AUDIO_RATE);
    b.copyToChannel(leftAudio.subarray(0,count),0);
    b.copyToChannel(rightAudio.subarray(0,count),1);
    const src=audioCtx.createBufferSource();
    src.buffer=b; src.connect(audioCtx.destination);
    // Limit latency/backlog after a paused tab or slow frame.
    if (nextAudioTime < audioCtx.currentTime || nextAudioTime > audioCtx.currentTime + 0.20)
      nextAudioTime = audioCtx.currentTime + 0.025;
    src.start(nextAudioTime);
    nextAudioTime += b.duration;
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
    ensureWasmViews();
    pollControls();
    emulator._tick();
    finishFaultPulse();
    drawActiveVideo();
    audioFrame();
    frames++;
    // Statistics describe byte differences under the projection model.
    if (typeof emulator._get_vram_changed_reads === 'function')
      $('readCount').textContent = emulator._get_vram_changed_reads().toLocaleString();
    if (typeof emulator._get_vram_changed_writes === 'function')
      $('writeCount').textContent = emulator._get_vram_changed_writes().toLocaleString();
    refreshLogicMetrics();
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
    while (accumulated>=FRAME_MS && done<3) {
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
    paused=!paused;
    $('pauseBtn').textContent = paused ? 'Resume' : 'Pause';
    if (paused) nextAudioTime=0;
    stamp(paused?'Emulation paused':'Emulation resumed');
  }

  async function soundToggle() {
    if (!started) return;
    const enabling = !audioOn;
    if (enabling) {
      if (!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:AUDIO_RATE});
      if (audioCtx.state==='suspended') await audioCtx.resume();
      if (audioCtx.state !== 'running') throw new Error('Browser audio is not running. Check Firefox audio permissions.');
    }
    audioOn=enabling;
    nextAudioTime=0;
    $('soundBtn').textContent=audioOn?'Mute Sound':'Enable Sound';
    $('soundBtn').setAttribute('aria-pressed',String(audioOn));
    stamp(audioOn?'Audio enabled (FM + PSG; no sound-chip faults yet)':'Audio muted');
  }

  async function startCartridge(bytes, name, {cleanRestart=false}={}) {
    if (!emulator) throw new Error('Emulator not ready. Build the modified core first.');
    if (bytes.length<0x200 || bytes.length>4*1024*1024)
      throw new Error('Expected a 512-byte to 4-MB uncompressed Mega Drive ROM.');
    // Ordinary .bin/.md ROMs contain the SEGA ID at offset 0x100.
    const marker = new TextDecoder('ascii').decode(bytes.subarray(0x100,0x104));
    if (marker !== 'SEGA') throw new Error('ROM header missing "SEGA" at offset 0x100. Supply a valid uncompressed .bin/.md file.');
    // Stop the loop while we replace the cartridge image and reset the core.
    const wasStarted=started; started=false;
    const ptr=emulator._get_rom_buffer_ref(bytes.length);
    if (!ptr) {started=wasStarted;throw new Error('Emulator refused ROM buffer allocation.');}
    ensureWasmViews();
    new Uint8Array(emulator.HEAPU8.buffer,ptr,bytes.length).set(bytes);
    if (logicActive) disconnectLogic({silent:true});
    emulator._start();
    if (typeof emulator._set_vram_short !== 'function')
      throw new Error('Core missing _set_vram_short. You must build the patched core (not the upstream prebuilt WASM).');
    frameView=null;
    started=true;
    cpuInterventions=[];
    faultPulses=[]; pendingPulse=null;
    vramAddressMask=0;vramAddressLineChanges=[];
    logicAddressMask=0;addressLineChanges=[];
    logicActive=false; // runtime_start clears the work RAM fault and counters.
    logicStatsRetained=false;
    logicResetState=cleanRestart ? 'Clean restart; work RAM fault and counters reset' : 'Cartridge loaded; work RAM fault and counters reset';
    resetLogicSelection();
    logicStatusMessage=logicApiReady() ? 'Load or apply a logic fault when ready.' : 'Rebuild core for logic faults';
    ensureWasmViews();
    emulator._set_vram_short(...(actualPair() || [-1,-1]));
    updateFaultUI();
    $('screenPlaceholder').hidden=true;
    loadedName=name;
    $('romName').textContent=name.toUpperCase().slice(0,60);
    setRunning(true);
    paused=false;
    $('pauseBtn').textContent='Pause';
    accumulated=0;lastFrame=0;resetStats();nextAudioTime=0;
    updateLogicControls();
    stamp(`Cartridge inserted: ${name} (forced NTSC-U)`);
    // Browser audio is unlocked by a separate Sound button after user gesture.
  }

  async function loadLocalRom(file) {
    if (!file) return;
    try {
      stamp(`Loading local cartridge: ${file.name}`);
      romBytes=new Uint8Array(await file.arrayBuffer());
      romHashPromise=sha256Hex(romBytes).catch(error=>{
        stamp(`ROM SHA-256 unavailable: ${error.message}`);
        return null;
      });
      await startCartridge(romBytes,file.name);
    } catch(e) {
      stamp(`ERROR: ${e.message}`);
      message('CARTRIDGE COULD NOT START',e.message);
    }
  }

  function installKeyboard() {
    document.addEventListener('keydown', event => {
      if (event.target instanceof HTMLInputElement ||
          event.target instanceof HTMLSelectElement ||
          event.target instanceof HTMLTextAreaElement ||
          event.target.isContentEditable) return;
      const code=event.code;
      // Let focused UI controls activate normally rather than swallowing their
      // Enter/Space as controller inputs (notably the keyboard patchbay).
      if (['Enter','Space'].includes(code) &&
          event.target.closest('button, a, summary, label')) return;
      if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','Enter'].includes(code))event.preventDefault();
      if (/^Digit[0-8]$/.test(code)) {
        event.preventDefault();
        if (event.repeat) return;
        const n=Number(code.slice(5));
        if (n===0)disconnect();
        else if (event.shiftKey) { recordVramMask(0,'replaced by momentary VRAM bridge');momentary=canonical(PRESETS[n-1]);updateFaultUI(); }
        else latch(PRESETS[n-1]);
      } else if (code==='KeyP' && !event.repeat) {
        event.preventDefault();pauseToggle();
      } else pressed.add(code);
    });
    document.addEventListener('keyup', event=> {
      pressed.delete(event.code);
      if (/^Digit[1-8]$/.test(event.code) && momentary) {
        momentary=null;updateFaultUI();
      }
    });
    window.addEventListener('blur',()=>{
      pressed.clear();
      if(momentary){momentary=null;updateFaultUI();}
      focusReleased=true;
    });
    window.addEventListener('focus',()=>{if(focusReleased){lastFrame=0;focusReleased=false;}});
    document.addEventListener('visibilitychange',()=>{lastFrame=0;nextAudioTime=0;});
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
    $('fullscreenBtn').textContent = active ? 'Exit fullscreen' : 'Fullscreen';
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
    $('logicCpuResetBtn').addEventListener('click',()=>recoverLogicCPU(2));
    $('logicDisconnectBtn').addEventListener('click',()=>disconnectLogic());
    $('logicExperimentBtn').addEventListener('click',()=>downloadExperimentJSON().catch(error=>{
      setLogicStatus(`Could not create experiment metadata: ${error.message}`);
      stamp(`Metadata export failed: ${error.message}`);
    }));
    $('rawVideoToggle').addEventListener('change', () => {
      previousVideoStatus = "";
      drawActiveVideo();
    });
    $('romFile').addEventListener('change',event=>{loadLocalRom(event.target.files?.[0]);event.target.value='';});
    $('resetBtn').addEventListener('click',async()=>{
      if (!romBytes) return;
      // Reset the VDP and reload the original cartridge without any bridged pins.
      // VRAM content altered by earlier simulated shorts cannot be undone by disconnecting alone.
      disconnect();
      disconnectLogic({silent:true});
      try {
        await startCartridge(romBytes,loadedName,{cleanRestart:true});
        possibleVramResidue = false;
        updateFaultUI();
        setLogicStatus(logicApiAvailable ? 'Clean restart: VRAM/work RAM faults cleared; counters reset.' : 'Rebuild core for logic faults');
        stamp('Clean restart: VRAM/work RAM reset; all fault domains disconnected');
      } catch (error) { stamp(`Restart failed: ${error.message}`); }
    });
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
