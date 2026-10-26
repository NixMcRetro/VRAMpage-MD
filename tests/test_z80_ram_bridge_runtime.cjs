'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const [runtimeArg, normalArg] = process.argv.slice(2);
const runtimePath = runtimeArg ? path.resolve(runtimeArg) : null;
const normalPath = normalArg ? path.resolve(normalArg) : null;

function cartridge() {
  const rom = new Uint8Array(0x10000), view = new DataView(rom.buffer);
  for (let offset = 0; offset < 0x100; offset += 4) view.setUint32(offset, 0x300);
  view.setUint32(0, 0xffff00); view.setUint32(4, 0x200);
  rom.set(Buffer.from('SEGA MEGA DRIVE '), 0x100);
  view.setUint32(0x1a4, rom.length - 1); view.setUint32(0x1a8, 0xff0000); view.setUint32(0x1ac, 0xffffff);
  const z80 = [0x3e,0x44,0x32,0xff,0x1f, 0x3e,0x55,0x32,0xff,0x3f, 0x18,0xfe];
  const words = [], word = (a,v) => words.push(0x33fc,v,a>>>16,a&0xffff);
  const byte = (a,v) => words.push(0x13fc,v,a>>>16,a&0xffff);
  word(0xa11100,0x0100); word(0xa11200,0x0100);
  z80.forEach((v,i) => byte(0xa00000+i,v));
  word(0xa00800,0x0055); // High byte 00 is stored once; low byte is ignored.
  word(0xa11100,0x0000); words.push(0x60fe);
  words.forEach((v,i) => view.setUint16(0x200+i*2,v));
  [0x4e72,0x2700,0x60fe].forEach((v,i) => view.setUint16(0x300+i*2,v));
  return rom;
}

function z80ProgramCartridge(z80, initPsg=false, waitReset=false, initialDenied=false, deniedState2=false, deniedState1=false) {
  const rom=new Uint8Array(0x10000), view=new DataView(rom.buffer);
  for(let offset=0;offset<0x100;offset+=4)view.setUint32(offset,0x300);
  const codeStart=z80.length>32?0x2000:0x200;
  view.setUint32(0,0xffff00);view.setUint32(4,codeStart);rom.set(Buffer.from('SEGA MEGA DRIVE '),0x100);
  view.setUint32(0x1a4,rom.length-1);view.setUint32(0x1a8,0xff0000);view.setUint32(0x1ac,0xffffff);
  const words=[],word=(a,v)=>words.push(0x33fc,v,a>>>16,a&0xffff),byte=(a,v)=>words.push(0x13fc,v,a>>>16,a&0xffff);
  if(initialDenied)byte(0xa00100,0x66); // denied in zstate 0
  word(0xa11100,0x0100);if(deniedState2)byte(0xa00100,0x66); // denied in zstate 2
  word(0xa11200,0x0100);z80.forEach((v,i)=>byte(0xa00000+i,v));
  if(initPsg)for(const v of [0x8a,0x10,0x90])byte(0xc00011,v);
  word(0xa11100,0);if(deniedState1)byte(0xa00100,0x66); // denied in zstate 1
  if(waitReset) words.push(0x1039,0x00ff,0x0000,0x4a00,0x67f6,0x33fc,0x0000,0x00a1,0x1200,0x60fe);
  else words.push(0x60fe);
  words.forEach((v,i)=>view.setUint16(codeStart+i*2,v));
  [0x4e72,0x2700,0x60fe].forEach((v,i)=>view.setUint16(0x300+i*2,v));
  return rom;
}
async function createCore(file,rom) {
  const c=await require(file)({locateFile:n=>path.join(path.dirname(file),n)});c._init();
  c.HEAPU8.set(rom,c._get_rom_buffer_ref(rom.length));c._start();
  new Float32Array(c.HEAPF32.buffer,c._get_input_buffer_ref(),32).fill(0);return c;
}
function frame(c) {
  c._wasm_input_update();c._tick();const count=c._sound(),left=c._get_web_audio_l_ref()>>>2,right=c._get_web_audio_r_ref()>>>2;
  return {count,left:Float32Array.from(c.HEAPF32.subarray(left,left+count)),right:Float32Array.from(c.HEAPF32.subarray(right,right+count))};
}
function parameterCartridge() {
  const z=[0x3e,0x10,0x32,0x00,0x01,0x3e,0x1f,0x32,0x00,0x11,
    0x3a,0x00,0x01,0x32,0x00,0x05,0x32,0x11,0x7f,0x76];
  return z80ProgramCartridge(z,true);
}
function storedInstructionCartridge() {
  const z=new Uint8Array(0x107);
  z[0]=0xc3;z[1]=0x20;z[2]=0x00; // Jump to the writer at $20.
  z.set([0x3e,0x00,0x32,0x00,0x09,0xc3,0x00,0x01],0x20); // Write $0900, then fetch at $0100.
  z[0x100]=0x76; // HALT, which A11/A12 low dominance overwrites with NOP.
  z.set([0x3e,0x5a,0x32,0x00,0x05,0x76],0x101);
  return z80ProgramCartridge(z);
}
async function testSoundParameterAndCpuReset() {
  const rom=parameterCartridge(),normal=await createCore(normalPath,rom),off=await createCore(runtimePath,rom);
  let clean,offPcm;for(let i=0;i<2;i++){clean=frame(normal);offPcm=frame(off);}
  assert.equal(offPcm.count,clean.count);assert.deepEqual(offPcm.left,clean.left,'runtime-off preserves normal sound samples');
  const expected=0x10;
  const offRam=off._get_z80_ram_ref();
  assert.equal(off.HEAPU8[offRam+0x100],expected,'clean RAM stores retain the first parameter byte at $100');
  assert.equal(off.HEAPU8[offRam+0x500],expected,'mailbox records the exact clean PSG input byte');

  async function activeRepeat() {
    const c=await createCore(runtimePath,rom);
    assert.equal(c._set_z80_ram_bridge(1,11,12),0);
    const ram=c._get_z80_ram_ref();
    let pcm;for(let i=0;i<2;i++)pcm=frame(c);
    const state=c._get_z80_ram_bridge_state();
    assert.equal(c.HEAPU8[ram+0x100],0x1f,'aliased parameter store changes the literal byte read and emitted to PSG');
    assert.equal(c.HEAPU8[ram+0x500],0x1f,'mailbox records exact PSG input byte');
    assert.ok(BigInt(state.z80Writes)>0n);assert.equal(state.m68kWrites,'20','the granted 68000 uploads each byte of the Z80 program once');
    assert.ok([...pcm.left,...pcm.right].every(Number.isFinite));
    assert.notDeepEqual(pcm.left,offPcm.left,'changed PSG parameter changes measured audio');
    const damaged=c.HEAPU8.slice(ram,ram+0x1000);
    assert.equal(c._set_fm_data_bridge(1,0,7),0,'independent FM input setting can coexist');
    assert.equal(c._recover_logic_cpu(2),0,'CPU Reset succeeds');
    const resetState=c._get_z80_ram_bridge_state();
    assert.equal(resetState.configured,false);assert.equal(resetState.ramWrites,'0');
    assert.equal(c._get_fm_data_bridge_state().configured,true,'CPU Reset preserves independent FM settings');
    assert.deepEqual(c.HEAPU8.slice(ram,ram+0x1000),damaged,'CPU Reset clears contact/counters while preserving Z80 RAM synchronously');
    return {pcm,state,ram:damaged};
  }
  const first=await activeRepeat(),second=await activeRepeat();
  assert.deepEqual(first.ram,second.ram,'fresh-instance writes repeat deterministically');
  assert.deepEqual(first.pcm.left,second.pcm.left,'active PCM repeats for the same frame/store sequence');
}
async function testDeniedZ80OwnershipStates() {
  const cases=[
    ['zstate 0',z80ProgramCartridge([],false,false,true)],
    ['zstate 2',z80ProgramCartridge([],false,false,false,true)],
    ['zstate 1',z80ProgramCartridge([],false,false,false,false,true)]
  ];
  for(const [label,rom] of cases){
    const c=await createCore(runtimePath,rom);assert.equal(c._set_z80_ram_bridge(1,0,1),0);frame(c);
    const state=c._get_z80_ram_bridge_state(),ram=c._get_z80_ram_ref();
    assert.equal(state.ramWrites,'0',`${label} denies 68000 stores before the bridge`);
    assert.equal(state.m68kWrites,'0');assert.equal(c.HEAPU8[ram+0x100],0,`${label} preserves ZRAM`);
  }
}
async function testNativeZ80ResetPersistence() {
  const rom=z80ProgramCartridge([0x3e,0x33,0x32,0x01,0x01,0x18,0xfb],false,true);
  const c=await createCore(runtimePath,rom);frame(c);
  assert.equal(c._set_z80_ram_bridge(1,0,1),0);
  frame(c);
  assert.equal(c._set_fm_data_bridge(1,0,7),0);
  const ram=c._get_z80_ram_ref(),before=c._get_z80_ram_bridge_state();
  assert.ok(BigInt(before.z80Writes)>0n);assert.equal(c.HEAPU8[ram+0x100],0x33);
  const mainRam=c._get_logic_ram_ref();c.HEAPU8[mainRam+1]=1; // logical $FF0000 byte in the native LSB_FIRST work-RAM layout
  frame(c);const resetTransition=c._get_z80_ram_bridge_state();frame(c);
  const after=c._get_z80_ram_bridge_state();
  assert.equal(after.configured,true,'native Z80 RESET retains the address contact');
  assert.equal(c._get_fm_data_bridge_state().configured,true,'native Z80 RESET does not remove independent FM configuration');
  assert.ok(BigInt(resetTransition.ramWrites)>=BigInt(before.ramWrites),'a store already in flight may complete at native reset');
  assert.equal(after.ramWrites,resetTransition.ramWrites,'native Z80 RESET retains counters and stops future writes');
  assert.equal(c.HEAPU8[ram+0x100],0x33,'native Z80 RESET preserves local sound RAM');
}
async function testStoredInstructionFetch() {
  const rom=storedInstructionCartridge(),off=await createCore(runtimePath,rom),active=await createCore(runtimePath,rom);
  assert.equal(active._set_z80_ram_bridge(1,11,12),0);
  for(let i=0;i<4;i++){frame(off);frame(active);}
  const offRam=off._get_z80_ram_ref();
  assert.equal(off.HEAPU8[offRam+0x100],0x76,'original byte oracle contains HALT');
  assert.equal(off.HEAPU8[offRam+0x500],0,'unmodified HALT prevents mailbox write');

  const ram=active._get_z80_ram_ref();
  assert.equal(active.HEAPU8[ram+0x100],0,'store through $0900 aliases to the literal opcode at $0100');
  assert.equal(active.HEAPU8[ram+0x500],0x5a,'Z80 fetch observes the stored opcode and reaches mailbox code');
}

async function testCleanRestart() {
  const c=await createCore(runtimePath,cartridge());
  assert.equal(c._set_z80_ram_bridge(1,11,12),0);frame(c);
  assert.ok(BigInt(c._get_z80_ram_bridge_state().ramWrites)>0n);
  const rom=cartridge();c.HEAPU8.set(rom,c._get_rom_buffer_ref(rom.length));c._start();
  const state=c._get_z80_ram_bridge_state();
  assert.equal(state.configured,false,'Clean Restart clears the native address contact');
  assert.equal(state.ramWrites,'0','Clean Restart clears native counters');
}
async function main() {
  if (!runtimePath || !normalPath) throw new Error('Pass runtime and normal genplus.js paths.');
  const core = await require(runtimePath)({locateFile:n=>path.join(path.dirname(runtimePath),n)});
  core._init(); const rom=cartridge(); core.HEAPU8.set(rom,core._get_rom_buffer_ref(rom.length)); core._start();
  assert.equal(core._set_z80_ram_bridge(1,11,12),0);
  core._wasm_input_update(); core._tick(); core._sound();
  core._wasm_input_update(); core._tick(); core._sound();
  const state=core._get_z80_ram_bridge_state();
  assert.equal(state.configured,true); assert.equal(state.effective,true);
  assert.ok(BigInt(state.ramWrites)>0n); assert.ok(BigInt(state.z80Writes)>0n);
  assert.equal(state.m68kWrites,'13','the granted 68000 counts twelve uploaded byte stores and one word high byte');
  assert.ok(BigInt(state.changedAddresses)>=1n,'partial A11/A12 combinations are remapped');
  const base=core._get_z80_ram_ref();
  assert.equal(core.HEAPU8[base+0x1fff],0x55,'$1FFF and mirrored $3FFF reach the same last byte, with the later Z80 byte winning');
  assert.equal(core._set_z80_ram_bridge(0,-1,-1),0);
  assert.equal(core._get_z80_ram_bridge_state().ramWrites,'0','disconnect clears counters and leaves RAM inspectable');
  assert.equal(core.HEAPU8[base+0x1fff],0x55,'disconnect retains the mirrored end byte');
  console.log('Actual WASM Z80/68000 stores exercised literal Z80 RAM address-pair mapping and disconnect persistence.');
  await testSoundParameterAndCpuReset();
  await testStoredInstructionFetch();
  await testNativeZ80ResetPersistence();
  await testDeniedZ80OwnershipStates();
  await testCleanRestart();
}
if (require.main === module) main().catch(error=>{console.error(error);process.exitCode=1;});
module.exports = { z80WriteHeavyCartridge: cartridge, z80ProgramCartridge };
