'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const {execFileSync} = require('node:child_process');
const observer = require('../scripts/observe-attract-demo.cjs');
const candidate = require('../scripts/observe-ram-gameplay-candidate.cjs');
const followup = require('../scripts/observe-ram-status-followup.cjs');

const spec = followup.FOLLOWUP;
const trace = {cpu_address: 0xffd022, ram_offset: 0xd022, mapped_offset: 0xc022,
  width: 1, frame: 1800, reason: 1};
const pulse = (release = 8) => ({requestedAffectedWrites: 8, finalCoreState: 2,
  affectedWritesAtRelease: release, releaseTick: 1801});

function makeTrial(scenario, diverge = false, alterRelease = null) {
  const timeline = [];
  for (let tick = 1799; tick <= 2400; tick++) {
    const changed = diverge && tick >= 1803 && tick < 1863;
    timeline.push({tick, rawActiveFrameSHA256: 'same-frame', gameMode: 8, demoFlag: 1,
      demoLevelNumber: 1, demoCursor: tick, demoCountdown: tick & 0xff,
      heldPad: tick & 7, pressedPad: tick & 15, playerObjectId: 1,
      worldXFixed: 0x640000 + (changed ? 0x10000 : 0), worldYFixed: 0x200000,
      velocityX: 0, velocityY: 0});
  }
  const isCandidate = scenario !== 'baseline';
  return {scenario, ticks: 2400, externalInputZeroTicks: 2400,
    preFaultStreamSHA256: 'same-prefault', streamSHA256: 'stream', timelineSHA256: 'timeline',
    cursorValueChanges: 300, heldPadValueChanges: 200, samples: [{tick: 1799, gameMode: 8}], timeline,
    faultSetterFrame: isCandidate ? 1800 : null,
    effectiveFaultTick: isCandidate ? 1801 : null,
    reportedActivationFrame: isCandidate ? 1800 : null,
    pulse: isCandidate ? pulse(alterRelease ?? 8) : null,
    safety: {cpuStopTicks: 0, cpuHaltTicks: 0, cpuNonzeroTicks: 0,
      demoActiveTicks: 599, postFaultCursorValueChanges: 100,
      postFaultHeldPadValueChanges: 20, postFaultPressedPadValueChanges: 20,
      playerObjectIdOneTimelineTicks: 602}};
}

async function mockRuns({diverge = false, alterRelease = null} = {}) {
  const calls = [];
  const runs = await candidate.compareCandidateRuns(null, null, spec,
    async (_factory, _rom, scenario, enabled) => {
      calls.push([scenario, enabled]);
      const trial = makeTrial(scenario, diverge && scenario !== 'baseline',
        scenario !== 'baseline' ? alterRelease : null);
      return {trial, firstAffectedWrite: enabled && scenario !== 'baseline' ? trace : null};
    });
  return {runs, calls};
}

(async () => {
  let groups = 0;
  assert.equal(Object.isFrozen(spec), true);
  assert.deepEqual(observer.validateConfiguredWritePulse(spec).args, [1, 11, 12, 8]);
  assert.equal(spec.faultTick, 1801);
  assert.equal(spec.maxTicks, 2400);
  assert.equal(candidate.mapWordAddressPair(0xd022, 11, 12), 0xc022);
  assert.equal(candidate.classifyFirstWrite(trace, spec).accepted, true);
  assert.equal(candidate.classifyFirstWrite(trace, spec).originalPlayerKinematicFieldOverlap, false);
  groups++;

  const {runs, calls} = await mockRuns();
  assert.deepEqual(calls, [['baseline', false], ['baseline', true], ['baseline', true],
    [spec.name, false], [spec.name, true], [spec.name, true]]);
  assert.equal(runs[spec.name].disabled.observation.pulse.requestedAffectedWrites, 8);
  assert.equal(runs[spec.name].enabled.observation.pulse.affectedWritesAtRelease, 8);
  groups++;

  const tool = {clean: true, sourceDirty: false, sourceCommit: 'a'.repeat(40),
    hashes: {'scripts/observe-attract-demo.cjs': 'b'.repeat(64)}};
  for (const diverge of [false, true]) {
    const generated = await mockRuns({diverge});
    const report = followup.assembleReport(generated.runs, tool);
    assert.equal(report.protocol, 'object-alias-eight-writes-v1');
    assert.deepEqual(report.settings.apiArgs, [1, 11, 12, 8]);
    assert.equal(report.settings.sourceRevision, 0);
    assert.equal(report.protocolAcceptance.accepted, true);
    assert.equal(report.scientificOutcome.boundedTrajectoryDivergenceObserved, diverge);
    assert.equal(report.scientificOutcome.phaseAlignment.uniqueSameLag, true);
    assert.equal(report.phaseReports.enabled.phases.find(row => row.lag === 0).demoStateMatches, 596);
    assert.doesNotMatch(JSON.stringify(report), /"timeline"\s*:/);
  }
  groups++;

  const badRelease = await mockRuns({alterRelease: 1});
  const integrityReport = followup.assembleReport(badRelease.runs, tool);
  assert.equal(integrityReport.protocolAcceptance.accepted, false);
  assert.equal(badRelease.runs[spec.name].tracePreservesObservation, true);
  assert.equal(badRelease.runs[spec.name].repeatIdentical, true);
  assert.equal(integrityReport.protocolAcceptance.checks.pulseExactlyConfiguredAffectedWrites, false);
  assert.equal(integrityReport.scientificOutcome.boundedTrajectoryDivergenceObserved, false);
  const badSource = await mockRuns();
  assert.equal(followup.assembleReport(badSource.runs, {...tool, clean: false})
    .protocolAcceptance.accepted, false);
  groups++;

  const tempRepo = fs.mkdtempSync(path.join(os.tmpdir(), 'ram-status-followup-identity-'));
  try {
    const repoRoot = path.resolve(__dirname, '..');
    const identityFiles = [
      'scripts/observe-attract-demo.cjs',
      'scripts/observe-ram-gameplay-candidate.cjs',
      'scripts/trace-attract-write.cjs',
      'scripts/observe-ram-alias-audio-phase.cjs',
      'tests/test_ram_gameplay_candidate.cjs',
      'scripts/observe-ram-status-followup.cjs',
      'tests/test_ram_status_followup.cjs'
    ];
    for (const relative of identityFiles) {
      const destination = path.join(tempRepo, relative);
      fs.mkdirSync(path.dirname(destination), {recursive: true});
      fs.copyFileSync(path.join(repoRoot, relative), destination);
    }
    execFileSync('git', ['init', '-q'], {cwd: tempRepo});
    execFileSync('git', ['add', ...identityFiles], {cwd: tempRepo});
    execFileSync('git', ['-c', 'user.name=Test Fixture', '-c', 'user.email=fixture@example.invalid',
      '-c', 'commit.gpgsign=false', 'commit', '-qm', 'identity fixture'], {cwd: tempRepo});
    const fixtureFollowup = require(path.join(tempRepo, 'scripts/observe-ram-status-followup.cjs'));
    const cleanIdentity = fixtureFollowup.sourceIdentity();
    assert.equal(cleanIdentity.clean, true);
    assert.equal(cleanIdentity.sourceDirty, false);
    assert.deepEqual(Object.keys(cleanIdentity.hashes).sort(), identityFiles.slice().sort());
    const ownScript = path.join(tempRepo, 'scripts/observe-ram-status-followup.cjs');
    const ownBytes = fs.readFileSync(ownScript);
    fs.appendFileSync(ownScript, '\n// dirty own-file fixture\n');
    const ownDirty = fixtureFollowup.sourceIdentity();
    assert.equal(ownDirty.clean, false);
    assert.equal(ownDirty.sourceDirty, true);
    assert.equal(ownDirty.sourceCommit, cleanIdentity.sourceCommit);
    fs.writeFileSync(ownScript, ownBytes);
    assert.equal(fixtureFollowup.sourceIdentity().clean, true);
    const baseHelper = path.join(tempRepo, 'scripts/observe-ram-gameplay-candidate.cjs');
    const baseBytes = fs.readFileSync(baseHelper);
    fs.appendFileSync(baseHelper, '\n// dirty base-file fixture\n');
    const baseDirty = fixtureFollowup.sourceIdentity();
    assert.equal(baseDirty.clean, false);
    assert.equal(baseDirty.sourceDirty, true);
    assert.equal(baseDirty.sourceCommit, cleanIdentity.sourceCommit);
  } finally { fs.rmSync(tempRepo, {recursive: true, force: true}); }
  groups++;

  const invalidCli = spawnSync(process.execPath, [path.resolve(__dirname,
    '../scripts/observe-ram-status-followup.cjs'), '--invalid'], {encoding: 'utf8'});
  assert.equal(invalidCli.status, 1);
  assert.match(invalidCli.stderr, /Usage: node scripts\/observe-ram-status-followup/);
  groups++;
  console.log(`RAM status follow-up: ${groups} groups passed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
