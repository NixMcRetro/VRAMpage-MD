'use strict';
// Data-oriented regression checks for the display adapter, with no ROM or browser.
const assert = require('node:assert/strict');
const {copyActiveFrame, WIDTH, HEIGHT, PITCH} = require('../site/framebuffer.js');
const ROW_BYTES = WIDTH * 4;
const inputBuffer = () => new Uint8Array(PITCH * 480);
const outputBuffer = () => new Uint8ClampedArray(ROW_BYTES * HEIGHT);

function makeProgressive(seed) {
  let n = seed >>> 0;
  const src = inputBuffer();
  for (let y = 0; y < HEIGHT; y++) {
    for (let x = 0; x < WIDTH; x++) {
      n ^= n << 13; n ^= n >>> 17; n ^= n << 5; n >>>= 0;
      const at = y * PITCH + x * 4;
      src[at] = 40 + (n % 160);
      src[at + 1] = 30 + ((n >>> 8) % 170);
      src[at + 2] = 35 + ((n >>> 16) % 160);
      src[at + 3] = 255;
    }
  }
  return src;
}
function expectedCrop(src) {
  const expected = outputBuffer();
  for (let y = 0; y < HEIGHT; y++)
    expected.set(src.subarray(y * PITCH, y * PITCH + ROW_BYTES), y * ROW_BYTES);
  return expected;
}

// Progressive scenes must remain byte-for-byte identical, with no interpolation.
for (const seed of [1, 17, 2345, 0xdecafbad]) {
  const src = makeProgressive(seed), untouched = src.slice(), out = outputBuffer();
  const status = copyActiveFrame(src, out);
  assert.equal(status.repairedRows, 0);
  assert.deepEqual(out, expectedCrop(src));
  assert.deepEqual(src, untouched, 'Rendering changed emulated memory');
}

// Raw mode must be a byte-accurate view, even if most odd rows are empty.
{
  const src = makeProgressive(42);
  for (let y = 1; y < HEIGHT; y += 2) src.fill(0, y * PITCH, y * PITCH + ROW_BYTES);
  const original = src.slice(), raw = outputBuffer(), recovered = outputBuffer();
  assert.equal(copyActiveFrame(src, raw, {raw: true}).repairedRows, 0);
  assert.deepEqual(raw, expectedCrop(src));
  assert.equal(copyActiveFrame(src, recovered).repairedRows, HEIGHT / 2);
  assert.deepEqual(src, original);
}

// A handful of isolated dark lines must not trigger whole-frame repairs.
{
  const src = makeProgressive(19), out = outputBuffer();
  for (let y = 21; y < 40; y += 2) src.fill(0, y * PITCH, y * PITCH + ROW_BYTES);
  assert.equal(copyActiveFrame(src, out).repairedRows, 0);
  assert.deepEqual(out, expectedCrop(src));
}

// Buffer bounds fail explicitly, rather than reading or writing out of range.
assert.throws(() => copyActiveFrame(new Uint8Array(30), outputBuffer()), RangeError);
assert.throws(() => copyActiveFrame(inputBuffer(), new Uint8ClampedArray(20)), RangeError);
console.log('Framebuffer property tests: seven cases passed.');