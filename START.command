#!/bin/bash

# Finder launches this file with an arbitrary working directory, so locate the
# bundle from the command file itself.
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required to run VRAMpage MD locally."
  echo "Install Python 3 from https://www.python.org/downloads/macos/ and try again."
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
