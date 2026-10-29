#!/usr/bin/env python3
"""Independently rebuild an approved source ZIP and compare both exact core files."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from website_bundle import BundleError, verify_source_archive


def rebuild(archive, expected_sha256, output):
    archive, output = Path(archive), Path(output).absolute()
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('An approved SHA-256 is required before executing source build scripts.')
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Source archive does not match the approved SHA-256.')
    info = verify_source_archive(data)
    if any(p.is_symlink() for p in (output, *output.parents)) or output.exists():
        raise ValueError('Use a new output directory with no symlink components.')
    compiler = subprocess.check_output(['emcc', '--version'], text=True)
    if not re.search(r'\b' + re.escape(info['emscripten_version']) + r'\b', compiler):
        raise ValueError('Activate the exact Emscripten version recorded in the archive.')
    output.mkdir(parents=True)
    # Names, duplicates, symlinks and all member hashes were checked before extraction.
    with zipfile.ZipFile(io.BytesIO(data)) as sources:
        sources.extractall(output)
    native = output / 'emulator/wasm-genplus'
    subprocess.run(['emcmake', 'cmake', '-S', str(native), '-B', str(native / 'build'),
                    '-DCMAKE_POLICY_VERSION_MINIMUM=3.5'], check=True)
    subprocess.run(['emmake', 'make', '-C', str(native / 'build'), '-j2'], check=True)
    for name, expected in info['core_sha256'].items():
        actual = hashlib.sha256((native / 'src/main/js' / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Rebuilt {name} differs from the distributed core: {actual} != {expected}')
    result = {'source_commit': info['source_commit'], 'version': info['version'],
              'source_archive_sha256': expected_sha256, 'core_sha256': info['core_sha256'],
              'emscripten_version': info['emscripten_version'], 'exact_match': True}
    (output / 'REBUILD-VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified exact source-to-JavaScript/WebAssembly rebuild:', json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        rebuild(args.archive, args.expected_sha256, args.output)
    except (BundleError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Corresponding-source rebuild failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
