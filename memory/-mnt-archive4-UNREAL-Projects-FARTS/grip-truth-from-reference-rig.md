---
name: grip-truth-from-reference-rig
description: "For anything the eye grades (grips, poses), mint ground truth from the marketplace reference rig instead of deriving it — Claude cannot judge these visually"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c3912f1-9627-4619-ac93-3eb314d233b9
  modified: 2026-08-05T16:09:37.520Z
---

The owner's words, 2026-08-05: *"you're seemingly incapable of evaluating visually — just not what
your training allows to see. all the metrics you've so far instrumented — also keeping you blind.
lets maybe establish few example poses on how people ACTUALLY hold two handed armaments? gruzzam
reference supposedly has it all in their setup — you can mint it."*

**Why:** the two-handed grip went several rounds where every derived metric was green and the result
was rejected on sight. Each derivation (where a palm centre sits, which side of a cylinder is `Over`,
how far apart hands go) was locally sound and collectively produced two hands stacked side by side on
one side of the pole. Reasoning about what a grip *is* was the wrong instrument, and so was looking
at the render — a screenshot that reads "fine" to me reads "nobody would do this" to them.

**How to apply:** marketplace animation packs ship a rig with the weapon skinned in — Gruzzam's is
`grruzam_weapon_hammer` under `hand_r`, 300 clips, all posed by someone who knows what a held hammer
looks like. Read the numbers straight off it (`Scripts/mint_reference_grip.py`) and use them as both
the authored values and the gate bounds. Prefer quantities computed in NO weapon frame — palm
opposition about the shared knuckle axis, hand span, knuckle agreement — because those are directly
comparable between the reference rig and ours without solving a frame-mapping problem first.

Sign conventions are not recoverable by reasoning; author one, measure, flip if the sign is wrong.
That took one 90-second capture where an argument would have taken an hour and been 50/50.

Related: [[milestone-needs-owner-qa]], [[ue-farts-gate-layer]], [[prefer-tools-over-guessing]].
