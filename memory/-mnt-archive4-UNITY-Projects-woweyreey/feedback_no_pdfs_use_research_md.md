---
name: Use docs/research markdown, not PDFs
description: All research is extracted to markdown under docs/research/ — never read original PDFs
type: feedback
originSessionId: 18453239-4b64-4a12-ac7d-fa95ffc07a9c
---
Do not use `Read` on PDFs in `~/Downloads/` or anywhere else for research context. The project has already OCR-extracted every research source into `docs/research/*.md`.

**Why:** User stopped me mid-task when I read the Nubis Cubed PDF directly for slide context. The extracted markdown is the canonical project reference — reading PDFs risks (a) duplicating content the project has already curated, (b) pulling in context the project intentionally excluded during extraction, (c) undermining the research-anchoring convention.

**How to apply:** When a research citation is needed, go straight to `/mnt/archive4/UNITY/Projects/woweyreey/docs/research/<slug>.md`. The `index.md` in that folder lists all sources. If the markdown doesn't contain what you need (image-only slides), ask the user — don't fall back to the PDF.
