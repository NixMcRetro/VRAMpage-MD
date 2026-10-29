#!/usr/bin/env bash
# Stage a tested VRAMpage MD build in a LOCAL McRetro.net release branch.
# Intentionally does not commit, push or merge.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/path/to/mcretro.net-clone" >&2
  exit 2
fi
TARGET="$(cd "$1" && pwd)"
if [[ ! -d "$TARGET/.git" || ! -f "$TARGET/_config.yml" ]]; then
  echo "Expected a separate, normal McRetro.net Git checkout: $TARGET" >&2
  exit 1
fi
branch="$(git -C "$TARGET" branch --show-current)"
if [[ -z "$branch" || "$branch" == "main" || "$branch" == "master" ]]; then
  echo "Refusing to stage on the website main/master branch. Switch to a release branch first." >&2
  exit 1
fi
for file in   "$ROOT/site/index.html" "$ROOT/site/app.js" "$ROOT/site/style.css" "$ROOT/site/framebuffer.js" "$ROOT/site/rgb-encoder.js" "$ROOT/site/circuit-config.js" "$ROOT/site/experiment-comparison.js"   "$ROOT/site/core/genplus.js" "$ROOT/site/core/genplus.wasm"   "$ROOT/site/source/README.txt"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing release artifact: $file" >&2
    echo "Activate Emscripten and run ./scripts/build-core.sh first." >&2
    exit 1
  fi
done
# Build and verify the new original Demo Cart for FUTURE approved website builds.
python3 "$ROOT/scripts/build-demo-cart.py"
DEMO="$ROOT/site/demo/VRAMpage-MD-Demo-Cart-v0.3.5.bin"
LEGACY_DEMO="$ROOT/site/demo/VRAMpage-MD-Demo-Cart-v0.1.bin"
for item in "$DEMO" "$LEGACY_DEMO"; do
  if [[ ! -f "$item" ]]; then
    echo "Approved Demo Cart missing: $item" >&2; exit 1
  fi
done
checksum="$(shasum -a 256 "$DEMO" | awk '{print $1}')"
legacy_checksum="$(shasum -a 256 "$LEGACY_DEMO" | awk '{print $1}')"
if [[ "$checksum" != "89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f" || "$legacy_checksum" != "93b9fc72a428657c012fb4325bc1382b69b9d3c9d0af4a4dc312732789dfe0d4" ]]; then
  echo "Approved original cartridge checksum mismatch. Refusing to stage." >&2; exit 1
fi
if find "$ROOT/site" -type f \( -iname '*.bin' -o -iname '*.gen' -o -iname '*.smd' -o -iname 'sonic.md' \) | grep -v -F -x "$DEMO" | grep -v -F -x "$LEGACY_DEMO" | grep -q .; then
  echo "Unapproved cartridge files detected inside site/. Refusing to stage." >&2
  exit 1
fi
DEST="$TARGET/homepages/vrampage-md"
mkdir -p "$DEST/core" "$DEST/source" "$DEST/demo"
cp "$ROOT/site/index.html" "$ROOT/site/app.js" "$ROOT/site/style.css" "$ROOT/site/framebuffer.js" "$ROOT/site/rgb-encoder.js" "$ROOT/site/circuit-config.js" "$ROOT/site/experiment-comparison.js" "$DEST/"
cp "$ROOT/site/core/genplus.js" "$ROOT/site/core/genplus.wasm" "$DEST/core/"
cp "$DEMO" "$DEST/demo/"
cp -R "$ROOT/site/source/." "$DEST/source/"
cp "$ROOT/README.md" "$DEST/README.md"
printf 'VRAMpage MD release staged locally at: %s\n' "$DEST"
printf 'Website branch: %s\n' "$branch"
printf 'No commit, push or deployment was made. Review these files:\n'
git -C "$TARGET" status --short -- homepages/vrampage-md
