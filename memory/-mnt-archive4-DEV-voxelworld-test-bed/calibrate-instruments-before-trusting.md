---
name: calibrate-instruments-before-trusting
description: Every metric in this project must have a calibration case with a known answer before its readings are believed or reported
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 109615a6-bc32-4e53-9db6-8d07cc0b337a
  modified: 2026-07-27T12:01:24.137Z
---

Do not report a measurement from an instrument that has no calibration case. In one session on
2026-07-27, five instruments each read plausibly while measuring themselves:

- An enclosed-background void classifier that called any hole touching the frame edge "sky", and
  read exactly 26 089 px across three builds whose trees differed 8×.
- A moving-vs-settled identity oracle, structurally blind to permanent holes — they are background
  in both passes and cancel to zero.
- An overhead ortho black-pixel count at 640×360, where `orthographicSize` is the VERTICAL
  half-extent, so ~40 % of the frame was off-world. It read 39.69 % "holes" on a sound world.
- `chunks_constant_solid`, which no code ever incremented. Its hard zero was read as proof the
  terrain had no interior, and cost hours.
- The Deck delivery benchmark judging a Steam Deck against the 4.2 ms desktop floor at 2× its
  native resolution, because `SystemInfo.deviceModel` returns "PC".

**Why:** a metric that cannot move when the subject moves is not measuring the subject, and a
wrong number costs more than no number — it directs the work. The user saw holes on screen while
the gate reported zero, twice.

**How to apply:** give every metric a case whose answer is known independently and assert it FIRST
— a converged stationary world must read ~0 holes; a counter must be shown to be written. Prefer
oracles that cannot drift (two implementations, the same input twice, an exact identity). When a
number does not match what is on screen, suspect the instrument before the subject. See
[[port-verbatim-dont-rederive]].
