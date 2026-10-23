/* Visible Mode 5 synthetic scene for renderer read/caching checks. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const factories = process.argv.slice(2).map(p => ({p, f: require(path.resolve(p))}));
const FRAME_BYTES = 640 * 480 * 4;
function absWord(address, value) { return [0x33fc, value & 0xffff, address >>> 16, address & 0xffff]; }
function vdpRegister(reg, value) { return absWord(0xc00004, 0x8000 | ((reg & 0x1f) << 8) | (value & 0xff)); }
function vdpData(address, words) {
  const hi = 0x4000 | (address & 0x3fff), lo = (address >>> 14) & 3;
  const code = [...absWord(0xc00004, hi), ...absWord(0xc00004, lo)];
  for (const w of words) code.push(...absWord(0xc00000, w));
  return code;
}
function vdpCram(address, words) {
  const code = [...absWord(0xc00004, 0xc000 | (address & 0x3f)),
                ...absWord(0xc00004, (address >>> 14) & 3)];
  for (const w of words) code.push(...absWord(0xc00000, w));
  return code;
}
function visibleCartridge(scrollPixels = 0, options = {}) {
  const rom = new Uint8Array(0x80000), view = new DataView(rom.buffer);
  for (let o = 0; o < 0x100; o += 4) view.setUint32(o, 0x300);
  view.setUint32(0, 0xffff00); view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE VISIBLE RENDER TEST'), 0x120);
  view.setUint32(0x1a4, rom.length - 1); view.setUint32(0x1a8, 0xff0000); view.setUint32(0x1ac, 0xffffff);
  let words = [];
  // Select Mode 5 and table layout while display is still off.
  words.push(...vdpRegister(1, 0x34), ...vdpRegister(2, 0x38),
    ...vdpRegister(4, 0x07), ...vdpRegister(7, 0),
    ...vdpRegister(11, options.vscroll ? 0x04 : 0),
    ...vdpRegister(12, options.interlace2 ? 0x87 : 0x81),
    ...vdpRegister(13, 0x3f), ...vdpRegister(15, 2));
  // Colors 0..3 and two visibly different repeated-pixel pattern tiles.
  words.push(...vdpCram(0, [0x000e, 0x00e0, 0x0e00, 0x0eee]));
  words.push(...vdpData(0x2000, Array(16).fill(0x1111)));
  words.push(...vdpData(0x2020, Array(16).fill(0x2222)));
  words.push(...vdpData(0x2040, Array(16).fill(0x3333)));
  words.push(...vdpData(0xe000, [0x0100, 0x0101, 0x0102, ...Array(29).fill(0x0100)]));
  const scrollTable = Array(40).fill(0x0000);
  if (scrollPixels) scrollTable[0] = 0x0003;
  words.push(...vdpData(0xfc00, scrollTable));
  words.push(...vdpRegister(1, 0x74)); // Display enable after scene setup.
  words.push(0x4e72, 0x2700, 0x60fe); // STOP, then remain stopped.
  words.forEach((w, i) => view.setUint16(0x200 + i * 2, w));
  return rom;
}
async function makeCore({p, f}, rom) {
  const c = await f({locateFile: name => path.join(path.dirname(p), name)});
  c._init(); c.HEAPU8.set(rom, c._get_rom_buffer_ref(rom.length)); c._start();
  new Float32Array(c.HEAPF32.buffer, c._get_input_buffer_ref(), 32).fill(0);
  return c;
}
function frame(c) {
  const p = c._get_frame_buffer_ref();
  return Buffer.from(c.HEAPU8.subarray(p, p + FRAME_BYTES));
}
function pixel(f, x, y) {
  const i = (y * 640 + x) * 4;
  return [...f.subarray(i, i + 4)];
}
function observable(c, samples) {
  const f = frame(c);
  const left = c._get_web_audio_l_ref() >>> 2;
  const right = c._get_web_audio_r_ref() >>> 2;
  const ram = c._get_logic_ram_ref();
  return {
    frame: f,
    audioSamples: samples,
    audioLeft: Float32Array.from(c.HEAPF32.subarray(left, left + samples)),
    audioRight: Float32Array.from(c.HEAPF32.subarray(right, right + samples)),
    ram: Buffer.from(c.HEAPU8.subarray(ram, ram + 0x10000)),
    logicFrame: c._get_logic_frame(), cpuFlags: c._get_logic_cpu_flags()
  };
}
async function runScene(entry, rom, ticks = 5) {
  const c = await makeCore(entry, rom);
  let samples = 0;
  for (let t = 0; t < ticks; t++) { c._wasm_input_update(); c._tick(); samples = c._sound(); }
  return {c, state: observable(c, samples)};
}
function equivalent(actual, expected, label) {
  assert.equal(actual.audioSamples, expected.audioSamples, `${label}: audio sample count`);
  assert.deepEqual(actual.frame, expected.frame, `${label}: complete framebuffer`);
  assert.deepEqual(actual.audioLeft, expected.audioLeft, `${label}: left audio`);
  assert.deepEqual(actual.audioRight, expected.audioRight, `${label}: right audio`);
  assert.deepEqual(actual.ram, expected.ram, `${label}: RAM`);
  assert.equal(actual.logicFrame, expected.logicFrame, `${label}: logic frame`);
  assert.equal(actual.cpuFlags, expected.cpuFlags, `${label}: CPU flags`);
}
function nextFrame(c) { c._wasm_input_update(); c._tick(); return observable(c, c._sound()); }
async function main() {
  const [baselinePath, normalPath, diagnosticPath, altDiagnosticPath] = process.argv.slice(2);
  if (!diagnosticPath) throw new Error('Pass PR36 baseline, current normal, and diagnostic core paths.');
  const baselineEntry = {p: path.resolve(baselinePath), f: require(path.resolve(baselinePath))};
  const normalEntry = {p: path.resolve(normalPath), f: require(path.resolve(normalPath))};
  const diagnosticEntry = {p: path.resolve(diagnosticPath), f: require(path.resolve(diagnosticPath))};
  const altEntry = altDiagnosticPath && {
    p: path.resolve(altDiagnosticPath), f: require(path.resolve(altDiagnosticPath))};
  const rom = visibleCartridge();
  const baseline = await runScene(baselineEntry, rom);
  const scrollBaseline = await runScene(baselineEntry, visibleCartridge(3));
  const scrollDiagnostic = await runScene(diagnosticEntry, visibleCartridge(3));
  assert.deepEqual(pixel(scrollBaseline.state.frame, 8, 0), [0, 34, 0, 255],
    'independent hscroll ROM moves the first tile boundary three pixels right');
  assert.equal(scrollDiagnostic.c._get_vram_tx_test_hscroll_base(), 0xfc00);
  assert.deepEqual([0,1,2,3].map(i=>scrollDiagnostic.c._get_vram_tx_test_byte(0xfc00+i)),
    [0,3,0,0], 'ROM initializes the distinct logical hscroll bytes for row zero');
  const vsScene = await runScene(diagnosticEntry, visibleCartridge(0, {vscroll: true}));
  assert.equal(vsScene.c._get_vram_tx_test_render_path(), 2,
    'register 11 selects the real Mode 5 vertical-scroll renderer');
  const interlaceVsScene = await runScene(diagnosticEntry,
    visibleCartridge(0, {vscroll: true, interlace2: true}), 8);
  assert.equal(interlaceVsScene.c._get_vram_tx_test_render_path(), 4,
    'registers 11 and 12 select the real Mode 5 interlace-2 vertical-scroll renderer');
  const normal = await runScene(normalEntry, rom);
  const diagnosticOff = await runScene(diagnosticEntry, rom);
  equivalent(normal.state, baseline.state, 'current normal vs pinned PR36 renderer');
  equivalent(diagnosticOff.state, baseline.state, 'diagnostic off vs pinned PR36 renderer');
  if (altEntry) {
    const alt = await runScene(altEntry, rom);
    equivalent(alt.state, baseline.state, 'ALT_RENDERER diagnostic off vs pinned PR36 renderer');
    const altAlias = await runScene(altEntry, rom, 5);
    assert.equal(altAlias.c._set_vram_transaction_diagnostic(2, 8, -1, -1), 0,
      'ALT_RENDERER AD3 selection succeeds for active visible cache fixture');
    const altMapped = nextFrame(altAlias.c);
    assert.deepEqual(pixel(altMapped.frame, 0, 0), [0, 34, 0, 255]);
    assert.deepEqual(pixel(altMapped.frame, 8, 0), [0, 34, 0, 255],
      'ALT_RENDERER pattern-cache read aliases the second visible logical tile');
    altAlias.c._clear_vram_tx_test_cache();
    assert.equal(altAlias.c._run_vram_tx_test(0, 0x2820, 0x0000, 0, 1), 0,
      'ALT_RENDERER third logical alias writes shared pattern data');
    assert.notEqual(altAlias.c._get_vram_tx_test_cache_dirty(256), 0,
      'ALT_RENDERER write invalidates logical pattern key256');
    assert.notEqual(altAlias.c._get_vram_tx_test_cache_dirty(257), 0,
      'ALT_RENDERER write invalidates logical pattern key257');
    const altChanged = nextFrame(altAlias.c);
    assert.deepEqual(pixel(altChanged.frame, 0, 0), pixel(altChanged.frame, 8, 0),
      'ALT_RENDERER refreshes both aliased visible pattern keys');
  }
  assert.deepEqual(pixel(baseline.state.frame, 0, 0), [0, 34, 0, 255],
    'independent expected first tile pixel (palette entry 1)');
  assert.deepEqual(pixel(baseline.state.frame, 8, 0), [0, 0, 34, 255],
    'independent expected second tile pixel (palette entry 2)');
  assert.deepEqual(pixel(baseline.state.frame, 16, 0), [34, 34, 34, 255],
    'independent expected third tile pixel (palette entry 3)');
  const opaquePixels = Array.from({length: 640 * 480}, (_, i) => baseline.state.frame[i * 4 + 3])
    .filter(alpha => alpha === 255).length;
  assert.ok(opaquePixels > 70000, 'display-enabled scene produces a full visible plane');

  const identity = await runScene(diagnosticEntry, rom, 4);
  assert.equal(identity.c._set_vram_transaction_diagnostic(2, 0, -1, -1), 0,
    'identity transaction selection succeeds in Mode 5');
  equivalent(nextFrame(identity.c), baseline.state, 'selected identity vs pinned PR36 renderer');
  assert.equal(identity.c._get_vram_tx_counter(1), 0n, 'identity path has no mapped writes');

  // AD3 aliases pattern-cache keys 256 and 257 at 0x2000. The independent
  // expected scene uses distinct palette pixels for those two keys and key258.
  const alias = await runScene(diagnosticEntry, rom, 5);
  assert.equal(alias.c._set_vram_transaction_diagnostic(2, 8, -1, -1), 0,
    'AD3 selection succeeds for the visible cache-alias fixture');
  assert.notEqual(alias.c._set_vram_transaction_diagnostic(2, 256, -1, -1), 0,
    'invalid mask is rejected without replacing active transaction settings');
  const aliased = nextFrame(alias.c);
  assert.deepEqual(pixel(aliased.frame, 0, 0), [0, 34, 0, 255]);
  assert.deepEqual(pixel(aliased.frame, 8, 0), [0, 34, 0, 255],
    'logical pattern key257 reads the same mapped bytes as key256');
  assert.deepEqual(pixel(aliased.frame, 16, 0), [34, 34, 34, 255],
    'logical pattern key258 remains a distinct visible cache key');
  assert.deepEqual(pixel(aliased.frame, 16, 0), [34, 34, 34, 255],
    'zero hscroll keeps the third tile at its original visible boundary');
  const hscrollAlias = await runScene(diagnosticEntry, rom, 5);
  assert.equal(hscrollAlias.c._set_vram_transaction_diagnostic(2, 8, -1, -1), 0,
    'AD3 selection succeeds for the visible hscroll fixture');
  assert.equal(hscrollAlias.c._run_vram_tx_test(0, 0xfc00, 0x0003, 0, 1), 0,
    'AD3-alias write targets the mapped row-zero horizontal-scroll bytes');
  const scrolled = nextFrame(hscrollAlias.c);
  assert.deepEqual(pixel(scrolled.frame, 16, 0), [0, 34, 0, 255],
    'mapped hscroll u32 read moves the third-tile boundary by three pixels');
  alias.c._clear_vram_tx_test_cache();
  assert.equal(alias.c._run_vram_tx_test(0, 0x2820, 0x0000, 0, 1), 0,
    'a third logical alias writes the shared pattern bytes through the real VDP handler');
  assert.notEqual(alias.c._get_vram_tx_test_cache_dirty(256), 0,
    'changed physical byte invalidates logical pattern key256');
  assert.notEqual(alias.c._get_vram_tx_test_cache_dirty(257), 0,
    'changed physical byte invalidates logical pattern key257');
  const changed = nextFrame(alias.c);
  assert.notDeepEqual(pixel(changed.frame, 0, 0), pixel(aliased.frame, 0, 0),
    'first visible logical pattern updates after third-alias write');
  assert.notDeepEqual(pixel(changed.frame, 8, 0), pixel(aliased.frame, 8, 0),
    'second visible logical pattern updates after third-alias write');
  assert.deepEqual(pixel(changed.frame, 0, 0), pixel(changed.frame, 8, 0),
    'both aliased visible patterns converge on the changed shared physical bytes');

  assert.equal(alias.c._run_vram_tx_test(11, 0, 0x00, 0, 0), 0,
    'leave Mode 5 while the transaction selection remains configured');
  nextFrame(alias.c);
  assert.equal(alias.c._run_vram_tx_test(11, 0, 0x74, 0, 0), 0,
    're-enter Mode 5 without changing the selected transaction settings');
  const reentered = nextFrame(alias.c);
  assert.deepEqual(pixel(reentered.frame, 0, 0), pixel(reentered.frame, 8, 0),
    'Mode 5 re-entry rebuilds aliases and refreshes both visible pattern keys');

  assert.equal(alias.c._set_vram_transaction_diagnostic(2, 0, -1, -1), 0,
    'faulted alias selection can reconnect to a selected identity transaction');
  const identityRestored = nextFrame(alias.c);
  assert.deepEqual(pixel(identityRestored.frame, 8, 0), [0, 0, 34, 255],
    'selected identity clears the prior fault and restores raw tile257 pixels');
  assert.equal(alias.c._get_vram_tx_counter(1), 0n,
    'selected identity reports no mapped writes after fault removal');

  assert.equal(alias.c._set_vram_transaction_diagnostic(0, 0, -1, -1), 0,
    'disabling the transaction mapping restores direct renderer reads');
  const restored = nextFrame(alias.c);
  assert.deepEqual(pixel(restored.frame, 8, 0), [0, 0, 34, 255],
    'raw tile257 value returns after mapping is disabled and cache is refreshed');
  assert.deepEqual(pixel(restored.frame, 16, 0), [34, 34, 34, 255],
    'unaliased raw tile258 remains independently visible');

  const names = await runScene(diagnosticEntry, rom, 5);
  assert.equal(names.c._set_vram_transaction_diagnostic(2, 1, -1, -1), 0,
    'AD0 selection succeeds for the name-table alias fixture');
  const nameAliased = nextFrame(names.c);
  assert.notDeepEqual(pixel(nameAliased.frame, 16, 0), pixel(baseline.state.frame, 16, 0),
    'the third name-table cell changes when its logical word aliases e000');
  assert.deepEqual(pixel(nameAliased.frame, 0, 0), pixel(nameAliased.frame, 16, 0),
    'name cells zero and two resolve through the same mapped name-table bytes');
  console.log('VRAM visible renderer fixture passed: baseline equivalence, visible aliases, cache refresh, reconnect.');
}
main().catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
