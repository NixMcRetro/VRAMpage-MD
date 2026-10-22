'use strict';
const assert = require('node:assert/strict');
const {differenceCount, runTrial, sweep} = require('../scripts/sweep-ram-pulses.cjs');
const settings = {activationFrame:2, pulseFrames:2, observeFrames:4, sampleEvery:2};
const rom = new Uint8Array([1,2,3,4]); // Original protocol fixture, not an executable cartridge.
function fixture({reject=false, seed=0, staticPicture=false} = {}) {
  const heap = new Uint8Array(2_000_000), events = [];
  let frame=0, active=false, writes=0, flags=0;
  const ram=1_300_000;
  const core = {
    HEAPU8:heap, events,
    _init() {}, _start() {heap[ram+2]=seed;},
    _get_rom_buffer_ref:()=>1_400_000, _get_input_buffer_ref:()=>1_500_000,
    _get_frame_buffer_ref:()=>0, _get_web_audio_l_ref:()=>1_510_000,
    _get_web_audio_r_ref:()=>1_520_000, _get_logic_ram_ref:()=>ram,
    _get_logic_frame:()=>frame, _get_logic_cpu_flags:()=>flags,
    _get_logic_reads:()=>0, _get_logic_writes:()=>writes,
    _wasm_input_update() {assert.ok(new Float32Array(heap.buffer,1_500_000,32).every(v=>v===0));},
    _set_logic_fault(kind,access,a,b) {
      events.push(['apply',frame,kind,access,a,b]);
      if(reject) return 5;
      active=true;writes=0;return 0;
    },
    _tick() {
      frame++;heap[ram]=frame;
      if(!staticPicture) heap[0]=frame;
      events.push(['tick',frame,active]);
      if(active) {heap[ram+1]=77;writes++;flags=2;}
    },
    _sound() {events.push(['sound',frame]);return 0;},
    _recover_logic_cpu(mode) {events.push(['recover',frame,mode]);active=false;flags=0;return 0;}
  };
  return core;
}
(async()=>{
  let tests=0;
  assert.equal(differenceCount(Buffer.from([1,2,3]),Buffer.from([1,4,5])),2);
  assert.throws(()=>differenceCount(Buffer.alloc(1),Buffer.alloc(2)));tests++;
  const core=fixture();
  const trial=await runTrial(async()=>core,rom,[0,1],settings);
  assert.deepEqual(core.events.filter(e=>e[0]==='tick'&&e[2]).map(e=>e[1]),[3,4]);
  assert.deepEqual(core.events.find(e=>e[0]==='apply'),['apply',2,1,2,0,1]);
  const recoveryIndex=core.events.findIndex(e=>e[0]==='recover');
  assert.deepEqual(core.events[recoveryIndex-1],['sound',4]);
  assert.deepEqual(core.events[recoveryIndex+1],['tick',5,false]);
  assert.deepEqual(trial.record.samples.map(s=>s.frame),[2,4,6,8]);
  assert.deepEqual(trial.record.recovery,{frame:4,action:'force-resume',status:0,
    flagsBefore:2,flagsAfter:0,ramBytesChanged:0});
  assert.equal(trial.record.samples.at(-1).writes,2);tests++;
  const result=await sweep(async()=>fixture(),rom,settings,[[0,1]]);
  assert.equal(result.baseline.repeatIdentical,true);
  assert.equal(result.results[0].repeatIdentical,true);
  assert.equal(result.results[0].comparison.contactEndRAMBytesDifferentFromBaseline,1);
  assert.equal(result.results[0].comparison.finalRAMMatchesBaseline,false);
  assert.equal(result.results[0].comparison.finalPictureMatchesBaseline,true);
  assert.equal(result.results[0].comparison.pictureChangesBetweenPostContactSamples,1);
  assert.equal(result.results[0].comparison.haltObservedAfterRecovery,false);
  assert.equal(result.baseline.recovery,null);
  assert.equal(JSON.stringify(result).includes('contactEndRAM"'),false,'Do not serialize captured RAM');
  assert.equal(JSON.stringify(result).includes('"type":"Buffer"'),false);tests++;
  let seed=0;
  const unstable=await sweep(async()=>fixture({seed:seed++}),rom,settings,[[0,1]]);
  assert.equal(unstable.baseline.repeatIdentical,false);
  assert.equal(unstable.results[0].repeatIdentical,false);
  assert.ok(unstable.results[0].repeat.samples,'Keep failed repeat evidence');tests++;
  const still=await sweep(async()=>fixture({staticPicture:true}),rom,settings,[[0,1]]);
  assert.equal(still.results[0].comparison.pictureChangesBetweenPostContactSamples,0);
  assert.equal(still.results[0].samples.at(-1).cpuFlags,0);tests++;
  for(const name of Object.keys(settings))
    await assert.rejects(runTrial(async()=>{throw Error('must not create core');},rom,[0,1],{...settings,[name]:0}),/positive/);
  await assert.rejects(runTrial(async()=>fixture(),rom,[0,0],settings),/different WA/);
  await assert.rejects(runTrial(async()=>fixture({reject:true}),rom,[0,1],settings),/Fault rejected/);
  const missing=fixture();delete missing._recover_logic_cpu;
  await assert.rejects(runTrial(async()=>missing,rom,[0,1],settings),/Core missing/);tests++;
  const failures=await sweep(async()=>fixture({reject:true}),rom,settings,[[0,1]]);
  assert.match(failures.results[0].error.message,/Fault rejected/);
  assert.equal(failures.results[0].comparison,null);
  assert.equal(failures.results[0].repeatIdentical,true);tests++;
  const badRAM=fixture();badRAM._get_logic_ram_ref=()=>NaN;
  await assert.rejects(runTrial(async()=>badRAM,rom,null,settings),/work-RAM range/);
  const badFrame=fixture();badFrame._get_frame_buffer_ref=()=>badFrame.HEAPU8.length;
  await assert.rejects(runTrial(async()=>badFrame,rom,null,settings),/framebuffer range/);
  const badAudio=fixture();badAudio._sound=()=>-1;
  await assert.rejects(runTrial(async()=>badAudio,rom,null,settings),/audio sample count/);tests++;
  console.log(`Pulse sweep protocol: ${tests} test groups passed.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
