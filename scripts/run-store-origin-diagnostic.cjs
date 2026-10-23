#!/usr/bin/env node
/* Private six-trial store-origin diagnostic. Emits scalar metadata and hashes only. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const observer = require('./observe-attract-demo.cjs');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const FIELDS = ['cpu_address','ram_offset','mapped_offset','width','frame','reason'];

function diag(core) {
  const traceState = core._get_logic_write_trace_state();
  const diagState = core._get_store_diag_state();
  if (traceState === 0 && diagState === 0) return null;
  if (traceState !== 2 || diagState !== 1) throw new Error('First affected write diagnostic is incomplete.');
  const trace = Object.fromEntries(FIELDS.map(k => [k, core[`_get_logic_write_trace_${k}`]() >>> 0]));
  const pc = core._get_store_diag_pc() >>> 0;
  const pcKnownRaw = core._get_store_diag_pc_known() >>> 0;
  const pcKnown = pcKnownRaw === 1;
  const valueClass = core._get_store_diag_value_class() >>> 0;
  const width = core._get_store_diag_width() >>> 0;
  if (trace.cpu_address > 0xffffff || trace.ram_offset !== (trace.cpu_address & 0xffff) ||
      trace.mapped_offset > 0xffff || ![1,2].includes(trace.width) || ![1,2,3].includes(trace.reason) ||
      width !== trace.width || pc > 0xffffff || ![0,1].includes(pcKnownRaw) || ![1,2].includes(valueClass) ||
      (!pcKnown && pc !== 0)) throw new Error('Invalid store-origin metadata.');
  const vblankCandidate = trace.cpu_address === 0xfff62a && trace.ram_offset === 0xf62a &&
      trace.mapped_offset === 0xf22a && width === 1 && trace.reason === 1;
  return {trace, instructionPC: pcKnown ? pc : null, pcKnown, originalTargetByteClass: ['unknown','zero','nonzero'][valueClass],
    vblankCandidate, interpretation: vblankCandidate && valueClass ? (valueClass === 1 ? 'zero-write' : 'nonzero-write') : 'uninterpreted'};
}

async function trial(factory, rom, scenario, enabled) {
  let core;
  const observed = await observer.runTrial(async () => {
    core = await factory();
    const names = ['_set_logic_write_trace_enabled','_get_logic_write_trace_state', ...FIELDS.map(k => `_get_logic_write_trace_${k}`),
      '_get_store_diag_state','_get_store_diag_pc','_get_store_diag_pc_known','_get_store_diag_value_class','_get_store_diag_width'];
    for (const n of names) if (typeof core[n] !== 'function') throw new Error(`Missing private diagnostic export ${n}.`);
    const start = core._start.bind(core);
    core._start = () => { start(); if (core._set_logic_write_trace_enabled(enabled ? 1 : 0) !== 0) throw new Error('Trace enable rejected.'); };
    return core;
  }, rom, scenario);
  return {observation: observer.serializeTrial(observed), record: diag(core)};
}

function checkAcceptance(runs, publicEquivalent, publicRuns) {
  const fault = runs['A10A11-one-write'];
  const pulseAccepted = ['enabled','repeated'].every(k => fault[k].observation.pulse?.releaseTick === 1801 &&
    fault[k].observation.pulse?.affectedWritesAtRelease === 1 && fault[k].observation.pulse?.finalCoreState === 2);
  const repeatsMatch = ['baseline','A10A11-one-write'].every(name =>
    JSON.stringify(runs[name].enabled.observation) === JSON.stringify(runs[name].repeated.observation) &&
    JSON.stringify(runs[name].enabled.record) === JSON.stringify(runs[name].repeated.record));
  const preFaultMatches = ['baseline','A10A11-one-write'].every(name =>
    observer.prefaultMatches(runs[name].disabled.observation, runs[name].enabled.observation) &&
    observer.prefaultMatches(runs[name].disabled.observation, runs[name].repeated.observation)) &&
    ['disabled','enabled','repeated'].every(k => observer.prefaultMatches(
      runs.baseline[k].observation, fault[k].observation)) &&
    observer.prefaultMatches(publicRuns.baseline, publicRuns['A10A11-one-write']);
  const timingAndInput = ['baseline','A10A11-one-write'].every(name =>
    ['disabled','enabled','repeated'].every(k => {
      const o = runs[name][k].observation;
      return o.externalInputZeroTicks === 2400 && (name === 'baseline' ||
        (o.faultSetterFrame === 1800 && o.effectiveFaultTick === 1801 && o.reportedActivationFrame === 1800));
    })) && ['baseline','A10A11-one-write'].every(name => {
      const o = publicRuns[name];
      return o.externalInputZeroTicks === 2400 && (name === 'baseline' ||
        (o.faultSetterFrame === 1800 && o.effectiveFaultTick === 1801 && o.reportedActivationFrame === 1800));
    });
  const noUnexpectedTrace = ['baseline','A10A11-one-write'].every(name => runs[name].disabled.record === null) &&
    ['disabled','enabled','repeated'].every(k => runs.baseline[k].record === null);
  const targetProven = fault.enabled.record?.vblankCandidate === true && fault.enabled.record?.pcKnown === true &&
    fault.enabled.record?.instructionPC !== null && fault.enabled.record?.interpretation !== 'uninterpreted' &&
    JSON.stringify(fault.enabled.record) === JSON.stringify(fault.repeated.record);
  const diagnosticNoninterference = ['baseline','A10A11-one-write'].every(name => runs[name].noninterference);
  const publicCoreEquivalent = Object.values(publicEquivalent).length === 2 && Object.values(publicEquivalent).every(Boolean);
  const accepted = {noUnexpectedTrace, diagnosticNoninterference, publicCoreEquivalent, pulseAccepted,
    repeatsMatch, preFaultMatches, timingAndInput, targetProven};
  return { ...accepted, passes: Object.values(accepted).every(Boolean) };
}

async function main(args) {
  if (args.length !== 3) throw new Error('Usage: node scripts/run-store-origin-diagnostic.cjs /private/path/sonic.md EMPTY_DIAGNOSTIC_OUTPUT_ROOT /path/to/extracted-public-v0.2.7');
  const rom = fs.readFileSync(args[0]);
  const cartridge = observer.validateRomBuffer(rom);
  const output = path.resolve(args[1]);
  const provenance = JSON.parse(fs.readFileSync(path.join(output,'PROVENANCE.json')));
  if (provenance.kind !== 'private diagnostic build; not public v0.2.7') throw new Error('Diagnostic provenance mismatch.');
  const source = path.join(output,'wasm-genplus');
  const sourceHash = crypto.createHash('sha256');
  const files = [];
  function walk(dir) { for (const entry of fs.readdirSync(dir,{withFileTypes:true})) { if (entry.name === '.git' || entry.name === 'build' || entry.name === 'node_modules') continue; const file=path.join(dir,entry.name); if(entry.isDirectory()) walk(file); else if (!['src/main/js/genplus.js','src/main/js/genplus.wasm'].includes(path.relative(source,file).split(path.sep).join('/'))) files.push(file); } }
  walk(source);
  for (const file of files.sort()) { sourceHash.update(path.relative(source,file).split(path.sep).join('/')); sourceHash.update(Buffer.from(sha(fs.readFileSync(file)),'hex')); }
  if (sourceHash.digest('hex') !== provenance.stagedSourceTreeSHA256) throw new Error('Staged source tree hash does not match provenance. Rebuild the diagnostic stage.');
  const repo = path.resolve(__dirname,'..');
  for (const [name,digest] of Object.entries(provenance.toolSourcesSHA256 || {})) {
    if (sha(fs.readFileSync(path.join(repo,name))) !== digest) throw new Error(`Diagnostic dependency hash mismatch: ${name}`);
  }
  const commit = require('node:child_process').execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim();
  if (commit !== provenance.repositoryCommit) throw new Error('Repository source commit changed after diagnostic staging.');
  const publicPackage = require('./observe-ram-alias-audio-phase.cjs').validateAppDirectory(path.resolve(args[2]));
  const js = path.join(output,'wasm-genplus/src/main/js/genplus.js');
  const wasm = path.join(output,'wasm-genplus/src/main/js/genplus.wasm');
  if (!fs.existsSync(js) || !fs.readFileSync(wasm).subarray(0,4).equals(Buffer.from([0,97,115,109]))) throw new Error('Missing custom diagnostic core.');
  const factory = require(js);
  const publicFactory = require(publicPackage.coreJsPath);
  const runs = {};
  for (const name of ['baseline','A10A11-one-write']) {
    const disabled = await trial(() => factory({locateFile:n=>path.join(path.dirname(js),n)}),rom,name,false);
    const first = await trial(() => factory({locateFile:n=>path.join(path.dirname(js),n)}),rom,name,true);
    const repeated = await trial(() => factory({locateFile:n=>path.join(path.dirname(js),n)}),rom,name,true);
    runs[name] = {disabled,enabled:first,repeated,noninterference:JSON.stringify(disabled.observation)===JSON.stringify(first.observation)&&JSON.stringify(disabled.observation)===JSON.stringify(repeated.observation)};
  }
  const publicRuns = {};
  for (const name of ['baseline','A10A11-one-write']) {
    const obs = await observer.runTrial(()=>publicFactory({locateFile:n=>path.join(path.dirname(publicPackage.coreJsPath),n)}),rom,name);
    publicRuns[name] = observer.serializeTrial(obs);
  }
  const publicEquivalent = Object.fromEntries(['baseline','A10A11-one-write'].map(name=>[name,
    JSON.stringify(runs[name].disabled.observation)===JSON.stringify(publicRuns[name])]));
  const acceptance = checkAcceptance(runs, publicEquivalent, publicRuns);
  const outputRecord = {schemaVersion:1,protocol:'private-store-origin-v1',applicationIdentity:'custom diagnostic build; not public v0.2.7',
    provenance, cartridge, customCore:{javascriptSHA256:sha(fs.readFileSync(js)),wasmSHA256:sha(fs.readFileSync(wasm))},
    publicCore:{sourceCommit:publicPackage.manifest.source_commit,javascriptSHA256:publicPackage.javascriptSHA256,wasmSHA256:publicPackage.wasmSHA256},
    settings:{ticks:2400,externalInput:'zero every tick',faultTick:1801,pulse:'A10/A11 one affected write',recovery:'none'},
    acceptance,publicRuns,runs};
  process.stdout.write(JSON.stringify(outputRecord,null,2)+'\n');
  if (!acceptance.passes) process.exitCode=1;
}
if (require.main === module) main(process.argv.slice(2)).catch(e=>{process.stderr.write(e.message+'\n');process.exitCode=1;});
module.exports={diag,trial,checkAcceptance};
