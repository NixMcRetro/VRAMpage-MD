/* Synthetic 68000 checks for bounded VBlank wait probes. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const coreFile = path.resolve(process.argv[2]);
if (!process.argv[2]) throw new Error('Pass staged diagnostic genplus.js.');
const factory = require(coreFile);
const CPU_TARGET = 0xfff62a, LOGICAL_TARGET = 0xf62a;
const BUS_PCS = [0x202,0x20e,0x21a];
const PROBE_PCS = [0x208,0x21a];
function cartridge(addressWord=0xf62a) {
  const rom=new Uint8Array(0x10000), v=new DataView(rom.buffer);
  for(let p=0;p<0x100;p+=4)v.setUint32(p,0x300);
  v.setUint32(0,0xffff00);v.setUint32(4,0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '),0x100);rom.set(Buffer.from('VRAMPAGE WAIT PROBE TEST'),0x120);
  v.setUint32(0x1a4,rom.length-1);v.setUint32(0x1a8,0xff0000);v.setUint32(0x1ac,0xffffff);rom[0x1f0]=85;
  const words=[0x7001,0x4a38,addressWord,0x6602,0x6010,0x51c8,0xfff6,
    0x13fc,0x0000,0x00ff,addressWord,0x7001,0x60e8,
    0x13fc,0x0008,0x00ff,addressWord,0x4e72,0x2700];
  words.forEach((w,i)=>v.setUint16(0x200+i*2,w));
  [0x4e72,0x2700,0x60fe].forEach((w,i)=>v.setUint16(0x300+i*2,w));
  return rom;
}
function ioWriteCartridge() {
  const rom=cartridge(),v=new DataView(rom.buffer);
  [0x13fc,0x0000,0x00a1,0x0003,0x60fe].forEach((w,i)=>v.setUint16(0x200+i*2,w));
  return rom;
}
function events(c) {
  const rows=[];
  for(let i=0;i<c._get_waitdiag_count();i++) rows.push(Array.from({length:9},(_,f)=>c._get_waitdiag_event(i,f)));
  return rows.map(([kind,pc,known,tick,before,after,count,first,last])=>({kind,pc,known,tick,before,after,count,first,last}));
}
function configure(c,{enabled=1,start=1,end=4,busPcs=BUS_PCS,probePcs=PROBE_PCS}={}) {
  const all=[...busPcs,...Array(8-busPcs.length).fill(0)];
  const probes=[...probePcs,...Array(4-probePcs.length).fill(0)];
  return c._set_waitdiag_profile(enabled,start,end,CPU_TARGET,LOGICAL_TARGET,busPcs.length,...all,probePcs.length,...probes);
}
async function run({enabled=1,fault=false,start=1,end=4,busPcs=BUS_PCS,probePcs=PROBE_PCS,
  addressWord=0xf62a,romBytes=null,ticks=1}={}) {
  const c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});c._init();
  c.HEAPU8.set(romBytes||cartridge(addressWord),c._get_rom_buffer_ref(0x10000));c._start();
  const ram=c._get_logic_ram_ref();c.HEAPU8[ram+(LOGICAL_TARGET^1)]=1;
  assert.equal(configure(c,{enabled,start,end,busPcs,probePcs}),0);
  assert.equal(c._set_logic_write_trace_enabled(1),0);
  if(fault)assert.equal(c._arm_logic_write_pulse(1,9,10,1),0);
  new Float32Array(c.HEAPU8.buffer,c._get_input_buffer_ref(),32).fill(0);
  for(let i=0;i<ticks;i++){c._wasm_input_update();c._tick();}
  return {c,rows:events(c)};
}
function overflowCartridge() {
  const rom=cartridge(),v=new DataView(rom.buffer);
  for(let i=0;i<8;i++){
    const p=0x200+i*6;v.setUint16(p,0x0a38);v.setUint16(p+2,1);v.setUint16(p+4,0xf62a);
  }
  v.setUint16(0x230,0x60ce);return rom;
}
async function runOverflow() {
  const c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});c._init();
  c.HEAPU8.set(overflowCartridge(),c._get_rom_buffer_ref(0x10000));c._start();
  const ram=c._get_logic_ram_ref();c.HEAPU8[ram+(LOGICAL_TARGET^1)]=0;
  const pcs=Array.from({length:8},(_,i)=>0x200+i*6),probes=pcs.slice(0,4);
  assert.equal(configure(c,{start:1,end:4,busPcs:pcs,probePcs:probes}),0);
  for(let i=0;i<4;i++){new Float32Array(c.HEAPU8.buffer,c._get_input_buffer_ref(),32).fill(0);c._wasm_input_update();c._tick();}
  return c;
}
(async()=>{
  let groups=0;
  const normal=await run();
  assert.equal(normal.c._get_waitdiag_overflow(),0);assert.equal(normal.c._get_waitdiag_unexpected_pc(),0);
  assert.ok(normal.rows.some(e=>e.kind===2&&e.pc===0x202&&e.before===2&&e.count>=2),'actual target reads must capture repeated nonzero polls');groups++;
  assert.ok(normal.rows.some(e=>e.kind===3&&e.pc===0x20e&&e.before===2&&e.after===1),'clear write must move native flag nonzero to zero');groups++;
  assert.ok(normal.rows.some(e=>e.kind===3&&e.pc===0x21a&&e.before===1&&e.after===2),'next setup write must restore nonzero flag');groups++;
  assert.ok(normal.rows.some(e=>e.kind===1&&e.pc===0x208),'exit branch is a PC-start probe');groups++;
  assert.ok(normal.rows.every(e=>e.tick===1),'effective tick uses completed frame plus one at the inclusive start boundary');groups++;
  const fault=await run({fault:true});
  assert.equal(fault.c._get_logic_writes(),1);assert.equal(fault.c._get_logic_pulse_state(),2);
  assert.ok(fault.rows.some(e=>e.kind===3&&e.pc===0x20e&&e.before===2&&e.after===2),'affected clear leaves the original flag nonzero');groups++;
  assert.ok(fault.rows.some(e=>e.kind===3&&e.pc===0x20e&&e.before===2&&e.after===1),'post-release clear completes the delayed wait');groups++;
  assert.ok(fault.rows.some(e=>e.kind===3&&e.pc===0x21a&&e.before===1&&e.after===2),'execution reaches the next setup after delayed release');groups++;
  const disabled=await run({enabled:0});
  assert.equal(disabled.c._get_waitdiag_count(),0);assert.equal(disabled.c._get_waitdiag_overflow(),0);groups++;
  const outside=await run({start:5,end:6});
  assert.equal(outside.c._get_waitdiag_count(),0);groups++;
  const otherTarget=await run({addressWord:0xf62b});
  assert.equal(otherTarget.rows.some(e=>e.kind===2||e.kind===3),false);
  assert.equal(otherTarget.c._get_waitdiag_unexpected_pc(),0);groups++;
  const unauthorized=await run({busPcs:[0x202],probePcs:[]});
  assert.equal(unauthorized.c._get_waitdiag_unexpected_pc(),1);groups++;
  const unauthorizedOutside=await run({start:5,end:6,busPcs:[0x202],probePcs:[]});
  assert.equal(unauthorizedOutside.c._get_waitdiag_unexpected_pc(),0);assert.equal(unauthorizedOutside.c._get_waitdiag_count(),0);groups++;
  const ioWrite=await run({romBytes:ioWriteCartridge(),busPcs:[0x200],probePcs:[]});
  assert.equal(ioWrite.c._get_waitdiag_count(),0);assert.equal(ioWrite.c._get_waitdiag_unexpected_pc(),0);groups++;
  const unknown=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});unknown._init();
  assert.equal(configure(unknown),0);unknown._work_ram_waitdiag_bus(2,CPU_TARGET,1,0,0);
  assert.equal(unknown._get_waitdiag_event(0,1),0);assert.equal(unknown._get_waitdiag_event(0,2),0);groups++;
  const order=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});order._init();assert.equal(configure(order),0);
  order._work_ram_waitdiag_bus(2,CPU_TARGET,0,0,0);order._work_ram_waitdiag_bus(3,CPU_TARGET,0,0,1);
  order._work_ram_waitdiag_bus(2,CPU_TARGET,0,0,0);
  assert.equal(order._get_waitdiag_count(),3);assert.deepEqual([0,1,2].map(i=>order._get_waitdiag_event(i,7)),[1,2,3]);groups++;
  const overflow=await runOverflow();assert.equal(overflow._get_waitdiag_overflow(),1);groups++;
  const bad=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});bad._init();
  assert.notEqual(bad._set_waitdiag_profile(1,0,4,CPU_TARGET,LOGICAL_TARGET,0,...Array(7).fill(0),0,...Array(4).fill(0)),0);groups++;
  console.log(`VBlank wait actual WASM: ${groups} groups passed.`);
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
