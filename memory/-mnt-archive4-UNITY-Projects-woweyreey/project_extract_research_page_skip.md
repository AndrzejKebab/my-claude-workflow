---
name: extract_research.py page-render skip heuristic
description: paper-mode page renders are gated by _page_has_figure (≥1 image OR ≥12 vector drawings); pure-prose pages skip rendering by design but text is preserved in marker.md
type: project
originSessionId: a91f9ef3-255a-40d8-831d-c930ede6a80f
---
`extract_research.py:703` `_page_has_figure(page)` skips rendering paper-PDF pages that have **zero embedded images AND fewer than 12 vector drawing operations**. This is by design — vision pass on a 200-page thesis should not produce 200 page renders. Pure-prose pages typically have 5-10 drawings (paragraph underlines, page chrome, occasional bullets) which falls below the threshold.

Concrete: lefebvre-hoppe-2006-perfect-spatial-hashing.pdf has 10 pages; renders skip pages 2 (9 drawings), 5 (7 drawings), 10 (7 drawings). Body text from those pages IS in `marker.md` between the corresponding `{N}---` page boundaries — only the per-page raster (`pNNN-page.png`) is absent, so vision pass has no image to look at.

**Why:** trade-off documented at `extract_research.py:706-720` — small over-render is cheap, missing a figure costs a vision-pass blind spot. Heuristic intentionally errs toward inclusion.

**How to apply:** if a "missing" page render concerns you, check the drawings count first — if it's a pure-prose page, no action needed (text-layer extraction in marker.md is the canonical body for those pages). For an equation-dense prose page where you want vision to confirm marker fidelity, the workaround is a per-source override in `SOURCES` lowering the threshold, or a `--render-all-pages` flag (not yet implemented, would be a one-line patch to the triage call).
