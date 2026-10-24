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
for file in   "$ROOT/site/index.html" "$ROOT/site/app.js" "$ROOT/site/style.css" "$ROOT/site/framebuffer.js" "$ROOT/site/circuit-config.js"   "$ROOT/site/core/genplus.js" "$ROOT/site/core/genplus.wasm"   "$ROOT/site/source/README.txt"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing release artifact: $file" >&2
    echo "Activate Emscripten and run ./scripts/build-core.sh first." >&2
    exit 1
  fi
done
if find "$ROOT/site" -type f \( -iname '*.bin' -o -iname '*.gen' -o -iname '*.smd' -o -iname 'sonic.md' \) | grep -q .; then
  echo "ROM-like files detected inside site/. Remove them before staging." >&2
  exit 1
fi
DEST="$TARGET/homepages/vrampage"
mkdir -p "$DEST/core" "$DEST/source"
cp "$ROOT/site/index.html" "$ROOT/site/app.js" "$ROOT/site/style.css" "$ROOT/site/framebuffer.js" "$ROOT/site/circuit-config.js" "$DEST/"
cp "$ROOT/site/core/genplus.js" "$ROOT/site/core/genplus.wasm" "$DEST/core/"
cp -R "$ROOT/site/source/." "$DEST/source/"
cp "$ROOT/README.md" "$DEST/README.md"
printf 'VRAMpage MD release staged locally at: %s\n' "$DEST"
printf 'Website branch: %s\n' "$branch"
printf 'No commit, push or deployment was made. Review these files:\n'
git -C "$TARGET" status --short -- homepages/vrampage
