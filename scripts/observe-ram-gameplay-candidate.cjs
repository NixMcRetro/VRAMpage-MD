#!/usr/bin/env node
'use strict';
// Bounded, source-checked configured write pulse. Emits scalar fields and hashes only.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const observer = require('./observe-attract-demo.cjs');
const traceRunner = require('./trace-attract-write.cjs');
const publicPackage = require('./observe-ram-alias-audio-phase.cjs');

const CANDIDATE = Object.freeze({
  name: 'a12-a13-object-region-one-write', kind: 1, lineA: 11, lineB: 12,
  affectedWrites: 1, faultTick: 1801, maxTicks: 2400
});
const SOURCE_LAYOUT = Object.freeze({objectStart: 0xd000, objectEndExclusive: 0xf000,
  preObjectBufferStart: 0xc000, preObjectBufferEndExclusive: 0xd000,
  playerFieldsStart: 0xd008, playerFieldsEndExclusive: 0xd014});
const TOOL_FILES = Object.freeze([
  'scripts/observe-attract-demo.cjs', 'scripts/observe-ram-gameplay-candidate.cjs',
  'scripts/trace-attract-write.cjs', 'scripts/observe-ram-alias-audio-phase.cjs',
  'tests/test_ram_gameplay_candidate.cjs'
]);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function mapWordAddressPair(byteAddress, lineA, lineB) {
  const wordAddress = byteAddress >>> 1;
  const mask = (1 << lineA) | (1 << lineB);
  const mappedWord = (wordAddress & mask) === mask ? wordAddress : (wordAddress & ~mask);
  return ((mappedWord << 1) | (byteAddress & 1)) >>> 0;
}

function classifyFirstWrite(record, candidate = CANDIDATE) {
  if (!record) return {accepted: false, reason: 'missing-write-trace', objectWrite: false, playerField: false};
  const offset = record.ram_offset;
  const mapped = mapWordAddressPair(offset, candidate.lineA, candidate.lineB);
  const exactMap = record.mapped_offset === mapped;
  const width = record.width;
  const originalEnd = offset + width;
  const mappedEnd = record.mapped_offset + width;
  const originalObjectOverlap = offset < SOURCE_LAYOUT.objectEndExclusive && originalEnd > SOURCE_LAYOUT.objectStart;
  const mappedObjectOverlap = record.mapped_offset < SOURCE_LAYOUT.objectEndExclusive &&
    mappedEnd > SOURCE_LAYOUT.objectStart;
  const originalPlayerKinematicFieldOverlap = offset < SOURCE_LAYOUT.playerFieldsEndExclusive &&
    originalEnd > SOURCE_LAYOUT.playerFieldsStart;
  const mappedPlayerKinematicFieldOverlap = record.mapped_offset < SOURCE_LAYOUT.playerFieldsEndExclusive &&
    mappedEnd > SOURCE_LAYOUT.playerFieldsStart;
  const objectWrite = [1, 2].includes(width) && offset >= SOURCE_LAYOUT.objectStart &&
    originalEnd <= SOURCE_LAYOUT.objectEndExclusive;
  const expectedMappedRegion = record.mapped_offset >= SOURCE_LAYOUT.preObjectBufferStart &&
    mappedEnd <= SOURCE_LAYOUT.preObjectBufferEndExclusive;
  const sourceTraceValid = record.reason === 1 && record.frame === CANDIDATE.faultTick - 1 &&
    [1, 2].includes(width) && record.cpu_address >= 0xe00000 && record.cpu_address <= 0xffffff &&
    record.ram_offset === (record.cpu_address & 0xffff);
  const accepted = sourceTraceValid && objectWrite && expectedMappedRegion && exactMap;
  return {accepted, reason: accepted ? null : 'first-write-outside-source-backed-object-alias',
    objectWrite, originalObjectOverlap, mappedObjectOverlap,
    originalPlayerKinematicFieldOverlap, mappedPlayerKinematicFieldOverlap,
    exactAddressMapping: exactMap, mappedPreObjectBufferRegion: expectedMappedRegion,
    effectLabel: originalPlayerKinematicFieldOverlap ?
      'original-player-kinematic-field-write-redirected-out-of-player-object' :
      'object-region-write-redirected-into-pre-object-buffer-region',
    sourceTraceValid,
    expectedMappedOffset: mapped,
    originalRange: {start: offset, endExclusive: originalEnd},
    mappedRange: {start: record.mapped_offset, endExclusive: mappedEnd},
    observedRamOffset: offset, observedMappedOffset: record.mapped_offset};
}

function validTraceMetadata(record, candidate = CANDIDATE) {
  return Boolean(record && record.reason === 1 && record.frame === candidate.faultTick - 1 &&
    [1, 2].includes(record.width) && record.cpu_address >= 0xe00000 && record.cpu_address <= 0xffffff &&
    record.ram_offset === (record.cpu_address & 0xffff) && record.mapped_offset <= 0xffff);
}

function positionDivergenceByLag(baselineTimeline, candidateTimeline, phaseRows) {
  const baselineByTick = new Map(baselineTimeline.map(row => [row.tick, row]));
  const candidateByTick = new Map(candidateTimeline.map(row => [row.tick, row]));
  return phaseRows.map(phase => {
    const demoAligned = phase.comparedPairs === observer.PHASE_WINDOW.candidateTickCount &&
      phase.missingPairs === 0 && phase.demoStateMatches === observer.PHASE_WINDOW.candidateTickCount;
    let current = 0, longest = 0, divergentTicks = 0;
    if (demoAligned) {
      for (let tick = observer.PHASE_WINDOW.candidateTickStart;
           tick <= observer.PHASE_WINDOW.candidateTickEnd; tick++) {
        const candidate = candidateByTick.get(tick);
        const baseline = baselineByTick.get(tick + phase.lag);
        const divergent = Boolean(candidate && baseline &&
          Math.max(Math.abs((candidate.worldXFixed - baseline.worldXFixed) | 0),
            Math.abs((candidate.worldYFixed - baseline.worldYFixed) | 0)) >= 0x10000);
        if (divergent) { current++; divergentTicks++; longest = Math.max(longest, current); }
        else current = 0;
      }
    }
    return {lag: phase.lag, demoAligned, divergentPositionTicksAtLeastOnePixel: divergentTicks,
      longestConsecutiveTicksAtLeastOnePixel: longest, boundedTrajectoryDivergence: demoAligned && longest >= 60};
  });
}

function hasBoundedTrajectoryDivergence(phaseReports) {
  const aligned = phaseReports.filter(row => row.demoAligned);
  return aligned.length === 1 && aligned[0].boundedTrajectoryDivergence === true;
}

function uniqueDemoAlignedLag(phaseReports) {
  const aligned = phaseReports.filter(row => row.demoAligned);
  return {unique: aligned.length === 1, ambiguous: aligned.length !== 1,
    lag: aligned.length === 1 ? aligned[0].lag : null, alignedLagCount: aligned.length};
}

function readConfiguredTrace(core) {
  return traceRunner.readTrace(core);
}

async function tracedTrial(factory, rom, scenario, enabled, spec) {
  let core;
  const trial = scenario === 'baseline'
    ? await observer.runTrial(async () => {
      core = await factory();
      enableTraceAfterStart(core, enabled);
      return core;
    }, rom, 'baseline', {collectSafety: true})
    : await observer.runConfiguredWritePulseTrial(async () => {
      core = await factory();
      enableTraceAfterStart(core, enabled);
      return core;
    }, rom, spec, {collectSafety: true});
  return {trial, firstAffectedWrite: readConfiguredTrace(core)};
}

function enableTraceAfterStart(core, enabled) {
  for (const name of ['_set_logic_write_trace_enabled', '_get_logic_write_trace_state',
    ...['cpu_address', 'ram_offset', 'mapped_offset', 'width', 'frame', 'reason']
      .map(field => `_get_logic_write_trace_${field}`)]) {
    if (typeof core[name] !== 'function') throw new Error(`Missing trace API ${name}.`);
  }
  const start = core._start.bind(core);
  core._start = () => {
    start();
    if (core._set_logic_write_trace_enabled(enabled ? 1 : 0) !== 0) throw new Error('Trace enable rejected.');
  };
}

async function compareCandidateRuns(factory, rom, spec = CANDIDATE, run = tracedTrial) {
  const output = {};
  for (const scenario of ['baseline', spec.name]) {
    const disabled = await run(factory, rom, scenario, false, spec);
    const enabled = await run(factory, rom, scenario, true, spec);
    const repeated = await run(factory, rom, scenario, true, spec);
    const rows = {
      disabled: {observation: disabled.trial, firstAffectedWrite: disabled.firstAffectedWrite},
      enabled: {observation: enabled.trial, firstAffectedWrite: enabled.firstAffectedWrite},
      repeated: {observation: repeated.trial, firstAffectedWrite: repeated.firstAffectedWrite},
      tracePreservesObservation: observer.sameTrials(disabled.trial, enabled.trial) &&
        observer.sameTrials(disabled.trial, repeated.trial),
      repeatIdentical: observer.sameTrials(enabled.trial, repeated.trial) &&
        JSON.stringify(enabled.firstAffectedWrite) === JSON.stringify(repeated.firstAffectedWrite)
    };
    rows.prefaultMatchesBaseline = scenario === 'baseline' ? null :
      ['disabled', 'enabled', 'repeated'].every(key => observer.prefaultMatches(
        output.baseline.disabled.observation, rows[key].observation));
    output[scenario] = rows;
  }
  return output;
}

function protocolAcceptance(runs, sourceCheck, spec = CANDIDATE) {
  const base = runs.baseline;
  const candidate = runs[spec.name];
  const observations = [candidate?.disabled?.observation, candidate?.enabled?.observation,
    candidate?.repeated?.observation, base?.disabled?.observation,
    base?.enabled?.observation, base?.repeated?.observation].filter(Boolean);
  const allZeroInput = observations.length === 6 && observations.every(row =>
    row.externalInputZeroTicks === spec.maxTicks);
  const allBounded = observations.length === 6 && observations.every(row => row.ticks === spec.maxTicks);
  const pulseExactlyOne = [candidate?.enabled?.observation, candidate?.repeated?.observation].every(row =>
    row?.pulse?.requestedAffectedWrites === spec.affectedWrites && row.pulse.finalCoreState === 2 &&
    row.pulse.affectedWritesAtRelease === spec.affectedWrites && row.pulse.releaseTick === spec.faultTick &&
    row.faultSetterFrame === spec.faultTick - 1 && row.effectiveFaultTick === spec.faultTick &&
    row.reportedActivationFrame === spec.faultTick - 1);
  const traces = [candidate?.enabled?.firstAffectedWrite, candidate?.repeated?.firstAffectedWrite];
  const sourceChecks = traces.map(record => classifyFirstWrite(record, spec));
  const traceMetadataIsValid = traces.every(record => validTraceMetadata(record, spec));
  return {
    accepted: Boolean(sourceCheck.clean && base?.tracePreservesObservation && base?.repeatIdentical &&
      candidate?.tracePreservesObservation && candidate?.repeatIdentical && candidate?.prefaultMatchesBaseline &&
      candidate?.disabled?.firstAffectedWrite === null && base?.disabled?.firstAffectedWrite === null &&
      base?.enabled?.firstAffectedWrite === null && base?.repeated?.firstAffectedWrite === null &&
      pulseExactlyOne && allZeroInput && allBounded && traceMetadataIsValid),
    checks: {cleanToolSources: sourceCheck.clean,
      baselineTracePreservesObservation: base?.tracePreservesObservation === true,
      baselineRepeatIdentical: base?.repeatIdentical === true,
      candidateTracePreservesObservation: candidate?.tracePreservesObservation === true,
      candidateRepeatIdentical: candidate?.repeatIdentical === true,
      prefaultMatchesBaseline: candidate?.prefaultMatchesBaseline === true,
      noTraceWhenDisabled: candidate?.disabled?.firstAffectedWrite === null,
      noTraceOnBaseline: [base?.disabled, base?.enabled, base?.repeated].every(row => row?.firstAffectedWrite === null),
      pulseExactlyConfiguredAffectedWrites: pulseExactlyOne, allExternalInputZero: allZeroInput,
      allTrialsWithinBound: allBounded, candidateTraceMetadataValid: traceMetadataIsValid},
    firstWriteSourceChecks: sourceChecks,
    firstWriteTraceMetadataValid: traces.map(record => validTraceMetadata(record, spec))
  };
}

function scientificSafety(runs, spec = CANDIDATE) {
  const candidate = runs[spec.name];
  const observations = [candidate?.disabled?.observation, candidate?.enabled?.observation,
    candidate?.repeated?.observation, runs.baseline?.disabled?.observation,
    runs.baseline?.enabled?.observation, runs.baseline?.repeated?.observation].filter(Boolean);
  const complete = observations.length === 6;
  const noCpuFlags = complete && observations.every(row => row.safety?.cpuNonzeroTicks === 0 &&
    row.safety?.cpuStopTicks === 0 && row.safety?.cpuHaltTicks === 0);
  const demoContinues = complete && observations.every(row =>
    row.safety?.demoActiveTicks === spec.maxTicks - spec.faultTick &&
    row.safety?.postFaultCursorValueChanges > 0 &&
    row.safety?.postFaultHeldPadValueChanges + row.safety?.postFaultPressedPadValueChanges > 0);
  const playerObserved = complete && observations.every(row =>
    row.safety?.playerObjectIdOneTimelineTicks === 602);
  return {accepted: noCpuFlags && demoContinues && playerObserved,
    checks: {noCpuFlags, demoActiveAndProgressing: demoContinues,
      playerObjectIdOneAcrossTimeline: playerObserved},
    observationScopes: {cpuAndDemoSafety: {startTick: 1802, endTick: 2400, ticks: 599},
      playerObjectId: {startTick: 1799, endTick: 2400, ticks: 602}}};
}

function serializeCandidateRuns(runs) {
  return Object.fromEntries(Object.entries(runs).map(([scenario, run]) => [scenario, {
    disabled: {...run.disabled, observation: observer.serializeTrial(run.disabled.observation)},
    enabled: {...run.enabled, observation: observer.serializeTrial(run.enabled.observation)},
    repeated: {...run.repeated, observation: observer.serializeTrial(run.repeated.observation)},
    tracePreservesObservation: run.tracePreservesObservation,
    repeatIdentical: run.repeatIdentical,
    prefaultMatchesBaseline: run.prefaultMatchesBaseline
  }]));
}

function buildCandidateReport(runs, tool, spec = CANDIDATE) {
  const baseline = runs.baseline.disabled.observation;
  const candidate = runs[spec.name];
  const phaseReports = {};
  for (const key of ['enabled', 'repeated']) {
    const candidateObservation = candidate[key].observation;
    const phases = observer.comparePhases(baseline.timeline, candidateObservation.timeline);
    phaseReports[key] = {phases, positionDivergence: positionDivergenceByLag(
      baseline.timeline, candidateObservation.timeline, phases)};
  }
  const enabledAlignment = uniqueDemoAlignedLag(phaseReports.enabled.positionDivergence);
  const repeatAlignment = uniqueDemoAlignedLag(phaseReports.repeated.positionDivergence);
  const uniqueSameLag = enabledAlignment.unique && repeatAlignment.unique &&
    enabledAlignment.lag === repeatAlignment.lag;
  const acceptance = protocolAcceptance(runs, tool, spec);
  const safety = scientificSafety(runs, spec);
  const sourceHypothesisMatches = acceptance.firstWriteSourceChecks.length === 2 &&
    acceptance.firstWriteSourceChecks.every(row => row.accepted);
  const science = {boundedTrajectoryDivergenceObserved: acceptance.accepted && safety.accepted &&
      sourceHypothesisMatches &&
      hasBoundedTrajectoryDivergence(phaseReports.enabled.positionDivergence) &&
      hasBoundedTrajectoryDivergence(phaseReports.repeated.positionDivergence) && uniqueSameLag,
    protocolAccepted: acceptance.accepted,
    sourceHypothesisMatches,
    safety,
    phaseAlignment: {enabled: enabledAlignment, repeated: repeatAlignment, uniqueSameLag},
    interpretation: 'A negative outcome is a valid accepted experiment; phase-aligned demo state with no sustained one-pixel player-position difference does not establish trajectory divergence.'};
  return {protocolAcceptance: acceptance, scientificOutcome: science,
    phaseReports, runs: serializeCandidateRuns(runs)};
}

function sourceIdentity() {
  const repo = path.resolve(__dirname, '..');
  const sourceCommit = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: repo, encoding: 'utf8'}).trim();
  const status = execFileSync('git', ['status', '--porcelain', '--untracked-files=all', '--', ...TOOL_FILES],
    {cwd: repo, encoding: 'utf8'}).trim();
  const hashes = Object.fromEntries(TOOL_FILES.map(file => [file, sha256(fs.readFileSync(path.join(repo, file)))]));
  return {sourceCommit, sourceDirty: Boolean(status), clean: !status, hashes};
}

function verifyPackage(appDirectory) {
  const verified = publicPackage.validateAppDirectory(appDirectory);
  return {...verified, js: verified.coreJsPath};
}

async function main(args) {
  if (args.length !== 3 || args[1] !== '--app') throw new Error(
    'Usage: node scripts/observe-ram-gameplay-candidate.cjs /private/path/sonic.md --app /path/to/extracted/VRAMpage-MD');
  const tool = sourceIdentity();
  if (!tool.clean) throw new Error('Configured candidate tools must be committed and clean before a private trial.');
  const rom = fs.readFileSync(args[0]);
  const cartridge = observer.validateRomBuffer(rom);
  const app = verifyPackage(path.resolve(args[2]));
  const factory = require(app.js);
  const runs = await compareCandidateRuns(
    () => factory({locateFile: name => path.join(path.dirname(app.js), name)}), rom, CANDIDATE);
  const report = buildCandidateReport(runs, tool);
  process.stdout.write(JSON.stringify({schemaVersion: 1, protocol: 'configured-write-pulse-gameplay-v1',
    runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    tool, cartridge,
    package: {applicationVersion: app.manifest.application_version, sourceCommit: app.manifest.source_commit,
      corePin: observer.APP_PROFILE.corePin, javascriptSHA256: app.javascriptSHA256, wasmSHA256: app.wasmSHA256,
      sourceProject: 'sonicretro/s1disasm', sourceCommitForLayout: '15dfa3a6ee4c53aeb482233e493755c84b4f3479',
      sourceRevision: 0, matchedSourceBuildROM_SHA256: cartridge.romSHA256,
      sourceFilesForLayout: ['_Variables.asm', '_Constants.asm']},
    settings: {trialName: CANDIDATE.name, kind: 'address', addressLines: ['A12', 'A13'],
      apiArgs: [CANDIDATE.kind, CANDIDATE.lineA, CANDIDATE.lineB, CANDIDATE.affectedWrites],
      setterFrame: 1800, effectiveTick: CANDIDATE.faultTick, ticks: CANDIDATE.maxTicks, freshCoreTrials: 6,
      phaseWindow: observer.PHASE_WINDOW, externalInput: 'zero every tick', cpuRecovery: 'none',
      sourceRanges: {objectRegion: {start: SOURCE_LAYOUT.objectStart, endExclusive: SOURCE_LAYOUT.objectEndExclusive},
        playerKinematicFields: {start: SOURCE_LAYOUT.playerFieldsStart, endExclusive: SOURCE_LAYOUT.playerFieldsEndExclusive},
        mappedPreObjectBufferRegion: {start: SOURCE_LAYOUT.preObjectBufferStart,
          endExclusive: SOURCE_LAYOUT.preObjectBufferEndExclusive}},
      sourceHypothesis: 'A12/A13 maps eligible object-region writes in $D000-$EFFF into the source-allocated pre-object buffer region $C000-$CFFF; first affected write is trace-gated.'},
    protocolAcceptance: report.protocolAcceptance, scientificOutcome: report.scientificOutcome,
    runs: report.runs, phaseReports: report.phaseReports}, null, 2) + '\n');
  if (!report.protocolAcceptance.accepted) process.exitCode = 1;
}

if (require.main === module) main(process.argv.slice(2)).catch(error => {
  process.stderr.write(`${error.message}\n`); process.exitCode = 1;
});

module.exports = {CANDIDATE, SOURCE_LAYOUT, mapWordAddressPair, classifyFirstWrite,
  positionDivergenceByLag, hasBoundedTrajectoryDivergence, compareCandidateRuns,
  protocolAcceptance, serializeCandidateRuns, buildCandidateReport, verifyPackage, sourceIdentity};
