---
name: extract_research.py --force destroys refined output
description: Never pass --force to extract_research.py without explicit authorization — it overwrites Pass-3-refined markdown in place with raw marker output, and there is no auto-backup
type: feedback
originSessionId: a91f9ef3-255a-40d8-831d-c930ede6a80f
---
`extract_research.py --force` overwrites the canonical `docs/research/<slug>.md` in place. The default (no --force) writes a `<slug>.regen-<YYYYMMDD-HHMMSS>-<6hex>.md` sidecar instead, preserving the existing refined doc — that is the safe path. **Never pass --force without explicit user authorization for that specific slug.**

**Why:** lost the Pass-3-refined `lefebvre-hoppe-2006-perfect-spatial-hashing.md` (317 clean LaTeX blocks, vision-pass content, refiner-fixed `\begin{split}`) by passing --force to test the new always-render policy. The refined doc was untracked in git and there was no backup — recovery cost a full vision + refine cycle. The script doesn't write a `.bak` before overwriting, so the regen sidecar (which only fires WITHOUT --force) is the only safety net.

**How to apply:** to validate extractor changes, either (1) work against a temp copy of the slug elsewhere, (2) check `git status` and confirm the file is uncommitted-but-pristine before --force, or (3) skip --force and inspect the resulting `.regen-*.md` sidecar instead. The default path is the safe one — let it work.
