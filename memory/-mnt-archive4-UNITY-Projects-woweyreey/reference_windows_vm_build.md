---
name: Windows VM build pipeline
description: SSH into Windows VM (192.168.122.75) for IL2CPP Windows builds — drive mapping, credentials, prerequisites
type: reference
originSessionId: e1f14525-b805-4234-b695-513d02fc5490
---
Windows build runs on a QEMU/KVM VM (`ssh vm` / 192.168.122.75, user: mail).

**Drive mapping**: SSH sessions can't see interactive mapped drives. The bat file must `net use J: \\192.168.122.1\unityprj /user:midori <password> /persistent:yes` before launching Unity. Password is in `unity_build.bat` (scp'd to VM by `build.sh`).

**Two-file approach**: `build.sh` scps `unity_build.bat` to VM then executes it — avoids bash→SSH→cmd.exe escaping nightmares.

**VM prerequisites**: Unity 6000.3.14f1, Windows IL2CPP module (via Unity Hub `--headless install-modules`), Visual Studio "Desktop development with C++" workload (MSVC for IL2CPP).

**Unity Hub path**: `C:\Program Files\Unity Hub\Unity Hub.exe` (NOT `C:\Program Files\Unity\Hub\`).

**First run after code changes**: May OOM during import+build. Run a refresh-only pass first (`-batchmode -nographics -projectPath ... -logFile - -quit` without `-executeMethod`), then build.

**Output**: `Builds/Windows/` in main project (via `../woweyreey/Builds/Windows/` relative path from `woweyreey_copy`).

**Deck deploy (Proton)**: `deploy-deck.sh` registers as `woweyreey_Windows` with `steam_play: 1`. D3D12 shader variants may need attention (black & white rendering observed 2026-04-26).
