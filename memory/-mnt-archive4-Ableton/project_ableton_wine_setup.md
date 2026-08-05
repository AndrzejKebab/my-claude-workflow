---
name: Ableton Live 11 Suite under Wine — install & launch recipe
description: Working setup at /mnt/archive4/wine-audio/prefix, launch via wine-cachyos + pw-jack + WineASIO
type: project
originSessionId: 4887e00b-609e-48c9-ae07-a2ac802bc0d1
---
Ableton Live 11 Suite installed under Wine, sharing the existing audio prefix at `/mnt/archive4/wine-audio/prefix` (the prefix Bitwig's yabridge VSTs already live in — Wine-Live loads them directly, no yabridge needed for the in-Wine DAW).

**Why this prefix:** VSTs already installed there (Kilohearts, NI, Archetype Tim Henson X, etc.). Live in Wine sees Windows VSTs natively from `Program Files/Common Files/VST{2,3}`.

**How to apply** when working on this Ableton setup:

Install gotchas (already worked around):
- Push3 audio driver MSI crashes (`tlsetupfx.exe` page faults — kernel driver, won't work in Wine). Marked non-vital in the bundle so installer continues; skip with `InstallAudioDriver=0` if needed but it doesn't actually skip Push.
- Final start-menu CustomAction calls `powershell.exe` which Wine doesn't ship → MSI fails with 0x80070642 → Burn rolls back the 4.5 GB Live install. **Mitigation: kill `wineserver` mid-rollback** (after MSI log shows `InstallFinalize`/`ProcessComponents`) to preserve files. Then delete the bundle's resume key: `wine reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{10D40FDC-F88C-48F3-B426-DFFB523AF190}" /f`.
- Live.exe lives at `C:\ProgramData\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe`.

WineASIO setup (already done):
- AUR `wineasio` package installs into `/usr/lib/wine/x86_64-{unix,windows}/`.
- The `wineasio-register` script bails on Wine 11+ (looks for nonexistent `wine64` binary).
- Manual install: copy `/usr/lib/wine/x86_64-unix/wineasio64.dll.so` to `$WINEPREFIX/drive_c/windows/system32/wineasio.dll` AND `system/wineasio.dll`, then `wine regsvr32 wineasio.dll`. Verify with `wine reg query "HKLM\\SOFTWARE\\ASIO\\WineASIO"`.

Launch command (must use wine-cachyos for Qt auth dialog to render):
```
WINEPREFIX=/mnt/archive4/wine-audio/prefix \
PATH=/opt/wine-cachyos/bin:$PATH \
WINELOADER=/opt/wine-cachyos/bin/wine \
WINESERVER=/opt/wine-cachyos/bin/wineserver \
pw-jack /opt/wine-cachyos/bin/wine \
  "/mnt/archive4/wine-audio/prefix/drive_c/ProgramData/Ableton/Live 11 Suite/Program/Ableton Live 11 Suite.exe"
```

Audio: WineASIO → JACK API → PipeWire (via `pipewire-jack`). In Live's Audio prefs, pick the WineASIO driver.
