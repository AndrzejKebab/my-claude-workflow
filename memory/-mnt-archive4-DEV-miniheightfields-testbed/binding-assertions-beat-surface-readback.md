---
name: binding-assertions-beat-surface-readback
description: "A wrong pool origin still lands in some painted slot — assert the MPB binding, never the rendered surface, when the claim is about WHERE a sampler reads"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4f26c060-09f8-4d4e-96ce-ef002cea51cc
  modified: 2026-08-05T02:38:44.322Z
---

When the assertion is **where** a sampler reads — pool origin, per-layer `TileParams`/`PhysicalSize`,
which page table — grade the **MaterialPropertyBlock the draw writes**, not the pixels it produces.

Measured 2026-08-05 on the VT channel debug view. A sabotage bound the *reference* layer's pool
geometry instead of the *selected* layer's. The surface readback stayed **green**; the MPB assertion
failed exactly: `Expected (32.00, 2.00, 39.00, 0.00) But was (128.00, 2.00, 39.00, 0.00)`.

**Why:** a uniformly-painted pool slot means a wrong origin still lands in *some* painted slot. The
ground looks correct while the arithmetic is wrong, so the picture cannot distinguish the two.

**How to apply:** split the gate. Content claims ("this channel shows that value") read the pool or the
surface; *addressing* claims ("it read the selected layer's own geometry") read the bound values and
compare exactly. A single surface gate covering both passes vacuously on the addressing half.

Same family as [[vt-composite-determinism]]'s measured rule that a rendered frame and a pool readback
disagree about identical pool content, and [[gate-must-exercise-worst-case-regime]] — all three say the
rendered picture is the weaker oracle. See also
[[render-gate-settle-must-wait-on-subject]].
