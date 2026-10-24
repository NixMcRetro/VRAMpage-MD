'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const [runtimePath, normalPath] = process.argv.slice(2).map(value => path.resolve(value));
if (!runtimePath || !normalPath) throw new Error('Pass runtime and normal genplus.js paths.');

function locate(file) {
  return {locateFile: name => path.join(path.dirname(file), name)};
}

function fmToneCartridge() {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE FM DATA TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);

  const words = [];
  const byte = (address, value) => words.push(0x13fc, value, address >>> 16, address & 0xffff);
  const reg = (address, value) => {
    byte(0x00a04000, address);
    byte(0x00a04001, value);
  };
  reg(0x22, 0x00); // LFO off
  reg(0x27, 0x00); // normal channel mode
  for (const offset of [0, 4, 8, 12]) {
    reg(0x30 + offset, 0x01); // multiplier
    reg(0x50 + offset, 0x1f); // fast attack
    reg(0x60 + offset, 0x00);
    reg(0x70 + offset, 0x00);
    reg(0x80 + offset, 0x0f); // sustain/release
    reg(0x40 + offset, offset === 12 ? 0x00 : 0x7f);
  }
  reg(0xb0, 0x07); // algorithm 7, four carriers
  reg(0xb4, 0xc0); // both output channels
  reg(0xa0, 0x98);
  reg(0xa4, 0x22);
  reg(0x28, 0xf0); // key on channel 0
  words.push(0x60fe);
  words.forEach((value, index) => view.setUint16(0x200 + index * 2, value));
  [0x4e72, 0x2700, 0x60fe].forEach((value, index) => view.setUint16(0x300 + index * 2, value));
  return rom;
}

async function createCore(file, rom) {
  const core = await require(file)(locate(file));
  core._init();
  core.HEAPU8.set(rom, core._get_rom_buffer_ref(rom.length));
  core._start();
  new Float32Array(core.HEAPF32.buffer, core._get_input_buffer_ref(), 32).fill(0);
  return core;
}

function nextAudio(core) {
  core._wasm_input_update();
  core._tick();
  const count = core._sound();
  const left = core._get_web_audio_l_ref() >>> 2;
  const right = core._get_web_audio_r_ref() >>> 2;
  return {
    count,
    left: Float32Array.from(core.HEAPF32.subarray(left, left + count)),
    right: Float32Array.from(core.HEAPF32.subarray(right, right + count))
  };
}

function testUnsignedCounterFacadeBoundaries() {
  const module = {
    postRun: [], _set_fm_data_bridge_c: () => 0,
    _get_fm_data_bridge_version: () => 0, HEAPU8: new Uint8Array([0]),
    _get_fm_data_bridge_supported: () => 1, _get_fm_data_bridge_enabled: () => 1,
    _get_fm_data_bridge_a: () => 0, _get_fm_data_bridge_b: () => 5,
    _get_fm_data_bridge_input_writes: () => -1n,
    _get_fm_data_bridge_changed_writes: () => -(1n << 63n)
  };
  const shim = fs.readFileSync(path.join(__dirname, '../scripts/fm_data_fault_api.js'), 'utf8');
  vm.runInNewContext(shim, {Module: module});
  module.postRun[0]();
  const state = module._get_fm_data_bridge_state();
  assert.equal(state.inputWrites, '18446744073709551615');
  assert.equal(state.changedWrites, '9223372036854775808');
}

async function main() {
  testUnsignedCounterFacadeBoundaries();
  const rom = fmToneCartridge();
  const normal = await createCore(normalPath, rom);
  assert.equal(typeof normal._set_fm_data_bridge, 'undefined',
    'normal core does not expose the optional FM bridge');
  const baseline = nextAudio(normal);
  assert.ok(baseline.count > 0, 'synthetic FM program produces audio samples');
  assert.ok([...baseline.left, ...baseline.right].every(Number.isFinite));
  assert.ok([...baseline.left, ...baseline.right].some(value => Math.abs(value) > 0.0001),
    'synthetic FM program produces nonzero audio');

  const off = await createCore(runtimePath, rom);
  assert.equal(typeof off._set_fm_data_bridge, 'function');
  assert.equal(typeof off._set_fm_data_bridge_c, 'undefined');
  assert.equal(off._get_fm_data_bridge_state().supported, true);
  const offSamples = nextAudio(off);
  assert.equal(offSamples.count, baseline.count, 'runtime-off sample count matches normal');
  assert.deepEqual(offSamples.left, baseline.left, 'runtime-off left samples match normal');
  assert.deepEqual(offSamples.right, baseline.right, 'runtime-off right samples match normal');
  assert.equal(off._get_fm_data_bridge_state().inputWrites, '0');

  const active = await createCore(runtimePath, rom);
  assert.equal(active._set_fm_data_bridge(1, 0, 5), 0);
  const changed = nextAudio(active);
  const state = active._get_fm_data_bridge_state();
  assert.equal(changed.count, baseline.count, 'active bridge preserves sample count');
  assert.ok([...changed.left, ...changed.right].every(Number.isFinite));
  assert.ok(BigInt(state.inputWrites) > 0n, 'shared FM write sink counts 68K register bytes');
  assert.ok(BigInt(state.changedWrites) > 0n, 'bridge changes FM address or data bytes');
  assert.notDeepEqual(changed.left, baseline.left, 'active bridge changes generated FM audio');
  assert.equal(typeof active._get_fm_data_bridge_input_writes(), 'bigint',
    'compiled uint64 input counter uses exact Wasm BigInt ABI');
  assert.equal(typeof active._get_fm_data_bridge_changed_writes(), 'bigint',
    'compiled uint64 changed counter uses exact Wasm BigInt ABI');

  const beforeInvalid = active._get_fm_data_bridge_state();
  const coercion = {valueOf() { throw new Error('must not coerce'); }};
  const invalidValues = ['1', null, true, new Number(1), 1n, Symbol('bridge'), coercion,
    1.5, NaN, Infinity];
  for (let position = 0; position < 3; position++) {
    for (const invalid of invalidValues) {
      const args = [1, 0, 5];
      args[position] = invalid;
      assert.equal(active._set_fm_data_bridge(...args), 1,
        `rejects invalid JS value in argument ${position + 1}`);
    }
  }
  assert.equal(active._set_fm_data_bridge(1, 0), 1, 'rejects missing argument');
  assert.equal(active._set_fm_data_bridge(1, 0, 5, 6), 1, 'rejects extra argument');
  assert.deepEqual(active._get_fm_data_bridge_state(), beforeInvalid,
    'invalid calls preserve bridge configuration and counters');

  const reset = await createCore(runtimePath, rom);
  assert.equal(reset._set_fm_data_bridge(1, 0, 5), 0);
  const prior = nextAudio(reset);
  assert.ok(BigInt(reset._get_fm_data_bridge_state().inputWrites) > 0n);
  reset.HEAPU8.set(rom, reset._get_rom_buffer_ref(rom.length));
  reset._start();
  const resetState = reset._get_fm_data_bridge_state();
  assert.equal(resetState.configured, false, 'full sound reset clears bridge selection');
  assert.equal(resetState.inputWrites, '0', 'full sound reset clears write counter');
  assert.equal(resetState.changedWrites, '0', 'full sound reset clears changed counter');
  const restored = nextAudio(reset);
  assert.equal(restored.count, baseline.count);
  assert.deepEqual(restored.left, baseline.left,
    'new cartridge returns future FM output to normal');
  assert.notDeepEqual(prior.left, restored.left);
  console.log('Synthetic 68K FM writes matched normal output while off, changed output while active, and reset cleanly.');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
