#!/usr/bin/env node
/* Bounded Sonic 1 demo-state observer; emits scalar summaries and hashes only. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');

const TOOL_VERSION = 2;
const PROTOCOL_VERSION = 2;
const APP_PROFILE = Object.freeze({
  application: 'VRAMpage MD', applicationVersion: '0.2.6', packageFormat: 1,
  packageSourceCommit: '6d18f8e80191f1d60e5aa7b5899d3524c6dcbc07',
  corePin: '6090aff9e9b2f578cd28882bd4571d2e35b1d674',
  javascriptSHA256: '700f1b809687c5004486c7bf0a5b2ae5f94c586fee714235eec2003c2eded5b5',
  wasmSHA256: '79c1fa077e16e281697af78751702bddb180021cd3e419492589c2944da6d2e0',
  romLength: 524288,
  romSHA256: '46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6'
});

// s1disasm AS @ 15dfa3a6ee4c53aeb482233e493755c84b4f3479.
// v_gamemode and pad states are bytes; v_btnpushtime2 is operated on as a
// byte at the word's logical base ($F792); LSB_FIRST stores it physically at
// RAM+$F793 through the byte-lane XOR. v_btnpushtime1 is a word.
const SONIC1_LAYOUT = Object.freeze({
  gameMode: 0xf600,
  heldPad: 0xf604,
  pressedPad: 0xf605,
  demoCursor: 0xf790,
  demoCountdown: 0xf792,
  demoFlag: 0xfff0,
  demoLevelNumber: 0xfff2
});
// s1disasm AS @ 15dfa3a6ee4c53aeb482233e493755c84b4f3479:
// _Variables.asm allocates v_objspace after byte regions totaling
// $A400+$400+$200+$200+$400+$1800+$2E0+$20+$100+$380+$80 = $D000;
// v_player is object slot 0. _Constants.asm defines object_size=$40 and the
// player fields below. obX/obY are 16.16 fixed-point longs; obVelX/obVelY
// are signed 16-bit words. LSB_FIRST byte lanes are resolved by the readers.
const PLAYER_LAYOUT = Object.freeze({
  objectBase: 0xd000,
  objectId: 0x00,
  worldXFixed: 0x08,
  worldYFixed: 0x0c,
  velocityX: 0x10,
  velocityY: 0x12
});
const PHASE_WINDOW = Object.freeze({
  candidateTickStart: 1803,
  candidateTickEnd: 2398,
  candidateTickCount: 596,
  lagMin: -2,
  lagMax: 2,
  offsetConvention: 'compare candidate tick t with baseline tick t + lag'
});
const TRIAL = Object.freeze({
  maxTicks: 2400,
  faultTick: 1801,
  sampleTicks: Object.freeze([1799, 1800, 1801, 1860, 1920, 2100, 2400]),
  scenarios: Object.freeze({
    baseline: null,
    'D0D1-read': Object.freeze({type: 'ordinary', args: Object.freeze([2, 1, 0, 1])}),
    'A10A11-one-write': Object.freeze({type: 'writePulse', args: Object.freeze([1, 9, 10, 1])})
  })
});
const CONFIGURED_WRITE_PULSE_LIMITS = Object.freeze({faultTick: 1801, maxTicks: 2400});

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function fail(message) { throw new Error(message); }

function validateRomBuffer(rom, profile = APP_PROFILE) {
  if (!(Buffer.isBuffer(rom) || rom instanceof Uint8Array)) fail('ROM input must be bytes.');
  if (rom.byteLength !== profile.romLength) fail('ROM length does not match the supported Sonic 1 profile.');
  const actual = sha256(rom);
  if (actual !== profile.romSHA256) fail('ROM SHA-256 does not match the supported Sonic 1 profile.');
  return {romLength: rom.byteLength, romSHA256: actual};
}

function readJSON(file, label) {
  let parsed;
  try { parsed = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (error) { fail(`${label} is missing or invalid JSON: ${error.message}`); }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) fail(`${label} must be a JSON object.`);
  return parsed;
}

function validateManifest(manifest, profile = APP_PROFILE) {
  if (manifest.application !== profile.application ||
      manifest.application_version !== profile.applicationVersion ||
      manifest.package_format !== profile.packageFormat ||
      manifest.source_commit !== profile.packageSourceCommit) {
    fail('Application build manifest does not match the supported v0.2.6 package profile.');
  }
  return manifest;
}

function validateAppDirectory(appDirectory, profile = APP_PROFILE) {
  const appRoot = path.resolve(appDirectory);
  const rootManifestPath = path.join(appRoot, 'BUILD-INFO.json');
  const siteManifestPath = path.join(appRoot, 'site', 'build-info.json');
  let rootManifestBytes, siteManifestBytes;
  try {
    rootManifestBytes = fs.readFileSync(rootManifestPath);
    siteManifestBytes = fs.readFileSync(siteManifestPath);
  } catch (error) { fail(`Application package manifests are missing: ${error.message}`); }
  if (!rootManifestBytes.equals(siteManifestBytes)) fail('Application package manifests differ.');
  const manifest = validateManifest(readJSON(rootManifestPath, 'BUILD-INFO.json'), profile);
  let version;
  try { version = fs.readFileSync(path.join(appRoot, 'VERSION'), 'utf8').trim(); }
  catch (error) { fail(`Application VERSION is missing: ${error.message}`); }
  if (version !== profile.applicationVersion) fail('Application VERSION does not match its manifest.');

  const coreJsPath = path.join(appRoot, 'site', 'core', 'genplus.js');
  const coreWasmPath = path.join(appRoot, 'site', 'core', 'genplus.wasm');
  let jsBytes, wasmBytes;
  try {
    jsBytes = fs.readFileSync(coreJsPath);
    wasmBytes = fs.readFileSync(coreWasmPath);
  } catch (error) { fail(`Application core files are missing: ${error.message}`); }
  const javascriptSHA256 = sha256(jsBytes);
  const wasmSHA256 = sha256(wasmBytes);
  if (javascriptSHA256 !== profile.javascriptSHA256 || wasmSHA256 !== profile.wasmSHA256) {
    fail('Application core hashes do not match the supported v0.2.6 package profile.');
  }
  if (wasmBytes.length < 4 || !wasmBytes.subarray(0, 4).equals(Buffer.from([0, 0x61, 0x73, 0x6d]))) {
    fail('Application WebAssembly core has an invalid binary signature.');
  }
  return {appRoot, manifest, coreJsPath, coreWasmPath, javascriptSHA256, wasmSHA256};
}

function readLogicalByte(heap, ramPointer, logicalAddress) {
  if (!(heap instanceof Uint8Array) || !Number.isSafeInteger(ramPointer) || ramPointer < 0 ||
      !Number.isInteger(logicalAddress) || logicalAddress < 0 || logicalAddress > 0xffff ||
      ramPointer + 0x10000 > heap.length) fail('Invalid logical work-RAM byte range.');
  // The fixed, hash-verified WebAssembly build is LSB_FIRST: 68K byte lane a is at a^1.
  return heap[ramPointer + (logicalAddress ^ 1)];
}

function readLogicalWord(heap, ramPointer, logicalAddress) {
  if (!Number.isInteger(logicalAddress) || logicalAddress < 0 || logicalAddress >= 0xffff) {
    fail('Invalid logical work-RAM word range.');
  }
  return (readLogicalByte(heap, ramPointer, logicalAddress) << 8) |
    readLogicalByte(heap, ramPointer, logicalAddress + 1);
}

function readLogicalLong(heap, ramPointer, logicalAddress) {
  if (!Number.isInteger(logicalAddress) || logicalAddress < 0 || logicalAddress > 0xfffc) {
    fail('Invalid logical work-RAM long range.');
  }
  return (readLogicalWord(heap, ramPointer, logicalAddress) * 0x10000 +
    readLogicalWord(heap, ramPointer, logicalAddress + 2)) >>> 0;
}

function readLogicalSignedWord(heap, ramPointer, logicalAddress) {
  const value = readLogicalWord(heap, ramPointer, logicalAddress);
  return value >= 0x8000 ? value - 0x10000 : value;
}

function readAttractFields(heap, ramPointer) {
  const player = PLAYER_LAYOUT.objectBase;
  return {
    gameMode: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.gameMode),
    demoFlag: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoFlag),
    demoLevelNumber: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoLevelNumber),
    demoCursor: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoCursor),
    demoCountdown: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.demoCountdown),
    heldPad: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.heldPad),
    pressedPad: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.pressedPad),
    playerObjectId: readLogicalByte(heap, ramPointer, player + PLAYER_LAYOUT.objectId),
    worldXFixed: readLogicalLong(heap, ramPointer, player + PLAYER_LAYOUT.worldXFixed),
    worldYFixed: readLogicalLong(heap, ramPointer, player + PLAYER_LAYOUT.worldYFixed),
    velocityX: readLogicalSignedWord(heap, ramPointer, player + PLAYER_LAYOUT.velocityX),
    velocityY: readLogicalSignedWord(heap, ramPointer, player + PLAYER_LAYOUT.velocityY)
  };
}

function inputBufferIsZero(input) {
  if (!input || typeof input.length !== 'number') fail('Invalid external input buffer.');
  for (let index = 0; index < input.length; index++) if (input[index] !== 0) return false;
  return true;
}

function updateAggregate(hash, fields) {
  const row = Buffer.alloc(10);
  row[0] = fields.gameMode;
  row.writeUInt16BE(fields.demoFlag, 1);
  row.writeUInt16BE(fields.demoLevelNumber, 3);
  row.writeUInt16BE(fields.demoCursor, 5);
  row[7] = fields.demoCountdown;
  row[8] = fields.heldPad;
  row[9] = fields.pressedPad;
  hash.update(row);
}

function hashRawActiveFrame(core) {
  const heap = core.HEAPU8;
  const pointer = core._get_frame_buffer_ref();
  const lastByte = pointer + ((224 - 1) * 640 + 320) * 4;
  if (!Number.isSafeInteger(pointer) || pointer < 0 || lastByte > heap.length) fail('Invalid framebuffer range.');
  const hash = crypto.createHash('sha256');
  for (let y = 0; y < 224; y++) {
    const row = pointer + y * 640 * 4;
    hash.update(heap.subarray(row, row + 320 * 4));
  }
  return hash.digest('hex');
}

function demoTuple(fields) {
  return [fields.gameMode, fields.demoFlag, fields.demoLevelNumber, fields.demoCursor,
    fields.demoCountdown, fields.heldPad, fields.pressedPad];
}

function playerTuple(fields) {
  return [fields.playerObjectId, fields.worldXFixed, fields.worldYFixed,
    fields.velocityX, fields.velocityY];
}

function comparePhases(baselineTimeline, candidateTimeline) {
  const baselineByTick = new Map(baselineTimeline.map(row => [row.tick, row]));
  const candidateByTick = new Map(candidateTimeline.map(row => [row.tick, row]));
  const results = [];
  for (let lag = PHASE_WINDOW.lagMin; lag <= PHASE_WINDOW.lagMax; lag++) {
    const counts = {candidateTicks: PHASE_WINDOW.candidateTickCount, comparedPairs: 0, missingPairs: 0,
      rawActiveFrameMatches: 0, demoStateMatches: 0, playerStateMatches: 0, allMatches: 0};
    for (let tick = PHASE_WINDOW.candidateTickStart; tick <= PHASE_WINDOW.candidateTickEnd; tick++) {
      const candidate = candidateByTick.get(tick);
      const baseline = baselineByTick.get(tick + lag);
      if (!candidate || !baseline) { counts.missingPairs++; continue; }
      counts.comparedPairs++;
      const frameMatch = candidate.rawActiveFrameSHA256 === baseline.rawActiveFrameSHA256;
      const demoMatch = JSON.stringify(demoTuple(candidate)) === JSON.stringify(demoTuple(baseline));
      const playerMatch = JSON.stringify(playerTuple(candidate)) === JSON.stringify(playerTuple(baseline));
      if (frameMatch) counts.rawActiveFrameMatches++;
      if (demoMatch) counts.demoStateMatches++;
      if (playerMatch) counts.playerStateMatches++;
      if (frameMatch && demoMatch && playerMatch) counts.allMatches++;
    }
    results.push({lag, ...counts});
  }
  return results;
}

function requireCoreAPI(core, scenario, configuredWritePulse = false) {
  const names = ['_init', '_start', '_tick', '_sound', '_wasm_input_update',
    '_get_rom_buffer_ref', '_get_input_buffer_ref', '_get_frame_buffer_ref',
    '_get_logic_ram_ref', '_get_logic_frame', '_get_logic_reads', '_get_logic_writes',
    '_get_logic_cpu_flags', '_get_logic_activation_frame', '_get_logic_pulse_state'];
  if (scenario !== 'baseline' && !configuredWritePulse) names.push('_set_logic_fault');
  if (scenario === 'A10A11-one-write' || configuredWritePulse) names.push('_arm_logic_write_pulse');
  for (const name of names) if (typeof core[name] !== 'function') fail(`Core API missing ${name}.`);
  if (!(core.HEAPU8 instanceof Uint8Array)) fail('Core API missing HEAPU8.');
}

function validateConfiguredWritePulse(spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) fail('A named write-pulse specification is required.');
  const {name, kind, lineA, lineB, affectedWrites, faultTick, maxTicks} = spec;
  if (typeof name !== 'string' || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(name)) fail('Invalid configured trial name.');
  if (['baseline', 'D0D1-read', 'A10A11-one-write'].includes(name)) fail('Configured trial name is reserved.');
  if (kind !== 1 && kind !== 2) fail('Configured write-pulse kind must be address (1) or data (2).');
  const lineLimit = kind === 1 ? 15 : 16;
  if (!Number.isInteger(lineA) || lineA < 0 || lineA >= lineLimit ||
      !Number.isInteger(lineB) || lineB < 0 || lineB >= lineLimit || lineA === lineB) {
    fail('Configured write-pulse lines are invalid for their fault kind.');
  }
  if (!Number.isSafeInteger(affectedWrites) || affectedWrites < 1 || affectedWrites > 1024) {
    fail('Configured write-pulse budget must be an integer from 1 through 1024.');
  }
  if (faultTick !== CONFIGURED_WRITE_PULSE_LIMITS.faultTick ||
      maxTicks !== CONFIGURED_WRITE_PULSE_LIMITS.maxTicks) {
    fail('Configured write-pulse timing must use tick 1801 and a 2400 tick bound.');
  }
  return Object.freeze({name, kind, lineA, lineB, affectedWrites, faultTick, maxTicks,
    type: 'writePulse', args: Object.freeze([kind, lineA, lineB, affectedWrites])});
}

async function executeTrial(coreFactory, rom, scenario, faultConfig,
                            {onTimelineSample, collectSafety = false} = {}) {
  const core = await coreFactory();
  const isWritePulse = faultConfig?.type === 'writePulse';
  requireCoreAPI(core, scenario, isWritePulse);
  core._init();
  const romPointer = core._get_rom_buffer_ref(rom.length);
  if (!Number.isSafeInteger(romPointer) || romPointer <= 0 || romPointer + rom.length > core.HEAPU8.length) {
    fail('Core refused the supported cartridge buffer.');
  }
  core.HEAPU8.set(rom, romPointer);
  core._start();
  const inputPointer = core._get_input_buffer_ref();
  if (!Number.isSafeInteger(inputPointer) || inputPointer < 0 ||
      inputPointer + 32 * Float32Array.BYTES_PER_ELEMENT > core.HEAPU8.length) fail('Invalid external input buffer range.');
  const input = new Float32Array(core.HEAPU8.buffer, inputPointer, 32);
  const streamHash = crypto.createHash('sha256');
  const preFaultHash = crypto.createHash('sha256');
  const samples = [];
  const timeline = [];
  const timelineHash = crypto.createHash('sha256');
  let externalInputZeroTicks = 0;
  let cursorValueChanges = 0;
  let heldPadValueChanges = 0;
  let previous = null;
  let faultSetterFrame = null;
  let effectiveFaultTick = null;
  let reportedActivationFrame = null;
  let pulseStateAtEnd = null;
  let pulseReleaseTick = null;
  let affectedWritesAtRelease = null;
  let cpuStopTicks = 0;
  let cpuHaltTicks = 0;
  let cpuNonzeroTicks = 0;
  let demoActiveTicks = 0;
  let postFaultCursorValueChanges = 0;
  let postFaultHeldPadValueChanges = 0;
  let postFaultPressedPadValueChanges = 0;
  let playerObjectIdOneTimelineTicks = 0;
  let postFaultPrevious = null;
  for (let tick = 1; tick <= TRIAL.maxTicks; tick++) {
    if (faultConfig && tick === (faultConfig.faultTick ?? TRIAL.faultTick)) {
      faultSetterFrame = core._get_logic_frame();
      if (faultSetterFrame !== 1800) fail(`Fault timing expected core frame 1800, got ${faultSetterFrame}.`);
      const status = isWritePulse
        ? core._arm_logic_write_pulse(...faultConfig.args)
        : core._set_logic_fault(...faultConfig.args);
      if (status !== 0) fail(`Core rejected ${scenario} with status ${status}.`);
      reportedActivationFrame = core._get_logic_activation_frame();
      effectiveFaultTick = tick;
    }
    input.fill(0);
    const externalZeroThisTick = inputBufferIsZero(input);
    if (externalZeroThisTick) externalInputZeroTicks++;
    core._wasm_input_update();
    core._tick();
    const coreFrame = core._get_logic_frame();
    if (coreFrame !== tick) fail(`Core frame mismatch at tick ${tick}: reported ${coreFrame}.`);
    const audioSamples = core._sound();
    if (!Number.isSafeInteger(audioSamples) || audioSamples < 0) fail('Invalid audio sample count.');

    const fields = readAttractFields(core.HEAPU8, core._get_logic_ram_ref());
    if (collectSafety && tick >= 1799 && tick <= 2400 && fields.playerObjectId === 1) {
      playerObjectIdOneTimelineTicks++;
    }
    if (collectSafety && tick > TRIAL.faultTick) {
      const flags = core._get_logic_cpu_flags();
      if (flags !== 0) cpuNonzeroTicks++;
      if (flags & 1) cpuStopTicks++;
      if (flags & 2) cpuHaltTicks++;
      if (fields.gameMode === 8 && fields.demoFlag === 1) demoActiveTicks++;
      if (postFaultPrevious) {
        if (fields.demoCursor !== postFaultPrevious.demoCursor) postFaultCursorValueChanges++;
        if (fields.heldPad !== postFaultPrevious.heldPad) postFaultHeldPadValueChanges++;
        if (fields.pressedPad !== postFaultPrevious.pressedPad) postFaultPressedPadValueChanges++;
      }
      postFaultPrevious = fields;
    }
    updateAggregate(streamHash, fields);
    if (tick < TRIAL.faultTick) updateAggregate(preFaultHash, fields);
    if (previous) {
      if (fields.demoCursor !== previous.demoCursor) cursorValueChanges++;
      if (fields.heldPad !== previous.heldPad) heldPadValueChanges++;
    }
    previous = fields;
    const corePulseState = core._get_logic_pulse_state();
    if (isWritePulse) {
      pulseStateAtEnd = corePulseState;
      if (pulseReleaseTick === null && (corePulseState === 2 || corePulseState === 3)) {
        pulseReleaseTick = tick;
        affectedWritesAtRelease = core._get_logic_writes();
      }
    }
    const inTimeline = tick >= 1799 && tick <= 2400;
    if (TRIAL.sampleTicks.includes(tick) || inTimeline) {
      const rawActiveFrameSHA256 = hashRawActiveFrame(core);
      if (inTimeline) {
        const row = Object.freeze({tick, rawActiveFrameSHA256, ...fields});
        timeline.push(row);
        timelineHash.update(JSON.stringify(row));
        timelineHash.update('\n');
        if (onTimelineSample) onTimelineSample(row);
      }
      if (TRIAL.sampleTicks.includes(tick)) {
        samples.push({
          tick, coreFrame,
          rawActiveFrameSHA256,
          faultReads: core._get_logic_reads(), faultWrites: core._get_logic_writes(),
          cpuFlags: core._get_logic_cpu_flags(), corePulseState,
          externalInputZeroThisTick: externalZeroThisTick,
          ...fields
        });
      }
    }
  }
  const result = {
    scenario, ticks: TRIAL.maxTicks,
    faultSetterFrame, effectiveFaultTick, reportedActivationFrame,
    externalInputZeroTicks, cursorValueChanges, heldPadValueChanges,
    streamSHA256: streamHash.digest('hex'),
    preFaultStreamSHA256: preFaultHash.digest('hex'),
    timelineSHA256: timelineHash.digest('hex'),
    pulse: isWritePulse ? {
      requestedAffectedWrites: faultConfig.args[3], finalCoreState: pulseStateAtEnd, releaseTick: pulseReleaseTick,
      affectedWritesAtRelease,
      releaseReason: pulseStateAtEnd === 2 ? 'affected-write-limit' :
        pulseStateAtEnd === 3 ? 'frame-limit' : 'still-active-or-unknown'
    } : null,
    samples,
    timeline
  };
  if (collectSafety) result.safety = {cpuStopTicks, cpuHaltTicks, cpuNonzeroTicks, demoActiveTicks,
    postFaultCursorValueChanges, postFaultHeldPadValueChanges, postFaultPressedPadValueChanges,
    playerObjectIdOneTimelineTicks};
  return result;
}

async function runTrial(coreFactory, rom, scenario, options = {}) {
  if (!Object.hasOwn(TRIAL.scenarios, scenario)) fail(`Unknown trial scenario: ${scenario}`);
  return executeTrial(coreFactory, rom, scenario, TRIAL.scenarios[scenario], options);
}

async function runConfiguredWritePulseTrial(coreFactory, rom, spec, options = {}) {
  const config = validateConfiguredWritePulse(spec);
  return executeTrial(coreFactory, rom, config.name, config, options);
}

function sameTrials(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function serializeTrial(trial) {
  const {timeline, ...summary} = trial;
  return summary;
}

function prefaultMatches(baseline, candidate) {
  const baselineSamples = baseline.samples.filter(sample => sample.tick < TRIAL.faultTick);
  const candidateSamples = candidate.samples.filter(sample => sample.tick < TRIAL.faultTick);
  return baseline.preFaultStreamSHA256 === candidate.preFaultStreamSHA256 &&
    JSON.stringify(baselineSamples) === JSON.stringify(candidateSamples);
}

function toolIdentity() {
  let sourceCommit = null;
  let sourceDirty = null;
  try {
    const sourceRoot = execFileSync('git', ['-C', __dirname, 'rev-parse', '--show-toplevel'], {encoding: 'utf8'}).trim();
    sourceCommit = execFileSync('git', ['-C', sourceRoot, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim();
    const relativeTool = path.relative(sourceRoot, __filename);
    const status = execFileSync('git', ['-C', sourceRoot, 'status', '--porcelain', '--untracked-files=all', '--', relativeTool], {encoding: 'utf8'});
    sourceDirty = status.trim().length > 0;
  } catch (_) { /* A copied standalone tool has no Git identity. */ }
  return {version: TOOL_VERSION, sha256: sha256(fs.readFileSync(__filename)), sourceCommit, sourceDirty};
}

async function loadVerified({romPath, appDirectory, profile = APP_PROFILE, loadCore}) {
  if (typeof loadCore !== 'function') fail('A core loader is required.');
  let rom;
  try { rom = fs.readFileSync(romPath); }
  catch (error) { fail(`Cannot read local cartridge: ${error.message}`); }
  const romIdentity = validateRomBuffer(rom, profile);
  const app = validateAppDirectory(appDirectory, profile);
  const coreFactory = await loadCore(app);
  return {rom, romIdentity, app, coreFactory};
}

function parseArgs(argv) {
  if (argv.length === 1 && (argv[0] === '--help' || argv[0] === '-h')) return {help: true};
  if (argv.length !== 3 || argv[1] !== '--app') {
    fail('Usage: node scripts/observe-attract-demo.cjs /private/path/sonic.md --app /path/to/extracted/VRAMpage-MD');
  }
  return {romPath: path.resolve(argv[0]), appDirectory: path.resolve(argv[2])};
}

async function main(argv) {
  const args = parseArgs(argv);
  if (args.help) {
    process.stdout.write('Usage: node scripts/observe-attract-demo.cjs /private/path/sonic.md --app /path/to/extracted/VRAMpage-MD\n');
    return;
  }
  const verified = await loadVerified({...args, loadCore: async app => {
    // Executable JS is loaded only after ROM, manifests, app version and core hashes pass.
    const moduleFactory = require(app.coreJsPath);
    return () => moduleFactory({locateFile: name => path.join(path.dirname(app.coreJsPath), name)});
  }});
  const factories = [];
  const freshFactory = () => {
    const factory = verified.coreFactory;
    factories.push(true);
    return factory();
  };
  const runs = {};
  for (const scenario of Object.keys(TRIAL.scenarios)) {
    const first = await runTrial(freshFactory, verified.rom, scenario);
    const repeat = await runTrial(freshFactory, verified.rom, scenario);
    runs[scenario] = {
      first, repeat,
      repeatIdentical: sameTrials(first, repeat),
      prefaultMatchesBaseline: scenario === 'baseline' ? null :
        prefaultMatches(runs.baseline.first, first) && prefaultMatches(runs.baseline.first, repeat)
    };
  }
  const serializedRuns = Object.fromEntries(Object.entries(runs).map(([scenario, run]) => [scenario, {
    first: serializeTrial(run.first), repeat: serializeTrial(run.repeat),
    repeatIdentical: run.repeatIdentical,
    prefaultMatchesBaseline: run.prefaultMatchesBaseline
  }]));
  const phaseComparisons = Object.fromEntries(Object.keys(TRIAL.scenarios)
    .filter(scenario => scenario !== 'baseline')
    .map(scenario => [scenario, {
      first: comparePhases(runs.baseline.first.timeline, runs[scenario].first.timeline),
      repeat: comparePhases(runs.baseline.first.timeline, runs[scenario].repeat.timeline)
    }]));
  const tool = toolIdentity();
  const output = {
    schemaVersion: 2,
    protocolVersion: PROTOCOL_VERSION,
    modelVersion: '0.2.6-experimental',
    tool,
    runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    package: {
      applicationVersion: verified.app.manifest.application_version,
      sourceCommit: verified.app.manifest.source_commit,
      corePin: APP_PROFILE.corePin,
      javascriptSHA256: verified.app.javascriptSHA256,
      wasmSHA256: verified.app.wasmSHA256,
      playerProfile: {
        sourceProject: 'sonicretro/s1disasm',
        sourceCommit: '15dfa3a6ee4c53aeb482233e493755c84b4f3479',
        sourceFiles: ['_Variables.asm', '_Constants.asm'],
        playerObjectBase: PLAYER_LAYOUT.objectBase,
        positionEncoding: 'unsigned 16.16 fixed-point',
        velocityEncoding: 'signed 16-bit 68K word'
      }
    },
    cartridge: verified.romIdentity,
    settings: {
      externalInputBufferLength: 32,
      tickLimit: TRIAL.maxTicks,
      sampleTicks: TRIAL.sampleTicks,
      timeline: {
        tickStart: 1799, tickEnd: 2400, tickCount: 602,
        includes: ['rawActiveFrameSHA256', 'demoFields', 'playerFields'],
        serialized: false
      },
      phaseComparison: PHASE_WINDOW,
      faults: {
        'D0D1-read': {setterFrame: 1800, effectiveTick: 1801, kind: 'data', access: 'read', lines: ['D0', 'D1']},
        'A10A11-one-write': {setterFrame: 1800, effectiveTick: 1801, kind: 'address', lines: ['A10', 'A11'], requestedAffectedWrites: 1}
      },
      cpuRecovery: 'none'
    },
    freshCoreTrials: factories.length,
    runs: serializedRuns,
    phaseComparisons
  };
  process.stdout.write(JSON.stringify(output, null, 2) + '\n');
}

if (require.main === module) {
  main(process.argv.slice(2)).catch(error => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  TOOL_VERSION, PROTOCOL_VERSION, APP_PROFILE, SONIC1_LAYOUT, PLAYER_LAYOUT, PHASE_WINDOW, TRIAL,
  inputBufferIsZero, readAttractFields, readLogicalByte, readLogicalWord, readLogicalLong, readLogicalSignedWord,
  comparePhases, serializeTrial, prefaultMatches, runTrial, runConfiguredWritePulseTrial,
  validateConfiguredWritePulse, sameTrials, CONFIGURED_WRITE_PULSE_LIMITS,
  validateAppDirectory, validateManifest, validateRomBuffer, loadVerified
};
