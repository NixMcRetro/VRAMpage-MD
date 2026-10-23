'use strict';
const assert=require('node:assert/strict');
const path=require('node:path');
const {profile,getWait,candidateSetter,sequenceSummary,assembleAcceptance,assembleReport}=require('../scripts/run-vblank-wait-sequence.cjs');
const {verifyStage}=require('../scripts/run-vblank-wait-sequence.cjs');
const {checkAcceptance}=require('../scripts/run-store-origin-diagnostic.cjs');
let groups=0;
let captured=null;
profile({_set_waitdiag_profile(...args){captured=args;return 0;}},[0x29a4,0xb14,0xb46,0x3ae2],true);
assert.equal(captured[0],1);assert.deepEqual(captured.slice(1,5),[1800,1803,0xfff62a,0xf62a]);groups++;
assert.equal(candidateSetter([{kind:3,pc:0x3ae2,after:2}]),0x3ae2);groups++;
assert.throws(()=>candidateSetter([{kind:3,pc:0x3ae2,after:2},{kind:3,pc:0x3a90,after:2}]),/expected exactly one/);groups++;
function fake(events,{overflow=0,unexpected=0}={}){
  return {_get_waitdiag_count:()=>events.length,_get_waitdiag_overflow:()=>overflow,_get_waitdiag_unexpected_pc:()=>unexpected,
    _get_waitdiag_event:(i,f)=>events[i][f]};
}
const events=[
  [2,0x29a4,1,1800,2,2,4,1,4],
  [2,0x29a4,1,1801,2,2,1,5,5],
  [3,0xb46,1,1801,2,2,1,6,6],
  [2,0x29a4,1,1801,2,2,7,7,13],
  [3,0xb46,1,1802,2,1,1,14,14],
  [2,0x29a4,1,1802,1,1,1,15,15],
  [1,0x29aa,1,1802,0,0,1,16,16],
  [1,0x3aec,1,1802,0,0,1,17,17],
  [3,0x3ae2,1,1803,1,2,1,18,18]
];
const record={instructionPC:0xb46,originalTargetByteClass:'zero'};
const summary=sequenceSummary(events.map(([kind,pc,pcKnown,tick,before,after,repeats,firstOrder,lastOrder])=>
  ({kind,pc,pcKnown:!!pcKnown,tick,before,after,repeats,firstOrder,lastOrder})),record,0x3ae2,'A10A11-one-write');
assert.equal(summary.affectedClear.tick,1801);assert.equal(summary.pollAfter.count,7);
assert.ok(summary.releaseClear.order<summary.pollZero.order&&summary.pollZero.order<summary.exit.order);
assert.equal(summary.nextSetup.order,18);groups++;
assert.throws(()=>sequenceSummary(events.slice(0,5).map(([kind,pc,pcKnown,tick,before,after,repeats,firstOrder,lastOrder])=>
  ({kind,pc,pcKnown:!!pcKnown,tick,before,after,repeats,firstOrder,lastOrder})),record,0x3ae2,'A10A11-one-write'),/Missing wait\/release milestone/);groups++;
const badBaseline=[
  {kind:3,pc:0xb46,tick:1801,before:2,after:1,firstOrder:1,lastOrder:1,repeats:1},
  {kind:2,pc:0x29a4,tick:1801,before:2,after:2,firstOrder:2,lastOrder:2,repeats:1},
  {kind:2,pc:0x29a4,tick:1802,before:1,after:1,firstOrder:3,lastOrder:3,repeats:1},
  {kind:1,pc:0x29aa,tick:1802,before:0,after:0,firstOrder:4,lastOrder:4,repeats:1},
  {kind:1,pc:0x3aec,tick:1802,before:0,after:0,firstOrder:5,lastOrder:5,repeats:1},
  {kind:3,pc:0x3ae2,tick:1803,before:1,after:2,firstOrder:6,lastOrder:6,repeats:1}
];
assert.throws(()=>sequenceSummary(badBaseline,null,0x3ae2,'baseline'),/Missing wait\/release milestone/);groups++;
const pairedBaseline=[
  {kind:2,pc:0x29a4,tick:1800,before:2,after:2,firstOrder:1,lastOrder:1,repeats:1},
  {kind:3,pc:0xb46,tick:1800,before:2,after:1,firstOrder:2,lastOrder:2,repeats:1},
  {kind:2,pc:0x29a4,tick:1801,before:2,after:2,firstOrder:3,lastOrder:3,repeats:1},
  {kind:3,pc:0xb46,tick:1801,before:2,after:1,firstOrder:4,lastOrder:4,repeats:1},
  {kind:2,pc:0x29a4,tick:1801,before:1,after:1,firstOrder:5,lastOrder:5,repeats:1},
  {kind:1,pc:0x29aa,tick:1801,before:0,after:0,firstOrder:6,lastOrder:6,repeats:1},
  {kind:1,pc:0x3aec,tick:1801,before:0,after:0,firstOrder:7,lastOrder:7,repeats:1},
  {kind:3,pc:0x3ae2,tick:1802,before:1,after:2,firstOrder:8,lastOrder:8,repeats:1}
];
assert.equal(sequenceSummary(pairedBaseline,null,0x3ae2,'baseline').releaseClear.tick,1801);groups++;
assert.equal(getWait(fake(events)).length,events.length);groups++;
assert.throws(()=>getWait(fake(events,{overflow:1})),/overflowed/);groups++;
assert.throws(()=>getWait(fake(events,{unexpected:1})),/outside the locked/);groups++;
assert.throws(()=>getWait({...fake(events),_get_waitdiag_count:()=>65}),/exceeds the fixed capacity/);groups++;
assert.throws(()=>getWait(fake(events,{overflow:2})),/not boolean/);groups++;
assert.throws(()=>getWait(fake(events.map((e,i)=>i===0?[...e.slice(0,4),3,...e.slice(5)]:e))),/metadata is invalid/);groups++;
assert.throws(()=>getWait(fake(events.map((e,i)=>i===0?[...e.slice(0,6),3,...e.slice(7)]:e))),/metadata is invalid/);groups++;
assert.throws(()=>getWait(fake(events.map((e,i)=>i===1?[...e.slice(0,7),6,...e.slice(8)]:e))),/metadata is invalid/);groups++;
assert.throws(()=>getWait(fake(events.map((e,i)=>i===1?[...e.slice(0,6),5,e[7],9]:e))),/noncontiguous/);groups++;
assert.throws(()=>getWait(fake(events.map((e,i)=>i===1?[...e.slice(0,3),1799,...e.slice(4)]:e))),/metadata is invalid/);groups++;
function mockTrials(){
  const base={preFaultStreamSHA256:'stable',samples:[{tick:100}],externalInputZeroTicks:2400};
  const fault={...base,faultSetterFrame:1800,effectiveFaultTick:1801,reportedActivationFrame:1800,
    pulse:{releaseTick:1801,affectedWritesAtRelease:1,finalCoreState:2}};
  const record={vblankCandidate:true,pcKnown:true,instructionPC:0xb46,interpretation:'zero-write'};
  const make=(observation,enabledRecord=null)=>({disabled:{observation,record:null},
    enabled:{observation,record:enabledRecord},repeated:{observation,record:enabledRecord&&{...enabledRecord}}});
  return {runs:{baseline:make(base),'A10A11-one-write':make(fault,record)},publicRuns:{baseline:base,'A10A11-one-write':fault}};
}
const mock=mockTrials(),eq={baseline:true,'A10A11-one-write':true};
const seq={baseline:{enabled:summary,repeated:structuredClone(summary)},'A10A11-one-write':{enabled:summary,repeated:structuredClone(summary)}};
const assembled=assembleAcceptance(mock.runs,eq,mock.publicRuns,seq,0x3ae2);
assert.equal(assembled.originAcceptance.passes,true);assert.equal(assembled.sequenceAcceptance.passes,true);groups++;
const badMock=mockTrials();badMock.runs.baseline.enabled.observation.externalInputZeroTicks=2399;
assert.equal(assembleAcceptance(badMock.runs,eq,badMock.publicRuns,seq,0x3ae2).originAcceptance.passes,false);groups++;
const report=assembleReport({p1:{repositoryCommit:'abc'},p2:{baseStage:'/private/stage/path',repositoryCommit:'abc'},customCore:{},publicCore:{},
  cartridge:{},profile:{},settings:{},originAcceptance:assembled.originAcceptance,sequenceAcceptance:assembled.sequenceAcceptance,
  scout:{},sequences:seq,observations:{},publicRuns:mock.publicRuns});
assert.equal(Object.hasOwn(report.provenance.waitDiagnostic,'baseStage'),false);
assert.equal(JSON.stringify(report).includes('/private/stage/path'),false);groups++;
if(process.argv[2]){
  const verified=verifyStage(path.resolve(process.argv[2]),path.resolve(__dirname,'..'),{requireCore:false});
  assert.equal(verified.p2.protocol,'private-vblank-wait-probes-v2');
  assert.equal(verified.customCore,null);groups++;
}
process.stdout.write(`VBlank wait runner: ${groups} groups passed.\n`);
