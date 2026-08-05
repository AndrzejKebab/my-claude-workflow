---
name: deck-verdict-mislabels-machine-and-resolution
description: Delivery-benchmark verdicts from a Deck run print machine=PC and resolution=1920x1080 — mislabels; the numbers are real Deck costs
metadata: 
  node_type: memory
  type: reference
  originSessionId: 692b3934-7133-48d6-8cf4-18654c28c086
  modified: 2026-07-24T00:06:22.180Z
---

A `heightfield_delivery_*_verdict.txt` produced by a run that actually executed **on the Steam Deck**
prints `machine=PC` and `resolution=1920x1080`. Both are **mislabels** — the run was on the Deck and
the timings are real Deck costs. The reliable tell it ran on the Deck is `floor_ms=8.0000` (the Deck
floor; the dev-box floor is 4.2) and the delivery skill's log showing `=== ... on Steam Deck ===` +
deploy. Confirmed by the user twice (2026-07-23/24): "all of them ran on deck."

Do **not** re-interpret a Deck verdict as a local run because of the `machine=`/`resolution=` fields —
it wastes a round trip. Read the floor and the skill's deploy log instead. (The delivery skill probes
the Deck over SSH; only `--local` or a failed probe truly falls back to the dev box, and then the floor
reads 4.2.)

Related: [[deck-benchmark-launcher-and-staleness]].
