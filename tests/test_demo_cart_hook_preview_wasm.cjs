/* Real Genesis Plus GX chip-rendered original 20-second instrumental.
 * The production 180-second v0.3.8 score remains unchanged.
 */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const coreFile=path.resolve(process.argv[2]||'site/core/genplus.js');
const romPath=path.join(root,'demo-cart/show-lab/build/music-lab/VRAMpage-MD-Demo-Cart-v0.3.8-Hook-Preview.bin');
const reportPath=path.join(root,'demo-cart/show-lab/build/music-lab/rom_report.json');
const output=path.join(root,'artifacts/demo-cart-music-lab');
fs.mkdirSync(output,{recursive:true});
function wav(file,chunks){
 const pcm=Buffer.concat(chunks);
 const wav=Buffer.alloc(pcm.length+44);
 wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);
 wav.write('WAVE',8);wav.write('fmt ',12);
 wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(2,22);
 wav.writeUInt32LE(44100,24);wav.writeUInt32LE(176400,28);
 wav.writeUInt16LE(4,32);wav.writeUInt16LE(16,34);
 wav.write('data',36);wav.writeUInt32LE(pcm.length,40);
 pcm.copy(wav,44);fs.writeFileSync(path.join(output,file),wav);
 return {file,sha256:crypto.createHash('sha256').update(wav).digest('hex')};
}
async function runRegion(region,fps,idle){
 const rom=fs.readFileSync(romPath);
 const report=JSON.parse(fs.readFileSync(reportPath));
 assert.equal(report.music.lengthSeconds,20);
 assert.equal(report.music.musicLabPreview,true);
 assert.deepEqual(report.music.ymLogicalSlotOffsets,[0,8,4,12]);
 assert.equal(report.music.steps,100);
 assert.equal(report.sha256,crypto.createHash('sha256').update(rom).digest('hex'));
 const core=await require(coreFile)({locateFile:n=>path.join(path.dirname(coreFile),n)});
 core._init();assert.equal(core._set_region_request(region),0);
 core.HEAPU8.set(rom,core._get_rom_buffer_ref(rom.length));core._start();
 const inbuf=new Float32Array(core.HEAPF32.buffer,core._get_input_buffer_ref(),32);
 const L=new Float32Array(core.HEAPF32.buffer,core._get_web_audio_l_ref(),2048);
 const R=new Float32Array(core.HEAPF32.buffer,core._get_web_audio_r_ref(),2048);
 const tick=()=>{inbuf.fill(0);core._wasm_input_update();core._tick();return core._sound();};
 for(let i=0;i<idle+4;i++)tick();
 const buffers=[],bins=[];
 for(let second=0;second<20;second++){
  let sum=0,count=0,peak=0; const chunks=[];
  for(let i=0;i<fps;i++){
   const n=tick();assert.ok(n>0&&n<=2048);
   const b=Buffer.alloc(n*4);
   for(let j=0;j<n;j++){
    const l=L[j],r=R[j];assert.ok(Number.isFinite(l)&&Number.isFinite(r));
    const x=(l*l+r*r)/2;sum+=x;count++;
    peak=Math.max(peak,Math.abs(l),Math.abs(r));
    b.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(l*32767))),j*4);
    b.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(r*32767))),j*4+2);
   }
   chunks.push(b);
  }
  bins.push({second,rms:Math.sqrt(sum/count),peak});
  buffers.push(...chunks);
 }
 // Fail if the audition produces silence or an accidental stalled score.
 for(const section of [[0,3],[3,8],[8,13],[13,19]]){
  assert.ok(bins.slice(...section).some(x=>x.rms>0.0001),
      'No native audio during '+JSON.stringify(section)+' in region '+region);
 }
 const name=(region===1?'NTSC':'PAL')+'-Original-Ska-Hook-20s.wav';
 const file=wav(name,buffers);
 return {region:region===1?'NTSC':'PAL',durationSeconds:20,...file,bins,
  maxPeak:Math.max(...bins.map(x=>x.peak))};
}
(async()=>{
 const result=[];
 for(const [region,fps,idle] of [[1,60,600],[2,50,500]])
  result.push(await runRegion(region,fps,idle));
 fs.writeFileSync(path.join(output,'AUDITION_REPORT.json'),
    JSON.stringify({engine:'Genesis Plus GX',format:'stereo 44.1kHz 16-bit PCM',
      source:'Real native YM2612/PSG output from original homebrew ROM',
      auditionSeconds:20,results:result},null,2)+'\n');
 console.log('Real 20-second FM/PSG audition captured in NTSC and PAL');
})().catch(e=>{console.error(e);process.exitCode=1;});
