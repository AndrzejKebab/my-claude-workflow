---
name: pin-orthogonal-dimension-in-fixtures
description: "When a new adaptive subsystem couples gates to machine speed, each gate's fixture pins the orthogonal dimensions off via app config — never weaken the assertion"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 85f708ca-0120-4f06-9ab7-c197b1de2768
  modified: 2026-07-19T17:55:17.313Z
---

Budget pacing (per-wall-frame capacity), the speed response (wall-velocity margins/shed), and
adaptive prices (live GPU averages) each couple previously-deterministic gates to machine speed.
The fix that survived review: each gate keeps its exact assertion and its FIXTURE pins the
orthogonal dimensions to deterministic values through app config (`uploadBudgetMs = 0`,
`speedAdaptiveResidency = false`, explicit `uploadTileCostMs`/`pyramidTexelCostMs`) — the
cadence gate tests cadence unpaced, the pacing gates test pacing with speed off, the
adaptivity is judged by the on-device delivery benchmark, which is the only honest oracle for a
live-measured number.

**Why:** the alternative — loosening assertions (tolerances, streak allowances) — rots the gate;
observed when a hitch-tolerance rework was drafted for `MachFlight_ResidentSetTracksCamera` and
the config pin made it unnecessary and exact again.

**How to apply:** when a gate flakes after adding an adaptive/wall-clock-coupled feature, first
ask which dimension the gate's subject actually is, pin every other dimension via public config
in the fixture (one comment naming why), and leave the assertion exact. Related:
[[gate-must-exercise-worst-case-regime]], [[durable-e2e-not-editor-qa]].
