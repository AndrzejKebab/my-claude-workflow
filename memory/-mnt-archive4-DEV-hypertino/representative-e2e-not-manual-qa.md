---
name: representative-e2e-not-manual-qa
description: "verify rendering/web work with an automated e2e that exercises the REAL shipped artifact; don't offload verification to the user by handing run commands"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8e855018-86eb-4b88-9a40-bee5d862e61c
---

User instruction (verbatim): "use e2e tests for this, dont ask me to run it." The gate must exercise the REAL shipped artifact — a real browser for web, the real GPU for native render — representative enough to catch the actual failure mode. A green build or a proxy harness is not proof.

**Why:** twice a passing gate shipped a visible break the user caught by eyeballing. (1) The `png_content.py` variance gate passed while the Noesis panel rendered BEHIND scene geometry — variance ≠ "UI on top". (2) An ANGLE-headless "in-browser" web gate reported 0 console errors while the real `just web` page aborted at WebGL2-context creation in the user's actual browser. The user should not be the one discovering regressions.

**How to apply:** for rendering/web work, build or strengthen an automated e2e that loads the REAL served artifact in a real browser / runs on the real GPU, captures the real console, and FAILS on the concrete failure mode (prove it bites: fail pre-fix → pass post-fix, non-vacuous). Do not hand the user a `just …` command as the verification step. Eyeballing is a bonus, never the gate. Related: [[reverse-z-clip-convention]] — a bug class these gates must catch.

**Run it HEADFUL, in the environment matching the user's.** A web fix regressed twice partly because it was tested headless with WebGPU absent (SwiftShader / `--disable-gpu` / forced `--use-gl`). Degradation/fallback bugs (WebGPU→WebGL2 boot, backend selection) only appear where the PRIMARY backend exists — so a WebGPU-capable real browser is required to reproduce a WebGPU/WebGL2 clash; headless-software masks it and reports false green. Match the user's real config (their GPU class, WebGPU available), and the user said plainly: "run the tests headful."
