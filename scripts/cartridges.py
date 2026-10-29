#!/usr/bin/env python3
"""Build and verify the manifest's approved original cartridges (stdlib only)."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROM_SUFFIXES = {'.bin', '.gen', '.smd', '.rom', '.sms', '.gg', '.32x', '.iso', '.cue', '.chd', '.mdx'}
STATIC_FILES = ('index.html', 'style.css', 'app.js', 'cartridges.js', 'cartridges.json',
                'framebuffer.js', 'rgb-encoder.js', 'circuit-config.js', 'experiment-comparison.js',
                'core/genplus.js', 'core/genplus.wasm', 'source/README.txt')
ARCHIVE_SUFFIXES = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz'}
SECRET_NAMES = {'credentials', 'credentials.json', 'id_rsa', 'id_ed25519', 'id_ecdsa',
                'secrets.json', 'secrets.yaml', 'secrets.yml'}
SECRET_SUFFIXES = {'.pem', '.p12', '.pfx', '.key'}


class CartridgeError(ValueError):
    pass


def safe_path(relative):
    if (not isinstance(relative, str) or not relative
            or not re.fullmatch(r'[A-Za-z0-9_./-]+', relative)
            or relative != PurePosixPath(relative).as_posix()
            or PurePosixPath(relative).is_absolute()
            or any(part in {'.', '..'} for part in relative.split('/'))):
        raise CartridgeError(f'Unsafe cartridge path: {relative!r}')
    return relative


def repo_file(root, relative):
    path = Path(root) / safe_path(relative)
    component = Path(root)
    for part in PurePosixPath(relative).parts:
        component = component / part
        if component.is_symlink():
            raise CartridgeError(f'Symlinks are not allowed in cartridge inputs: {relative}')
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(Path(root).resolve())
    except (OSError, ValueError) as error:
        raise CartridgeError(f'Missing or escaping cartridge input: {relative}') from error
    if not resolved.is_file():
        raise CartridgeError(f'Cartridge input is not a regular file: {relative}')
    return path


def _identity(asset):
    safe_path(asset.get('path'))
    if (type(asset.get('size')) is not int or asset['size'] <= 0
            or not isinstance(asset.get('sha256'), str)
            or not re.fullmatch(r'[0-9a-f]{64}', asset['sha256'])):
        raise CartridgeError('Each approved asset requires an exact size and SHA-256')


def validate_manifest(manifest):
    if (not isinstance(manifest, dict) or type(manifest.get('schemaVersion')) is not int
            or manifest['schemaVersion'] != 1
            or not isinstance(manifest.get('cartridges'), list) or not manifest['cartridges']
            or not isinstance(manifest.get('preservedAssets'), list)):
        raise CartridgeError('Invalid cartridge manifest schema')
    ids, paths = set(), set()
    for entry in manifest['cartridges']:
        if not isinstance(entry, dict):
            raise CartridgeError('Invalid cartridge entry')
        _identity(entry)
        cartridge_id = entry.get('id')
        if (not isinstance(cartridge_id, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', cartridge_id)
                or cartridge_id in ids or cartridge_id == 'local' or entry.get('approved') is not True
                or any(not isinstance(entry.get(key), str) or not entry[key].strip()
                       for key in ('displayName', 'version'))):
            raise CartridgeError('Each cartridge needs a unique ID, version, name and explicit approval')
        ids.add(cartridge_id)
        if (not re.fullmatch(r'demo/[A-Za-z0-9][A-Za-z0-9._-]*\.bin', entry['path'])
                or not 512 <= entry['size'] <= 4*1024*1024):
            raise CartridgeError('Approved cartridge paths must be demo/*.bin')
        source, build = safe_path(entry.get('source')), entry.get('build')
        if (not source.startswith('demo-cart/') or not source.endswith('.py')
                or not isinstance(build, dict) or build.get('method') != 'python3'):
            raise CartridgeError('Approved cartridges require an original Python source builder')
        output = safe_path(build.get('output'))
        if not output.startswith(str(PurePosixPath(source).parent) + '/') or not output.endswith('.bin'):
            raise CartridgeError('Build output must stay within the cartridge source directory')
        notice = entry.get('license')
        if (not isinstance(notice, dict)
                or any(not isinstance(notice.get(key), str) or not notice[key].strip()
                       for key in ('type', 'attribution', 'redistribution', 'notice'))):
            raise CartridgeError('Approved cartridges require attribution and redistribution evidence')
        safe_path(notice['notice'])
        if 'originalNotice' in notice:
            safe_path(notice['originalNotice'])
        regions = entry.get('regions')
        if (not isinstance(regions, list) or not regions
                or any(region not in ('J', 'U', 'E') for region in regions)
                or len(regions) != len(set(regions))):
            raise CartridgeError('Invalid cartridge region header metadata')
        relative = 'site/' + entry['path']
        if relative in paths:
            raise CartridgeError(f'Duplicate approved asset path: {relative}')
        paths.add(relative)
    if (not isinstance(manifest.get('defaultCartridge'), str)
            or manifest['defaultCartridge'] not in ids):
        raise CartridgeError('Default cartridge must identify an approved manifest entry')
    for asset in manifest['preservedAssets']:
        if not isinstance(asset, dict):
            raise CartridgeError('Invalid preserved asset entry')
        _identity(asset)
        if asset['path'] in paths:
            raise CartridgeError(f"Duplicate approved asset path: {asset['path']}")
        paths.add(asset['path'])
    return manifest


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CartridgeError(f'Duplicate manifest field: {key}')
        result[key] = value
    return result


def load_manifest(root=ROOT):
    try:
        data = repo_file(root, 'site/cartridges.json').read_text(encoding='utf-8')
        return validate_manifest(json.loads(data, object_pairs_hook=_unique_object))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CartridgeError(f'Cannot read cartridge manifest: {error}') from error


def approved_assets(manifest):
    return {**{'site/' + entry['path']: entry for entry in manifest['cartridges']},
            **{asset['path']: asset for asset in manifest['preservedAssets']}}


def is_secret_path(relative):
    path = PurePosixPath(relative)
    name = path.name.lower()
    return (any(part.lower() in {'.git', '.aws', '.ssh', 'secrets', 'credentials'} for part in path.parts)
            or name == '.env' or name.startswith('.env.')
            or name in SECRET_NAMES or path.suffix.lower() in SECRET_SUFFIXES)


def verify_asset(relative, data, assets):
    if is_secret_path(relative):
        raise CartridgeError(f'Refusing to package a file that may contain a user secret: {relative}')
    expected = assets.get(relative)
    if expected is not None:
        if len(data) != expected['size'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise CartridgeError(f'Approved cartridge asset has an unexpected checksum or size: {relative}')
        if relative.endswith('.bin') and data[0x100:0x104] != b'SEGA':
            raise CartridgeError(f'Approved cartridge has an invalid Mega Drive header: {relative}')
        return
    suffix = PurePosixPath(relative).suffix.lower()
    if suffix in ROM_SUFFIXES or PurePosixPath(relative).name.lower() == 'sonic.md':
        raise CartridgeError(f'Refusing to package a game ROM or disc image: {relative}')
    if suffix in ARCHIVE_SUFFIXES:
        raise CartridgeError(f'Refusing to package an opaque nested archive: {relative}')
    if data[0x100:0x104] == b'SEGA':
        raise CartridgeError(f'Refusing to package a Mega Drive ROM signature: {relative}')


def source_paths(manifest):
    paths = {'scripts/cartridges.py', 'scripts/build-demo-cart.py', 'site/cartridges.json'}
    for entry in manifest['cartridges']:
        paths.update((entry['source'], entry['license']['notice']))
        if 'originalNotice' in entry['license']:
            paths.add(entry['license']['originalNotice'])
    paths.update(asset['path'] for asset in manifest['preservedAssets']
                 if not asset['path'].startswith('site/'))
    return paths


def verify_site(root=ROOT, manifest=None):
    root = Path(root)
    manifest = manifest or load_manifest(root)
    assets = approved_assets(manifest)
    for relative in assets.keys() | source_paths(manifest):
        verify_asset(relative, repo_file(root, relative).read_bytes(), assets)
    for path in (root / 'site').rglob('*'):
        if path.is_symlink():
            raise CartridgeError(f'Symlinks are not allowed in static cartridge bundles: {path}')
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            verify_asset(relative, repo_file(root, relative).read_bytes(), assets)
    return manifest


def build_cartridges(root=ROOT):
    root = Path(root)
    manifest = load_manifest(root)
    assets = approved_assets(manifest)
    for asset in manifest['preservedAssets']:
        verify_asset(asset['path'], repo_file(root, asset['path']).read_bytes(), assets)
    generated = []
    for entry in manifest['cartridges']:
        source = repo_file(root, entry['source'])
        subprocess.run([sys.executable, str(source)], cwd=root, check=True)
        data = repo_file(root, entry['build']['output']).read_bytes()
        relative = 'site/' + entry['path']
        verify_asset(relative, data, assets)
        destination = root / relative
        try:
            destination.resolve().relative_to(root.resolve())
        except ValueError as error:
            raise CartridgeError(f'Unsafe cartridge destination: {relative}') from error
        generated.append((destination, data, relative))
    # Verify every output before replacing any staged cartridge.
    for destination, data, relative in generated:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        print(f"Verified {relative}: {len(data)} bytes, SHA-256 {assets[relative]['sha256']}")
    verify_site(root, manifest)


def stage_site(destination, root=ROOT):
    root, destination = Path(root), Path(destination)
    if (any(part.is_symlink() for part in (destination, *destination.parents))
            or destination.resolve().is_relative_to((root / 'site').resolve())):
        raise CartridgeError('Static destination must be separate from site/ and not a symlink')
    manifest = verify_site(root)
    for relative in STATIC_FILES:
        if not repo_file(root, 'site/' + relative).read_bytes():
            raise CartridgeError(f'Empty static application file: {relative}')
    if not repo_file(root, 'site/core/genplus.wasm').read_bytes().startswith(b'\0asm'):
        raise CartridgeError('Static emulator does not have the WebAssembly signature')
    assets = approved_assets(manifest)
    # Validate before changing a destination, including any stale cartridge files.
    if destination.exists():
        for path in destination.rglob('*'):
            if path.is_symlink():
                raise CartridgeError(f'Symlinks are not allowed in a static destination: {path}')
            if path.is_file():
                relative = path.relative_to(destination).as_posix()
                repo_file(destination, relative)
                checked = (relative.removeprefix('source/cartridges/')
                           if relative.startswith('source/cartridges/') else 'site/' + relative)
                verify_asset(checked, path.read_bytes(), assets)
    shutil.copytree(root / 'site', destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    snapshot = destination / 'source' / 'cartridges'
    paths = source_paths(manifest) | {asset['path'] for asset in manifest['preservedAssets']}
    for relative in paths:
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_file(root, relative), target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'verify-site', 'stage-site'))
    parser.add_argument('destination', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.command == 'build':
            build_cartridges(args.root)
        elif args.command == 'stage-site':
            if args.destination is None:
                parser.error('stage-site requires a destination')
            stage_site(args.destination, args.root)
        else:
            verify_site(args.root)
    except (CartridgeError, OSError, subprocess.CalledProcessError) as error:
        print(f'Cartridge verification failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
