---
name: tile-parking-system
description: "zori.is viewport-radius tile-parking — P1 (CA) landed, P2–P4 remain"
metadata: 
  node_type: memory
  type: project
  originSessionId: ffef0a73-7381-406f-9545-d7c9b208eb0f
---

Viewport-radius tile-parking on branch `api-haus/world-streaming`: park (freeze sim for) entities outside
`camera.active_tile_radius` TILEs of the viewport, to bound active sim cost to ~viewport-area. The load
lever the particle/sim work was built toward. Design + phasing: `docs/streaming/tile-parking.md`.

**P1 (CA cells) — DONE**, commit `1681c1b` (2026-06-30). `camera.active_tile_radius` (Camera group,
default **-1 = off**), published per tick beside the viewport; `WorldDims::window_active` /
`tile_active_buffer` + `streaming::on_screen_margin` are the active-tile authority; two gates in
`band.rs` — `simulate_tile` skips off-radius sim, `tick_cooldowns` freezes a parked tile's dirty rect so
unpark resumes. Gate: `tests/tile-parking.spec.js`.

**Remaining:** P2 particle cull (wire built `park_tiles`/`unpark_tiles`), P3 body cull (`evict_tiles` +
RAM `SavedBody` + collider cache), P4 rain/handoff active-region gating — then flip the default on.

Default is -1 until P4 because parking the window's top row would freeze rain before it reaches a viewport
below it. At -1 every code path is inert (byte-identical to pre-park).

Gotchas seen landing P1: `paintWorld` enqueues to the worker mailbox (applied during a tick, not
synchronously); sand dropped into open void is handed off to the airborne-particle tier and leaves the
grid (P4 will gate this). `tests/streaming.spec.js` + `events`/`events-hud` specs fail on clean HEAD
already (stale OPFS-save + event-kinds expectations) — NOT regressions. Related: [[world-streaming-indirection]], [[blackbox-test-harness]].
