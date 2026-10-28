'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
if (!process.argv[2] || !process.argv[3]) throw new Error('Pass runtime and normal genplus.js paths.');
const runtimeFile = path.resolve(process.argv[2]);
const normalFile = path.resolve(process.argv[3]);
const FRAME_BYTES = 640 * 480 * 4;

function factory(file) {
  return require(file)({locateFile: name => path.join(path.dirname(file), name)});
}
function cartridge(country = 'U') {
  const rom = new Uint8Array(0x10000), v = new DataView(rom.buffer);
  for (let p = 0; p < 0x100; p += 4) v.setUint32(p, 0x300);
  v.setUint32(0, 0xffff00); v.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('REGION PROFILE TEST'), 0x120);
  rom.set(Buffer.from(country), 0x1f0);
  v.setUint32(0x1a4, rom.length - 1); v.setUint32(0x1a8, 0xff0000); v.setUint32(0x1ac, 0xffffff);
  v.setUint16(0x200, 0x60fe);
  v.setUint16(0x300, 0x4e72); v.setUint16(0x302, 0x2700); v.setUint16(0x304, 0x60fe);
  return rom;
}
async function start(file, request, country) {
  const core = await factory(file);
  core._init();
  if (typeof core._set_region_request === 'function') assert.equal(core._set_region_request(request), 0);
  core.HEAPU8.set(cartridge(country), core._get_rom_buffer_ref(0x10000));
  core._start();
  return core;
}
function rendered(core) {
  const frame = core._get_frame_buffer_ref();
  const count = core._sound();
  const lp = core._get_web_audio_l_ref() >>> 2, rp = core._get_web_audio_r_ref() >>> 2;
  assert.ok(count >= 0 && count <= 1024, `audio count ${count} fits the 2048-interleaved-sample allocation`);
  const left = Array.from(core.HEAPF32.subarray(lp, lp + count));
  const right = Array.from(core.HEAPF32.subarray(rp, rp + count));
  assert.ok(left.concat(right).every(Number.isFinite));
  return {frame: Buffer.from(core.HEAPU8.subarray(frame, frame + FRAME_BYTES)), left, right};
}

(async () => {
  const untouched = await factory(normalFile);
  assert.equal(typeof untouched._set_region_request, 'undefined', 'normal profile has no region API');
  assert.equal(typeof untouched._get_region_state, 'undefined', 'normal profile has no region state API');

  const unstarted = await factory(runtimeFile);
  const before = unstarted._get_region_state();
  assert.deepEqual(before, {schemaVersion:1,available:true,loaded:false,requestedRegion:1,
    regionCode:null,pal:null,masterClock:null,frameRate:null,linesPerFrame:null,width:null,height:null,interlaced:null});
  assert.equal(unstarted._set_region_request(-1), 1);
  assert.equal(unstarted._set_region_request(5), 1);
  assert.equal(unstarted._set_region_request(1.5), 1);
  assert.deepEqual(unstarted._get_region_state(), before, 'invalid IDs leave staged state unchanged');

  const expected = [
    {id:0,country:'E',code:0xc0,pal:true,clock:53203424,lines:313},
    {id:1,country:'J',code:0x80,pal:false,clock:53693175,lines:262},
    {id:2,country:'U',code:0xc0,pal:true,clock:53203424,lines:313},
    {id:3,country:'E',code:0x00,pal:false,clock:53693175,lines:262},
    {id:4,country:'U',code:0x40,pal:true,clock:53203424,lines:313}
  ];
  for (const item of expected) {
    const core = await start(runtimeFile, item.id, item.country);
    const state = core._get_region_state();
    assert.equal(state.loaded, true);
    assert.equal(state.requestedRegion, item.id);
    assert.equal(state.regionCode, item.code);
    assert.equal(state.pal, item.pal);
    assert.equal(state.masterClock, item.clock);
    assert.equal(state.linesPerFrame, item.lines);
    assert.ok(state.width >= 256 && state.width <= 320, `reported rendered width ${state.width}`);
    assert.ok(state.height >= 192 && state.height <= 480, `reported rendered height ${state.height}`);
    assert.equal(state.interlaced, false);
    const frequency = item.pal ? 53203424 / (3420 * 313) : 53693175 / (3420 * 262);
    assert.ok(Math.abs(state.frameRate - frequency) < 1e-9);
    core._wasm_input_update(); core._tick();
    const audio = rendered(core);
    if (item.id === 1) {
      const legacy = await start(normalFile, 1, item.country);
      legacy._wasm_input_update(); legacy._tick();
      assert.deepEqual(audio, rendered(legacy), 'default NTSC-U framebuffer and PCM match normal runtime');
    }
  }

  const autoJapan = await start(runtimeFile, 0, 'J');
  assert.equal(autoJapan._get_region_state().regionCode, 0x00, 'Auto follows the ROM Japan header');
  assert.equal(autoJapan._get_region_state().linesPerFrame, 262);
  console.log('PASS native region profile API, timing, viewport bounds, audio bounds, Auto detection and NTSC-U parity');
})().catch(error => { console.error(error); process.exitCode = 1; });
