#!/usr/bin/env node
'use strict';
// Developer-only protocol: compare a single RAM alias write and per-tick audio.
// Raw audio, RAM, ROM, frame pixels and timelines are never serialized.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const observer = require('./observe-attract-demo.cjs');

const TOOL_VERSION = 1;
const PROTOCOL_VERSION = 1;
const APP_PROFILE = Object.freeze({
  application: 'VRAMpage MD', applicationVersion: '0.2.7', packageFormat: 1,
  packageSourceCommit: '1d87fd9a921194a557fc5320e54be48295c62b1f',
  javascriptSHA256: '3b984104bf92fd9e7a47fa5f081ed18d020e61dee6cd87df7580c147a3edc3bd',
  wasmSHA256: '86b1086cc33091542bf2b866984b0cd3a541143448258a1a5e49abe846621f42',
  romLength: 524288,
  romSHA256: '46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6'
});
const AUDIO = Object.freeze({capacity: 2048});
const STATE_LAYOUT = Object.freeze({
  vBlankRoutine: 0xf62a,
  sfxFm3TrackAMSFMSPan: 0xf22a,
  spriteBufferByte: 0xf84a
});
const SOURCE_LAYOUT = Object.freeze({project: 'sonicretro/s1disasm',
  commit: '15dfa3a6ee4c53aeb482233e493755c84b4f3479',
  files: ['_Variables.asm', 's1.sounddriver.ram.asm'],
  mapping: 'v_vblank_routine at $F62A; v_sfx_fm3_track.AMSFMSPan at $F22A; sprite buffer starts at $F800'});
const OFFSETS = Object.freeze([-2, -1, 0, 1, 2]);
const SCENARIOS = Object.freeze(['baseline', 'A10A11-one-write']);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function fail(message) { throw new Error(message); }

function validateAppDirectory(directory, profile = APP_PROFILE) {
  const appRoot = path.resolve(directory);
  const rootPath = path.join(appRoot, 'BUILD-INFO.json');
  const sitePath = path.join(appRoot, 'site/build-info.json');
  const rootBytes = fs.readFileSync(rootPath);
  if (!rootBytes.equals(fs.readFileSync(sitePath))) fail('Package manifests differ.');
  const manifest = JSON.parse(rootBytes);
  if (manifest.application !== profile.application ||
      manifest.application_version !== profile.applicationVersion ||
      manifest.package_format !== profile.packageFormat ||
      manifest.source_commit !== profile.packageSourceCommit ||
      fs.readFileSync(path.join(appRoot, 'VERSION'), 'utf8').trim() !== profile.applicationVersion) {
    fail('Package does not match the pinned public v0.2.7 profile.');
  }
  const coreJsPath = path.join(appRoot, 'site/core/genplus.js');
  const coreWasmPath = path.join(appRoot, 'site/core/genplus.wasm');
  const jsBytes = fs.readFileSync(coreJsPath);
  const wasmBytes = fs.readFileSync(coreWasmPath);
  const javascriptSHA256 = sha256(jsBytes), wasmSHA256 = sha256(wasmBytes);
  if (javascriptSHA256 !== profile.javascriptSHA256 || wasmSHA256 !== profile.wasmSHA256 ||
      !wasmBytes.subarray(0, 4).equals(Buffer.from([0, 97, 115, 109]))) fail('Package core hashes/signature do not match the pinned public v0.2.7 profile.');
  return {appRoot, manifest, coreJsPath, javascriptSHA256, wasmSHA256};
}

function hashFloatSamples(heap, pointer, count, capacity = AUDIO.capacity) {
  if (!(heap instanceof Uint8Array) || !Number.isSafeInteger(pointer) || pointer < 0 || pointer % 4 !== 0 ||
      !Number.isSafeInteger(count) || count < 0 || count > capacity ||
      !Number.isSafeInteger(capacity) || capacity <= 0 || pointer + capacity * 4 > heap.length) {
    fail('Audio buffer range or sample count is invalid.');
  }
  return sha256(heap.subarray(pointer, pointer + count * 4));
}
function readNamedRamScalars(heap, ramPointer) {
  return {
    vBlankRoutine: observer.readLogicalByte(heap, ramPointer, STATE_LAYOUT.vBlankRoutine),
    sfxFm3TrackAMSFMSPan: observer.readLogicalByte(heap, ramPointer, STATE_LAYOUT.sfxFm3TrackAMSFMSPan)
  };
}

function instrumentedFactory(coreFactory) {
  return async () => {
    const core = await coreFactory();
    for (const name of ['_get_web_audio_l_ref', '_get_web_audio_r_ref']) {
      if (typeof core[name] !== 'function') fail(`Core API missing ${name}.`);
    }
    const originalSound = core._sound.bind(core);
    core.__aliasAudioRows = [];
    core._sound = () => {
      const count = originalSound();
      const left = hashFloatSamples(core.HEAPU8, core._get_web_audio_l_ref(), count);
      const right = hashFloatSamples(core.HEAPU8, core._get_web_audio_r_ref(), count);
      const namedRamScalars = readNamedRamScalars(core.HEAPU8, core._get_logic_ram_ref());
      core.__aliasAudioRows.push({tick: core._get_logic_frame(), sampleCount: count,
        completePairs: count, leftSHA256: left, rightSHA256: right, ...namedRamScalars});
      return count;
    };
    return core;
  };
}

async function runTrial(coreFactory, rom, scenario) {
  let observedCore;
  const trial = await observer.runTrial(async () => {
    observedCore = await instrumentedFactory(coreFactory)();
    return observedCore;
  }, rom, scenario);
  if (!observedCore || observedCore.__aliasAudioRows.length !== observer.TRIAL.maxTicks) fail('Audio timeline is incomplete.');
  const audioTimeline = observedCore.__aliasAudioRows;
  const audioByTick = new Map(audioTimeline.map(row => [row.tick, row]));
  const timeline = trial.timeline.map(row => ({...row, ...audioByTick.get(row.tick)}));
  return {...trial, timeline, audioTimeline};
}

function compareAudioPhase(baseline, candidate, offset) {
  if (!Number.isInteger(offset) || !OFFSETS.includes(offset)) fail('Unsupported audio phase offset.');
  const baselineByTick = new Map(baseline.map(row => [row.tick, row]));
  const candidateByTick = new Map(candidate.map(row => [row.tick, row]));
  const first = observer.PHASE_WINDOW.candidateTickStart;
  const last = observer.PHASE_WINDOW.candidateTickEnd;
  const result = {offset, candidateTicks: last - first + 1, comparedPairs: 0,
    missingPairs: 0, completeSamplePairs: 0, zeroSamplePairs: 0, sampleCountMatches: 0,
    leftHashMatches: 0, rightHashMatches: 0, audioMatches: 0,
    vBlankRoutineMatches: 0, sfxFm3TrackAMSFMSPanMatches: 0,
    demoMatches: 0, playerMatches: 0, frameMatches: 0};
  for (let tick = first; tick <= last; tick++) {
    const c = candidateByTick.get(tick), b = baselineByTick.get(tick + offset);
    if (!c || !b) { result.missingPairs++; continue; }
    result.comparedPairs++;
    if (c.completePairs > 0 && b.completePairs > 0) result.completeSamplePairs++;
    if (c.completePairs === 0 && b.completePairs === 0) result.zeroSamplePairs++;
    if (c.sampleCount === b.sampleCount) result.sampleCountMatches++;
    const left = c.leftSHA256 === b.leftSHA256, right = c.rightSHA256 === b.rightSHA256;
    if (c.completePairs > 0 && b.completePairs > 0) {
      if (left) result.leftHashMatches++;
      if (right) result.rightHashMatches++;
      if (left && right && c.sampleCount === b.sampleCount) result.audioMatches++;
    }
    if (c.vBlankRoutine === b.vBlankRoutine) result.vBlankRoutineMatches++;
    if (c.sfxFm3TrackAMSFMSPan === b.sfxFm3TrackAMSFMSPan) result.sfxFm3TrackAMSFMSPanMatches++;
    if (JSON.stringify(observerDemo(c)) === JSON.stringify(observerDemo(b))) result.demoMatches++;
    if (JSON.stringify(observerPlayer(c)) === JSON.stringify(observerPlayer(b))) result.playerMatches++;
    if (c.rawActiveFrameSHA256 === b.rawActiveFrameSHA256) result.frameMatches++;
  }
  return result;
}
function observerDemo(row) { return [row.gameMode,row.demoFlag,row.demoLevelNumber,row.demoCursor,row.demoCountdown,row.heldPad,row.pressedPad]; }
function observerPlayer(row) { return [row.playerObjectId,row.worldXFixed,row.worldYFixed,row.velocityX,row.velocityY]; }
function prefaultMatches(baseline, candidate) {
  return observer.prefaultMatches(baseline, candidate) &&
    JSON.stringify(baseline.timeline.filter(r => r.tick < observer.TRIAL.faultTick)) ===
    JSON.stringify(candidate.timeline.filter(r => r.tick < observer.TRIAL.faultTick));
}
function sameObservation(a, b) {
  return observer.sameTrials({...a, timeline: []}, {...b, timeline: []}) &&
    JSON.stringify(a.timeline) === JSON.stringify(b.timeline);
}
function summarizeAudioRows(rows) {
  if (!Array.isArray(rows) || rows.length !== observer.TRIAL.maxTicks) fail('Audio summary requires a complete bounded run.');
  let totalSamplePairs = 0, minSampleCount = AUDIO.capacity, maxSampleCount = 0, zeroSampleTicks = 0;
  const digest = crypto.createHash('sha256');
  for (const row of rows) {
    if (!Number.isSafeInteger(row.sampleCount) || row.sampleCount < 0 || row.sampleCount > AUDIO.capacity ||
        row.completePairs !== row.sampleCount || !/^[0-9a-f]{64}$/.test(row.leftSHA256) ||
        !/^[0-9a-f]{64}$/.test(row.rightSHA256)) fail('Invalid per-tick audio summary input.');
    totalSamplePairs += row.completePairs;
    minSampleCount = Math.min(minSampleCount, row.sampleCount);
    maxSampleCount = Math.max(maxSampleCount, row.sampleCount);
    if (row.sampleCount === 0) zeroSampleTicks++;
    digest.update(JSON.stringify(row));
    digest.update('\n');
  }
  return {tickCount: rows.length, totalSamplePairs, minSampleCount, maxSampleCount,
    zeroSampleTicks, perTickRecordsSHA256: digest.digest('hex')};
}
function selectedSamples(trial) {
  const audioByTick = new Map(trial.audioTimeline.map(row => [row.tick, row]));
  const observerByTick = new Map(trial.samples.map(row => [row.tick, row]));
  return observer.TRIAL.sampleTicks.map(tick => {
    const state = observerByTick.get(tick), audio = audioByTick.get(tick);
    if (!state || !audio) fail(`Missing selected observation at tick ${tick}.`);
    return {...state, sampleCount: audio.sampleCount, completePairs: audio.completePairs,
      leftSHA256: audio.leftSHA256, rightSHA256: audio.rightSHA256,
      vBlankRoutine: audio.vBlankRoutine, sfxFm3TrackAMSFMSPan: audio.sfxFm3TrackAMSFMSPan};
  });
}
function serializeObserverSummary(trial) {
  const {audioTimeline, ...withoutAudioTimeline} = trial;
  const {samples, ...summary} = observer.serializeTrial(withoutAudioTimeline);
  return summary;
}
function assertBoundedReport(value) {
  const forbidden = new Set(['timeline', 'audioTimeline', 'audioSamples', 'romBytes', 'ramBytes', 'rawSamples']);
  function walk(node) {
    if (Array.isArray(node)) {
      if (node.length > 7) fail('Report contains an array longer than the seven selected ticks.');
      for (const item of node) walk(item);
    } else if (node && typeof node === 'object') {
      for (const [key, child] of Object.entries(node)) {
        if (forbidden.has(key)) fail(`Report contains forbidden field ${key}.`);
        walk(child);
      }
    }
  }
  walk(value);
  return value;
}
function stripAudioObservation(trial) {
  const {audioTimeline, ...base} = trial;
  return {...base, timeline: trial.timeline.map(({sampleCount, completePairs, leftSHA256, rightSHA256,
    vBlankRoutine, sfxFm3TrackAMSFMSPan, ...row}) => row)};
}
function compareTrials(runs) {
  for (const scenario of SCENARIOS) {
    const [first, repeat] = runs[scenario];
    if (!sameObservation(first, repeat)) fail(`${scenario} fresh-core repeat differs.`);
  }
  if (!runs.baseline.every(r => r.preFaultStreamSHA256 === runs.baseline[0].preFaultStreamSHA256) ||
      !runs['A10A11-one-write'].every(r => prefaultMatches(runs.baseline[0], r))) fail('Prefault observations do not match.');
  const faultRuns = runs['A10A11-one-write'];
  if (faultRuns.some(r => r.faultSetterFrame !== 1800 || r.effectiveFaultTick !== 1801 ||
      r.pulse?.requestedAffectedWrites !== 1 || r.pulse?.affectedWritesAtRelease !== 1 ||
      r.pulse?.releaseReason !== 'affected-write-limit')) fail('One-write pulse did not release at the required boundary.');
  return Object.fromEntries(faultRuns.map((r, index) => [index === 0 ? 'first' : 'repeat',
    Object.fromEntries(OFFSETS.map(offset => [String(offset), compareAudioPhase(runs.baseline[0].timeline, r.timeline, offset)]))]));
}

async function main(args) {
  if (args.length !== 3 || args[1] !== '--app') throw new Error('Usage: node scripts/observe-ram-alias-audio-phase.cjs /private/path/sonic.md --app /path/to/VRAMpage-MD');
  const rom = fs.readFileSync(args[0]);
  const cartridge = observer.validateRomBuffer(rom, APP_PROFILE);
  const app = validateAppDirectory(args[2]);
  const factory = require(app.coreJsPath);
  const coreFactory = () => factory({locateFile: name => path.join(path.dirname(app.coreJsPath), name)});
  const runs = {}, plainRuns = {};
  for (const scenario of SCENARIOS) {
    runs[scenario] = [];
    plainRuns[scenario] = [];
    for (let repeat = 0; repeat < 2; repeat++) {
      plainRuns[scenario].push(await observer.runTrial(coreFactory, rom, scenario));
      runs[scenario].push(await runTrial(coreFactory, rom, scenario));
    }
  }
  for (const scenario of SCENARIOS) for (let i = 0; i < 2; i++) {
    if (!observer.sameTrials(plainRuns[scenario][i], stripAudioObservation(runs[scenario][i]))) {
      fail(`${scenario} observation changed under the audio observer.`);
    }
  }
  const phaseComparisons = compareTrials(runs);
  const repo = path.resolve(__dirname, '..');
  const sourceCommit = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: repo, encoding: 'utf8'}).trim();
  const toolBytes = fs.readFileSync(__filename);
  const sourceDirty = execFileSync('git', ['status', '--porcelain', '--untracked-files=all', '--',
    path.relative(repo, __filename)], {cwd: repo, encoding: 'utf8'}).trim().length > 0;
  const observerSHA256 = sha256(fs.readFileSync(path.join(__dirname, 'observe-attract-demo.cjs')));
  const output = {schemaVersion: 1, tool: {version: TOOL_VERSION, sourceCommit,
    sourceDirty, sha256: sha256(toolBytes)}, protocol: {version: PROTOCOL_VERSION,
    name: 'ram-alias-audio-phase-v1', applicationVersion: '0.2.7'},
    runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    package: {sourceCommit: app.manifest.source_commit, corePin: observer.APP_PROFILE.corePin,
      javascriptSHA256: app.javascriptSHA256, wasmSHA256: app.wasmSHA256}, cartridge,
    dependency: {observerSHA256},
    settings: {ticks: observer.TRIAL.maxTicks, externalInput: 'zero every tick', scenarios: SCENARIOS,
      setterFrame: 1800, effectiveTick: 1801, requestedAffectedWrites: 1, cpuRecovery: 'none',
      soundSampleCapacityPerChannel: AUDIO.capacity, bufferUnit: 'float32 samples',
      audioHashMethod: 'SHA-256 of the returned count of raw Float32 bytes per channel; WebAssembly memory is little-endian; buffers and sample values are never serialized',
      emptyAudioComparison: 'zero-count channel buffers hash as SHA-256(empty); zeroSamplePairs and sampleCountMatches report these separately, while channel hash matches and audioMatches require samples on both sides',
      stateReadBoundary: 'after sound generation each tick; named work-RAM scalar values only',
      phaseOffsetConvention: observer.PHASE_WINDOW.offsetConvention, phaseOffsets: OFFSETS},
    equivalence: {baselineRepeats: sameObservation(...runs.baseline),
      faultRepeats: sameObservation(...runs['A10A11-one-write']),
      prefaultMatchesBaseline: runs['A10A11-one-write'].every(r => prefaultMatches(runs.baseline[0], r)),
      noFaultObservationalNoninterference: plainRuns.baseline.every((plain, i) =>
        observer.sameTrials(plain, stripAudioObservation(runs.baseline[i]))),
      instrumentedObservationsMatchUninstrumented: Object.fromEntries(SCENARIOS.map(s => [s,
        plainRuns[s].every((plain, i) => observer.sameTrials(plain, stripAudioObservation(runs[s][i])))]))}, phaseComparisons,
    audioSummary: {baseline: summarizeAudioRows(runs.baseline[0].audioTimeline),
      fault: summarizeAudioRows(runs['A10A11-one-write'][0].audioTimeline)},
    selectedSamples: {baseline: selectedSamples(runs.baseline[0]),
      fault: selectedSamples(runs['A10A11-one-write'][0])},
    stateLayout: {...SOURCE_LAYOUT, addresses: STATE_LAYOUT},
    observerSummary: Object.fromEntries(SCENARIOS.map(s => [s, runs[s].map(serializeObserverSummary)]))};
  assertBoundedReport(output);
  process.stdout.write(JSON.stringify(output, null, 2) + '\n');
}
if (require.main === module) main(process.argv.slice(2)).catch(error => {
  process.stderr.write(`${error.message}\n`); process.exitCode = 1;
});
module.exports = {APP_PROFILE, AUDIO, TOOL_VERSION, PROTOCOL_VERSION, validateAppDirectory,
  hashFloatSamples, readNamedRamScalars, STATE_LAYOUT, SOURCE_LAYOUT, compareAudioPhase,
  prefaultMatches, sameObservation, compareTrials, stripAudioObservation, summarizeAudioRows,
  selectedSamples, serializeObserverSummary, assertBoundedReport};
