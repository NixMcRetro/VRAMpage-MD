#!/usr/bin/env node
'use strict';

// Explicit, preregistered renderer/DMA benchmark. Do not invoke during builds or
// other timing-sensitive work; coordinate a quiet host period first.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const {visibleCartridge, makeCore, observable} = require('../tests/test_vram_renderer_visible.cjs');

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (!key.startsWith('--')) throw new Error(`Invalid argument: ${key}`);
    if (key === '--preflight-only') { args.preflightOnly = true; continue; }
    if (i + 1 >= argv.length || argv[i + 1].startsWith('--'))
      throw new Error(`Missing value for ${key}`);
    args[key.slice(2)] = argv[++i];
  }
  for (const key of ['baseline', 'normal', 'diagnostic', 'out']) {
    if (!args[key]) throw new Error(`Missing required --${key}`);
  }
  args.pairs = Number(args.pairs || 5);
  args.durationMs = Number(args['duration-ms'] || 30000);
  if (!Number.isInteger(args.pairs) || args.pairs !== 5) throw new Error('--pairs is fixed at 5');
  if (!Number.isInteger(args.durationMs) || args.durationMs !== 30000)
    throw new Error('--duration-ms is fixed at 30000');
  return args;
}

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function percentile(samples, fraction) {
  const sorted = [...samples].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(fraction * sorted.length) - 1)];
}
function median(samples) {
  const sorted = [...samples].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function commandVersion(command, args) {
  try { return execFileSync(command, args, {encoding: 'utf8'}).trim().split('\n')[0]; }
  catch { return 'unavailable on benchmark host'; }
}

function entry(jsPath) {
  const absolute = path.resolve(jsPath);
  const resolved = fs.realpathSync(absolute);
  return {p: resolved, f: require(resolved)};
}

function tick(core) {
  core._wasm_input_update();
  core._tick();
  return core._sound();
}

function cpuLoopCount(state) { return state.ram.readUInt16BE(0); }

async function runPreflightVariant(name, factory, rom, mask, ticksAfterSelection) {
  const core = await makeCore(factory, rom);
  let samples = tick(core); // Mode 5 support is established by the first tick.
  const loopBeforeSelection = cpuLoopCount(observable(core, samples));
  if (mask !== null) {
    const result = core._set_vram_transaction_diagnostic(2, mask, -1, -1);
    if (result !== 0) throw new Error(`${name}: transaction configuration rejected (${result})`);
  }
  for (let i = 0; i < ticksAfterSelection; i++) samples = tick(core);
  const state = observable(core, samples);
  const loopAfterSelection = cpuLoopCount(state);
  if (loopAfterSelection <= loopBeforeSelection)
    throw new Error(`${name}: recurring DMA CPU loop did not advance during preflight`);
  const counters = typeof core._get_vram_tx_counter === 'function'
    ? [0, 1, 2, 3, 4].map(i => String(core._get_vram_tx_counter(i))) : null;
  if (mask === 8 && (!counters || BigInt(counters[1]) === 0n))
    throw new Error('active-ad3: fixed-tick preflight observed no mapped DMA writes');
  if (mask === 0 && counters && BigInt(counters[1]) !== 0n)
    throw new Error('identity: fixed-tick preflight unexpectedly counted mapped writes');
  return {
    variant: name,
    setupTicksBeforeSelection: 1,
    fixedTicksAfterSelection: ticksAfterSelection,
    loopCounterBeforeSelection: loopBeforeSelection,
    loopCounterAfterSelection: loopAfterSelection,
    frameSha256: crypto.createHash('sha256').update(state.frame).digest('hex'),
    ramSha256: crypto.createHash('sha256').update(state.ram).digest('hex'),
    audioSamples: state.audioSamples,
    logicFrame: state.logicFrame,
    cpuFlags: state.cpuFlags,
    transactionCounters: counters,
    state // Removed before JSON serialization; used only for exact in-process comparison.
  };
}

function comparePreflightState(actual, expected, label) {
  const assert = require('node:assert/strict');
  assert.equal(actual.audioSamples, expected.audioSamples, `${label}: audio sample count`);
  assert.deepEqual(actual.frame, expected.frame, `${label}: full framebuffer`);
  assert.deepEqual(actual.audioLeft, expected.audioLeft, `${label}: left audio`);
  assert.deepEqual(actual.audioRight, expected.audioRight, `${label}: right audio`);
  assert.deepEqual(actual.ram, expected.ram, `${label}: work RAM`);
  assert.equal(actual.logicFrame, expected.logicFrame, `${label}: logic frame`);
  assert.equal(actual.cpuFlags, expected.cpuFlags, `${label}: CPU flags`);
}

async function runVariant(name, factory, rom, mask, ticksAfterSelection) {
  const core = await makeCore(factory, rom);
  let samples = tick(core); // Let every variant enter Mode 5 before selection.
  if (mask !== null) {
    const result = core._set_vram_transaction_diagnostic(2, mask, -1, -1);
    if (result !== 0) throw new Error(`${name}: transaction configuration rejected (${result})`);
  }
  for (let i = 0; i < ticksAfterSelection; i++) samples = tick(core);

  const frameMs = [];
  const started = process.hrtime.bigint();
  const durationNs = 30000000000n;
  let audioSamples = 0;
  while (process.hrtime.bigint() - started < durationNs) {
    const before = process.hrtime.bigint();
    audioSamples = tick(core);
    frameMs.push(Number(process.hrtime.bigint() - before) / 1e6);
  }
  const elapsedMs = Number(process.hrtime.bigint() - started) / 1e6;
  const state = observable(core, audioSamples);
  const frameHash = crypto.createHash('sha256').update(state.frame).digest('hex');
  const audioHash = crypto.createHash('sha256')
    .update(Buffer.from(state.audioLeft.buffer, state.audioLeft.byteOffset, state.audioLeft.byteLength))
    .update(Buffer.from(state.audioRight.buffer, state.audioRight.byteOffset, state.audioRight.byteLength))
    .digest('hex');
  const counters = typeof core._get_vram_tx_counter === 'function'
    ? [0, 1, 2, 3, 4].map(i => String(core._get_vram_tx_counter(i))) : null;
  return {
    variant: name,
    elapsedMs,
    frameCount: frameMs.length,
    medianFrameMs: percentile(frameMs, 0.5),
    p95FrameMs: percentile(frameMs, 0.95),
    frameDurationsMs: frameMs,
    audioSamples,
    frameSha256: frameHash,
    finalAudioSha256: audioHash,
    logicFrame: core._get_logic_frame(),
    cpuFlags: core._get_logic_cpu_flags(),
    transactionCounters: counters
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const root = path.resolve(__dirname, '..');
  const git = (command, ...argv) => execFileSync('git', [command, ...argv], {
    cwd: root, encoding: 'utf8'
  }).trim();
  const trackedClean = () => {
    try {
      execFileSync('git', ['diff-index', '--quiet', 'HEAD', '--'], {cwd: root});
      return true;
    } catch { return false; }
  };
  const sourceBefore = {
    commit: git('rev-parse', 'HEAD'),
    tree: git('rev-parse', 'HEAD^{tree}'),
    trackedClean: trackedClean(),
    status: git('status', '--porcelain', '--untracked-files=normal')
  };
  if (!sourceBefore.trackedClean)
    throw new Error('Benchmark source checkout has tracked modifications; commit the reviewed snapshot first');
  const factories = {
    baseline: entry(args.baseline),
    normal: entry(args.normal),
    diagnostic: entry(args.diagnostic),
    'diagnostic-off': entry(args.diagnostic),
    identity: entry(args.diagnostic),
    'active-ad3': entry(args.diagnostic)
  };
  const coreBasenames = Object.fromEntries(Object.entries(factories)
    .map(([key, value]) => [key, path.basename(value.p)]));
  const artifactManifest = Object.fromEntries(['baseline', 'normal', 'diagnostic'].map(role => {
    const js = factories[role].p;
    const wasm = js.replace(/\.js$/, '.wasm');
    return [role, {jsBasename: path.basename(js), jsSha256: sha256(js), wasmBasename: path.basename(wasm), wasmSha256: sha256(wasm)}];
  }));
  const hostBefore = {
    loadAverage: os.loadavg(),
    node: process.version,
    platform: process.platform,
    arch: process.arch,
    cpuModel: os.cpus()[0]?.model || 'unknown',
    logicalCpus: os.cpus().length,
    totalMemoryBytes: os.totalmem(),
    emscripten: commandVersion('emcc', ['--version']),
    cmake: commandVersion('cmake', ['--version'])
  };
  const variants = [
    ['baseline', null], ['normal', null], ['diagnostic-off', null],
    ['identity', 0], ['active-ad3', 8]
  ];
  const forward = variants.map(([name]) => name);
  const pairs = [];
  const rom = visibleCartridge(0, {recurringDma: true});
  const preflightVariants = [
    ['baseline', null], ['normal', null], ['diagnostic-off', null],
    ['identity', 0], ['active-ad3', 8]
  ];
  const preflight = {};
  for (const [name, mask] of preflightVariants) {
    preflight[name] = await runPreflightVariant(name, factories[name], rom, mask, 120);
  }
  for (const name of ['normal', 'diagnostic-off', 'identity']) {
    comparePreflightState(preflight[name].state, preflight.baseline.state,
      `fixed-tick preflight ${name} vs baseline`);
  }
  for (const value of Object.values(preflight)) delete value.state;
  if (!args.preflightOnly) {
    for (let pair = 0; pair < 5; pair++) {
      const order = pair % 2 === 0 ? forward : [...forward].reverse();
      const runs = [];
      for (const name of order) {
        const [, mask] = variants.find(([variant]) => variant === name);
        runs.push(await runVariant(name, factories[name], rom, mask, 120));
      }
      pairs.push({pair: pair + 1, order, runs});
    }
  }
  const byVariant = {};
  if (!args.preflightOnly) {
    for (const name of forward) {
      byVariant[name] = pairs.map(pair => {
        const run = pair.runs.find(candidate => candidate.variant === name);
        const baseline = pair.runs.find(candidate => candidate.variant === 'baseline');
        return {
          pair: pair.pair,
          medianFrameMs: run.medianFrameMs,
          p95FrameMs: run.p95FrameMs,
          medianRatioToBaseline: run.medianFrameMs / baseline.medianFrameMs,
          p95RatioToBaseline: run.p95FrameMs / baseline.p95FrameMs
        };
      });
    }
  }
  const noFaultVariants = ['normal', 'diagnostic-off', 'identity'];
  const gateSummary = args.preflightOnly ? null : Object.fromEntries(noFaultVariants.map(name => {
    const paired = byVariant[name];
    const medianRatio = median(paired.map(run => run.medianRatioToBaseline));
    const p95Ratio = median(paired.map(run => run.p95RatioToBaseline));
    return [name, {
      medianOfFivePairedMedianRatios: medianRatio,
      medianOfFivePairedP95Ratios: p95Ratio,
      pass: medianRatio <= 1.05 && p95Ratio <= 1.05
    }];
  }));
  const performanceGatePass = args.preflightOnly ? null : Object.values(gateSummary).every(value => value.pass);
  const artifactsUnchanged = Object.fromEntries(Object.entries(artifactManifest).map(([role, artifact]) => {
    const js = factories[role].p;
    const wasm = js.replace(/\.js$/, '.wasm');
    return [role, artifact.jsSha256 === sha256(js) && artifact.wasmSha256 === sha256(wasm)];
  }));
  const sourceAfter = {
    commit: git('rev-parse', 'HEAD'),
    tree: git('rev-parse', 'HEAD^{tree}'),
    trackedClean: trackedClean(),
    status: git('status', '--porcelain', '--untracked-files=normal')
  };
  const provenanceStable = sourceBefore.commit === sourceAfter.commit &&
    sourceBefore.tree === sourceAfter.tree && sourceAfter.trackedClean &&
    Object.values(artifactsUnchanged).every(Boolean);
  const hostAfter = {loadAverage: os.loadavg()};
  const report = {
    recordedAt: new Date().toISOString(),
    protocol: {
      name: 'visible-mode5-recurring-32-word-dma-paired-v1',
      mode: args.preflightOnly ? 'preflight-only' : 'timed-benchmark',
      measured: !args.preflightOnly,
      fixedPairs: args.preflightOnly ? null : 5,
      fixedDurationMsPerRun: args.preflightOnly ? null : 30000,
      warmupTicks: 120,
      preflight: 'one common first Mode 5 tick, then diagnostic selection where applicable, then exactly 120 fixed ticks; recurring CPU loop counter must advance; baseline, normal, diagnostic-off, and identity must match full frame/audio/RAM/CPU-flag observations',
      timedUnit: 'one input-update + emulator tick + audio render; per-frame hrtime duration in milliseconds',
      pairOrder: 'pairs 1,3,5 forward; pairs 2,4 reverse; no result-based reordering or exclusion',
      percentile: 'nearest-rank: sorted[Math.ceil(p*n)-1]; median is nearest-rank p=0.50; p95 is per-run frame p=0.95',
      statisticUse: 'report raw five per-run medians and p95s; do not pool frame samples across runs',
      performanceGate: 'For normal, diagnostic-off, and identity, median of five paired run ratios to baseline must be <=1.05 for both per-run median frame duration and per-run p95 frame duration. Active AD3 is descriptive and does not determine the no-fault gate.',
      workload: 'visible synthetic Mode 5 tile scene plus original 68K ROM loop issuing recurring 32-word VRAM DMA from ROM byte 0x4000 to VRAM 0x6000',
      variants: forward,
      quietPeriodRequired: true,
      noisePolicy: 'retain every sample; do not retime, rerun, or exclude based on results; record host load before and after; the fixed 1.05 threshold still applies'
    },
    provenance: {
      sourceBefore,
      sourceAfter,
      hostBefore,
      hostAfter,
      coreBasenames,
      artifactManifest,
      artifactsUnchanged,
      provenanceStable
    },
    preflight,
    pairs,
    pairedSummary: byVariant,
    performanceGate: {
      thresholdRatio: 1.05,
      aggregation: 'median of five paired ratios; per-run p95 is nearest-rank frame p95 within that run',
      noFaultVariants: noFaultVariants,
      details: gateSummary,
      pass: performanceGatePass,
      failureExitCode: 2,
      provenanceFailureExitCode: 3
    }
  };
  const output = path.resolve(args.out);
  fs.mkdirSync(path.dirname(output), {recursive: true});
  fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`Wrote ${args.preflightOnly ? 'fixed-tick preflight' : 'five-pair benchmark'} record to ${output}\n`);
  if (!provenanceStable) process.exitCode = 3;
  else if (performanceGatePass === false) process.exitCode = 2;
}

main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
