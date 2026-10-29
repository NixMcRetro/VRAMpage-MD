'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const path = require('node:path');
assert.ok(process.argv[2], 'Pass the production runtime core path');
const corePath = path.resolve(process.argv[2]);
const factory = require(corePath);
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

// Original synthetic programs exercise VDP/audio, pad protocols and ordinary SRAM.
function cartridge(kind = 'dynamic') {
  const rom = new Uint8Array(0x10000), v = new DataView(rom.buffer), w = [];
  for (let p = 0; p < 0x100; p += 4) v.setUint32(p, 0x300);
  v.setUint32(0, 0xffff00); v.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE ORIGINAL CHECKPOINT TEST'), 0x120);
  v.setUint32(0x1a4, rom.length - 1); v.setUint32(0x1a8, 0xff0000); v.setUint32(0x1ac, 0xffffff);
  rom[0x1f0] = 0x55;
  const word = (a, x) => w.push(0x33fc, x, a >>> 16, a & 0xffff);
  const byte = (a, x) => w.push(0x13fc, x, a >>> 16, a & 0xffff);
  const branch = loop => w.push(0x6000 | ((2 * (loop - (w.length + 1))) & 0xff));
  if (kind === 'dynamic') {
    word(0xc00004, 0x8004); word(0xc00004, 0x8144); word(0xc00004, 0x8c81);
    word(0xc00004, 0x8f02); word(0xc00004, 0x8701);
    byte(0xc00011, 0x8a); byte(0xc00011, 0x10); byte(0xc00011, 0x90);
    const loop = w.length;
    word(0xc00004, 0xc002); word(0xc00004, 0);
    w.push(0x5279, 0x00ff, 0x1000, 0x3039, 0x00ff, 0x1000, 0x33c0, 0x00c0, 0x0000);
    branch(loop);
  } else if (kind === 'pad6') {
    rom[0x190] = '6'.charCodeAt(0);
    byte(0xa10009, 0x40);
    const loop = w.length;
    for (let i = 0; i < 3; i++) { byte(0xa10003, 0); byte(0xa10003, 0x40); }
    w.push(0x1039, 0x00a1, 0x0003, 0x3239, 0x00ff, 0x0000, 0xd240, 0x33c1, 0x00ff, 0x0000);
    branch(loop);
  } else if (kind === 'pad3') {
    const loop = w.length;
    w.push(0x1039, 0x00a1, 0x0003, 0x33c0, 0x00ff, 0x0000);
    branch(loop);
  } else {
    rom.set(Buffer.from('RA'), 0x1b0); rom[0x1b2] = 0xe0;
    v.setUint32(0x1b4, 0x200000); v.setUint32(0x1b8, 0x20ffff);
    if (kind === 'protected-sram') byte(0xa130f1, 3);
    const loop = w.length;
    if (kind === 'protected-sram') {
      // B enables writes once; neutral never reapplies protection. Replay needs the saved handlers.
      w.push(0x1039, 0x00a1, 0x0003, 0x0200, 0x0010, 0x6608);
      byte(0xa130f1, 1);
    }
    w.push(0x3039, 0x0020, 0x0000, 0x5240, 0x33c0, 0x0020, 0x0000, 0x33c0, 0x00ff, 0x0000);
    branch(loop);
  }
  assert.ok(0x200 + 2 * w.length < 0x300);
  w.forEach((x, i) => v.setUint16(0x200 + 2 * i, x));
  [0x4e72, 0x2700, 0x60fe].forEach((x, i) => v.setUint16(0x300 + 2 * i, x));
  return rom;
}
function fmCartridge() {
  const rom = cartridge(), v = new DataView(rom.buffer), z = [], w = [];
  v.setUint32(4, 0x800);
  const fm = (a, x) => z.push(0x3e, a, 0x32, 0, 0x40, 0x3e, x, 0x32, 1, 0x40);
  fm(0x22, 0); fm(0x27, 0);
  for (const o of [0, 4, 8, 12]) {
    fm(0x30 + o, 1); fm(0x50 + o, 0x1f); fm(0x60 + o, 0); fm(0x70 + o, 0);
    fm(0x80 + o, 0x0f); fm(0x40 + o, o === 12 ? 0 : 0x7f);
  }
  fm(0xb0, 7); fm(0xb4, 0xc0); fm(0xa0, 0x98); fm(0xa4, 0x22); fm(0x28, 0xf0);
  z.push(0x18, 0xfe);
  const word = (a, x) => w.push(0x33fc, x, a >>> 16, a & 0xffff);
  const byte = (a, x) => w.push(0x13fc, x, a >>> 16, a & 0xffff);
  word(0xa11100, 0x100); word(0xa11200, 0x100);
  z.forEach((x, i) => byte(0xa00000 + i, x)); word(0xa11100, 0); w.push(0x60fe);
  w.forEach((x, i) => v.setUint16(0x800 + 2 * i, x));
  return rom;
}
function neutral(c, buttons = []) {
  const input = new Float32Array(c.HEAPF32.buffer, c._get_input_buffer_ref(), 32);
  input.fill(0); for (const b of buttons) input[b] = 1;
  c._wasm_input_update();
}
async function create(kind) {
  const c = await factory({locateFile: n => path.join(path.dirname(corePath), n)});
  c._init(); install(c, cartridge(kind));
  assert.equal(c._get_session_checkpoint_support(), 1, `${kind}: ordinary profile supports checkpoints`);
  assert.equal(c._get_session_checkpoint_ready(), 0);
  assert.equal(c._restore_session_checkpoint(), 3);
  return c;
}
function install(c, rom) { c.HEAPU8.set(rom, c._get_rom_buffer_ref(rom.length)); c._start(); neutral(c); }
function pixels(c) { const p = c._get_frame_buffer_ref(); return hash(c.HEAPU8.subarray(p, p + 640 * 480 * 4)); }
function ram(c) { const p = c._get_logic_ram_ref(); return hash(c.HEAPU8.subarray(p, p + 0x10000)); }
function frame(c, buttons = []) {
  neutral(c, buttons); c._tick(); const count = c._sound();
  const lp = c._get_web_audio_l_ref() >>> 2, rp = c._get_web_audio_r_ref() >>> 2;
  const left = Float32Array.from(c.HEAPF32.subarray(lp, lp + count));
  const right = Float32Array.from(c.HEAPF32.subarray(rp, rp + count));
  assert.ok([...left, ...right].every(Number.isFinite));
  return {count, pixels: pixels(c), ram: ram(c), left: hash(Buffer.from(left.buffer)), right: hash(Buffer.from(right.buffer)),
    nonzero: [...left, ...right].some(x => Math.abs(x) > 0.0001)};
}
function save(c) {
  neutral(c); const before = c._get_logic_frame();
  assert.equal(c._save_session_checkpoint(), 0);
  assert.equal(c._get_session_checkpoint_saved_frame(), before);
  assert.equal(c._get_logic_frame(), before, 'capture must not advance a frame');
  assert.equal(c._get_session_checkpoint_ready(), 1);
}
function restore(c, image) {
  neutral(c); const before = c._get_logic_frame();
  assert.equal(c._restore_session_checkpoint(), 0);
  assert.equal(c._get_logic_frame(), before, 'restore keeps monotonic experiment bookkeeping and never ticks');
  assert.equal(pixels(c), image, 'saved raw image is available before any emulation frame');
  assert.equal(c._get_session_checkpoint_ready(), 1, 'slot remains reusable');
}
async function fmOutputModelCore(model, region=1) {
  const c = await factory({locateFile: n => path.join(path.dirname(corePath), n)});
  c._init();
  assert.equal(c._set_region_request(region), 0);
  assert.equal(c._set_fm_output_model_request(model), 0);
  install(c, fmCartridge());
  const state=c._get_fm_output_model_state();
  assert.equal(state.effectiveModel, model===0?'discrete':'integrated');
  assert.equal(state.backend,'mame-opn2');
  const regionState=c._get_region_state();
  assert.equal(regionState.regionCode,region===2?0xc0:0x80,
    'selected Region is active alongside the FM Output Model');
  return c;
}
function modelProofFrames(c) { return Array.from({length: 6}, () => frame(c)); }
(async () => {
  let groups = 0;
  if (process.argv[3]) {
    const normalPath = path.resolve(process.argv[3]);
    const legacy = await require(normalPath)({locateFile: n => path.join(path.dirname(normalPath), n)});
    for (const name of ['save_session_checkpoint', 'restore_session_checkpoint', 'discard_session_checkpoint',
      'get_session_checkpoint_support', 'get_session_checkpoint_ready', 'get_session_checkpoint_saved_frame']) {
      assert.equal(typeof legacy[`_${name}`], 'undefined', 'normal profile remains checkpoint-free');
    }
    for (const name of ['set_fm_output_model_request','get_fm_output_model_state'])
      assert.equal(typeof legacy[`_${name}`], 'undefined', 'normal profile has no FM Output Model API');
  }
  const c = await create('dynamic'); frame(c); save(c); const savedImage = pixels(c), savedFrame = c._get_session_checkpoint_saved_frame();
  const first = Array.from({length: 6}, () => frame(c));
  assert.ok(first.some(x => x.nonzero), 'synthetic PSG produces nonzero PCM');
  assert.ok(new Set(first.map(x => x.pixels)).size > 1, 'VDP scene changes across frames');
  assert.notEqual(pixels(c), savedImage);
  restore(c, savedImage);
  assert.deepEqual(Array.from({length: 6}, () => frame(c)), first, 'dynamic video/audio/WRAM continuation replays exactly'); groups++;

  // Current faults and held inputs must not hide an existing slot/profile from the UI.
  const setters = [
    [() => c._set_logic_fault(2, 2, 0, 1), () => c._set_logic_fault(0, 0, -1, -1)],
    [() => c._set_logic_address_mask(1, 2), () => c._set_logic_address_mask(0, 2)],
    [() => c._set_vram_fault_model(1, 8, -1, -1), () => c._set_vram_fault_model(1, 0, -1, -1)],
    [() => c._set_psg_data_bridge(1, 0, 1), () => c._set_psg_data_bridge(0, -1, -1)],
    [() => c._set_fm_data_bridge(1, 0, 1), () => c._set_fm_data_bridge(0, -1, -1)]
  ];
  for (const [set, clear] of setters) {
    assert.equal(set(), 0); const state = ram(c);
    assert.equal(c._get_session_checkpoint_support(), 1); assert.equal(c._get_session_checkpoint_ready(), 1);
    assert.equal(c._save_session_checkpoint(), 2); assert.equal(c._restore_session_checkpoint(), 2);
    assert.equal(ram(c), state, 'unsafe refusal does not load state');
    assert.equal(c._get_session_checkpoint_saved_frame(), savedFrame, 'failed replacement retains old slot');
    assert.equal(clear(), 0);
  }
  assert.equal(c._set_z80_ram_bridge(1, 0, 1), 0);
  const z80FaultRam = ram(c), z80FaultState = c._get_z80_ram_bridge_state();
  assert.equal(c._save_session_checkpoint(), 2, 'active Z80 RAM contact refuses checkpoint capture');
  assert.equal(c._get_z80_ram_bridge_state().configured, true);
  assert.equal(c._restore_session_checkpoint(), 2, 'restore refuses while the contact remains configured');
  assert.equal(c._get_z80_ram_bridge_state().configured, true, 'refusal preserves contact configuration');
  assert.equal(c._get_z80_ram_bridge_state().ramWrites, z80FaultState.ramWrites, 'refusal preserves contact counters');
  assert.equal(ram(c), z80FaultRam, 'refusal does not load state or mutate RAM');
  assert.equal(c._set_z80_ram_bridge(0, -1, -1), 0);
  assert.equal(c._restore_session_checkpoint(), 0, 'restore succeeds after frontend-style explicit disconnect');
  assert.equal(c._get_z80_ram_bridge_state().configured, false);
  neutral(c, [11]); assert.equal(c._get_session_checkpoint_support(), 1); assert.equal(c._save_session_checkpoint(), 2);
  assert.equal(c._restore_session_checkpoint(), 2); neutral(c); restore(c, savedImage); groups++;
  assert.equal(c._recover_logic_cpu(2), 0); assert.equal(c._get_session_checkpoint_ready(), 1);
  restore(c, savedImage); assert.deepEqual(Array.from({length: 6}, () => frame(c)), first, 'CPU-only reset retains replay slot'); groups++;
  c._discard_session_checkpoint(); assert.equal(c._get_session_checkpoint_ready(), 0); assert.equal(c._restore_session_checkpoint(), 3);
  save(c);
  assert.equal(c._set_logic_address_mask(1, 2), 0);
  assert.equal(c._set_vram_fault_model(1, 8, -1, -1), 0);
  assert.equal(c._set_psg_data_bridge(1, 0, 1), 0);
  assert.equal(c._set_fm_data_bridge(1, 0, 1), 0);
  assert.equal(c._set_z80_ram_bridge(1, 0, 1), 0);
  c._start(); assert.equal(c._get_session_checkpoint_ready(), 0);
  assert.equal(c._get_logic_address_mask(), 0); assert.equal(c._get_logic_frame(), 0);
  assert.equal(c._get_vram_fault_model_state().effective, false);
  assert.equal(c._get_psg_data_bridge_state().configured, false);
  assert.equal(c._get_fm_data_bridge_state().configured, false);
  assert.equal(c._get_z80_ram_bridge_state().configured, false);
  neutral(c); save(c); install(c, cartridge('pad3')); assert.equal(c._get_session_checkpoint_ready(), 0); groups++;

  const fm = await create('dynamic'); install(fm, fmCartridge());
  for (let i = 0; i < 8; i++) frame(fm);
  save(fm); const fmImage = pixels(fm);
  const fmFirst = Array.from({length: 6}, () => frame(fm));
  assert.ok(fmFirst.some(x => x.nonzero), 'FM-only cartridge produces nonzero PCM');
  restore(fm, fmImage);
  assert.deepEqual(Array.from({length: 6}, () => frame(fm)), fmFirst, 'FM continuation replays exact PCM'); groups++;

  assert.equal(typeof c._set_fm_output_model_request,'function',
    'runtime profile exposes staged FM Output Model selection');
  {
    const modelOutputs = new Map();
    for (const region of [1, 2]) for (const model of [0, 1]) {
      const c = await fmOutputModelCore(model, region);
      for (let i = 0; i < 8; i++) frame(c);
      const warm = frame(c);
      assert.ok(warm.nonzero, `model ${model}: FM ROM produces native nonzero PCM`);
      save(c);
      const image = pixels(c);
      const expected = modelProofFrames(c);
      assert.ok(expected.some(x => x.nonzero));
      assert.equal(c._get_fm_output_model_state().effectiveModel,model===0?'discrete':'integrated');

      assert.equal(c._set_fm_output_model_request(1 - model), 0);
      assert.equal(c._get_fm_output_model_state().effectiveModel,model===0?'discrete':'integrated',
        'pending model cannot alter active MAME model');
      assert.equal(c._get_fm_output_model_state().requestedModel,model===0?'integrated':'discrete');
      assert.equal(c._get_session_checkpoint_ready(), 1,
        'pending model change preserves live checkpoint slot');
      assert.equal(c._set_fm_output_model_request(2), 1, 'unsupported model request rejects');
      assert.equal(c._get_fm_output_model_state().requestedModel,model===0?'integrated':'discrete',
        'rejected request is atomic');
      assert.equal(c._get_session_checkpoint_ready(), 1,
        'rejected request preserves live checkpoint slot');

      assert.equal(c._recover_logic_cpu(2), 0, 'CPU Reset succeeds during model lifetime');
      assert.equal(c._get_fm_output_model_state().effectiveModel,model===0?'discrete':'integrated',
        'CPU Reset retains active MAME model');
      assert.equal(c._get_session_checkpoint_ready(), 1,
        'CPU Reset retains checkpoint for same-model restore');
      restore(c, image);
      assert.deepEqual(modelProofFrames(c), expected,
        'save, CPU Reset, restore replays exact model-specific native output');

      const replacement = 1 - model;
      const replacementRegion=region;
      assert.equal(c._get_session_checkpoint_ready(), 1);
      assert.equal(c._set_region_request(replacementRegion),0,
        'pending Region remains independently staged beside FM model');
      install(c, fmCartridge());
      assert.equal(c._get_session_checkpoint_ready(), 0,
        'Clean Restart/new ROM discards prior-model checkpoint before activation');
      assert.equal(c._get_fm_output_model_state().effectiveModel,replacement===0?'discrete':'integrated',
        'Clean Restart applies the pending model after defaults and before sound init');
      const restarted = frame(c);
      assert.ok(restarted.nonzero);
      const freshModel = await fmOutputModelCore(replacement, replacementRegion);
      assert.equal(c._get_region_state().regionCode,
        replacementRegion===2?0xc0:0x80,'Clean Restart retains the selected Region with FM model');
      assert.deepEqual(restarted, frame(freshModel),
        'Clean Restart native output matches a fresh instance of the requested model');
      if (!modelOutputs.has(region)) modelOutputs.set(region, []);
      modelOutputs.get(region).push({model, warm, restarted});
      groups++;
    }
    for (const [region, outputs] of modelOutputs) {
      assert.notDeepEqual(outputs[0].warm.left, outputs[1].warm.left,
        `region ${region}: checkpoint fixture isolates different native PCM across MAME models`);
    }
  }

  for (const kind of ['pad3', 'pad6', 'sram', 'protected-sram']) {
    const p = await create(kind);
    for (let i = 0; i < 30; i++) frame(p);
    save(p); const image = pixels(p), savedRam = ram(p);
    const sequence = kind === 'pad6' ? [[8], [], [12], [], [13], [14]] : [[11], [], [11], [], [11], []];
    const neutralFirst = Array.from({length: 6}, () => frame(p));
    restore(p, image);
    const expected = sequence.map(b => frame(p, b));
    assert.ok(expected.some(x => x.ram !== savedRam), `${kind}: actual 68K accesses change WRAM`);
    restore(p, image); assert.equal(ram(p), savedRam);
    assert.deepEqual(Array.from({length: 6}, () => frame(p)), neutralFirst,
      `${kind}: restoration preserves ordinary SRAM write protection`);
    restore(p, image);
    assert.deepEqual(sequence.map(b => frame(p, b)), expected, `${kind}: pad protocol/SRAM replay`);
    restore(p, image);
    assert.deepEqual(sequence.map(b => frame(p, b)), expected, `${kind}: repeated restore`);
    groups++;
  }
  console.log(`${groups} Session Checkpoint actual-WASM groups passed`);
})().catch(e => { console.error(e); process.exitCode = 1; });
