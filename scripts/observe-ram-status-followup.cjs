#!/usr/bin/env node
'use strict';
// Preregistered eight-write follow-up using the existing generic observer.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const observer = require('./observe-attract-demo.cjs');
const candidate = require('./observe-ram-gameplay-candidate.cjs');

const FOLLOWUP = Object.freeze({
  name: 'a12-a13-object-region-eight-writes', kind: 1, lineA: 11, lineB: 12,
  affectedWrites: 8, faultTick: 1801, maxTicks: 2400
});
const OWN_FILES = Object.freeze([
  'scripts/observe-ram-status-followup.cjs',
  'tests/test_ram_status_followup.cjs'
]);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function sourceIdentity() {
  const base = candidate.sourceIdentity();
  const repo = path.resolve(__dirname, '..');
  const status = execFileSync('git', ['status', '--porcelain', '--untracked-files=all', '--', ...OWN_FILES],
    {cwd: repo, encoding: 'utf8'}).trim();
  const ownHashes = Object.fromEntries(OWN_FILES.map(file =>
    [file, sha256(fs.readFileSync(path.join(repo, file)))]));
  return {...base, clean: base.clean && !status, sourceDirty: Boolean(base.sourceDirty || status),
    hashes: {...base.hashes, ...ownHashes}};
}

function assembleReport(runs, tool) {
  const report = candidate.buildCandidateReport(runs, tool, FOLLOWUP);
  return {
    schemaVersion: 1,
    protocol: 'object-alias-eight-writes-v1',
    tool,
    settings: {
      trialName: FOLLOWUP.name,
      kind: 'address',
      addressLines: ['A12', 'A13'],
      apiArgs: [FOLLOWUP.kind, FOLLOWUP.lineA, FOLLOWUP.lineB, FOLLOWUP.affectedWrites],
      setterFrame: FOLLOWUP.faultTick - 1,
      effectiveTick: FOLLOWUP.faultTick,
      ticks: FOLLOWUP.maxTicks,
      freshCoreTrials: 6,
      phaseWindow: observer.PHASE_WINDOW,
      externalInput: 'zero every tick',
      cpuRecovery: 'none',
      sourceRevision: 0,
      sourceCommitForLayout: '15dfa3a6ee4c53aeb482233e493755c84b4f3479',
      matchedSourceBuildROM_SHA256: '46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6',
      priorOneWriteContext: {
        args: [1, 11, 12, 1],
        firstAffectedWrite: 'player obStatus at $D022 redirected to $C022',
        observation: '596 player/demo/frame tuples matched at phase 0; CPU, demo and input progression continued'
      },
      sourceBasis: 'Rev 0 defines player obX/obY/obVelX/obVelY at offsets $08/$0C/$10/$12; A12/A13 maps eligible object writes from $D000-$EFFF into the pre-object buffer $C000-$CFFF. Sonic_MdNormal calls Sonic_Move before SpeedToPos. Eight is a fixed small multiwrite budget intended to allow later natural object writes in the same frame to be affected; static source does not establish the dynamic next-write sequence or prove a kinematic write is reached.',
      sourceRanges: {
        objectRegion: {start: 0xd000, endExclusive: 0xf000},
        playerKinematicFields: {start: 0xd008, endExclusive: 0xd014},
        mappedPreObjectBufferRegion: {start: 0xc000, endExclusive: 0xd000}
      }
    },
    protocolAcceptance: report.protocolAcceptance,
    scientificOutcome: report.scientificOutcome,
    runs: report.runs,
    phaseReports: report.phaseReports
  };
}

function verifyPackage(appDirectory) { return candidate.verifyPackage(appDirectory); }

async function main(args) {
  if (args.length !== 3 || args[1] !== '--app') throw new Error(
    'Usage: node scripts/observe-ram-status-followup.cjs /private/path/sonic.md --app /path/to/extracted/VRAMpage-MD');
  const tool = sourceIdentity();
  if (!tool.clean) throw new Error('Follow-up tools and reused observer sources must be committed and clean before a private trial.');
  const rom = fs.readFileSync(args[0]);
  const cartridge = observer.validateRomBuffer(rom);
  const app = verifyPackage(path.resolve(args[2]));
  const factory = require(app.js);
  const runs = await candidate.compareCandidateRuns(
    () => factory({locateFile: name => path.join(path.dirname(app.js), name)}), rom, FOLLOWUP);
  const report = assembleReport(runs, tool);
  report.runtime = {node: process.versions.node, platform: process.platform, arch: process.arch};
  report.cartridge = cartridge;
  report.package = {applicationVersion: app.manifest.application_version,
    sourceCommit: app.manifest.source_commit, corePin: observer.APP_PROFILE.corePin,
    javascriptSHA256: app.javascriptSHA256, wasmSHA256: app.wasmSHA256,
    sourceProject: 'sonicretro/s1disasm'};
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  if (!report.protocolAcceptance.accepted) process.exitCode = 1;
}

if (require.main === module) main(process.argv.slice(2)).catch(error => {
  process.stderr.write(`${error.message}\n`); process.exitCode = 1;
});

module.exports = {FOLLOWUP, OWN_FILES, sourceIdentity, assembleReport, verifyPackage};
