'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');

if (!process.argv[2]) throw new Error('Pass the production runtime core path.');
const corePath = path.resolve(process.argv[2]);

function locate(file) {
  return {locateFile: name => path.join(path.dirname(file), name)};
}

function installMode5Rom(core) {
  const rom = new Uint8Array(0x80000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
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
}

(async () => {
  const core = await require(corePath)(locate(corePath));
  assert.equal(typeof core._set_vram_fault_model, 'function');
  assert.equal(typeof core._set_vram_fault_model_c, 'undefined');
  assert.equal(typeof core._get_vram_fault_model_state, 'function');
  assert.equal(typeof core._get_vram_supported_model_mask, 'function');
  assert.equal(typeof core._set_psg_data_bridge, 'function');
  assert.equal(typeof core._set_psg_data_bridge_c, 'undefined');
  assert.equal(typeof core._set_psg_data_mask, 'function');
  assert.equal(typeof core._set_psg_data_mask_c, 'undefined');
  assert.equal(typeof core._get_psg_data_bridge_state, 'function');
  assert.equal(typeof core._set_fm_data_bridge, 'function');
  assert.equal(typeof core._set_fm_data_bridge_c, 'undefined');
  assert.equal(typeof core._set_fm_data_mask, 'function');
  assert.equal(typeof core._set_fm_data_mask_c, 'undefined');
  assert.equal(typeof core._get_fm_data_bridge_state, 'function');
  assert.equal(typeof core._set_logic_data_mask, 'function');
  assert.equal(typeof core._set_logic_data_mask_c, 'undefined');
  assert.equal(typeof core._get_logic_data_mask, 'function');
  assert.equal(typeof core._get_logic_data_mask_c, 'undefined');
  assert.equal(core._get_logic_data_mask(), 0);
  assert.equal(core._set_logic_data_mask(0x10000, 1), 5);
  assert.equal(core._set_logic_data_mask(1.5, 1), 5);
  assert.equal(core._set_logic_data_mask(1, 4), 5);
  assert.equal(core._get_logic_data_mask(), 0, 'invalid mask requests do not mutate state');
  const diagnosticOnly = [
    '_run_vram_tx_test', '_get_vram_tx_counter', '_set_vram_transaction_diagnostic',
    '_get_vram_tx_test_physical_byte', '_get_vram_tx_test_sat_byte',
    '_get_vram_tx_test_cache_dirty', '_get_vram_tx_test_addr',
    '_get_vram_tx_test_dma_source', '_get_vram_tx_test_dma_region',
    '_get_vram_tx_test_dma_remaining', '_get_vram_tx_test_hscroll_base',
    '_get_vram_tx_test_render_path', '_get_vram_tx_test_byte',
    '_set_vram_tx_test_sat_physical_byte', '_clear_vram_tx_test_cache'
  ];
  for (const name of diagnosticOnly) {
    assert.equal(typeof core[name], 'undefined',
      `production runtime profile excludes ${name}`);
  }
  core._init();
  assert.equal(core._get_vram_supported_model_mask(), 3);
  installMode5Rom(core);
  core._wasm_input_update(); core._tick(); core._sound();
  const psgState = core._get_psg_data_bridge_state();
  assert.equal(psgState.modelVersion, 'psg-data-low-dominant-v2');
  assert.equal(psgState.dataMask, 0);
  assert.equal(psgState.supported, true);
  assert.equal(psgState.configured, false);
  assert.equal(core._set_psg_data_bridge(1, 0, 0), 1,
    'invalid same-input bridge is rejected');
  assert.deepEqual(core._get_psg_data_bridge_state(), psgState,
    'invalid bridge request is atomic');
  const fmState = core._get_fm_data_bridge_state();
  assert.equal(fmState.modelVersion, 'fm-register-data-low-dominant-v2');
  assert.equal(fmState.dataMask, 0);
  assert.equal(fmState.supported, true);
  assert.equal(fmState.configured, false);
  assert.equal(core._set_fm_data_bridge(1, 0, 0), 1,
    'invalid same-input FM bridge is rejected');
  assert.deepEqual(core._get_fm_data_bridge_state(), fmState,
    'invalid FM bridge request is atomic');
  assert.equal(core._get_vram_supported_model_mask(), 7);
  assert.equal(core._set_vram_fault_model(2, 8, -1, -1), 0);
  core._tick();
  let state = core._get_vram_fault_model_state();
  assert.equal(state.modelId, 2);
  assert.equal(state.modelVersion, 'logical-byte-transaction-v1');
  assert.equal(state.supportedModelsMask, 7);
  assert.ok(state.lastFrameCounts.logicalByteReads > 0);
  assert.ok(state.lastFrameCounts.logicalByteWrites > 0);
  const before = state;
  assert.equal(core._set_vram_fault_model('1', 0, -1, -1), 1);
  assert.deepEqual(core._get_vram_fault_model_state(), before,
    'production runtime API rejects coercible input without changing state');
  assert.equal(core._set_vram_address_mask(0), 0);
  state = core._get_vram_fault_model_state();
  assert.equal(state.modelId, 1, 'legacy setter continues selecting frame projection');
  console.log('Production runtime build factory passed API and bridge-surface checks.');
})().catch(error => { console.error(error); process.exitCode = 1; });
