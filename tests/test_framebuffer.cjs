'use strict';
const assert = require('node:assert/strict');
const {copyActiveFrame, WIDTH, HEIGHT, PITCH} = require('../site/framebuffer.js');
const stride = WIDTH * 4;
const dest = () => new Uint8ClampedArray(stride * HEIGHT);
function field(parity, chosenPixels = WIDTH) {
  const input = new Uint8Array(PITCH * 480);
  for(let y=parity;y<HEIGHT;y+=2) {
    for(let x=0;x<chosenPixels;x++) {
      const i=y*PITCH+x*4;
      input[i]=100 + (y%31);input[i+1]=166;input[i+2]=31;input[i+3]=255;
    }
  }
  return input;
}
{
  const src=field(0), out=dest();
  const result=copyActiveFrame(src,out);
  assert.equal(result.missingParity,1);
  assert.equal(result.repairedRows,112);
  for(let y=0;y<HEIGHT;y+=2) {
    assert.deepEqual(out.slice((y+1)*stride,(y+2)*stride),out.slice(y*stride,(y+1)*stride));
  }
}
{
  const src=field(0), out=dest();
  const result=copyActiveFrame(src,out,{raw:true});
  assert.equal(result.repairedRows,0);
  assert.deepEqual([...out.slice(stride,stride+16)],Array(16).fill(0));
}
{
  const src=field(1),out=dest();
  const result=copyActiveFrame(src,out);
  assert.equal(result.missingParity,0);
  assert.equal(result.repairedRows,112); // row 0 has no prior image, use row 1.
  assert.equal(out[0],src[PITCH]);
}
{
  const src=new Uint8Array(PITCH*480);const out=dest();
  const result=copyActiveFrame(src,out);
  assert.equal(result.repairedRows,0); // true black screen stays black
}
{
  const src=new Uint8Array(PITCH*480),out=dest();
  for(let y=0;y<HEIGHT;y++) {
    const i=y*PITCH;src[i]=20;src[i+1]=40;
  }
  const result=copyActiveFrame(src,out);
  assert.equal(result.repairedRows,0); // ordinary progressive video left intact
}
{
  const src=field(0), out=dest();
  for(let y=1;y<HEIGHT;y+=2) src[y*PITCH + 9*4]=64; // content between stride samples
  const result=copyActiveFrame(src,out);
  assert.equal(result.repairedRows,0); // no overwrite of genuine nonzero pixels
  assert.equal(out[stride+9*4],64);
}
{
  // Alternating rows with a mid-screen field polarity change. A simple
  // global even/odd heuristic misses this, but isolated gaps still recover.
  const src = new Uint8Array(PITCH*480), out = dest();
  for (let y=0;y<HEIGHT;y++) {
    const parity = y < 112 ? 0 : 1;
    if ((y&1) !== parity) continue;
    for(let x=0;x<WIDTH;x++){
      const i=y*PITCH+x*4;
      src[i]=40;src[i+1]=180;src[i+2]=45;src[i+3]=255;
    }
  }
  const result=copyActiveFrame(src,out);
  assert.ok(result.repairedRows>=100);
}
console.log('Framebuffer recovery: seven tests passed.');