---
name: ca-sleep-economy-stalls-phase-transitions
description: zori.is CA tests — settled regions sleep and stop running phase transitions/reactions
metadata: 
  node_type: memory
  type: reference
  originSessionId: a9d9a506-4575-4472-8e10-6ddaec57d5df
---

In zori.is the dirty-rect sleep economy stops scanning a settled, unchanging tile (cooldown → 0), so `resolve_cell` (and thus `phase_transition` / `react`) no longer runs there. A black-box test that fills a **packed, static** pool of material and expects a temperature/reaction conversion will stall partway: the region converts only while still awake, then sleeps with material unconverted.

**How to apply:** fill the material so it keeps *moving* — at the top with void below (it falls/settles), the way `weather_tests` does for snow-melt and water-freeze — so the tiles stay awake until the conversion completes. `change_material` wakes neighbours, which keeps an actively-converting region awake, but a region that settles before converting will sleep first.

Related: [[blackbox-test-harness.md]].
