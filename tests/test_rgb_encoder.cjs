'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const encoder = require('../site/rgb-encoder.js');

const clone = pixels => new Uint8Array(pixels);
const rgba = (r, g, b, a=255) => new Uint8Array([r, g, b, a]);
const pairCases = [[0,1],[0,2],[1,2]];

assert.equal(encoder.modelVersion, 'rgb-input-code-voltage-v1');
assert.equal(typeof encoder.create, 'function');

// Literal primary bars exercise each join, including three half-up 255/0 cases.
const bars = new Uint8Array([
  255,0,0,255, 0,255,0,128, 0,0,255,0,
  255,255,255,17, 0,0,0,18, 85,86,84,19
]);
const literalBars = [
  [128,128,0,255, 128,128,0,128, 0,0,255,0, 255,255,255,17, 0,0,0,18, 86,86,84,19],
  [128,0,128,255, 0,255,0,128, 128,0,128,0, 255,255,255,17, 0,0,0,18, 85,86,85,19],
  [255,0,0,255, 0,128,128,128, 0,128,128,0, 255,255,255,17, 0,0,0,18, 85,85,85,19]
];
for (let index=0; index<pairCases.length; index++) {
  const pair = pairCases[index];
  const output = clone(bars);
  const returned = encoder.create({cutMask:0,pair}).apply(output);
  assert.equal(returned, output, 'active application mutates and returns the supplied frame');
  assert.deepEqual([...output], literalBars[index], `literal RGBA bars for ${pair}`);
}

// Equal codes across a grey ramp are unchanged by any pair; odd sums round up.
const greyRamp = new Uint8Array([
  0,0,0,255, 17,17,17,192, 85,85,85,128, 128,128,128,64, 255,255,255,0
]);
for (const pair of pairCases)
  assert.deepEqual([...encoder.create({cutMask:0,pair}).apply(clone(greyRamp))], [...greyRamp]);
const oddRounding = rgba(5,0,0);
encoder.create({cutMask:0,pair:[0,1]}).apply(oddRounding);
assert.deepEqual([...oddRounding], [3,3,0,255], 'odd code sum rounds half up');

// A cut is black termination at the same normalized impedance; cuts precede a join.
const cutThenJoin = encoder.create({cutMask:1,pair:[1,0]});
const cutFrame = new Uint8Array([255,64,10,7, 80,255,31,9]);
cutThenJoin.apply(cutFrame);
assert.deepEqual([...cutFrame], [32,32,10,7, 128,128,31,9]);
const allCut = encoder.create({cutMask:7,pair:null});
const allCutPixels = new Uint8Array([1,2,3,4, 255,128,64,5]);
allCut.apply(allCutPixels);
assert.deepEqual([...allCutPixels], [0,0,0,4, 0,0,0,5]);
const cutMaskLiterals = [
  [3,120,255,87], [0,120,255,87], [3,0,255,87], [0,0,255,87],
  [3,120,0,87], [0,120,0,87], [3,0,0,87], [0,0,0,87]
];
for (let mask=0; mask<8; mask++)
  assert.deepEqual([...encoder.create({cutMask:mask,pair:null}).apply(new Uint8Array([3,120,255,87]))], cutMaskLiterals[mask]);

// Exhaust all 65,536 source-code pairs for every bridge and cut-mask combination.
for (const pair of pairCases) {
  const [a,b]=pair, third=3-a-b;
  const input=new Uint8Array(256*256*4);
  for (let x=0; x<256; x++) for (let y=0; y<256; y++) {
    const i=(x*256+y)*4;
    input[i+a]=x;input[i+b]=y;input[i+third]=173;input[i+3]=(x+y)&255;
  }
  for (let mask=0; mask<8; mask++) {
    const output=clone(input);
    const plan=encoder.create({cutMask:mask,pair});
    assert.equal(plan.active,true);
    plan.apply(output);
    for (let x=0; x<256; x++) for (let y=0; y<256; y++) {
      const i=(x*256+y)*4;
      const sourceA=mask&(1<<a)?0:x, sourceB=mask&(1<<b)?0:y;
      const joined=output[i+a];
      if (joined!==output[i+b] || joined<Math.min(sourceA,sourceB) || joined>Math.max(sourceA,sourceB) ||
          Math.abs(2*joined-sourceA-sourceB)>1 || output[i+third]!==((mask&(1<<third))?0:173) ||
          output[i+3]!==input[i+3])
        assert.fail(`pair ${pair}, mask ${mask}, input ${x}/${y} violates join invariants`);
    }
  }
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
