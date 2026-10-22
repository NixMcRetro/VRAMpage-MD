#!/usr/bin/env node
/* Bounded Sonic 1 demo-state observer; emits scalar summaries and hashes only. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');

const TOOL_VERSION = 1;
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

function readAttractFields(heap, ramPointer) {
  return {
    gameMode: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.gameMode),
    demoFlag: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoFlag),
    demoLevelNumber: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoLevelNumber),
    demoCursor: readLogicalWord(heap, ramPointer, SONIC1_LAYOUT.demoCursor),
    demoCountdown: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.demoCountdown),
    heldPad: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.heldPad),
    pressedPad: readLogicalByte(heap, ramPointer, SONIC1_LAYOUT.pressedPad)
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

function hashVisibleFrame(core) {
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

function requireCoreAPI(core, scenario) {
  const names = ['_init', '_start', '_tick', '_sound', '_wasm_input_update',
    '_get_rom_buffer_ref', '_get_input_buffer_ref', '_get_frame_buffer_ref',
    '_get_logic_ram_ref', '_get_logic_frame', '_get_logic_reads', '_get_logic_writes',
    '_get_logic_cpu_flags', '_get_logic_activation_frame', '_get_logic_pulse_state'];
  if (scenario !== 'baseline') names.push('_set_logic_fault');
  if (scenario === 'A10A11-one-write') names.push('_arm_logic_write_pulse');
  for (const name of names) if (typeof core[name] !== 'function') fail(`Core API missing ${name}.`);
  if (!(core.HEAPU8 instanceof Uint8Array)) fail('Core API missing HEAPU8.');
}

async function runTrial(coreFactory, rom, scenario) {
  if (!Object.hasOwn(TRIAL.scenarios, scenario)) fail(`Unknown trial scenario: ${scenario}`);
  const faultConfig = TRIAL.scenarios[scenario];
  const core = await coreFactory();
  requireCoreAPI(core, scenario);
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
  for (let tick = 1; tick <= TRIAL.maxTicks; tick++) {
    if (faultConfig && tick === TRIAL.faultTick) {
      faultSetterFrame = core._get_logic_frame();
      if (faultSetterFrame !== 1800) fail(`Fault timing expected core frame 1800, got ${faultSetterFrame}.`);
      const status = faultConfig.type === 'writePulse'
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
    updateAggregate(streamHash, fields);
    if (tick < TRIAL.faultTick) updateAggregate(preFaultHash, fields);
    if (previous) {
      if (fields.demoCursor !== previous.demoCursor) cursorValueChanges++;
      if (fields.heldPad !== previous.heldPad) heldPadValueChanges++;
    }
    previous = fields;
    const corePulseState = core._get_logic_pulse_state();
    if (scenario === 'A10A11-one-write') {
      pulseStateAtEnd = corePulseState;
      if (pulseReleaseTick === null && (corePulseState === 2 || corePulseState === 3)) {
        pulseReleaseTick = tick;
        affectedWritesAtRelease = core._get_logic_writes();
      }
    }
    if (TRIAL.sampleTicks.includes(tick)) {
      samples.push({
        tick, coreFrame,
        visibleFrameSHA256: hashVisibleFrame(core),
        faultReads: core._get_logic_reads(), faultWrites: core._get_logic_writes(),
        cpuFlags: core._get_logic_cpu_flags(), corePulseState,
        externalInputZeroThisTick: externalZeroThisTick,
        ...fields
      });
    }
  }
  return {
    scenario, ticks: TRIAL.maxTicks,
    faultSetterFrame, effectiveFaultTick, reportedActivationFrame,
    externalInputZeroTicks, cursorValueChanges, heldPadValueChanges,
    streamSHA256: streamHash.digest('hex'),
    preFaultStreamSHA256: preFaultHash.digest('hex'),
    pulse: scenario === 'A10A11-one-write' ? {
      requestedAffectedWrites: 1, finalCoreState: pulseStateAtEnd, releaseTick: pulseReleaseTick,
      affectedWritesAtRelease,
      releaseReason: pulseStateAtEnd === 2 ? 'affected-write-limit' :
        pulseStateAtEnd === 3 ? 'frame-limit' : 'still-active-or-unknown'
    } : null,
    samples
  };
}

function sameTrials(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
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
  const tool = toolIdentity();
  const output = {
    schemaVersion: 1,
    protocolVersion: 1,
    modelVersion: '0.2.6-experimental',
    tool,
    runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    package: {
      applicationVersion: verified.app.manifest.application_version,
      sourceCommit: verified.app.manifest.source_commit,
      corePin: APP_PROFILE.corePin,
      javascriptSHA256: verified.app.javascriptSHA256,
      wasmSHA256: verified.app.wasmSHA256
    },
    cartridge: verified.romIdentity,
    settings: {
      externalInputBufferLength: 32,
      tickLimit: TRIAL.maxTicks,
      sampleTicks: TRIAL.sampleTicks,
      faults: {
        'D0D1-read': {setterFrame: 1800, effectiveTick: 1801, kind: 'data', access: 'read', lines: ['D0', 'D1']},
        'A10A11-one-write': {setterFrame: 1800, effectiveTick: 1801, kind: 'address', lines: ['A10', 'A11'], requestedAffectedWrites: 1}
      },
      cpuRecovery: 'none'
    },
    freshCoreTrials: factories.length,
    runs
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
  APP_PROFILE, SONIC1_LAYOUT, TRIAL,
  inputBufferIsZero, readAttractFields, readLogicalByte, readLogicalWord,
  prefaultMatches, runTrial, sameTrials, validateAppDirectory, validateManifest, validateRomBuffer, loadVerified
};
