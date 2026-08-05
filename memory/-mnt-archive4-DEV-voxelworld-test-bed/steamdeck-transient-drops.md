---
name: steamdeck-transient-drops
description: "The Steam Deck naps off the network then returns on the same IP; one failed ssh probe is not \"offline\"."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4f78ac3b-ebaa-4cd8-b6ef-873b37bd28c1
  modified: 2026-07-24T22:44:46.219Z
---

The Steam Deck (`ssh steamdeck` → `192.168.50.214`, user `deck`, key `~/.config/steamos-devkit/devkit_rsa`; the ssh alias hard-codes that HostName) transiently drops off the network while it sleeps — `ssh` returns "no route to host" and ping is 100 % loss — then returns on the **same IP** with multi-day uptime (observed: back with 6 days uptime minutes after a failed probe). A single failed probe is NOT evidence the Deck is offline or that its IP changed; retry, or ask the user to wake it, before concluding `NOT-MEASURED` for a Deck-gated benchmark (R-1).

This is the second near-miss concluding "Deck offline" from thin evidence — the first (D-1) concluded it from a *missing config file*, corrected by the user ("deck is online, `ssh steamdeck` always works"). Measure at the boundary: the Deck answers ssh when awake. The delivery-benchmark skill gates `DECK_ONLINE` on `DECK_IP` (from `SteamDeckDeploySettings.asset`) and `SSH_KEY` both non-empty. Related: [[voxelworld-foundations-spec]].
