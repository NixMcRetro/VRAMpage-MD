'use strict';
const assert = require('node:assert/strict');
const {diag,checkAcceptance} = require('../scripts/run-store-origin-diagnostic.cjs');
let count = 0;
function core(fields, pc, klass, width) {
  const result = {_get_logic_write_trace_state:()=>2,_get_store_diag_state:()=>1,
    _get_store_diag_pc:()=>pc,_get_store_diag_pc_known:()=>pc===0?0:1,_get_store_diag_value_class:()=>klass,_get_store_diag_width:()=>width};
  for (const [name,value] of Object.entries(fields)) result[`_get_logic_write_trace_${name}`]=()=>value;
  return result;
}
const target={cpu_address:0xfff62a,ram_offset:0xf62a,mapped_offset:0xf22a,width:1,frame:1800,reason:1};
let row=diag(core(target,0x1234,1,1));
assert.equal(row.vblankCandidate,true); assert.equal(row.interpretation,'zero-write'); count++;
row=diag(core(target,0x1234,2,1)); assert.equal(row.interpretation,'nonzero-write'); count++;
row=diag(core({...target,cpu_address:0xfff84a,ram_offset:0xf84a},0x1234,1,1));
assert.equal(row.vblankCandidate,false); assert.equal(row.interpretation,'uninterpreted'); count++;
row=diag(core(target,0,1,1)); assert.equal(row.instructionPC,null); assert.equal(row.pcKnown,false);
assert.equal(row.originalTargetByteClass,'zero'); count++;
assert.throws(()=>diag(core(target,0x1234,1,2)),/Invalid store-origin/); count++;
function evidence() {
  const observation={preFaultStreamSHA256:'same',samples:[{tick:1800}],externalInputZeroTicks:2400};
  const faultObservation={...observation,faultSetterFrame:1800,effectiveFaultTick:1801,reportedActivationFrame:1800,
    pulse:{releaseTick:1801,affectedWritesAtRelease:1,finalCoreState:2}};
  const record={vblankCandidate:true,pcKnown:true,instructionPC:0x200,interpretation:'zero-write'};
  return {
    baseline:{disabled:{observation,record:null},enabled:{observation,record:null},repeated:{observation,record:null},noninterference:true},
    'A10A11-one-write':{disabled:{observation:faultObservation,record:null},enabled:{observation:faultObservation,record},repeated:{observation:faultObservation,record:{...record}},noninterference:true}
  };
}
let result=checkAcceptance(evidence(),{baseline:true,'A10A11-one-write':true},
  {baseline:structuredClone(evidence().baseline.disabled.observation),
    'A10A11-one-write':structuredClone(evidence()['A10A11-one-write'].enabled.observation)});
assert.equal(result.passes,true); count++;
const bad=evidence(); bad['A10A11-one-write'].repeated.observation.pulse.releaseTick=1802;
result=checkAcceptance(bad,{baseline:true,'A10A11-one-write':true},
  {baseline:evidence().baseline.disabled.observation,'A10A11-one-write':evidence()['A10A11-one-write'].enabled.observation});
assert.equal(result.passes,false); assert.equal(result.pulseAccepted,false); count++;
const stale=evidence(); stale.baseline.enabled.record={};
result=checkAcceptance(stale,{baseline:true,'A10A11-one-write':true},
  {baseline:evidence().baseline.disabled.observation,'A10A11-one-write':evidence()['A10A11-one-write'].enabled.observation});
assert.equal(result.noUnexpectedTrace,false); assert.equal(result.passes,false); count++;
console.log(`Store-origin runner: ${count} groups passed.`);
