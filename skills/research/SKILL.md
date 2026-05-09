---
name: research
description: Extract research content from YouTube presentations, PDFs, or PPTX files into structured markdown. Dispatches each pass to a dedicated sub-agent (research-extractor / research-vision / research-refiner / research-indexer) so per-deck vision passes scale to hundreds of slides without bloating the parent context.
---

Extract research material into `docs/research/` as annotated markdown with images, transcripts, and OCR. The orchestrator (you) is a thin coordinator: every load-bearing pass runs in a dedicated sub-agent's context window so the parent session stays small.

## Toolchain layout

The Python pipeline ships with the skill, including its own venv. Everything is self-contained at `~/.claude/skills/research/`:

```
~/.claude/skills/research/
├── SKILL.md              ← this file
├── pyproject.toml        ← uv-managed dependency spec
├── .venv/                ← skill-local venv (created by `uv sync`, gitignored)
└── tools/
    ├── README.md
    ├── extract_research.py
    ├── extract_research_phase2.py
    ├── cleanup_research.py
    ├── research_video.py
    ├── transcribe_to_srt.py
    ├── upgrade_to_slide_renders.py
    ├── redetect_scenes.py
    ├── subsample_long_scenes.py
    ├── srt_to_windows.py
    ├── audit_research_index.py
    └── prune_research_index.py
```

**Why a skill-local venv** (not the project's `tools/.venv/`): projects vary wildly in their Python requirements — some have no venv at all, some have one with conflicting versions (numpy pinned for ML, opencv with GUI flavour, …). The research pipeline needs specific versions of PyMuPDF, opencv-python-headless, faster-whisper, etc. Pinning those at the skill level decouples the toolchain from whatever the project happens to have lying around.

**uv as the package manager.** Dependencies are pinned in `pyproject.toml`; the venv is created/updated with `uv sync` from the skill directory. uv resolves and installs in seconds vs minutes for plain pip — important when the skill is dispatched from many projects.

### Setup (first run only)

```bash
cd ~/.claude/skills/research
uv sync                       # creates .venv, installs dependencies (~30 s cold)
```

Plus system dependencies (tracked in `tools/README.md`):

```bash
# Arch
sudo pacman -S libreoffice-fresh yt-dlp ffmpeg

# Debian / Ubuntu
sudo apt install libreoffice yt-dlp ffmpeg

# macOS
brew install --cask libreoffice
brew install yt-dlp ffmpeg
```

LibreOffice is needed for PPTX → PNG rendering. yt-dlp + ffmpeg are needed for the video pipeline. OCR is provided by [OpenOCR](https://github.com/Topdu/OpenOCR) (`openocr-python`), pinned in `pyproject.toml` — no system OCR engine is needed. OpenOCR auto-downloads ONNX detection + recognition models (~36 MB total) to `~/.cache/openocr/` on first use.

### Invocation

The agents invoke scripts using the skill venv directly:

```bash
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/<script>.py --only=<slug>
```

Or via `uv run` (which auto-syncs if `pyproject.toml` changed):

```bash
uv run --project ~/.claude/skills/research python ~/.claude/skills/research/tools/<script>.py --only=<slug>
```

Both forms work; the explicit-path form is faster because it skips the uv sync check.

### Per-document helpers

One-off helpers (e.g. `split_<slug>_notes.py` for a particular deck's PowerPoint Notes-Pages text-layer split) stay in `<project>/tools/`, never in the skill — they are project-specific and would clutter the shared skill.

### Legacy project copies

Projects that adopted /research before this restructuring (notably `woweyreey`) may have their own `<project>/tools/*.py` copies running against `<project>/tools/.venv/`. Those continue to work but are **legacy**: no further updates land there. Migration path for those projects: `cd ~/.claude/skills/research && uv sync`, then update any project-specific `tools/<script>.py` invocations to point at the skill copy.

## Architecture overview

You are the orchestrator for the /research skill. You do **not** read 268-slide PDFs or run the OCR pipeline yourself. Instead, you scope the work and dispatch it to specialised sub-agents:

| Pass | Agent | Purpose |
|---|---|---|
| 1 — extraction | `research-extractor` | Add the source to `tools/extract_research.py` SOURCES, run scripts, archive source to `/mnt/archive4/PAPERS/`, report slug + asset counts |
| 2 — vision | `research-vision` | Read slide / figure images and write `**Diagram (LLM vision pass):**` blocks via Edit. Batches well — dispatch one agent per ~30 slides to keep individual context lean |
| 3 — refine | `research-refiner` | Heading fixes, broken-Unicode equation re-transcription, speaker-notes typo cleanup, optional top-of-doc summary |
| 4 — index | `research-indexer` | Add table row + checklist entry to `docs/research/index.md`, drain the extractor's pending sidecar |

You may also dispatch additional vision-pass batches **between** Pass 2 and 3 (e.g. "vision-pass slides 100-130 of the same doc, focusing on plot panels") if the first pass missed coverage.

### Running inside a /delegate orchestrator

If your top-level invocation came from `/delegate` (the multi-agent orchestration mode that uses shared `docs/orchestrate/<topic>/` files), you are **doubly orchestrating**: /delegate dispatched you to handle the research portion, and you in turn dispatch the four research sub-agents. In that mode:

- The parent `/delegate` orchestrator owns `docs/orchestrate/<topic>/` and expects status reports there. Pass that directory path through to each sub-agent's brief so they append their findings to `docs/orchestrate/<topic>/<NN>-research-<pass>.md`.
- Do not re-do reuse-audit / architectural Q&A — `/delegate` already covered those. Treat your role as "the one that knows /research" within the larger plan.
- Your final message to the parent /delegate orchestrator is a one-screen summary; the file deliverables on disk are the load-bearing output.

If you are invoked directly (not via /delegate), skip the `docs/orchestrate/<topic>/` dance — the briefs talk to the four research agents directly, and your final message to the user summarises the work.

### When to skip dispatch

For a small extraction (single-page paper, < 5 slides, or "just rerun extraction on an existing source"), running the four-agent dance is wasteful. In that case:

- Pass 1 you can run inline (it's a script invocation).
- Pass 4 you can run inline (one Edit + one rm).
- **Pass 2 (vision) and Pass 3 (refine) still get dispatched**: they are the context-heavy passes and the agent boundary is what makes the skill scale.

## Diagram description policy (vision pass output)

Every diagram, plot, image-only table, photograph, or code listing the vision agent processes lands in the markdown as a **tagged block** immediately before the image reference. The tag is one of:

- `**Diagram (LLM vision pass):**` — schematic, flowchart, polar plot, geometry sketch.
- `**Plot (LLM vision pass):**` — quantitative-axis graph (density profile, error curve, …).
- `**Table (LLM vision pass):**` — image-only data table (transcribed as markdown table inline).
- `**Image (LLM vision pass):**` — photograph, screenshot, before/after.
- `**Code (LLM vision pass):**` — code shown as image (transcribed as fenced block with language tag).

**Why "(LLM vision pass)"** — the parenthetical attribution is **non-negotiable**. It does two things:

1. **Distinguishes the block from speaker-notes** (which are author-attributed transcription) and from slide-content text (which is text-layer extraction). Three sources of text in one document, three different reliability levels — the reader must be able to tell at a glance which is which.
2. **Marks the block as auditable for hallucination correction**. Vision-pass output is the lossy stage of the pipeline. When (not if) a future reader spots a wrong axis label or a fabricated number, the tag tells them this is the block to verify against the source image and correct. Without the tag, hallucinated numbers metastasise into citations.

The `research-vision` agent is required to use these tags. The `research-refiner` agent is allowed to flag suspicious blocks but **must not silently rewrite them** — flag for human review instead.

### Description discipline (enforced by the vision agent)

- Lead with structure (axes, conventions, plot type), then content (curve shape, key values), then conclusion (what the visual demonstrates).
- Be quantitative when the slide is, qualitative when the slide is.
- Flag uncertainty ("approximately N", "roughly", "appears to be") rather than fabricate precision.

### Skip rules

A slide is skipped (no vision block written) ONLY when:

- **Decorative**: title page, agenda, section divider, "Thanks!", "References", transition card.
- **Pure-text bullets**: no diagram, plot, photo, table, or code anywhere on the slide.
- **Already tagged**: a `**X (LLM vision pass):**` block already exists for that slide — re-tagging would duplicate.

Any slide with a real visual gets a per-slide block.

## REQUIRED: Citable Canonical Naming

Every extracted document MUST be renamed (and its asset directory MUST be renamed) to a **citable canonical slug** before pass 4. The Pass 1 script emits a slug derived from the source title (e.g. `intro-to-gpu-occlusion`) — this is **scaffolding only** and is never the final filename.

## REQUIRED: Citable Canonical Naming

Every extracted document MUST be renamed (and its asset directory MUST be renamed) to a **citable canonical slug** before pass 4. The Pass 1 script emits a slug derived from the source title (e.g. `intro-to-gpu-occlusion`) — this is **scaffolding only** and is never the final filename.

**Pattern:** `<author-surname(-coauthor)?>-<year>-<short-topic>.md`

- Author surname(s) lowercased, hyphen-separated. For 1 author: `brands`. For 2: `aaltonen-haar`. For 3+: first author only or first-last (match adjacent corpus precedent).
- Year is the publication / talk year (4 digits).
- Short topic: 1–4 hyphenated words capturing the load-bearing technical contribution, not the marketing title. Strip "intro to", "advances in", "real-time", "an efficient", etc. — they appear in every paper and add zero discriminating power.
- All lowercase, hyphen-separated, no underscores, no caps, no punctuation.

**Examples** (from the existing corpus):

| Source title | Canonical slug |
|---|---|
| "Intro to GPU Occlusion" (Leon Brands, GPC 2024) | `brands-2024-gpu-occlusion` |
| "GPU-Driven Rendering Pipelines" (Haar & Aaltonen, SIGGRAPH 2015) | `aaltonen-haar-2015-gpu-driven` |
| "Improved Culling for Tiled and Clustered Rendering" (Drobot, SIGGRAPH 2017) | `drobot-2017-improved-culling` |
| "Real-Time, All-Frequency Shadows in Dynamic Scenes" (Annen et al., TOG 2008) | `annen-2008-all-frequency-shadows` |
| "Adaptive Shadow Maps" (Fernando et al., SIGGRAPH 2001) | `fernando-2001-adaptive-shadow-maps` |
| "Sparse Virtual Textures" (Sean Barrett, GDC 2008) | `barrett-2008-sparse-virtual-textures` |
| "Creating the Atmospheric World of Red Dead Redemption 2" (Bauer, SIGGRAPH 2019) | `bauer-2019-rdr2-atmospherics` |

**Why this matters:** the corpus is cross-referenced from `docs/`, memory files, and other research notes by slug. Title-derived slugs (`intro-to-gpu-occlusion`, `volumetric-fog-in-enshrouded`) are not citation-stable — two unrelated talks could share a generic title — and they break the corpus convention. Anything filed under a non-canonical slug must be renamed before commit; deferring this creates dangling references.

**Required actions before pass 4:**

1. Pick the canonical slug per the rules above (cross-check `docs/research/index.md` for adjacent precedent if unsure — match the surrounding pattern).
2. `mv docs/research/<scaffolding>.md docs/research/<canonical>.md`
3. `mv docs/research/assets/<scaffolding>/ docs/research/assets/<canonical>/`
4. Update inside the markdown: `slug:` frontmatter field, every `assets/<scaffolding>/` image path.
5. Pass 4 (index update) uses the canonical slug from this point forward.

If the source genuinely has no clear single author (e.g. an Epic UE documentation page, a vendor whitepaper), use the publishing organisation in lowercase as the "author": `epic-2022-ue51-virtual-shadow-maps-docs`, `khronos-2023-...`. Match adjacent corpus precedent.

## REQUIRED: Source Archive in `/mnt/archive4/PAPERS/`

Every research source — PDF, PPTX, YouTube video, HLS / m3u8 stream, local mp4 — **MUST** be preserved at its canonical name in `/mnt/archive4/PAPERS/`. This is the long-term archive of every primary document the project depends on. The markdown extracts in `docs/research/*.md` are derived artefacts; **PAPERS/ is the source of truth**.

**Layout:**

| Source type | Where it lives in PAPERS/ |
|---|---|
| PDF | `/mnt/archive4/PAPERS/<canonical-slug>.pdf` |
| PPTX | `/mnt/archive4/PAPERS/<canonical-slug>.pptx` |
| YouTube video | `/mnt/archive4/PAPERS/<year>-<slug-tail>/<canonical-slug>.mp4` + `<canonical-slug>.en.srt` |
| HLS / m3u8 stream | same folder layout as YouTube |
| Local mp4/mkv/webm + SRT | same folder layout as YouTube |

The canonical slug is the same one used for `docs/research/<slug>.md` (see "REQUIRED: Citable Canonical Naming" above). The video-folder prefix `<year>-<slug-tail>` is just the canonical slug rotated so the year sorts first — e.g. canonical `feller-2024-volumetric-fog-enshrouded` → folder `2024-feller-volumetric-fog-enshrouded/`.

**Examples:**

```
/mnt/archive4/PAPERS/
├── annen-2008-all-frequency-shadows.pdf
├── hillaire-2020-sky-atmosphere.pdf
├── bauer-2019-rdr2-atmospherics.pptx
├── wright-2021-radiance-caching-lumen.pptx
├── 2024-feller-volumetric-fog-enshrouded/
│   ├── feller-2024-volumetric-fog-enshrouded.mp4
│   └── feller-2024-volumetric-fog-enshrouded.en.srt
└── 2024-dekeersmaecker-numerical-precision-large-worlds/
    ├── dekeersmaecker-2024-numerical-precision-large-worlds.mp4
    └── dekeersmaecker-2024-numerical-precision-large-worlds.en.srt
```

**When to copy:** After Pass 1 (automated extraction) finishes and the canonical slug is decided, copy the source(s) into PAPERS/ **before Pass 4** (index update). Copy must use the canonical slug, never the scaffolding slug emitted by Pass 1.

For PDFs / PPTXs:
```bash
cp "<source-path>" "/mnt/archive4/PAPERS/<slug>.<ext>"
```

For YouTube / HLS / local videos (yt-dlp + research_video.py write into `/tmp/research-<random>/<scaffolding>.{mp4,en.srt}`):
```bash
mkdir -p "/mnt/archive4/PAPERS/<year>-<slug-tail>/"
cp "/tmp/research-XXXX/<scaffolding>.mp4"    "/mnt/archive4/PAPERS/<year>-<slug-tail>/<slug>.mp4"
cp "/tmp/research-XXXX/<scaffolding>.en.srt" "/mnt/archive4/PAPERS/<year>-<slug-tail>/<slug>.en.srt"
```

**Why this matters:**
- `tempfile.mkdtemp(prefix="research-")` does not auto-clean, but `/tmp` is wiped on reboot, and the videos are typically 100 MB+. Without the explicit copy, every `/research` rerun re-downloads from the network.
- A canonical-slugged file in PAPERS/ is the citation target for everything else (memory, design docs, sub-agents). Title-derived scaffolding names break those references.
- Pass 2 vision and Pass 3 refine can re-read the source from PAPERS/ on subsequent runs without re-extraction.

**Skip criteria:** none. Even small or "obvious" sources get archived — the point of the archive is that it's complete. The only exception is a source that is genuinely already at its canonical path in PAPERS/ (cp into the same path is a no-op, but check the size — if the existing copy is smaller / corrupt, replace it).

## Arguments

The argument is a URL or file path:

- YouTube URL → download video, detect slides, OCR + transcribe, output markdown
- HLS stream (m3u8 URL) → download via ffmpeg, transcribe with faster-whisper, then video pipeline
- `.pdf` path → extract text via PyMuPDF + per-page rendering (slide deck) **or** per-figure cutouts (paper)
- `.pptx` path → render every slide via LibreOffice → PDF → PNG, plus python-pptx text + speaker notes
- `.mp4`/`.mkv`/`.webm` local path → video pipeline with `--title` and `--slug` flags

## REQUIRED: Slide-deck vs Paper image policy

Every PDF/PPTX is classified once at extraction time as **slide deck** or **paper**, and the image-extraction strategy follows:

| Class | Image strategy | Asset filename pattern |
|---|---|---|
| **Slide deck** (PPTX, or PDF exported from PowerPoint / Keynote / Google Slides / Beamer / Impress, or any landscape PDF with standard 4:3 / 16:10 / 16:9 aspect ratio across all pages) | One **rendered slide image per page** at 2× scale via PyMuPDF `get_pixmap`. **Never** extract embedded image objects — slide-deck PDFs decompose visuals into many small embedded image blobs (chart chrome split from plot, photo split from frame, decorative banner separated from photo) that lose meaning when separated. The vision pass reads the rendered slide — that's the whole slide as the audience saw it. | `assets/<slug>/sNNN-slide.png` |
| **Paper** (academic paper, technical report, portrait-orientation PDF without slide-export metadata) | Extract embedded image objects as **figures** — these are real per-figure assets (Fig. 1, Fig. 2, …) embedded by the author. | `assets/<slug>/pNNN-figXX.png` |

**Detection** (in `tools/extract_research.py`):

- PPTX → always `is_slide_deck = True`. Rendered via `soffice --headless --convert-to pdf`, then PyMuPDF rasterises each page.
- PDF → `is_slide_deck_pdf(doc)` triggers True if **any** of:
  - Metadata `creator` / `producer` / `title` / `subject` mentions PowerPoint / Keynote / Google Slides / Beamer / Impress / "presentation".
  - **All** pages are landscape AND aspect ratio is in `[1.25, 1.85]` (4:3 ≈ 1.33, 16:10 ≈ 1.6, 16:9 ≈ 1.78), AND page count ≥ 3.
- Override per-source: set `"slide_deck": True/False` in the SOURCES entry to force a particular mode (e.g. for a portrait-orientation slide deck export, or a landscape figure-heavy paper).

**Why this matters**: when `extract_research.py` mistakenly enters paper-mode on a slide deck, the cutout images are useless fragments and the vision pass — which reads those cutouts — fails to recover the slide content. Going straight to per-page rendering for slide decks removes the failure mode entirely.

### PPTX rendering dependency: LibreOffice

PPTX → slide image rendering requires **LibreOffice headless** (`soffice` / `libreoffice` on PATH).

```bash
# Arch
sudo pacman -S libreoffice-fresh

# Debian / Ubuntu
sudo apt install libreoffice

# macOS
brew install --cask libreoffice
```

The script auto-detects `soffice` / `libreoffice` via `shutil.which` and falls back to common install paths (`/usr/bin/soffice`, `/Applications/LibreOffice.app/Contents/MacOS/soffice`). If LibreOffice is missing, `extract_research.py` raises a clear error pointing back to this section.

PPTX conversion takes ~30-60s per deck (LibreOffice cold-start + PDF export). Subsequent runs hit the same temp PDF if the script's `tempfile.mkdtemp` happens to land on an existing directory; in practice expect ~1 minute per deck on first run.

You may see `MuPDF error: format error: No common ancestor in structure tree` warnings during PPTX rendering — these are non-fatal, MuPDF complaining about LibreOffice's PDF tagging structure. The rendered images are still correct.

## Full Pipeline (4 passes — orchestrator dispatches each)

### Pass 1: Extraction (dispatched to research-extractor, or run inline for trivial sources)

For PDFs / PPTXs and recorded-talk videos, dispatch a `research-extractor` agent with a brief naming the source path / URL and the canonical slug. The agent adds the source to `tools/extract_research.py` SOURCES, runs the extraction script(s), runs phase2 OCR + cleanup, archives the source to `/mnt/archive4/PAPERS/`, and reports back.

For trivial cases (single-page paper, source already in SOURCES, just need to rerun under `--force`), the orchestrator may run inline:

Determine input type and run the appropriate script:

**YouTube URL:**
```bash
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/research_video.py "URL"
```

**HLS stream (m3u8 URL, e.g. GDC Vault):**

Step 1 — verify and pick quality from the master playlist:
```bash
curl -s "MASTER_M3U8_URL" -H 'Origin: ...' -H 'Referer: ...'
# Lists quality sub-playlists; pick the highest resolution index_1.m3u8
```

Step 2 — download with ffmpeg (use the quality-specific sub-m3u8, not the master):
```bash
mkdir -p /tmp/research-SLUG
ffmpeg -y \
  -headers $'User-Agent: Mozilla/5.0...\r\nOrigin: https://...\r\nReferer: https://...\r\n' \
  -i 'QUALITY_SUB_M3U8_URL' \
  -c copy /tmp/research-SLUG/SLUG.mp4
```

Step 3 — transcribe with faster-whisper (CUDA). If no auto-captions are available (non-YouTube source), generate SRT from audio using the tracked helper `tools/transcribe_to_srt.py`:
```bash
# Requires libcublas on PATH — set LD_LIBRARY_PATH for this machine:
LD_LIBRARY_PATH=/usr/local/lib/ollama/cuda_v12:$LD_LIBRARY_PATH \
  ~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/transcribe_to_srt.py \
  /tmp/research-SLUG/SLUG.mp4 \
  /tmp/research-SLUG/SLUG.en.srt \
  medium
```

`tools/transcribe_to_srt.py` is the canonical tracked version of the old inline `/tmp/transcribe_to_srt.py` snippet — **do not recreate it inline**. If you need to extend it (different language, larger model, word-level timestamps), edit the tracked file in `tools/` and commit the change so the next /research run benefits.

Step 4 — run video pipeline on local file:
```bash
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/research_video.py \
  /tmp/research-SLUG/SLUG.mp4 \
  "--title=Full Talk Title (Event Year)" \
  "--slug=my-slug"
```

The script finds the SRT automatically next to the mp4 file (same stem, `.en.srt` suffix).

**PDF/PPTX file:** Add to `SOURCES` in `tools/extract_research.py`, then:
```bash
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/extract_research.py --only=SLUG
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/extract_research_phase2.py --only=SLUG
```
Also add to `SOURCES_BY_SLUG` in `tools/extract_research_phase2.py` for the `--only` filter to work.

**Cleanup (all types):**
```bash
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/cleanup_research.py --only=SLUG
```

This produces a rough markdown with native-text-extracted body, screenshots, and transcript text. **OCR's role in this skill is narrow**: when a page has no native text layer (scanned PDFs, image-only slide exports, PPTX slides whose content is rasterised), phase 1 OCRs the page's image asset and uses the result as the page body — same role native PyMuPDF text extraction plays for PDFs that have a text layer. There is no separate "OCR pass". OCR is just one of two body-text sources phase 1 selects between, gated on whether `len(native_text) < 20`. This is the **only** path on which OCR enters the canonical document body.

**OCR is never applied to image inclusions inside an otherwise-text-rich doc.** Image inclusions are read by the vision pass with full visual context — modern multi-modal LLMs vastly outclass any CPU OCR engine at structured figure description, and an OCR scaffolding block alongside an image only narrows what the vision agent looks at and primes it with mistakes. Phase 2 has no per-image OCR — it only handles PPTX video transcription.

Phase 1's OCR fallback fires for:
- **Scanned PDFs** (Adobe Acrobat / scanner-software output, no text layer): each page is one big embedded image; phase 1 OCRs the image and uses the result as page body.
- **Slide-deck PDFs / PPTXs whose slides are rasterised** (presentation exported as flattened images): the per-page render goes through OCR; vision pass still describes the rendered slide.
- **Video frame OCR** for recorded talks (handled by `research_video.py`, not phase 2): captions cover speaker audio but miss slide content shown only visually, so OCR on each detected scene's representative frame supplies the missing slide text.

`extract_research.py` no longer emits any `OCR-PENDING` markers — the OCR fallback runs inline during phase 1 and the result lands directly in the page body.

### Pass 1.5: Re-detect under-found scenes (when needed)

`research_video.py` uses a 0.35 Bhattacharyya histogram threshold tuned for typical recorded-talk video. For slide-heavy talks where consecutive slides share a template (same chrome, only text changes), it under-detects badly — e.g. a 40-min, 64-slide deck can collapse to 5–7 detected scenes. **Symptom**: pass 1 finishes with a number of `frame-XXXX-NNNN.jpg` files much smaller than the slide count visible in the deck.

When this happens, use the tracked helpers (do **not** re-create them inline in `/tmp`):

```bash
# Cut down to ~60 scenes (or whatever the deck has) at threshold 0.18
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/redetect_scenes.py \
    /tmp/research-SLUG/SLUG.mp4 SLUG \
    --threshold 0.18 --interval 1.0

# For any scene that's still > 40s, sample additional frames every 20s
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/subsample_long_scenes.py \
    /tmp/research-SLUG/SLUG.mp4 SLUG \
    --interval 20 --min-len 40

# After identifying real slide-start timestamps via vision, group the SRT
# into per-slide windows (one paragraph per slide):
~/.claude/skills/research/.venv/bin/python ~/.claude/skills/research/tools/srt_to_windows.py \
    /tmp/research-SLUG/SLUG.en.srt /tmp/slide_starts.txt \
    --out /tmp/windowed_transcript.txt
```

These helpers are non-destructive — they only write new `scene-NNN-*.jpg` / `sub-NNN-MM-*.jpg` files into the asset dir and a TSV in `/tmp`. To clear stale scene files from a prior run with different parameters, delete them explicitly first; the helpers intentionally do not.

If you find yourself wanting yet-another redetection knob (different colourspace, edge-detection instead of histogram, etc.), edit `tools/redetect_scenes.py` and commit the change — never spawn a one-off `/tmp/*.py` for it.

### Pass 2: Vision (dispatched to research-vision)

**This is the expensive, context-heavy pass.** It MUST be dispatched to the `research-vision` sub-agent — never run inline. A 268-slide deck would burn the orchestrator's context window in vision-pass alone; the agent boundary is what makes the pass scale.

#### Dispatch pattern

The orchestrator decides which slides need vision treatment, then dispatches one `research-vision` agent per batch of ~20-40 slides. For very large decks, dispatch multiple batches **sequentially** (not in parallel — they all Edit the same file). For papers (per-figure cutouts) where each figure is independent, batches can run in parallel.

For each batch, the brief MUST contain:

1. The canonical slug (e.g. `suzuki-yasutomi-2023-gt7-sky-dome`).
2. The exact list of slide / page numbers to process (e.g. "slides 30, 32-46, 50-55, 65, 78-80, 88, 90, 94").
3. Already-tagged slides to skip (slides that already have a `**X (LLM vision pass):**` block from a prior batch — re-tagging would duplicate).
4. Path to `tools/.venv/bin/python3` if the agent might need to render extra crops (paper-mode multi-figure pages).

The agent is responsible for the format — `**Diagram (LLM vision pass):**` / `**Plot (LLM vision pass):**` / `**Image (LLM vision pass):**` / `**Table (LLM vision pass):**` / `**Code (LLM vision pass):**`. See agent definition `~/.claude/agents/research-vision.md` and the "Diagram description policy" section earlier in this skill.

#### Inputs the orchestrator prepares

- **Image targets**: slide decks → one `pNNN-slide.png` (PDF) or `sNNN-slide.png` (PPTX) per page; papers → multiple `pNNN-figXX.png` per page; videos → `frame-XXXX-NNNN.jpg` scenes.
- **No OCR scaffolding adjacent to images**: previous versions of this skill dropped per-image OCR blocks under each figure reference. That has been removed — OCR labels without visual context only narrow what the vision agent looks at and prime it with mistakes. The vision agent reads each image directly with full visual context and writes its description from scratch.
- **Transcript** (YouTube / HLS / PPTX speaker notes / PDF Notes-Pages text-layer split): the orchestrator runs the transcript loader and verifies blockquotes are populated **before** dispatching the vision agent. The vision agent does not touch transcript content.

#### Skip rules (orchestrator-level)

Same as the agent-level skip list (see "Skip rules" earlier in this skill):

- Title pages, agenda slides, section dividers, "Thanks!" slides, "References" pages — never dispatched.
- Pure-text bullet slides with no diagrams / images / plots / tables / code.
- Slides that already have a `**X (LLM vision pass):**` block from an earlier batch — re-tagging would duplicate.

The vision agent enforces the same list as a second pass.

### Pass 3: Refine (dispatched to research-refiner)

After all Pass-2 batches complete, dispatch a single `research-refiner` agent with a brief listing the specific concerns the orchestrator wants fixed:

- Broken-Unicode equations (slide numbers).
- Heading fixes (slide numbers + recommended titles, or "infer from slide content").
- Speaker-notes typo fixes (paths to areas with known auto-caption errors).
- Whether to write a top-of-document summary, and which sections / cross-references it should cover.

The refiner reads the document end-to-end in its own context window — never run this inline either, because the document is typically 3-5 K lines long after Pass 2.

### Pass 4: Index Update (dispatched to research-indexer)

`docs/research/index.md` is agent-curated. No tool ever writes to it (`extract_research.py` and `extract_research_phase2.py` were both neutralised on this concern; they emit `index_extracted_pending-<timestamp>-<rand>.md` sidecars for the indexer to drain).

Dispatch a single `research-indexer` agent with:

- The canonical slug.
- The path to the produced `docs/research/<slug>.md`.
- Confirmation the source has been archived to `/mnt/archive4/PAPERS/<slug>.<ext>` (or the video subfolder).
- Optional: explicit cross-references to memory entries (`project_*`, `feedback_*`) the indexer should mention in the checklist entry. If omitted, the indexer infers from the document's existing top-of-doc Summary section.

**Preconditions** (orchestrator MUST verify before dispatch):

1. The file is at its canonical slug. Title-derived scaffolding slugs (`intro-to-foo`, `the-X-of-Y`) NEVER reach the indexer — rename first.
2. The source master is at `/mnt/archive4/PAPERS/<slug>.<ext>`.
3. There is at most one `index_extracted_pending-*.md` file matching this slug. (Multiple pending files for the same slug indicate a duplicate extraction run; resolve before dispatch.)

## Pipeline Scripts

All scripts live in `tools/` and use the venv at `tools/.venv/`. None of them touch `docs/research/index.md`. None of them silently overwrite an existing per-slug `.md` — if a `<slug>.md` already exists, they either skip or write a `<slug>.md.regen` sidecar.

| Script | Purpose | Destructive? |
|--------|---------|---------------|
| `tools/research_video.py` | YouTube or local video → scene detection, OCR, transcript alignment. Accepts `--title=` `--slug=` flags. SRT is found automatically next to the mp4 (same stem, `.en.srt`). | Refuses to overwrite existing `<slug>.md` — writes `<slug>.regen-<YYYYMMDD-HHMMSS>-<6hex>.md` next to it instead (randomised so concurrent agents don't clobber each other). Pass `--force` to overwrite in place. |
| `tools/redetect_scenes.py` | Aggressive scene re-detection for slide-heavy talks (low histogram threshold, finer interval). Writes `scene-NNN-*.jpg` to the asset dir + a TSV to `/tmp`. | Append-only. Manually clear stale `scene-*.jpg` first if you re-run with different parameters. |
| `tools/subsample_long_scenes.py` | Reads the `redetect_scenes` TSV and writes additional `sub-NNN-MM-*.jpg` frames inside any scene longer than `--min-len`. | Append-only. |
| `tools/srt_to_windows.py` | Groups an SRT into per-slide transcript windows from a `slide_starts.txt`. Output to a chosen path (defaults to `/tmp`). | Writes only to the explicit `--out` path. |
| `tools/transcribe_to_srt.py` | faster-whisper SRT generation for non-YouTube videos (HLS, local mp4 with no captions). | Refuses to overwrite an existing SRT — writes `<srt-stem>.regen-<YYYYMMDD-HHMMSS>-<6hex>.srt` sidecar instead. Pass `--force` to overwrite in place. |
| `tools/extract_research.py` | PDF/PPTX → text + image extraction. Supports `--only=SLUG` and `--force`. | Refuses to overwrite an existing per-slug `.md` even under `--only` — writes a `<slug>.regen-<YYYYMMDD-HHMMSS>-<6hex>.md` sidecar instead. Pass `--force` to overwrite in place. **Never writes index.md** — writes a suggested-rows file at `index_extracted_pending-<YYYYMMDD-HHMMSS>-<6hex>.md` instead (merge by hand, then delete). All sidecar suffixes are randomised so concurrent agents don't clobber each other. |
| `tools/extract_research_phase2.py` | Extract videos embedded in PPTX decks and transcribe them with faster-whisper. (Body-text OCR fallback for image-only PDFs / slides moved into phase 1; per-image OCR was removed entirely — the vision pass owns image description.) Supports `--only=SLUG[,SLUG2]`. | Per-slug `.md` only. **Never writes index.md**. |
| `tools/cleanup_research.py` | Strip watermarks, duplicate headings, garbage OCR. Supports `--only=SLUG`. | Per-slug `.md` only. |

**If you need a one-off media-processing helper that doesn't fit the above:** edit / add a tracked file under `tools/` and commit it. **Do not** write throwaway helpers to `/tmp` — every future /research run will re-derive the same script from scratch otherwise.

## Determining Input Type

- Starts with `http` or `https` and contains `m3u8` → HLS stream pipeline (ffmpeg download + whisper)
- Starts with `http` or `https` → YouTube pipeline (yt-dlp)
- Ends with `.pdf` → PDF extraction
- Ends with `.pptx` → PPTX extraction
- Ends with `.mp4`, `.mkv`, `.webm` → local video (research_video.py with `--title` and `--slug`)

## Output Structure

```
docs/research/
  index.md                          # TOC for all extracted documents
  {slug}.md                         # one markdown per source
  assets/{slug}/                    # images, frames, videos
```

In addition, the **source master** lives in `/mnt/archive4/PAPERS/` (see "REQUIRED: Source Archive in `/mnt/archive4/PAPERS/`" above). PDFs/PPTXs go top-level as `<slug>.pdf`/`<slug>.pptx`; videos go in a `<year>-<slug-tail>/` subfolder with both the mp4 and the .en.srt. Copying source into PAPERS/ is part of every `/research` run, not optional.

## Dependencies

Venv at `tools/.venv/`: `pymupdf`, `python-pptx`, `opencv-python-headless`, `openocr-python`, `faster-whisper`

System: `yt-dlp`, `ffmpeg`, `libreoffice` (PPTX rendering)

OCR engine: [OpenOCR](https://github.com/Topdu/OpenOCR) (mobile/ONNX backend, auto-downloads models to `~/.cache/openocr/` on first run). Wrapped behind `tools/openocr_engine.py` as a singleton — model load happens once per process and is shared between phase 1 (body-text fallback for image-only sources) and the video pipeline (`research_video.py` per-frame OCR). Override behaviour via env vars: `OPENOCR_MODE=server` (higher accuracy, requires `pip install torch torchvision`), `OPENOCR_BACKEND=torch`, `OPENOCR_DROP_SCORE=0.5`.
