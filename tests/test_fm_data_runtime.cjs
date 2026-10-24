'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const [runtimeArg, normalArg, variant] = process.argv.slice(2);
const runtimePath = runtimeArg && path.resolve(runtimeArg);
const normalPath = normalArg && path.resolve(normalArg);
if (!runtimePath || !normalPath) throw new Error('Pass runtime and normal genplus.js paths.');

function locate(file) {
  return {locateFile: name => path.join(path.dirname(file), name)};
}

function fmToneCartridge() {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x800);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE FM DATA TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);

  const words = [];
  const word = (address, value) => words.push(0x33fc, value, address >>> 16, address & 0xffff);
  const fastByte = (address, value) => words.push(0x13fc, value, address >>> 16, address & 0xffff);
  const byte = (address, value) => {
    words.push(0x13fc, value, address >>> 16, address & 0xffff);
    // Give YM3438 its busy interval while exercising the shared write boundary.
    for (let i = 0; i < 16; i++) words.push(0x4e71);
  };
  const reg = (address, value) => {
    byte(0x00a04000, address);
    byte(0x00a04001, value);
  };
  word(0x00a11100, 0x0100); // Assert BUSREQ before using the Z80/FM bus.
  word(0x00a11200, 0x0100); // Release the Z80 reset while BUSREQ is held.
  fastByte(0x00a04000, 0x22);
  fastByte(0x00a04001, 0x00);
  // Record immediate and delayed FM status reads in work RAM to check that
  // the input wrapper preserves the core's busy/status timing.
  words.push(0x1039, 0x00a0, 0x4000, 0x13c0, 0x00ff, 0x0100);
  for (let i = 0; i < 400; i++) words.push(0x4e71);
  words.push(0x1039, 0x00a0, 0x4000, 0x13c0, 0x00ff, 0x0101);
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
  words.push(0x303c, 0x7fff); // Let the tone run across frames before Z80 reset.
  const dbra = words.length;
  words.push(0x51c8, ((dbra * 2) - ((dbra + 1) * 2)) & 0xffff); // DBRA D0, loop
  word(0x00a11200, 0x0000); // Assert Z80 reset after FM writes have been counted.
  word(0x00a11200, 0x0100); // Release it; this is a chip-only partial FM reset.
  words.push(0x13fc, 0x005a, 0x00ff, 0x0102); // Mailbox marks execution after reset.
  words.push(0x60fe);
  words.forEach((value, index) => view.setUint16(0x800 + index * 2, value));
  [0x4e72, 0x2700, 0x60fe].forEach((value, index) => view.setUint16(0x300 + index * 2, value));
  return rom;
}

function validateZ80FmPsgBootstrapStores(words, z80Length) {
  for (let index = 0; index < words.length;) {
    const opcode = words[index];
    if (opcode === 0x33fc || opcode === 0x13fc) {
      assert.ok(index + 3 < words.length, 'complete Z80 bootstrap immediate store');
      const address = words[index + 2] * 0x10000 + words[index + 3];
      assert.ok(address === 0x00a11100 || address === 0x00a11200 ||
        (address >= 0x00a00000 && address < 0x00a00000 + z80Length),
      `68K bootstrap targets only bus-control registers or Z80 RAM, got $${address.toString(16)}`);
      index += 4;
    } else if (opcode === 0x60fe && index === words.length - 1) {
      index++;
    } else {
      assert.fail(`unexpected Z80/FM bootstrap opcode $${opcode.toString(16)} at word ${index}`);
    }
  }
}

function z80FmAndPsgCartridge() {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x800);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE Z80 FM PSG TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);
  rom[0x1f0] = 0x55;

  const z80 = [];
  const fm = (address, value) => {
    z80.push(0x3e, address, 0x32, 0x00, 0x40, 0x3e, value, 0x32, 0x01, 0x40);
  };
  const psg = value => z80.push(0x3e, value, 0x32, 0x11, 0x7f);
  fm(0x22, 0x00); // LFO off
  fm(0x27, 0x00); // normal channel mode
  for (const offset of [0, 4, 8, 12]) {
    fm(0x30 + offset, 0x01);
    fm(0x50 + offset, 0x1f);
    fm(0x60 + offset, 0x00);
    fm(0x70 + offset, 0x00);
    fm(0x80 + offset, 0x0f);
    fm(0x40 + offset, offset === 12 ? 0x00 : 0x7f);
  }
  fm(0xb0, 0x07); // algorithm 7, four carriers
  fm(0xb4, 0xc0); // both output channels
  fm(0xa0, 0x98);
  fm(0xa4, 0x22);
  fm(0x28, 0xf0); // key on channel 0
  psg(0x8a); // PSG channel 0 tone latch
  psg(0x10); // PSG tone period low bits
  psg(0x90); // PSG channel 0 volume
  z80.push(0x18, 0xfe);

  const words = [];
  const word = (address, value) => words.push(0x33fc, value, address >>> 16, address & 0xffff);
  const byte = (address, value) => words.push(0x13fc, value, address >>> 16, address & 0xffff);
  word(0x00a11100, 0x0100); // Assert BUSREQ before changing Z80 RAM.
  word(0x00a11200, 0x0100); // Release Z80 RESET while BUSREQ remains active.
  z80.forEach((value, index) => byte(0x00a00000 + index, value));
  word(0x00a11100, 0x0000); // Release BUSREQ so the Z80 owns the shared FM/PSG sink.
  words.push(0x60fe);

  validateZ80FmPsgBootstrapStores(words, z80.length);
  const forbiddenFmStore = words.slice();
  forbiddenFmStore[10] = 0x00a0;
  forbiddenFmStore[11] = 0x4000;
  assert.throws(() => validateZ80FmPsgBootstrapStores(forbiddenFmStore, z80.length),
    /bootstrap targets only bus-control registers or Z80 RAM/,
    'the proof rejects a 68K store directly to the FM port');
  words.forEach((value, index) => view.setUint16(0x800 + index * 2, value));
  [0x4e72, 0x2700, 0x60fe].forEach((value, index) => view.setUint16(0x300 + index * 2, value));
  return rom;
}

async function testZ80FmAndPsg(runtimePath, normalPath) {
  const rom = z80FmAndPsgCartridge();
  const normal = await createCore(normalPath, rom);
  const baseline = nextAudio(normal);
  assert.ok(baseline.count > 0);
  assert.ok([...baseline.left, ...baseline.right].every(Number.isFinite));
  assert.ok([...baseline.left, ...baseline.right].some(value => Math.abs(value) > 0.0001),
    'Z80 FM and PSG program produces nonzero audio');

  const runtimeOff = await createCore(runtimePath, rom);
  const offSamples = nextAudio(runtimeOff);
  assert.equal(offSamples.count, baseline.count);
  assert.deepEqual(offSamples.left, baseline.left, 'runtime-off Z80 FM/PSG equals normal');
  assert.deepEqual(offSamples.right, baseline.right, 'runtime-off Z80 FM/PSG equals normal');
  assert.equal(runtimeOff._get_fm_data_bridge_state().inputWrites, '0');
  assert.equal(runtimeOff._get_psg_data_bridge_state().inputWrites, '0');

  const fmOnly = await createCore(runtimePath, rom);
  assert.equal(fmOnly._set_fm_data_bridge(1, 0, 5), 0);
  const fmSamples = nextAudio(fmOnly);
  const fmState = fmOnly._get_fm_data_bridge_state();
  assert.ok(BigInt(fmState.inputWrites) > 0n, 'Z80 FM port writes reach the FM sink');
  assert.equal(fmState.inputWrites, '62', 'Z80 sends 62 FM address/data port bytes');
  assert.equal(fmState.changedWrites, '33', 'the selected FM pair changes 33 bytes');
  assert.equal(fmOnly._get_psg_data_bridge_state().inputWrites, '0',
    'FM-only selection leaves PSG input counters untouched');
  assert.notDeepEqual(fmSamples.left, baseline.left, 'FM-only bridge transforms the generated tone');

  const psgOnly = await createCore(runtimePath, rom);
  assert.equal(psgOnly._set_psg_data_bridge(1, 0, 7), 0);
  const psgSamples = nextAudio(psgOnly);
  const psgState = psgOnly._get_psg_data_bridge_state();
  assert.equal(psgOnly._get_fm_data_bridge_state().inputWrites, '0',
    'PSG-only selection leaves FM input counters untouched');
  assert.equal(psgState.inputWrites, '3', 'Z80 emits exactly three PSG data writes');
  assert.equal(psgState.changedWrites, '2', 'PSG pair transforms two of three Z80 bytes');
  assert.notDeepEqual(psgSamples.left, baseline.left, 'PSG-only bridge transforms the generated tone');

  const both = await createCore(runtimePath, rom);
  assert.equal(both._set_fm_data_bridge(1, 0, 5), 0);
  assert.equal(both._set_psg_data_bridge(1, 0, 7), 0);
  const bothSamples = nextAudio(both);
  const bothFm = both._get_fm_data_bridge_state();
  const bothPsg = both._get_psg_data_bridge_state();
  assert.equal(bothFm.configured, true);
  assert.equal(bothPsg.configured, true);
  assert.equal(bothFm.inputWrites, fmState.inputWrites,
    'activating PSG leaves Z80 FM traffic count unchanged');
  assert.equal(bothFm.changedWrites, fmState.changedWrites);
  assert.equal(bothPsg.inputWrites, psgState.inputWrites,
    'activating FM leaves Z80 PSG traffic count unchanged');
  assert.equal(bothPsg.changedWrites, psgState.changedWrites);
  assert.notDeepEqual(bothSamples.left, baseline.left, 'combined bridges transform the generated tone');

  const bothFmBeforeRemoval = both._get_fm_data_bridge_state();
  const bothPsgBeforeRemoval = both._get_psg_data_bridge_state();
  assert.equal(both._set_fm_data_bridge(0, -1, -1), 0);
  assert.deepEqual(both._get_psg_data_bridge_state(), bothPsgBeforeRemoval,
    'removing FM input bridge preserves PSG configuration and counters');
  const fmAfterRemoval = both._get_fm_data_bridge_state();
  assert.equal(both._set_psg_data_bridge(0, -1, -1), 0);
  assert.equal(bothFmBeforeRemoval.configured, true);
  assert.equal(bothPsgBeforeRemoval.configured, true);
  assert.equal(both._get_fm_data_bridge_state().configured, false);
  assert.equal(both._get_psg_data_bridge_state().configured, false);
  assert.deepEqual(both._get_fm_data_bridge_state(), fmAfterRemoval,
    'removing PSG input bridge preserves FM configuration and counters');

  const clean = await createCore(runtimePath, rom);
  assert.equal(clean._set_fm_data_bridge(1, 0, 5), 0);
  assert.equal(clean._set_psg_data_bridge(1, 0, 7), 0);
  nextAudio(clean);
  clean.HEAPU8.set(rom, clean._get_rom_buffer_ref(rom.length));
  clean._start();
  assert.equal(clean._get_fm_data_bridge_state().configured, false);
  assert.equal(clean._get_fm_data_bridge_state().inputWrites, '0');
  assert.equal(clean._get_psg_data_bridge_state().configured, false);
  assert.equal(clean._get_psg_data_bridge_state().inputWrites, '0');
  console.log('Z80 shared FM/PSG writes match normal while off and transform independently or together.');
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

function fmStatusProbe(core) {
  const base = core._get_logic_ram_ref() >>> 0;
  // The 68K work RAM byte lanes are word-swapped in the exported heap view.
  return [core.HEAPU8[base + 0x101], core.HEAPU8[base + 0x100]];
}

function fmZ80ResetMarker(core) {
  const base = core._get_logic_ram_ref() >>> 0;
  // 68K byte stores use ADDR ^ 1 in the raw heap view.
  return core.HEAPU8[base + (0x0102 ^ 1)];
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
  let baselineCore;
  if (variant === 'ym3438') {
    baselineCore = await createCore(normalPath, rom);
    assert.equal(typeof baselineCore._set_fm_data_bridge, 'undefined',
      'normal YM3438 core does not expose the optional FM bridge');
  } else {
    baselineCore = await createCore(normalPath, rom);
    assert.equal(typeof baselineCore._set_fm_data_bridge, 'undefined',
      'normal core does not expose the optional FM bridge');
  }
  const baseline = nextAudio(baselineCore);
  const baselineStatus = fmStatusProbe(baselineCore);
  assert.equal(baselineStatus[0] & 0x80, 0x80,
    'immediate FM status read observes the busy bit');
  assert.equal(baselineStatus[1] & 0x80, 0,
    'delayed FM status read observes busy clear');
  assert.ok(baseline.count > 0, 'synthetic FM program produces audio samples');
  assert.ok([...baseline.left, ...baseline.right].every(Number.isFinite));
  assert.ok([...baseline.left, ...baseline.right].some(value => Math.abs(value) > 0.0001),
    'synthetic FM program produces nonzero audio');

  const off = await createCore(runtimePath, rom);
  assert.equal(typeof off._set_fm_data_bridge, 'function');
  assert.equal(typeof off._set_fm_data_bridge_c, 'undefined');
  assert.equal(off._get_fm_data_bridge_state().supported, true);
  const offSamples = nextAudio(off);
  assert.deepEqual(fmStatusProbe(off), baselineStatus,
    'runtime-off immediate and delayed FM status reads match normal');
  assert.equal(offSamples.count, baseline.count, 'runtime-off sample count matches baseline');
  assert.deepEqual(offSamples.left, baseline.left, 'runtime-off left samples match baseline');
  assert.deepEqual(offSamples.right, baseline.right, 'runtime-off right samples match baseline');
  assert.equal(off._get_fm_data_bridge_state().inputWrites, '0');

  const active = await createCore(runtimePath, rom);
  assert.equal(active._set_fm_data_bridge(1, 0, 5), 0);
  assert.equal(active._set_psg_data_bridge(1, 1, 7), 0,
    'PSG and FM bridges can be configured independently');
  assert.equal(fmZ80ResetMarker(active), 0,
    'post-reset mailbox is empty before the delayed reset instruction executes');
  const psgBeforeFmWrites = active._get_psg_data_bridge_state();
  const changed = nextAudio(active);
  assert.equal(fmZ80ResetMarker(active), 0,
    'the delayed Z80-only reset and following mailbox store have not executed yet');
  assert.deepEqual(fmStatusProbe(active), baselineStatus,
    'FM bridge leaves the immediate and delayed busy/status reads unchanged');
  const state = active._get_fm_data_bridge_state();
  assert.deepEqual(active._get_psg_data_bridge_state(), psgBeforeFmWrites,
    'FM activity does not mutate PSG bridge configuration or counters');
  assert.equal(changed.count, baseline.count, 'active bridge preserves sample count');
  assert.ok([...changed.left, ...changed.right].every(Number.isFinite));
  assert.ok(BigInt(state.inputWrites) > 0n,
    'FM writes after the ROM bootstrap Z80-only reset reach the shared sink');
  assert.ok(BigInt(state.changedWrites) > 0n, 'bridge changes FM address or data bytes');
  assert.notDeepEqual(changed.left, baseline.left, 'active bridge changes generated FM audio');
  assert.equal(typeof active._get_fm_data_bridge_input_writes(), 'bigint',
    'compiled uint64 input counter uses exact Wasm BigInt ABI');
  assert.equal(typeof active._get_fm_data_bridge_changed_writes(), 'bigint',
    'compiled uint64 changed counter uses exact Wasm BigInt ABI');
  const beforeZ80Reset = active._get_fm_data_bridge_state();
  for (let frame = 0; frame < 5; frame++) nextAudio(active);
  const afterZ80Reset = active._get_fm_data_bridge_state();
  assert.equal(fmZ80ResetMarker(active), 0x5a,
    'post-reset mailbox confirms the Z80-only reset executed before counter checks');
  assert.equal(afterZ80Reset.configured, true,
    'Z80-only reset leaves the FM bridge connected');
  assert.equal(afterZ80Reset.inputWrites, beforeZ80Reset.inputWrites,
    'Z80-only reset preserves aggregate FM write counters');
  assert.equal(afterZ80Reset.changedWrites, beforeZ80Reset.changedWrites,
    'Z80-only reset preserves changed-byte counters');

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
  assert.equal(active._set_fm_data_bridge(0, -1, -1), 0);
  assert.deepEqual(active._get_psg_data_bridge_state(), psgBeforeFmWrites,
    'removing FM bridge does not mutate PSG bridge state');

  const reset = await createCore(runtimePath, rom);
  const resetControl = await createCore(runtimePath, rom);
  assert.equal(reset._set_fm_data_bridge(1, 0, 5), 0);
  assert.equal(reset._set_psg_data_bridge(1, 1, 7), 0);
  nextAudio(resetControl);
  const prior = nextAudio(reset);
  assert.ok(BigInt(reset._get_fm_data_bridge_state().inputWrites) > 0n);
  reset.HEAPU8.set(rom, reset._get_rom_buffer_ref(rom.length));
  reset._start();
  const resetState = reset._get_fm_data_bridge_state();
  assert.equal(resetState.configured, false, 'full sound reset clears bridge selection');
  assert.equal(resetState.inputWrites, '0', 'full sound reset clears write counter');
  assert.equal(resetState.changedWrites, '0', 'full sound reset clears changed counter');
  assert.equal(reset._get_psg_data_bridge_state().configured, false,
    'full sound reset also clears the independent PSG bridge');
  const restored = nextAudio(reset);
  resetControl.HEAPU8.set(rom, resetControl._get_rom_buffer_ref(rom.length));
  resetControl._start();
  const controlAfterReset = nextAudio(resetControl);
  assert.equal(restored.count, baseline.count);
  assert.deepEqual(restored.left, controlAfterReset.left,
    'new cartridge returns future FM output to an unbridged full-reset control');
  assert.notDeepEqual(prior.left, restored.left);
  await testZ80FmAndPsg(runtimePath, normalPath);
  console.log(`Synthetic 68K FM writes matched ${variant === 'ym3438' ? 'normal YM3438' : 'normal MAME'} output while off, changed output while active, and reset cleanly.`);
}

main().catch(error => { console.error(error); process.exitCode = 1; });
