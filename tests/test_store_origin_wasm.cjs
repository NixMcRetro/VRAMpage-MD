/* Synthetic 68000 store-origin checks against the private staged WASM core. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const coreFile = path.resolve(process.argv[2]);
if (!process.argv[2]) throw new Error('Pass staged diagnostic genplus.js.');
const factory = require(coreFile);
function cartridge(words) {
  const rom = new Uint8Array(0x10000), view = new DataView(rom.buffer);
  for (let offset=0; offset<0x100; offset+=4) view.setUint32(offset,0x300);
  view.setUint32(0,0xffff00); view.setUint32(4,0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '),0x100);
  rom.set(Buffer.from('VRAMPAGE STORE ORIGIN TEST'),0x120);
  view.setUint32(0x1a4,rom.length-1); view.setUint32(0x1a8,0xff0000); view.setUint32(0x1ac,0xffffff);
  rom[0x1f0]='U'.charCodeAt(0);
  words.forEach((word,i)=>view.setUint16(0x200+i*2,word));
  [0x4e72,0x2700,0x60fe].forEach((word,i)=>view.setUint16(0x300+i*2,word));
  return rom;
}
async function run(words,{trace=true,pulse=true}={}) {
  const core=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});
  core._init(); core.HEAPU8.set(cartridge(words),core._get_rom_buffer_ref(0x10000)); core._start();
  assert.equal(core._set_logic_write_trace_enabled(trace?1:0),0);
  if(pulse) assert.equal(core._arm_logic_write_pulse(1,9,10,1),0);
  new Float32Array(core.HEAPU8.buffer,core._get_input_buffer_ref(),32).fill(0);
  core._wasm_input_update(); core._tick();
  return core;
}
(async()=>{
  let cases=0;
  // MOVE.B #imm,abs.l has immediate and address extension words. PC must be opcode $200.
  let c=await run([0x13fc,0x0008,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_logic_write_trace_state(),2); assert.equal(c._get_logic_write_trace_cpu_address(),0xfff62a);
  assert.equal(c._get_logic_write_trace_mapped_offset(),0xf22a); assert.equal(c._get_logic_write_trace_width(),1);
  assert.equal(c._get_store_diag_pc(),0x200); assert.equal(c._get_store_diag_pc_known(),1); assert.equal(c._get_store_diag_value_class(),2);
  assert.equal(c._get_store_diag_width(),1); assert.equal(c._get_logic_writes(),1); cases++;
  c=await run([0x13fc,0x0000,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_store_diag_pc(),0x200); assert.equal(c._get_store_diag_pc_known(),1); assert.equal(c._get_store_diag_value_class(),1); cases++;
  // Word bus op has a nonzero low lane but zero high lane at the even target byte.
  c=await run([0x33fc,0x0001,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_logic_write_trace_width(),2); assert.equal(c._get_store_diag_value_class(),1); cases++;
  // Longword write is split into two word cycles; a one-write pulse releases after the first.
  c=await run([0x23fc,0x1122,0x3344,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_logic_write_trace_width(),2); assert.equal(c._get_store_diag_pc(),0x200);
  assert.equal(c._get_logic_writes(),1); assert.equal(c._get_logic_pulse_state(),2); cases++;
  // Branching changes the instruction address, which must still point to the opcode start.
  c=await run([0x6002,0x4e71,0x13fc,0x0008,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_store_diag_pc(),0x204); assert.equal(c._get_store_diag_value_class(),2); cases++;
  // An odd word store raises an address error; its exception-frame write has no executing opcode PC.
  c=await run([0x2e7c,0x00ff,0xf640,0x33fc,0x1234,0x00ff,0xf62b,0x4e72,0x2700]);
  assert.equal(c._get_logic_write_trace_state(),2); assert.equal(c._get_store_diag_state(),1);
  assert.equal(c._get_store_diag_pc_known(),0); assert.equal(c._get_store_diag_pc(),0); cases++;
  c=await run([0x13fc,0x0008,0x00ff,0xf62a,0x4e72,0x2700],{trace:false});
  assert.equal(c._get_logic_write_trace_state(),0); assert.equal(c._get_store_diag_state(),0); cases++;
  // A selected address line already low produces a no-op and no diagnostic record.
  c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)}); c._init();
  c.HEAPU8.set(cartridge([0x13fc,0x0055,0x00ff,0xf000,0x4e72,0x2700]),c._get_rom_buffer_ref(0x10000)); c._start();
  assert.equal(c._set_logic_write_trace_enabled(1),0); assert.equal(c._set_logic_address_mask(1,2),0);
  new Float32Array(c.HEAPU8.buffer,c._get_input_buffer_ref(),32).fill(0); c._wasm_input_update(); c._tick();
  assert.equal(c._get_logic_write_trace_state(),0); assert.equal(c._get_store_diag_state(),0); assert.equal(c._get_logic_writes(),0); cases++;
  // Re-enabling and a fresh non-clear activation erase a completed old record.
  c=await run([0x13fc,0x0008,0x00ff,0xf62a,0x4e72,0x2700]);
  assert.equal(c._get_store_diag_state(),1); assert.equal(c._set_logic_write_trace_enabled(1),0);
  assert.equal(c._get_store_diag_state(),0); assert.equal(c._set_logic_fault(1,2,9,10),0);
  assert.equal(c._get_logic_write_trace_state(),0); assert.equal(c._get_store_diag_state(),0); cases++;
  console.log(`Store-origin actual WASM CPU: ${cases} groups passed.`);
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
