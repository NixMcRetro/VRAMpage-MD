'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const runtimePath = path.resolve(process.argv[2]);
const normalPath = path.resolve(process.argv[3]);
const diagnosticPath = path.resolve(process.argv[4]);
if (!runtimePath || !normalPath || !diagnosticPath) {
  throw new Error('Pass runtime, normal, and diagnostic core paths.');
}

function locate(corePath) {
  return {locateFile: name => path.join(path.dirname(corePath), name)};
}

function syncInstantiate(corePath, options = {}) {
  const wasm = fs.readFileSync(path.join(path.dirname(corePath), 'genplus.wasm'));
  return require(corePath)({...options, ...locate(corePath), instantiateWasm(imports, receive) {
    const module = new WebAssembly.Module(wasm);
    const instance = new WebAssembly.Instance(module, imports);
    receive(instance, module);
    return instance.exports;
  }});
}

function makeMode5Rom(core) {
  const rom = new Uint8Array(0x80000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00); view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  view.setUint32(0x1a4, rom.length - 1); view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);
  const words = [
    0x33fc, 0x8144, 0x00c0, 0x0004,
    0x33fc, 0x5204, 0x00c0, 0x0004,
    0x33fc, 0x0000, 0x00c0, 0x0004,
    0x33fc, 0x5aa5, 0x00c0, 0x0000,
    0x60e6
  ];
  words.forEach((word, index) => view.setUint16(0x200 + index * 2, word));
  [0x4e72, 0x2700, 0x60fe].forEach((word, index) => view.setUint16(0x300 + index * 2, word));
  core.HEAPU8.set(rom, core._get_rom_buffer_ref(rom.length));
  core._start();
  core._tick();
}

(async () => {
  const normal = await require(normalPath)(locate(normalPath));
  assert.equal(typeof normal._set_vram_fault_model, 'undefined');
  assert.equal(typeof normal._run_vram_tx_test, 'undefined');
  assert.equal(typeof normal._set_vram_short, 'function', 'legacy controls remain available');

  const runtime = await require(runtimePath)(locate(runtimePath));
  assert.equal(typeof runtime._set_vram_fault_model, 'function');
  assert.equal(typeof runtime._set_vram_fault_model_c, 'undefined', 'raw C ABI is hidden behind the guarded public entry point');
  assert.equal(typeof runtime._run_vram_tx_test, 'undefined', 'runtime profile has no test bridges');
  runtime._init();
  assert.equal(runtime._set_logic_address_mask(128, 1), 0, 'activate a RAM fault for boundary checks');
  const ramBefore = [runtime._get_logic_address_mask(), runtime._get_logic_reads(), runtime._get_logic_writes()];
  assert.equal(runtime._set_vram_fault_model(0, 0, -1, -1), 0,
    'OFF is safe as the first API call after init');
  let state = runtime._get_vram_fault_model_state();
  assert.equal(state.modelId, 0);
  assert.equal(state.modelVersion, 'off');
  assert.equal(state.effective, false);
  assert.deepEqual(state.lastFrameCounts, {
    logicalByteReads: 0, logicalByteWrites: 0, redirectedByteReads: 0,
    redirectedByteWrites: 0, changedPhysicalByteWrites: 0
  });
  assert.deepEqual([runtime._get_logic_address_mask(), runtime._get_logic_reads(), runtime._get_logic_writes()], ramBefore,
    'valid VRAM API calls leave active RAM settings and counters untouched');

  const invalidCalls = [
    ['1', 0, -1, -1], [null, 0, -1, -1], [true, 0, -1, -1],
    [undefined, 0, -1, -1], [1.25, 0, -1, -1], [NaN, 0, -1, -1],
    [Infinity, 0, -1, -1], [-Infinity, 0, -1, -1], [1, 0, -1],
    [1, 0, -1, -1, 99], [1, 256, -1, -1], [2, 1, 0, 1]
  ];
  for (const args of invalidCalls) {
    const before = runtime._get_vram_fault_model_state();
    assert.equal(runtime._set_vram_fault_model(...args), 1, `invalid args rejected: ${String(args)}`);
    assert.deepEqual(runtime._get_vram_fault_model_state(), before, 'invalid call leaves model state atomic');
    assert.deepEqual([runtime._get_logic_address_mask(), runtime._get_logic_reads(), runtime._get_logic_writes()], ramBefore,
      'invalid VRAM API calls leave active RAM settings and counters untouched');
  }

  assert.equal(runtime._set_vram_fault_model(2, 8, -1, -1), 2,
    'transaction model rejects unsupported pre-Mode-5 state');
  assert.equal(runtime._get_vram_fault_model_state().modelId, 0,
    'unsupported call leaves current model selected');
  assert.deepEqual([runtime._get_logic_address_mask(), runtime._get_logic_reads(), runtime._get_logic_writes()], ramBefore,
    'unsupported VRAM API call leaves active RAM settings and counters untouched');
  assert.equal(runtime._set_vram_fault_model(1, 128, -1, -1), 0);
  state = runtime._get_vram_fault_model_state();
  assert.equal(state.modelId, 1);
  assert.equal(state.modelVersion, 'frame-projection-v1');
  assert.equal(state.mask, 128);
  assert.equal(runtime._set_vram_address_mask(0), 0);
  assert.equal(runtime._get_vram_fault_model_state().modelId, 1,
    'legacy setter continues selecting frame projection');

  const callbackOrder = [];
  const callbacks = await require(runtimePath)({
    ...locate(runtimePath),
    preRun: [() => callbackOrder.push('pre-1'), () => callbackOrder.push('pre-2')],
    postRun: [core => {
      callbackOrder.push('post-1');
      assert.equal(typeof core._set_vram_fault_model, 'function',
        'API is installed before user postRun callbacks execute');
    }, () => callbackOrder.push('post-2')]
  });
  assert.deepEqual(callbackOrder, ['pre-1', 'pre-2', 'post-1', 'post-2'],
    'array callbacks retain order');
  const functionCallbackOrder = [];
  const functionCallbacks = await require(runtimePath)({
    ...locate(runtimePath),
    preRun: () => functionCallbackOrder.push('pre'),
    postRun: core => {
      functionCallbackOrder.push('post');
      assert.equal(typeof core._get_vram_fault_model_state, 'function');
    }
  });
  assert.deepEqual(functionCallbackOrder, ['pre', 'post'], 'function callbacks are preserved');
  const sync = await syncInstantiate(runtimePath, {
    postRun: core => assert.equal(typeof core._set_vram_fault_model, 'function',
      'pre-js wrapper installs with synchronous instantiateWasm')
  });
  assert.equal(typeof sync._get_vram_fault_model_state, 'function');
  assert.equal(typeof callbacks._get_vram_fault_model_state, 'function');
  assert.equal(typeof functionCallbacks._get_vram_fault_model_state, 'function');

  const diagnostic = await require(diagnosticPath)(locate(diagnosticPath));
  assert.equal(typeof diagnostic._set_vram_fault_model, 'function');
  assert.equal(typeof diagnostic._run_vram_tx_test, 'function',
    'diagnostic-only bridge remains present in diagnostic profile');

  const core = await require(runtimePath)(locate(runtimePath));
  core._init();
  makeMode5Rom(core);
  core._wasm_input_update(); core._tick(); core._sound();
  assert.equal(core._set_vram_fault_model(2, 8, -1, -1), 0,
    'transaction model can be selected in supported Mode 5');
  state = core._get_vram_fault_model_state();
  assert.equal(state.modelId, 2);
  assert.equal(state.modelVersion, 'logical-byte-transaction-v1');
  assert.equal(state.effective, true);
  assert.equal(state.reason, 'none');
  core._tick();
  state = core._get_vram_fault_model_state();
  assert.ok(state.lastFrameCounts.logicalByteReads > 0,
    'a known Mode 5 frame reports renderer transaction reads');
  assert.ok(state.lastFrameCounts.logicalByteWrites > 0,
    'a known Mode 5 frame reports transaction writes');
  const firstFrameCounts = state.lastFrameCounts;
  core._tick();
  const secondFrameCounts = core._get_vram_fault_model_state().lastFrameCounts;
  assert.ok(secondFrameCounts.logicalByteWrites >= 3000 && secondFrameCounts.logicalByteWrites < 5000,
    'known repeated loop writes fit one frame and do not accumulate');
  assert.ok(secondFrameCounts.logicalByteWrites < firstFrameCounts.logicalByteWrites * 1.5,
    'second-frame writes replace, rather than add to, the first-frame count');
  for (const count of Object.values(state.lastFrameCounts)) {
    assert.equal(typeof count, 'number');
    assert.ok(Number.isSafeInteger(count) && count >= 0);
  }
  console.log('Public VRAM model API: profiles, validation, metadata, callbacks and runtime behavior passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
