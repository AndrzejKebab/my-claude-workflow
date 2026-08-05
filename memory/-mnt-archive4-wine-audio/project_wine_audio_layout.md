---
name: project-wine-audio-layout
description: /mnt/archive4/wine-audio is a self-contained wine prefix for audio plugins with its own bundled wine-tkg runner; WINEPREFIX is NOT set automatically in shell
metadata: 
  node_type: memory
  type: project
  originSessionId: 615f231a-b711-465f-a087-4e4eef09e5f4
---

`/mnt/archive4/wine-audio/` is a self-contained audio-plugin wine setup with non-standard layout:
- `prefix/` — the WINEPREFIX (drive_c with FabFilter, Native Instruments, Neural DSP, Arturia, Steinberg, SINE Player, iLok, etc.)
- `runner/` — bundled wine-tkg 9.21 staging-fsync-esync build (wine-9.21.r0.gf03d32e3); `runner/bin/wine` is the binary
- Prefix is Windows 10 Pro mode

**Why:** Audio production prefix kept separate from system wine so plugin installs and configs don't get clobbered by system updates. Bundled runner pins a known-working wine build for the audio toolchain.

**How to apply:**
- The shell has `WINELOADER=/mnt/archive4/wine-audio/runner/bin/wine` set but **NOT** `WINEPREFIX` — always set `WINEPREFIX=/mnt/archive4/wine-audio/prefix` explicitly when invoking wine here.
- To install a new app: `WINEPREFIX=/mnt/archive4/wine-audio/prefix /mnt/archive4/wine-audio/runner/bin/wine <installer.exe>` — but for WebView2/Electron apps the bundled 9.21 may not work; see [[feedback-wine-version-for-webview2]] (Beatport Access needed wine-staging 11.2).
- Working invocation for Beatport Access: `WINEPREFIX=/mnt/archive4/wine-audio/prefix ~/.local/share/lutris/runners/wine/wine-staging-11.2-x86_64/bin/wine "C:\Program Files\Plugin Boutique\Beatport Access\Beatport Access.exe"`. WebView2 Runtime 148.0.3967.70 was installed into the prefix via the bundled `MicrosoftEdgeWebview2Setup.exe`.
- Switching wine versions on this prefix requires killing the existing wineserver: `WINEPREFIX=/mnt/archive4/wine-audio/prefix /mnt/archive4/wine-audio/runner/bin/wineserver -k` — the wine-tkg wineserver tends to stay resident across sessions.
