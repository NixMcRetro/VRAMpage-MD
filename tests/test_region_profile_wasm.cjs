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
function cartridge(country = 'U', activeLines = 224, interlaced = false) {
  const rom = new Uint8Array(0x10000), v = new DataView(rom.buffer);
  for (let p = 0; p < 0x100; p += 4) v.setUint32(p, 0x300);
  v.setUint32(0, 0xffff00); v.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('REGION PROFILE TEST'), 0x120);
  rom.set(Buffer.from(country), 0x1f0);
  v.setUint32(0x1a4, rom.length - 1); v.setUint32(0x1a8, 0xff0000); v.setUint32(0x1ac, 0xffffff);
  const words = [];
  const word=(address,value)=>words.push(0x33fc,value,address>>>16,address&0xffff);
  const byte=(address,value)=>words.push(0x13fc,value,address>>>16,address&0xffff);
  word(0xc00004,0x8004);
  word(0xc00004,activeLines===240?0x814c:0x8144);
  word(0xc00004,interlaced?0x8c02:0x8c00);
  word(0xc00004,0x8f02);
  words.push(0x23fc,0xc000,0x0000,0x00c0,0x0004);
  word(0xc00000,0x000e);
  byte(0xc00011,0x8a);byte(0xc00011,0x10);byte(0xc00011,0x90);
  words.push(0x13f9,0x00a1,0x0001,0x00ff,0x1002); // Save the software-visible version register.
  words.push(0x5279,0x00ff,0x1000,0x60f8);
  words.forEach((word, index) => v.setUint16(0x200 + index * 2, word));
  v.setUint16(0x300, 0x4e72); v.setUint16(0x302, 0x2700); v.setUint16(0x304, 0x60fe);
  return rom;
}
async function start(core, request, country, activeLines = 224, interlaced = false) {
  assert.equal(core._set_region_request(request), 0);
  core.HEAPU8.set(cartridge(country, activeLines, interlaced), core._get_rom_buffer_ref(0x10000));
  core._start();
  return core;
}
function rendered(core) {
  const frame = core._get_frame_buffer_ref();
  const count = core._sound();
  const lp = core._get_web_audio_l_ref() >>> 2, rp = core._get_web_audio_r_ref() >>> 2;
  assert.ok(count >= 700 && count <= 1024, `audio count ${count} fits the 2048-interleaved-sample allocation`);
  const left = Array.from(core.HEAPF32.subarray(lp, lp + count));
  const right = Array.from(core.HEAPF32.subarray(rp, rp + count));
  assert.ok(left.concat(right).every(Number.isFinite));
  const ram = core._get_logic_ram_ref();
  return {frame: Buffer.from(core.HEAPU8.subarray(frame, frame + FRAME_BYTES)),
    ram: Buffer.from(core.HEAPU8.subarray(ram, ram + 0x10000)), left, right};
}
function tickToViewport(core) {
  core._wasm_input_update(); core._tick(); core._sound();
  core._tick();
}

(async () => {
  const untouched = await factory(normalFile);
  assert.equal(typeof untouched._set_region_request, 'undefined', 'normal profile has no region API');
  assert.equal(typeof untouched._get_region_state, 'undefined', 'normal profile has no region state API');

  const unstarted = await factory(runtimeFile);
  unstarted._init();
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
    const core = await start(unstarted, item.id, item.country);
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
    if (item.id === 0) {
      const active = {regionCode:state.regionCode,pal:state.pal,masterClock:state.masterClock,
        frameRate:state.frameRate,linesPerFrame:state.linesPerFrame,width:state.width,height:state.height,
        interlaced:state.interlaced};
      assert.equal(core._set_region_request(1), 0);
      const staged = core._get_region_state();
      assert.equal(staged.requestedRegion, 1);
      assert.deepEqual({regionCode:staged.regionCode,pal:staged.pal,masterClock:staged.masterClock,
        frameRate:staged.frameRate,linesPerFrame:staged.linesPerFrame,width:staged.width,
        height:staged.height,interlaced:staged.interlaced}, active,
      'staging a valid selection does not change the live effective machine');
    }
    tickToViewport(core);
    assert.equal(core._get_region_state().width, 256, 'active Mode 5 width follows the native viewport');
    assert.equal(core._get_region_state().height, 224, 'PAL and NTSC can both render 224 active lines');
    const audio = rendered(core);
    assert.ok(audio.frame.some((v,i)=>i%4===0&&v>0),'nonzero red backdrop exercises framebuffer parity');
    assert.ok(audio.left.some(v=>v!==0)||audio.right.some(v=>v!==0),'nonzero PSG samples exercise PCM parity');
    assert.ok(audio.ram[0x1000]||audio.ram[0x1001],'eligible synthetic code updates Work RAM');
    assert.equal(audio.ram[0x1003]&0xc0,item.code,'software-visible region agrees (native RAM byte lanes are swapped)');
    assert.ok(Math.abs(audio.left.length-44100/state.frameRate)<8,'generated sample count follows native cadence');
    if (item.id === 1) {
      const legacy = await factory(normalFile);
      legacy._init(); legacy.HEAPU8.set(cartridge(item.country), legacy._get_rom_buffer_ref(0x10000)); legacy._start();
      tickToViewport(legacy);
      assert.deepEqual(audio, rendered(legacy), 'default NTSC-U framebuffer and PCM match normal runtime');
    }
  }

  const autoJapan = await start(unstarted, 0, 'J');
  assert.equal(autoJapan._get_region_state().regionCode, 0x00, 'Auto follows the ROM Japan header');
  assert.equal(autoJapan._get_region_state().linesPerFrame, 262);
  const pal240 = await start(unstarted, 2, 'U', 240);
  tickToViewport(pal240);
  assert.equal(pal240._get_region_state().height, 240, 'native active viewport reports 240 lines when VDP mode selects it');
  const interlace = await start(unstarted, 3, 'U', 224, true);
  tickToViewport(interlace);
  assert.equal(interlace._get_region_state().interlaced, true);
  assert.equal(interlace._get_region_state().height, 224,
    'interlace reports its native rendered height while double-resolution output is disabled');
  console.log('PASS native region profile API, timing, viewport bounds, audio bounds, Auto detection and NTSC-U parity');
})().catch(error => { console.error(error); process.exitCode = 1; });
