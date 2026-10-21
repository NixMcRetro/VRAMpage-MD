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
  const ctx = canvas.getContext('2d', {alpha: false});
  const imageData = ctx.createImageData(GAME_WIDTH, GAME_HEIGHT);
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
  }

  function samePair(a,b) { return !!(a && b) && a[0] === b[0] && a[1] === b[1]; }
  function canonical(pair) { return pair ? [...pair].sort((a,b) => a-b) : null; }
  function actualPair() { return momentary || latched; }
  function describe(pair) { return pair ? `AD${pair[0]} ↔ AD${pair[1]}` : 'NONE — OPEN CIRCUIT'; }

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
    if (next !== lastContact) {
      if (emulator && typeof emulator._set_vram_short === 'function')
        emulator._set_vram_short(pair ? pair[0] : -1, pair ? pair[1] : -1);
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

  function renderFrame() {
    ensureWasmViews();
    pollControls();
    emulator._tick();
    // Copy 320 active pixels per row; the source framebuffer pitch is 640.
    const srcPitchBytes = SCREEN_WIDTH * 4;
    const rowBytes = GAME_WIDTH * 4;
    for (let y = 0; y < GAME_HEIGHT; y++) {
      const start = y * srcPitchBytes;
      imageData.data.set(frameView.subarray(start, start + rowBytes), y * rowBytes);
    }
    ctx.putImageData(imageData,0,0);
    audioFrame();
    frames++;
    // Statistics describe byte differences under the projection model.
    if (typeof emulator._get_vram_changed_reads === 'function')
      $('readCount').textContent = emulator._get_vram_changed_reads().toLocaleString();
    if (typeof emulator._get_vram_changed_writes === 'function')
      $('writeCount').textContent = emulator._get_vram_changed_writes().toLocaleString();
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

  async function startCartridge(bytes, name) {
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
    emulator._start();
    if (typeof emulator._set_vram_short !== 'function')
      throw new Error('Core missing _set_vram_short. You must build the patched core (not the upstream prebuilt WASM).');
    frameView=null;
    started=true;
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
    stamp(`Cartridge inserted: ${name} (forced NTSC-U)`);
    // Browser audio is unlocked by a separate Sound button after user gesture.
  }

  async function loadLocalRom(file) {
    if (!file) return;
    try {
      stamp(`Loading local cartridge: ${file.name}`);
      romBytes=new Uint8Array(await file.arrayBuffer());
      await startCartridge(romBytes,file.name);
    } catch(e) {
      stamp(`ERROR: ${e.message}`);
      message('CARTRIDGE COULD NOT START',e.message);
    }
  }

  function installKeyboard() {
    document.addEventListener('keydown', event => {
      if (event.target instanceof HTMLInputElement) return;
      const code=event.code;
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
      updateFaultUI();
      setRunning(false);
      message('INSERT YOUR CARTRIDGE','Choose a Sonic the Hedgehog ROM stored on your computer. The file is loaded only in this browser.');
      stamp('NTSC-U core loaded; ready for local ROM.');
    } catch(e) {
      emulator=null;
      message('CORE INITIALISATION FAILED',e.message);
      stamp(`Core error: ${e.message}`);
    }
  }

  function setup() {
    setupPatchbay();installKeyboard();
    $('romFile').addEventListener('change',event=>{loadLocalRom(event.target.files?.[0]);event.target.value='';});
    $('resetBtn').addEventListener('click',async()=>{if(romBytes) await startCartridge(romBytes,loadedName);});
    $('pauseBtn').addEventListener('click',pauseToggle);
    $('soundBtn').addEventListener('click',()=>soundToggle().catch(e=>stamp(`Audio error: ${e.message}`)));
    $('fullscreenBtn').addEventListener('click',()=>{if(!document.fullscreenElement)canvas.requestFullscreen?.();else document.exitFullscreen?.();});
    setRunning(false);
    resetStats();
    requestAnimationFrame(animationFrame);
    initialiseCore();
  }
  setup();
})();