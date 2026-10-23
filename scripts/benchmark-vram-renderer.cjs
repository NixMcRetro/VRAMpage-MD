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
    if (!key.startsWith('--') || i + 1 >= argv.length) throw new Error(`Invalid argument: ${key}`);
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
  return {p: absolute, f: require(absolute)};
}

async function runVariant(name, factory, rom, mask) {
  const core = await makeCore(factory, rom);
  if (mask !== null) {
    const result = core._set_vram_transaction_diagnostic(2, mask, -1, -1);
    if (result !== 0) throw new Error(`${name}: transaction configuration rejected (${result})`);
  }
  const tick = () => {
    core._wasm_input_update();
    core._tick();
    return core._sound();
  };
  for (let i = 0; i < 120; i++) tick();

  const frameMs = [];
  const started = process.hrtime.bigint();
  const durationNs = 30000000000n;
  let audioSamples = 0;
  while (process.hrtime.bigint() - started < durationNs) {
    const before = process.hrtime.bigint();
    audioSamples = tick();
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
  const factories = {
    baseline: entry(args.baseline),
    normal: entry(args.normal),
    'diagnostic-off': entry(args.diagnostic),
    identity: entry(args.diagnostic),
    'active-ad3': entry(args.diagnostic)
  };
  const corePaths = Object.fromEntries(Object.entries(factories).map(([key, value]) => [key, value.p]));
  const variants = [
    ['baseline', null], ['normal', null], ['diagnostic-off', null],
    ['identity', 0], ['active-ad3', 8]
  ];
  const forward = variants.map(([name]) => name);
  const pairs = [];
  const rom = visibleCartridge(0, {recurringDma: true});
  for (let pair = 0; pair < 5; pair++) {
    const order = pair % 2 === 0 ? forward : [...forward].reverse();
    const runs = [];
    for (const name of order) {
      const [, mask] = variants.find(([variant]) => variant === name);
      runs.push(await runVariant(name, factories[name], rom, mask));
    }
    pairs.push({pair: pair + 1, order, runs});
  }
  const byVariant = {};
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
  const noFaultVariants = ['normal', 'diagnostic-off', 'identity'];
  const gateSummary = Object.fromEntries(noFaultVariants.map(name => {
    const paired = byVariant[name];
    const medianRatio = median(paired.map(run => run.medianRatioToBaseline));
    const p95Ratio = median(paired.map(run => run.p95RatioToBaseline));
    return [name, {
      medianOfFivePairedMedianRatios: medianRatio,
      medianOfFivePairedP95Ratios: p95Ratio,
      pass: medianRatio <= 1.05 && p95Ratio <= 1.05
    }];
  }));
  const performanceGatePass = Object.values(gateSummary).every(value => value.pass);
  const sourceCommit = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim();
  const report = {
    recordedAt: new Date().toISOString(),
    protocol: {
      name: 'visible-mode5-recurring-32-word-dma-paired-v1',
      fixedPairs: 5,
      fixedDurationMsPerRun: 30000,
      warmupTicks: 120,
      timedUnit: 'one input-update + emulator tick + audio render; per-frame hrtime duration in milliseconds',
      pairOrder: 'pairs 1,3,5 forward; pairs 2,4 reverse; no result-based reordering or exclusion',
      percentile: 'nearest-rank: sorted[Math.ceil(p*n)-1]; median is nearest-rank p=0.50; p95 is per-run frame p=0.95',
      statisticUse: 'report raw five per-run medians and p95s; do not pool frame samples across runs',
      performanceGate: 'For normal, diagnostic-off, and identity, median of five paired run ratios to baseline must be <=1.05 for both per-run median frame duration and per-run p95 frame duration. Active AD3 is descriptive and does not determine the no-fault gate.',
      workload: 'visible synthetic Mode 5 tile scene plus original 68K ROM loop issuing recurring 32-word VRAM DMA from ROM byte 0x4000 to VRAM 0x6000',
      variants: forward,
      quietPeriodRequired: true,
      noisePolicy: 'retain every run; report host contention and limitations; no automatic threshold or run removal'
    },
    provenance: {
      sourceCommit,
      node: process.version,
      platform: process.platform,
      arch: process.arch,
      cpuModel: os.cpus()[0]?.model || 'unknown',
      logicalCpus: os.cpus().length,
      totalMemoryBytes: os.totalmem(),
      loadAverageAtStart: os.loadavg(),
      emscripten: commandVersion('emcc', ['--version']),
      cmake: commandVersion('cmake', ['--version']),
      corePaths,
      coreSha256: Object.fromEntries(Object.entries(corePaths).map(([key, js]) => [key, {
        js: sha256(js), wasm: sha256(js.replace(/\.js$/, '.wasm'))
      }]))
    },
    pairs,
    pairedSummary: byVariant,
    performanceGate: {
      thresholdRatio: 1.05,
      aggregation: 'median of five paired ratios; per-run p95 is nearest-rank frame p95 within that run',
      noFaultVariants: noFaultVariants,
      details: gateSummary,
      pass: performanceGatePass
    }
  };
  const output = path.resolve(args.out);
  fs.mkdirSync(path.dirname(output), {recursive: true});
  fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`Wrote five-pair benchmark record to ${output}\n`);
}

main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
