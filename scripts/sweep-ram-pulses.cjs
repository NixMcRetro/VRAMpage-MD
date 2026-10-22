/* Deterministic frame-pulse experiments. No cartridge/RAM bytes in JSON output. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const PIN = '6090aff9e9b2f578cd28882bd4571d2e35b1d674';
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function differenceCount(a, b) {
  if (a.length !== b.length) throw Error('Cannot compare different memory sizes');
  let changed = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) changed++;
  return changed;
}

function validateSettings(settings) {
  for (const name of ['activationFrame','pulseFrames','observeFrames','sampleEvery'])
    if (!Number.isSafeInteger(settings[name]) || settings[name] < 1)
      throw Error(`${name} must be a positive safe integer`);
  if (settings.affectedWrites !== undefined &&
      (!Number.isSafeInteger(settings.affectedWrites) || settings.affectedWrites<1 || settings.affectedWrites>1024 || settings.pulseFrames!==1))
    throw Error('Affected-write limits must be 1..1024 with a one-frame maximum');
  if (!Number.isSafeInteger(settings.activationFrame + settings.pulseFrames + settings.observeFrames))
    throw Error('Frame range is too large');
}

async function runTrial(factory, rom, pair, settings) {
  validateSettings(settings);
  if (pair && (pair.length !== 2 || !pair.every(n => Number.isInteger(n) && n >= 0 && n < 15) || pair[0] === pair[1]))
    throw Error('Address pair must contain two different WA indices from 0 through 14');
  const core = await factory();
  for (const name of ['_init','_start','_tick','_sound','_wasm_input_update',
    '_get_rom_buffer_ref','_get_input_buffer_ref','_get_frame_buffer_ref',
    '_get_web_audio_l_ref','_get_web_audio_r_ref','_get_logic_ram_ref',
    '_set_logic_fault','_recover_logic_cpu','_get_logic_cpu_flags',
    '_get_logic_frame','_get_logic_reads','_get_logic_writes'])
    if (typeof core[name] !== 'function') throw Error(`Core missing ${name}; rebuild it`);
  if (settings.affectedWrites !== undefined)
    for (const name of ['_arm_logic_write_pulse','_get_logic_pulse_state'])
      if (typeof core[name] !== 'function') throw Error(`Core missing ${name}; rebuild it`);
  core._init();
  const romPointer = core._get_rom_buffer_ref(rom.length);
  if (!romPointer) throw Error('Core refused cartridge buffer');
  core.HEAPU8.set(rom, romPointer);
  core._start();
  const endFrame = settings.activationFrame + settings.pulseFrames;
  const finalFrame = endFrame + settings.observeFrames;
  const checkpoints = new Set([settings.activationFrame, endFrame, finalFrame]);
  for (let f = endFrame + settings.sampleEvery; f < finalFrame; f += settings.sampleEvery)
    checkpoints.add(f);
  const ram = () => {
    const pointer = core._get_logic_ram_ref();
    if (!Number.isSafeInteger(pointer) || pointer < 0 || pointer + 65536 > core.HEAPU8.length) throw Error('Invalid work-RAM range');
    return Buffer.from(core.HEAPU8.subarray(pointer, pointer + 65536));
  };
  const samples = [];
  let contactEndRAM, recovery = null;
  for (let frame = 1; frame <= finalFrame; frame++) {
    if (pair && frame === settings.activationFrame + 1) {
      const status = settings.affectedWrites===undefined
        ? core._set_logic_fault(1, 2, pair[0], pair[1])
        : core._arm_logic_write_pulse(1,pair[0],pair[1],settings.affectedWrites);
      if (status !== 0) throw Error(`Fault rejected: ${status}`);
    }
    new Float32Array(core.HEAPU8.buffer, core._get_input_buffer_ref(), 32).fill(0);
    core._wasm_input_update();
    core._tick();
    const audioSamples = core._sound();
    if (core._get_logic_frame() !== frame) throw Error('Core frame counter diverged');
    if (!checkpoints.has(frame)) continue;
    const bytes = ram();
    const picture = crypto.createHash('sha256');
    const picturePointer = core._get_frame_buffer_ref();
    if (!Number.isSafeInteger(picturePointer) || picturePointer < 0 ||
        picturePointer + (223 * 640 + 320) * 4 > core.HEAPU8.length)
      throw Error('Invalid framebuffer range');
    if (!Number.isSafeInteger(audioSamples) || audioSamples < 0) throw Error('Invalid audio sample count');
    // Visible 320x224 NTSC picture only, in the native 640-pixel framebuffer stride.
    for (let y = 0; y < 224; y++) {
      const row = picturePointer + y * 640 * 4;
      picture.update(core.HEAPU8.subarray(row, row + 320 * 4));
    }
    const audioHash = pointer => {
      if (!Number.isSafeInteger(pointer) || pointer < 0 || pointer + audioSamples * 4 > core.HEAPU8.length)
        throw Error('Invalid audio buffer range');
      return digest(core.HEAPU8.subarray(pointer, pointer + audioSamples * 4));
    };
    samples.push({frame, ramSHA256:digest(bytes), pictureSHA256:picture.digest('hex'),
      audioLeftSHA256:audioHash(core._get_web_audio_l_ref()),
      audioRightSHA256:audioHash(core._get_web_audio_r_ref()), audioSamples,
      cpuFlags:core._get_logic_cpu_flags(), reads:core._get_logic_reads(), writes:core._get_logic_writes()});
    if (frame === endFrame) {
      contactEndRAM = bytes;
      if (pair) {
        const flagsBefore = core._get_logic_cpu_flags();
        const pulseState=settings.affectedWrites===undefined ? null : core._get_logic_pulse_state();
        const status = core._recover_logic_cpu(1);
        if (status !== 0) throw Error(`Recovery rejected: ${status}`);
        recovery = {...(pulseState===null ? {} : {writePulseState:pulseState,
          releaseReason:pulseState===2 ? 'affected-write-limit' : 'frame-limit'}),frame, action:'force-resume', status, flagsBefore,
          flagsAfter:core._get_logic_cpu_flags(), ramBytesChanged:differenceCount(bytes, ram())};
      }
    }
  }
  return {record:{pair, samples, recovery}, contactEndRAM};
}

function compareTrial(trial, baseline) {
  const record = trial.record;
  const last = record.samples.at(-1), baselineLast = baseline.record.samples.at(-1);
  const after = record.samples.filter(sample => !record.recovery || sample.frame > record.recovery.frame);
  let pictureChanges = 0;
  for (let i = 1; i < after.length; i++)
    if (after[i].pictureSHA256 !== after[i-1].pictureSHA256) pictureChanges++;
  const ramMetric=record.recovery?.writePulseState===undefined
    ? 'contactEndRAMBytesDifferentFromBaseline' : 'frameEndRAMBytesDifferentFromBaseline';
  return {[ramMetric]:differenceCount(trial.contactEndRAM, baseline.contactEndRAM),
    finalRAMMatchesBaseline:last.ramSHA256 === baselineLast.ramSHA256,
    finalPictureMatchesBaseline:last.pictureSHA256 === baselineLast.pictureSHA256,
    pictureChangesBetweenPostContactSamples:pictureChanges,
    haltObservedAfterRecovery:after.some(sample => (sample.cpuFlags & 2) !== 0),
    stopObservedAfterRecovery:after.some(sample => (sample.cpuFlags & 1) !== 0)};
}

async function sweep(factory, rom, settings, pairs, progress = () => {}) {
  validateSettings(settings);
  const baseline = await runTrial(factory, rom, null, settings);
  const baselineRepeat = await runTrial(factory, rom, null, settings);
  const results = [];
  const repeatRecord = (first, repeat) => {
    const identical = JSON.stringify(first) === JSON.stringify(repeat);
    return {repeatIdentical:identical, ...(identical ? {} : {repeat})};
  };
  const attempt = async pair => {
    try { return await runTrial(factory, rom, pair, settings); }
    catch (error) { return {record:{pair, error:{message:error.message}}}; }
  };
  for (const pair of pairs) {
    progress(`Testing A${pair[0]+1}/A${pair[1]+1} write pulse twice`);
    const trial = await attempt(pair);
    const repeat = await attempt(pair);
    results.push({...trial.record, ...repeatRecord(trial.record, repeat.record), comparison:trial.record.error ? null : compareTrial(trial, baseline)});
  }
  return {protocolVersion:settings.affectedWrites===undefined?1:2, modelVersion:'0.2.4-experimental', corePin:PIN,
    romSHA256:digest(rom), externalInput:'all zero', settings,
    baseline:{...baseline.record, ...repeatRecord(baseline.record, baselineRepeat.record)}, results};
}

async function main(argv) {
  const [romFile, ...options] = argv;
  if (!romFile) throw Error('Usage: node scripts/sweep-ram-pulses.cjs /private/cartridge.md [--core core.js] [--activation N] [--pulse N] [--observe N] [--writes N]');
  const settings = {activationFrame:1800, pulseFrames:1, observeFrames:600, sampleEvery:60};
  let coreFile = path.resolve('site/core/genplus.js');
  const keys = {'--activation':'activationFrame','--pulse':'pulseFrames','--observe':'observeFrames','--writes':'affectedWrites'};
  for (let i = 0; i < options.length; i += 2) {
    const name = options[i], value = options[i+1];
    if (!value) throw Error(`Missing value for ${name}`);
    if (name === '--core') coreFile = path.resolve(value);
    else if (keys[name]) settings[keys[name]] = Number(value);
    else throw Error(`Unknown option ${name}`);
  }
  validateSettings(settings);
  const moduleFactory = require(coreFile);
  const factory = () => moduleFactory({locateFile:name => path.join(path.dirname(coreFile), name)});
  const pairs = Array.from({length:14}, (_, i) => [i,i+1]);
  const result = await sweep(factory, fs.readFileSync(romFile), settings, pairs, message => process.stderr.write(message+'\n'));
  result.runtime={node:process.versions.node, platform:process.platform, arch:process.arch};
  result.coreFiles={javascriptSHA256:digest(fs.readFileSync(coreFile)),
    wasmSHA256:digest(fs.readFileSync(path.join(path.dirname(coreFile),'genplus.wasm')))};
  process.stdout.write(JSON.stringify(result, null, 2)+'\n');
}
if (require.main === module) main(process.argv.slice(2)).catch(error => {process.stderr.write(error.message+'\n');process.exitCode=1;});
module.exports = {differenceCount, runTrial, compareTrial, sweep};
