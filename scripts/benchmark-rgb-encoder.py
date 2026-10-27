#!/usr/bin/env python3
"""Fixed five-pair canvas-copy benchmark; not a physical encoder benchmark."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--executable')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(**({'executable_path': args.executable} if args.executable else {}))
    page = browser.new_page()
    for filename in ['framebuffer.js', 'rgb-encoder.js']:
        page.add_script_tag(path=ROOT/'site'/filename)
    result = page.evaluate('''() => {
        const source=new Uint8Array(640*480*4), destination=new Uint8ClampedArray(320*224*4);
        for(let i=0;i<source.length;i++)source[i]=(i*73+19)&255;
        const off=VRAMpageRgbEncoder.create({cutMask:0,pair:null});
        const active=VRAMpageRgbEncoder.create({cutMask:1,pair:[0,1]});
        const copy=()=>VRAMpageFrame.copyActiveFrame(source,destination);
        const copyOff=()=>{copy();off.apply(destination);};
        const transform=()=>active.apply(destination);
        const measure=fn=>{
            const samples=[];
            for(let batch=0;batch<200;batch++) {
                const start=performance.now();
                for(let i=0;i<100;i++)fn();
                samples.push((performance.now()-start)/100);
            }return samples;
        };
        const percentile=(samples,q)=>[...samples].sort((a,b)=>a-b)[Math.ceil(samples.length*q)-1];
        for(let i=0;i<2000;i++){copy();copyOff();transform();}
        const pairs=[];
        for(let i=0;i<5;i++) {
            let baseline,candidate;
            if(i%2){candidate=measure(copyOff);baseline=measure(copy);}
            else {baseline=measure(copy);candidate=measure(copyOff);}
            pairs.push({order:i%2?'candidate-first':'baseline-first',baseline,candidate,
                medianRatio:percentile(candidate,.5)/percentile(baseline,.5),
                p95Ratio:percentile(candidate,.95)/percentile(baseline,.95)});
        }
        const activeSamples=measure(transform);
        return {pairs,activeSamples,summary:{
            inactiveMedianRatio:percentile(pairs.map(p=>p.medianRatio),.5),
            inactiveP95Ratio:percentile(pairs.map(p=>p.p95Ratio),.5),
            activeP95Ms:percentile(activeSamples,.95)}};
    }''')
    result.update(browser=browser.version, platform=platform.platform(),
                  sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  sourceHashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                for name in ['site/framebuffer.js','site/rgb-encoder.js','scripts/benchmark-rgb-encoder.py']},
                  protocol='rgb-encoder-display-v1',
                  limits={'inactiveMedianRatio':1.05,'inactiveP95Ratio':1.05,'activeP95Ms':1.0})
    result['passed']=all(result['summary'][key]<=limit for key,limit in result['limits'].items())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['summary','limits','passed']},indent=2))
    browser.close()
raise SystemExit(0 if result['passed'] else 1)
