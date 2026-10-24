'use strict';
const assert = require('node:assert/strict');
const {parse, validate, format, version} = require('../site/circuit-config.js');

const audio = (pair=null, dataMask=0) => ({pair,dataMask});
const valid = {
  format, schemaVersion: version,
  configuration: {
    vram: {modelId: 2, mask: 0, pair: [0, 1]}, ram: null,
    psg: audio([0, 7]), fm: audio([1, 6])
  }
};
assert.deepEqual(parse(JSON.stringify(valid)), valid);

const legacyV1 = {
  format, schemaVersion: 1,
  configuration: {vram:{modelId:1,mask:0,pair:null},ram:null,psg:[7,0],fm:null}
};
assert.deepEqual(parse(JSON.stringify(legacyV1)), {
  format, schemaVersion: 2,
  configuration: {vram:{modelId:1,mask:0,pair:null},ram:null,
    psg:audio([0,7]),fm:audio()}
});

const audioMasks = structuredClone(valid);
audioMasks.configuration.psg = audio(null, 0x81);
audioMasks.configuration.fm = audio(null, 0x42);
assert.deepEqual(validate(audioMasks).configuration.psg, audio(null,0x81));
assert.deepEqual(validate(audioMasks).configuration.fm, audio(null,0x42));

const addressMask = structuredClone(valid);
addressMask.configuration.vram = {modelId: 1, mask: 0, pair: null};
addressMask.configuration.ram = {type: 'address-mask', mask: 0x101, access: 3};
assert.deepEqual(validate(addressMask).configuration.ram, addressMask.configuration.ram);

const linePair = structuredClone(valid);
linePair.configuration.vram = {modelId: 1, mask: 0, pair: null};
linePair.configuration.ram = {type: 'line-pair', kind: 2, access: 1, a: 1, b: 7};
assert.deepEqual(validate(linePair).configuration.ram, linePair.configuration.ram);

const reversedPairs = structuredClone(valid);
reversedPairs.configuration.vram = {modelId: 1, mask: 0, pair: [5, 2]};
reversedPairs.configuration.psg = audio([7, 0]);
reversedPairs.configuration.fm = audio([6, 1]);
assert.deepEqual(validate(reversedPairs).configuration, {
  vram: {modelId: 1, mask: 0, pair: [2, 5]}, ram: null,
  psg: audio([0,7]), fm: audio([1,6])
});

const reversedRam = structuredClone(linePair);
reversedRam.configuration.ram = {type: 'line-pair', kind: 2, access: 3, a: 7, b: 1};
assert.deepEqual(validate(reversedRam).configuration.ram,
  {type: 'line-pair', kind: 2, access: 3, a: 1, b: 7});

const invalid = [];
invalid.push({...valid, extra: true});
invalid.push({...valid, schemaVersion: 1});
invalid.push({...valid, configuration: {...valid.configuration, logic: null}});
invalid.push({...valid, configuration: {...valid.configuration,
  vram: {...valid.configuration.vram, mask: -1}}});
invalid.push({...valid, configuration: {...valid.configuration,
  vram: {...valid.configuration.vram, mask: 1}}});
invalid.push({...valid, configuration: {...valid.configuration, ram: {
  type: 'line-pair', kind: 2, access: 1, a: 7, b: 8
}}});
invalid.push({...valid, configuration: {...valid.configuration, ram: {
  type: 'line-pair', kind: 1, access: 1, a: 1, b: 1
}}});
invalid.push({...valid, configuration: {...valid.configuration, ram: {
  type: 'address-mask', mask: 0, access: 1
}}});
invalid.push({...valid, configuration: {...valid.configuration, ram: {
  type: 'line-pair', kind: 1, access: 1, a: 0, b: 15
}}});
invalid.push({...valid, configuration: {...valid.configuration, psg: audio([0,8])}});
invalid.push({...valid, configuration: {...valid.configuration, fm: audio([3,3])}});
invalid.push({...valid, configuration: {...valid.configuration, psg: audio(null,-1)}});
invalid.push({...valid, configuration: {...valid.configuration, fm: audio(null,256)}});
invalid.push({...valid, configuration: {...valid.configuration, psg: audio([0,1],1)}});
invalid.push({...valid, configuration: {...valid.configuration,
  vram: {modelId: 1, mask: 0x40, pair: null},
  ram: {type: 'address-mask', mask: 1, access: 1}
}});
for (const value of invalid) assert.throws(() => validate(value));

const invalidLegacy={...legacyV1,configuration:{...legacyV1.configuration,psg:[0,0]}};
assert.throws(()=>parse(JSON.stringify(invalidLegacy)));
for (const text of ['', '{', '[]', 'null', ' '.repeat(32769)]) assert.throws(() => parse(text));
console.log('Circuit configuration schema v2 validates masks and imports legacy v1 settings.');
