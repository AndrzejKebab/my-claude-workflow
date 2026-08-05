---
name: research Pass 2.5 validation
description: Pass 2.5 of /research validates LaTeX (KaTeX) and Mermaid (mermaid.parse) syntax between vision and refine passes — marker is the upstream source of broken LaTeX it catches
type: project
originSessionId: a91f9ef3-255a-40d8-831d-c930ede6a80f
---
`/research` Pass 2.5 (`tools/validate_research.py` in the skill) extracts every `$…$` / `$$…$$` / ```` ```mermaid ```` block from `docs/research/<slug>.md`, parses each via KaTeX (`throwOnError: true`) and `mermaid.parse()` (jsdom), writes `assets/<slug>/findings-pass2.5-validate.md`, exits 1 on any parse error.

Runs **between Pass 2 (vision) and Pass 3 (refine)**, then re-runs after refine as a clean-room check before Pass 4 (index).

**Why:** marker's LLM-cleanup pass (Gemini `gemini-2.0-flash` for headings/tables/equations) is the upstream source of structurally-plausible-but-KaTeX-incompatible LaTeX — confirmed instances include misplaced `&` inside `\begin{split}` (lefebvre-hoppe-2006), undefined macros like `\ddy/\ddx` (mittring-2008-advanced-virtual-texture-topics:1036), and `(1 + cos a)` instead of `(1 + cos²a)` for the Rayleigh phase function. Refiner missed all three until validator surfaced them. Without Pass 2.5 these wrong-but-plausible equations metastasise into citations.

**How to apply:** orchestrator MUST cite the Pass-2.5 sidecar in the refiner brief; validator exit 1 hard-blocks Pass 3 (and Pass 4 on the post-refine re-validate). Tooling lives at `~/.claude/skills/research/tools/validate_{research.py,md.mjs}` + `render_md_html.mjs` (HTML preview), Node deps in `~/.claude/skills/research/package.json` (`npm install` in skill dir).
