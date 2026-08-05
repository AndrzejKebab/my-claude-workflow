---
name: extract_research.py --only clobbers index.md
description: tools/extract_research.py with --only=<slug> rewrites docs/research/index.md containing only the filtered entry, losing all other rows.
type: feedback
originSessionId: 7e96d880-c43f-4116-9110-de068fded0cd
---
When running `tools/.venv/bin/python3 tools/extract_research.py --only=<slug>`, the `write_index(results)` call at the end only sees the filtered sources and overwrites `docs/research/index.md` with just that one row, erasing every other entry.

**Why:** `extract_research.py` uses `continue` inside the `only_slugs` check before appending to `results`, so `write_index` receives a truncated list. The script was written for bulk extraction, not partial runs.

**How to apply:** After any `--only=` or `--force` partial run, restore the index from git (`git show HEAD:docs/research/index.md > docs/research/index.md`) and manually add the new row, or patch the script to merge with existing rows before writing. Also prefer rendering composite per-page slides via `page.get_pixmap()` over keeping the hundreds of `p###-fig##.png` embedded-image fragments PyMuPDF extracts — the composite renders are what readers actually want.
