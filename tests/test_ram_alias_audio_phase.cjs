'use strict';
const assert = require('node:assert/strict');
const {hashFloatSamples, readNamedRamScalars, compareAudioPhase, AUDIO, STATE_LAYOUT,
  summarizeAudioRows, selectedSamples, serializeObserverSummary, assertBoundedReport} =
  require('../scripts/observe-ram-alias-audio-phase.cjs');

let cases = 0;
const heap = new Uint8Array(64);
for (let i = 0; i < 16; i++) new DataView(heap.buffer).setFloat32(i * 4, i / 4, true);
assert.equal(hashFloatSamples(heap, 0, 0, 16).length, 64);
assert.equal(hashFloatSamples(heap, 0, 0, 16),
  'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
assert.equal(hashFloatSamples(heap, 0, 16, 16).length, 64);
assert.notEqual(hashFloatSamples(heap, 0, 3, 16), hashFloatSamples(heap, 0, 4, 16));
assert.throws(() => hashFloatSamples(heap, 0, -1, 16), /invalid/i);
assert.throws(() => hashFloatSamples(heap, 0, 17, 16), /invalid/i);
assert.throws(() => hashFloatSamples(heap, 4, 16, 16), /invalid/i);
assert.throws(() => hashFloatSamples(heap, 0, 1.5, 16), /invalid/i);
const known = new Uint8Array(8);
new DataView(known.buffer).setFloat32(0, 1, true);
new DataView(known.buffer).setFloat32(4, -2, true);
assert.equal(hashFloatSamples(known, 0, 2, 2),
  'ee4ac73c2bd27756ab82780f27c73a7bc4d3f0bb6acb37e008bc27eccd7e588b');
assert.equal(AUDIO.capacity, 2048);
const ramHeap = new Uint8Array(0x10000 + 32);
const ramBase = 8;
// Literal addresses deliberately make this fixture independent of STATE_LAYOUT.
ramHeap[ramBase + (0xf62a ^ 1)] = 0x11;
ramHeap[ramBase + (0xf22a ^ 1)] = 0x22;
ramHeap[ramBase + (0xf84a ^ 1)] = 0x33;
assert.deepEqual(readNamedRamScalars(ramHeap, ramBase), {
  vBlankRoutine: 0x11, sfxFm3TrackAMSFMSPan: 0x22
});
assert.equal(ramHeap[ramBase + (0xf84a ^ 1)], 0x33);
assert.deepEqual(STATE_LAYOUT, {vBlankRoutine: 0xf62a,
  sfxFm3TrackAMSFMSPan: 0xf22a, spriteBufferByte: 0xf84a});
assert.equal(0x40 + 18 * 0x30 + 0x220, 0x5c0);
assert.equal(0xf000 + 0x5c0 + 0x40, 0xf600);
assert.equal(0xf600 + 0x2a, 0xf62a);
cases++;

function row(tick, patch = {}) {
  return {tick, sampleCount: 2, completePairs: 2, leftSHA256: `left-${tick}`, rightSHA256: `right-${tick}`,
    gameMode: 8, demoFlag: 1, demoLevelNumber: 2,
    demoCursor: tick, demoCountdown: 3, heldPad: 0, pressedPad: 0,
    playerObjectId: 1, worldXFixed: tick, worldYFixed: tick + 1,
    velocityX: 2, velocityY: 3, rawActiveFrameSHA256: `frame-${tick}`, ...patch};
}
const baseline = Array.from({length: 602}, (_, i) => row(1799 + i));
const same = Array.from({length: 602}, (_, i) => row(1799 + i));
const equal = compareAudioPhase(baseline, same, 0);
assert.equal(equal.comparedPairs, 596);
assert.equal(equal.missingPairs, 0);
assert.equal(equal.completeSamplePairs, 596);
assert.equal(equal.audioMatches, 596);
assert.equal(equal.vBlankRoutineMatches, 596);
assert.equal(equal.sfxFm3TrackAMSFMSPanMatches, 596);
assert.equal(equal.demoMatches, 596);
assert.equal(equal.playerMatches, 596);
assert.equal(equal.frameMatches, 596);
const different = Array.from({length: 602}, (_, i) => row(1799 + i,
  i === 4 ? {rightSHA256: 'different', sfxFm3TrackAMSFMSPan: 9} : {}));
const negative = compareAudioPhase(baseline, different, 0);
assert.equal(negative.rightHashMatches, 595);
assert.equal(negative.audioMatches, 595);
assert.equal(negative.sfxFm3TrackAMSFMSPanMatches, 595);
const countMismatch = Array.from({length: 602}, (_, i) => row(1799 + i,
  i === 5 ? {sampleCount: 1, completePairs: 1} : {}));
const counts = compareAudioPhase(baseline, countMismatch, 0);
assert.equal(counts.sampleCountMatches, 595);
assert.equal(counts.audioMatches, 595);
const emptyRows = Array.from({length: 602}, (_, i) => row(1799 + i,
  {sampleCount: 0, completePairs: 0, leftSHA256: hashFloatSamples(heap, 0, 0, 16),
    rightSHA256: hashFloatSamples(heap, 0, 0, 16)}));
const emptyComparison = compareAudioPhase(emptyRows, emptyRows, 0);
assert.equal(emptyComparison.completeSamplePairs, 0);
assert.equal(emptyComparison.zeroSamplePairs, 596);
assert.equal(emptyComparison.sampleCountMatches, 596);
assert.equal(emptyComparison.audioMatches, 0);

for (const offset of [-2, -1, 0, 1, 2]) {
  const phaseShifted = Array.from({length: 602}, (_, i) => {
    const tick = 1799 + i;
    const source = baseline.find(r => r.tick === tick + offset);
    return row(tick, source ? {...source, tick} : {});
  });
  const matched = compareAudioPhase(baseline, phaseShifted, offset);
  assert.equal(matched.comparedPairs, 596);
  assert.equal(matched.missingPairs, 0);
  assert.equal(matched.audioMatches, 596);
  assert.equal(matched.frameMatches, 596);
}
assert.equal(compareAudioPhase(baseline, same.filter(r => r.tick !== 1803), -2).missingPairs, 1);
assert.equal(compareAudioPhase(baseline.filter(r => r.tick !== 1801), same, -2).missingPairs, 1);
assert.equal(compareAudioPhase(baseline.filter(r => r.tick !== 2400), same, 2).missingPairs, 1);
assert.equal(compareAudioPhase(baseline, same.filter(r => r.tick !== 2398), 2).missingPairs, 1);
const aligned = Array.from({length: 602}, (_, i) => {
  const tick = 1799 + i;
  const source = baseline.find(r => r.tick === tick + 1);
  return row(tick, source ? {...source, tick} : {});
});
assert.equal(compareAudioPhase(baseline, aligned, 1).audioMatches, 596);
assert.equal(compareAudioPhase(baseline, aligned, 0).audioMatches, 0);
assert.throws(() => compareAudioPhase(baseline, same, 3), /offset/);
const incomplete = same.filter(r => r.tick !== 1803);
const missing = compareAudioPhase(baseline, incomplete, -2);
assert.equal(missing.comparedPairs + missing.missingPairs, 596);
assert.equal(missing.missingPairs, 1);

const ticks = [1799, 1800, 1801, 1860, 1920, 2100, 2400];
const fakeTrial = {scenario: 'fixture', ticks: 2400, samples: ticks.map(tick => row(tick)),
  timeline: Array.from({length: 602}, (_, i) => row(1799 + i)),
  audioTimeline: Array.from({length: 2400}, (_, i) => ({...row(i + 1), sampleCount: 2,
    completePairs: 2, leftSHA256: 'a'.repeat(64), rightSHA256: 'b'.repeat(64)}))};
const privacyFixture = {summary: serializeObserverSummary(fakeTrial), selected: selectedSamples(fakeTrial),
  audio: summarizeAudioRows(fakeTrial.audioTimeline)};
assert.equal(privacyFixture.selected.length, 7);
assert.equal(privacyFixture.audio.tickCount, 2400);
assertBoundedReport(privacyFixture);
assert.throws(() => assertBoundedReport({timeline: [1]}), /forbidden/);
assert.throws(() => assertBoundedReport({audioTimeline: [1]}), /forbidden/);
assert.throws(() => assertBoundedReport({data: new Array(8).fill(0)}), /longer/);
cases++;
process.stdout.write(`RAM alias audio phase tests passed (${cases} groups).\n`);
