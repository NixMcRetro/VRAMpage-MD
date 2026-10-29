'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const path = require('node:path');
const {fmToneCartridge, z80FmAndPsgCartridge, createCore, nextAudio, fmStatusProbe, fmStatusPorts} =
  require('./test_fm_data_runtime.cjs');

const [runtimeArg, normalArg] = process.argv.slice(2);
assert.ok(runtimeArg && normalArg,
  'Pass the production runtime and unmodified production core paths');
const runtimePath = path.resolve(runtimeArg);
const normalPath = path.resolve(normalArg);

async function modelCore(model, rom) {
  return createCore(runtimePath, rom, core => {
    assert.equal(core._set_fm_output_model_request(model), 0);
    assert.equal(core._get_fm_output_model_state().requestedModel,
      model === 0 ? 'discrete' : 'integrated');
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
  const defaultModel = runtime._get_fm_output_model_state();
  assert.deepEqual(defaultModel, {schemaVersion:1,available:true,supported:true,loaded:true,
    requestedModel:'discrete',effectiveModel:'discrete',backend:'mame-opn2',reason:'none'});
  assertPcmEqual(runtimePcm, normalPcm, 'default runtime matches the unmodified production core');
  assert.deepEqual(runtimeState, normalState,
    'default runtime preserves unmodified production pixels and native memory progress');
  assert.deepEqual(fmStatusProbe(runtime), fmStatusProbe(normal),
    'default runtime preserves production FM status reads');
  assert.deepEqual(fmStatusPorts(runtime), fmStatusPorts(normal),
    'default runtime preserves production status-port reads');

  const invalid = await createCore(runtimePath, rom, core => {
    const before = core._get_fm_output_model_state();
    assert.equal(typeof core._set_fm_output_model_request_c, 'undefined',
      'raw native request setter is hidden behind strict facade validation');
    assert.equal(before.loaded, false, 'native model is not effective before cartridge start');
    assert.equal(before.requestedModel, 'discrete', 'pending selection defaults to Discrete');
    assert.equal(before.effectiveModel, null);
    for (const value of [-1, 2, 3, 1.5, NaN, Infinity, -Infinity, true, false, '1', null,
      undefined, [], {}, [1]])
      assert.equal(core._set_fm_output_model_request(value), 1);
    assert.equal(core._set_fm_output_model_request(), 1, 'missing argument is rejected');
    assert.equal(core._set_fm_output_model_request(1, 0), 1, 'extra arguments are rejected');
    assert.deepEqual(core._get_fm_output_model_state(), before,
      'invalid requests leave pending and effective state unchanged');
  });
  assert.equal(invalid._get_fm_output_model_state().effectiveModel, 'discrete');

  const modelRuns = [];
  for (const model of [0, 1]) {
    const first = await modelCore(model, rom);
    assert.equal(first._get_fm_output_model_state().effectiveModel,
      model === 0 ? 'discrete' : 'integrated');
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
  for (const model of [0, 1]) {
    const noDac = await modelCore(model, fmToneCartridge());
    const noDacSamples = pcm(noDac);
    const byByte = [];
    for (const dacByte of [0, 128, 255]) {
      const c = await modelCore(model, fmToneCartridge(dacByte));
      const samples = pcm(c);
      assert.equal(samples.count, noDacSamples.count);
      assert.notDeepEqual(samples.left, noDacSamples.left,
        `model ${model} DAC byte ${dacByte}: enabling/writing DAC changes native PCM`);
      byByte.push({dacByte, left: digest(samples.left)});
    }
    assert.equal(new Set(byByte.map(item => item.left)).size, 3,
      `model ${model}: each DAC data byte produces distinct native PCM`);
    dacResults.push({model, noDacLeft: digest(noDacSamples.left), byByte});
  }
  for (const dacByte of [0, 128, 255]) {
    const discreteDac = await modelCore(0, fmToneCartridge(dacByte));
    const integratedDac = await modelCore(1, fmToneCartridge(dacByte));
    assert.notDeepEqual(pcm(discreteDac).left, pcm(integratedDac).left,
      `DAC byte ${dacByte}: native output distinguishes Discrete and Integrated models`);
  }

  const faultResults = [];
  for (const model of [0, 1]) {
    const cpuControl = await modelCore(model, fmToneCartridge());
    const cpuBaseline = pcm(cpuControl);
    const cpuFm = await modelCore(model, fmToneCartridge());
    assert.equal(cpuFm._set_fm_data_bridge(1, 0, 5), 0);
    const cpuFaultPcm = sample(cpuFm);
    const cpuFmState = cpuFm._get_fm_data_bridge_state();
    assert.equal(cpuFmState.inputWrites, '64',
      `model ${model}: CPU FM path delivers its literal write count`);
    assert.equal(cpuFmState.changedWrites, '34',
      `model ${model}: CPU FM bridge changes its literal byte count`);
    assert.notDeepEqual(cpuFaultPcm.left, cpuBaseline.left,
      `model ${model}: CPU FM fault changes native PCM`);
    const cpuCut = await modelCore(model, fmToneCartridge());
    assert.equal(cpuCut._set_fm_data_mask(0x80), 0);
    const cpuCutPcm = sample(cpuCut), cpuCutState = cpuCut._get_fm_data_bridge_state();
    assert.equal(cpuCutState.inputWrites, '64', `model ${model}: CPU FM cut receives literal writes`);
    assert.equal(cpuCutState.changedWrites, '11', `model ${model}: CPU FM cut changes literal bytes`);
    assert.notDeepEqual(cpuCutPcm.left, cpuBaseline.left,
      `model ${model}: CPU FM data cut changes native PCM`);

    const z80Control = await modelCore(model, z80FmAndPsgCartridge());
    const z80Baseline = pcm(z80Control);
    const fm = await modelCore(model, z80FmAndPsgCartridge());
    assert.equal(fm._set_fm_data_bridge(1, 0, 5), 0);
    const z80FmPcm = pcm(fm);
    const fmState = fm._get_fm_data_bridge_state();
    assert.equal(fmState.inputWrites, '62',
      `model ${model}: banked Z80 FM path delivers its literal write count`);
    assert.equal(fmState.changedWrites, '33',
      `model ${model}: banked Z80 FM bridge changes its literal byte count`);
    assert.notDeepEqual(z80FmPcm.left, z80Baseline.left,
      `model ${model}: banked Z80 FM fault changes native PCM`);
    const z80Cut = await modelCore(model, z80FmAndPsgCartridge());
    assert.equal(z80Cut._set_fm_data_mask(0x80), 0);
    const z80CutPcm = sample(z80Cut), z80CutState = z80Cut._get_fm_data_bridge_state();
    assert.equal(z80CutState.inputWrites, '62', `model ${model}: Z80 FM cut receives literal writes`);
    assert.equal(z80CutState.changedWrites, '11', `model ${model}: Z80 FM cut changes literal bytes`);
    assert.notDeepEqual(z80CutPcm.left, z80Baseline.left,
      `model ${model}: banked Z80 FM data cut changes native PCM`);
    assert.equal(fm._get_psg_data_bridge_state().inputWrites, '0',
      `model ${model}: FM fault does not reroute traffic to PSG`);
    const psg = await modelCore(model, z80FmAndPsgCartridge());
    assert.equal(psg._set_psg_data_bridge(1, 0, 7), 0);
    const psgFaultPcm = pcm(psg);
    const psgState = psg._get_psg_data_bridge_state();
    assert.equal(psg._get_fm_data_bridge_state().inputWrites, '0',
      `model ${model}: PSG fault does not reroute traffic to FM`);
    assert.equal(psgState.inputWrites, '3', `model ${model}: Z80 PSG literal write count`);
    assert.equal(psgState.changedWrites, '2', `model ${model}: Z80 PSG literal changed-byte count`);
    assert.notDeepEqual(psgFaultPcm.left, z80Baseline.left,
      `model ${model}: isolated PSG fault changes native PCM`);
    faultResults.push({model, cpuFmWrites: cpuFmState.inputWrites,
      cpuFmChanged: cpuFmState.changedWrites, cpuCutWrites: cpuCutState.inputWrites,
      cpuCutChanged: cpuCutState.changedWrites, z80FmWrites: fmState.inputWrites,
      z80FmChanged: fmState.changedWrites,
      z80CutWrites: z80CutState.inputWrites, z80CutChanged: z80CutState.changedWrites,
      z80PsgWrites: psgState.inputWrites, z80PsgChanged: psgState.changedWrites});
  }
  console.log(JSON.stringify({proof:'Production MAME FM Output Model actual-WASM',
    defaultParity:{runtime:{leftPcm:digest(runtimePcm.left),rightPcm:digest(runtimePcm.right),
        pixels:digest(runtimeState.pixels),ram:digest(runtimeState.ram)},
      normal:{leftPcm:digest(normalPcm.left),rightPcm:digest(normalPcm.right),
        pixels:digest(normalState.pixels),ram:digest(normalState.ram)}},
    models:modelRuns.map(({model,samples,ports})=>({model,
      leftPcm:digest(samples.left),rightPcm:digest(samples.right),statusPorts:ports})),
    dac:dacResults,faultRouting:faultResults}, null, 2));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
