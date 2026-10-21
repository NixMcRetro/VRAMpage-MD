#!/usr/bin/env bash
# Import the verified local v0.1 source into a new GitHub review branch.
# Usage: bash scripts/import-local-v0.1.sh /absolute/path/to/mega-drive-vram-bender
# Run this from inside a clean VRAMpage-MD repository clone.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="${1:-$HOME/Downloads/mega-drive-vram-bender}"
SOURCE="$(cd "$SOURCE" && pwd)"
BRANCH="import/v0.1-source"
if [[ ! -d "$ROOT/.git" ]]; then
  echo "Run from a Git checkout of https://github.com/NixMcRetro/VRAMpage-MD" >&2
  exit 1
fi
if [[ "$(git -C "$ROOT" remote get-url origin)" != *"NixMcRetro/VRAMpage-MD"* ]]; then
  echo "The repository origin is not NixMcRetro/VRAMpage-MD; stopping." >&2
  exit 1
fi
if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
  echo "The destination checkout has uncommitted changes. Stop and review them." >&2
  exit 1
fi
if git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "A local $BRANCH already exists; not overwriting it." >&2
  exit 1
fi
if git -C "$ROOT" ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  echo "Remote $BRANCH already exists; not replacing it." >&2
  exit 1
fi
FILES=(
  scripts/build-core.sh
  scripts/patch_core.py
  scripts/test.sh
  scripts/vram_fault_patch.c
  site/app.js
  site/index.html
  site/style.css
  tests/fault_engine_smoke.c
  tests/test_mapping.py
)
for rel in "${FILES[@]}"; do
  if [[ ! -f "$SOURCE/$rel" ]]; then
    echo "Missing local source file: $SOURCE/$rel" >&2
    exit 1
  fi
done
if ! grep -qi 'VRAMpage' "$SOURCE/site/index.html"; then
  if grep -q 'Mega Drive VRAM Circuit Bender' "$SOURCE/site/index.html"; then
    echo "The working prototype still has its original title; apply the v0.1 frontend update first." >&2
    echo "Starting directory: anywhere." >&2
    echo "  cd \"$SOURCE\"" >&2
    echo "  python3 /Users/nix/Downloads/apply-vrampage-md-v0.1.py" >&2
    echo "Then rerun this importer from the VRAMpage-MD repository." >&2
  else
    echo "This does not look like the expected VRAMpage MD frontend; no files were imported." >&2
  fi
  exit 1
fi

git -C "$ROOT" fetch origin main
git -C "$ROOT" switch -c "$BRANCH" origin/main
for rel in "${FILES[@]}"; do
  mkdir -p "$ROOT/$(dirname "$rel")"
  cp "$SOURCE/$rel" "$ROOT/$rel"
done
mkdir -p "$ROOT/site/core" "$ROOT/docs"
printf '%s\n' 'Generated genplus.js and genplus.wasm are produced by scripts/build-core.sh.' > "$ROOT/site/core/.gitkeep"
if [[ -f "$SOURCE/README.md" ]]; then
  cp "$SOURCE/README.md" "$ROOT/docs/PROTOTYPE-V0.1-NOTES.md"
fi
chmod +x "$ROOT/scripts/build-core.sh" "$ROOT/scripts/test.sh" "$ROOT/scripts/stage-mcretro-release.sh"
git -C "$ROOT" add -- "${FILES[@]}" site/core/.gitkeep docs/PROTOTYPE-V0.1-NOTES.md scripts/stage-mcretro-release.sh
git -C "$ROOT" diff --cached --check
echo
echo "Source files to import:"
git -C "$ROOT" diff --cached --stat
echo
echo "Safety check: Only the files listed above are staged."
read -r -p "Create and push $BRANCH to GitHub? [y/N] " reply
if [[ ! "$reply" =~ ^[yY]$ ]]; then
  echo "Nothing was committed or pushed. Review the staged diff in $ROOT."
  exit 0
fi
git -C "$ROOT" commit -m "Import working VRAMpage MD v0.1 frontend and emulator fault-model source"
git -C "$ROOT" push -u origin "$BRANCH"
echo
echo "Pushed review branch: $BRANCH"
echo "Open: https://github.com/NixMcRetro/VRAMpage-MD/compare/main...$BRANCH?expand=1"
echo "No changes were made to McRetro.net."
