#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
root=${CHECKPOINT_PROOF_DIR:-"$repo/build/checkpoint-proof"}
mkdir -p "$root"
python3 "$repo/scripts/checkpoint-proof/build.py" "$repo" "$root"
