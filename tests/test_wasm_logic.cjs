/* Original miniature 68000 programs. No commercial ROM or game-derived data.
 * Run after building the actual core: node tests/test_wasm_logic.cjs site/core/genplus.js
 */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const coreFile = path.resolve(process.argv[2] || 'site/core/genplus.js');
const factory = require(coreFile);

function cartridge(words) {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE ORIGINAL MEMORY TEST'), 0x120);
  view.setUint32(0x1a0, 0);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);
  rom[0x1f0] = 'U'.charCodeAt(0);
  words.forEach((word, i) => view.setUint16(0x200 + 2 * i, word));
  // Exception handler stops without rescuing or masking the failing test.
  [0x4e72, 0x2700, 0x60fe].forEach((word, i) => view.setUint16(0x300 + 2 * i, word));
  return rom;
}
const wordWrite = (a,v) => [0x33fc,v,a>>>16,a&0xffff];
const byteWrite = (a,v) => [0x13fc,v,a>>>16,a&0xffff];
const longWrite = (a,v) => [0x23fc,v>>>16,v&0xffff,a>>>16,a&0xffff];
const stop = [0x4e72,0x2700];
const getWord = (c,a) => new DataView(c.HEAPU8.buffer).getUint16(c._get_logic_ram_ref()+a,true);
const putWord = (c,a,v) => new DataView(c.HEAPU8.buffer).setUint16(c._get_logic_ram_ref()+a,v,true);
const getByte = (c,a) => c.HEAPU8[c._get_logic_ram_ref()+(a^1)];

async function create(words, config, init) {
  const c = await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});
  c._init();
  assert.equal(typeof c._set_logic_fault, 'function', 'Rebuild the logic-capable core');
  const rom = cartridge(words);
  c.HEAPU8.set(rom,c._get_rom_buffer_ref(rom.length));
  c._start();
  if(init) init(c);
  if(config) assert.equal(c._set_logic_fault(...config),0);
  const input=new Float32Array(c.HEAPF32.buffer,c._get_input_buffer_ref(),32);
  input.fill(0);c._wasm_input_update();c._tick();c._sound();
  assert.equal(c._get_logic_frame(),1);
  return c;
}

(async()=>{
  let tests=0;
  // Real CPU word/byte/long transfers through the actual patched memory paths.
  let c=await create([
    ...wordWrite(0xff1000,0xa55a),...byteWrite(0xff1002,0x3c),...byteWrite(0xff1003,0xc3),
    0x3039,0x00ff,0x1000,0x33c0,0x00ff,0x1010,
    0x1239,0x00ff,0x1002,0x13c1,0x00ff,0x1012,
    ...longWrite(0xff1014,0x11223344),0x2439,0x00ff,0x1014,0x23c2,0x00ff,0x1018,...stop
  ]);
  assert.equal(getWord(c,0x1000),0xa55a);assert.equal(getWord(c,0x1002),0x3cc3);
  assert.equal(getWord(c,0x1010),0xa55a);assert.equal(getByte(c,0x1012),0x3c);
  assert.equal(getWord(c,0x1018),0x1122);assert.equal(getWord(c,0x101a),0x3344);
  assert.equal(c._get_logic_reads(),0);assert.equal(c._get_logic_writes(),0);
  assert.equal(c._get_logic_cpu_flags(),1);tests++;

  c=await create([
    ...wordWrite(0xff1000,0xabcd),...wordWrite(0xff1002,0x1234),
    0x3039,0x00ff,0x1002,0x33c0,0x00ff,0x1010,
    0x1239,0x00ff,0x1003,0x13c1,0x00ff,0x1013,...stop
  ],[1,1,0,1]);
  assert.equal(getWord(c,0x1000),0xabcd);assert.equal(getWord(c,0x1002),0x1234);
  assert.equal(getWord(c,0x1010),0xabcd);assert.equal(getByte(c,0x1013),0xcd);
  assert.ok(c._get_logic_reads()>=2);assert.equal(c._get_logic_writes(),0);tests++;

  c=await create([...wordWrite(0xff1002,0x1234),...byteWrite(0xff1003,0x5a),...stop],[1,2,0,1]);
  assert.equal(getWord(c,0x1000),0x125a);assert.equal(getWord(c,0x1002),0);
  const writes=c._get_logic_writes();assert.equal(writes,2);
  assert.equal(c._set_logic_fault(0,0,-1,-1),0);assert.equal(getWord(c,0x1000),0x125a);
  assert.equal(c._get_logic_writes(),writes);tests++;

  c=await create([
    ...wordWrite(0xff1000,0x0202),
    0x1039,0x00ff,0x1000,0x13c0,0x00ff,0x1010,
    0x1239,0x00ff,0x1001,0x13c1,0x00ff,0x1011,...stop
  ],[2,1,8,9]);
  assert.equal(getWord(c,0x1000),0x0202);assert.equal(getWord(c,0x1010),0x0002);
  assert.equal(c._get_logic_reads(),1);assert.equal(c._set_logic_fault(2,3,0,8),6);tests++;

  // Read-side D4/D5 changes a RAM-fetched immediate operand; opcodes stay valid.
  c=await create([0x4ef9,0x00ff,0x2000],[2,1,4,5], c=>{
    [...wordWrite(0xff1000,0x1357),...stop].forEach((w,i)=>putWord(c,0x2000+i*2,w));
  });
  assert.equal(getWord(c,0x1000),0x1347);assert.equal(getWord(c,0x2002),0x1357);
  assert.ok(c._get_logic_reads()>0);assert.equal(c._get_logic_cpu_flags(),1);tests++;

  c=await create([0x4ef9,0x00ff,0x2000],[2,1,4,5],c=>{
    [0x303a,0x000e,0x33c0,0x00ff,0x1000,...stop].forEach((w,i)=>putWord(c,0x2000+i*2,w));
    putWord(c,0x2010,0x1357);
  });
  assert.equal(getWord(c,0x1000),0x1347);assert.equal(getWord(c,0x2010),0x1357);tests++;

  // VDP DMA reads the same faulted work-RAM bus, not an independent raw shortcut.
  for (const fault of [null,[2,1,0,1]]) {
    c=await create([
      ...wordWrite(0xff1000,0x0002),...wordWrite(0xc00004,0x8114),
      ...wordWrite(0xc00004,0x8f02),...wordWrite(0xc00004,0x9301),
      ...wordWrite(0xc00004,0x9400),...wordWrite(0xc00004,0x9500),
      ...wordWrite(0xc00004,0x9688),...wordWrite(0xc00004,0x977f),
      ...longWrite(0xc00004,0x40000080),...longWrite(0xc00004,0),
      0x3039,0x00c0,0x0000,0x33c0,0x00ff,0x1010,...stop
    ],fault);
    assert.equal(getWord(c,0x1010),fault?0:2,'VDP DMA transfer');
    assert.equal(getWord(c,0x1000),2);
    if(fault)assert.ok(c._get_logic_reads()>0);tests++;
  }
  // A fresh cartridge load clears the fault, counters, and frame metadata.
  c._start();assert.equal(c._get_logic_reads(),0);assert.equal(c._get_logic_writes(),0);
  assert.equal(c._get_logic_frame(),0);assert.equal(c._get_logic_activation_frame(),0);tests++;
  console.log(`Actual WASM logic integration: ${tests} original 68000 cartridge checks passed.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
