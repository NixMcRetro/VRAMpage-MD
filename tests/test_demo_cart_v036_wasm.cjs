/* Run the exact experimental Demo Cart inside compiled Genesis Plus GX WASM.
 * This is a runtime probe, not a replacement for human visual acceptance.
 * Usage: node tests/test_demo_cart_v035_wasm.cjs site/core/genplus.js
 */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const coreFile = path.resolve(process.argv[2] || 'site/core/genplus.js');
const romFile = path.join(root, 'demo-cart/show-lab/build/VRAMpage-MD-Demo-Cart-v0.3.6-Show.bin');
const reportFile = path.join(root, 'demo-cart/show-lab/build/rom_report.json');
const output = path.join(root, 'artifacts/demo-cart-v036-genplus');
const WIDTH = 320, HEIGHT = 224, PITCH = 640;
const PREVIOUS_SHA = 'ba276ed3aa7d6876684c60a7c49a6cf2febddfec8f94867cd85db8b0181f72e1';
// Pin the new v0.3.5 digest after the first real Genesis Plus GX build report is inspected.
const EXPECTED_SHA = '89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f';

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


(async () => {
  fs.mkdirSync(output,{recursive:true});
  const rom=fs.readFileSync(romFile);
  const report=JSON.parse(fs.readFileSync(reportFile,'utf8'));
  assert.equal(report.music.lengthSeconds,180);
  assert.equal(report.music.steps,720);
  assert.equal(report.sha256,crypto.createHash('sha256').update(rom).digest('hex'));
  const captures=[];
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
    const right=new Float32Array(m.core.HEAPF32.buffer,m.core._get_web_audio_r_ref(),2048);
    const clipFrames=4*fps, pcm=[];
    for(let i=0;i<clipFrames;i++){
      const count=m.frame();
      for(let j=0;j<count;j++){
        pcm.push(Math.max(-32768,Math.min(32767,Math.round(left[j]*32767))));
        pcm.push(Math.max(-32768,Math.min(32767,Math.round(right[j]*32767))));
      }
    }
    const riff=Buffer.alloc(44+pcm.length*2);
    riff.write('RIFF',0,'ascii');riff.writeUInt32LE(riff.length-8,4);
    riff.write('WAVE',8,'ascii');riff.write('fmt ',12,'ascii');
    riff.writeUInt32LE(16,16);riff.writeUInt16LE(1,20);
    riff.writeUInt16LE(2,22);riff.writeUInt32LE(44100,24);
    riff.writeUInt32LE(44100*4,28);riff.writeUInt16LE(4,32);
    riff.writeUInt16LE(16,34);riff.write('data',36,'ascii');
    riff.writeUInt32LE(pcm.length*2,40);
    for(let j=0;j<pcm.length;j++)riff.writeInt16LE(pcm[j],44+j*2);
    fs.writeFileSync(path.join(output,label+'-original-score.wav'),riff);
    m.run(20*fps+20-clipFrames);
    captures.push(m.capture(label+'-vortex'));
    m.run(30*fps+20);
    captures.push(m.capture(label+'-aurora'));
    m.run(30*fps+20);
    captures.push(m.capture(label+'-sprites'));
    m.run(35*fps+20);
    captures.push(m.capture(label+'-reactor'));
    m.press('C');m.run(8);
    captures.push(m.capture(label+'-interactive-max'));
    m.press('B');m.run(8);
    captures.push(m.capture(label+'-interactive-restored'));
    m.run(40*fps-25);
    captures.push(m.capture(label+'-finale'));
    assert.ok(m.core._get_logic_frame()>160*fps,
      'Show must advance through the 160-second scene boundary on real WASM');
  }
  const ntsc=captures.filter(x=>x.region===1);
  assert.ok(new Set(ntsc.map(x=>x.rgbaSHA256)).size>=5,
    'Six-scene native show must show visually distinct stages');
  fs.writeFileSync(path.join(output,'show_report.json'),
    JSON.stringify({romSHA256:report.sha256,music:report.music,captures},null,2));
  console.log('Original 180-second Mega Drive show verified in native NTSC/PAL WASM');
})().catch(err=>{console.error(err);process.exitCode=1;});
