---
name: epic-launcher-wine-eos
description: "Epic Games Store 20.x under Lutris/umu-Proton — self-update never restarts, and the hard EOS gate needs dotnet48 + win10 + manual service registration"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6049b6d4-a8d0-4e04-938c-09d50b889db6
  modified: 2026-08-04T20:29:51.272Z
---

Epic Games Launcher lives in the Lutris prefix `/mnt/archive4/epic-games-store`
(runner `umu-run` + GE-Proton11-3, launched with `-opengl -SkipBuildPatchPrereq`).
It is needed **only** to download Fab / UE marketplace vault content for the native
Linux UE at `/mnt/archive4/UNREAL/UE_5.8.0` — the Windows UE it downloads
(`/mnt/archive4/UNREAL/WIN/UE_5.8`) cannot run under Proton at all
(see [[epic-windows-ue-not-runnable]]).

Four separate traps, hit in order on 2026-08-04:

**1. Self-update never completes.** The launcher stages the update fine, then logs
`Bootstrap shutdown: Set bShouldPrimeEms=true for restart` and exits — and Proton
never relaunches it. Looks like a hang; the umu wrapper lingers with no window.
Fix: after it exits, apply the staged tree by hand —
`rsync -a <prefix>/drive_c/ProgramData/Epic/EpicGamesLauncher/Data/Update/Install/ \
 "<prefix>/drive_c/Program Files/Epic Games/Launcher/"`
then `cp LauncherUpdate.manifest{,.meta} → Launcher.manifest{,.meta}`. Without the
manifest copy it re-stages forever (`InstalledManifestWithDataFuture was not valid`).
Installing the latest MSI alone does NOT update `Launcher.manifest`, so it loops.

**2. 19.x had no EOS requirement; 20.x has a non-dismissible one.** Verified: the
19.1.7-era log has zero `EoshState`/`InstallEOS` lines. 20.x shows a modal whose only
button is "Restart and Install" — EOS cannot be skipped. Updating off 19.1.7 is a
one-way door unless you keep the old binaries.

**3. EOS MSI needs real .NET.** Fails 1603 with
`SFXCA: Failed to get requested CLR info` — WiX managed custom actions; Wine Mono
doesn't satisfy them. `winetricks dotnet48` (drive it with GE-Proton's own wine via
`WINE=.../GE-Proton11-3/files/bin/wine`, no runner switch needed).
The MSI still aborts on its last action, so install it with rollback off:
grab the extracted MSI from `ProgramData/Epic/EpicOnlineServices/EOSInstaller/<GUID>/`
mid-run, then `msiexec /i C:\EOS.msi /qn DISABLEROLLBACK=1 EOSPRODUCTID=EpicGamesLauncher`.

**4. dotnet48 sets the prefix to win7, which breaks EOS.** The EOS helper is a
**Node.js** app (`os_toolbox.node`) and refuses to run below Windows 8.1
(`Node.js is only supported on Windows 8.1 ... or higher`). Run `winetricks -q win10`
*after* dotnet48. Then the last blocker is the EOS Windows service, which
`EpicOnlineServicesHost.exe install` cannot register under Wine (exit 1006/238) —
register it manually instead:
`sc create EpicOnlineServicesHost binPath= "C:\Program Files (x86)\Epic Games\Epic Online Services\service\EpicOnlineServicesHost.exe" start= auto`
then `sc start EpicOnlineServicesHost`. Launcher then reports `EoshState = Enabled`.

Registry EOS registration lives at `HKLM\Software\Wow6432Node\Epic Games\EOS\`
(`MainService\Version` is the value the launcher version-checks).

**Alternative worth preferring for Fab:** fab.com "My Library" downloads directly in a
browser, and `pip install ue-asset-cli` is a Linux CLI for marketplace assets — neither
needs this prefix. Reach for those before rebuilding any of the above.

Prefix backup (registry + Epic manifests, pre-dotnet48):
`/mnt/archive4/epic-games-store.backup-pre-dotnet48`.
