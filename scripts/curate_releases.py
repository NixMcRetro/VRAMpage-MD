#!/usr/bin/env python3
"""Synchronize novice-friendly GitHub release titles and notes without changing binaries."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "release-notes/catalog.json"


class CurationError(Exception):
    pass


def load_catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    source_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    released_version = data["current"].removeprefix("v")
    if data["repository"] != "NixMcRetro/VRAMpage-MD":
        raise CurationError("Unexpected repository in release catalog.")
    if not re.fullmatch(r"0\.\d+\.\d+", source_version):
        raise CurationError("Invalid source VERSION.")
    if tuple(map(int, source_version.split("."))) < tuple(map(int, released_version.split("."))):
        raise CurationError("Published release version is newer than source VERSION.")
    entries = data["releases"]
    tags = [entry["tag"] for entry in entries]
    if len(tags) != 12 or len(set(tags)) != len(tags) or tags[0] != data["current"]:
        raise CurationError("Incorrect, duplicate or unordered release entries.")
    for entry in entries:
        tag = entry["tag"]
        if not re.fullmatch(r"v0\.\d+\.\d+", tag):
            raise CurationError(f"Invalid release tag: {tag}")
        if not re.fullmatch("[a-f0-9]{40}", entry["source_commit"]):
            raise CurationError(f"Invalid original commit for {tag}")
        if not entry["title"].startswith(f"VRAMpage MD {tag}"):
            raise CurationError(f"Invalid title for {tag}")
        expected = ([f"VRAMpage-MD-{tag}-macos.zip", "SHA256SUMS.txt"]
                    if tag in ("v0.2.4", "v0.2.5", "v0.2.6") else [])
        if sorted(entry["assets"]) != sorted(expected):
            raise CurationError(f"Unexpected asset policy for {tag}")
        note = (ROOT / "release-notes" / f"{tag}.md").read_text(encoding="utf-8")
        if entry["source_commit"] not in note or "v0.2.6" not in note:
            raise CurationError(f"Missing provenance/latest-version link for {tag}")
        if expected and expected[0] not in note:
            raise CurationError(f"No direct Mac ZIP link for {tag}")
        if not expected and "SOURCE HISTORY ONLY" not in note:
            raise CurationError(f"Historical {tag} must state source-only status.")
    return data


def gh_get(repository, path):
    proc = subprocess.run(["gh", "api", f"repos/{repository}/{path}"],
                          capture_output=True, text=True, check=False)
    if proc.returncode:
        raise CurationError(f"GitHub API failed for {path}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def preflight(data):
    """Check every immutable source tag and attached file BEFORE changing notes."""
    remote = {}
    for item in data["releases"]:
        tag = item["tag"]
        rel = gh_get(data["repository"], f"releases/tags/{tag}")
        ref = gh_get(data["repository"], f"git/ref/tags/{tag}")
        assets = sorted(asset["name"] for asset in rel.get("assets", []))
        if rel["tag_name"] != tag or rel.get("draft") or rel.get("prerelease"):
            raise CurationError(f"Unexpected published release status: {tag}")
        if assets != sorted(item["assets"]):
            raise CurationError(f"Release assets differ for {tag}: {assets}")
        if ref["object"]["type"] != "commit" or ref["object"]["sha"] != item["source_commit"]:
            raise CurationError(f"Release tag changed unexpectedly: {tag}")
        remote[tag] = rel
    return remote


def sync(data, remote):
    repo = data["repository"]
    for item in data["releases"]:
        tag = item["tag"]
        path = ROOT / "release-notes" / f"{tag}.md"
        note = path.read_text(encoding="utf-8")
        existing = remote[tag]
        if existing["name"] == item["title"] and existing.get("body", "").rstrip() == note.rstrip():
            print(f"Already current: {tag}")
            continue
        subprocess.run(["gh", "release", "edit", tag, "--repo", repo,
                        "--title", item["title"], "--notes-file", str(path)], check=True)
        print(f"Updated title and notes: {tag}")
    subprocess.run(["gh", "release", "edit", data["current"],
                    "--repo", repo, "--latest"], check=True)
    print(f"Latest release: {data['current']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Offline validation (default)")
    parser.add_argument("--apply", action="store_true", help="Apply curated notes using GitHub Actions on main")
    args = parser.parse_args(argv)
    try:
        data = load_catalog()
        if args.apply:
            if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REF") != "refs/heads/main":
                raise CurationError("Applying changes is restricted to GitHub Actions on main.")
            if os.environ.get("GITHUB_REPOSITORY") != data["repository"]:
                raise CurationError("Wrong GitHub repository for release edits.")
            sync(data, preflight(data))
        else:
            print(f"Validated {len(data['releases'])} release notes; current: {data['current']}.")
    except (CurationError, ValueError, KeyError, FileNotFoundError,
            subprocess.CalledProcessError) as error:
        print(f"Release curation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
