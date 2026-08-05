---
name: verification-representatives-protocol
description: "How to build e2e verification gates in the miniheightfields testbed — real system vs scripting-constructed representatives / analytical primitives, then human-eye PNG review"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 647f1e5f-9794-4eec-9f71-127b52c6d1e9
---

For complex milestone verification AND durable regression e2e tests: stand up the **actual minimal setup of our actual system** (real controller/VT/render path, not stubs, not a reimplemented sim loop), drive it against a **scripting-constructed representative** or an **analytical primitive**, capture the e2e render, and compute SSIM (complex) / exact-pixel (analytical) against the representative. On match, present final `.png` images for the user's eye to review — the eye is terminal acceptance, the SSIM/exact gate is the precondition that earns it.

Representatives: hand-authored mesh via manual mesh scripting that exactly represents the instanced quadtree terrain the system draws (SSIM the e2e render vs it); a known CC0 image / UV-quad / checkerboard encoded through the real VT and rendered via the e2e `SAMPLE_VT` minimap shader.

**Why:** "not fake little reproducible cases" — toy repro cases validate an authored implementation against its own specifics and rot. Representatives derived independently (manual scripting, analytical math, external CC0 asset) are a genuine ground truth, so the gate bites and stays as a durable regression foundation.

**How to apply:** every milestone validation dispatch builds its gate this way. Representative-construction scripts + golden assets commit with the work; these tests are kept as the invariant-shaped battery, not retired. Overrides the default gate-tiering caution (acceptance-retires) for this project — the user explicitly wants these durable. See [[mhf-phase1-orchestration]].
