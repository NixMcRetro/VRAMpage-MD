'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {readTrace, compareRuns, verifyPackage, passesEvidence} = require('../scripts/trace-attract-write.cjs');
(async () => {
  let tests = 0;
  assert.equal(readTrace({_get_logic_write_trace_state: () => 0}), null);
  assert.throws(() => readTrace({_get_logic_write_trace_state: () => 1}), /not completed/);
  assert.throws(() => readTrace({_get_logic_write_trace_state: () => 99}), /not completed/);
  tests++;
  const core = {_get_logic_write_trace_state: () => 2};
  const values = {cpu_address: 0xff1234, ram_offset: 0x1234, mapped_offset: 0x1034, width: 2, frame: 1800, reason: 1};
  for (const [key, value] of Object.entries(values)) core[`_get_logic_write_trace_${key}`] = () => value;
  assert.deepEqual(readTrace(core), values);
  assert.deepEqual(Object.keys(readTrace(core)), Object.keys(values)); // No game-data fields.
  core._get_logic_write_trace_width = () => 0;
  assert.throws(() => readTrace(core), /Invalid first-write/);
  tests++;
  const events = [];
  const fake = async (factory, rom, scenario, enabled) => {
    events.push([scenario, enabled]);
    return {trial: {scenario, ticks: 2400, samples: [], timeline: [{tick: 1801, marker: 1}]},
      firstAffectedWrite: enabled && scenario !== 'baseline' ? values : null};
  };
  let runs = await compareRuns(null, null, fake);
  assert.deepEqual(events, [['baseline',false],['baseline',true],['baseline',true],
    ['A10A11-one-write',false],['A10A11-one-write',true],['A10A11-one-write',true]]);
  for (const run of Object.values(runs)) {
    assert.equal(run.tracePreservesObservation, true);
    assert.equal(run.repeatIdentical, true);
    assert.ok(!Object.hasOwn(run.enabled.observation, 'timeline'));
  }
  const historical = {baseline: true, 'A10A11-one-write': true};
  assert.equal(passesEvidence(runs, historical), true);
  const missing = structuredClone(runs);
  missing['A10A11-one-write'].enabled.firstAffectedWrite = null;
  assert.equal(passesEvidence(missing, historical), false);
  const stray = structuredClone(runs);
  stray.baseline.enabled.firstAffectedWrite = values;
  assert.equal(passesEvidence(stray, historical), false);
  assert.equal(passesEvidence(runs, {...historical, baseline: false}), false);
  assert.equal(passesEvidence(runs, {}), false);
  tests++;
  let count = 0;
  runs = await compareRuns(null, null, async (...args) => {
    const result = await fake(...args);
    if (++count === 2) result.trial.timeline[0].marker = 2;
    return result;
  });
  assert.equal(runs.baseline.tracePreservesObservation, false);
  assert.equal(runs.baseline.repeatIdentical, false);
  assert.equal(passesEvidence(runs, {baseline: true, 'A10A11-one-write': true}), false);
  tests++;
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'trace-package-'));
  try {
    fs.mkdirSync(path.join(temp, 'site/core'), {recursive: true});
    const manifest = JSON.stringify({application: 'VRAMpage MD', application_version: '0.2.7', package_format: 1, source_commit: 'a'.repeat(40)});
    fs.writeFileSync(path.join(temp, 'BUILD-INFO.json'), manifest);
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), manifest);
    fs.writeFileSync(path.join(temp, 'VERSION'), '0.2.7\n');
    fs.writeFileSync(path.join(temp, 'site/core/genplus.js'), 'fixture only');
    fs.writeFileSync(path.join(temp, 'site/core/genplus.wasm'), Buffer.from([0,97,115,109,1,0,0,0]));
    assert.equal(verifyPackage(temp).manifest.source_commit, 'a'.repeat(40));
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), '{}');
    assert.throws(() => verifyPackage(temp), /manifests differ/);
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), manifest);
    fs.writeFileSync(path.join(temp, 'VERSION'), '0.2.6');
    assert.throws(() => verifyPackage(temp), /v0.2.7/);
    fs.writeFileSync(path.join(temp, 'VERSION'), '0.2.7');
    fs.writeFileSync(path.join(temp, 'site/core/genplus.wasm'), 'bad');
    assert.throws(() => verifyPackage(temp), /signature/);
  } finally {fs.rmSync(temp, {recursive: true, force: true});}
  tests++;
  console.log(`Write trace runner: ${tests} groups passed.`);
})().catch(e => {console.error(e); process.exitCode = 1;});
