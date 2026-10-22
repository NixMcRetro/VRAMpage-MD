#!/bin/bash

# Finder launches this file with an arbitrary working directory, so locate the
# bundle from the command file itself.
cd "$(dirname "$0")" || exit 1

# macOS may expose a python3 shim even when a usable interpreter is absent.
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
  echo "Python 3.8 or later is required to run VRAMpage MD locally."
  echo "Install Python 3 from https://www.python.org/downloads/macos/ and try again."
  read -r -p "Press Return to close this window. "
  exit 1
fi

if [ ! -f scripts/serve.py ]; then
  echo "This download is incomplete: scripts/serve.py is missing."
  echo "Re-download the complete runnable ZIP from the VRAMpage MD release page and extract the whole folder."
  read -r -p "Press Return to close this window. "
  exit 1
fi

python3 scripts/serve.py "$@"
status=$?
if [ "$status" -ne 0 ]; then
  echo
  read -r -p "Press Return to close this window. "
fi
exit "$status"
