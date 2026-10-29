const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

function fail(message) {
  console.error(message);
  process.exit(1);
}

const [wasmPath, headerPath, expectedRawHash] = process.argv.slice(2);
if (!wasmPath || !headerPath) fail('Usage: node test_musashi_notice_wasm.cjs module.wasm m68k.h [raw-sha256]');
const wasm = fs.readFileSync(wasmPath);
if (!WebAssembly.validate(wasm)) fail('Musashi-notice WebAssembly module does not validate.');
const header = fs.readFileSync(headerPath);
const noticeMatch = header.toString('latin1').match(
  /\/\* ={8,} \*\/\r?\n\/\* =+ LICENSING & COPYRIGHT =+ \*\/\r?\n\/\* ={8,} \*\/\r?\n\/\*.*?\*\//s
);
if (!noticeMatch) fail('Pinned Musashi notice block is missing.');
const notice = Buffer.from(noticeMatch[0], 'latin1');
if (!notice.includes(Buffer.from('Copyright Karl Stenerud'))
    || !notice.includes(Buffer.from('binary files'))
    || !notice.includes(Buffer.from('All other licensing terms must be negotiated'))) {
  fail('Extracted m68k.h comment is not the required Musashi notice.');
}
WebAssembly.compile(wasm).then(module => {
  const sections = WebAssembly.Module.customSections(module, 'license.Musashi');
  if (sections.length !== 1) fail(`Expected one license.Musashi section, found ${sections.length}.`);
  if (!Buffer.from(sections[0]).equals(notice)) fail('Embedded Musashi notice differs from pinned m68k.h bytes.');
  if (expectedRawHash) {
    let offset = 8;
    let stripped = null;
    while (offset < wasm.length) {
      const start = offset;
      const sectionId = wasm[offset++];
      let size = 0;
      let shift = 0;
      let byte;
      do {
        byte = wasm[offset++];
        size |= (byte & 0x7f) << shift;
        shift += 7;
      } while (byte & 0x80);
      const payloadStart = offset;
      const end = payloadStart + size;
      if (sectionId === 0) {
        let nameSize = 0;
        let nameShift = 0;
        let nameByte;
        do {
          nameByte = wasm[offset++];
          nameSize |= (nameByte & 0x7f) << nameShift;
          nameShift += 7;
        } while (nameByte & 0x80);
        const name = wasm.subarray(offset, offset + nameSize).toString('utf8');
        if (name === 'license.Musashi') {
          if (stripped) fail('Duplicate Musashi notice custom sections found.');
          stripped = Buffer.concat([wasm.subarray(0, start), wasm.subarray(end)]);
        }
      }
      offset = end;
    }
    if (!stripped) fail('Could not locate Musashi section to verify the raw module hash.');
    const rawHash = crypto.createHash('sha256').update(stripped).digest('hex');
    if (rawHash !== expectedRawHash) fail(`Stripping the notice changed core identity: ${rawHash} != ${expectedRawHash}`);
  }
  console.log(`Validated ${path.basename(wasmPath)} with exact Musashi notice (${notice.length} bytes).`);
}).catch(error => fail(`Could not compile notice-bearing Wasm module: ${error.message}`));
