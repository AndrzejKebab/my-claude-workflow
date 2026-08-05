---
name: visual confirmation required for render/shader fixes
description: Never treat visual fixes as done without user visual confirmation; compilation alone is not proof
type: feedback
originSessionId: dde37fbc-e42d-43b8-bc24-0871f1611018
---
Never mark a visual fix (shader, rendering, UI, post-processing) as done before receiving visual confirmation from the user. This applies to ANY change where correctness is visible on screen — shader output, debug views, compositing, projection, color, alpha, overlay rendering.

**Why:** Multiple debug view fixes were marked "done" after compilation alone, but the user confirmed they still don't work. Compilation proves syntax, not behavior. Shader data flow bugs (missing uniforms, texture binding failures, branch logic errors) are invisible to the compiler.

**How to apply:** After any shader/render change: (1) compile, (2) explicitly ask the user to verify visually before treating as fixed, (3) do NOT mark task complete or move on until visual confirmation is received. If the user can't verify immediately, leave the task in_progress and wait.

**Exception:** Explicit integration/E2E tests that provide automated visual verification (render comparison tests, screenshot diff tests).
