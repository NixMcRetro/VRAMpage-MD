'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const path = require('node:path');
const {fmToneCartridge, z80FmAndPsgCartridge, createCore, nextAudio, fmStatusProbe, fmStatusPorts} =
  require('./test_fm_data_runtime.cjs');

const [proofArg, runtimeArg, normalArg] = process.argv.slice(2);
assert.ok(proofArg && runtimeArg && normalArg,
  'Pass proof, production runtime, and unmodified production core paths');
const proofPath = path.resolve(proofArg);
const runtimePath = path.resolve(runtimeArg);
const normalPath = path.resolve(normalArg);

async function modelCore(model, rom) {
  return createCore(proofPath, rom, core => {
    assert.equal(core._fm_model_proof_request(model), 0);
    assert.equal(core._fm_model_proof_pending_model(), model);
  });
}

function sample(core) {
  const audio = nextAudio(core);
  assert.ok(audio.count > 0);
  assert.ok([...audio.left, ...audio.right].every(Number.isFinite));
  return audio;
}

function pcm(core) {
  const audio = sample(core);
  assert.ok([...audio.left, ...audio.right].some(value => Math.abs(value) > 0.0001));
  return audio;
}

function visibleState(core) {
  const frame = core._get_frame_buffer_ref();
  const ram = core._get_logic_ram_ref();
  return {
    pixels: Buffer.from(core.HEAPU8.subarray(frame, frame + 640 * 480 * 4)),
    ram: Buffer.from(core.HEAPU8.subarray(ram, ram + 0x10000))
  };
}

function assertPcmEqual(a, b, label) {
  assert.equal(a.count, b.count, `${label}: sample count`);
  assert.deepEqual(a.left, b.left, `${label}: left PCM`);
  assert.deepEqual(a.right, b.right, `${label}: right PCM`);
}

const digest = data => crypto.createHash('sha256').update(Buffer.from(data.buffer,
  data.byteOffset, data.byteLength)).digest('hex');

async function main() {
  const rom = fmToneCartridge();
  const normal = await createCore(normalPath, rom);
  const runtime = await createCore(runtimePath, rom);
  const normalPcm = pcm(normal), normalState = visibleState(normal);
  const runtimePcm = pcm(runtime), runtimeState = visibleState(runtime);
  assertPcmEqual(runtimePcm, normalPcm, 'default proof core matches shipped production core');
  assert.deepEqual(runtimeState, normalState,
    'default proof core preserves production pixels and native memory progress');
  assert.deepEqual(fmStatusProbe(runtime), fmStatusProbe(normal),
    'default proof core preserves production FM status reads');

  const invalid = await createCore(proofPath, rom, core => {
    assert.equal(core._fm_model_proof_active_model(), -1,
      'module has no effective FM model before cartridge start');
    assert.equal(core._fm_model_proof_pending_model(), 0,
      'module defaults its pending FM model to Discrete');
    const before = core._fm_model_proof_pending_model();
    for (const value of [-1, 2, 3, 1.5]) assert.equal(core._fm_model_proof_request(value), 1);
    assert.equal(core._fm_model_proof_pending_model(), before,
      'unsupported requests leave pending selection unchanged');
  });
  assert.equal(invalid._fm_model_proof_active_model(), 0);

  const modelRuns = [];
  for (const model of [0, 1]) {
    const first = await modelCore(model, rom);
    assert.equal(first._fm_model_proof_active_model(), model);
    const samples = pcm(first), status = fmStatusProbe(first), ports = fmStatusPorts(first);
    assert.equal(status[0] & 0x80, 0x80, `model ${model}: immediate status reports busy`);
    assert.equal(status[1] & 0x80, 0, `model ${model}: delayed status clears busy`);
    if (model === 0) assert.deepEqual([ports[2], ports[3]], [0, 0],
      'Discrete model reads from the unconnected second status port return zero');
    else {
      assert.equal(ports[2] & 0x80, 0x80, 'Integrated model second port exposes immediate busy');
      assert.equal(ports[3] & 0x80, 0, 'Integrated model second port exposes delayed status');
    }
    const repeat = await modelCore(model, rom);
    assertPcmEqual(pcm(repeat), samples, `model ${model} deterministic PCM`);
    assert.deepEqual(fmStatusProbe(repeat), status, `model ${model} deterministic status`);
    modelRuns.push({model, samples, status, ports});
  }
  assert.equal(modelRuns[0].samples.count, modelRuns[1].samples.count);
  assert.notDeepEqual(modelRuns[0].samples.left, modelRuns[1].samples.left,
    'MAME Discrete and Integrated produce different native left PCM');
  assert.notDeepEqual(modelRuns[0].samples.right, modelRuns[1].samples.right,
    'MAME Discrete and Integrated produce different native right PCM');
  assert.notDeepEqual(modelRuns[0].ports, modelRuns[1].ports,
    'MAME Discrete and Integrated status-port behavior differs on native reads');

  const dacResults = [];
  for (const dacByte of [0, 128, 255]) {
    const discreteDac = await modelCore(0, fmToneCartridge(dacByte));
    const integratedDac = await modelCore(1, fmToneCartridge(dacByte));
    const discreteSamples = pcm(discreteDac), integratedSamples = pcm(integratedDac);
    assert.equal(discreteSamples.count, integratedSamples.count);
    assert.notDeepEqual(discreteSamples.left, integratedSamples.left,
      `DAC byte ${dacByte}: native output distinguishes Discrete and Integrated models`);
    dacResults.push({dacByte, discreteLeft: digest(discreteSamples.left),
      integratedLeft: digest(integratedSamples.left)});
  }

  const faultResults = [];
  for (const model of [0, 1]) {
    const cpuControl = await modelCore(model, fmToneCartridge());
    const cpuBaseline = pcm(cpuControl);
    const cpuFm = await modelCore(model, fmToneCartridge());
    assert.equal(cpuFm._set_fm_data_bridge(1, 0, 5), 0);
    const cpuFaultPcm = sample(cpuFm);
    const cpuFmState = cpuFm._get_fm_data_bridge_state();
    assert.ok(BigInt(cpuFmState.inputWrites) > 0n,
      `model ${model}: CPU FM writes reach selected FM input fault`);
    assert.ok(BigInt(cpuFmState.changedWrites) > 0n,
      `model ${model}: CPU FM fault changes delivered register bytes`);
    assert.notDeepEqual(cpuFaultPcm.left, cpuBaseline.left,
      `model ${model}: CPU FM fault changes native PCM`);

    const z80Control = await modelCore(model, z80FmAndPsgCartridge());
    const z80Baseline = pcm(z80Control);
    const fm = await modelCore(model, z80FmAndPsgCartridge());
    assert.equal(fm._set_fm_data_bridge(1, 0, 5), 0);
    const z80FmPcm = pcm(fm);
    const fmState = fm._get_fm_data_bridge_state();
    assert.ok(BigInt(fmState.inputWrites) > 0n, `model ${model}: CPU/Z80 FM traffic reaches FM fault`);
    assert.ok(BigInt(fmState.changedWrites) > 0n, `model ${model}: FM fault changes selected-chip data`);
    assert.notDeepEqual(z80FmPcm.left, z80Baseline.left,
      `model ${model}: banked Z80 FM fault changes native PCM`);
    assert.equal(fm._get_psg_data_bridge_state().inputWrites, '0',
      `model ${model}: FM fault does not reroute traffic to PSG`);
    const psg = await modelCore(model, z80FmAndPsgCartridge());
    assert.equal(psg._set_psg_data_bridge(1, 0, 7), 0);
    const psgFaultPcm = pcm(psg);
    assert.equal(psg._get_fm_data_bridge_state().inputWrites, '0',
      `model ${model}: PSG fault does not reroute traffic to FM`);
    assert.ok(BigInt(psg._get_psg_data_bridge_state().inputWrites) > 0n,
      `model ${model}: Z80 PSG traffic reaches PSG fault`);
    assert.notDeepEqual(psgFaultPcm.left, z80Baseline.left,
      `model ${model}: isolated PSG fault changes native PCM`);
    faultResults.push({model, cpuFmWrites: cpuFmState.inputWrites,
      cpuFmChanged: cpuFmState.changedWrites, z80FmWrites: fmState.inputWrites,
      z80FmChanged: fmState.changedWrites,
      z80PsgWrites: psg._get_psg_data_bridge_state().inputWrites});
  }
  console.log(JSON.stringify({proof:'MAME FM Output Model actual-WASM',
    defaultParity:{leftPcm:digest(runtimePcm.left),rightPcm:digest(runtimePcm.right),
      pixels:digest(runtimeState.pixels),ram:digest(runtimeState.ram)},
    models:modelRuns.map(({model,samples,ports})=>({model,
      leftPcm:digest(samples.left),rightPcm:digest(samples.right),statusPorts:ports})),
    dac:dacResults,faultRouting:faultResults}, null, 2));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
