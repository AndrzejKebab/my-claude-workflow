---
name: transition-regimen-reproduce-first
description: A single MotionTransitionSessionTests plant run is not evidence — it returned a materially different answer once and was identical on four runs either side
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0dea0b5e-5c2c-44aa-95dc-1a57e852cc29
  modified: 2026-07-25T13:48:42.519Z
---

`Swordgal.Tests.MotionTransitionSessionTests`' **plant** regimen (the 180 flick) returns materially
different answers on the same build. The arc regimen has never varied — across every run of both
episodes below it has been bit-identical to every decimal, including its walked distance.

Seen twice, both on the referential arm:

- 2026-07-25a: content −124.8° of body −164.4° once, against −60.4° of −134.6° on four runs before
  and after, nothing in the tree changed.
- 2026-07-25b: **content 76.2% of the flip on a `-testFilter` run and 63.1% in the full suite**, same
  commit, same arm, same session — while the arc returned 205.1° / 72.3% / 14.58 m on both. So
  suite context is one thing that moves it, and possibly the only thing, but that is not established.

**Why:** that one anomalous run was attributed to a code change (the settled penalty reading the
role's turn axis) and committed as a measured fix. An A/B with the condition reverted came back
bit-identical on both regimens, so the change was a no-op and the commit had to be withdrawn
(`4acd8d0c`). The cause of the anomaly is still unknown.

**How to apply:** before attributing any plant movement to a change, run it twice, and run the
control. A filtered run is cheap — `-testFilter Swordgal.Tests.MotionTransitionSessionTests` is two
cases — but **a filtered run and a full-suite run are not the same measurement**, so compare like
with like. Reverting the suspected line and confirming bit-identical output is the decisive test and
costs one more run. This is the project's own law applied to itself: a change that does not move the
metric is not the fix.

State the plant's **direction** when both readings agree on it and never a single figure; the arc is
the regimen to quote a number from.

Related: [[character-controls-manual-qa-over-e2e]], [[unity-test-xml-root-total-lies]].
