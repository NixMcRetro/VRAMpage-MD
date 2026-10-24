#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${1-normal}"
if [[ $# -gt 1 || ( "$PROFILE" != normal && "$PROFILE" != runtime && "$PROFILE" != site-runtime ) ]]; then
  echo "Usage: $0 [normal|runtime|site-runtime]" >&2
  exit 2
fi
if [[ "$PROFILE" == runtime ]]; then
  exec python3 "$ROOT/scripts/build-core-runtime.py"
fi
if [[ "$PROFILE" == site-runtime ]]; then
  python3 "$ROOT/scripts/build-core-runtime.py"
  exec python3 "$ROOT/scripts/install-runtime-site.py"
fi
CORE="$ROOT/vendor/wasm-genplus"
PINNED_COMMIT="6090aff9e9b2f578cd28882bd4571d2e35b1d674"

for executable in git python3 emcmake emmake cmake; do
  if ! command -v "$executable" >/dev/null 2>&1; then
    echo "Missing build tool: $executable" >&2
    if [[ "$executable" == emcmake || "$executable" == emmake ]]; then
      echo "Activate Emscripten: source ~/emsdk/emsdk_env.sh" >&2
    fi
    exit 1
  fi
done

mkdir -p "$ROOT/vendor" "$ROOT/site/core"
if [[ -e "$CORE" ]]; then
  if [[ ! -d "$CORE/.git" ]]; then
    echo "Existing vendor/wasm-genplus is not a Git checkout. Move it aside, then retry." >&2
    exit 1
  fi
  actual_commit="$(git -C "$CORE" rev-parse HEAD)"
  if [[ "$actual_commit" != "$PINNED_COMMIT" ]]; then
    echo "Existing vendor/wasm-genplus is at $actual_commit, not $PINNED_COMMIT." >&2
    echo "Keep this checkout untouched; move it aside before a clean build." >&2
    exit 1
  fi
  if grep -q 'VRAM Circuit Bender: initial frame-scoped' "$CORE/src/main/c/wasm/wasm.c"; then
    echo "Reusing the already-patched vendor/wasm-genplus checkout."
  else
    if ! git -C "$CORE" diff --quiet || ! git -C "$CORE" diff --cached --quiet; then
      echo "Existing checkout contains unrecognised changes. Not overwriting them." >&2
      exit 1
    fi
    git -C "$CORE" submodule update --init --recursive
  fi
else
  git clone --recursive https://github.com/h1romas4/wasm-genplus.git "$CORE"
  git -C "$CORE" checkout "$PINNED_COMMIT"
  git -C "$CORE" submodule update --init --recursive
fi

# Reapply the supported, idempotent patches on both fresh and previously
# patched pinned checkouts. This also upgrades an existing checkout when a
# later frontend release needs a narrowly scoped source patch.
python3 "$ROOT/scripts/patch_core.py" "$CORE"

# Emscripten 4.0.7+ no longer exports HEAPU8 / HEAPF32 by default.
# The standalone browser frontend reads pixel, ROM, controller and audio data
# through those views. Add linker exports without relying on CMake CLI flags:
# upstream cmake/macros.cmake forcibly resets CMAKE_EXE_LINKER_FLAGS.
# Applying this even to an existing patched checkout is safe and idempotent.
python3 - "$CORE/CMakeLists.txt" <<'PY_EMSCRIPTEN_EXPORTS'
from pathlib import Path
import sys

cmake = Path(sys.argv[1])
text = cmake.read_text()
flag = '-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32'
if flag not in text:
    anchor = 'add_executable(${PROJECT_NAME} ${SOURCE_FILES})'
    if text.count(anchor) != 1:
        raise SystemExit('Expected CMakeLists target definition missing. Not modifying vendor source.')
    text = text.replace(anchor,
        '# VRAM Circuit Bender: export JS-accessible WASM heap views.\n'
        f'add_compile_flags(LD "{flag}")\n'
        + anchor, 1)
    cmake.write_text(text)
    print('Enabled Emscripten HEAPU8 and HEAPF32 runtime exports.')
else:
    print('Emscripten HEAPU8 and HEAPF32 runtime exports already configured.')
PY_EMSCRIPTEN_EXPORTS

mkdir -p "$CORE/build"
# wasm-genplus specifies cmake_minimum_required(VERSION 3.0), which CMake 4
# rejects by default. Setting the policy minimum leaves the vendor source
# untouched and works for both new and resumed builds.
(
  cd "$CORE/build"
  emcmake cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  emmake make -j2
)

cp "$ROOT/README.md" "$ROOT/site/README.md"
cp "$CORE/src/main/js/genplus.js" "$ROOT/site/core/genplus.js"
cp "$CORE/src/main/js/genplus.wasm" "$ROOT/site/core/genplus.wasm"
# Keep complete corresponding source with the distributed modified binary.
mkdir -p "$ROOT/site/source"
cp -R "$CORE/src" "$ROOT/site/source/"
cp "$CORE/CMakeLists.txt" "$ROOT/site/source/"
cp -R "$CORE/cmake" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_fault_patch.c" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction.c" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction.h" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction_core.h" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction_runtime.h" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction_render.h" "$ROOT/site/source/"
cp "$ROOT/scripts/work_ram_fault.c" "$ROOT/site/source/"
cp "$ROOT/scripts/work_ram_fault.h" "$ROOT/site/source/"
cp "$ROOT/scripts/work_ram_runtime.c" "$ROOT/site/source/"
cp "$ROOT/scripts/work_ram_runtime.h" "$ROOT/site/source/"
cp "$ROOT/scripts/patch_core.py" "$ROOT/site/source/"
cp "$ROOT/scripts/build-core.sh" "$ROOT/site/source/"
cp "$ROOT/scripts/build-core-runtime.py" "$ROOT/site/source/"
cp "$ROOT/scripts/vram_transaction_api.js" "$ROOT/site/source/"
cp "$ROOT/scripts/psg_data_fault.h" "$ROOT/site/source/"
cp "$ROOT/scripts/psg_data_fault_core.c" "$ROOT/site/source/"
cp "$ROOT/scripts/psg_data_fault_runtime.c" "$ROOT/site/source/"
cp "$ROOT/scripts/psg_data_fault_api.js" "$ROOT/site/source/"
cp "$ROOT/scripts/fm_data_fault.h" "$ROOT/site/source/"
cp "$ROOT/scripts/fm_data_fault_core.c" "$ROOT/site/source/"
cp "$ROOT/scripts/fm_data_fault_runtime.c" "$ROOT/site/source/"
cp "$ROOT/scripts/fm_data_fault_api.js" "$ROOT/site/source/"
cat > "$ROOT/site/source/README.txt" <<'TEXT'
Source for the modified Genesis Plus GX WebAssembly binary in ../core/.
Upstream: https://github.com/h1romas4/wasm-genplus
Please also consult the Genesis Plus GX source headers and licence notices.
This bundle is for personal/non-commercial use, subject to upstream terms.
TEXT
printf '\nBuilt! Run: cd "%s/site" && python3 -m http.server 8080\n' "$ROOT"
