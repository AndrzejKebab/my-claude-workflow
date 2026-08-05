---
name: gpl-repo-split
description: "DONE (2026-07-03) — clap-router split into 4 published submodules + private root, GPL source-offer, CI-built cross-platform native binaries."
metadata: 
  node_type: memory
  type: project
  originSessionId: afe9eb2a-daae-4588-9f32-774d2a9d9ce2
---

Executed 2026-07-03. The private monorepo `github.com/api-haus/clap-router` (PRIVATE) now
embeds four published submodules (owner api-haus, fresh-init, no history):

- **MIT public:** `music-router` (`packages/music-router`), `clap-ipc-client` (`packages/clap-ipc-client`), `is.zori.unity-clap-router` (root path).
- **GPL-3.0 public:** `clap-ipc` (`packages/clap-ipc`) — the host.
- `clap-ipc` and `clap-ipc-client` each vendor `music-router` as a nested submodule behind `if(NOT TARGET music_router)` in CMake, so they build standalone (guard skips the double-add in the monorepo). `clap-ipc` also carries the CLAP SDK submodule (pinned). READMEs cross-link all four. Submodule URLs: SSH in root, HTTPS in the public repos.
- The Unity testbed game stays a subdirectory of the private root (private, not a separate repo).

**Native binaries (per user correction): the Unity package ships them, not gitignores them.** `is.zori.unity-clap-router/.github/workflows/build-native.yml` matrix-builds `clap_ipc_client` on ubuntu/windows/macos from the `clap-ipc-client` repo and a `commit-binaries` job commits `Plugins/{linux-x86_64,win-x86_64,macos}/` in-place (fastnoise2 pattern; triggers on push to the workflow file). All three platforms build green; per-platform `.meta` files were hand-authored. clap_ipc_client is MIT so shipping compiled artifacts is fine.

**GPL corresponding-source = written offer** ([[gpl-repo-split]] earlier decision): the packer writes `SOURCE-OFFER.txt` into StreamingAssets listing every GPL binary (clap-ipc host, Six Sines, Surge XT, Surge XT Effects) with exact-commit refs + a 3-year offer; no source trees bundled.

**Surge:** fetched via `tools/fetch_surge.sh` into gitignored `artifacts/surge/<platform>/` (linux + win done; macOS `.part`-died, re-fetchable). Packer (`ClapRouterContentPacker`, linux-only-guarded) ships linux Surge XT + Effects. **Vital still deferred** — no reproducible corresponding-source (upstream builds no CLAP).
