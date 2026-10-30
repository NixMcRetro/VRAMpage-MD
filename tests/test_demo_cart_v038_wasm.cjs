/* Run the exact approved full Demo Cart inside compiled Genesis Plus GX WASM.
 * This is a runtime probe, not a replacement for human visual acceptance.
 * Usage: node tests/test_demo_cart_v038_wasm.cjs site/core/genplus.js
 */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const coreFile = path.resolve(process.argv[2] || 'site/core/genplus.js');
const romFile = path.join(root, 'demo-cart/show-lab/build/VRAMpage-MD-Demo-Cart-v0.3.8-Show.bin');
const reportFile = path.join(root, 'demo-cart/show-lab/build/rom_report.json');
const output = path.join(root, 'artifacts/demo-cart-v038-genplus');
const WIDTH = 320, HEIGHT = 224, PITCH = 640;
const manifest = JSON.parse(fs.readFileSync(path.join(root,'site/cartridges.json'),'utf8'));
const approved = manifest.cartridges.find(cart => cart.id === manifest.defaultCartridge);

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const value of bytes) {
    crc ^= value;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function pngChunk(type, data) {
  const name = Buffer.from(type, 'ascii');
  const out = Buffer.alloc(data.length + 12);
  out.writeUInt32BE(data.length, 0);
  name.copy(out, 4);
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}
function png(rgba) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(WIDTH, 0);
  header.writeUInt32BE(HEIGHT, 4);
  header[8] = 8; header[9] = 6;
  const scanlines = Buffer.alloc(HEIGHT * (1 + WIDTH * 4));
  for (let y = 0; y < HEIGHT; y++) {
    const offset = y * (1 + WIDTH * 4);
    scanlines[offset] = 0;
    rgba.copy(scanlines, offset + 1, y * WIDTH * 4, (y + 1) * WIDTH * 4);
  }
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),
    pngChunk('IHDR', header), pngChunk('IDAT', zlib.deflateSync(scanlines)),
    pngChunk('IEND', Buffer.alloc(0))]);
}
function visiblePixels(core) {
  const mem = core.HEAPU8, base = core._get_frame_buffer_ref();
  const rgba = Buffer.alloc(WIDTH * HEIGHT * 4);
  for (let y = 0; y < HEIGHT; y++) {
    rgba.set(mem.subarray(base + y * PITCH * 4, base + y * PITCH * 4 + WIDTH * 4),
      y * WIDTH * 4);
  }
  return rgba;
}
async function machine(region, rom) {
  const core = await require(coreFile)({locateFile: name => path.join(path.dirname(coreFile), name)});
  core._init();
  assert.equal(core._set_region_request(region), 0);
  core.HEAPU8.set(rom, core._get_rom_buffer_ref(rom.length));
  core._start();
  const input = new Float32Array(core.HEAPF32.buffer, core._get_input_buffer_ref(), 32);
  function frame(button) {
    input.fill(0);
    if (button === 'up') input[7] = -1;
    if (button === 'down') input[7] = 1;
    if (button === 'left') input[6] = -1;
    if (button === 'right') input[6] = 1;
    if (button === 'A') input[10] = 1;
    if (button === 'B') input[11] = 1;
    if (button === 'C') input[9] = 1;
    if (button === 'START') input[15] = 1;
    core._wasm_input_update();
    core._tick();
    const count = core._sound();
    assert.ok(count >= 0 && count <= 2048, 'WASM audio frame stays inside output buffer');
    return count;
  }
  function run(n) { for (let i = 0; i < n; i++) frame(); }
  function press(key) { frame(key); run(2); }
  function capture(label) {
    const rgba = visiblePixels(core);
    const colours = new Set();
    let nonBlack = 0;
    for (let y = 0; y < HEIGHT; y += 2) for (let x = 0; x < WIDTH; x += 2) {
      const p = 4 * (y * WIDTH + x), r = rgba[p], g = rgba[p+1], b = rgba[p+2];
      colours.add((r << 16) | (g << 8) | b);
      if (r || g || b) nonBlack++;
    }
    const digest = crypto.createHash('sha256').update(rgba).digest('hex');
    fs.writeFileSync(path.join(output, label + '.png'), png(rgba));
    const sample = {label, region, nativeFrame:core._get_logic_frame(),
      uniqueColours:colours.size, nonBlack, rgbaSHA256:digest};
    assert.ok(colours.size >= 5 && nonBlack >= 500,
      'Real Genesis Plus GX frame unexpectedly empty: ' + JSON.stringify(sample));
    return sample;
  }
  return {core, frame, run, press, capture};
}


/* Record genuine stereo output from Genesis Plus GX, without altering the ROM
 * or substituting a generated soundtrack. Keep each scene separately reviewable.
 */
function recordSceneAudio(machine, label, frames, fps) {
  const core=machine.core;
  const left=new Float32Array(core.HEAPF32.buffer,core._get_web_audio_l_ref(),2048);
  const right=new Float32Array(core.HEAPF32.buffer,core._get_web_audio_r_ref(),2048);
  const blocks=[];
  let dataBytes=0, peak=0;
  const firstFrame=core._get_logic_frame();
  for(let i=0;i<frames;i++) {
    const count=machine.frame();
    const block=Buffer.alloc(count*4);
    for(let j=0;j<count;j++) {
      const l=left[j], r=right[j];
      assert.ok(Number.isFinite(l) && Number.isFinite(r),
        'Non-finite native audio in '+label);
      peak=Math.max(peak,Math.abs(l),Math.abs(r));
      block.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(l*32767))),j*4);
      block.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(r*32767))),j*4+2);
    }
    blocks.push(block);
    dataBytes+=block.length;
  }
  assert.ok(dataBytes>0 && peak>0.0001,'Native scene audio missing: '+label);
  const wav=Buffer.alloc(44+dataBytes);
  wav.write('RIFF',0,'ascii');wav.writeUInt32LE(wav.length-8,4);
  wav.write('WAVE',8,'ascii');wav.write('fmt ',12,'ascii');
  wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
  wav.writeUInt16LE(2,22);wav.writeUInt32LE(44100,24);
  wav.writeUInt32LE(44100*4,28);wav.writeUInt16LE(4,32);
  wav.writeUInt16LE(16,34);wav.write('data',36,'ascii');
  wav.writeUInt32LE(dataBytes,40);
  let at=44;
  for(const block of blocks) {block.copy(wav,at);at+=block.length;}
  fs.writeFileSync(path.join(output,label+'.wav'),wav);
  return {label, region:label.startsWith('ntsc')?'NTSC':'PAL',
    firstNativeFrame:firstFrame,lastNativeFrame:core._get_logic_frame(),
    durationSeconds:frames/fps, stereoSampleFrames:dataBytes/4,
    peak,sha256:crypto.createHash('sha256').update(wav).digest('hex')};
}


(async () => {
  fs.mkdirSync(output,{recursive:true});
  const rom=fs.readFileSync(romFile);
  const report=JSON.parse(fs.readFileSync(reportFile,'utf8'));
  assert.equal(approved.version,'0.3.8');
  assert.equal(rom.length,approved.size);
  assert.equal(report.sha256,approved.sha256);
  assert.equal(report.music.musicLabPreview,false);
  assert.deepEqual(fs.readFileSync(path.join(root,'site',approved.path)),rom);
  assert.equal(report.music.lengthSeconds,180);
  assert.equal(report.music.steps,900);
  assert.equal(report.music.tempoBPM,150);
  assert.equal(report.music.eventStrideBytes,16);
  assert.deepEqual(report.music.fmChannels,[0,1,2,3,4,5]);
  assert.equal(report.music.eventBytes,14400);
  assert.equal(report.sha256,crypto.createHash('sha256').update(rom).digest('hex'));
  const captures=[], audioClips=[];
  for (const [region,fps,idle,label] of [[1,60,600,'ntsc'],[2,50,500,'pal']]) {
    const m=await machine(region,rom);
    m.run(15);
    captures.push(m.capture(label+'-title'));
    m.run(idle+20);
    captures.push(m.capture(label+'-intro'));
    const left=new Float32Array(m.core.HEAPF32.buffer,m.core._get_web_audio_l_ref(),2048);
    const mem=new DataView(m.core.HEAPU8.buffer);
    const base=m.core._get_logic_ram_ref();
    const readWord=offset=>mem.getUint16(base+offset,true);
    let audibleSamples=0, audioFrames=0, lastCount=0,peak=0;
    for(let i=0;i<20;i++){
      lastCount=m.frame();
      if(lastCount>0) audioFrames++;
      for(let sample=0;sample<lastCount;sample++){
        const value=left[sample];
        peak=Math.max(peak,Math.abs(value));
        if(Number.isFinite(value) && Math.abs(value)>0.0001) audibleSamples++;
      }
    }
    console.log('SHOW AUDIO TRACE',JSON.stringify({
      region,frame:m.core._get_logic_frame(),cpuFlags:m.core._get_logic_cpu_flags(),
      songAccumulator:readWord(0),songIndex:readWord(2),active:readWord(6),
      cadence:readWord(8),audioFrames,lastCount,peak,audibleSamples
    }));
    assert.equal(readWord(6),1,'Original show must be active after idle and before score verification');
    assert.ok(audibleSamples>0,'YM2612/PSG score must generate non-silent native audio samples');
    // Capture original FM/PSG output directly from the WASM native audio
    // buffers, not a browser overlay or synthetic/offline soundtrack.
    // Fourteen seconds covers a complete scene chord cycle, rather than
    // the old four-second opening that did not allow meaningful listening.
    const clipFrames=14*fps;
    audioClips.push(recordSceneAudio(m,label+'-original-score',clipFrames,fps));
    m.run(20*fps+20-clipFrames);
    captures.push(m.capture(label+'-vortex'));
    audioClips.push(recordSceneAudio(m,label+'-chromatic-vortex',clipFrames,fps));
    m.run(30*fps+20-clipFrames);
    captures.push(m.capture(label+'-aurora'));
    audioClips.push(recordSceneAudio(m,label+'-neon-aurora',clipFrames,fps));
    m.run(30*fps+20-clipFrames);
    captures.push(m.capture(label+'-sprites'));
    audioClips.push(recordSceneAudio(m,label+'-sprite-storm',clipFrames,fps));
    m.run(35*fps+20-clipFrames);
    captures.push(m.capture(label+'-reactor'));
    audioClips.push(recordSceneAudio(m,label+'-chroma-reactor',clipFrames,fps));
    m.press('C');m.run(8);
    captures.push(m.capture(label+'-interactive-max'));
    m.press('B');m.run(8);
    captures.push(m.capture(label+'-interactive-restored'));
    m.run(40*fps-25-clipFrames);
    captures.push(m.capture(label+'-finale'));
    audioClips.push(recordSceneAudio(m,label+'-finale',clipFrames,fps));
    assert.ok(m.core._get_logic_frame()>160*fps,
      'Show must advance through the 160-second scene boundary on real WASM');
    let returnedToMenu=false, restarted=false;
    for (let i=0;i<45*fps;i++) {
      m.frame();
      if (readWord(6)===0) returnedToMenu=true;
      if (returnedToMenu && readWord(6)===1 && readWord(2)<40) {
        restarted=true;
        break;
      }
    }
    assert.ok(returnedToMenu,'The complete show returns to its original menu');
    assert.ok(restarted,'The next full show starts with a fresh score index');
    assert.equal(m.core._get_logic_cpu_flags(),0,'The full loop does not HALT or STOP');

    // Reuse the original cartridge's deterministic side-by-side VDP check
    // against this approved image in both regional modes.
    const bent=await machine(region,rom), reference=await machine(region,rom);
    for (const player of [bent,reference]) {
      player.run(15);
      player.press('down');player.press('down');player.press('down');
      player.press('A');player.run(30);
    }
    assert.deepEqual(visiblePixels(bent.core),visiblePixels(reference.core));
    bent.press('A');reference.run(3);bent.run(7);reference.run(7);
    const levelOne=visiblePixels(bent.core);
    assert.notDeepEqual(levelOne,visiblePixels(reference.core),
      'A changes actual VDP output in the approved cartridge');
    bent.press('B');reference.run(3);bent.run(7);reference.run(7);
    assert.deepEqual(visiblePixels(bent.core),visiblePixels(reference.core),
      'B restores byte-exact clean CRAM/HScroll output');
    bent.press('C');reference.run(3);bent.run(7);reference.run(7);
    assert.notDeepEqual(visiblePixels(bent.core),visiblePixels(reference.core),
      'C applies maximum native distortion');
    assert.notDeepEqual(visiblePixels(bent.core),levelOne);
    const beforeMenu=visiblePixels(bent.core);
    bent.press('START');bent.run(10);
    assert.notDeepEqual(visiblePixels(bent.core),beforeMenu,
      'START returns from Chroma Reactor to the cartridge menu');
  }
  assert.equal(audioClips.length,12,'Six separate native score excerpts in each region');
  assert.ok(audioClips.every(x=>x.durationSeconds===14 && x.stereoSampleFrames>0));
  const ntsc=captures.filter(x=>x.region===1);
  assert.ok(new Set(ntsc.map(x=>x.rgbaSHA256)).size>=5,
    'Six-scene native show must show visually distinct stages');
  fs.writeFileSync(path.join(output,'show_report.json'),
    JSON.stringify({romSHA256:report.sha256,music:report.music,captures,audioClips},null,2));
  console.log('Original 180-second Mega Drive show verified in native NTSC/PAL WASM');
})().catch(err=>{console.error(err);process.exitCode=1;});
