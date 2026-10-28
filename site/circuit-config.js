'use strict';
(() => {
  const FORMAT = 'vrampage-md-circuit-config';
  const VERSION = 6;

  function fail(message) { throw new Error(message); }
  function object(value, label, keys) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        Object.getPrototypeOf(value) !== Object.prototype) fail(`${label} must be an object`);
    const actual = Object.keys(value).sort();
    const expected = [...keys].sort();
    if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index]))
      fail(`${label} has missing or unknown fields`);
    return value;
  }
  function integer(value, min, max, label) {
    if (!Number.isInteger(value) || value < min || value > max) fail(`${label} is out of range`);
    return value;
  }
  function pair(value, label, max=7) {
    if (!Array.isArray(value) || value.length !== 2) fail(`${label} must be a pair`);
    const a = integer(value[0], 0, max, `${label}[0]`);
    const b = integer(value[1], 0, max, `${label}[1]`);
    if (a === b) fail(`${label} inputs must be distinct`);
    return a < b ? [a, b] : [b, a];
  }
  function audioV2(value, label) {
    object(value, `${label} configuration`, ['pair', 'dataMask']);
    const bridgePair=value.pair===null?null:pair(value.pair,`${label} pair`);
    const dataMask=integer(value.dataMask,0,255,`${label} data mask`);
    if (bridgePair && dataMask) fail(`${label} pair and data mask cannot both be active`);
    return {pair:bridgePair,dataMask};
  }
  function commonConfiguration(config, allowDataMask=false, allowWriteInhibit=false) {
    const vram = object(config.vram, 'VRAM configuration', ['modelId', 'mask', 'pair']);
    const modelId = vram.modelId;
    if (modelId !== 1 && modelId !== 2) fail('VRAM model must be 1 or 2');
    const mask = integer(vram.mask, 0, 255, 'VRAM mask');
    const bridgePair = vram.pair === null ? null : pair(vram.pair, 'VRAM pair');
    if (mask && bridgePair) fail('VRAM mask and bridge pair cannot both be set');

    let ram = null;
    if (config.ram !== null) {
      const raw = config.ram;
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) fail('RAM configuration must be null or an object');
      if (raw.type === 'address-mask' || allowDataMask && raw.type==='data-mask') {
        const data=raw.type==='data-mask';
        object(raw, `RAM ${data?'data':'address'}-mask configuration`, ['type', 'mask', 'access']);
        ram = {type: raw.type, mask: integer(raw.mask, 1, data?0xffff:0x7fff, `RAM ${data?'data':'address'} mask`),
          access: integer(raw.access, 1, 3, 'RAM access')};
      } else if (allowWriteInhibit && raw.type==='write-inhibit') {
        object(raw,'RAM write-inhibit configuration',['type','mask']);
        ram={type:raw.type,mask:integer(raw.mask,1,3,'RAM write-inhibit mask')};
      } else if (raw.type === 'line-pair') {
        object(raw, 'RAM line-pair configuration', ['type', 'kind', 'access', 'a', 'b']);
        const kind = integer(raw.kind, 1, 2, 'RAM kind');
        const max = kind === 1 ? 14 : 15;
        const a = integer(raw.a, 0, max, 'RAM line A');
        const b = integer(raw.b, 0, max, 'RAM line B');
        if (a === b) fail('RAM lines must be distinct');
        if (kind === 2 && Math.floor(a / 8) !== Math.floor(b / 8))
          fail('RAM data pair must stay within one byte lane');
        ram = {type: raw.type, kind, access: integer(raw.access, 1, 3, 'RAM access'),
          a: Math.min(a, b), b: Math.max(a, b)};
      } else {
        fail(allowWriteInhibit?'RAM type must be address-mask, data-mask, write-inhibit or line-pair':allowDataMask?'RAM type must be address-mask, data-mask or line-pair':'RAM type must be address-mask or line-pair');
      }
    }
    if (ram && (mask !== 0 || bridgePair !== null))
      fail('RAM and VRAM fault domains cannot both be active');
    return {vram:{modelId,mask,pair:bridgePair},ram};
  }
  function validateCurrent(value, allowDataMask=true, allowWriteInhibit=true) {
    object(value, 'configuration file', ['format', 'schemaVersion', 'configuration']);
    if (value.format !== FORMAT) fail('Unrecognized circuit configuration format');
    if (value.schemaVersion !== VERSION) fail('Unsupported circuit configuration version');
    const config = object(value.configuration, 'configuration', ['vram', 'ram', 'psg', 'fm', 'z80Ram', 'rgbEncoder']);
    const z80Ram=object(config.z80Ram,'Z80 RAM configuration',['pair']);
    const rgb=object(config.rgbEncoder,'RGB encoder configuration',['cutMask','pair']);
    const common=commonConfiguration(config,allowDataMask,allowWriteInhibit);
    return {format:FORMAT,schemaVersion:VERSION,configuration:{...common,
      psg:audioV2(config.psg,'PSG'),fm:audioV2(config.fm,'FM'),
      z80Ram:{pair:z80Ram.pair===null?null:pair(z80Ram.pair,'Z80 RAM pair',12)},
      rgbEncoder:{cutMask:integer(rgb.cutMask,0,7,'RGB cut mask'),
        pair:rgb.pair===null?null:pair(rgb.pair,'RGB pair',2)}}};
  }
  function validateV4(value) {
    object(value,'configuration file',['format','schemaVersion','configuration']);
    if (value.schemaVersion!==4) fail('Unsupported circuit configuration version');
    return validateCurrent({...value,schemaVersion:VERSION},false,false);
  }
  function validateV5(value) {
    object(value,'configuration file',['format','schemaVersion','configuration']);
    if (value.schemaVersion!==5) fail('Unsupported circuit configuration version');
    return validateCurrent({...value,schemaVersion:VERSION},true,false);
  }
  function validateV3(value) {
    object(value,'configuration file',['format','schemaVersion','configuration']);
    if (value.format!==FORMAT || value.schemaVersion!==3) fail('Unsupported circuit configuration format or version');
    const config=object(value.configuration,'configuration',['vram','ram','psg','fm','z80Ram']);
    return validateV4({...value,schemaVersion:4,
      configuration:{...config,rgbEncoder:{cutMask:0,pair:null}}});
  }
  function validateV2(value) {
    object(value, 'configuration file', ['format', 'schemaVersion', 'configuration']);
    if (value.format !== FORMAT) fail('Unrecognized circuit configuration format');
    if (value.schemaVersion !== 2) fail('Unsupported circuit configuration version');
    const config=object(value.configuration,'configuration',['vram','ram','psg','fm']);
    return {format:FORMAT,schemaVersion:VERSION,configuration:{...commonConfiguration(config),
      psg:audioV2(config.psg,'PSG'),fm:audioV2(config.fm,'FM'),z80Ram:{pair:null},rgbEncoder:{cutMask:0,pair:null}}};
  }
  function validateV1(value) {
    object(value, 'configuration file', ['format', 'schemaVersion', 'configuration']);
    if (value.format !== FORMAT) fail('Unrecognized circuit configuration format');
    if (value.schemaVersion !== 1) fail('Unsupported circuit configuration version');
    const config = object(value.configuration, 'configuration', ['vram', 'ram', 'psg', 'fm']);
    const common=commonConfiguration(config);
    const oldPair=(raw,label)=>raw===null?{pair:null,dataMask:0}:{pair:pair(raw,`${label} pair`),dataMask:0};
    return {format:FORMAT,schemaVersion:VERSION,configuration:{...common,
      psg:oldPair(config.psg,'PSG'),fm:oldPair(config.fm,'FM'),z80Ram:{pair:null},rgbEncoder:{cutMask:0,pair:null}}};
  }
  function validate(value) { return validateCurrent(value); }
  function parse(text) {
    if (typeof text !== 'string' || text.length > 32768) fail('Circuit configuration must be at most 32 KB');
    let parsed;
    try { parsed = JSON.parse(text); }
    catch (_) { fail('File is not valid JSON'); }
    return parsed?.schemaVersion===1?validateV1(parsed):parsed?.schemaVersion===2?validateV2(parsed):
      parsed?.schemaVersion===3?validateV3(parsed):parsed?.schemaVersion===4?validateV4(parsed):
      parsed?.schemaVersion===5?validateV5(parsed):validateCurrent(parsed);
  }
  const api = {format: FORMAT, version: VERSION, validate, parse};
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof window === 'object') window.VRAMpageCircuitConfig = api;
})();
