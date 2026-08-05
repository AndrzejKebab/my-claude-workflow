---
name: feedback-wine-version-for-webview2
description: "For WebView2/Electron grey-window or no-renderer-spawn issues under Wine, try a newer wine-staging version BEFORE tweaking Chromium flags"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 615f231a-b711-465f-a087-4e4eef09e5f4
---

For Chromium-based apps under Wine (WebView2 hosts, Electron, CEF) showing **grey/blank window** or **renderer subprocess never spawns**, try a newer wine-staging build before tweaking `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` / `--disable-gpu` / `--no-sandbox` flags.

**Why:** Beatport Access (Plugin Boutique, WebView2-based) was stuck grey under wine-tkg 9.21 — `Beatport Access.exe` was alive but **zero `msedgewebview2.exe` child processes spawned**. Adding `--no-sandbox` (the usual "fix") just crashed the main process. Switching to wine-staging 11.2 (Lutris runner) made the full Chromium process tree spawn correctly on first try. User confirmed by saying "we had success with stupid webapps by switching wine versions around" before I tried it.

**How to apply:**
- If you see a Chromium-based app render a flat grey/blank window under Wine, first thing: check process tree for `msedgewebview2.exe` / `chrome.exe` renderer children. **No children = wine version problem**, not a flag problem.
- Inventory wine versions before guessing: check `~/.local/share/lutris/runners/wine/`, `~/.steam/root/compatibilitytools.d/`, `/opt/wine-*`. Pick the newest staging build.
- Switching wines on an existing prefix requires killing the old wineserver first (`WINEPREFIX=... <old-wine-path>/wineserver -k`), else you get `version mismatch N/M` errors.
- Don't pile on Chromium flags blind — `--disable-software-rasterizer` combined with `--disable-gpu` removes ALL render paths and crashes the renderer; `--in-process-gpu` is unstable on Wine.
- See [[project-wine-audio-layout]] for the wine-audio prefix specifics.
