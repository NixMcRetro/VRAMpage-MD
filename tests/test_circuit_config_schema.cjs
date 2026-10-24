'use strict';
const assert = require('node:assert/strict');
const {parse, validate, format, version} = require('../site/circuit-config.js');

const valid = {
  format,
  schemaVersion: version,
  configuration: {
    vram: {modelId: 2, mask: 0, pair: [0, 1]},
    ram: null,
    psg: [0, 7],
    fm: [1, 6]
  }
};
assert.deepEqual(parse(JSON.stringify(valid)), valid);

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
reversedPairs.configuration.psg = [7, 0];
reversedPairs.configuration.fm = [6, 1];
assert.deepEqual(validate(reversedPairs).configuration, {
  vram: {modelId: 1, mask: 0, pair: [2, 5]},
  ram: null,
  psg: [0, 7], fm: [1, 6]
});

const reversedRam = structuredClone(linePair);
reversedRam.configuration.ram = {type: 'line-pair', kind: 2, access: 3, a: 7, b: 1};
assert.deepEqual(validate(reversedRam).configuration.ram,
  {type: 'line-pair', kind: 2, access: 3, a: 1, b: 7});

const invalid = [];
invalid.push({...valid, extra: true});
invalid.push({...valid, schemaVersion: 2});
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
invalid.push({...valid, configuration: {...valid.configuration, psg: [0, 8]}});
invalid.push({...valid, configuration: {...valid.configuration, fm: [3, 3]}});
invalid.push({...valid, configuration: {...valid.configuration,
  vram: {modelId: 1, mask: 0x40, pair: null},
  ram: {type: 'address-mask', mask: 1, access: 1}
}});

for (const value of invalid) assert.throws(() => validate(value));
for (const text of ['', '{', '[]', 'null', ' '.repeat(32769)])
  assert.throws(() => parse(text));

console.log('Circuit configuration schema accepts supported shapes and rejects malformed/conflicting files.');
