---
name: render-gate-settle-must-wait-on-subject
description: "A frozen terrain holds a bit-identical WRONG frame for ~15 frames at pending==0 — frame-count settles read mid-stream, three times now"
metadata: 
  node_type: memory
  type: project
  originSessionId: a9e768c7-eb1d-490d-aa8c-e4b31bc70e01
  modified: 2026-07-22T05:51:25.812Z
---

A frozen terrain holds a **bit-identical wrong frame for ~15 frames** at `pending == 0`, residency
stable and biases zero, then steps to the right one. So a render gate that settles by frame count
can read a mid-stream frame while every quiescence signal it checks says "done" — and because the
wrong frame is *stable*, repeating the capture reproduces it exactly, which reads as determinism.

Measured 2026-07-22: a 150-frame settle still had a tile **pending at frame 149**.

**Why:** residency is CPU-side and lands independently of the frame counter; "no pending work" is
published before the content it gates is actually sampled.

**How to apply:** `a settle is a wait on the subject, never a frame count` — now a law in
`AGENTS.md` §Running tests. `CaptureConverged` requires idleness plus a 30-frame window (the
measured 15, doubled). This defect has been found **three separate times** in this repo, so treat
any `Settle(SettleFrames)` you meet as suspect until you've checked what its subject is doing.
Related: [[durable-e2e-not-editor-qa]], [[waitallrequests-hides-cross-frame-readback-races]],
[[gate-must-exercise-worst-case-regime]].
