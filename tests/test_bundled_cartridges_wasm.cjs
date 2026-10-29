'use strict';
// Execute every manifest-approved cartridge on the actual production WASM core.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {validateManifest}=require('../site/cartridges.js');
const root=path.resolve(__dirname,'..');
const coreFile=path.resolve(process.argv[2] || 'site/core/genplus.js');
const manifest=validateManifest(JSON.parse(fs.readFileSync(path.join(root,'site/cartridges.json'))));
(async()=>{
  for (const cart of manifest.cartridges) {
    const rom=fs.readFileSync(path.join(root,'site',cart.path));
    assert.equal(rom.length,cart.size);
    assert.equal(crypto.createHash('sha256').update(rom).digest('hex'),cart.sha256);
    for (const request of [1,2]) {
      const core=await require(coreFile)({locateFile:name=>path.join(path.dirname(coreFile),name)});
      core._init();
      assert.equal(core._set_region_request(request),0);
      core.HEAPU8.set(rom,core._get_rom_buffer_ref(rom.length));
      core._start();
      const ram=core._get_logic_ram_ref();
      const ramBefore=Buffer.from(core.HEAPU8.subarray(ram,ram+65536));
      for (let frame=0;frame<180;frame++) {
        core._wasm_input_update();core._tick();
        const count=core._sound();
        assert.ok(count>0 && count<=2048,'Bounded native audio frame');
        for (const ref of [core._get_web_audio_l_ref(),core._get_web_audio_r_ref()]) {
          const samples=new Float32Array(core.HEAPF32.buffer,ref,count);
          for (const sample of samples) assert.ok(Number.isFinite(sample) && Math.abs(sample)<=1,'Finite bounded PCM');
        }
      }
      const state=core._get_region_state();
      assert.equal(state.pal,request===2);
      assert.equal(state.linesPerFrame,request===2?313:262);
      assert.equal(core._get_logic_frame(),180,'Native CPU frames completed');
      assert.notDeepEqual(Buffer.from(core.HEAPU8.subarray(ram,ram+65536)),ramBefore,'Original program made Work RAM progress');
      const pixels=core._get_frame_buffer_ref(), colours=new Set();
      for(let y=0;y<224;y+=4)for(let x=0;x<320;x+=4){
        const p=pixels+4*(y*640+x);
        colours.add(core.HEAPU8[p]+','+core.HEAPU8[p+1]+','+core.HEAPU8[p+2]);
      }
      assert.ok(colours.size>4,`${cart.id} renders original nonuniform colour pixels`);
      console.log(`PASS ${cart.displayName} v${cart.version}: ${request===2?'PAL':'NTSC-U'}, 180 native frames, ${colours.size} colours`);
    }
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
