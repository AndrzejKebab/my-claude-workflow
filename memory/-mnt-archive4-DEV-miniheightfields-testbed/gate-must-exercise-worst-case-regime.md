---
name: gate-must-exercise-worst-case-regime
description: "An e2e gate that exercises a proxy for the worst case (not the real worst case) passes green while the untested regime stays broken; pick the gate's inputs to hit the actual boundary"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 82f1c76b-2749-4fea-bb5f-a033284a0a98
---

A red-first e2e gate can pass and still leave the real failure regime uncovered if its input is a *proxy* for the worst case rather than the worst case itself. Green then means "the tested regime is fixed," not "the problem is fixed."

**Why:** observed 2026-07 on the shadow box-slide budget. The fix bounded the pyramid rebuild for a *partial* slide (surviving cells copied, only the entering strip deferred). The editor gate drove a "Mach-14-class" slide at 180 texels/frame ≈ 70% of the box — a **sub-box** slide (`shift < res`) — and passed. The deck benchmark then showed the real period-400 path slides the box by **≥ its full width** on many frames (`shift >= res`), which hits a *different* code path (the forced full rebuild at `cmax(abs(shift)) >= res`) the budget can't defer. The gate's 70%-of-box proxy sat just under the `shift >= res` boundary that separates the two regimes, so it validated the easy path and never touched the hard one. Only the on-device measurement surfaced it.

**How to apply:** when a fix has a threshold/branch (here: partial vs super-box slide, `shift < res` vs `>= res`), the gate input must **cross** that boundary, not approach it — drive `shift >= res` (teleport the camera > a full box width in one frame), not 70% of it. Enumerate the code's own branch conditions and make the gate hit the expensive branch explicitly. And treat the durable in-editor gate and the on-device benchmark as complementary: the gate proves the mechanism cheaply and repeatably, the deck proves the *regime coverage* — a green gate whose proxy dodged the boundary is why you still run the benchmark. Relates to [[durable-e2e-not-editor-qa]] and [[verification-representatives-protocol]].
