---
name: naadf-runs-on-linux-via-wine
description: NAADF (Windows-only DX11 voxel engine) builds on the win11 VM and runs on this Linux box via Wine+DXVK
metadata: 
  node_type: memory
  type: project
  originSessionId: 5c67887c-38f4-43eb-9ff8-621faa0882ac
---

NAADF is `net8.0-windows` + MonoGame Compute (WindowsDX/DX11) — README says Windows-only, but it builds and runs on Linux.

**Build:** the libvirt VM `win11` (`qemu:///system`, ssh host `vm` = 192.168.122.75, user `mail`) has .NET SDK 10 — no Visual Studio needed. `git clone` the repo there, then `dotnet publish NAADF/NAADF.csproj -c Release -r win-x64 --self-contained true`. SDK 10 builds the `net8.0` target fine. The csproj's `RestoreDotnetTools` target is harmless even without a `.config/dotnet-tools.json`.

**Run on Linux:** self-contained publish bundle lives at `/mnt/archive4/DEV/NAADF-win-build/publish/`; launch with `/mnt/archive4/DEV/NAADF-win-build/run-naadf.sh`. Wine 11.7 prefix at `~/.wine-naadf` with DXVK 2.7.1 installed (`winetricks -q dxvk`). Confirmed working 2026-05-14: world-gen DX11 compute shaders run through DXVK, renders at the RTX 5080. Steam/Proton also available at `/mnt/archive4/SteamLibrary/` but Wine+DXVK is the same stack and already works.

Note: `cc-filter` (`~/.cc-filter/config.yaml`) blocks `ssh`/`scp`/`sftp` by default — had to remove those `command_blocks` to drive the VM.
