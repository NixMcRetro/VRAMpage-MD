'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const [baseArg,currentArg,fixtureArg,outArg]=process.argv.slice(2);
const baseline=path.resolve(baseArg),current=path.resolve(currentArg),fixture=path.resolve(fixtureArg);
const {z80ProgramCartridge}=require(fixture);
// Original Z80 program: repeatedly store A to $1000, increment A, and loop.
const rom=z80ProgramCartridge([0x3e,0x55,0x32,0x00,0x10,0x3c,0x18,0xfa]);
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const median=a=>{const s=[...a].sort((x,y)=>x-y);return s[Math.floor(s.length/2)];};
const p95=a=>[...a].sort((x,y)=>x-y)[Math.ceil(a.length*.95)-1];
const records=[];
async function run(label,file,block) {
  const core=await require(file)({locateFile:name=>path.join(path.dirname(file),name)});
  core._init();core.HEAPU8.set(rom,core._get_rom_buffer_ref(rom.length));core._start();
  new Float32Array(core.HEAPF32.buffer,core._get_input_buffer_ref(),32).fill(0);
  const tick=()=>{core._wasm_input_update();core._tick();return core._sound();};
  for(let i=0;i<100;i++)tick();
  const before=core._get_logic_frame(),samples=[];let pcmSamples=0;
  for(let i=0;i<600;i++) {
    const start=process.hrtime.bigint();pcmSamples+=tick();
    samples.push(Number(process.hrtime.bigint()-start)/1e6);
  }
  const after=core._get_logic_frame();
  if((after-before)!==600)throw Error('Frame count mismatch');
  if(core._get_z80_ram_bridge_state) {
    const state=core._get_z80_ram_bridge_state();
    if(state.configured||state.ramWrites!=='0')throw Error('Inactive run counted or configured a fault');
    core._set_z80_ram_bridge(1,0,1);for(let i=0;i<2;i++)tick();
    if(BigInt(core._get_z80_ram_bridge_state().z80Writes)===0n)throw Error('Fixture did not exercise recurring Z80 RAM writes');
  }
  const record={label,block,medianMs:median(samples),p95Ms:p95(samples),pcmSamples,rawFrameMs:samples};
  records.push(record);return record;
}
(async()=>{
  const paired=[];
  for(let block=0;block<5;block++) {
    const order=block%2?['current','baseline']:['baseline','current'],result={};
    for(const label of order)result[label]=await run(label,label==='baseline'?baseline:current,block);
    if(result.current.pcmSamples!==result.baseline.pcmSamples)throw Error('Sample count mismatch');
    paired.push({block,order,medianRatio:result.current.medianMs/result.baseline.medianMs,
      p95Ratio:result.current.p95Ms/result.baseline.p95Ms});
  }
  const result={schemaVersion:1,purpose:'Inactive Z80 RAM store-path comparison; original cartridge only',
    protocol:{pairedBlocks:5,framesPerRun:600,warmupFrames:100,alternatingOrder:true,limit:1.05},
    host:{node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model},
    romSha256:crypto.createHash('sha256').update(rom).digest('hex'),fixtureSha256:hash(fixture),
    measurementScriptSha256:hash(__filename),
    baseline:{js:hash(baseline),wasm:hash(path.join(path.dirname(baseline),'genplus.wasm'))},
    current:{js:hash(current),wasm:hash(path.join(path.dirname(current),'genplus.wasm'))},
    paired,medianOfMedianRatios:median(paired.map(x=>x.medianRatio)),medianOfP95Ratios:median(paired.map(x=>x.p95Ratio)),records};
  result.passed=result.medianOfMedianRatios<=1.05&&result.medianOfP95Ratios<=1.05;
  fs.writeFileSync(outArg,JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({passed:result.passed,medianRatio:result.medianOfMedianRatios,p95Ratio:result.medianOfP95Ratios}));
  if(!result.passed)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});
