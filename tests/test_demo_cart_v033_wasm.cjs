/* Run the exact experimental Demo Cart inside compiled Genesis Plus GX WASM.
 * This is a runtime probe, not a replacement for human visual acceptance.
 * Usage: node tests/test_demo_cart_v033_wasm.cjs site/core/genplus.js
 */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const coreFile = path.resolve(process.argv[2] || 'site/core/genplus.js');
const romFile = path.join(root, 'demo-cart/fx-lab/build/VRAMpage-MD-FX-Lab-v0.3.3-Demoscene.bin');
const reportFile = path.join(root, 'demo-cart/fx-lab/build/rom_report.json');
const output = path.join(root, 'artifacts/demo-cart-v033-genplus');
const WIDTH = 320, HEIGHT = 224, PITCH = 640;
const PREVIOUS_SHA = 'd68e000980a38c715f8c057564e06f9c29e29025e9396232c15d9a5b9a334386';
// Pin the new digest after the first generated CI artefact has been independently inspected.
const EXPECTED_SHA = null;

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const value of bytes) {
    crc ^= value;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function pngChunk(type, data) {
  const name = Buffer.from(type, 'ascii');
  const out = Buffer.alloc(data.length + 12);
  out.writeUInt32BE(data.length, 0);
  name.copy(out, 4);
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}
function png(rgba) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(WIDTH, 0);
  header.writeUInt32BE(HEIGHT, 4);
  header[8] = 8; header[9] = 6;
  const scanlines = Buffer.alloc(HEIGHT * (1 + WIDTH * 4));
  for (let y = 0; y < HEIGHT; y++) {
    const offset = y * (1 + WIDTH * 4);
    scanlines[offset] = 0;
    rgba.copy(scanlines, offset + 1, y * WIDTH * 4, (y + 1) * WIDTH * 4);
  }
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),
    pngChunk('IHDR', header), pngChunk('IDAT', zlib.deflateSync(scanlines)),
    pngChunk('IEND', Buffer.alloc(0))]);
}
function visiblePixels(core) {
  const mem = core.HEAPU8, base = core._get_frame_buffer_ref();
  const rgba = Buffer.alloc(WIDTH * HEIGHT * 4);
  for (let y = 0; y < HEIGHT; y++) {
    rgba.set(mem.subarray(base + y * PITCH * 4, base + y * PITCH * 4 + WIDTH * 4),
      y * WIDTH * 4);
  }
  return rgba;
}
async function machine(region, rom) {
  const core = await require(coreFile)({locateFile: name => path.join(path.dirname(coreFile), name)});
  core._init();
  assert.equal(core._set_region_request(region), 0);
  core.HEAPU8.set(rom, core._get_rom_buffer_ref(rom.length));
  core._start();
  const input = new Float32Array(core.HEAPF32.buffer, core._get_input_buffer_ref(), 32);
  function frame(button) {
    input.fill(0);
    if (button === 'up') input[7] = -1;
    if (button === 'down') input[7] = 1;
    if (button === 'left') input[6] = -1;
    if (button === 'right') input[6] = 1;
    if (button === 'A') input[10] = 1;
    if (button === 'B') input[11] = 1;
    if (button === 'C') input[9] = 1;
    if (button === 'START') input[15] = 1;
    core._wasm_input_update();
    core._tick();
    const count = core._sound();
    assert.ok(count >= 0 && count <= 2048, 'WASM audio frame stays inside output buffer');
    return count;
  }
  function run(n) { for (let i = 0; i < n; i++) frame(); }
  function press(key) { frame(key); run(2); }
  function capture(label) {
    const rgba = visiblePixels(core);
    const colours = new Set();
    let nonBlack = 0;
    for (let y = 0; y < HEIGHT; y += 2) for (let x = 0; x < WIDTH; x += 2) {
      const p = 4 * (y * WIDTH + x), r = rgba[p], g = rgba[p+1], b = rgba[p+2];
      colours.add((r << 16) | (g << 8) | b);
      if (r || g || b) nonBlack++;
    }
    const digest = crypto.createHash('sha256').update(rgba).digest('hex');
    fs.writeFileSync(path.join(output, label + '.png'), png(rgba));
    const sample = {label, region, nativeFrame:core._get_logic_frame(),
      uniqueColours:colours.size, nonBlack, rgbaSHA256:digest};
    assert.ok(colours.size >= 5 && nonBlack >= 500,
      'Real Genesis Plus GX frame unexpectedly empty: ' + JSON.stringify(sample));
    return sample;
  }
  return {core, frame, run, press, capture};
}

(async () => {
  fs.mkdirSync(output, {recursive:true});
  const rom = fs.readFileSync(romFile);
  const report = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
  const sha = crypto.createHash('sha256').update(rom).digest('hex');
  assert.equal(rom.length, 150170, 'Test only the exact v0.3.3 build, never a stale ROM');
  assert.notEqual(sha, PREVIOUS_SHA, 'v0.3.3 must not reproduce the broken v0.3.2 map');
  if (EXPECTED_SHA) assert.equal(sha, EXPECTED_SHA);
  assert.equal(report.sha256, sha);
  assert.equal(report.romSize, rom.length);
  const captures = [];

  // NTSC-U: actual three-button input, menu and two new FX scenes.
  const manual = await machine(1, rom);
  manual.run(15);
  captures.push(manual.capture('ntsc-title'));
  manual.press('down');
  captures.push(manual.capture('ntsc-selector-1'));
  manual.press('down');
  captures.push(manual.capture('ntsc-selector-2'));
  // v0.3.2 had a fixed cyan arrow behind a second moving blue SAT cursor.
  // Once the cursor reaches item 3, item 1's old arrow area must be empty.
  {
    const frame = visiblePixels(manual.core);
    let stray = 0;
    for (let y = 69; y < 77; y++) for (let x = 11; x < 19; x++) {
      const p = (y * WIDTH + x) * 4;
      if (frame[p] + frame[p+1] + frame[p+2] > 35) stray++;
    }
    assert.equal(stray, 0, 'Obsolete first-row arrow must not coexist with moving selector');
  }
  manual.press('A');
  manual.run(25);
  const sprite1 = manual.capture('ntsc-sprite-storm-early');
  manual.run(28);
  const sprite2 = manual.capture('ntsc-sprite-storm-later');
  captures.push(sprite1, sprite2);
  assert.notEqual(sprite1.rgbaSHA256, sprite2.rgbaSHA256,
    'Sprite Storm output must change during real emulation');
  manual.press('START');
  manual.run(12);
  captures.push(manual.capture('ntsc-return-to-selector'));
  manual.press('down');
  manual.press('A');
  manual.run(25);
  const chroma1 = manual.capture('ntsc-chroma-reactor-early');
  manual.run(28);
  const chroma2 = manual.capture('ntsc-chroma-reactor-later');
  captures.push(chroma1, chroma2);
  assert.notEqual(chroma1.rgbaSHA256, chroma2.rgbaSHA256,
    'Chroma Reactor output must change during real emulation');
  assert.notEqual(sprite1.rgbaSHA256, chroma1.rgbaSHA256,
    'Sprite Storm and Chroma Reactor must display different native frames');

  // Continuous attract loop under both 60 Hz-class NTSC and 50 Hz PAL.
  for (const [region, label, moments] of [
    [1, 'ntsc', [['title',15], ['vortex',650], ['aurora',1390],
      ['sprite',2120], ['chroma',2610], ['psg',3100], ['title-return',3550]]],
    [2, 'pal', [['title',15], ['vortex',550], ['aurora',1160],
      ['sprite',1770], ['chroma',2190], ['psg',2600], ['title-return',2970]]]
  ]) {
    const auto = await machine(region, rom);
    let previousFrame = 0;
    const series = [];
    for (const [scene, targetFrame] of moments) {
      auto.run(targetFrame - previousFrame);
      previousFrame = targetFrame;
      const sample = auto.capture(label + '-auto-' + scene);
      captures.push(sample);
      series.push(sample.rgbaSHA256);
    }
    assert.ok(new Set(series).size >= 5,
      label + ' attract cycle must show multiple visibly distinct native frames');
    assert.equal(auto.core._get_region_state().pal, region === 2);
    assert.equal(auto.core._get_logic_frame(), moments[moments.length-1][1]);
  }

  const result = {romSize:rom.length, romSHA256:sha,
    engine:'real compiled Genesis Plus GX WebAssembly', regions:['NTSC-U','PAL'],
    scope:'Native framebuffer, input and attract-loop smoke; visual design review remains manual',
    captures};
  fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result, null, 2)+'\n');
  console.log('PASS actual Genesis Plus GX v0.3.3 ROM test; frames saved: ' + captures.length);
  console.log(JSON.stringify(result, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
