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
// Active geometry uses native pitch and cannot overwrite source or destination bounds.
for (const [width,height] of [[256,224],[320,240],[320,448],[320,480]]) {
  const src=new Uint8Array(PITCH*480), out=new Uint8ClampedArray(width*height*4);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++) {
    const i=y*PITCH+x*4;src[i]=17+x%201;src[i+1]=y%251;src[i+3]=255;
  }
  const before=src.slice();
  assert.equal(copyActiveFrame(src,out,{width,height,raw:true}).repairedRows,0);
  for(let y=0;y<height;y++)assert.deepEqual(new Uint8Array(out.buffer,y*width*4,width*4),src.slice(y*PITCH,y*PITCH+width*4));
  assert.deepEqual(src,before);
  assert.throws(()=>copyActiveFrame(src,out.subarray(4),{width,height}),/small/);
}
for(const geometry of [{width:641},{height:481},{width:0},{height:1.5},{width:'320'}])
  assert.throws(()=>copyActiveFrame(field(0),dest(),geometry),/dimensions/);
console.log('Active framebuffer geometry/bounds passed.');
