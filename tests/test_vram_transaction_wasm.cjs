/* Synthetic 68000 program exercises opt-in Mode 5 VRAM bus transactions. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const coreFile = path.resolve(process.argv[2]);
if (!process.argv[2]) throw new Error('Pass diagnostic genplus.js.');
const factory = require(coreFile);
const normalCoreFile = process.argv[3] && path.resolve(process.argv[3]);
const FRAME_BYTES = 640 * 480 * 4;
const AUDIO_CAPACITY = 2048;

function captureObservableState(core, audioSamples) {
  const frame = core._get_frame_buffer_ref();
  const left = core._get_web_audio_l_ref() >>> 2;
  const right = core._get_web_audio_r_ref() >>> 2;
  const ram = core._get_logic_ram_ref();
  return {
    frame: Buffer.from(core.HEAPU8.subarray(frame, frame + FRAME_BYTES)),
    audioLeft: Float32Array.from(core.HEAPF32.subarray(left, left + audioSamples)),
    audioRight: Float32Array.from(core.HEAPF32.subarray(right, right + audioSamples)),
    ram: Buffer.from(core.HEAPU8.subarray(ram, ram + 0x10000)),
    logicFrame: core._get_logic_frame(),
    cpuFlags: core._get_logic_cpu_flags()
  };
}

function assertObservableEquivalent(actual, expected, label) {
  assert.equal(actual.audioSamples, expected.audioSamples, `${label}: audio sample count`);
  assert.deepEqual(actual.frame, expected.frame, `${label}: complete framebuffer`);
  assert.deepEqual(actual.audioLeft, expected.audioLeft, `${label}: left audio samples`);
  assert.deepEqual(actual.audioRight, expected.audioRight, `${label}: right audio samples`);
  assert.deepEqual(actual.ram, expected.ram, `${label}: work RAM bytes`);
  assert.equal(actual.logicFrame, expected.logicFrame, `${label}: emulated frame count`);
  assert.equal(actual.cpuFlags, expected.cpuFlags, `${label}: exported CPU STOP/HALT flags`);
}

function wordWrite(address, value) {
  return [0x33fc, value, address >>> 16, address & 0xffff];
}
function cartridge() {
  const rom = new Uint8Array(0x80000), view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00); view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE VRAM TX TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1); view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff); rom[0x1f0] = 0x55;
  view.setUint16(0x3fffe, 0x11a1);
  view.setUint16(0x20000, 0x22b2);
  view.setUint16(0x40000, 0x33c3);
  const words = [
    ...wordWrite(0xc00004, 0x8104), // Enable Mode 5.
    ...wordWrite(0xc00004, 0x5204), // VRAM write command, logical 0x1204.
    ...wordWrite(0xc00004, 0x0000),
    ...wordWrite(0xc00000, 0x5aa5),
    0x60e6 // Repeat from the VDP address command to keep the same destination.
  ];
  words.forEach((word, index) => view.setUint16(0x200 + 2 * index, word));
  [0x4e72, 0x2700, 0x60fe].forEach((word, index) => view.setUint16(0x300 + 2 * index, word));
  return rom;
}

async function run() {
  if (!normalCoreFile) throw new Error('Pass the normal, non-diagnostic genplus.js.');
  const normalFactory = require(normalCoreFile);
  const normalCore = await normalFactory({locateFile: name => path.join(path.dirname(normalCoreFile), name)});
  assert.equal(typeof normalCore._set_vram_transaction_diagnostic, 'undefined',
    'normal core exports no diagnostic transaction selector');
  assert.equal(typeof normalCore._run_vram_tx_test, 'undefined',
    'normal core exports no diagnostic handler bridge');
  const core = await factory({locateFile: name => path.join(path.dirname(coreFile), name)});
  core._init();
  assert.equal(typeof core._set_vram_transaction_diagnostic, 'function');
  const rom = cartridge();
  core.HEAPU8.set(rom, core._get_rom_buffer_ref(rom.length));
  core._start();
  normalCore._init();
  normalCore.HEAPU8.set(rom, normalCore._get_rom_buffer_ref(rom.length));
  normalCore._start();
  new Float32Array(core.HEAPF32.buffer, core._get_input_buffer_ref(), 32).fill(0);
  new Float32Array(normalCore.HEAPF32.buffer, normalCore._get_input_buffer_ref(), 32).fill(0);
  core._wasm_input_update(); core._tick();
  normalCore._wasm_input_update(); normalCore._tick();
  const diagnosticOffSamples = core._sound();
  const normalOffSamples = normalCore._sound();
  assertObservableEquivalent(
    {...captureObservableState(core, diagnosticOffSamples), audioSamples: diagnosticOffSamples},
    {...captureObservableState(normalCore, normalOffSamples), audioSamples: normalOffSamples},
    'diagnostic-off first fixed tick matches the normal core');

  const identityCore = await factory({locateFile: name => path.join(path.dirname(coreFile), name)});
  identityCore._init();
  identityCore.HEAPU8.set(rom, identityCore._get_rom_buffer_ref(rom.length));
  identityCore._start();
  new Float32Array(identityCore.HEAPF32.buffer, identityCore._get_input_buffer_ref(), 32).fill(0);
  identityCore._wasm_input_update(); identityCore._tick(); identityCore._sound();
  assert.equal(identityCore._set_vram_transaction_diagnostic(2, 0, -1, -1), 0,
    'identity transaction selection is supported after the synthetic ROM enables Mode 5');
  identityCore._wasm_input_update(); identityCore._tick();
  normalCore._wasm_input_update(); normalCore._tick();
  const identitySamples = identityCore._sound();
  const normalIdentitySamples = normalCore._sound();
  assertObservableEquivalent(
    {...captureObservableState(identityCore, identitySamples), audioSamples: identitySamples},
    {...captureObservableState(normalCore, normalIdentitySamples), audioSamples: normalIdentitySamples},
    'selected identity transaction second fixed tick matches the normal core');
  assert.equal(identityCore._get_vram_tx_counter(1), 0n,
    'identity transaction performs no mapped transaction writes');

  // Unsupported requests preserve legacy configuration and return a status.
  assert.equal(core._set_vram_transaction_diagnostic(2, 1, -1, -1), 0);
  core._wasm_input_update(); core._tick();
  assert.ok(core._get_vram_tx_counter(1) > 0, 'CPU VDP word stores traverse the byte adapter');
  assert.ok(core._get_vram_tx_counter(3) > 0, 'AD0 redirects the logical byte lanes');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1200), 0xa5,
    'both AD0-mapped word lanes alias physical 0x1200 and the low byte is the final writer');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1201), 0x00,
    'aliased lane must not be spuriously written to the adjacent byte');
  assert.equal(core._run_vram_tx_test(0, 0x1205, 0x1234, 0, 1), 0,
    'odd-address 68K word write');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1200), 0x12,
    'odd-address word swap is applied before the aliased low lane wins');
  assert.equal(core._get_vram_tx_test_addr(), 0x1206,
    'one logical address increment follows the word, not each byte lane');

  const counters = Array.from({length: 5}, (_, i) => core._get_vram_tx_counter(i));
  assert.equal(core._set_vram_transaction_diagnostic(2, 1, 0, 1), 1,
    'invalid mutually exclusive settings are rejected without changing the active transaction');
  assert.deepEqual(Array.from({length: 5}, (_, i) => core._get_vram_tx_counter(i)), counters);

  // Exercise the actual 68K word, undocumented byte, and Z80 byte handlers.
  assert.equal(core._run_vram_tx_test(0, 0x2004, 0x1234, 0, 1), 0);
  assert.equal(core._get_vram_tx_test_physical_byte(0x2000), 0x34,
    'both AD0 word lanes collide and later low lane wins');
  assert.equal(core._run_vram_tx_test(3, 0x2004, 0, 0, 1), 0x3434,
    '68K aligned word read resolves both byte lanes');
  assert.equal(core._run_vram_tx_test(4, 0x2004, 0, 0, 1) & 0xff, 0x34,
    '68K code 0x0c byte read maps addr XOR 1');
  assert.equal(core._run_vram_tx_test(1, 0x2104, 0x76, 0, 1), 0,
    'Z80 Mode 5 write reaches mapped byte lane');
  assert.equal(core._run_vram_tx_test(2, 0x2104, 0, 0, 1), 0x76,
    'Z80 Mode 5 read reaches the same mapped byte');

  // Changed transaction writes notify only dependencies of the mapped
  // physical byte. The bridge exposes Genesis Plus GX pattern-cache rows.
  core._clear_vram_tx_test_cache();
  assert.equal(core._run_vram_tx_test(0, 0x1204, 0x1357, 0, 1), 0);
  assert.equal(core._get_vram_tx_test_physical_byte(0x1200), 0x57);
  assert.ok(Array.from({length: 0x800}, (_, i) =>
    core._get_vram_tx_test_cache_dirty(i)).some(bits => bits !== 0),
    'changed mapped write marks reverse-dependent pattern-cache rows');

  // All three 68K DMA source classes retain their source addressing while the
  // common vdp_bus_w destination applies the transaction map.
  const writesBeforeBadDma = core._get_vram_tx_counter(1);
  const addrBeforeBadDma = core._get_vram_tx_test_addr();
  const sourceBeforeBadDma = core._get_vram_tx_test_dma_source();
  assert.equal(core._run_vram_tx_test(5, 0x3004, 0, 0, 0), -3,
    'test bridge rejects zero-length do-while DMA before touching core state');
  assert.equal(core._run_vram_tx_test(5, 0x3004, 0, 0, 0x10001), -3,
    'test bridge rejects oversized do-while DMA before touching core state');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeBadDma);
  assert.equal(core._get_vram_tx_test_addr(), addrBeforeBadDma);
  assert.equal(core._get_vram_tx_test_dma_source(), sourceBeforeBadDma);
  let writesBeforeDma = core._get_vram_tx_counter(1);
  assert.equal(core._run_vram_tx_test(5, 0x3004, 0, 0x000000, 1), 0,
    'external-bus DMA');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 2n,
    'external-bus word DMA resolves both destination byte lanes');
  assert.equal(core._get_vram_tx_test_physical_byte(0x3000), 0xff,
    'external ROM source word reaches the aliased destination');
  const ram = core._get_logic_ram_ref();
  const ramView = new DataView(core.HEAPU8.buffer);
  ramView.setUint16(ram + 0x10, 0x3456, true);
  const sourceBefore = ramView.getUint16(ram + 0x10, true);
  writesBeforeDma = core._get_vram_tx_counter(1);
  assert.equal(core._run_vram_tx_test(6, 0x3204, 0, 0xff0010, 1), 0,
    'work-RAM DMA');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 2n,
    'work-RAM word DMA resolves both destination byte lanes');
  assert.equal(core._get_vram_tx_test_physical_byte(0x3200), 0x56);
  assert.equal(ramView.getUint16(ram + 0x10, true), sourceBefore,
    'VRAM destination mapping does not alter the RAM DMA source');
  writesBeforeDma = core._get_vram_tx_counter(1);
  assert.equal(core._run_vram_tx_test(7, 0x3304, 0, 0xa10000, 1), 0,
    'I/O-window DMA');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 2n,
    'I/O-window word DMA resolves both destination byte lanes');
  const ioOracle = core._run_vram_tx_test(17, 0, 0, 0xa10000, 0) & 0xff;
  assert.equal(core._get_vram_tx_test_physical_byte(0x3300), ioOracle,
    'mapped I/O DMA byte matches the separately sampled pinned I/O register value');

  writesBeforeDma = core._get_vram_tx_counter(1);
  const wrappedDma = core._run_vram_tx_test(13, 0xfffe, 2, 0x3fffe, 2) >>> 0;
  assert.equal(wrappedDma >>> 16, 1,
    '68K DMA source local word counter advances after the 128 KiB rollover');
  assert.equal(wrappedDma & 0xffff, 2,
    'VRAM destination independently wraps at 64 KiB with increment two');
  assert.equal(((core._get_vram_tx_test_dma_region() << 17) |
    (core._get_vram_tx_test_dma_source() << 1)) >>> 0, 0x20002,
    'the 128 KiB source window rolls over while preserving its high register region');
  assert.equal(core._get_vram_tx_test_physical_byte(0xfffa), 0xa1,
    'first DMA destination contains data read from source 0x3fffe');
  assert.equal(core._get_vram_tx_test_physical_byte(0), 0xb2,
    'second DMA destination contains wrapped source 0x20000, not wrong-carry 0x40000');
  assert.equal(core._get_vram_tx_test_addr(), 2,
    'wrapped VRAM destination exposes the post-wrap byte address');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 4n,
    'two wrapped DMA words resolve four destination byte lanes');

  writesBeforeDma = core._get_vram_tx_counter(1);
  const partialDma = core._run_vram_tx_test(14, 0x5000, 0, 0, 2) >>> 0;
  assert.equal(partialDma >>> 16, 1,
    'one word remains after the first partial DMA timing interval');
  assert.equal(core._get_vram_tx_test_dma_remaining(), 1);
  assert.equal(core._get_vram_tx_test_addr(), 0x5001,
    'partial progress advances the destination by one word transfer');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 2n,
    'partial DMA interval transfers exactly one word');
  const completedDma = core._run_vram_tx_test(15, 0, 0, 0, 0) >>> 0;
  assert.equal(completedDma >>> 16, 0,
    'subsequent DMA timing interval completes the remaining word');
  assert.equal(core._get_vram_tx_test_dma_remaining(), 0);
  assert.equal(core._get_vram_tx_test_addr(), 0x5002);
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 4n,
    'completed DMA has transferred exactly two words total');

  // VRAM copy maps its XOR-selected source and destination independently;
  // Fill preserves its pre-latched FIFO high byte and destination XOR.
  assert.equal(core._run_vram_tx_test(0, 0x3400, 0x77aa, 0, 1), 0);
  assert.equal(core._run_vram_tx_test(8, 0x3600, 0, 0x3400, 1), 0,
    'VRAM copy DMA');
  assert.equal(core._get_vram_tx_test_physical_byte(0x3600), 0xaa);
  assert.equal(core._set_vram_transaction_diagnostic(2, 0, 2, 3), 0);
  writesBeforeDma = core._get_vram_tx_counter(1);
  const fillState = core._run_vram_tx_test(9, 0x1200, 0x1234, 0xe3, 1) >>> 0;
  assert.equal(fillState & 0xffff, 2,
    'real CPU control-port fill arm and data-port trigger');
  assert.equal(core._get_vram_tx_test_addr(), 0x1202,
    'control trigger and fill each advance the VDP address once');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1200), 0x12,
    'fill consumes the high byte latched by the real trigger data-port write');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1201), 0x34,
    'trigger word still writes its second lane before fill begins');
  assert.equal(core._get_vram_tx_counter(1), writesBeforeDma + 3n,
    'CPU fill trigger contributes two word lanes and one fill byte');

  // Mapped SAT destinations drive both VRAM and the digital internal mirror;
  // mirror interception remains active for a same-value VRAM write.
  assert.equal(core._set_vram_transaction_diagnostic(2, 128, -1, -1), 0);
  core._set_vram_tx_test_sat_physical_byte(0, 0);
  core._set_vram_tx_test_sat_physical_byte(1, 0);
  assert.equal(core._run_vram_tx_test(10, 0x8200, 0xabcd, 0, 1), 0);
  assert.equal(core._get_vram_tx_test_physical_byte(0), 0xab);
  assert.equal(core._get_vram_tx_test_physical_byte(1), 0xcd);
  assert.equal(core._get_vram_tx_test_sat_byte(0), 0xab);
  assert.equal(core._get_vram_tx_test_sat_byte(1), 0xcd);
  core._set_vram_tx_test_sat_physical_byte(0, 0x11);
  core._set_vram_tx_test_sat_physical_byte(1, 0x22);
  const changedBeforeSameWrite = core._get_vram_tx_counter(4);
  assert.equal(core._run_vram_tx_test(10, 0x8200, 0xabcd, 0, 1), 0);
  assert.equal(core._get_vram_tx_test_sat_byte(0), 0xab);
  assert.equal(core._get_vram_tx_test_sat_byte(1), 0xcd);
  assert.equal(core._get_vram_tx_counter(4), changedBeforeSameWrite,
    'same-value writes still refresh SAT mirror but do not report changed VRAM bytes');

  // The register-1 hook suspends and rebuilds the alias index at the actual
  // Mode 5 exit/re-entry point, even without a frame boundary.
  assert.equal(core._run_vram_tx_test(11, 0, 0x00, 0, 0), 0);
  const suspendedReads = core._get_vram_tx_counter(0);
  assert.equal(core._run_vram_tx_test(11, 0, 0x04, 0, 0), 0);
  assert.equal(core._run_vram_tx_test(2, 0x8200, 0, 0, 1), 0xcd);
  assert.ok(core._get_vram_tx_counter(0) > suspendedReads,
    'Mode 5 re-entry resumes transaction counters and mapping');

  assert.equal(core._set_vram_transaction_diagnostic(0, 0, -1, -1), 0);
  assert.equal(core._get_vram_tx_counter(1), 0n);
  assert.equal(core._set_vram_transaction_diagnostic(2, 0, -1, -1), 0,
    'identity transaction mode is selectable and leaves VRAM on the direct path');
  core._wasm_input_update(); core._tick();
  assert.equal(core._get_vram_tx_counter(1), 0n);
  core._clear_vram_tx_test_cache();
  assert.equal(core._run_vram_tx_test(0, 0x1200, 0x2468, 0, 1), 0,
    'diagnostic bridge invokes the core vdp_bus_w path');
  assert.equal(core._get_vram_tx_test_physical_byte(0x1200), 0x24,
    'identity selection uses original core write behavior');
  assert.notEqual(core._get_vram_tx_test_cache_dirty(0x1200 >>> 5) & 1, 0,
    'identity selection retains the original core pattern-cache dirty mark');
  console.log('VRAM transaction actual WASM integration passed.');
}

run().catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
