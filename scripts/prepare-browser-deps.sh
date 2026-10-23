#!/usr/bin/env bash
# CI runner setup only. Keep Ubuntu suites, components and signing keys intact.
set -euo pipefail

task_sources=()
for task_source in /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list; do
  if [[ -f "$task_source" ]]; then
    sudo sed -i \
      -e 's|http://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' \
      -e 's|https://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' \
      "$task_source"
    task_sources+=("$task_source")
  fi
done

# Current hosted runners use mirror+file URIs, so updating only ubuntu.sources
# would leave the slow Azure mirror active. Keep those URI references intact.
if [[ -f /etc/apt/apt-mirrors.txt ]]; then
  printf '%s\n' 'https://archive.ubuntu.com/ubuntu/' | \
    sudo tee /etc/apt/apt-mirrors.txt >/dev/null
  task_sources+=(/etc/apt/apt-mirrors.txt)
fi
if [[ -f /etc/apt/apt-security-mirrors.txt ]]; then
  printf '%s\n' 'https://security.ubuntu.com/ubuntu/' | \
    sudo tee /etc/apt/apt-security-mirrors.txt >/dev/null
  task_sources+=(/etc/apt/apt-security-mirrors.txt)
fi

if ((${#task_sources[@]} == 0)) || \
    ! grep -Fq 'https://archive.ubuntu.com/ubuntu' "${task_sources[@]}"; then
  echo 'Ubuntu archive configuration was not found; review the runner image.' >&2
  exit 1
fi
if grep -Fq 'azure.archive.ubuntu.com' "${task_sources[@]}"; then
  echo 'The slow Ubuntu Azure mirror is still configured.' >&2
  exit 1
fi
printf '%s\n' 'Ubuntu packages: standard archive and security mirrors; original signing keys retained.'

# Playwright invokes apt itself. Bound idle transfers without changing its
# package list; the workflow step also has an overall time limit.
sudo tee /etc/apt/apt.conf.d/99vrampage-downloads >/dev/null <<'APT'
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";
Acquire::Retries "1";
APT
