---
name: deck-benchmark-launcher-and-staleness
description: "Deck run args live in the Steam shortcut, not -argv.json; and verify build/archive/scene are the same generation before measuring"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5262e936-24af-4221-9c7b-4689d3fdfe79
  modified: 2026-07-21T15:26:22.198Z
---

Two things that cost failed Deck runs (2026-07-21):

**Run args live in the Steam shortcut, not the `-argv.json` file.** `deploy-deck.sh` registers the shortcut via `steam-client-create-shortcut --parms '{... "argv":[...]}'`, and `unity-run-game` launches from that. `<Game>_Linux-argv.json` is *written by* that registration — editing it alone changes nothing, and the player boots with no flags (observed: the delivery benchmark never initialised, FreeCamera stayed active). To change args, re-register the shortcut with the full PARMS. Deploying also **resets** argv to bare `["./<exe>.x86_64"]`, so args must be re-applied after every deploy.

**Verify the build, the archive and the scene are one generation before measuring.** They drift independently: a freeze updates `Assets/StreamingAssets` without rebuilding, and the deployed player carries the scene as it was *at build time*. Pushing a fresh archive into a stale build gives a mismatched page table and a black/wrong terrain. Cheap checks — `.zvra` header is `ZVRA`, i32 version, tileSize, borderSize, layerCount, tileCount, u64 hash, finestMip, coarsestMip (so `xxd -l 40` tells you the recorded range and tile count); compare its mtime against the scene's and `GameAssembly.so`'s.

Note the build re-freezes stale archives itself (`FreezeStaleArchivesOnBuild`), so after a rebuild the deployed archive's hash may differ from the one frozen by hand — that is the guarantee working, not drift.

Related: [[single-editor-test-runs]], [[editor-decides-player-executes]].
