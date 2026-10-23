#!/usr/bin/env node
/* Private bounded wait/release sequence experiment. Never emits ROM or RAM bytes. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const cp=require('node:child_process');
const observer=require('./observe-attract-demo.cjs');
const origin=require('./run-store-origin-diagnostic.cjs');
const audio=require('./observe-ram-alias-audio-phase.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const START_TICK=1800,END_TICK=1803,CPU_TARGET=0xfff62a,LOGICAL_TARGET=0xf62a;
const SOURCE_SETTERS=[0x3a94,0x3ae6,0x3b98];
const FIXED_BUS_PCS=[0x29ac,0xb14,0xb42,0xb46];
const PROBE_PCS=[0x29b2,0x3af0];
const SOURCE_IDENTITY={repository:'sonicretro/s1disasm',commit:'15dfa3a6ee4c53aeb482233e493755c84b4f3479',
  revision:0,fixBugs:0,cheatsEnabled:0,allOptimizations:0,skipChecksumCheck:0,zeroOffsetOptimization:0,paddingOptimization:0,unusedOptimization:0,
  builtRomSHA256:'46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6'};
const BUS_KIND=2,WRITE_KIND=3,PROBE_KIND=1;

function fail(s){throw new Error(s);}
function validateBusProfile(busPCs){
  const locked=new Set([...FIXED_BUS_PCS,...SOURCE_SETTERS]);
  if(busPCs.length>8||new Set(busPCs).size!==busPCs.length||!FIXED_BUS_PCS.every(pc=>busPCs.includes(pc))||
    busPCs.some(pc=>!locked.has(pc))||busPCs.includes(0x29a4))
    fail('Bus profile does not match the locked Rev00 listing or omits a required wait/VBlank access.');
}
function profile(core,busPCs,enabled=true){
  const fn=core._set_waitdiag_profile;
  if(typeof fn!=='function')fail('Custom core is missing the private wait-sequence profile API.');
  validateBusProfile(busPCs);
  if(PROBE_PCS.length>4)fail('Wait-sequence allowlist exceeds the profile bound.');
  const bus=[...busPCs,...Array(8-busPCs.length).fill(0)];
  const probes=[...PROBE_PCS,...Array(4-PROBE_PCS.length).fill(0)];
  if(fn(enabled?1:0,START_TICK,END_TICK,CPU_TARGET,LOGICAL_TARGET,busPCs.length,...bus,PROBE_PCS.length,...probes)!==0)
    fail('Custom core rejected the bounded wait-sequence profile.');
}
function getWait(core){
  for(const n of ['_get_waitdiag_count','_get_waitdiag_overflow','_get_waitdiag_unexpected_pc','_get_waitdiag_event'])
    if(typeof core[n]!=='function')fail(`Custom core is missing ${n}.`);
  const count=core._get_waitdiag_count()>>>0,overflow=core._get_waitdiag_overflow()>>>0,
    unexpectedPC=core._get_waitdiag_unexpected_pc()>>>0,events=[];
  if(count>64)fail('Wait-sequence event count exceeds the fixed capacity.');
  if((overflow!==0&&overflow!==1)||(unexpectedPC!==0&&unexpectedPC!==1))
    fail('Wait-sequence status flags are not boolean.');
  for(let i=0;i<count;i++){
    const a=Array.from({length:9},(_,f)=>core._get_waitdiag_event(i,f)>>>0);
    const [kind,pc,pcKnown,tick,before,after,repeats,firstOrder,lastOrder]=a;
    if(![1,2,3].includes(kind)||pc>0xffffff||![0,1].includes(pcKnown)||tick<START_TICK||tick>END_TICK||
      ![0,1,2].includes(before)||![0,1,2].includes(after)||repeats<1||firstOrder<1||
      lastOrder-firstOrder+1!==repeats||(!pcKnown&&pc!==0)||
      (kind===1&&(before!==0||after!==0))||(kind===2&&(![1,2].includes(before)||after!==before))||
      (kind===3&&(![1,2].includes(before)||![1,2].includes(after))))
      fail('Wait-sequence event metadata is invalid.');
    if(events.length){const prior=events[events.length-1];
      if(firstOrder!==prior.lastOrder+1||tick<prior.tick)
        fail('Wait-sequence event order is noncontiguous or ticks moved backwards.');}
    events.push({kind,pc,pcKnown:!!pcKnown,tick,before,after,repeats,firstOrder,lastOrder});
  }
  if(overflow||unexpectedPC)fail('Wait-sequence buffer overflowed or observed a target access outside the locked PC profile.');
  return events;
}
function coreFor(js){return ()=>require(js)({locateFile:n=>path.join(path.dirname(js),n)});}
async function customTrial(js,rom,scenario,traceEnabled,busPCs,waitEnabled=true){
  let core;
  const factory=async()=>{
    core=await coreFor(js)();
    const start=core._start.bind(core);
    core._start=()=>{start();profile(core,busPCs,waitEnabled);};
    return core;
  };
  const result=await origin.trial(factory,rom,scenario,traceEnabled);
  return {result,events:getWait(core)};
}
function candidateSetter(events){
  const hits=events.filter(e=>e.kind===WRITE_KIND&&SOURCE_SETTERS.includes(e.pc)&&e.after===2);
  const pcs=[...new Set(hits.map(e=>e.pc))];
  if(pcs.length!==1)fail(`Baseline scout found ${pcs.length} candidate next-setup PCs; expected exactly one.`);
  return pcs[0];
}
function milestone(events,predicate,label){
  const e=events.find(predicate);
  if(!e)fail(`Missing wait/release milestone: ${label}.`);
  return {tick:e.tick,order:e.firstOrder,lastOrder:e.lastOrder,count:e.repeats,pc:e.pc,
    beforeClass:e.before,afterClass:e.after};
}
function sequenceSummary(events,storeRecord,setPC,scenario){
  if(events.length===0)fail('Wait-sequence record is empty.');
  const pollPC=0x29ac, clearPC=0xb46;
  let affectedClear=null,releaseClear=null;
  if(scenario==='A10A11-one-write'){
    affectedClear=milestone(events,e=>e.kind===WRITE_KIND&&e.pc===clearPC&&e.before===2&&e.after===2&&e.tick===1801,'affected VBlank clear');
    releaseClear=milestone(events,e=>e.kind===WRITE_KIND&&e.pc===clearPC&&e.before===2&&e.after===1&&e.firstOrder>affectedClear.order,'post-release VBlank clear');
    if(storeRecord?.instructionPC!==clearPC||storeRecord.originalTargetByteClass!=='zero')fail('Wait sequence disagrees with the pinned first affected zero-write record.');
  } else {
    releaseClear=milestone(events,e=>e.kind===WRITE_KIND&&e.pc===clearPC&&e.before===2&&e.after===1&&e.tick===1801,'tick-1801 baseline VBlank clear');
  }
  const waitTick=affectedClear?affectedClear.tick:releaseClear.tick;
  const pollBefore=milestone(events,e=>e.kind===BUS_KIND&&e.pc===pollPC&&e.before===2&&
    e.tick===waitTick&&e.firstOrder<(affectedClear?affectedClear.order:releaseClear.order),'nonzero wait poll in the clear tick');
  const pollAfter=affectedClear?milestone(events,e=>e.kind===BUS_KIND&&e.pc===pollPC&&e.before===2&&
    e.firstOrder>affectedClear.order&&e.firstOrder<releaseClear.order,'continued nonzero wait poll after affected clear'):null;
  const pollZero=milestone(events,e=>e.kind===BUS_KIND&&e.pc===pollPC&&e.before===1&&e.firstOrder>releaseClear.order,'zero poll after clear');
  const exit=milestone(events,e=>e.kind===PROBE_KIND&&e.pc===0x29b2&&e.firstOrder>pollZero.order,'WaitForVBlank return');
  const successor=milestone(events,e=>e.kind===PROBE_KIND&&e.pc===0x3af0&&e.firstOrder>exit.order,'caller successor');
  const setup=milestone(events,e=>e.kind===WRITE_KIND&&e.pc===setPC&&e.after===2&&e.firstOrder>successor.order,'next nonzero setup store');
  return {pollBefore,pollAfter,affectedClear,releaseClear,pollZero,exit,successor,nextSetup:setup};
}
function summarizeScenario(events,storeRecord,setPC,scenario){
  return sequenceSummary(events,storeRecord,setPC,scenario);
}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function assembleAcceptance(runs,publicEquivalent,publicRuns,sequences,setterPC){
  for(const name of ['baseline','A10A11-one-write'])
    runs[name].noninterference=same(runs[name].disabled.observation,runs[name].enabled.observation)&&
      same(runs[name].disabled.observation,runs[name].repeated.observation);
  const originAcceptance=origin.checkAcceptance(runs,publicEquivalent,publicRuns);
  const sequenceRepeats=Object.keys(sequences).every(s=>same(sequences[s].enabled,sequences[s].repeated));
  const sequenceAcceptance={scoutFoundOneSetter:SOURCE_SETTERS.includes(setterPC),sequenceRepeats,
    baselineSequenceComplete:Boolean(sequences.baseline.enabled.nextSetup),faultSequenceComplete:Boolean(sequences['A10A11-one-write'].enabled.nextSetup),
    passes:originAcceptance.passes&&SOURCE_SETTERS.includes(setterPC)&&sequenceRepeats&&
      Boolean(sequences.baseline.enabled.nextSetup)&&Boolean(sequences['A10A11-one-write'].enabled.nextSetup)};
  return {originAcceptance,sequenceAcceptance};
}
function assembleReport({p1,p2,customCore,publicCore,cartridge,profile:profileData,settings,
  originAcceptance,sequenceAcceptance,scout,sequences,observations,publicRuns}){
  const {baseStage,...waitDiagnostic}=p2;
  if(JSON.stringify(waitDiagnostic).includes(baseStage))fail('Private stage path leaked into report provenance.');
  return {schemaVersion:1,protocol:'private-vblank-wait-sequence-v1',applicationIdentity:'custom diagnostic build; not public v0.2.7',
    provenance:{base:p1,waitDiagnostic,customCore,publicCore},cartridge,profile:profileData,settings,
    originAcceptance,sequenceAcceptance,scout,sequences,observations,publicRuns};
}
function verifyStage(stage,repo,{requireCore=true}={}){
  const base=path.join(stage,'store-origin'),p1=JSON.parse(fs.readFileSync(path.join(base,'PROVENANCE.json')));
  const p2=JSON.parse(fs.readFileSync(path.join(stage,'WAITDIAG-PROVENANCE.json')));
  const commit=cp.execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim();
  if(p1.repositoryCommit!==commit)fail('v1 diagnostic stage does not match current source commit.');
  for(const [name,digest] of Object.entries(p1.toolSourcesSHA256||{}))
    if(sha(fs.readFileSync(path.join(repo,name)))!==digest)fail(`v1 source changed since stage: ${name}`);
  const js=path.join(base,'wasm-genplus/src/main/js/genplus.js'),wasm=path.join(base,'wasm-genplus/src/main/js/genplus.wasm');
  const runtime=path.join(base,'wasm-genplus/src/main/c/wasm/work_ram_runtime.c');
  const cpuBus=path.join(base,'wasm-genplus/src/main/c/core/m68k/m68kcpu.h');
  const cpuDecode=path.join(base,'wasm-genplus/src/main/c/core/m68k/m68kcpu.c');
  const treeDigest=crypto.createHash('sha256');
  function walk(dir){for(const ent of fs.readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0)){
    const full=path.join(dir,ent.name),rel=path.relative(path.join(base,'wasm-genplus'),full).split(path.sep).join('/');
    if(ent.isDirectory()){if(ent.name!=='.git'&&ent.name!=='build')walk(full);continue;}
    if(!ent.isFile()||rel==='src/main/js/genplus.js'||rel==='src/main/js/genplus.wasm')continue;
    treeDigest.update(rel);treeDigest.update(Buffer.from(sha(fs.readFileSync(full)),'hex'));
  }}
  walk(path.join(base,'wasm-genplus'));
  if(treeDigest.digest('hex')!==p2.patchedSourceTreeSHA256)fail('Patched v2 staged source tree changed after build.');
  if(p2.repositoryCommit!==commit)fail('Wait diagnostic stage does not match current source commit.');
  const currentDirty=cp.execFileSync('git',['status','--porcelain','--',
    'scripts/build-vblank-wait-diagnostic.py','scripts/run-vblank-wait-sequence.cjs',
    'tests/test_vblank_wait_wasm.cjs','tests/test_vblank_wait_runner.cjs'],{cwd:repo,encoding:'utf8'}).trimEnd().split(/\r?\n/).filter(Boolean);
  if(Boolean(p2.toolSourcesDirty)!==Boolean(currentDirty.length)||
    JSON.stringify(p2.toolSourcesDirtyScope)!==JSON.stringify(currentDirty))
    fail('Wait diagnostic dirty source scope changed after staging.');
  for(const [name,digest] of Object.entries(p2.toolSourcesSHA256||{}))
    if(sha(fs.readFileSync(path.join(repo,name)))!==digest)fail(`Wait diagnostic source changed since stage: ${name}`);
  if(sha(fs.readFileSync(path.join(repo,'scripts/build-vblank-wait-diagnostic.py')))!==p2.builderSHA256||
    sha(fs.readFileSync(runtime))!==p2.runtimeSHA256||sha(fs.readFileSync(cpuBus))!==p2.cpuBusSHA256||
    sha(fs.readFileSync(cpuDecode))!==p2.cpuDecodeSHA256||
    sha(fs.readFileSync(path.join(repo,'scripts/run-vblank-wait-sequence.cjs')))!==p2.runnerSHA256||
    sha(fs.readFileSync(path.join(repo,'tests/test_vblank_wait_wasm.cjs')))!==p2.wasmTestSHA256||
    sha(fs.readFileSync(path.join(repo,'tests/test_vblank_wait_runner.cjs')))!==p2.runnerTestSHA256)
    fail('Wait-sequence staged sources changed after build.');
  let customCore=null;
  if(requireCore){
    if(!fs.existsSync(js)||!fs.existsSync(wasm)||!fs.readFileSync(wasm).subarray(0,4).equals(Buffer.from([0,97,115,109])))
      fail('Staged custom diagnostic core is missing or invalid.');
    customCore={javascriptSHA256:sha(fs.readFileSync(js)),wasmSHA256:sha(fs.readFileSync(wasm))};
  }
  return {base,p1,p2,js,wasm,customCore};
}
async function main(args){
  if(args.length!==3)fail('Usage: node scripts/run-vblank-wait-sequence.cjs /private/path/sonic.md EMPTY_WAIT_STAGE /path/to/extracted-public-v0.2.7');
  const repo=path.resolve(__dirname,'..'),rom=fs.readFileSync(args[0]),cartridge=observer.validateRomBuffer(rom);
  if(sha(rom)!==SOURCE_IDENTITY.builtRomSHA256)fail('Cartridge image does not match the locked Rev00 source build.');
  const stage=verifyStage(path.resolve(args[1]),repo),publicPackage=audio.validateAppDirectory(path.resolve(args[2]));
  if(stage.p1.toolSourcesDirty||stage.p2.toolSourcesDirty)
    fail('Private cartridge runs require a clean committed source stage.');
  // Baseline scout uses only pinned listing candidates; fault runs use the single observed setter PC.
  const scoutPcs=[...FIXED_BUS_PCS,...SOURCE_SETTERS];
  const scout=await customTrial(stage.js,rom,'baseline',true,scoutPcs,true);
  const setterPC=candidateSetter(scout.events);
  const busPCs=[...FIXED_BUS_PCS,setterPC];
  const runs={baseline:{},'A10A11-one-write':{}};
  const sequences={baseline:{},'A10A11-one-write':{}};
  for(const scenario of ['baseline','A10A11-one-write']){
    for(const [label,enabled] of [['disabled',false],['enabled',true],['repeated',true]]){
      const trial=await customTrial(stage.js,rom,scenario,enabled,busPCs,enabled);
      runs[scenario][label]=trial.result;
      if(enabled)sequences[scenario][label]=summarizeScenario(trial.events,trial.result.record,setterPC,scenario);
      else if(trial.events.length)fail('Disabled wait diagnostic produced event records.');
    }
  }
  const publicFactory=require(publicPackage.coreJsPath);
  const publicRuns={};
  for(const scenario of ['baseline','A10A11-one-write']){
    const o=await observer.runTrial(()=>publicFactory({locateFile:n=>path.join(path.dirname(publicPackage.coreJsPath),n)}),rom,scenario);
    publicRuns[scenario]=observer.serializeTrial(o);
  }
  const publicEquivalent=Object.fromEntries(['baseline','A10A11-one-write'].map(s=>[s,
    JSON.stringify(runs[s].disabled.observation)===JSON.stringify(publicRuns[s])]));
  const {originAcceptance,sequenceAcceptance}=assembleAcceptance(runs,publicEquivalent,publicRuns,sequences,setterPC);
  const output=assembleReport({p1:stage.p1,p2:stage.p2,customCore:stage.customCore,
    publicCore:{sourceCommit:publicPackage.manifest.source_commit,javascriptSHA256:publicPackage.javascriptSHA256,wasmSHA256:publicPackage.wasmSHA256},
    cartridge,profile:{effectiveTicks:[START_TICK,END_TICK],cpuTarget:CPU_TARGET,logicalTarget:LOGICAL_TARGET,
      sourceIdentity:SOURCE_IDENTITY,
      busPCs:busPCs.map(x=>x.toString(16).toUpperCase()),probePCs:PROBE_PCS.map(x=>x.toString(16).toUpperCase()),
      setterPC:setterPC.toString(16).toUpperCase(),eventCapacity:64},
    settings:{ticks:2400,externalInput:'zero every tick',faultTick:1801,pulse:'A10/A11 one affected write',recovery:'none'},
    originAcceptance,sequenceAcceptance,scout:{eventCount:scout.events.length},sequences,
    observations:Object.fromEntries(['baseline','A10A11-one-write'].map(s=>[s,
      Object.fromEntries(['disabled','enabled','repeated'].map(k=>[k,runs[s][k].observation]))])),publicRuns});
  process.stdout.write(JSON.stringify(output,null,2)+'\n');
  if(!sequenceAcceptance.passes)process.exitCode=1;
}
if(require.main===module)main(process.argv.slice(2)).catch(e=>{process.stderr.write(`${e.message}\n`);process.exitCode=1;});
module.exports={profile,getWait,candidateSetter,sequenceSummary,summarizeScenario,assembleAcceptance,assembleReport,verifyStage,validateBusProfile,SOURCE_IDENTITY};
