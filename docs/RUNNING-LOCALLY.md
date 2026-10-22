# Run VRAMpage MD locally

1. Open the GitHub Actions build linked in the development report. Sign in to GitHub if prompted, then download **VRAMpage-MD-local-review** under **Artifacts**.
2. Unzip the download, then unzip the `VRAMpage-MD-local-review.zip` inside it. The inner ZIP preserves the Mac launcher’s executable permissions. GitHub’s **Code → Download ZIP** is source-only and does not include the built emulator.
3. In the resulting `VRAMpage-MD` folder, double-click `START.command`.
4. The launcher opens VRAMpage MD in your browser. Load a game file from your computer using **Load ROM**.

Python 3 must be installed ([official macOS installer](https://www.python.org/downloads/macos/)).
If macOS blocks `START.command`, use this Terminal fallback:

1. Open **Terminal**.
2. Type `bash `, including the space after it.
3. Drag `START.command` from Finder into the Terminal window.
4. Press **Return**. The script finds its own folder automatically.

The launcher chooses an available local port, so another local app need not be stopped.

The launcher serves the files from your computer and only listens on `127.0.0.1`. It does not send game files to a server. Leave the Terminal window open while using the page; press **Control+C** there to stop it.

The review bundle includes the built emulator and its corresponding source, so it does not need the Emscripten SDK. A source checkout without those build outputs must first follow the build instructions in [README.md](../README.md).

The playable interface is v0.1.4. The first v0.2 work-RAM model is a separately
tested C foundation; it does not add game-logic fault controls yet.

Review artifacts are kept on GitHub for 30 days and require a GitHub sign-in.
They do not depend on the Codex cloud environment remaining connected. To refresh
one, run the **Build VRAMpage MD website bundle** workflow on the review branch;
it builds artifacts and does not deploy the website.
