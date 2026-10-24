'use strict';
const assert = require('node:assert/strict');
const {
  parseArgs, profileDefinition, selectProfileModel
} = require('../scripts/benchmark-vram-renderer.cjs');

const common = ['--baseline', 'baseline.js', '--normal', 'normal.js', '--out', 'record.json'];
const diagnosticArgs = parseArgs([...common, '--diagnostic', 'diagnostic.js']);
assert.equal(diagnosticArgs.runtime, undefined);
assert.equal(profileDefinition(false).protocolName,
  'visible-mode5-recurring-32-word-dma-paired-v1');
assert.deepEqual(profileDefinition(false).variants.map(([name]) => name),
  ['baseline', 'normal', 'diagnostic-off', 'identity', 'active-ad3']);

const runtimeArgs = parseArgs([...common, '--runtime', '--runtime-core', 'runtime.js']);
assert.equal(runtimeArgs.runtime, true);
assert.equal(profileDefinition(true).protocolName,
  'visible-mode5-recurring-32-word-dma-runtime-v1');
assert.deepEqual(profileDefinition(true).variants.map(([name]) => name),
  ['baseline', 'normal', 'runtime-default', 'runtime-identity', 'runtime-active-ad3']);
assert.deepEqual(profileDefinition(true).noFaultVariants,
  ['normal', 'runtime-default', 'runtime-identity']);
assert.throws(() => parseArgs([...common, '--runtime']), /--runtime-core/);
assert.throws(() => parseArgs([...common, '--diagnostic', 'd.js', '--runtime', '--runtime-core', 'r.js']),
  /cannot be combined/);
assert.throws(() => parseArgs([...common, '--runtime-core', 'r.js']), /requires --runtime/);

function fakeRuntime(supportedModelsMask = 7) {
  const core = {
    model: {
      modelId: 1, modelVersion: 'frame-projection-v1', effective: false,
      reason: 'no-fault', supportedModelsMask, mask: 0, bridgeA: -1, bridgeB: -1,
      lastFrameCounts: {
        logicalByteReads: 0, logicalByteWrites: 0, redirectedByteReads: 0,
        redirectedByteWrites: 0, changedPhysicalByteWrites: 0
      }
    },
    setterCalls: [],
    _get_vram_supported_model_mask() { return supportedModelsMask; },
    _get_vram_fault_model_state() { return this.model; },
    _set_vram_fault_model(modelId, mask, bridgeA, bridgeB) {
      this.setterCalls.push([modelId, mask, bridgeA, bridgeB]);
      if (modelId === 2) {
        this.model = {...this.model, modelId, modelVersion: 'logical-byte-transaction-v1',
          effective: mask !== 0, reason: mask === 0 ? 'no-fault' : 'none',
          mask, bridgeA, bridgeB};
      }
      return 0;
    }
  };
  return core;
}

const runtime = profileDefinition(true);
const core = fakeRuntime();
const defaultState = selectProfileModel(core, runtime, null, 'runtime-default');
assert.equal(defaultState.modelId, 1);
assert.deepEqual(core.setterCalls, [], 'default profile is measured without mutating its model');
selectProfileModel(core, runtime, 0, 'runtime-identity');
selectProfileModel(core, runtime, 8, 'runtime-active-ad3');
assert.deepEqual(core.setterCalls,
  [[2, 0, -1, -1], [2, 8, -1, -1]], 'runtime variants use the public safe setter');

const unsupported = fakeRuntime(3);
assert.throws(() => selectProfileModel(unsupported, runtime, 8, 'runtime-active-ad3'),
  /unsupported in the active VDP mode/);
assert.deepEqual(unsupported.setterCalls, [], 'unsupported mode is rejected before mutation');

let diagnosticCalls = 0;
const diagnosticCore = {_set_vram_transaction_diagnostic() { diagnosticCalls++; return 0; }};
assert.equal(selectProfileModel(diagnosticCore, profileDefinition(false), 8, 'active-ad3'), null);
assert.equal(diagnosticCalls, 1, 'existing diagnostic mode remains available unchanged');

console.log('Runtime renderer benchmark profile mapping passed.');
