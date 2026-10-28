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

  function copyActiveFrame(source, destination, options = {}) {
    const width=options.width===undefined?WIDTH:options.width;
    const height=options.height===undefined?HEIGHT:options.height;
    if (!Number.isInteger(width)||width<1||width>640||!Number.isInteger(height)||height<1||height>480)
      throw new RangeError('Unsupported active framebuffer dimensions');
    const rowBytes=width*4;
    if (!source || source.length < (height - 1) * PITCH + rowBytes)
      throw new RangeError('Framebuffer is smaller than the visible Mega Drive picture');
    if (!destination || destination.length < height * rowBytes)
      throw new RangeError('Destination video buffer is too small');

    // Never use CSS interpolation to hide holes: the raw source is readable.
    // Sample RGB pixels across each native row to find an absent field.
    // A truly near-black row is checked fully before any repair takes place.
    let litEven = 0, litOdd = 0;
    const rowActive = new Uint8Array(height);
    for (let y = 0; y < height; y++) {
      const offset = y * PITCH;
      let active = false;
      for (let x = 0; x < width; x += 10) {
        const i = offset + 4 * x;
        if (source[i] > 16 || source[i + 1] > 16 || source[i + 2] > 16) {
          active = true;
          break;
        }
      }
      rowActive[y] = active ? 1 : 0;
      if (active) { if (y & 1) litOdd++; else litEven++; }
    }

    // An isolated missing row has usable picture immediately above and below.
    // Count isolated gaps instead of demanding a constant odd/even parity:
    // some core modes can switch field alignment in the middle of a display.
    let gaps = 0;
    let activeRows = litEven + litOdd;
    for (let y = 0; y < height; y++) {
      if (rowActive[y]) continue;
      if (y === 0 ? rowActive[1] : y === height - 1 ? rowActive[y - 1]
          : rowActive[y - 1] && rowActive[y + 1]) gaps++;
    }
    // A normal black background or an occasional black row should not change.
    // Require at least 70 isolated missing rows and 70 populated rows.
    const recover = !options.raw && gaps >= 70 && activeRows >= 70;
    let missingParity = -1;
    if (recover) {
      if (litEven >= 88 && litOdd <= 8) missingParity = 1;
      else if (litOdd >= 88 && litEven <= 8) missingParity = 0;
      else missingParity = 2; // Broken rows with mixed parity.
    }

    function rowIsFullyBlack(y) {
      const start = y * PITCH;
      for (let x = 0; x < width; x++) {
        const i = start + x * 4;
        if (source[i] > 16 || source[i + 1] > 16 || source[i + 2] > 16) return false;
      }
      return true;
    }

    let repairedRows = 0;
    for (let y = 0; y < height; y++) {
      let sourceY = y;
      const isolated = !rowActive[y] && (y === 0 ? !!rowActive[1] :
        y === height - 1 ? !!rowActive[y - 1] : !!(rowActive[y - 1] && rowActive[y + 1]));
      if (recover && isolated && rowIsFullyBlack(y)) {
        // Preserve vertical position by using the closest rendered row.
        const neighbor = y > 0 ? y - 1 : y + 1;
        if (rowActive[neighbor]) {
          sourceY = neighbor;
          repairedRows++;
        }
      }
      const start = sourceY * PITCH;
      destination.set(source.subarray(start, start + rowBytes), y * rowBytes);
    }
    return {repairedRows, missingParity, litEven, litOdd};
  }

  const api = Object.freeze({copyActiveFrame, WIDTH, HEIGHT, PITCH});
  root.VRAMpageFrame = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);