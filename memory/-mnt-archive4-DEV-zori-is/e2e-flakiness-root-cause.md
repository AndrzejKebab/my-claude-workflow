---
name: e2e-flakiness-root-cause
description: zori.is e2e flakiness = SwiftShader render starving the setInterval sim clock on an oversubscribed CPU; fix is drive-by-count
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fabd40-fd2b-445d-97f9-c7f602175573
---

zori.is Playwright e2e is **serial** (`fullyParallel: false`) but flakes because of contention *within* one test, not across tests. The headless backend is SwiftShader (WebGL emulated on CPU), so every rendered frame is a heavy **main-thread** job; the sim ticks on a `setInterval` on the *same* main thread, plus its worker pool. On the dev box (~22 baseline load on 24 cores) the suite's own render adds ~30 → ~load 53, so the render starves the tick clock and the sim crawls (measured: a 200-tick window advancing 5 ticks). Tests written as `waitForTimeout(...)` / fixed-window sampling / short condition-waits assume ~60 Hz and time out → the **failing set shifts run-to-run** (it's a timing race, not a fixed break; feature code is fine, adaptive is off under `webdriver`).

Fix = make tests deterministic by **count**, not wall-clock:
- sim-tick progress → `window.__zori.setLiveTick(false)` (spec owns the sim clock) + `runTicks(n)` / a `driveUntil(pred)` poll. NOTE: a painted material lands ~13 ticks after the mailbox push (worker pipeline lag), so use `driveUntil`, not a tiny fixed count.
- render-frame progress (meteors `shooting_active`, weather crossfade/auto-advance — all advance in `render_impl`) → `paceSetManual(true)` + a loop of `runTicks(1)`+`paceStep(t+=dt)` per frame in ONE `page.evaluate` (no per-frame IPC). Small dt: a sparse frame's big dt spawns-and-expires meteors in one step.
- the meteor night gate reads a render-published factor → `setNight(1.0)`; the director caps active events → raise `events.max_concurrent`.
- NEVER mix runTicks with the live tick (double-driver races the mailbox drain) — always `setLiveTick(false)` first.

Test seams added (DEV-gated in boot.js, `import.meta.env.DEV`): `debug_set_live_tick` / `__zori.setLiveTick`, `debug_set_night` / `__zori.setNight` (src/ca/debug.rs, src/ca/driver.rs). Pre-existing: `runTicks`, `paceSetManual`/`paceStep`. See [[avoid-long-verifications]].

Better long-term fix (not yet done): an `e2e-norender` mode that splits `frame()` into cheap "advance+publish" (keep — it publishes night/weather/preset into the sim) vs expensive GL passes (skip). Frees the thread so live-sim tests pass as-written and would let many of these conversions be reverted.
