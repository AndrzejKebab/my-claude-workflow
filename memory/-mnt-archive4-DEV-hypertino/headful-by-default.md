---
name: headful-by-default
description: Run browser gates headful by default on this machine; headless only for CI and unproven configs
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e5a23195-b623-44b8-ab47-8a5be77843ae
---

User directive (2026-07-03): "run everything true headful, you have no problems running it true headful always. do not default to headless, especially if you have problems. headless only for ci and unproven."

**Why:** dev machine has a real display + real GPU (NVIDIA RTX 5080). Headless Chrome falls back to SwiftShader software GL — pathologically slow, masks real behavior (also skips code paths like WebGPU present). Recorded in hypertino AGENTS.md as repo law.

**How to apply:** local gates/verification run browsers headful. Headless is reserved for CI runners and configs not yet proven headful. When a headless run misbehaves, switch to headful first — don't debug the headless environment. Related: [[representative-e2e-not-manual-qa]].
