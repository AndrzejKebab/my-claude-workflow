# OKF-adapted frontmatter schema for the PAPERS corpus

This document defines the YAML frontmatter schema for the research corpus at `/mnt/archive4/PAPERS/Prepared/` and `/mnt/archive4/PAPERS/Articles/`. The schema follows the Open Knowledge Format (OKF v0.1): each file is a markdown document with a YAML frontmatter block, the only hard requirement is a non-empty `type`, and consumers tolerate unknown keys. The corpus was already close to this shape; this schema closes the gap and fixes one semantic mismatch — the old `type` field held the source medium (`pdf`, `youtube`) rather than the OKF concept-kind.

This is the canonical schema for two consumers: the back-fill pass that normalizes the existing files, and the `/research` skill that emits frontmatter for newly extracted documents. Both must agree, so both read this file.

## Fields

The block is ordered as listed below; absent fields are omitted rather than emitted empty.

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | OKF concept-kind — what kind of knowledge this is. One of the controlled vocabulary below. |
| `title` | yes | Human-readable title, taken from the document's `# H1`. |
| `description` | recommended | One sentence stating what the document covers. |
| `medium` | recommended | Source format the document was extracted from. Holds the value the old `type` field used to carry. |
| `source` | recommended | Origin of the document — a local path for extracted papers, a URL for web articles. Keep whatever key already encodes this (`source` or `source_url`); do not rename an existing `source_url`. |
| `author` | optional | Author(s), where known. Keep existing values; do not invent. |
| `year` | optional | Publication year, where known. |
| `pages` | optional | Page or slide count. Prepared-only; keep existing. |
| `slide_deck` | optional | Boolean. Prepared-only; keep existing. |
| `duration` | optional | Runtime for video sources. Keep existing. |
| `slug` | yes | Citation ID, equal to the filename without `.md`. Already present everywhere; never change it. |
| `tags` | recommended | YAML list of cross-cutting topics drawn from the controlled vocabulary in `OKF-TAXONOMY.md`. This is the link substrate: topic pages are built from these tags. |

`extracted` (an existing Prepared key recording the extraction date) is kept as-is when present. Do not fabricate it where absent, and do not "correct" existing values — the back-fill pass has no way to know the true date.

## `type` — controlled vocabulary (concept-kind)

Pick the single best fit. OKF tolerates values outside this list, but staying inside it keeps the corpus filterable.

- `Research Paper` — academic / industry papers (the bulk of Prepared).
- `Conference Talk` — SIGGRAPH / GDC / Eurographics talks, whether the source is a slide deck (`slides-pdf`, `slides-pptx`, `pptx`) or a recorded talk video.
- `Course Notes` — course chapters and lecture notes (e.g. a SIGGRAPH "Advances in Real-Time Rendering" course chapter).
- `Thesis` — theses and dissertations.
- `Book Chapter` — chapters from books (e.g. GPU Gems).
- `Technical Article` — web articles, blog posts, and devlogs (the bulk of Articles).
- `Documentation` — vendor / engine reference docs (e.g. Unreal Engine documentation pages).
- `Code Repository` — extracted source repositories (the `repo-*` Articles).
- `Video Tutorial` — instructional videos that are not conference talks (coding-challenge / walkthrough videos).
- `Bibliography` — curated reading lists and bibliographies that point at other works rather than presenting one.

## `medium` — source-format vocabulary

`medium` carries the value the old `type` field used. For files that already had a `type`, copy it verbatim into `medium` (including compound values such as `pdf+video` or `pptx+youtube`). For files that never had one (most Articles), infer it: `html` for web articles, `github` for repositories, `pdf` when a sibling `.pdf` exists, `youtube`/`video` for video sources.

Observed values: `pdf`, `slides-pdf`, `pptx`, `slides-pptx`, `youtube`, `video`, `html`, `github`, `local`, `source-analysis`, and compounds joined with `+`.

## Mapping rules — existing files

The change is additive plus one rename. Preserve every existing key not listed for change.

- **Prepared files** (all already have frontmatter: `source`, `type`, `pages`, `slide_deck`, `extracted`, `slug`):
  - Rename `type` → `medium` (value unchanged).
  - Add `type` = concept-kind, inferred from `medium`, `slide_deck`, and the title.
  - Add `title` from the `# H1`.
  - Add `description` — one sentence, drawn from the `## Summary` section or the first body paragraph.
  - Add `tags` from the taxonomy.
  - Keep `source`, `pages`, `slide_deck`, `extracted`, `slug` unchanged.
- **Articles files with frontmatter** (`title`, `author`, `source_url`, `year`, `slug`, sometimes `language`):
  - Add `type`, `description`, `medium`, `tags`.
  - Keep `title`, `author`, `source_url`, `year`, `language`, `slug` unchanged.
- **Articles files without frontmatter** (the `papers-i-like-*`, `view-frustum-culling`, `frustum-culling-*`, `negative-space-in-programming`, `practical-dynamic-visibility-for-games` files — they open with a `# H1` and a source line):
  - Prepend a full frontmatter block: `type`, `title` (from H1), `description`, `medium`, `source` (the URL from the source line), `author`/`year` if stated, `slug` (the filename stem), `tags`.

## Link convention

OKF treats every markdown link as a directed edge of an untyped relationship. The link layer for this corpus is built from `tags`, not from hand-authored cross-references in document bodies: a topic page per tag (`<bundle>/topics/<tag>.md`) links every member document. Body-level cross-references between papers are out of scope for this pass.

## Edit-safety rules (back-fill pass)

The corpus is not git-tracked, so edits are surgical and reversible by intent:

- Modify only the YAML frontmatter block — the text between the first `---` and the second `---`. Never edit a single character below the second `---`.
- For a file that already has frontmatter, replace the whole block in one edit.
- For a file without frontmatter, prepend the new block above the existing first line; leave the body untouched.
- Read only the head of each file (roughly the first 90 lines) — enough for the existing frontmatter, the `# H1`, and the start of the summary. Do not read whole bodies; many files are thousands of lines.

## Out of scope (do not edit)

- `index.md` and any `index_*.md` (the curated index and the `index_missing` / `index_unfindable` / `index_extracted_pending-*` bookkeeping files). The main index is refreshed separately; the bookkeeping variants are left alone.
- `assets/`, raw sources (`.pdf`, `.pptx`, `.html`, `.mp4`, `.srt`, `.h`), per-source subdirectories, and any `.backup-*` directory.

## Going-forward (the `/research` skill)

New extractions must emit this schema. The two frontmatter-emission sites are `tools/extract_research.py` (`write_markdown`, the PDF/PPTX path) and `tools/research_video.py` (the YouTube/video path). The script emits `type` (a best-effort default — `Conference Talk` for slide decks, `Research Paper` otherwise), `title`, `medium` (the old `type` value), `source`, the format-specific keys, a real `extracted` date (not a hardcoded constant), and `slug`. The refiner pass — which already reads the document end to end — fills `description` and `tags` and corrects `type` when the heuristic default is wrong.
