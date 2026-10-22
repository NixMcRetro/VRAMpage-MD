'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {
  readLogicalByte, readLogicalWord, readLogicalLong, readLogicalSignedWord,
  readAttractFields, inputBufferIsZero,
  validateRomBuffer, validateManifest, validateAppDirectory, loadVerified,
  runTrial, prefaultMatches, sameTrials, comparePhases, serializeTrial,
  TOOL_VERSION, PROTOCOL_VERSION, APP_PROFILE, SONIC1_LAYOUT, PLAYER_LAYOUT, PHASE_WINDOW, TRIAL
} = require('../scripts/observe-attract-demo.cjs');

const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const setLogicalByte = (heap, base, address, value) => { heap[base + (address ^ 1)] = value; };
const setLogicalWord = (heap, base, address, value) => {
  setLogicalByte(heap, base, address, (value >>> 8) & 0xff);
  setLogicalByte(heap, base, address + 1, value & 0xff);
};
const setLogicalLong = (heap, base, address, value) => {
  setLogicalWord(heap, base, address, Math.floor(value / 0x10000));
  setLogicalWord(heap, base, address + 2, value & 0xffff);
};

function makeFixturePackage(root) {
  const app = path.join(root, 'app');
  fs.mkdirSync(path.join(app, 'site', 'core'), {recursive: true});
  const rom = Buffer.from([1,2,3,4,5,6]);
  const js = Buffer.from('module.exports = () => { throw new Error("fixture loader"); };\n');
  const wasm = Buffer.from([0,0x61,0x73,0x6d,1,0,0,0]);
  const profile = {
    application: 'VRAMpage MD', applicationVersion: '0.2.6', packageFormat: 1,
    packageSourceCommit: 'c'.repeat(40), corePin: 'fixture-core-pin',
    javascriptSHA256: sha256(js), wasmSHA256: sha256(wasm),
    romLength: rom.length, romSHA256: sha256(rom)
  };
  const manifest = {application: profile.application, application_version: profile.applicationVersion,
    source_commit: profile.packageSourceCommit, package_format: profile.packageFormat};
  fs.writeFileSync(path.join(app, 'BUILD-INFO.json'), JSON.stringify(manifest));
  fs.mkdirSync(path.join(app, 'site'), {recursive: true});
  fs.writeFileSync(path.join(app, 'site', 'build-info.json'), JSON.stringify(manifest));
  fs.writeFileSync(path.join(app, 'VERSION'), profile.applicationVersion + '\n');
  fs.writeFileSync(path.join(app, 'site', 'core', 'genplus.js'), js);
  fs.writeFileSync(path.join(app, 'site', 'core', 'genplus.wasm'), wasm);
  const romPath = path.join(root, 'synthetic.bin');
  fs.writeFileSync(romPath, rom);
  return {app, rom, romPath, profile};
}

function putFields(heap, base, fields) {
  setLogicalByte(heap, base, SONIC1_LAYOUT.gameMode, fields.gameMode);
  setLogicalByte(heap, base, SONIC1_LAYOUT.heldPad, fields.heldPad);
  setLogicalByte(heap, base, SONIC1_LAYOUT.pressedPad, fields.pressedPad);
  setLogicalWord(heap, base, SONIC1_LAYOUT.demoCursor, fields.demoCursor);
  setLogicalByte(heap, base, SONIC1_LAYOUT.demoCountdown, fields.demoCountdown);
  setLogicalWord(heap, base, SONIC1_LAYOUT.demoFlag, fields.demoFlag);
  setLogicalWord(heap, base, SONIC1_LAYOUT.demoLevelNumber, fields.demoLevelNumber);
  setLogicalByte(heap, base, PLAYER_LAYOUT.objectBase + PLAYER_LAYOUT.objectId, fields.playerObjectId);
  setLogicalLong(heap, base, PLAYER_LAYOUT.objectBase + PLAYER_LAYOUT.worldXFixed, fields.worldXFixed);
  setLogicalLong(heap, base, PLAYER_LAYOUT.objectBase + PLAYER_LAYOUT.worldYFixed, fields.worldYFixed);
  setLogicalWord(heap, base, PLAYER_LAYOUT.objectBase + PLAYER_LAYOUT.velocityX, fields.velocityX & 0xffff);
  setLogicalWord(heap, base, PLAYER_LAYOUT.objectBase + PLAYER_LAYOUT.velocityY, fields.velocityY & 0xffff);
}

function fakeCore({events, pulseWrite=true}={}) {
  const heap = new Uint8Array(1_600_000);
  const ram = 1_300_000;
  const inputPointer = 1_400_000;
  let frame = 0, faultReads = 0, faultWrites = 0, cpuFlags = 0;
  let activationFrame = null, pulseState = 0, active = false;
  const note = (...event) => events?.push(event);
  return {
    HEAPU8: heap,
    _init() { note('init'); },
    _start() { note('start'); },
    _get_rom_buffer_ref: () => 100,
    _get_input_buffer_ref: () => inputPointer,
    _get_frame_buffer_ref: () => 0,
    _get_logic_ram_ref: () => ram,
    _get_logic_frame: () => frame,
    _get_logic_activation_frame: () => activationFrame,
    _get_logic_reads: () => faultReads,
    _get_logic_writes: () => faultWrites,
    _get_logic_cpu_flags: () => cpuFlags,
    _get_logic_pulse_state: () => pulseState,
    _wasm_input_update() { note('input', frame + 1); },
    _set_logic_fault(...args) {
      note('ordinaryFault', frame, ...args);
      activationFrame = frame;
      active = true;
      return 0;
    },
    _arm_logic_write_pulse(...args) {
      note('pulseFault', frame, ...args);
      activationFrame = frame;
      active = true;
      pulseState = 1;
      return 0;
    },
    _tick() {
      frame++;
      note('tick', frame);
      const fields = {
        gameMode: 8, heldPad: frame % 4 === 0 ? 8 : 0,
        pressedPad: frame % 16 === 0 ? 8 : 0,
        demoCursor: frame, demoCountdown: frame % 255,
        demoFlag: 1, demoLevelNumber: 1,
        playerObjectId: 1, worldXFixed: 0x10000 + frame,
        worldYFixed: 0x20000 + frame, velocityX: frame & 0x7fff,
        velocityY: -(frame & 0x7fff)
      };
      putFields(heap, ram, fields);
      if (active && frame === 1801 && pulseState === 1) {
        if (pulseWrite) faultWrites++;
        active = false;
        pulseState = pulseWrite ? 2 : 3;
      }
      if (active) faultReads++;
      heap[frame % 320 * 4] = frame & 0xff;
    },
    _sound() { note('sound', frame); return 0; }
  };
}

(async () => {
  let tests = 0;
  // Logical bytes are word-lane-swapped in the actual LSB_FIRST profile.
  const heap = new Uint8Array(0x10000 + 32);
  const base = 16;
  heap[base + (0x100 ^ 1)] = 0x12;
  heap[base + (0x101 ^ 1)] = 0x34;
  heap[base + (0x102 ^ 1)] = 0xa5;
  assert.equal(readLogicalByte(heap, base, 0x100), 0x12);
  assert.equal(readLogicalWord(heap, base, 0x100), 0x1234);
  assert.equal(readLogicalByte(heap, base, 0x102), 0xa5);
  assert.equal(readLogicalLong(heap, base, 0x100), 0x1234a500);
  assert.equal(readLogicalSignedWord(heap, base, 0x100), 0x1234);
  heap[base + (0xffff ^ 1)] = 0x7b;
  assert.equal(readLogicalByte(heap, base, 0xffff), 0x7b);
  assert.throws(() => readLogicalWord(heap, base, 0xffff), /word range/);
  assert.throws(() => readLogicalLong(heap, base, 0xfffd), /long range/);
  assert.throws(() => readLogicalByte(heap, base, -1), /byte range/);
  assert.throws(() => readLogicalByte(heap, heap.length - 10, 0), /byte range/);
  tests++;

  const stateHeap = new Uint8Array(0x10000 + 32);
  const stateBase = 8;
  // Contract fixture uses literal logical addresses, independently of layout constants.
  // Distinct adjacent bytes catch accidental word reads and wrong byte offsets.
  stateHeap[stateBase + (0xf600 ^ 1)] = 0x08;
  stateHeap[stateBase + (0xf601 ^ 1)] = 0x99;
  stateHeap[stateBase + (0xf604 ^ 1)] = 0x08;
  stateHeap[stateBase + (0xf605 ^ 1)] = 0x10;
  stateHeap[stateBase + (0xf790 ^ 1)] = 0x12;
  stateHeap[stateBase + (0xf791 ^ 1)] = 0x34;
  stateHeap[stateBase + (0xf792 ^ 1)] = 0x56;
  stateHeap[stateBase + (0xf793 ^ 1)] = 0xaa;
  stateHeap[stateBase + (0xfff0 ^ 1)] = 0x00;
  stateHeap[stateBase + (0xfff1 ^ 1)] = 0x01;
  stateHeap[stateBase + (0xfff2 ^ 1)] = 0x00;
  stateHeap[stateBase + (0xfff3 ^ 1)] = 0x02;
  stateHeap[stateBase + (0xd000 ^ 1)] = 0x01;
  stateHeap[stateBase + (0xd008 ^ 1)] = 0x12;
  stateHeap[stateBase + (0xd009 ^ 1)] = 0x34;
  stateHeap[stateBase + (0xd00a ^ 1)] = 0x56;
  stateHeap[stateBase + (0xd00b ^ 1)] = 0x78;
  stateHeap[stateBase + (0xd00c ^ 1)] = 0x89;
  stateHeap[stateBase + (0xd00d ^ 1)] = 0xab;
  stateHeap[stateBase + (0xd00e ^ 1)] = 0xcd;
  stateHeap[stateBase + (0xd00f ^ 1)] = 0xef;
  stateHeap[stateBase + (0xd010 ^ 1)] = 0xff;
  stateHeap[stateBase + (0xd011 ^ 1)] = 0xfe;
  stateHeap[stateBase + (0xd012 ^ 1)] = 0x12;
  stateHeap[stateBase + (0xd013 ^ 1)] = 0x34;
  const before = Buffer.from(stateHeap.subarray(stateBase, stateBase + 0x10000));
  assert.deepEqual(readAttractFields(stateHeap, stateBase), {
    gameMode: 8, demoFlag: 1, demoLevelNumber: 2, demoCursor: 0x1234,
    demoCountdown: 0x56, heldPad: 0x08, pressedPad: 0x10,
    playerObjectId: 1, worldXFixed: 0x12345678, worldYFixed: 0x89abcdef,
    velocityX: -2, velocityY: 0x1234
  });
  assert.deepEqual(Buffer.from(stateHeap.subarray(stateBase, stateBase + 0x10000)), before,
    'diagnostic readers do not change work RAM');
  tests++;

  const playerAllocationOffset = 0x200 * 0x52 + 0x80 * 8 + 0x200 + 0x200 + 8 * 0x80 +
    0x1800 + 0x20 * 23 + 0x20 + 0x100 + 0x380 + 0x80;
  assert.equal(playerAllocationOffset, 0xd000,
    'v_objspace follows the source allocation sizes in _Variables.asm/_Constants.asm');
  assert.equal(PLAYER_LAYOUT.objectBase, playerAllocationOffset);
  assert.equal(PHASE_WINDOW.candidateTickCount, 596);
  assert.equal(TOOL_VERSION, 2);
  assert.equal(PROTOCOL_VERSION, 2);
  tests++;

  assert.equal(inputBufferIsZero(new Float32Array(32)), true);
  assert.equal(inputBufferIsZero(new Float32Array([0, 0, 1])), false);
  assert.equal(inputBufferIsZero(new Float32Array([0, NaN])), false);
  tests++;

  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'attract-profile-test-'));
  try {
    const fixture = makeFixturePackage(temp);
    assert.deepEqual(validateRomBuffer(fixture.rom, fixture.profile), {
      romLength: fixture.rom.length, romSHA256: fixture.profile.romSHA256
    });
    assert.equal(validateManifest({application: 'VRAMpage MD', application_version: '0.2.6',
      source_commit: 'c'.repeat(40), package_format: 1}, fixture.profile).application_version, '0.2.6');
    assert.equal(validateAppDirectory(fixture.app, fixture.profile).manifest.source_commit, 'c'.repeat(40));
    assert.throws(() => validateRomBuffer(Buffer.from([1,2]), fixture.profile), /length/);
    assert.throws(() => validateRomBuffer(Buffer.from([6,5,4,3,2,1]), fixture.profile), /SHA-256/);
    assert.throws(() => validateManifest({application: 'Other'}, fixture.profile), /manifest/);

    let coreLoaded = false;
    const loaded = await loadVerified({romPath: fixture.romPath, appDirectory: fixture.app,
      profile: fixture.profile, loadCore: async app => { coreLoaded = true; return app.coreJsPath; }});
    assert.equal(coreLoaded, true);
    assert.equal(loaded.app.manifest.application_version, '0.2.6');

    coreLoaded = false;
    fs.writeFileSync(path.join(fixture.app, 'site', 'build-info.json'), '{}');
    await assert.rejects(loadVerified({romPath: fixture.romPath, appDirectory: fixture.app,
      profile: fixture.profile, loadCore: async () => { coreLoaded = true; }}), /differ/);
    assert.equal(coreLoaded, false, 'core loader must not run before package verification');
    fs.writeFileSync(path.join(fixture.app, 'site', 'build-info.json'), fs.readFileSync(path.join(fixture.app, 'BUILD-INFO.json')));

    coreLoaded = false;
    fs.writeFileSync(path.join(fixture.app, 'VERSION'), '0.2.5\n');
    await assert.rejects(loadVerified({romPath: fixture.romPath, appDirectory: fixture.app,
      profile: fixture.profile, loadCore: async () => { coreLoaded = true; }}), /VERSION/);
    assert.equal(coreLoaded, false);
    fs.writeFileSync(path.join(fixture.app, 'VERSION'), '0.2.6\n');

    coreLoaded = false;
    const badROM = path.join(temp, 'wrong.bin');
    fs.writeFileSync(badROM, Buffer.from([6,5,4,3,2,1]));
    await assert.rejects(loadVerified({romPath: badROM, appDirectory: fixture.app,
      profile: fixture.profile, loadCore: async () => { coreLoaded = true; }}), /SHA-256/);
    assert.equal(coreLoaded, false);
    tests++;
  } finally { fs.rmSync(temp, {recursive: true, force: true}); }

  const eventLog = [];
  let factoryCount = 0;
  const timelineCallbacks = [];
  const baseline = await runTrial(async () => { factoryCount++; return fakeCore({events:eventLog}); },
    Buffer.from([1]), 'baseline', {onTimelineSample: row => {
      assert.equal(Object.isFrozen(row), true);
      assert.equal('HEAPU8' in row, false);
      timelineCallbacks.push(row.tick);
    }});
  assert.equal(factoryCount, 1);
  assert.deepEqual(baseline.samples.map(sample => sample.tick), [...TRIAL.sampleTicks]);
  assert.equal(baseline.externalInputZeroTicks, TRIAL.maxTicks);
  assert.equal(baseline.samples[0].gameMode, 8);
  assert.equal(baseline.samples[1].tick, 1800);
  assert.equal(baseline.samples[1].heldPad, 8);
  assert.equal(baseline.samples[1].pressedPad, 0);
  assert.equal(baseline.timeline.length, 602);
  assert.equal(timelineCallbacks.length, 602);
  assert.equal(baseline.timeline[0].tick, 1799);
  assert.equal(baseline.timeline.at(-1).tick, 2400);
  assert.equal(baseline.timelineSHA256.length, 64);
  assert.equal(JSON.stringify(serializeTrial(baseline)).includes('"timeline"'), false,
    'serialized trial summaries exclude internal timelines');
  assert.equal(JSON.stringify(baseline).includes('HEAPU8'), false);
  assert.equal(JSON.stringify(baseline).includes('romBytes'), false);
  assert.equal(JSON.stringify(baseline).includes('ramBytes'), false);
  tests++;

  const phaseBase = [];
  const phaseFields = tick => ({
    gameMode: 8, demoFlag: 1, demoLevelNumber: 1, demoCursor: tick,
    demoCountdown: tick % 256, heldPad: tick % 16, pressedPad: tick % 8,
    playerObjectId: 1, worldXFixed: tick * 0x10001, worldYFixed: tick * 0x10003,
    velocityX: tick - 2000, velocityY: 2000 - tick
  });
  for (let tick = 1799; tick <= 2400; tick++) {
    phaseBase.push({tick, rawActiveFrameSHA256: `frame-${tick}`, ...phaseFields(tick)});
  }
  for (let intendedLag = -2; intendedLag <= 2; intendedLag++) {
    const shifted = phaseBase.map(row => ({
      tick: row.tick, rawActiveFrameSHA256: `frame-${row.tick + intendedLag}`,
      ...phaseFields(row.tick + intendedLag)
    }));
    const comparisons = comparePhases(phaseBase, shifted);
    assert.equal(comparisons.length, 5);
    const exact = comparisons.find(result => result.lag === intendedLag);
    assert.equal(exact.comparedPairs, 596);
    assert.equal(exact.missingPairs, 0);
    assert.equal(exact.rawActiveFrameMatches, 596);
    assert.equal(exact.demoStateMatches, 596);
    assert.equal(exact.playerStateMatches, 596);
    assert.equal(exact.allMatches, 596);
    assert(comparisons.filter(result => result.lag !== intendedLag)
      .every(result => result.allMatches < 596));
  }
  const playerChanged = phaseBase.map(row => ({...row, worldXFixed: row.worldXFixed + 1}));
  const playerComparison = comparePhases(phaseBase, playerChanged).find(result => result.lag === 0);
  assert.equal(playerComparison.rawActiveFrameMatches, 596);
  assert.equal(playerComparison.demoStateMatches, 596);
  assert.equal(playerComparison.playerStateMatches, 0);
  assert.equal(playerComparison.allMatches, 0);
  const demoChanged = phaseBase.map(row => ({...row, demoCountdown: row.demoCountdown ^ 1}));
  const demoComparison = comparePhases(phaseBase, demoChanged).find(result => result.lag === 0);
  assert.equal(demoComparison.playerStateMatches, 596);
  assert.equal(demoComparison.demoStateMatches, 0);
  assert.equal(demoComparison.allMatches, 0);
  const shiftedMinusTwo = phaseBase.map(row => ({
    tick: row.tick, rawActiveFrameSHA256: `frame-${row.tick - 2}`,
    ...phaseFields(row.tick - 2)
  }));
  const missingBoundary = comparePhases(phaseBase.filter(row => row.tick !== 1801), shiftedMinusTwo)
    .find(result => result.lag === -2);
  assert.equal(missingBoundary.comparedPairs, 595);
  assert.equal(missingBoundary.missingPairs, 1);
  const missingCandidate = comparePhases(phaseBase, shiftedMinusTwo.filter(row => row.tick !== 1803));
  assert(missingCandidate.every(result => result.missingPairs === 1));
  tests++;

  const ordinaryEvents = [];
  const ordinary = await runTrial(async () => fakeCore({events:ordinaryEvents}), Buffer.from([1]), 'D0D1-read');
  const event1801 = ordinaryEvents.slice(ordinaryEvents.findIndex(e => e[0] === 'ordinaryFault'),
    ordinaryEvents.findIndex((e, i) => i > ordinaryEvents.findIndex(x => x[0] === 'ordinaryFault') && e[0] === 'sound'));
  assert.deepEqual(event1801[0], ['ordinaryFault', 1800, 2, 1, 0, 1]);
  assert.equal(ordinary.faultSetterFrame, 1800);
  assert.equal(ordinary.effectiveFaultTick, 1801);
  assert.equal(ordinary.reportedActivationFrame, 1800);
  assert.equal(ordinary.samples.find(s => s.tick === 1801).faultReads, 1);
  tests++;

  const pulseEvents = [];
  const pulse = await runTrial(async () => fakeCore({events:pulseEvents}), Buffer.from([1]), 'A10A11-one-write');
  const pulseApply = pulseEvents.find(e => e[0] === 'pulseFault');
  assert.deepEqual(pulseApply, ['pulseFault', 1800, 1, 9, 10, 1]);
  assert.deepEqual(pulse.pulse, {requestedAffectedWrites:1, finalCoreState:2, releaseTick:1801,
    affectedWritesAtRelease:1, releaseReason:'affected-write-limit'});
  assert.equal(pulse.samples.find(s => s.tick === 1801).cpuFlags, 0);
  assert.equal(pulse.samples.find(s => s.tick === 1801).corePulseState, 2);
  assert.equal('recover' in pulse, false, 'observer never resumes or resets the CPU');
  assert.equal(prefaultMatches(baseline, ordinary), true);
  assert.equal(prefaultMatches(baseline, pulse), true,
    'baseline and pulse share the observed pre-fault pulse state');
  const changedPrefault = structuredClone(pulse);
  changedPrefault.samples.find(s => s.tick === 1800).demoCountdown ^= 1;
  assert.equal(prefaultMatches(baseline, changedPrefault), false,
    'a changed pre-fault sample must break the comparison');
  assert.equal(sameTrials(baseline, await runTrial(async () => fakeCore(), Buffer.from([1]), 'baseline')), true);
  const noWritePulse = await runTrial(async () => fakeCore({pulseWrite:false}), Buffer.from([1]), 'A10A11-one-write');
  assert.equal(noWritePulse.pulse.finalCoreState, 3);
  assert.equal(noWritePulse.pulse.releaseReason, 'frame-limit');
  tests++;

  assert.equal(APP_PROFILE.applicationVersion, '0.2.6');
  assert.equal(APP_PROFILE.romSHA256.length, 64);
  assert.equal(TRIAL.maxTicks, 2400);
  console.log(`Attract diagnostic protocol: ${tests} test groups passed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
