# Run VRAMpage MD locally

1. Download and unzip the **ready-built review bundle** supplied with the development report. GitHub’s **Code → Download ZIP** is source-only and does not include the built emulator.
2. Double-click `START.command`.
3. The launcher opens VRAMpage MD in your browser. Load a game file from your computer using **Load ROM**.

Python 3 must be installed ([official macOS installer](https://www.python.org/downloads/macos/)). If macOS blocks `START.command`, open Terminal, move into the unzipped folder, and run:

```sh
bash START.command
```

The launcher serves the files from your computer and only listens on `127.0.0.1`. It does not send game files to a server. Leave the Terminal window open while using the page; press **Control+C** there to stop it.

The review bundle includes the built emulator and its corresponding source, so it does not need the Emscripten SDK. A source checkout without those build outputs must first follow the build instructions in [README.md](../README.md).

The playable interface is v0.1.4. The first v0.2 work-RAM model is a separately
tested C foundation; it does not add game-logic fault controls yet.
