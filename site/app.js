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
  let possibleVramResidue = false;
  let displayRefreshQueued = false;
  let logicApiAvailable = false, logicActive = false, logicStatsRetained = false;
  let logicStatusMessage = 'Checking core support…';
  let lastLogicExperiment = null;
  let logicResetState = 'No cartridge loaded';
  let romHashPromise = Promise.resolve(null);
  const CORE_PIN = '6090aff9e9b2f578cd28882bd4571d2e35b1d674';
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
  }

  function samePair(a,b) { return !!(a && b) && a[0] === b[0] && a[1] === b[1]; }
  function canonical(pair) { return pair ? [...pair].sort((a,b) => a-b) : null; }
  function actualPair() { return momentary || latched; }
  function describe(pair) { return pair ? `AD${pair[0]} ↔ AD${pair[1]}` : 'NONE — OPEN CIRCUIT'; }

  function logicApiReady(core=emulator) {
    return !!core && LOGIC_API.every(name => typeof core[name] === 'function');
  }

  function updateLogicControls() {
    logicApiAvailable = logicApiReady();
    const canUse = started && logicApiAvailable;
    for (const id of ['logicKind','logicAccess','logicLineA','logicLineB','logicApplyBtn'])
      $(id).disabled = !canUse;
    $('logicDisconnectBtn').disabled = !canUse;
    $('logicExperimentBtn').disabled = !started || !romBytes;
    if (!logicApiAvailable) logicStatusMessage = 'Rebuild core for logic faults';
    else if (!started && ['Checking core support…','Rebuild core for logic faults'].includes(logicStatusMessage))
      logicStatusMessage = 'Load a ROM to enable logic faults.';
    $('logicStatus').textContent = logicStatusMessage;
    refreshLogicMetrics();
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

  function applyLogicFault() {
    if (!started || !logicApiReady()) return;
    const config=logicConfigFromControls();
    if (config.a===config.b) {
      setLogicStatus('Choose two different lines. No fault was applied.');
      return;
    }
    if (config.kind===2 && Math.floor(config.a/8)!==Math.floor(config.b/8)) {
      setLogicStatus('Data pairs must stay within D0–D7 or D8–D15. No fault was applied.');
      return;
    }
    if (actualPair()) disconnect();
    const status=emulator._set_logic_fault(config.kind,config.access,config.a,config.b);
    if (status!==0) {
      setLogicStatus(`Core rejected this logic fault (status ${status}).`);
      stamp(`Logic fault rejected: core status ${status}`);
      return;
    }
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
  }

  function disconnectLogic({silent=false}={}) {
    if (!logicActive) {
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
    logicActive=false;
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
      modelVersion:'0.2-experimental',
      corePin:CORE_PIN,
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
    $('connectionLabel').textContent = describe(pair);
    pinButtons.forEach((button, index) => {
      button.classList.toggle('connected', !!(pair && pair.includes(index)));
      button.classList.toggle('selected', selectedPin === index);
      button.setAttribute('aria-pressed', !!(pair && pair.includes(index)));
    });
    document.querySelectorAll('.preset').forEach((button, index) => {
      const isActive = samePair(pair, PRESETS[index]);
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-pressed', isActive);
    });
    const next = describe(pair);
    if (pair && started) possibleVramResidue = true;
    const faultHint = $('faultHint');
    if (faultHint) faultHint.hidden = !(!pair && possibleVramResidue && started);
    if (next !== lastContact) {
      const removedLogic=!!(pair && started && logicActive);
      if (removedLogic && !disconnectLogic({silent:true})) {
        // Keep the domains exclusive if the core refuses to clear work RAM.
        latched=null; momentary=null; selectedPin=null;
        updateFaultUI();
        setLogicStatus('Could not disconnect the logic fault; VRAM fault was not applied.');
        return;
      }
      if (emulator && typeof emulator._set_vram_short === 'function')
        emulator._set_vram_short(pair ? pair[0] : -1, pair ? pair[1] : -1);
      if (removedLogic) {
        logicResetState='Logic fault disconnected because VRAM fault was activated';
        logicStatusMessage='VRAM patch active; logic/work RAM fault disconnected.';
        $('logicStatus').textContent=logicStatusMessage;
        stamp('Logic/work RAM fault disconnected because the VRAM patch was activated');
      }
      if (lastContact) stamp(pair ? `SHORT CONNECTED: ${next}` : 'All shorts removed');
      lastContact = next;
    }
  }

  function latch(pair) {
    const sorted = canonical(pair);
    latched = samePair(latched, sorted) ? null : sorted;
    selectedPin = null;
    updateFaultUI();
  }

  function disconnect() {
    latched = null;
    momentary = null;
    selectedPin = null;
    updateFaultUI();
  }

  function setupPatchbay() {
    for (let i=0;i<8;i++) {
      const b = document.createElement('button');
      b.type='button'; b.className='pin'; b.textContent=`AD${i}`;
      b.title=`External address/data net AD${i}. Select a second net to bridge.`;
      b.setAttribute('aria-label', `Select net AD${i}`);
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => {
        if (selectedPin === null) selectedPin = i;
        else if (selectedPin === i) selectedPin = null;
        else { latch([selectedPin, i]); selectedPin = null; }
        updateFaultUI();
      });
      $('pinGrid').append(b);
      pinButtons.push(b);
    }
    PRESETS.forEach((pair,index) => {
      const b=document.createElement('button');
      b.type='button'; b.className='preset'; b.setAttribute('aria-pressed','false');
      const k=document.createElement('kbd'); k.textContent=`[${index+1}]`;
      const lab=document.createElement('span'); lab.textContent=`${pair[0]} ↔ ${pair[1]}`;
      b.append(k,lab);
      b.addEventListener('click',() => latch(pair));
      $('presetGrid').append(b);
    });
    $('disconnectBtn').addEventListener('click',disconnect);
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
        else if (event.shiftKey) { momentary=canonical(PRESETS[n-1]);updateFaultUI(); }
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
        'The patchbay is ready, but Sonic cannot run until you build the local genplus.js and genplus.wasm files. See README.md.');
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
    $('logicApplyBtn').addEventListener('click',applyLogicFault);
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
