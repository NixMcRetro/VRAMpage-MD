/* VRAMpage MD: framebuffer adapter for the pinned wasm-genplus 640x480 RGBA output.
 * Source pixel data is never modified. This is DISPLAY recovery, not a VRAM fault.
 * If alternate entire output rows are empty, duplicate adjacent rendered lines.
 * Disable via 'Raw emulator output' to inspect exactly what the core produced.
 */
(function (root) {
  'use strict';
  const WIDTH = 320;
  const HEIGHT = 224;
  const PITCH = 640 * 4;
  const ROW_BYTES = WIDTH * 4;

  function copyActiveFrame(source, destination, options = {}) {
    if (!source || source.length < (HEIGHT - 1) * PITCH + ROW_BYTES)
      throw new RangeError('Framebuffer is smaller than the visible Mega Drive picture');
    if (!destination || destination.length < HEIGHT * ROW_BYTES)
      throw new RangeError('Destination video buffer is too small');

    // Never use CSS interpolation to hide holes: the raw source is readable.
    // Sample 32 evenly spaced RGB pixels per native row to find an absent field.
    // A truly blank row is checked fully before any repair takes place.
    let litEven = 0, litOdd = 0;
    const rowActive = new Uint8Array(HEIGHT);
    for (let y = 0; y < HEIGHT; y++) {
      const offset = y * PITCH;
      let active = false;
      for (let x = 0; x < WIDTH; x += 10) {
        const i = offset + 4 * x;
        if (source[i] | source[i + 1] | source[i + 2]) {
          active = true;
          break;
        }
      }
      rowActive[y] = active ? 1 : 0;
      if (active) { if (y & 1) litOdd++; else litEven++; }
    }

    // Guard against legitimate dark screens and ordinary VRAM corruption.
    // Repairs only overwhelmingly systematic whole-row blanking (112 rows/parity).
    let missingParity = -1;
    if (!options.raw) {
      if (litEven >= 88 && litOdd <= 8) missingParity = 1;
      else if (litOdd >= 88 && litEven <= 8) missingParity = 0;
    }

    function rowIsFullyBlack(y) {
      const start = y * PITCH;
      for (let x = 0; x < WIDTH; x++) {
        const i = start + x * 4;
        if (source[i] | source[i + 1] | source[i + 2]) return false;
      }
      return true;
    }

    let repairedRows = 0;
    for (let y = 0; y < HEIGHT; y++) {
      let sourceY = y;
      if (missingParity === (y & 1) && !rowActive[y] && rowIsFullyBlack(y)) {
        // Preserve vertical position by using the closest rendered row.
        const neighbor = y > 0 ? y - 1 : y + 1;
        if (rowActive[neighbor]) {
          sourceY = neighbor;
          repairedRows++;
        }
      }
      const start = sourceY * PITCH;
      destination.set(source.subarray(start, start + ROW_BYTES), y * ROW_BYTES);
    }
    return {repairedRows, missingParity, litEven, litOdd};
  }

  const api = Object.freeze({copyActiveFrame, WIDTH, HEIGHT, PITCH});
  root.VRAMpageFrame = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);