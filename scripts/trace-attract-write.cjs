#!/usr/bin/env node
'use strict';
// Developer-only bounded comparison. No ROM, RAM, image or audio bytes in output.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const observer = require('./observe-attract-demo.cjs');
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const SCENARIOS = ['baseline', 'A10A11-one-write'];
const FIELDS = ['cpu_address', 'ram_offset', 'mapped_offset', 'width', 'frame', 'reason'];
function readTrace(core) {
  const state = core._get_logic_write_trace_state();
  if (state === 0) return null;
  if (state !== 2) throw new Error('Trace was not completed at the observation boundary.');
  const record = Object.fromEntries(FIELDS.map(name => [name, core[`_get_logic_write_trace_${name}`]() >>> 0]));
  if (record.cpu_address > 0xffffff || record.ram_offset !== (record.cpu_address & 0xffff) ||
      record.mapped_offset > 0xffff || ![1, 2].includes(record.width) ||
      ![1, 2, 3].includes(record.reason) || record.frame >= observer.TRIAL.maxTicks) {
    throw new Error('Invalid first-write trace metadata.');
  }
  return record;
}
async function tracedTrial(factory, rom, scenario, enabled) {
  let core;
  const trial = await observer.runTrial(async () => {
    core = await factory();
    for (const name of ['_set_logic_write_trace_enabled', '_get_logic_write_trace_state',
      ...FIELDS.map(field => `_get_logic_write_trace_${field}`)]) {
      if (typeof core[name] !== 'function') throw new Error(`Missing trace API ${name}.`);
    }
    const start = core._start.bind(core);
    core._start = () => {
      start();
      if (core._set_logic_write_trace_enabled(enabled ? 1 : 0) !== 0) throw new Error('Trace enable rejected.');
    };
    return core;
  }, rom, scenario);
  return {trial, firstAffectedWrite: readTrace(core)};
}
async function compareRuns(factory, rom, run = tracedTrial) {
  const runs = {};
  for (const scenario of SCENARIOS) {
    const disabled = await run(factory, rom, scenario, false);
    const first = await run(factory, rom, scenario, true);
    const repeat = await run(factory, rom, scenario, true);
    runs[scenario] = {
      disabled: {observation: observer.serializeTrial(disabled.trial), firstAffectedWrite: disabled.firstAffectedWrite},
      enabled: {observation: observer.serializeTrial(first.trial), firstAffectedWrite: first.firstAffectedWrite},
      repeated: {observation: observer.serializeTrial(repeat.trial), firstAffectedWrite: repeat.firstAffectedWrite},
      tracePreservesObservation: observer.sameTrials(disabled.trial, first.trial) && observer.sameTrials(disabled.trial, repeat.trial),
      repeatIdentical: observer.sameTrials(first, repeat)
    };
  }
  return runs;
}
function verifyPackage(app) {
  const root = fs.readFileSync(path.join(app, 'BUILD-INFO.json'));
  if (!root.equals(fs.readFileSync(path.join(app, 'site/build-info.json')))) throw new Error('Package manifests differ.');
  const manifest = JSON.parse(root);
  if (manifest.application !== 'VRAMpage MD' || manifest.application_version !== '0.2.7' ||
      manifest.package_format !== 1 || !/^[0-9a-f]{40}$/.test(manifest.source_commit) ||
      fs.readFileSync(path.join(app, 'VERSION'), 'utf8').trim() !== '0.2.7') throw new Error('Expected complete v0.2.7 package.');
  const js = path.join(app, 'site/core/genplus.js');
  const wasm = fs.readFileSync(path.join(app, 'site/core/genplus.wasm'));
  if (!wasm.subarray(0, 4).equals(Buffer.from([0, 97, 115, 109]))) throw new Error('Invalid WASM signature.');
  return {manifest, js, javascriptSHA256: sha256(fs.readFileSync(js)), wasmSHA256: sha256(wasm)};
}
function passesEvidence(runs, historicalComparison) {
  return SCENARIOS.every(scenario => runs[scenario]?.tracePreservesObservation === true &&
    runs[scenario]?.repeatIdentical === true && historicalComparison[scenario] === true &&
    runs[scenario].disabled.firstAffectedWrite === null &&
    (scenario === 'baseline'
      ? runs[scenario].enabled.firstAffectedWrite === null && runs[scenario].repeated.firstAffectedWrite === null
      : runs[scenario].enabled.firstAffectedWrite != null && runs[scenario].repeated.firstAffectedWrite != null));
}
async function main(args) {
  if (args.length !== 3 || args[1] !== '--app') throw new Error('Usage: node scripts/trace-attract-write.cjs /private/path/sonic.md --app /path/to/VRAMpage-MD');
  const rom = fs.readFileSync(args[0]);
  const cartridge = observer.validateRomBuffer(rom); // Retain the source-verified cartridge layout.
  const app = verifyPackage(path.resolve(args[2]));
  const factory = require(app.js); // User-selected local executable, loaded only after validation.
  const runs = await compareRuns(() => factory({locateFile: name => path.join(path.dirname(app.js), name)}), rom);
  const repo = path.resolve(__dirname, '..');
  const tool = {sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: repo, encoding: 'utf8'}).trim(),
    sourceDirty: Boolean(execFileSync('git', ['status', '--porcelain', '--untracked-files=all', '--', 'scripts', 'tests', 'VERSION', 'site/app.js', 'site/index.html', '.github/workflows'], {cwd: repo, encoding: 'utf8'}).trim()),
    traceRunnerSHA256: sha256(fs.readFileSync(__filename)), observerSHA256: sha256(fs.readFileSync(path.join(__dirname, 'observe-attract-demo.cjs')))};
  const historical = JSON.parse(fs.readFileSync(path.join(repo, 'docs/experiments/2026-10-22-attract-demo-observer-v2.json')));
  const historicalComparison = Object.fromEntries(SCENARIOS.map(s => [s,
    observer.sameTrials(runs[s].disabled.observation, historical.runs[s].first)]));
  process.stdout.write(JSON.stringify({schemaVersion: 1, protocol: 'first-affected-write-v1', applicationVersion: '0.2.7',
    runtime: {node: process.versions.node, platform: process.platform, arch: process.arch}, tool, cartridge,
    package: {sourceCommit: app.manifest.source_commit, javascriptSHA256: app.javascriptSHA256, wasmSHA256: app.wasmSHA256,
      corePin: observer.APP_PROFILE.corePin}, settings: {ticks: 2400, externalInput: 'zero every tick',
      fault: 'A10/A11 one affected write', setterFrame: 1800, effectiveTick: 1801, cpuRecovery: 'none',
      traceFrame: 'completed frames before access; during tick N this is N-1', width: 'bytes per bus cycle; longword uses two word cycles'},
    historicalComparison, runs}, null, 2) + '\n');
  if (!passesEvidence(runs, historicalComparison)) process.exitCode = 1;
}
if (require.main === module) main(process.argv.slice(2)).catch(e => {process.stderr.write(e.message + '\n'); process.exitCode = 1;});
module.exports = {readTrace, tracedTrial, compareRuns, verifyPackage, passesEvidence};
