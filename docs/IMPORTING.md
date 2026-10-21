# Import the working v0.1 source from the Mac

The GitHub repo was created before the working Mac files were imported. The verified prototype was developed locally at `~/Downloads/mega-drive-vram-bender`. The source import must read that folder **without moving or modifying it**. Generated WebAssembly binaries are deliberately excluded from Git so builds are reproducible.

## Exact Terminal commands

**Starting directory: anywhere.** Run:

```bash
cd /Users/nix/Downloads
git clone https://github.com/NixMcRetro/VRAMpage-MD.git
cd /Users/nix/Downloads/VRAMpage-MD
bash ./scripts/import-local-v0.1.sh /Users/nix/Downloads/mega-drive-vram-bender
```

Confirm with `y` after reviewing the staged file list. Git will create `import/v0.1-source`, commit the allowlisted files and push the review branch. Git may request authentication. It **does not** touch McRetro.net, change the existing working prototype or merge into `main`.

Then open the pull request URL printed by the script. Review files and tests before merging into `VRAMpage-MD/main`. The website's `main` remains completely separate.

## Included from the local working project

- `site/index.html`, `site/app.js`, `site/style.css`
- `scripts/build-core.sh`, `scripts/patch_core.py`, `scripts/vram_fault_patch.c`, `scripts/test.sh`
- `tests/test_mapping.py`, `tests/fault_engine_smoke.c`
- The original local technical notes preserved in `docs/PROTOTYPE-V0.1-NOTES.md`
- A tracked placeholder for `site/core/`, whose real WASM/JS contents are produced by the build.

## Deliberately excluded

The repository does not import any local `vendor/` Git checkout, `site/source/` generated source distribution, compiled core, game ROM, game-save data, credentials, backup files or caches.

If the clone already exists or the import branch already exists, inspect its status rather than deleting work or rerunning import blindly.

## Next stage

After the source review PR is merged, test the opt-in **Build VRAMpage MD website bundle** GitHub Action. The resulting archive contains a complete static `vrampage/` folder including corresponding modified emulator source, ready to stage in `mcretro.net/homepages/vrampage/` on a separate review branch.
