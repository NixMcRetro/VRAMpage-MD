#!/usr/bin/env bash
# CI runner setup only. Keep Ubuntu suites, components and signing keys intact.
set -euo pipefail

for task_source in /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list; do
  if [[ -f "$task_source" ]]; then
    sudo sed -i 's|http://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g; s|https://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' "$task_source"
  fi
done

# Playwright invokes apt itself. Bound idle transfers without changing its
# package list; the workflow step also has an overall time limit.
sudo tee /etc/apt/apt.conf.d/99vrampage-downloads >/dev/null <<'APT'
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";
Acquire::Retries "1";
APT
