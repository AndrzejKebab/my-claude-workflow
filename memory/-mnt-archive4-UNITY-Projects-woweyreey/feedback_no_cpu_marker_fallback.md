---
name: feedback-no-cpu-marker-fallback
description: "Never force CPU marker extraction with CUDA_VISIBLE_DEVICES=\"\" — accept the PyMuPDF fall-through instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c432bf6d-5efa-40a0-94c3-6539035f2fb8
---

When `research-extractor` reports CUDA OOM on marker extraction, **do not** retry with `CUDA_VISIBLE_DEVICES=""` to force CPU mode. Accept the legacy PyMuPDF span-walker fall-through as the final state.

**Why:** CPU marker inference on a multi-page paper can take literal hours (Nishita 1993 took 2.5 minutes on CPU at 9 pages; a 40-page thesis or 33 MB figure-dense paper extrapolates to multiple hours). The user explicitly prefers the fast, degraded output over a slow, clean one — the vision pass can recover degraded body text from the rendered page images, and the refiner reconstructs equations from there.

**How to apply:**
- In `research-extractor` briefs, DO NOT include "if you hit OOM, set CUDA_VISIBLE_DEVICES='' and retry". That instruction was active during the 2026-05-14 sky-LUT batch and produced the wrong behaviour on Nishita 1993.
- When an extractor reports PyMuPDF fall-through, accept it as final. Flag the degradation in the orchestrator-level summary for the user, and rely on the vision pass + refiner to reconstruct equations from page renders.
- Skill canon (`~/.claude/skills/research/SKILL.md`) does mention a 2 GiB free-VRAM CPU guard, but it's known to not always engage — that's a toolchain bug, not a workaround target. The right answer is just to accept the fall-through.

Related: [[feedback-no-force-extract-research]] (different concern — avoid clobbering refined output) and [[feedback-research-index-clobber]].
