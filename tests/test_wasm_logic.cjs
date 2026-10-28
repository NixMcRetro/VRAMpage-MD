/* Original miniature 68000 programs. No commercial ROM or game-derived data.
 * Run after building the actual core: node tests/test_wasm_logic.cjs site/core/genplus.js
 */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const coreFile = path.resolve(process.argv[2] || 'site/core/genplus.js');
const factory = require(coreFile);

function cartridge(words, codeStart=0x200) {
  const rom = new Uint8Array(0x10000);
  const view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00);
  view.setUint32(4, codeStart);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  rom.set(Buffer.from('VRAMPAGE ORIGINAL MEMORY TEST'), 0x120);
  view.setUint32(0x1a0, 0);
  view.setUint32(0x1a4, rom.length - 1);
  view.setUint32(0x1a8, 0xff0000);
  view.setUint32(0x1ac, 0xffffff);
  rom[0x1f0] = 'U'.charCodeAt(0);
  words.forEach((word, i) => view.setUint16(codeStart + 2 * i, word));
  // Exception handler stops without rescuing or masking the failing test.
  [0x4e72, 0x2700, 0x60fe].forEach((word, i) => view.setUint16(0x300 + 2 * i, word));
  return rom;
}
function bankedZ80StoreCartridge() {
  const z80=[];
  const ldImmediateStore=(address,value)=>z80.push(0x3e,value,0x32,address&0xff,address>>>8);
  // The Z80 shifts bank-register bits into bit 23; LSB-first serial value 510
  // maps its 15-bit window to $FF0000. Stores at $9000/$9001 then hit $FF1000/1.
  for(const bit of [0,1,1,1,1,1,1,1,1]) ldImmediateStore(0x6000,bit);
  ldImmediateStore(0x1234,0x77); // local 8 KiB Z80 RAM must remain independent
  ldImmediateStore(0x9000,0x55);
  ldImmediateStore(0x9001,0x66);
  z80.push(0x76);
  const words=[...wordWrite(0xa11100,0x0100),...wordWrite(0xa11200,0x0100)];
  for(let i=0;i<z80.length;i++) words.push(...byteWrite(0xa00000+i,z80[i]));
  words.push(...wordWrite(0xa11100,0),0x60fe);
  return cartridge(words,0x2000);
}
const wordWrite = (a,v) => [0x33fc,v,a>>>16,a&0xffff];
const byteWrite = (a,v) => [0x13fc,v,a>>>16,a&0xffff];
const longWrite = (a,v) => [0x23fc,v>>>16,v&0xffff,a>>>16,a&0xffff];
const stop = [0x4e72,0x2700];
const getWord = (c,a) => new DataView(c.HEAPU8.buffer).getUint16(c._get_logic_ram_ref()+a,true);
const putWord = (c,a,v) => new DataView(c.HEAPU8.buffer).setUint16(c._get_logic_ram_ref()+a,v,true);
const getByte = (c,a) => c.HEAPU8[c._get_logic_ram_ref()+(a^1)];

async function create(words, config, init, dataMaskConfig, inhibitMask) {
  const c = await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});
  c._init();
  assert.equal(typeof c._set_logic_fault, 'function', 'Rebuild the logic-capable core');
  const rom = cartridge(words);
  c.HEAPU8.set(rom,c._get_rom_buffer_ref(rom.length));
  c._start();
  if(init) init(c);
  if(config) assert.equal(c._set_logic_fault(...config),0);
  if(dataMaskConfig) assert.equal(c._set_logic_data_mask(...dataMaskConfig),0);
  if(inhibitMask !== undefined) assert.equal(c._set_logic_write_inhibit(inhibitMask),0);
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
  assert.equal(c._get_logic_write_trace_state(),0,'trace is disabled by default');tests++;
  assert.equal(c._get_logic_cpu_flags(),1);tests++;

  // Real CPU stores retain prior bytes on selected lanes; reads stay ordinary.
  c=await create([
    ...wordWrite(0xff1000,0x1122),...wordWrite(0xff1002,0x1122),
    ...longWrite(0xff1004,0x11223344),...byteWrite(0xff1008,0x11),...byteWrite(0xff1009,0x22),
    0x3039,0x00ff,0x1000,0x33c0,0x00ff,0x1010,...stop
  ],null,core=>{putWord(core,0x1000,0xaabb);putWord(core,0x1002,0xaabb);
    putWord(core,0x1004,0xaabb);putWord(core,0x1006,0xccdd);putWord(core,0x1008,0xaabb);
    putWord(core,0x1010,0xaabb);},null,1);
  assert.equal(c._get_logic_write_inhibit(),1);
  assert.equal(getWord(c,0x1000),0x11bb);
  assert.equal(getWord(c,0x1002),0x11bb);
  assert.equal(getWord(c,0x1004),0x11bb);assert.equal(getWord(c,0x1006),0x33dd);
  assert.equal(getByte(c,0x1008),0x11,'even byte address selects the uninhibited upper lane');
  assert.equal(getByte(c,0x1009),0xbb,'odd byte address retains the inhibited lower lane');
  assert.equal(getWord(c,0x1010),0x11bb,'CPU reads return stored bytes unchanged');
  assert.equal(c._get_logic_reads(),0);
  assert.equal(c._set_logic_write_inhibit(4),5);
  assert.equal(c._set_logic_write_inhibit(1.5),5);
  assert.equal(c._set_logic_write_inhibit(),5);
  assert.equal(c._get_logic_write_inhibit(),1,'invalid or malformed calls preserve active inhibit');
  assert.equal(c._set_logic_fault(1,1,0,1),0);
  assert.equal(c._get_logic_write_inhibit(),0,'accepted legacy fault replaces inhibit');
  assert.equal(c._set_logic_write_inhibit(3),0);
  assert.equal(c._recover_logic_cpu(1),0);
  assert.equal(c._get_logic_write_inhibit(),0,'CPU recovery clears inhibit');
  tests++;

  // Real Z80 code uses its serial bank register to store through the $FFxxxx
  // Work RAM window, while a separate store remains in local Z80 sound RAM.
  const z80rom=bankedZ80StoreCartridge();
  c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});c._init();
  c.HEAPU8.set(z80rom,c._get_rom_buffer_ref(z80rom.length));c._start();
  putWord(c,0x1000,0xaabb);putWord(c,0x1002,0xccdd);
  assert.equal(c._set_logic_write_inhibit(0),0);
  c._wasm_input_update();c._tick();c._sound();
  assert.equal(getWord(c,0x1000),0x5566,'baseline banked Z80 stores both selected bytes');
  assert.equal(c.HEAPU8[c._get_z80_ram_ref()+0x1234],0x77,'Z80 local RAM receives its independent marker');
  tests++;
  for(const [mask,expected,affected] of [[1,0x55bb,1],[2,0xaa66,1],[3,0xaabb,2]]) {
    c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});c._init();
    c.HEAPU8.set(z80rom,c._get_rom_buffer_ref(z80rom.length));c._start();
    putWord(c,0x1000,0xaabb);putWord(c,0x1002,0xccdd);
    assert.equal(c._set_logic_write_inhibit(mask),0);
    c._wasm_input_update();c._tick();c._sound();
    assert.equal(getWord(c,0x1000),expected,`banked Z80 write honors inhibit mask ${mask}`);
    assert.equal(c._get_logic_writes(),affected,`one affected transaction per retained Z80 byte for mask ${mask}`);
    assert.equal(c.HEAPU8[c._get_z80_ram_ref()+0x1234],0x77,'local Z80 RAM remains outside Work RAM inhibit');
    tests++;
  }

  // Independent byte lanes affect byte, word and both halves of longword CPU stores.
  c=await create([
    ...wordWrite(0xff1000,0xffff),...byteWrite(0xff1002,0xff),
    ...byteWrite(0xff1003,0xff),...longWrite(0xff1004,0xffffffff),
    ...wordWrite(0xe01008,0xffff),...stop
  ],null,null,[0x8085,2]);
  assert.equal(c._get_logic_data_mask(),0x8085);
  assert.equal(getWord(c,0x1000),0x7f7a);
  assert.equal(getWord(c,0x1002),0x7f7a);
  assert.equal(getWord(c,0x1004),0x7f7a);assert.equal(getWord(c,0x1006),0x7f7a);
  assert.equal(getWord(c,0x1008),0x7f7a,'E0 and FF Work RAM windows share the same lane fault');
  assert.equal(c._get_logic_writes(),6);
  assert.equal(c._set_logic_fault(1,1,0,1),0);
  assert.equal(c._get_logic_data_mask(),0,'legacy address configuration replaces the data mask');
  tests++;

  // Read-only cuts project CPU data while preserving backing RAM and writes.
  c=await create([
    0x3039,0x00ff,0x1000,0x33c0,0x00ff,0x1010,...stop
  ],null,core=>putWord(core,0x1000,0xffff),[0x8085,1]);
  assert.equal(getWord(c,0x1000),0xffff);
  assert.equal(getWord(c,0x1010),0x7f7a);
  assert.equal(c._get_logic_reads(),1);assert.equal(c._get_logic_writes(),0);
  assert.equal(c._set_logic_data_mask(0x10000,1),5);
  assert.equal(c._get_logic_data_mask(),0x8085,'invalid native range leaves the active mask unchanged');
  assert.equal(c._recover_logic_cpu(1),0);
  assert.equal(c._get_logic_data_mask(),0,'CPU recovery disconnects the data mask');
  assert.equal(c._set_logic_data_mask(0x0080,3),0);
  c._start();
  assert.equal(c._get_logic_data_mask(),0,'Clean Restart disconnects the data mask');
  tests++;

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
  c=await create([
    ...wordWrite(0xff1000,0x0002),...wordWrite(0xc00004,0x8114),
    ...wordWrite(0xc00004,0x8f02),...wordWrite(0xc00004,0x9301),
    ...wordWrite(0xc00004,0x9400),...wordWrite(0xc00004,0x9500),
    ...wordWrite(0xc00004,0x9688),...wordWrite(0xc00004,0x977f),
    ...longWrite(0xc00004,0x40000080),...longWrite(0xc00004,0),
    0x3039,0x00c0,0x0000,0x33c0,0x00ff,0x1010,...stop
  ],null,null,[0x0002,1]);
  assert.equal(getWord(c,0x1010),0,'VDP DMA reads the configured Work RAM data lane');
  assert.equal(getWord(c,0x1000),2,'read-side DMA fault preserves Work RAM');
  assert.ok(c._get_logic_reads()>0);tests++;
  // A fresh cartridge load clears the fault, counters, and frame metadata.
  c._start();assert.equal(c._get_logic_reads(),0);assert.equal(c._get_logic_writes(),0);
  assert.equal(c._get_logic_frame(),0);assert.equal(c._get_logic_activation_frame(),0);tests++;
  // Forced resume clears STOP and continues at the existing PC without rewriting RAM.
  c=await create([...stop,...wordWrite(0xff1100,0x5678),...stop]);
  putWord(c,0x1200,0xbeef);
  assert.equal(c._get_logic_cpu_flags(),1);
  assert.equal(c._set_logic_fault(2,1,0,1),0);
  const frameBefore=c._get_logic_frame();
  assert.equal(c._recover_logic_cpu(99),5);
  assert.equal(c._get_logic_cpu_flags(),1);
  assert.equal(c._recover_logic_cpu(1),0);
  assert.equal(c._get_logic_cpu_flags(),0);
  assert.equal(c._get_logic_frame(),frameBefore);
  assert.equal(getWord(c,0x1200),0xbeef);
  c._tick();c._sound();
  assert.equal(getWord(c,0x1100),0x5678,'resume executes after STOP, with data fault disconnected');
  assert.equal(c._get_logic_reads(),0);tests++;

  // CPU-only reset rereads the cartridge vectors; no system/RAM reset occurs.
  c=await create([0x5279,0x00ff,0x1000,...stop]); // ADDQ.W #1,($ff1000)
  assert.equal(getWord(c,0x1000),1);
  const before=Buffer.from(c.HEAPU8.subarray(c._get_logic_ram_ref(),c._get_logic_ram_ref()+65536));
  assert.equal(c._recover_logic_cpu(2),0);
  assert.equal(c._get_logic_cpu_flags(),0);
  assert.deepEqual(Buffer.from(c.HEAPU8.subarray(c._get_logic_ram_ref(),c._get_logic_ram_ref()+65536)),before);
  c._tick();c._sound();assert.equal(getWord(c,0x1000),2,'reset executes entry point again');tests++;

  // Odd stack + odd word read causes a real nested address error and HALT.
  c=await create([0x2e7c,0x0000,0x0001,0x3039,0x00ff,0x0001,...stop]);
  assert.ok(c._get_logic_cpu_flags() & 2,'nested address error sets HALT (STOP may also remain set)');
  assert.equal(c._recover_logic_cpu(1),0);
  assert.equal(c._get_logic_cpu_flags(),0);
  // This only proves release of HALT, not successful game recovery.
  assert.equal(c._recover_logic_cpu(2),0);tests++;
  // Regression: both longword halves must traverse the ordinary write-fault hook.
  c=await create([...longWrite(0xff0004,0x11223344),...stop],[1,2,1,2]);
  assert.equal(getWord(c,0),0x1122);assert.equal(getWord(c,2),0x3344);
  assert.equal(getWord(c,4),0);assert.equal(getWord(c,6),0);
  assert.equal(c._get_logic_writes(),2);tests++;
  // The first longword half consumes the budget; the second must use normal RAM.
  c=await create([...longWrite(0xff0004,0x11223344),...wordWrite(0xff0008,0x5566),...stop],null,c=>{
    assert.equal(c._set_logic_write_trace_enabled(1),0);
    assert.equal(c._arm_logic_write_pulse(1,1,2,1),0);
  });
  assert.equal(getWord(c,0),0x1122);assert.equal(getWord(c,2),0);
  assert.equal(getWord(c,4),0);assert.equal(getWord(c,6),0x3344);
  assert.equal(getWord(c,8),0x5566);assert.equal(c._get_logic_writes(),1);
  assert.equal(c._get_logic_write_trace_state(),2);
  assert.equal(c._get_logic_write_trace_cpu_address(),0xff0004);
  assert.equal(c._get_logic_write_trace_ram_offset(),4);
  assert.equal(c._get_logic_write_trace_mapped_offset(),0);
  assert.equal(c._get_logic_write_trace_width(),2);
  assert.equal(c._get_logic_write_trace_reason(),1);
  assert.equal(c._get_logic_pulse_state(),2);tests++;

  // Byte writes report the CPU address and logical offsets, with data-only cause.
  c=await create([...byteWrite(0xff1001,0x01),...stop],null,c=>{
    assert.equal(c._set_logic_write_trace_enabled(1),0);
    assert.equal(c._arm_logic_write_pulse(2,0,1,1),0);
  });
  assert.equal(c._get_logic_write_trace_state(),2);
  assert.equal(c._get_logic_write_trace_cpu_address(),0xff1001);
  assert.equal(c._get_logic_write_trace_ram_offset(),0x1001);
  assert.equal(c._get_logic_write_trace_mapped_offset(),0x1001);
  assert.equal(c._get_logic_write_trace_width(),1);
  assert.equal(c._get_logic_write_trace_reason(),2);
  assert.equal(c._get_logic_writes(),1);tests++;

  // Unaffected lanes/values do not consume a data budget; subsequent writes stay normal.
  c=await create([
    ...byteWrite(0xff1000,1),...byteWrite(0xff1001,3),
    ...byteWrite(0xff1003,1),...byteWrite(0xff1005,2),...stop
  ],null,c=>assert.equal(c._arm_logic_write_pulse(2,0,1,1),0));
  assert.equal(getWord(c,0x1000),0x0103);assert.equal(getByte(c,0x1003),0);
  assert.equal(getByte(c,0x1005),2);assert.equal(c._get_logic_writes(),1);
  assert.equal(c._get_logic_reads(),0);assert.equal(c._get_logic_pulse_state(),2);tests++;

  // No selected access means a zero-effect timeout, not an indefinitely armed fault.
  c=await create(stop,null,c=>assert.equal(c._arm_logic_write_pulse(1,0,1,1),0));
  assert.equal(c._get_logic_writes(),0);assert.equal(c._get_logic_pulse_state(),3);
  assert.equal(c._get_logic_cpu_flags(),1);tests++;

  // A partially used budget expires as a frame limit and preserves its write count.
  c=await create([...wordWrite(0xff0004,0x1234),...stop],null,c=>{
    assert.equal(c._arm_logic_write_pulse(1,0,1,4),0);
    assert.equal(c._arm_logic_write_pulse(1,0,1,0),5);
    assert.equal(c._get_logic_pulse_state(),1);
  });
  assert.equal(getWord(c,0),0x1234);assert.equal(c._get_logic_writes(),1);
  assert.equal(c._get_logic_pulse_state(),3);
  assert.equal(c._recover_logic_cpu(1),0);assert.equal(c._get_logic_pulse_state(),3);tests++;

  assert.equal(c._arm_logic_write_pulse(1,0,1,1),0);
  c._start();assert.equal(c._get_logic_pulse_state(),0);
  c._tick();c._sound();assert.equal(getWord(c,4),0x1234);
  assert.equal(c._get_logic_writes(),0);tests++;
  // One line stuck low aliases reads, preserves source RAM and both byte lanes.
  c=await create([
    0x3039,0x00ff,0x1002,0x33c0,0x00ff,0x1010,...stop
  ],null,c=>{putWord(c,0x1000,0x1234);putWord(c,0x1002,0xabcd);
    assert.equal(c._set_logic_address_mask(1,1),0);});
  assert.equal(getWord(c,0x1010),0x1234);assert.equal(getWord(c,0x1002),0xabcd);
  assert.equal(c._get_logic_address_mask(),1);tests++;
  // Multiple disabled lines redirect a real longword write; disconnect preserves it.
  c=await create([...longWrite(0xff0004,0x11223344),...stop],null,c=>{
    assert.equal(c._set_logic_address_mask(6,2),0);
  });
  assert.equal(getWord(c,0),0x1122);assert.equal(getWord(c,2),0x3344);
  assert.equal(getWord(c,4),0);assert.equal(c._get_logic_writes(),2);
  assert.equal(c._set_logic_address_mask(0x8000,3),5);
  assert.equal(c._get_logic_address_mask(),6);
  assert.equal(c._recover_logic_cpu(1),0);assert.equal(c._get_logic_address_mask(),0);
  assert.equal(getWord(c,0),0x1122);tests++;
  c=await create([
    ...byteWrite(0xff0002,0x56),...byteWrite(0xff0003,0x78),...stop
  ],null,c=>assert.equal(c._set_logic_address_mask(1,2),0));
  assert.equal(getWord(c,0),0x5678);assert.equal(getWord(c,2),0);
  c._start();assert.equal(c._get_logic_address_mask(),0);tests++;
  // VRAM masks use the compiled frame projection, not work-RAM fault hooks.
  c=await create(stop,null,c=>{
    assert.equal(c._set_vram_address_mask(0x81),0);
    assert.equal(c._get_vram_address_mask(),0x81);
    assert.equal(c._get_vram_short_a(),-1);
    assert.equal(c._set_vram_address_mask(-1),1);
    assert.equal(c._set_vram_address_mask(256),1);
    assert.equal(c._get_vram_address_mask(),0x81);
  });
  c._set_vram_short(2,7);
  assert.equal(c._get_vram_address_mask(),0);
  assert.equal(c._get_vram_short_a(),2);
  assert.equal(c._set_vram_address_mask(256),1);
  assert.equal(c._get_vram_short_a(),2);
  assert.equal(c._set_vram_address_mask(2),0);
  assert.equal(c._get_vram_short_a(),-1);
  c._start();
  assert.equal(c._get_vram_address_mask(),0);
  assert.equal(c._get_vram_short_a(),-1);
  assert.equal(c._get_vram_changed_reads(),0);
  assert.equal(c._get_vram_changed_writes(),0);tests++;

  // Original 68000 cartridge writes VRAM at logical byte address 8. AD1 low
  // clears row A3, so the frame's changed bytes reconcile to physical address 0.
  // Resume after removing the mask, then read through the real VDP data port.
  c=await create([
    ...wordWrite(0xc00004,0x8004),...wordWrite(0xc00004,0x8144),
    ...wordWrite(0xc00004,0x8f02),...longWrite(0xc00004,0x40080000),
    ...wordWrite(0xc00000,0xccdd),...stop,
    ...longWrite(0xc00004,0),0x3039,0x00c0,0x0000,0x33c0,0x00ff,0x1100,
    ...longWrite(0xc00004,0x00080000),0x3039,0x00c0,0x0000,0x33c0,0x00ff,0x1102,
    ...stop
  ],null,c=>assert.equal(c._set_vram_address_mask(2),0));
  assert.equal(c._get_vram_changed_writes(),2);
  assert.equal(c._set_vram_address_mask(0),0);
  assert.equal(c._recover_logic_cpu(1),0);
  c._tick();c._sound();
  assert.equal(getWord(c,0x1100),0xccdd,'reconciled VRAM write persists after reconnect');
  assert.equal(getWord(c,0x1102),0,'unmapped physical VRAM source remains unchanged');
  assert.equal(c._get_vram_address_mask(),0);tests++;
  console.log(`Actual WASM logic integration: ${tests} original 68000 cartridge checks passed.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
