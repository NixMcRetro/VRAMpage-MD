/*
 * RGB input-contact approximation for the browser's RGBA framebuffer.
 *
 * The pinned core expands 3-bit Mode 5 CRAM channels to display-byte codes;
 * those bytes are not calibrated CXA1145 voltages or linear-light values.
 * This model uses code/255 only as an explicit normalized source-voltage proxy.
 * A cut is black-terminated at the same normalized source impedance. A pair
 * is one zero-resistance join between equal-impedance sources, after cuts.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VRAMpageRgbEncoder = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const MODEL_VERSION = 'rgb-input-code-voltage-v1';
  const CONFIG_KEYS = ['cutMask', 'pair'];

  function exactOwnKeys(value, expected, label) {
    if (value === null || typeof value !== 'object' ||
        (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null))
      throw new TypeError(label + ' must be a plain object');
    const keys = Reflect.ownKeys(value);
    if (keys.length !== expected.length || expected.some(key => !Object.prototype.hasOwnProperty.call(value, key)) ||
        keys.some(key => typeof key !== 'string' || !expected.includes(key)))
      throw new TypeError(label + ' has unexpected or missing keys');
  }

  function canonicalPair(pair) {
    if (pair === null) return null;
    if (!Array.isArray(pair) || Object.getPrototypeOf(pair) !== Array.prototype || pair.length !== 2 ||
        Reflect.ownKeys(pair).length !== 3 || !Object.prototype.hasOwnProperty.call(pair, 0) ||
        !Object.prototype.hasOwnProperty.call(pair, 1))
      throw new TypeError('pair must be null or an exact two-channel array');
    const [a, b] = pair;
    if (!Number.isInteger(a) || !Number.isInteger(b) || a < 0 || a > 2 || b < 0 || b > 2 || a === b)
      throw new RangeError('pair channels must be distinct indexes from 0 through 2');
    return Object.freeze(a < b ? [a, b] : [b, a]);
  }

  function create(configuration) {
    exactOwnKeys(configuration, CONFIG_KEYS, 'configuration');
    const cutMask = configuration.cutMask;
    if (!Number.isInteger(cutMask) || cutMask < 0 || cutMask > 7)
      throw new RangeError('cutMask must be an integer from 0 through 7');
    const pair = canonicalPair(configuration.pair);
    const config = Object.freeze({cutMask, pair});
    const active = cutMask !== 0 || pair !== null;

    function apply(pixels) {
      if (!(pixels instanceof Uint8Array || pixels instanceof Uint8ClampedArray) || pixels.length % 4 !== 0)
        throw new TypeError('pixels must be an RGBA Uint8Array or Uint8ClampedArray');
      if (!active) return pixels;

      const cutR = cutMask & 1, cutG = cutMask & 2, cutB = cutMask & 4;
      const pairA = pair === null ? -1 : pair[0], pairB = pair === null ? -1 : pair[1];
      for (let i = 0; i < pixels.length; i += 4) {
        let r = cutR ? 0 : pixels[i];
        let g = cutG ? 0 : pixels[i + 1];
        let b = cutB ? 0 : pixels[i + 2];
        if (pairA === 0 || pairB === 0) {
          const other = pairA === 0 ? pairB : pairA;
          r = Math.floor((r + (other === 1 ? g : b) + 1) / 2);
          if (other === 1) g = r; else b = r;
        } else if (pairA === 1 || pairB === 1) {
          g = Math.floor((g + b + 1) / 2);
          b = g;
        }
        pixels[i] = r;
        pixels[i + 1] = g;
        pixels[i + 2] = b;
      }
      return pixels;
    }

    return Object.freeze({modelVersion: MODEL_VERSION, configuration: config, active, apply});
  }

  return Object.freeze({modelVersion: MODEL_VERSION, create});
});
