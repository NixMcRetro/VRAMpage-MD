'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const encoder = require('../site/rgb-encoder.js');

const clone = pixels => new Uint8Array(pixels);
const rgba = (r, g, b, a=255) => new Uint8Array([r, g, b, a]);
const pairCases = [
  {pair:[0,1], left:0, right:1},
  {pair:[0,2], left:0, right:2},
  {pair:[1,2], left:1, right:2}
];

assert.equal(encoder.modelVersion, 'rgb-input-code-voltage-v1');
assert.equal(typeof encoder.create, 'function');

// CRAM-like primary bars and greys prove pair joins preserve their source mean.
const bars = new Uint8Array([
  255,0,0,255, 0,255,0,128, 0,0,255,0,
  255,255,255,17, 0,0,0,18, 85,85,85,19
]);
for (const {pair,left,right} of pairCases) {
  const output = clone(bars);
  const plan = encoder.create({cutMask:0,pair}).apply(output);
  assert.equal(plan, output, 'active application mutates and returns the supplied frame');
  for (let i=0; i<bars.length; i+=4) {
    const mean = Math.floor((bars[i+left]+bars[i+right]+1)/2);
    assert.equal(output[i+left], mean, `${pair} joined first channel at pixel ${i/4}`);
    assert.equal(output[i+right], mean, `${pair} joined second channel at pixel ${i/4}`);
    for (let channel=0; channel<3; channel++)
      if (channel!==left && channel!==right)
        assert.equal(output[i+channel], bars[i+channel], `${pair} leaves the third channel untouched`);
    assert.equal(output[i+3], bars[i+3], 'join preserves alpha');
  }
}

// Half-up integer code rounding is explicit: 255 and 0 join at 128; 5 and 0 at 3.
for (const pair of [[0,1],[0,2],[1,2]]) {
  const p = encoder.create({cutMask:0,pair});
  const pixels = rgba(255,0,5);
  p.apply(pixels);
  const [a,b] = pair;
  assert.equal(pixels[a], Math.floor(([255,0,5][a]+[255,0,5][b]+1)/2));
  assert.equal(pixels[b], pixels[a]);
}

// A cut is black termination at the same normalized impedance; cuts precede a join.
const cutThenJoin = encoder.create({cutMask:1,pair:[1,0]});
const cutFrame = new Uint8Array([255,64,10,7, 80,255,31,9]);
cutThenJoin.apply(cutFrame);
assert.deepEqual([...cutFrame], [32,32,10,7, 128,128,31,9]);
const allCut = encoder.create({cutMask:7,pair:null});
const allCutPixels = new Uint8Array([1,2,3,4, 255,128,64,5]);
allCut.apply(allCutPixels);
assert.deepEqual([...allCutPixels], [0,0,0,4, 0,0,0,5]);

// Exhaust every mask and pair option against the stated per-channel equations.
const options = [null,[0,1],[0,2],[1,2]];
for (let mask=0; mask<8; mask++) for (const pair of options) {
  const input = new Uint8Array([1,42,255,3, 127,128,129,4, 0,5,254,5]);
  const expected = clone(input);
  for (let i=0; i<input.length; i+=4) {
    const rgb = [0,1,2].map(c => mask & (1<<c) ? 0 : input[i+c]);
    if (pair) {
      const mean=Math.floor((rgb[pair[0]]+rgb[pair[1]]+1)/2);
      rgb[pair[0]]=mean;rgb[pair[1]]=mean;
    }
    expected.set(rgb,i);
  }
  const target = clone(input);
  const plan=encoder.create({cutMask:mask,pair});
  assert.equal(plan.active, mask!==0 || pair!==null);
  assert.deepEqual([...plan.apply(target)], [...expected], `mask ${mask}, pair ${pair}`);
}

// The disabled plan is an identity fast path and preserves frame storage exactly.
const disabled = encoder.create({cutMask:0,pair:null});
const identityPixels = new Uint8ClampedArray([0,17,255,23, 32,64,128,0]);
const identityBefore = clone(identityPixels);
assert.equal(disabled.active, false);
assert.equal(disabled.apply(identityPixels), identityPixels);
assert.deepEqual([...identityPixels], [...identityBefore]);

// Config is cloned, canonical, and immutable at each exposed level.
const source = {cutMask:2,pair:[2,0]};
const canonical = encoder.create(source);
source.cutMask=7;source.pair.reverse();
assert.deepEqual(canonical.configuration, {cutMask:2,pair:[0,2]});
assert.ok(Object.isFrozen(canonical));
assert.ok(Object.isFrozen(canonical.configuration));
assert.ok(Object.isFrozen(canonical.configuration.pair));
assert.throws(() => { canonical.configuration.cutMask=0; }, TypeError);
assert.throws(() => { canonical.configuration.pair[0]=1; }, TypeError);

// Reject malformed public requests before touching any destination bytes.
const invalidConfigurations = [
  null, [], {cutMask:0}, {cutMask:0,pair:null,extra:true},
  {cutMask:false,pair:null}, {cutMask:1.5,pair:null}, {cutMask:8,pair:null},
  {cutMask:-1,pair:null}, {cutMask:0,pair:[]}, {cutMask:0,pair:[0]},
  {cutMask:0,pair:[0,0]}, {cutMask:0,pair:[0,3]}, {cutMask:0,pair:[0,1.1]},
  {cutMask:0,pair:[0,1,2]}, Object.assign(Object.create({}),{cutMask:0,pair:null}),
  Object.defineProperty({cutMask:0,pair:null}, Symbol('unexpected'), {value:1})
];
for (const configuration of invalidConfigurations)
  assert.throws(() => encoder.create(configuration), 'invalid config must be rejected');
const active=encoder.create({cutMask:0,pair:[0,1]});
for (const invalidPixels of [null, [], new Uint16Array(4), new DataView(new ArrayBuffer(4)), new Uint8Array(3)]) {
  const before=invalidPixels instanceof Uint8Array ? clone(invalidPixels) : null;
  assert.throws(() => active.apply(invalidPixels), 'invalid frame shape must be rejected');
  if (before) assert.deepEqual(invalidPixels, before, 'invalid frame remains untouched');
}

// The same file installs the documented global when loaded as a browser script.
const browserGlobal = {};
vm.runInNewContext(fs.readFileSync(require.resolve('../site/rgb-encoder.js'),'utf8'), browserGlobal);
assert.equal(browserGlobal.VRAMpageRgbEncoder.modelVersion, encoder.modelVersion);
assert.deepEqual(Array.from(vm.runInNewContext(
  '[...VRAMpageRgbEncoder.create({cutMask:0,pair:[0,2]}).apply(new Uint8Array([255,0,0,255]))]',
  browserGlobal)), [128,0,128,255]);

console.log('RGB encoder code-domain cuts, pair joins, rounding, validation, and identity passed.');
