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

function toneCartridge() {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE PSG INPUT TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);
  rom[0x1f0] = 0x55;
  const words = [];
  const word = (address, value) => words.push(0x33fc, value, address >>> 16, address & 0xffff);
  const byte = (address, value) => words.push(0x13fc, value, address >>> 16, address & 0xffff);
  word(0xc00004, 0x8004);
  word(0xc00004, 0x8144);
  word(0xc00004, 0x8c81);
  word(0xc00004, 0x8f02);
  byte(0xc00011, 0x8a);
  byte(0xc00011, 0x10);
  byte(0xc00011, 0x90);
  words.push(0x5279, 0x00ff, 0x1000, 0x60f8);
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
    postRun: [],
    _set_psg_data_bridge_c: () => 0,
    _get_psg_data_bridge_version: () => 0,
    HEAPU8: new Uint8Array([0]),
    _get_psg_data_bridge_supported: () => 1,
    _get_psg_data_bridge_enabled: () => 1,
    _get_psg_data_bridge_a: () => 0,
    _get_psg_data_bridge_b: () => 7,
    _get_psg_data_mask: () => 0,
    _get_psg_data_bridge_input_writes: () => -1n,
    _get_psg_data_bridge_changed_writes: () => -(1n << 63n)
  };
  const shim = fs.readFileSync(path.join(__dirname, '../scripts/psg_data_fault_api.js'), 'utf8');
  vm.runInNewContext(shim, {Module: module});
  module.postRun[0]();
  const state = module._get_psg_data_bridge_state();
  assert.equal(state.inputWrites, '18446744073709551615',
    'uint64 maximum remains unsigned in the public decimal-string API');
  assert.equal(state.changedWrites, '9223372036854775808',
    'uint64 high-bit boundary remains unsigned in the public decimal-string API');
}

async function main() {
  testUnsignedCounterFacadeBoundaries();
  const rom = toneCartridge();
  const normal = await createCore(normalPath, rom);
  assert.equal(typeof normal._set_psg_data_bridge, 'undefined',
    'normal core has no PSG input API');
  const baseline = nextAudio(normal);
  assert.ok(baseline.count > 0, 'synthetic 68K program produces audio samples');
  assert.ok([...baseline.left, ...baseline.right].every(Number.isFinite));
  assert.ok([...baseline.left, ...baseline.right].some(value => Math.abs(value) > 0.0001),
    'synthetic 68K program produces nonzero PSG audio');

  const off = await createCore(runtimePath, rom);
  assert.equal(typeof off._set_psg_data_bridge, 'function');
  assert.equal(typeof off._set_psg_data_bridge_c, 'undefined');
  let offState = off._get_psg_data_bridge_state();
  assert.equal(offState.modelVersion, 'psg-data-low-dominant-v2');
  assert.equal(offState.dataMask, 0);
  assert.equal(offState.supported, true);
  assert.equal(offState.configured, false);
  const offSamples = nextAudio(off);
  assert.equal(offSamples.count, baseline.count, 'runtime-off sample count equals normal');
  assert.deepEqual(offSamples.left, baseline.left, 'runtime-off left samples equal normal');
  assert.deepEqual(offSamples.right, baseline.right, 'runtime-off right samples equal normal');
  const active = await createCore(runtimePath, rom);
  assert.equal(typeof active._set_psg_data_bridge_c, 'undefined');
  assert.equal(typeof active._set_psg_data_mask_c, 'undefined');
  const invalidMasks = ['128', null, true, new Number(128), 1n, Symbol('mask'),
    {valueOf() { throw new Error('mask setter must not coerce'); }}, 1.5, NaN, Infinity];
  const beforeInvalidMask = active._get_psg_data_bridge_state();
  for (const invalid of invalidMasks) {
    assert.equal(active._set_psg_data_mask(invalid), 1, 'mask setter rejects non-integer-number values');
  }
  assert.equal(active._set_psg_data_mask(), 1, 'mask setter rejects missing args');
  assert.equal(active._set_psg_data_mask(1, 2), 1, 'mask setter rejects extra args');
  assert.deepEqual(active._get_psg_data_bridge_state(), beforeInvalidMask,
    'rejected mask calls do not change configuration or counters');
  assert.equal(active._set_psg_data_bridge(1, 0, 7), 0);
  const activeSamples = nextAudio(active);
  const activeState = active._get_psg_data_bridge_state();
  assert.equal(activeSamples.count, baseline.count, 'active bridge keeps sample count');
  assert.ok([...activeSamples.left, ...activeSamples.right].every(Number.isFinite));
  assert.ok(BigInt(activeState.inputWrites) > 0n, 'real 68K PSG route reaches sink');
  assert.ok(BigInt(activeState.changedWrites) > 0n, 'bridge changes synthetic PSG bytes');
  assert.notDeepEqual(activeSamples.left, baseline.left,
    'active data bridge changes generated PSG audio');

  const inputCountExport = active._get_psg_data_bridge_input_writes;
  const changedCountExport = active._get_psg_data_bridge_changed_writes;
  assert.equal(typeof inputCountExport.call(active), 'bigint',
    'compiled uint64 input counter uses the exact Wasm BigInt ABI');
  assert.equal(typeof changedCountExport.call(active), 'bigint',
    'compiled uint64 changed counter uses the exact Wasm BigInt ABI');
  assert.equal(String(inputCountExport.call(active)), activeState.inputWrites);
  assert.equal(String(changedCountExport.call(active)), activeState.changedWrites);
  active._get_psg_data_bridge_input_writes = () => 9007199254740993n;
  active._get_psg_data_bridge_changed_writes = () => 9007199254740995n;
  assert.equal(active._get_psg_data_bridge_state().inputWrites, '9007199254740993',
    'facade preserves uint64 counters beyond JavaScript safe integers');
  assert.equal(active._get_psg_data_bridge_state().changedWrites, '9007199254740995');
  active._get_psg_data_bridge_input_writes = inputCountExport;
  active._get_psg_data_bridge_changed_writes = changedCountExport;

  const beforeInvalid = active._get_psg_data_bridge_state();
  const coercion = {valueOf() { throw new Error('must not coerce'); }};
  const invalidValues = ['1', null, true, new Number(1), 1n, Symbol('bridge'), coercion, 1.5, NaN, Infinity];
  for (let position = 0; position < 3; position++) {
    for (const invalid of invalidValues) {
      const args = [1, 0, 1];
      args[position] = invalid;
      assert.equal(active._set_psg_data_bridge(...args), 1,
        `rejects invalid JS value in argument ${position + 1}`);
    }
  }
  assert.equal(active._set_psg_data_bridge(1, 0), 1, 'rejects missing argument');
  assert.equal(active._set_psg_data_bridge(1, 0, 1, 2), 1, 'rejects extra argument');
  assert.deepEqual(active._get_psg_data_bridge_state(), beforeInvalid,
    'rejected calls preserve active model, pair, and counters');

  const masked = await createCore(runtimePath, rom);
  assert.equal(masked._set_psg_data_mask(0x80), 0);
  let maskedState = masked._get_psg_data_bridge_state();
  assert.equal(maskedState.dataMask, 0x80);
  assert.equal(maskedState.bridgeA, -1);
  assert.equal(maskedState.bridgeB, -1);
  assert.equal(maskedState.configured, true);
  const maskedSamples = nextAudio(masked);
  maskedState = masked._get_psg_data_bridge_state();
  assert.equal(maskedSamples.count, baseline.count);
  assert.ok([...maskedSamples.left, ...maskedSamples.right].every(Number.isFinite));
  assert.ok(BigInt(maskedState.inputWrites) > 0n);
  assert.ok(BigInt(maskedState.changedWrites) > 0n);
  assert.notDeepEqual(maskedSamples.left, baseline.left,
    'stuck-low data mask changes the real synthetic PSG stream');
  assert.equal(masked._set_psg_data_bridge(1, 0, 7), 0,
    'pair setter replaces mask configuration');
  assert.equal(masked._get_psg_data_bridge_state().dataMask, 0);
  assert.equal(masked._set_psg_data_mask(0), 0, 'zero mask clears all PSG input faults');
  const clearedMask = masked._get_psg_data_bridge_state();
  assert.equal(clearedMask.configured, false);
  assert.equal(clearedMask.dataMask, 0);
  assert.equal(clearedMask.inputWrites, '0');
  assert.equal(clearedMask.changedWrites, '0');

  const reset = await createCore(runtimePath, rom);
  assert.equal(reset._set_psg_data_bridge(1, 0, 7), 0);
  const changed = nextAudio(reset);
  const beforeReset = reset._get_psg_data_bridge_state();
  assert.ok(BigInt(beforeReset.inputWrites) > 0n);
  reset.HEAPU8.set(rom, reset._get_rom_buffer_ref(rom.length));
  reset._start();
  const resetState = reset._get_psg_data_bridge_state();
  assert.equal(resetState.configured, false, 'PSG reset clears bridge configuration');
  assert.equal(resetState.inputWrites, '0', 'PSG reset clears input counter');
  assert.equal(resetState.changedWrites, '0', 'PSG reset clears changed counter');
  const afterReset = nextAudio(reset);
  assert.equal(afterReset.count, baseline.count);
  assert.deepEqual(afterReset.left, baseline.left,
    'reset restores normal future PSG writes without repairing prior output');
  assert.notDeepEqual(changed.left, afterReset.left,
    'active bridge altered the actual synthetic tone');
  console.log('Runtime PSG pair/mask faults matched normal output while off, altered actual 68K PSG tone while active, and reset cleanly.');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
