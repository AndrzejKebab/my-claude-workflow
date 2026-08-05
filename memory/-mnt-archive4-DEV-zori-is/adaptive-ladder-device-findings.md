---
name: adaptive-ladder-device-findings
description: "Device perf characteristics driving the adaptive quality ladder (iPhone vs Samsung tablet, June 2026)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0e8979ab-e848-4720-aa7c-43ef3163fcdb
---

Device benchmarks (June 2026) for redesigning `src/scene/adaptive.rs` LADDER. Ship `render.scale`
is **≤0.5** — scale=1.0 is **never** an operating point (per user). Neither iPhone nor the Samsung
tablet exposes a WebGL2 GPU timer, so the per-effect signal is the whole-frame leave-one-out A/B.

- **iPhone**: GPU-comfortable. Locked 60 fps at scale 0.5 with headroom → the ladder rarely engages.
  Per-effect costs are below the vsync margin at 0.5 (unmeasurable there); ranking came from a
  saturated scale=1.0 run.
- **Samsung tablet**: the constrained device the ladder serves. At scale 0.5 it's ~30 fps (frame
  ~33 ms, sim throttled to 30 Hz). Saturated → the A/B resolves the big costs.

**Cross-device cost ranking (the rung ordering basis):**
`render.scale (∝ scale², the giant) ≫ aurora (volumetric march; aurora.steps is the knob) > nebula
> {weather, lens_dirt, bloom, tonemap, wet ~2–4 ms} > {events, mountains, stars, cloudlight ~0.1–0.5}
> {reflect-capture, clouds, jfa-cull, shoot — below the A/B floor}`. aurora+nebula ≈ 19 ms on the
tablet. Fine count knobs (jfa.iterations, reflect.march_max, …) sit below the cadence-bounce floor.

Full data + raw summaries: `docs/orchestrate/adaptive-ladder/`. See [[measurement-reports-committed]].
