'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const api=require('../site/cartridges.js');
const cart={id:'demo',approved:true,version:'test',displayName:'Test',path:'demo/test.bin',size:512,sha256:'0'.repeat(64)};
const manifest={schemaVersion:1,defaultCartridge:'demo',cartridges:[cart]};
assert.equal(api.validateManifest(manifest),manifest);
api.validateManifest(require('../site/cartridges.json'));
for (const change of [{approved:false},{id:'../bad'},{id:'2027-demo'},{id:'-demo'},{path:'demo/sub/cart.bin'},{path:'https://bad.test/rom.bin'},{path:'demo/../rom.bin'},
  {path:'demo/x.bin?x=1'},{size:511},{size:4194305},{size:NaN},{sha256:'x'.repeat(64)},{displayName:''}])
  assert.throws(()=>api.validateManifest({...manifest,cartridges:[{...cart,...change}]}));
for (const bad of [{...manifest,schemaVersion:2},{...manifest,defaultCartridge:'unknown'},
  {...manifest,cartridges:[cart,cart]},{...manifest,cartridges:[cart,{...cart,id:'other'}]}])
  assert.throws(()=>api.validateManifest(bad));
(async()=>{
  for (const size of [0,1,3,55,56,63,64,65,119,120,512,65536,150564,1000000]) {
    const bytes=Uint8Array.from({length:size},(_,i)=>(i*17+31)&255);
    const digest=crypto.createHash('sha256').update(bytes).digest('hex');
    assert.equal(api.sha256(bytes),digest,`SHA-256 padding and multi-block size ${size}`);
    if (size>=512) {
      const approved={...cart,size,sha256:digest};
      await api.verify(bytes,approved,null);
      await api.verify(bytes,approved,crypto.webcrypto.subtle);
      await assert.rejects(()=>api.verify(bytes,{...approved,size:size+1},null),/size/);
      await assert.rejects(()=>api.verify(bytes,{...approved,sha256:'0'.repeat(64)},null),/SHA-256/);
    }
  }
  console.log('PASS cartridge manifest validation, SHA-256 oracle and approval checks');
})().catch(error=>{console.error(error);process.exitCode=1;});
