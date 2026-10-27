'use strict';
const assert = require('node:assert/strict');
const {parse, validate, format, version} = require('../site/circuit-config.js');

const audio = (pair=null, dataMask=0) => ({pair,dataMask});
const valid = {
  format, schemaVersion: version,
  configuration: {
    vram: {modelId: 2, mask: 0, pair: [0, 1]}, ram: null,
    psg: audio([0, 7]), fm: audio([1, 6]), z80Ram:{pair:null},
    rgbEncoder:{cutMask:0,pair:null}
  }
};
assert.deepEqual(parse(JSON.stringify(valid)), valid);

const legacyV1 = {
  format, schemaVersion: 1,
  configuration: {vram:{modelId:1,mask:0,pair:null},ram:null,psg:[7,0],fm:null}
};
assert.deepEqual(parse(JSON.stringify(legacyV1)), {
  format, schemaVersion: version,
  configuration: {vram:{modelId:1,mask:0,pair:null},ram:null,
    psg:audio([0,7]),fm:audio(),z80Ram:{pair:null},rgbEncoder:{cutMask:0,pair:null}}
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
  psg: audio([0,7]), fm: audio([1,6]), z80Ram:{pair:null}, rgbEncoder:{cutMask:0,pair:null}
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
const legacyV2={format,schemaVersion:2,configuration:{vram:{modelId:1,mask:0,pair:null},ram:null,psg:audio(null,3),fm:audio([0,1])}};
assert.deepEqual(parse(JSON.stringify(legacyV2)).configuration,{...legacyV2.configuration,
  z80Ram:{pair:null},rgbEncoder:{cutMask:0,pair:null}});
assert.deepEqual(parse(JSON.stringify(legacyV2)).configuration.rgbEncoder,{cutMask:0,pair:null});
assert.equal(parse(JSON.stringify(legacyV2)).schemaVersion,4);
const legacyV3={format,schemaVersion:3,configuration:{...legacyV2.configuration,z80Ram:{pair:null}}};
assert.deepEqual(parse(JSON.stringify(legacyV3)).configuration.rgbEncoder,{cutMask:0,pair:null});
assert.equal(parse(JSON.stringify(legacyV3)).schemaVersion,4);
assert.throws(()=>parse(JSON.stringify({...legacyV3,configuration:{...legacyV3.configuration,rgbEncoder:{cutMask:1,pair:null}}})),/unknown fields/);
const rgb=structuredClone(valid);rgb.configuration.rgbEncoder={cutMask:3,pair:[2,0]};
assert.deepEqual(validate(rgb).configuration.rgbEncoder,{cutMask:3,pair:[0,2]});
for(const config of [{cutMask:-1,pair:null},{cutMask:8,pair:null},{cutMask:1.5,pair:null},
  {cutMask:0,pair:[0,0]},{cutMask:0,pair:[0,3]},{cutMask:0,pair:[0,1,2]},
  {cutMask:0,pair:null,extra:true}]) {
  const malformed=structuredClone(valid);malformed.configuration.rgbEncoder=config;
  assert.throws(()=>validate(malformed));
}
const z80=structuredClone(valid);z80.configuration.z80Ram.pair=[12,0];
assert.deepEqual(validate(z80).configuration.z80Ram,{pair:[0,12]});
for(const value of [[0,13],[0,0],[-1,2],[0,1.5],[],[0,1,2],'0,1']) {
  z80.configuration.z80Ram.pair=value;assert.throws(()=>validate(z80));
}
z80.configuration.z80Ram={pair:null,dataMask:1};assert.throws(()=>validate(z80));
const legacyUnknown=structuredClone(legacyV2);legacyUnknown.configuration.z80Ram={pair:[0,1]};
assert.throws(()=>parse(JSON.stringify(legacyUnknown)));
console.log('Circuit schema v4 validates RGB encoder contacts and imports v1/v2/v3 with RGB off.');
