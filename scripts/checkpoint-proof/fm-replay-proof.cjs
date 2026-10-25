'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const path = require('node:path');
const corePath = process.env.CHECKPOINT_CORE_JS;
assert.ok(corePath, 'CHECKPOINT_CORE_JS must name the isolated experimental build');
const factory = require(corePath);
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
function cartridge() {
  const rom = new Uint8Array(0x10000), v = new DataView(rom.buffer);
  for (let p=0;p<0x100;p+=4) v.setUint32(p,0x300);
  v.setUint32(0,0xffff00); v.setUint32(4,0x800);
  rom.set(Buffer.from('SEGA MEGA DRIVE '),0x100);
  rom.set(Buffer.from('VRAMPAGE ORIGINAL FM CHECKPOINT REPLAY'),0x120);
  v.setUint32(0x1a4,rom.length-1); v.setUint32(0x1a8,0xff0000); v.setUint32(0x1ac,0xffffff); rom[0x1f0]=0x55;
  const z=[]; const fm=(a,x)=>z.push(0x3e,a,0x32,0,0x40,0x3e,x,0x32,1,0x40); const psg=x=>z.push(0x3e,x,0x32,0x11,0x7f);
  fm(0x22,0); fm(0x27,0);
  for(const o of [0,4,8,12]) { fm(0x30+o,1); fm(0x50+o,0x1f); fm(0x60+o,0); fm(0x70+o,0); fm(0x80+o,0x0f); fm(0x40+o,o===12?0:0x7f); }
  fm(0xb0,7); fm(0xb4,0xc0); fm(0xa0,0x98); fm(0xa4,0x22); fm(0x28,0xf0); psg(0x8a); psg(0x10); psg(0x90); z.push(0x18,0xfe);
  const w=[]; const word=(a,x)=>w.push(0x33fc,x,a>>>16,a&0xffff); const byte=(a,x)=>w.push(0x13fc,x,a>>>16,a&0xffff);
  word(0x00a11100,0x0100); word(0x00a11200,0x0100); z.forEach((x,i)=>byte(0x00a00000+i,x)); word(0x00a11100,0); w.push(0x60fe);
  w.forEach((x,i)=>v.setUint16(0x800+2*i,x)); [0x4e72,0x2700,0x60fe].forEach((x,i)=>v.setUint16(0x300+2*i,x)); return rom;
}
async function create() {
  const c=await factory({locateFile:n=>path.join(path.dirname(corePath),n)});
  c._init(); c.HEAPU8.set(cartridge(),c._get_rom_buffer_ref(0x10000)); c._start();
  new Float32Array(c.HEAPF32.buffer,c._get_input_buffer_ref(),32).fill(0);
  assert.equal(c._state_proof_set_filter(Number(process.env.STATE_PROOF_FILTER||1)),0);
  return c;
}
function frame(c, buttons=0) {
  const input=new Float32Array(c.HEAPF32.buffer,c._get_input_buffer_ref(),32); input.fill(0); input[10]=buttons;
  c._wasm_input_update(); c._tick(); const n=c._sound();
  const fp=c._get_frame_buffer_ref()>>>2, lp=c._get_web_audio_l_ref()>>>2, rp=c._get_web_audio_r_ref()>>>2;
  const pixelBytes=Buffer.from(c.HEAPU8.subarray(c._get_frame_buffer_ref(),c._get_frame_buffer_ref()+640*480*4));
  const left=Float32Array.from(c.HEAPF32.subarray(lp,lp+n));
  const right=Float32Array.from(c.HEAPF32.subarray(rp,rp+n));
  assert.ok([...left,...right].every(Number.isFinite));
  return {count:n,pixels:digest(pixelBytes),left:digest(Buffer.from(left.buffer)),right:digest(Buffer.from(right.buffer)),nonzero:[...left,...right].some(x=>Math.abs(x)>0.0001)};
}
(async()=>{
  const c=await create();
  assert.equal(c._state_proof_reject_empty(),1,'empty slot rejects before stock loader');
  const warm=frame(c);
  assert.ok(warm.count>0); assert.ok(warm.nonzero,'synthetic cartridge must produce nonzero PCM');
  const length=c._state_proof_save();
  const audioLength=c._state_proof_audio_save();
  assert.equal(c._state_proof_audio_small_capacity_refused(),1,'zero-capacity audio save refuses without writes');
  assert.equal(c._state_proof_audio_profile_refused(),1,'mismatched audio profile is refused');
  const pointerBefore=c._state_proof_audio_pointer_fingerprint();
  assert.ok(audioLength>0&&audioLength<0x80000);
  assert.equal(c._state_proof_audio_guard_ok(),1,'audio supplement stayed within capacity');
  assert.ok(length>0&&length<0xfd000); assert.equal(c._state_proof_guard_ok(),1,'save stayed within declared payload');
  const saved=Buffer.from(c.HEAPU8.subarray(c._state_proof_payload_ref(),c._state_proof_payload_ref()+length));
  const first=[]; for(let i=0;i<6;i++) first.push(frame(c,i&1));
  const fresh=await create(); frame(fresh); const freshContinuation=[]; for(let i=0;i<6;i++) freshContinuation.push(frame(fresh,i&1));
  const mutationHash=digest(Buffer.from(c.HEAPU8.subarray(c._get_logic_ram_ref(),c._get_logic_ram_ref()+0x10000)));
  assert.equal(c._state_proof_load(),length,'native loader reports consumed serialized length');
  assert.equal(c._state_proof_audio_load(),audioLength,'scratch audio supplement restores same-instance runtime state');
  assert.equal(c._state_proof_audio_pointer_fingerprint(),pointerBefore,'restore preserves live Blip and ring allocations');
  const restoredLength=c._state_proof_save(); assert.equal(restoredLength,length);
  const restored=Buffer.from(c.HEAPU8.subarray(c._state_proof_payload_ref(),c._state_proof_payload_ref()+length));
  const stateRoundTripEqual=saved.equals(restored);
  const second=[]; for(let i=0;i<6;i++) second.push(frame(c,i&1));
  const replayEqual=JSON.stringify(first)===JSON.stringify(second);
  assert.equal(stateRoundTripEqual,true,'native serialized state reserializes identically');
  assert.equal(replayEqual,true,'restored continuation matches samples and pixels');
  assert.equal(JSON.stringify(first),JSON.stringify(freshContinuation),'fresh same-build run is deterministic');
  assert.equal(c._state_proof_guard_ok(),1);
  const result={core:'6090aff9e9b2f578cd28882bd4571d2e35b1d674 plus repository-supported runtime patch',filterMode:Number(process.env.STATE_PROOF_FILTER||1),stateLength:length,audioSupplementLength:audioLength,stateCapacity:0xfd000,audioSupplementCapacity:0x80000,capacityGuardPassed:true,nonzeroWarmPcm:warm.nonzero,warmSamples:warm.count,savedStateReserializationEqual:stateRoundTripEqual,continuationReplayEqual:replayEqual,freshContinuationEqual:JSON.stringify(first)===JSON.stringify(freshContinuation),firstContinuation:first,secondContinuation:second,mutatedRamDigest:mutationHash};
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
