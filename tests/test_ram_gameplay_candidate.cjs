'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const observer = require('../scripts/observe-attract-demo.cjs');
const candidate = require('../scripts/observe-ram-gameplay-candidate.cjs');
const pinnedPackage = require('../scripts/observe-ram-alias-audio-phase.cjs');

const spec = candidate.CANDIDATE;
const writeTrace = (overrides = {}) => ({cpu_address: 0xffd008, ram_offset: 0xd008,
  mapped_offset: 0xc008, width: 2, frame: 1800, reason: 1, ...overrides});

function setLogicalByte(heap, base, address, value) { heap[base + (address ^ 1)] = value; }
function setLogicalWord(heap, base, address, value) {
  setLogicalByte(heap, base, address, value >>> 8);
  setLogicalByte(heap, base, address + 1, value & 0xff);
}
function setLogicalLong(heap, base, address, value) {
  setLogicalWord(heap, base, address, Math.floor(value / 0x10000));
  setLogicalWord(heap, base, address + 2, value & 0xffff);
}

function makeCore() {
  const heap = new Uint8Array(1_600_000);
  const ram = 1_300_000;
  const input = 1_400_000;
  let frame = 0, activationFrame = null, pulseState = 0, writes = 0, armArgs = null;
  const core = {
    HEAPU8: heap,
    _init() {}, _start() {}, _get_rom_buffer_ref: () => 100,
    _get_input_buffer_ref: () => input, _get_frame_buffer_ref: () => 0,
    _get_logic_ram_ref: () => ram, _get_logic_frame: () => frame,
    _get_logic_activation_frame: () => activationFrame,
    _get_logic_pulse_state: () => pulseState,
    _get_logic_reads: () => 0, _get_logic_writes: () => writes,
    _get_logic_cpu_flags: () => 0,
    _wasm_input_update() {}, _sound: () => 0,
    _arm_logic_write_pulse(...args) {
      armArgs = args;
      activationFrame = frame;
      pulseState = 1;
      return 0;
    },
    _tick() {
      frame++;
      if (frame === observer.TRIAL.faultTick && pulseState === 1) {
        writes = spec.affectedWrites;
        pulseState = 2;
      }
      setLogicalByte(heap, ram, observer.SONIC1_LAYOUT.gameMode, 8);
      setLogicalWord(heap, ram, observer.SONIC1_LAYOUT.demoFlag, 1);
      setLogicalWord(heap, ram, observer.SONIC1_LAYOUT.demoLevelNumber, 1);
      setLogicalWord(heap, ram, observer.SONIC1_LAYOUT.demoCursor, frame);
      setLogicalByte(heap, ram, observer.SONIC1_LAYOUT.demoCountdown, frame & 0xff);
      setLogicalByte(heap, ram, observer.SONIC1_LAYOUT.heldPad, frame & 8);
      setLogicalByte(heap, ram, observer.SONIC1_LAYOUT.pressedPad, frame & 16);
      const player = observer.PLAYER_LAYOUT.objectBase;
      setLogicalByte(heap, ram, player, 1);
      setLogicalLong(heap, ram, player + observer.PLAYER_LAYOUT.worldXFixed, 0x10000 + frame);
      setLogicalLong(heap, ram, player + observer.PLAYER_LAYOUT.worldYFixed, 0x20000 + frame);
      setLogicalWord(heap, ram, player + observer.PLAYER_LAYOUT.velocityX, frame);
      setLogicalWord(heap, ram, player + observer.PLAYER_LAYOUT.velocityY, frame);
    }
  };
  return {core, getArmArgs: () => armArgs};
}

(async () => {
  let tests = 0;
  const validated = observer.validateConfiguredWritePulse(spec);
  assert.deepEqual(validated.args, [1, 11, 12, 1]);
  assert.equal(validated.faultTick, 1801);
  assert.equal(validated.maxTicks, 2400);
  assert.equal(Object.isFrozen(validated), true);
  assert.equal(Object.isFrozen(validated.args), true);
  const mutableSpec = {...spec};
  const copiedSpec = observer.validateConfiguredWritePulse(mutableSpec);
  mutableSpec.lineA = 0;
  assert.deepEqual(copiedSpec.args, [1, 11, 12, 1]);
  assert.equal(observer.validateConfiguredWritePulse({...spec, affectedWrites: 1024}).affectedWrites, 1024);
  for (const patch of [
    {affectedWrites: 0}, {affectedWrites: 1025}, {affectedWrites: 65535},
    {kind: 3}, {lineA: 15}, {lineB: 11}, {faultTick: 1802}, {maxTicks: 2401}, {name: 'baseline'}
  ]) assert.throws(() => observer.validateConfiguredWritePulse({...spec, ...patch}));
  tests++;

  assert.equal(candidate.mapWordAddressPair(0xd008, 11, 12), 0xc008);
  assert.equal(candidate.mapWordAddressPair(0xf62a, 11, 12), 0xf62a);
  assert.equal(candidate.mapWordAddressPair(0xfffe, 11, 12), 0xfffe);
  assert.equal(candidate.validTraceMetadata(writeTrace()), true);
  const unrelatedGenericWrite = writeTrace({cpu_address: 0xff9000, ram_offset: 0x9000, mapped_offset: 0x8000});
  assert.equal(candidate.validTraceMetadata(unrelatedGenericWrite), true);
  for (const invalidTrace of [
    writeTrace({mapped_offset: 0xd008}),
    writeTrace({mapped_offset: 0xd008, width: 1}),
    writeTrace({cpu_address: 0xffd009, ram_offset: 0xd009, mapped_offset: 0xc009}),
    writeTrace({cpu_address: 0xffffff, ram_offset: 0xffff, mapped_offset: 0xffff, width: 2}),
    writeTrace({mapped_offset: 0x10000}),
    writeTrace({cpu_address: 0xffd008 + 0.5})
  ]) assert.equal(candidate.validTraceMetadata(invalidTrace), false);
  const classified = candidate.classifyFirstWrite(writeTrace());
  assert.equal(classified.accepted, true);
  assert.equal(classified.originalPlayerKinematicFieldOverlap, true);
  assert.equal(classified.mappedPlayerKinematicFieldOverlap, false);
  assert.equal(classified.effectLabel, 'original-player-kinematic-field-write-redirected-out-of-player-object');
  assert.deepEqual(classified.originalRange, {start: 0xd008, endExclusive: 0xd00a});
  assert.deepEqual(classified.mappedRange, {start: 0xc008, endExclusive: 0xc00a});
  assert.equal(candidate.classifyFirstWrite(writeTrace({ram_offset: 0xc008})).accepted, false);
  assert.equal(candidate.classifyFirstWrite(writeTrace({mapped_offset: 0xd008})).accepted, false);
  assert.equal(candidate.classifyFirstWrite(writeTrace({reason: 2})).accepted, false);
  assert.equal(candidate.classifyFirstWrite(writeTrace({frame: 1801})).accepted, false);
  assert.equal(candidate.classifyFirstWrite(writeTrace({width: 4})).accepted, false);
  assert.equal(candidate.classifyFirstWrite(writeTrace({cpu_address: 0x0000d008})).sourceTraceValid, false);
  tests++;

  const fresh = makeCore();
  const trial = await observer.runConfiguredWritePulseTrial(() => fresh.core, Buffer.from([1]), spec,
    {collectSafety: true});
  assert.equal(trial.scenario, spec.name);
  assert.equal(trial.faultSetterFrame, 1800);
  assert.equal(trial.effectiveFaultTick, 1801);
  assert.deepEqual(fresh.getArmArgs(), [1, 11, 12, 1]);
  assert.equal(trial.pulse.finalCoreState, 2);
  assert.equal(trial.pulse.affectedWritesAtRelease, 1);
  assert.equal(trial.externalInputZeroTicks, 2400);
  assert.equal(trial.safety.cpuNonzeroTicks, 0);
  assert.equal(trial.safety.demoActiveTicks, 599);
  assert.equal(trial.safety.postFaultCursorValueChanges, 598);
  const legacyCore = makeCore().core;
  await assert.rejects(observer.runTrial(async () => legacyCore, Buffer.from([1]), 'A10A11-one-write'),
    /Core API missing _set_logic_fault/);
  tests++;

  const ticks = [];
  for (let tick = 1803; tick <= 2398; tick++) {
    ticks.push({tick, gameMode: 8, demoFlag: 1, demoLevelNumber: 1, demoCursor: tick,
      demoCountdown: tick & 0xff, heldPad: tick & 7, pressedPad: tick & 3,
      playerObjectId: 1, worldXFixed: 0x7ffffff0, worldYFixed: 0x20000});
  }
  const changed = ticks.map(row => ({...row}));
  for (let i = 80; i < 140; i++) changed[i].worldXFixed = 0x8000fff0;
  const phase = [{lag: 0, candidateTicks: 596, comparedPairs: 596, missingPairs: 0,
    demoStateMatches: 596}];
  const divergence = candidate.positionDivergenceByLag(ticks, changed, phase);
  assert.equal(divergence[0].longestConsecutiveTicksAtLeastOnePixel, 60);
  assert.equal(candidate.hasBoundedTrajectoryDivergence(divergence), true);
  const ambiguous = [...divergence, {...divergence[0], lag: 1}];
  assert.equal(candidate.hasBoundedTrajectoryDivergence(ambiguous), false);
  changed[100].worldXFixed = 0x80000000; // Signed wrap delta is only 16 fixed-point units.
  const wrapped = candidate.positionDivergenceByLag(ticks, changed, phase);
  assert.equal(wrapped[0].longestConsecutiveTicksAtLeastOnePixel, 39);
  tests++;

  const obs = (pulse = null) => ({ticks: 2400, externalInputZeroTicks: 2400, faultSetterFrame: 1800,
    effectiveFaultTick: 1801, reportedActivationFrame: 1800, safety: {
    cpuStopTicks: 0, cpuHaltTicks: 0, cpuNonzeroTicks: 0, demoActiveTicks: 599,
    postFaultCursorValueChanges: 1, postFaultHeldPadValueChanges: 1,
    postFaultPressedPadValueChanges: 1, playerObjectIdOneTimelineTicks: 602
  }, cursorValueChanges: 1, heldPadValueChanges: 1, pulse});
  const baseRun = {disabled: {observation: obs(), firstAffectedWrite: null},
    enabled: {observation: obs(), firstAffectedWrite: null}, repeated: {observation: obs(), firstAffectedWrite: null},
    tracePreservesObservation: true, repeatIdentical: true};
  const pulseResult = {requestedAffectedWrites: 1, finalCoreState: 2,
    affectedWritesAtRelease: 1, releaseTick: 1801};
  const candRun = {disabled: {observation: obs(), firstAffectedWrite: null},
    enabled: {observation: obs(pulseResult), firstAffectedWrite: writeTrace()},
    repeated: {observation: obs(pulseResult), firstAffectedWrite: writeTrace()},
    tracePreservesObservation: true, repeatIdentical: true, prefaultMatchesBaseline: true};
  const acceptedNegative = candidate.protocolAcceptance({baseline: baseRun, [spec.name]: candRun}, {clean: true});
  assert.equal(acceptedNegative.accepted, true);
  assert.equal(candidate.hasBoundedTrajectoryDivergence([]), false);
  tests++;

  const createTrial = (scenario, diverge, freeze = false) => {
    const pulse = scenario === 'baseline' ? null : {requestedAffectedWrites: 1, finalCoreState: 2,
      affectedWritesAtRelease: 1, releaseTick: 1801};
    const timeline = [];
    for (let tick = 1799; tick <= 2400; tick++) {
      const heldPad = freeze && tick >= 1802 ? 0 : tick & 7;
      const pressedPad = freeze && tick >= 1802 ? 0 : tick & 15;
      timeline.push({tick, rawActiveFrameSHA256: 'frame-hash', gameMode: 8, demoFlag: 1,
        demoLevelNumber: 1, demoCursor: freeze && tick >= 1802 ? 1801 : tick,
        demoCountdown: tick & 0xff, heldPad, pressedPad, playerObjectId: 1,
        worldXFixed: 0x640000 + (diverge && tick >= 1803 && tick < 1863 ? 0x10000 : 0),
        worldYFixed: 0x200000, velocityX: 0, velocityY: 0});
    }
    return {scenario, ticks: 2400, externalInputZeroTicks: 2400, preFaultStreamSHA256: 'same-prefault',
      streamSHA256: 'scalar-stream', timelineSHA256: 'timeline-hash', cursorValueChanges: 300,
      heldPadValueChanges: 200, pulse, safety: {cpuStopTicks: 0, cpuHaltTicks: 0, cpuNonzeroTicks: 0,
        demoActiveTicks: 599, postFaultCursorValueChanges: freeze ? 0 : 100,
        postFaultHeldPadValueChanges: freeze ? 0 : 20,
        postFaultPressedPadValueChanges: freeze ? 0 : 20, playerObjectIdOneTimelineTicks: 602},
      faultSetterFrame: scenario === 'baseline' ? null : 1800,
      effectiveFaultTick: scenario === 'baseline' ? null : 1801,
      reportedActivationFrame: scenario === 'baseline' ? null : 1800,
      samples: [{tick: 1799, gameMode: 8}, {tick: 1800, gameMode: 8}], timeline};
  };
  const sourceCheck = {clean: true, sourceDirty: false, sourceCommit: 'a'.repeat(40), hashes: {}};
  for (const diverge of [false, true]) {
    let runCount = 0;
    const runs = await candidate.compareCandidateRuns(null, null, spec, async (_factory, _rom, scenario, enabled) => {
      runCount++;
      const trial = createTrial(scenario, diverge && scenario !== 'baseline');
      return {trial, firstAffectedWrite: enabled && scenario !== 'baseline' ? writeTrace() : null};
    });
    assert.equal(runCount, 6);
    assert.equal(runs[spec.name].disabled.observation.scenario, spec.name);
    assert.equal(runs[spec.name].repeatIdentical, true);
    const report = candidate.buildCandidateReport(runs, sourceCheck);
    assert.equal(report.protocolAcceptance.accepted, true);
    assert.equal(report.scientificOutcome.boundedTrajectoryDivergenceObserved, diverge);
    assert.equal(report.scientificOutcome.phaseAlignment.uniqueSameLag, true);
    assert.equal(report.phaseReports.enabled.phases.find(row => row.lag === 0).rawActiveFrameMatches, 596);
    for (const run of Object.values(report.runs)) {
      for (const attempt of [run.disabled, run.enabled, run.repeated]) {
        assert.equal(Object.hasOwn(attempt.observation, 'timeline'), false);
      }
    }
  }
  tests++;

  const negativeCases = [
    {name: 'freeze', freeze: true, write: writeTrace()},
    {name: 'hypothesis-miss', freeze: false,
      write: writeTrace({cpu_address: 0xff9000, ram_offset: 0x9000, mapped_offset: 0x8000})}
  ];
  for (const testCase of negativeCases) {
    const runs = await candidate.compareCandidateRuns(null, null, spec,
      async (_factory, _rom, scenario, enabled) => ({
        trial: createTrial(scenario, false, testCase.freeze),
        firstAffectedWrite: enabled && scenario !== 'baseline' ? testCase.write : null
      }));
    const report = candidate.buildCandidateReport(runs, sourceCheck);
    assert.equal(report.protocolAcceptance.accepted, true, testCase.name);
    assert.equal(report.scientificOutcome.boundedTrajectoryDivergenceObserved, false, testCase.name);
    if (testCase.name === 'hypothesis-miss') assert.equal(report.scientificOutcome.sourceHypothesisMatches, false);
    if (testCase.name === 'hypothesis-miss') {
      assert.equal(candidate.validTraceMetadata(testCase.write), true);
      assert.equal(report.protocolAcceptance.checks.candidateTraceMetadataValid, true);
    }
    if (testCase.name === 'freeze') assert.equal(report.scientificOutcome.safety.accepted, false);
  }
  const wrongMapRuns = await candidate.compareCandidateRuns(null, null, spec,
    async (_factory, _rom, scenario, enabled) => ({
      trial: createTrial(scenario, scenario !== 'baseline'),
      firstAffectedWrite: enabled && scenario !== 'baseline' ? writeTrace({mapped_offset: 0xd008}) : null
    }));
  const wrongMapReport = candidate.buildCandidateReport(wrongMapRuns, sourceCheck);
  assert.equal(wrongMapReport.protocolAcceptance.accepted, false);
  assert.equal(wrongMapReport.scientificOutcome.boundedTrajectoryDivergenceObserved, false);
  const invalidRuns = await candidate.compareCandidateRuns(null, null, spec,
    async (_factory, _rom, scenario, enabled) => ({
      trial: createTrial(scenario, scenario !== 'baseline'),
      firstAffectedWrite: enabled && scenario !== 'baseline' ? writeTrace() : null
    }));
  const invalidReport = candidate.buildCandidateReport(invalidRuns, {...sourceCheck, clean: false});
  assert.equal(invalidReport.protocolAcceptance.accepted, false);
  assert.equal(invalidReport.scientificOutcome.boundedTrajectoryDivergenceObserved, false);
  tests++;

  const invalidCli = spawnSync(process.execPath, [path.resolve(__dirname,
    '../scripts/observe-ram-gameplay-candidate.cjs'), '--invalid'], {encoding: 'utf8'});
  assert.equal(invalidCli.status, 1);
  assert.match(invalidCli.stderr, /Usage: node scripts\/observe-ram-gameplay-candidate/);
  tests++;

  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'candidate-public-package-'));
  try {
    fs.mkdirSync(path.join(temp, 'site/core'), {recursive: true});
    const manifest = {application: pinnedPackage.APP_PROFILE.application,
      application_version: pinnedPackage.APP_PROFILE.applicationVersion,
      package_format: pinnedPackage.APP_PROFILE.packageFormat,
      source_commit: pinnedPackage.APP_PROFILE.packageSourceCommit};
    fs.writeFileSync(path.join(temp, 'BUILD-INFO.json'), JSON.stringify(manifest));
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), JSON.stringify(manifest));
    fs.writeFileSync(path.join(temp, 'VERSION'), '0.2.7\n');
    const jsPath = path.join(temp, 'site/core/genplus.js');
    const wasmPath = path.join(temp, 'site/core/genplus.wasm');
    fs.copyFileSync(path.resolve(__dirname, '../site/core/genplus.js'), jsPath);
    fs.copyFileSync(path.resolve(__dirname, '../site/core/genplus.wasm'), wasmPath);
    assert.equal(candidate.verifyPackage(temp).manifest.source_commit,
      pinnedPackage.APP_PROFILE.packageSourceCommit);
    fs.writeFileSync(jsPath, Buffer.concat([fs.readFileSync(jsPath), Buffer.from([0])]));
    assert.throws(() => candidate.verifyPackage(temp), /core hashes\/signature/);
    fs.copyFileSync(path.resolve(__dirname, '../site/core/genplus.js'), jsPath);
    fs.writeFileSync(wasmPath, Buffer.concat([fs.readFileSync(wasmPath), Buffer.from([0])]));
    assert.throws(() => candidate.verifyPackage(temp), /core hashes\/signature/);
    const wrongSource = {...manifest, source_commit: 'f'.repeat(40)};
    fs.writeFileSync(path.join(temp, 'BUILD-INFO.json'), JSON.stringify(wrongSource));
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), JSON.stringify(wrongSource));
    assert.throws(() => candidate.verifyPackage(temp), /pinned public v0.2.7 profile/);
    fs.writeFileSync(path.join(temp, 'site/build-info.json'), JSON.stringify(manifest));
    assert.throws(() => candidate.verifyPackage(temp), /manifests differ/);
  } finally { fs.rmSync(temp, {recursive: true, force: true}); }
  tests++;

  console.log(`RAM gameplay candidate: ${tests} groups passed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
