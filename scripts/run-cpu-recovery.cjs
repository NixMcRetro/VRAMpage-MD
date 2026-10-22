'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
if(!process.argv[2]) throw Error('Usage: node scripts/run-cpu-recovery.cjs /private/cartridge.md [core.js]');
const coreFile=path.resolve(process.argv[3]||'site/core/genplus.js');
const factory=require(coreFile);
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(mode){
 const c=await factory({locateFile:n=>path.join(path.dirname(coreFile),n)});c._init();
 const rom=fs.readFileSync(process.argv[2]);c.HEAPU8.set(rom,c._get_rom_buffer_ref(rom.length));c._start();
 for(let f=0;f<2000;f++){if(f===1800)c._set_logic_fault(1,1,0,1);new Float32Array(c.HEAPU8.buffer,c._get_input_buffer_ref(),32).fill(0);c._wasm_input_update();c._tick();c._sound();}
 const ram=()=>hash(Buffer.from(c.HEAPU8.subarray(c._get_logic_ram_ref(),c._get_logic_ram_ref()+65536)));
 const before={frame:c._get_logic_frame(),flags:c._get_logic_cpu_flags(),reads:c._get_logic_reads(),ramHash:ram()};
 const status=c._recover_logic_cpu(mode);
 const immediate={frame:c._get_logic_frame(),flags:c._get_logic_cpu_flags(),reads:c._get_logic_reads(),ramHash:ram()};
 for(let i=0;i<120;i++){c._tick();c._sound();}
 return {mode,status,before,immediate,after120:{flags:c._get_logic_cpu_flags(),reads:c._get_logic_reads(),ramHash:ram()}};
}
(async()=>console.log(JSON.stringify([await run(1),await run(2)],null,2)))().catch(e=>{console.error(e.message);process.exitCode=1});
