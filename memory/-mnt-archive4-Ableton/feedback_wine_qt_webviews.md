---
name: wine-cachyos fixes Qt/CEF webviews on Hyprland+NVIDIA
description: When Wine apps render webview/auth dialogs as pure-white on this machine, switch from mainline wine to /opt/wine-cachyos
type: feedback
originSessionId: 4887e00b-609e-48c9-ae07-a2ac802bc0d1
---
On this machine (Hyprland + NVIDIA), mainline `/usr/bin/wine` renders Qt5 QML / Chromium-embedded webviews as **pure-white blank panes** — the issue reproduces with native Chromium apps too, so it's a system-wide rendering quirk, not Wine-specific. The Wine app itself usually works (main UI renders); only embedded webviews are broken.

`/opt/wine-cachyos/bin/wine` (package `wine-cachyos-opt`) renders these correctly. Confirmed for Ableton Live 11 Suite's authorization dialog (Qt Quick + ANGLE + libEGL.dll). User reported similar issue and same fix worked previously for "stupid VST with webviews".

**Why:** wine-cachyos has different patch set (Qt/win32u/wow64) than mainline. Hyprland+NVIDIA EGL path that mainline wine uses produces white frames; cachyos avoids it.

**How to apply:** When Wine app shows white/blank webview dialog, do NOT waste time on:
- `LIBGL_ALWAYS_SOFTWARE=1`, `QT_QUICK_BACKEND=software`, `QT_OPENGL=software`
- `--disable-gpu` / Chromium flags passed to host exe
- `gamescope -- wine ...` wrapper

Those don't fix it. Go straight to:

```
PATH=/opt/wine-cachyos/bin:$PATH WINELOADER=/opt/wine-cachyos/bin/wine \
WINESERVER=/opt/wine-cachyos/bin/wineserver \
/opt/wine-cachyos/bin/wine "..."
```

Same WINEPREFIX is fine — both wine builds share prefix layout.
