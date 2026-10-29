const assert=require('node:assert/strict');
require('../site/experiment-comparison.js');
const {parse,compare,MAX_BYTES}=globalThis.VRAMpageExperimentComparison;
const A={schemaVersion:1,corePin:'d'.repeat(40),build:{applicationVersion:'0.4.1',sourceCommit:'a'.repeat(40)},modelVersion:'0.4.1-experimental',rom:{name:'Test',sha256:'b'.repeat(64)},vramFault:{kind:'none'},logic:{fault:null,readCount:0,writeCount:0},currentFrame:12,cpuFlags:0};
const B=JSON.parse(JSON.stringify(A));
assert.equal(compare(A,B).find(row=>row.label==='ROM SHA-256').status,'match');
assert.equal(compare(A,B).find(row=>row.label==='Core Revision').status,'match');
B.rom.sha256='c'.repeat(64);
assert.equal(compare(A,B).find(row=>row.label==='ROM SHA-256').status,'mismatch');
const legacy=compare({rom:{name:'old'}},{rom:{name:'old'}});
assert.equal(legacy.find(row=>row.label==='ROM SHA-256').status,'unknown');
assert.equal(legacy.find(row=>row.label==='Core Revision').status,'unknown');
assert.equal(legacy.find(row=>row.label==='VRAM Kind').a,'Unknown');
assert.equal(compare({corePin:'d'.repeat(40),build:{status:'unavailable',sourceCommit:'a'.repeat(40)}},{corePin:'d'.repeat(40),build:{status:'unavailable',sourceCommit:'a'.repeat(40)}}).find(row=>row.label==='Build Source Commit').status,'unknown');
const partialBuild=compare({build:{status:'available',sourceCommit:'a'.repeat(40)}},{build:{status:'unavailable',sourceCommit:'b'.repeat(40)}}).find(row=>row.label==='Build Source Commit');
assert.deepEqual([partialBuild.a,partialBuild.b,partialBuild.status],['a'.repeat(40),'Unknown','unknown']);
assert.equal(compare({logic:{available:true,modelVersion:'ram-v1'}},{logic:{available:true,modelVersion:'ram-v2'}}).find(row=>row.label==='RAM Model Version').status,'mismatch');
assert.throws(()=>parse(JSON.stringify({rom:{},schemaVersion:2})),/schema version/);
const oldAndNew=compare({rom:{name:'old'},faultActive:false,readCount:3},{rom:{name:'old'},logic:{available:true,active:false,readCount:3}});
assert.equal(oldAndNew.find(row=>row.label==='RAM Active').status,'match');
assert.equal(oldAndNew.find(row=>row.label==='RAM Affected Reads').status,'match');
assert.equal(compare({logic:{available:false,active:false,readCount:0}},{logic:{available:false,active:false,readCount:0}}).find(row=>row.label==='RAM Affected Reads').status,'unknown');
const audioUnavailable=compare({fmInputFault:{available:false,configured:false,dataMask:0}},{fmInputFault:{available:true,configured:false,dataMask:0}});
assert.equal(audioUnavailable.find(row=>row.label==='FM Configured').status,'unknown');
assert.equal(audioUnavailable.find(row=>row.label==='FM Configured').a,'Unknown');
assert.equal(audioUnavailable.find(row=>row.label==='FM Recorded Writes').status,'unknown');
assert.equal(audioUnavailable.find(row=>row.label==='FM Model Version').status,'unknown');
assert.equal(compare({psgInputFault:{schemaVersion:1,available:true,configured:false}},{psgInputFault:{schemaVersion:1,available:true,configured:false}}).find(row=>row.label==='PSG Data Mask').status,'unknown');
const disabled=compare({vramFault:{bridge:null},vramTransaction:{available:false,modelId:1}},{vramFault:{bridge:null},vramTransaction:{available:false,modelId:1}});
assert.equal(disabled.find(row=>row.label==='VRAM Bridge').status,'match');
assert.equal(disabled.find(row=>row.label==='VRAM Model ID').status,'unknown');
assert.equal(compare({rom:{name:'old'}},{rom:{name:'old'}}).find(row=>row.label==='ROM SHA-256').status,'unknown');
assert.equal(compare({vramFault:{addressMask:256,bridge:[0,0]}},{vramFault:{addressMask:256,bridge:[0,0]}}).find(row=>row.label==='VRAM Bridge').status,'unknown');
assert.equal(compare({logicFault:{kind:'address-stuck-low',addressMask:32768,lines:['D16']}},{logicFault:{kind:'address-stuck-low',addressMask:32768,lines:['D16']}}).find(row=>row.label==='RAM Recorded Address Mask').status,'unknown');
const hostile=parse('{"rom":{"name":"<img src=x onerror=alert(1)>"}}');
assert.equal(hostile.rom.name,'<img src=x onerror=alert(1)>');
assert.throws(()=>parse('[]'),/object/);
assert.throws(()=>parse('{}'),/experiment export/);
assert.throws(()=>parse('{"rom":{}}'),/experiment export/);
assert.throws(()=>parse('{"logicFault":null}'),/experiment export/);
assert.throws(()=>parse('{'),SyntaxError);
assert.throws(()=>parse(' '.repeat(MAX_BYTES+1)),/256 KB/);
assert.equal(parse(JSON.stringify({rom:{name:'x'}})+' '.repeat(MAX_BYTES-JSON.stringify({rom:{name:'x'}}).length)).rom.name,'x');
let deep={value:1};for(let i=0;i<18;i++)deep={next:deep};
assert.throws(()=>parse(JSON.stringify({rom:{name:'old'},deep})),/structure limits/);
assert.throws(()=>parse(JSON.stringify({rom:{name:'test'},many:Object.fromEntries(Array.from({length:513},(_,i)=>[`k${i}`,i]))})),/too many fields/);
assert.throws(()=>parse(JSON.stringify({rom:{name:'test'},many:Array.from({length:6000},()=>({a:0}))})),/structure limits/);
const malformed=compare({rom:{sha256:7},corePin:{value:'d'.repeat(40)},logic:{active:'false',readCount:'0'},fmInputFault:{available:true,configured:'false',dataMask:{}}},
  {rom:{sha256:7},corePin:{value:'d'.repeat(40)},logic:{active:'false',readCount:'0'},fmInputFault:{available:true,configured:'false',dataMask:{}}});
for(const label of ['ROM SHA-256','Core Revision','RAM Active','RAM Affected Reads','FM Configured','FM Data Mask'])
  assert.equal(malformed.find(row=>row.label===label).status,'unknown',`${label} must not match malformed values`);
assert.throws(()=>parse('{"rom":"not an object"}'),/experiment export/);
const outcomes=compare({faultDisconnects:[{action:'disconnect',results:[]}],cpuInterventions:[]},{faultDisconnects:[],cpuInterventions:[]});
assert.equal(outcomes.find(row=>row.label==='Fault Disconnect Outcomes').a,'[{"action":"disconnect","results":[]}]');
const checkpoints=compare({checkpointEvents:[{action:'restore',outcome:'restored'}],checkpointSegment:1},
  {checkpointEvents:[],checkpointSegment:0});
for(const label of ['Checkpoint Events','Checkpoint Segment'])
  assert.equal(checkpoints.find(row=>row.label===label).status,'mismatch');
assert.equal(compare(A,B).find(row=>row.label==='Checkpoint Segment').status,'unknown');
assert.equal(compare({checkpointSegment:-1},{checkpointSegment:-1}).find(row=>row.label==='Checkpoint Segment').status,'unknown');
const policies=compare({automaticRecovery:{forceResumeEnabled:true,cpuRecoveryEnabled:true,waitFrames:8}},
  {automaticRecovery:{forceResumeEnabled:false,cpuRecoveryEnabled:true,waitFrames:2}});
assert.equal(policies.find(row=>row.label==='Force Resume Enabled').status,'mismatch');
assert.equal(policies.find(row=>row.label==='CPU Recovery Enabled').status,'match');
assert.equal(policies.find(row=>row.label==='Recovery Wait Frames').status,'mismatch');
assert.equal(compare(A,B).find(row=>row.label==='Force Resume Enabled').status,'unknown');
const rgbA={rgbEncoderFault:{available:true,configured:true,effective:true,cutMask:5,pair:[0,2],modelVersion:'rgb-input-code-voltage-v1'}};
const rgbB=structuredClone(rgbA);rgbB.rgbEncoderFault.cutMask=1;
assert.equal(compare(rgbA,rgbA).find(row=>row.label==='RGB Encoder Effective').status,'match');
assert.equal(compare(rgbA,rgbB).find(row=>row.label==='RGB Encoder Cut Mask').status,'mismatch');
assert.equal(compare(rgbA,B).find(row=>row.label==='RGB Encoder Pair').status,'unknown');
rgbB.rgbEncoderFault.pair=[0,0];
assert.equal(compare(rgbA,rgbB).find(row=>row.label==='RGB Encoder Pair').status,'unknown',
  'equal pair endpoints are malformed and cannot compare as configured evidence');
console.log('Experiment comparison parser and row tests passed.');

const z80A={z80RamFault:{available:true,configured:true,effective:true,bridgeA:0,bridgeB:12,modelVersion:'z80-ram-write-address-pair-v1',activationFrame:8,ramWrites:'9007199254740993',changedAddresses:'4',z80Writes:'3',m68kWrites:'9007199254740990'}};
const z80B=structuredClone(z80A);z80B.z80RamFault.ramWrites='9007199254740994';
assert.deepEqual(parse(JSON.stringify(z80A)),z80A);
assert.equal(compare(z80A,z80B).find(row=>row.label==='Z80 RAM Recorded Writes').status,'mismatch');
assert.equal(compare(z80A,A).find(row=>row.label==='Z80 RAM Configured').status,'unknown');
z80B.z80RamFault.bridgeB=13;
assert.equal(compare(z80A,z80B).find(row=>row.label==='Z80 RAM Bridge B').status,'unknown');
z80B.z80RamFault.available=false;
assert.equal(compare(z80A,z80B).find(row=>row.label==='Z80 RAM Recorded Writes').status,'unknown');
const regionA={rom:{name:'region'},machine:{schemaVersion:1,available:true,regionCode:128,pal:false,
 masterClock:53693175,frameRate:59.92274,linesPerFrame:262,width:320,height:224,interlaced:false}};
const regionB={...regionA,machine:{...regionA.machine,regionCode:192,pal:true,linesPerFrame:313,frameRate:49.701459,height:240}};
assert.equal(compare(regionA,regionA).find(x=>x.label==='Effective Region').status,'match');
assert.equal(compare(regionA,regionB).find(x=>x.label==='Effective Region').status,'mismatch');
assert.equal(compare(regionA,{rom:{name:'legacy'}}).find(x=>x.label==='Frame Rate').status,'unknown');
assert.equal(compare(regionA,{...regionA,machine:{...regionA.machine,available:false}}).find(x=>x.label==='PAL Timing').status,'unknown');
assert.equal(compare(regionA,{...regionA,machine:{...regionA.machine,height:true}}).find(x=>x.label==='Video Height').status,'unknown');
const fmMachine=state=>({machine:{available:false,fmOutputModel:state}});
const fmDiscrete={schemaVersion:1,available:true,supported:true,loaded:true,requestedModel:'integrated',
  effectiveModel:'discrete',backend:'mame-opn2',reason:'none'};
const fmIntegrated={...fmDiscrete,requestedModel:'discrete',effectiveModel:'integrated'};
assert.equal(compare(fmMachine(fmDiscrete),fmMachine(fmDiscrete)).find(r=>r.label==='Effective FM Output Model').status,'match');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine(fmIntegrated)).find(r=>r.label==='Effective FM Output Model').status,'mismatch');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine(fmIntegrated)).find(r=>r.label==='Requested FM Output Model').status,'mismatch');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine({...fmDiscrete,backend:'nuked-opn2',supported:false,effectiveModel:null})).find(r=>r.label==='FM Output Backend').status,'mismatch');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine({...fmDiscrete,backend:'nuked-opn2'})).find(r=>r.label==='Effective FM Output Model').status,'unknown',
  'effective MAME identity is unknown when the reported backend contradicts it');
const missingBackend={...fmDiscrete};delete missingBackend.backend;
assert.equal(compare(fmMachine(fmDiscrete),fmMachine(missingBackend)).find(r=>r.label==='Effective FM Output Model').status,'unknown',
  'effective MAME identity is unknown when backend metadata is missing');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine({...fmDiscrete,backend:'unknown-opn'})).find(r=>r.label==='Effective FM Output Model').status,'unknown',
  'effective MAME identity is unknown when backend metadata is invalid');
assert.equal(compare(fmMachine(fmDiscrete),fmMachine({...fmDiscrete,schemaVersion:2})).find(r=>r.label==='Effective FM Output Model').status,'unknown');
assert.equal(compare(fmMachine(fmDiscrete),{machine:{available:true}}).find(r=>r.label==='Effective FM Output Model').status,'unknown');
console.log('Machine-region comparison observations passed.');

const dataRecord=mask=>({logic:{available:true,referenceProfile:'model1-pal-va65-two-byte-v1',
  dataMaskAvailable:true,dataMask:mask,fault:{kind:'data-stuck-low',access:'write',dataMask:mask,lines:['D0']}}});
assert.equal(compare(dataRecord(1),dataRecord(0x100)).find(row=>row.label==='RAM Data Mask').status,'mismatch');
assert.equal(compare(dataRecord(1),{}).find(row=>row.label==='RAM Data Mask').status,'unknown');
assert.equal(compare(dataRecord(1),{logic:{dataMaskAvailable:false,dataMask:0}}).find(row=>row.label==='RAM Data Mask').status,'unknown');
assert.equal(compare(dataRecord(1),dataRecord(1)).find(row=>row.label==='RAM Recorded Data Mask').status,'match');
assert.equal(compare(dataRecord(1),{}).find(row=>row.label==='RAM Reference Profile').status,'unknown');

const inhibitRecord=mask=>({...dataRecord(0),logic:{...dataRecord(0).logic,writeInhibitAvailable:true,writeInhibitMask:mask,
  fault:{kind:'write-inhibit',access:'write',lines:['/LWR'],writeInhibitMask:mask}}});
assert.equal(compare(inhibitRecord(1),inhibitRecord(2)).find(r=>r.label==='RAM Write Inhibit Mask').status,'mismatch');
assert.equal(compare(inhibitRecord(1),inhibitRecord(1)).find(r=>r.label==='RAM Recorded Lines / Pair').status,'match');
assert.equal(compare(inhibitRecord(1),dataRecord(0)).find(r=>r.label==='RAM Write Inhibit Mask').status,'unknown');
assert.equal(compare(inhibitRecord(1),{...inhibitRecord(1),logic:{writeInhibitAvailable:false,writeInhibitMask:0}}).find(r=>r.label==='RAM Write Inhibit Mask').status,'unknown');
